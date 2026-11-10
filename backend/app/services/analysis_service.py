import io
import logging
import re
import threading
import time
import traceback
import uuid
import warnings
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional, Dict, Any, List
from PIL import Image

logger = logging.getLogger(__name__)

from app.core.errors import APIError
from app.repositories.analysis_repository import AnalysisRepository
from app.services.storage_service import StorageService

from ai.inference.gradcam import GradCAMResult, generate_gradcam
from ai.config.model_config import MODEL_CONFIG
from ai.inference.domain_validator import ColonoscopyDomainValidator, DomainDecision
from ai.inference.pipeline import PHASE_INFERENCE, PipelineResult, run_pipeline
from ai.inference.segmentation import SegmentationResult, count_forward_passes, predict
from ai.inference.preprocessing import prepare_image


# A 'processing' record this process is NOT working on and that is older than
# this threshold is flagged (non-mutating) as potentially stuck for inspection.
# It never changes `status` and never marks a locally queued job stale, however
# long that job runs. Tunable; conservative to avoid false marks.
STALE_THRESHOLD = timedelta(minutes=15)

# progress_percent = floor(completed_units / total_units * 100), where a unit is
# one completed reportable phase (the 5 pipeline phases + the service-side
# artifact-upload phase) or one completed inference forward pass. This is
# countable completed work, never elapsed time or assumed durations.
_PROGRESS_FLOOR = 100.0

# DB-write throttle: emit an inference progress update roughly every this many
# completed forward passes, in addition to the once-per-phase updates. Keeps
# write volume bounded during the ~25-pass TTA loop.
_PROGRESS_PASS_THROTTLE = 5

# Service-side phase vocabulary (English, matches APIContract current_step,
# whose documented example value is `inference`).
_STEP_UPLOADING_RESULTS = "uploading_results"
_STEP_COMPLETED = "completed"


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Best-effort parse of a persisted UTC timestamp (tolerates 'Z' suffix)."""
    if not value:
        return None
    try:
        text = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (ValueError, TypeError):
        return None


class AnalysisProgressReporter:
    """Turn completed pipeline units into throttled DB progress writes.

    Progress is ``floor(completed_units / total_units * 100)`` over countable
    work: one unit per completed pipeline phase, plus one per completed
    inference forward pass. ``current_step`` always reflects the most recently
    completed phase.

    Safety properties:
    - ``progress_percent`` never decreases (writes are skipped when the rounded
      percent has not moved, and the service clamps the stored value).
    - A DB/reporting failure is swallowed and counted (``failed_writes``) but
      never propagates, so a successful AI pipeline is never turned into a
      failure by a progress write.
    - The percentage is capped below 100 (``percent``) so 100% is reserved for
      the final persisted 'completed' state.
    """

    def __init__(self, repository, analysis_id: str, user_id: str,
                 total_units: int, throttle: int = _PROGRESS_PASS_THROTTLE):
        self._repository = repository
        self._analysis_id = analysis_id
        self._user_id = user_id
        self.total_units = max(1, total_units)
        self._throttle = max(1, throttle)
        self._completed_units = 0
        self._passes_done = 0
        self._last_percent = -1
        self._last_step: Optional[str] = None
        self.failed_writes = 0

    @property
    def last_step(self) -> Optional[str]:
        """Most recently completed phase, or None if no phase completed yet."""
        return self._last_step

    @property
    def completed_units(self) -> int:
        return self._completed_units

    @property
    def percent(self) -> int:
        """Completed-work percentage, capped below 100 (100% is 'completed' only)."""
        raw = int(self._completed_units * _PROGRESS_FLOOR / self.total_units)
        return min(raw, 99)

    def on_phase(self, step: str) -> None:
        """Record one completed pipeline phase and report it."""
        self._completed_units += 1
        self._last_step = step
        self._write(step)

    def on_pass(self) -> None:
        """Record one completed inference forward pass; throttle DB writes."""
        self._completed_units += 1
        self._passes_done += 1
        if self._passes_done % self._throttle == 0:
            # Forward passes execute inside the inference stage, so report that
            # stage as running (APIContract: "Tahap yang sedang berjalan, mis.
            # inference"). The unit counted above is a *completed* pass only.
            self._write(PHASE_INFERENCE)

    def _write(self, step: str) -> None:
        percent = self.percent
        # Skip no-op writes (same step, same rounded percent) to keep volume low.
        if step == self._last_step and percent == self._last_percent:
            return
        try:
            self._repository.update(
                analysis_id=self._analysis_id,
                user_id=self._user_id,
                data={
                    "current_step": step,
                    "progress_percent": percent,
                    # The migration does not auto-update updated_at.
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                use_service_role=True,
            )
            self._last_percent = percent
        except Exception:
            # Reporting failure != inference failure. Count it, keep going, and
            # never let it abort a safe, successful pipeline.
            self.failed_writes += 1


class AnalysisJobQueue:
    """In-memory FIFO queue for background analysis pipelines (stdlib only).

    Capacity: the queue accepts at most ``MAX_WAITING + 1`` jobs total. A single
    worker thread runs one job at a time; up to ``MAX_WAITING`` additional jobs
    wait behind it. When full, ``try_enqueue`` returns ``False`` so the caller
    can return HTTP 429.

    Limitations (documented, not hidden):
    - The queue is in-memory and per-process. A process restart loses every
      queued and in-flight job; the affected record stays at 'processing'
      until inspected (see the non-mutating stale marker in ``get_analysis``).
    - Exactly-once execution holds for the normal queue lifecycle (each job is
      popped once). There is no retry and no cross-process coordination.
    """

    MAX_WAITING = 3

    def __init__(
        self,
        runner: Callable[[Dict[str, Any]], None],
        max_waiting: int = MAX_WAITING,
        auto_start: bool = True,
    ):
        self._runner = runner
        self._max_waiting = max_waiting
        self._jobs: deque[Dict[str, Any]] = deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._worker_started = False
        self._auto_start = auto_start
        self._active_analysis_id: Optional[str] = None

    @property
    def capacity(self) -> int:
        """Total jobs the queue accepts before reporting full (1 + MAX_WAITING)."""
        return self._max_waiting + 1

    def try_enqueue(self, job: Dict[str, Any]) -> bool:
        """Enqueue a job, returning False when the queue is at capacity."""
        import time
        job_with_time = dict(job)
        job_with_time["enqueued_at"] = time.perf_counter()
        with self._not_empty:
            if len(self._jobs) >= self.capacity:
                return False
            self._jobs.append(job_with_time)
            self._not_empty.notify()
        if self._auto_start:
            self._ensure_worker()
        return True

    def contains(self, analysis_id: str) -> bool:
        """True when the job is the active one or still waiting in this process."""
        with self._lock:
            if self._active_analysis_id == analysis_id:
                return True
            return any(job.get("analysis_id") == analysis_id for job in self._jobs)

    def pending_count(self) -> int:
        with self._lock:
            return len(self._jobs)

    def drain_one(self) -> bool:
        """Run exactly one queued job synchronously and return whether one ran.

        Deterministic test hook: avoids threads/sleeps so tests can step the
        queue without race conditions.
        """
        with self._not_empty:
            if not self._jobs:
                return False
            job = self._jobs.popleft()
            self._active_analysis_id = job.get("analysis_id")
        try:
            self._runner(job)
        finally:
            with self._lock:
                self._active_analysis_id = None
        return True

    def _ensure_worker(self) -> None:
        with self._not_empty:
            if self._worker_started:
                return
            self._worker_started = True
            threading.Thread(
                target=self._work_loop, name="analysis-worker", daemon=True
            ).start()

    def _work_loop(self) -> None:
        while True:
            with self._not_empty:
                while not self._jobs:
                    self._not_empty.wait()
                job = self._jobs.popleft()
                self._active_analysis_id = job.get("analysis_id")
                # Measure queue wait time
                enqueued_at = job.get("enqueued_at")
                if enqueued_at is not None:
                    wait_time = time.perf_counter() - enqueued_at
                    # Log queue wait time for monitoring
                    # Using print to avoid logging config dependency in this module
                    print(f"[TIMING] analysis_id={job.get('analysis_id')} stage=queue_wait duration_ms={wait_time * 1000:.1f}")
            try:
                self._runner(job)
            except Exception as exc:
                # The runner persists its own failures; this guard only keeps
                # the worker alive if an error ever escapes it.
                # Log the exception with traceback for debugging.
                import traceback
                analysis_id = job.get('analysis_id', 'unknown')
                print(f"[ERROR] Worker exception for analysis_id={analysis_id}: {exc}")
                traceback.print_exc()
            finally:
                with self._lock:
                    self._active_analysis_id = None


class AnalysisService:
    """Service handling analysis orchestration, secure image validation, and persistence.

    Strictly complies with TASK 08 boundaries:
    - Validates image dimensions, MIME type, and bytes via Pillow.
    - Persists original image to Supabase Storage.
    - Creates analysis record with status 'processing'.
    - Performs cleanup on partial failures.
    - NO AI inference, NO mock segmentation, NO Grad-CAM generation.
    """

    ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png'}
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

    def __init__(
        self,
        repository: Optional[AnalysisRepository] = None,
        storage_service: Optional[StorageService] = None,
        pipeline_runner: Optional[Callable[..., PipelineResult]] = None,
        job_queue: Optional[AnalysisJobQueue] = None,
        domain_validator: Optional[ColonoscopyDomainValidator] = None,
        auto_start_worker: bool = True,
        enforce_domain_validation: Optional[bool] = None,
        llm_validator: Optional[Callable[..., Any]] = None,
        enforce_llm_validation: Optional[bool] = None,
        llm_client: Optional[Any] = None,
    ):
        self.repository = repository or AnalysisRepository()
        self.storage_service = storage_service or StorageService()
        self.pipeline_runner = pipeline_runner or run_pipeline
        self.domain_validator = domain_validator or ColonoscopyDomainValidator()
        # The queue runner defers to the bound method so tests can inject a
        # synchronous pipeline_runner and step the queue deterministically.
        self.job_queue = job_queue or AnalysisJobQueue(
            runner=lambda job: self._run_analysis_job(job),
            auto_start=auto_start_worker,
        )
        self._enforce_domain_validation = enforce_domain_validation
        self._llm_validator = llm_validator
        self._enforce_llm_validation = enforce_llm_validation
        self._llm_client = llm_client

    @property
    def is_domain_validation_enabled(self) -> bool:
        if self._enforce_domain_validation is not None:
            return self._enforce_domain_validation
        try:
            from flask import current_app
            return bool(current_app.config.get("DOMAIN_VALIDATION_ENABLED", True))
        except (ImportError, RuntimeError):
            return True

    @property
    def is_llm_validation_enabled(self) -> bool:
        if self._enforce_llm_validation is not None:
            return self._enforce_llm_validation
        try:
            from flask import current_app
            return bool(current_app.config.get("LLM_VALIDATION_ENABLED", True))
        except (ImportError, RuntimeError):
            return True

    def validate_and_decode_image(self, file_storage) -> tuple[bytes, str, str, int, int]:
        """Validate uploaded file for size, format, integrity, and dimensions.

        Returns:
            tuple: (file_bytes, mime_type, extension, width, height)

        Raises:
            APIError: If validation fails.
        """
        filename = getattr(file_storage, "filename", "") if file_storage else ""
        if not filename:
            raise APIError("MISSING_FILE", "No image file provided in request.", 400)

        if (
            filename in {".", ".."}
            or ".." in filename
            or "/" in filename
            or "\\" in filename
            or any(ord(character) < 32 or ord(character) == 127 for character in filename)
        ):
            raise APIError("INVALID_IMAGE", "Uploaded filename is invalid.", 400)

        # Read binary content
        file_bytes = file_storage.read()
        if not file_bytes or len(file_bytes) == 0:
            raise APIError("EMPTY_FILE", "Uploaded image file is empty.", 400)

        if len(file_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise APIError(
                "FILE_TOO_LARGE",
                f"File size exceeds the 10 MB limit ({len(file_bytes)} bytes).",
                400,
            )

        declared_mime_type = getattr(file_storage, "mimetype", "")
        if declared_mime_type not in self.ALLOWED_MIME_TYPES:
            raise APIError("INVALID_IMAGE", "Only JPEG and PNG images are supported.", 400)

        # Verify image integrity and force a full decode before storing the original.
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(file_bytes)) as image:
                    raw_format = (image.format or "").upper()
                    image.verify()
                with Image.open(io.BytesIO(file_bytes)) as image:
                    image.load()
                    width, height = image.size
        except Exception:
            raise APIError("INVALID_IMAGE", "Uploaded file is not a valid or readable image.", 400)

        if raw_format == "JPEG":
            mime_type = "image/jpeg"
            extension = "jpg"
        elif raw_format == "PNG":
            mime_type = "image/png"
            extension = "png"
        else:
            raise APIError("INVALID_IMAGE", "Only JPEG and PNG images are supported.", 400)

        if declared_mime_type != mime_type:
            raise APIError("INVALID_IMAGE", "Declared MIME type does not match image content.", 400)

        if width <= 0 or height <= 0:
            raise APIError("INVALID_IMAGE", "Image dimensions must be positive integers.", 400)

        return file_bytes, mime_type, extension, width, height

    def create_analysis(self, file_storage, user_id: str) -> Dict[str, Any]:
        """Accept one upload and enqueue its analysis (two-phase, Batch P-02).

        Validates the image, persists the original, creates a 'processing'
        record, then enqueues the AI pipeline as a background job and returns
        the stable analysis_id immediately. The pipeline runs asynchronously;
        clients poll GET /api/analysis/<id> until status is 'completed' or
        'failed'.
        """
        import time
        if not user_id:
            raise APIError("UNAUTHORIZED", "Authenticated user ID is required.", 401)

        print(f"[CORRELATION] user_id={user_id} stage=create_analysis_service start")
        start_time = time.perf_counter()

        # 1. Validate and decode image
        file_bytes, mime_type, extension, width, height = self.validate_and_decode_image(
            file_storage
        )

        analysis_id = str(uuid.uuid4())
        safe_original_filename = file_storage.filename.strip()[:255]

        # 2. Medical domain validation (Colonoscopy vs Non-colonoscopy).
        # Runs before any storage upload, DB insert, or job enqueue so a REJECT
        # or UNCERTAIN leaves no file, no record, and no queued job.
        if self.is_domain_validation_enabled:
            domain_result = self.domain_validator.validate_bytes(file_bytes)
            feature_summary = ", ".join(
                f"{k}={v:.4f}" for k, v in sorted(domain_result.metrics.items())
            )
            print(
                f"[DOMAIN] analysis_id={analysis_id} user_id={user_id} "
                f"decision={domain_result.decision.value} "
                f"confidence={domain_result.confidence:.4f} "
                f"reasons={'; '.join(domain_result.reasons)} "
                f"features={{{feature_summary}}}"
            )
            if domain_result.decision == DomainDecision.REJECT:
                raise APIError(
                    "NOT_COLONOSCOPY_IMAGE",
                    domain_result.message or "Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.",
                    400,
                )
            if domain_result.decision == DomainDecision.UNCERTAIN:
                raise APIError(
                    "UNCERTAIN_COLONOSCOPY_IMAGE",
                    domain_result.message or "Sistem tidak dapat memastikan bahwa citra ini adalah kolonoskopi. Silakan unggah citra yang lebih jelas.",
                    400,
                )

        # 2b. Secondary LLM domain verification (Gemini Gate).
        # Only runs if heuristic validation produced ACCEPT.
        # Fail-closed: REJECT raises NOT_COLONOSCOPY_IMAGE, ERROR/failure raises UNCERTAIN_COLONOSCOPY_IMAGE.
        if self.is_llm_validation_enabled:
            from app.services.llm_image_validator import validate_with_llm, MSG_LLM_SERVICE_ERROR

            validator_fn = self._llm_validator or validate_with_llm
            model_name = "gemini-3.8-flash"
            min_conf = 0.80
            timeout_s = 15.0
            try:
                from flask import current_app
                model_name = current_app.config.get("LLM_VALIDATION_MODEL", model_name)
                min_conf = float(current_app.config.get("LLM_VALIDATION_MIN_CONF", min_conf))
                timeout_s = float(current_app.config.get("LLM_VALIDATION_TIMEOUT_S", timeout_s))
            except (ImportError, RuntimeError):
                pass

            llm_result = validator_fn(
                image_bytes=file_bytes,
                mime_type=mime_type,
                client=self._llm_client,
                model_name=model_name,
                min_confidence=min_conf,
                timeout_s=timeout_s,
            )

            print(
                f"[LLM_DOMAIN] analysis_id={analysis_id} user_id={user_id} "
                f"status={llm_result.status} image_type={llm_result.image_type} "
                f"confidence={llm_result.confidence:.4f} ok={llm_result.ok}"
            )

            if llm_result.status == "REJECT":
                raise APIError(
                    "NOT_COLONOSCOPY_IMAGE",
                    "Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.",
                    400,
                )
            if not llm_result.ok or llm_result.status == "ERROR":
                raise APIError(
                    "UNCERTAIN_COLONOSCOPY_IMAGE",
                    MSG_LLM_SERVICE_ERROR,  # B5: konstanta terpusat di llm_image_validator.py
                    400,
                )

        print(f"[CORRELATION] analysis_id={analysis_id} user_id={user_id} stage=create_analysis_service validation_done")

        # 2. Generate ownership-aware storage path
        original_image_path = self.storage_service.generate_original_image_path(
            user_id=user_id, analysis_id=analysis_id, extension=extension
        )

        # 3. Upload to private Supabase Storage
        try:
            upload_start = time.perf_counter()
            self.storage_service.upload_file(
                path=original_image_path,
                file_bytes=file_bytes,
                content_type=mime_type,
                user_id=user_id,
                use_service_role=True,
            )
            upload_dur = (time.perf_counter() - upload_start) * 1000
            print(f"[CORRELATION] analysis_id={analysis_id} stage=storage_upload_original duration_ms={upload_dur:.1f}")
        except Exception:
            try:
                self.storage_service.delete_file(
                    original_image_path, user_id=user_id, use_service_role=True
                )
            except Exception:
                pass
            raise APIError(
                "STORAGE_ERROR",
                "Failed to store uploaded image.",
                500,
            )

        # 4. Create analysis record in database
        try:
            record_data = {
                "id": analysis_id,
                "user_id": user_id,
                "status": "processing",
                "original_image_path": original_image_path,
                "original_filename": safe_original_filename,
                "original_mime_type": mime_type,
                "original_width": width,
                "original_height": height,
            }
            db_start = time.perf_counter()
            self.repository.create(
                user_id=user_id, data=record_data, use_service_role=True
            )
            db_dur = (time.perf_counter() - db_start) * 1000
            print(f"[CORRELATION] analysis_id={analysis_id} stage=db_create duration_ms={db_dur:.1f}")
        except Exception:
            # Rollback: Clean up uploaded asset if database insert fails
            try:
                self.storage_service.delete_file(
                    original_image_path, user_id=user_id, use_service_role=True
                )
            except Exception:
                pass
            try:
                self.repository.delete(
                    analysis_id, user_id, use_service_role=True
                )
            except Exception:
                pass
            raise APIError(
                "DATABASE_ERROR",
                "Failed to create analysis record.",
                500,
            )

        # 5. Enqueue the background pipeline job. Compensation: a rejected
        #    enqueue must not leave a record that looks like it is running.
        job = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "file_bytes": file_bytes,
        }
        queue_start = time.perf_counter()
        if not self.job_queue.try_enqueue(job):
            # Kompensasi: hapus record dan objek original yang baru diunggah
            # agar tidak ada record 'processing' yang menyesatkan (tidak pernah
            # berjalan). Kedua pembersihan bersifat best-effort; bila keduanya
            # gagal, record yatim bisa tersisa dan ditandai oleh mekanisme stale.
            try:
                self.repository.delete(analysis_id, user_id, use_service_role=True)
            except Exception:
                pass
            try:
                self.storage_service.delete_file(
                    original_image_path, user_id=user_id, use_service_role=True
                )
            except Exception:
                pass
            raise APIError(
                "QUEUE_FULL",
                "Analysis queue is at capacity. Please try again shortly.",
                429,
            )
        queue_dur = (time.perf_counter() - queue_start) * 1000
        print(f"[CORRELATION] analysis_id={analysis_id} stage=queue_enqueue duration_ms={queue_dur:.1f}")

        total_dur = (time.perf_counter() - start_time) * 1000
        print(f"[CORRELATION] analysis_id={analysis_id} user_id={user_id} stage=create_analysis_service end duration_ms={total_dur:.1f}")

        return {
            "analysis_id": analysis_id,
            "status": "processing",
        }

    def get_analysis(self, analysis_id: str, user_id: str) -> Dict[str, Any]:
        """Retrieve analysis details verifying user ownership.

        Returns persisted metadata and short-lived URLs for assets owned by the user.
        """
        import time
        start_time = time.perf_counter()
        if not user_id:
            raise APIError("UNAUTHORIZED", "Authenticated user ID is required.", 401)

        print(f"[CORRELATION] analysis_id={analysis_id} user_id={user_id} stage=get_analysis_service start")
        record = self.repository.get_by_id(
            analysis_id, user_id, use_service_role=True
        )
        if not record:
            raise APIError("ANALYSIS_NOT_FOUND", "Analysis not found or access denied.", 404)

        def signed_asset_url(path: Optional[str]) -> Optional[str]:
            if not path:
                return None
            try:
                return self.storage_service.create_signed_url(
                    path=path,
                    expires_in=3600,
                    user_id=user_id,
                    use_service_role=True,
                ) or None
            except Exception:
                return None

        analysis_data: Dict[str, Any] = {
            "id": record["id"],
            "status": record["status"],
            "created_at": record.get("created_at"),
            "completed_at": record.get("completed_at"),
            "original_filename": record.get("original_filename"),
        }
        if record.get("status") == "failed":
            analysis_data["error_code"] = "ANALYSIS_FAILED"
            analysis_data["error_message"] = (
                "Analysis could not be completed. Please try again."
            )

        # Optional progress fields (Batch P-02: nullable). In P-02 these stay
        # null; surfaced only when actually set — never fabricated.
        if record.get("current_step") is not None:
            analysis_data["current_step"] = record["current_step"]
        if record.get("progress_percent") is not None:
            analysis_data["progress_percent"] = record["progress_percent"]

        # Non-mutating stale marker: a 'processing' record this process is NOT
        # working on and that is older than STALE_THRESHOLD is flagged for
        # inspection. It never changes status and never marks a locally queued
        # (active/waiting) job stale, however long that job runs.
        if record.get("status") == "processing" and not self.job_queue.contains(
            analysis_id
        ):
            created_at = _parse_timestamp(record.get("created_at"))
            if created_at is not None:
                age = datetime.now(timezone.utc) - created_at
                if age > STALE_THRESHOLD:
                    analysis_data["stale"] = True

        data: Dict[str, Any] = {
            "analysis": analysis_data,
            "input": {
                "original_image_url": signed_asset_url(
                    record.get("original_image_path")
                ),
                "width": record.get("original_width"),
                "height": record.get("original_height"),
                "mime_type": record.get("original_mime_type"),
            },
        }

        segmentation = {
            "binary_mask_url": signed_asset_url(record.get("binary_mask_path")),
            "overlay_url": signed_asset_url(record.get("segmentation_overlay_path")),
        }
        model_analysis_fields = {
            "segmentation_status": "segmentation_status",
            "area_pixels": "area_pixels",
            "area_ratio": "area_ratio",
            "bounding_width_pixels": "bounding_width_pixels",
            "bounding_height_pixels": "bounding_height_pixels",
        }
        model_analysis = {
            response_key: record.get(record_key)
            for response_key, record_key in model_analysis_fields.items()
            if record.get(record_key) is not None
        }

        # Derive post-segmentation validation category from persisted summary
        summary_raw = record.get("summary_text") or ""
        detection_category = None
        if summary_raw.startswith("[POLYP_DETECTED]"):
            detection_category = "POLYP_DETECTED"
        elif summary_raw.startswith("[NO_POLYP_DETECTED]"):
            detection_category = "NO_POLYP_DETECTED"
        elif summary_raw.startswith("[LOW_CONFIDENCE]"):
            detection_category = "LOW_CONFIDENCE"
        elif record.get("segmentation_status") == "detected":
            detection_category = "POLYP_DETECTED"
        elif record.get("segmentation_status") == "not_detected":
            detection_category = "NO_POLYP_DETECTED"

        if detection_category:
            model_analysis["detection_category"] = detection_category

        if any(value is not None for value in segmentation.values()):
            data["segmentation"] = segmentation
        if model_analysis:
            data["model_analysis"] = model_analysis

        gradcam = {
            "heatmap_url": signed_asset_url(record.get("gradcam_heatmap_path")),
            "overlay_url": signed_asset_url(record.get("gradcam_overlay_path")),
        }
        if any(value is not None for value in gradcam.values()):
            data["gradcam"] = gradcam

        model = {
            response_key: record.get(record_key)
            for response_key, record_key in {
                "architecture": "model_architecture",
                "version": "model_version",
            }.items()
            if record.get(record_key) is not None
        }
        for response_key, record_key in {
            "threshold": "model_threshold",
            "checkpoint_sha256": "model_checkpoint_sha256",
            "input_size": "model_input_size",
            "tta_enabled": "tta_enabled",
            "postprocessing_enabled": "postprocessing_enabled",
            "gradcam_target_layer": "gradcam_target_layer",
            "gradcam_status": "gradcam_status",
        }.items():
            if record.get(record_key) is not None:
                model[response_key] = record[record_key]
        if model:
            data["model"] = model

        if record.get("summary_text"):
            raw_text = record["summary_text"]
            clean_text = raw_text.split("] ", 1)[-1] if raw_text.startswith("[") and "] " in raw_text else raw_text
            data["summary"] = {"text": clean_text}

        duration_ms = (time.perf_counter() - start_time) * 1000
        print(f"[CORRELATION] analysis_id={analysis_id} user_id={user_id} stage=get_analysis_service end duration_ms={duration_ms:.1f}")

        return data

    def list_user_analyses(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> list:
        """List analysis history for the authenticated user.

        Raw repository rows are mapped to a minimal list payload so private storage
        paths are never exposed. ``thumbnail_url`` is a short-lived signed URL for
        the original image, matching the APIContract list-history shape.
        """
        if not user_id:
            raise APIError("UNAUTHORIZED", "Authenticated user ID is required.", 401)

        try:
            records = self.repository.list_by_user(
                user_id=user_id,
                limit=limit,
                offset=offset,
                use_service_role=True,
            )
        except Exception as error:
            raise APIError(
                "DATABASE_ERROR", "Failed to retrieve analysis history.", 500
            ) from error

        items = []
        for record in records or []:
            thumbnail_url = None
            original_path = record.get("original_image_path")
            if original_path:
                try:
                    thumbnail_url = self.storage_service.create_signed_url(
                        path=original_path,
                        expires_in=3600,
                        user_id=user_id,
                        use_service_role=True,
                    ) or None
                except Exception:
                    thumbnail_url = None

            item: Dict[str, Any] = {
                "id": record.get("id"),
                "created_at": record.get("created_at"),
                "completed_at": record.get("completed_at"),
                "status": record.get("status"),
                "original_filename": record.get("original_filename"),
                "thumbnail_url": thumbnail_url,
            }
            if record.get("segmentation_status") is not None:
                item["segmentation_status"] = record.get("segmentation_status")
            items.append(item)

        return items

    def delete_analysis(self, analysis_id: str, user_id: str) -> bool:
        """Delete one analysis session and its stored assets for the owner.

        Ownership is verified first. The database record is removed before storage
        cleanup so a database failure leaves the stored assets intact and retryable,
        then stored objects are removed on a best-effort basis.
        """
        if not user_id:
            raise APIError("UNAUTHORIZED", "Authenticated user ID is required.", 401)

        record = self.repository.get_by_id(
            analysis_id, user_id, use_service_role=True
        )
        if not record:
            raise APIError(
                "ANALYSIS_NOT_FOUND", "Analysis not found or access denied.", 404
            )

        try:
            deleted = self.repository.delete(
                analysis_id, user_id, use_service_role=True
            )
        except Exception as error:
            raise APIError(
                "DATABASE_ERROR", "Failed to delete analysis record.", 500
            ) from error

        if not deleted:
            raise APIError(
                "ANALYSIS_NOT_FOUND", "Analysis not found or access denied.", 404
            )

        asset_paths = [
            path
            for path in (
                record.get("original_image_path"),
                record.get("binary_mask_path"),
                record.get("segmentation_overlay_path"),
                record.get("gradcam_heatmap_path"),
                record.get("gradcam_overlay_path"),
            )
            if path
        ]
        # DECISION A (locked by project owner): DB-first deletion with storage
        # cleanup as a required post-delete step. A storage failure after the
        # database record is gone is an explicit non-fatal residual-risk case:
        # the record stays deleted, the API still reports success, and no
        # storage internals are exposed to the client (APIContract §22).
        # The outcome is captured in `storage_cleanup_ok` (not silently
        # discarded) so tests and audit reports can pin the behavior.
        storage_cleanup_ok = True
        if asset_paths:
            try:
                storage_cleanup_ok = bool(
                    self.storage_service.delete_analysis_files(
                        paths=asset_paths,
                        user_id=user_id,
                        use_service_role=True,
                    )
                )
            except Exception:
                # Never expose storage internals; record is already removed.
                storage_cleanup_ok = False

        if not storage_cleanup_ok:
            # Residual risk (DECISION A): orphaned storage objects may remain.
            # They are unreachable via the API (record deleted, paths are
            # ownership-scoped). No resurrection is attempted: re-inserting
            # the record could produce a more inconsistent state.
            pass

        return True

    def _run_analysis_job(self, job: Dict[str, Any]) -> None:
        """Background worker entry point: run the pipeline, swallow the error.

        The failure is already persisted as status='failed' by
        ``_execute_pipeline``; there is no HTTP caller to respond to, so the
        terminal APIError is intentionally not re-raised here.
        """
        import traceback
        analysis_id = job.get("analysis_id", "unknown")
        try:
            self._execute_pipeline(
                analysis_id=job["analysis_id"],
                user_id=job["user_id"],
                file_bytes=job["file_bytes"],
            )
        except Exception as exc:
            # Log the exception with traceback for debugging before swallowing
            print(f"[ERROR] _run_analysis_job failed for analysis_id={analysis_id}: {exc}")
            traceback.print_exc()

    def _execute_pipeline(self, analysis_id: str, user_id: str, file_bytes: bytes) -> None:
        """Run the AI pipeline and persist results for one accepted analysis.

        Executes in the background worker. On failure it persists status='failed'
        (with an explicit updated_at) and re-raises so the caller decides how to
        surface the error. Ownership and service-role access mirror the original
        synchronous implementation.
        """
        generated_paths: list[str] = []
        # Progress reporter lives outside the try so the failure path can carry
        # forward the last *actual* progress (never 100%, never fabricated).
        progress: Optional[AnalysisProgressReporter] = None
        execute_start = time.perf_counter()
        try:
            # Progress reporter: counts completed units (phases + forward
            # passes) and writes throttled progress_percent/current_step. Its
            # writes are best-effort and never affect the inference outcome.
            # Units = 5 pipeline phases + 1 service-side artifact-upload phase
            # + one unit per TTA forward pass counted from the runtime config.
            total_units = 6 + count_forward_passes(MODEL_CONFIG)
            progress = AnalysisProgressReporter(
                repository=self.repository,
                analysis_id=analysis_id,
                user_id=user_id,
                total_units=total_units,
            )
            pipeline_start = time.perf_counter()
            pipeline_result = self.pipeline_runner(
                file_bytes,
                config=MODEL_CONFIG,
                on_phase=progress.on_phase,
                on_pass=progress.on_pass,
                analysis_id=analysis_id,
            )
            pipeline_dur = time.perf_counter() - pipeline_start
            print(f"[TIMING] analysis_id={analysis_id} stage=pipeline_ai duration_ms={pipeline_dur * 1000:.1f}")
            generated_assets = {
                self.storage_service.generate_binary_mask_path(user_id, analysis_id): (
                    pipeline_result.binary_mask_png,
                    "image/png",
                ),
                self.storage_service.generate_segmentation_overlay_path(user_id, analysis_id): (
                    pipeline_result.segmentation_overlay_png,
                    "image/png",
                ),
                self.storage_service.generate_gradcam_heatmap_path(user_id, analysis_id): (
                    pipeline_result.gradcam_heatmap_png,
                    "image/png",
                ),
                self.storage_service.generate_gradcam_overlay_path(user_id, analysis_id): (
                    pipeline_result.gradcam_overlay_png,
                    "image/png",
                ),
            }
            generated_paths: list[str] = []

            # Upload all 4 artifacts sequentially using StorageService
            # All must succeed before marking analysis as completed
            upload_start = time.perf_counter()
            for path, (asset_bytes, content_type) in generated_assets.items():
                single_upload_start = time.perf_counter()
                self.storage_service.upload_file(
                    path=path,
                    file_bytes=asset_bytes,
                    content_type=content_type,
                    user_id=user_id,
                    use_service_role=True,
                )
                generated_paths.append(path)
                single_upload_dur = time.perf_counter() - single_upload_start
                artifact_name = path.split("/")[-1]
                print(f"[TIMING] analysis_id={analysis_id} stage=storage_upload artifact={artifact_name} duration_ms={single_upload_dur * 1000:.1f}")

            upload_total_dur = time.perf_counter() - upload_start
            print(f"[TIMING] analysis_id={analysis_id} stage=storage_upload_total duration_ms={upload_total_dur * 1000:.1f}")

            # All 4 required artifacts are now stored: report the upload phase.
            progress.on_phase(_STEP_UPLOADING_RESULTS)

            measurements = pipeline_result.measurements
            update_data = {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                # Persist the last completed phase and full completion. 100% is
                # written only here, alongside the final 'completed' status.
                "current_step": _STEP_COMPLETED,
                "progress_percent": 100,
                "binary_mask_path": next(path for path in generated_paths if "/segmentation/" in path and path.endswith("mask.png")),
                "segmentation_overlay_path": next(path for path in generated_paths if path.endswith("overlay.png") and "/segmentation/" in path),
                "segmentation_status": measurements["segmentation_status"],
                "area_pixels": measurements["area_pixels"],
                "area_ratio": measurements["area_ratio"],
                "bounding_width_pixels": measurements["bounding_width_pixels"],
                "bounding_height_pixels": measurements["bounding_height_pixels"],
                "gradcam_heatmap_path": next(path for path in generated_paths if path.endswith("heatmap.png")),
                "gradcam_overlay_path": next(path for path in generated_paths if "/gradcam/" in path and path.endswith("overlay.png")),
                "gradcam_target_layer": pipeline_result.gradcam.target_layer,
                "gradcam_method": "Grad-CAM",
                "gradcam_config_version": MODEL_CONFIG.model_version,
                "gradcam_status": "completed",
                "model_architecture": MODEL_CONFIG.architecture,
                "model_version": MODEL_CONFIG.model_version,
                "model_config_version": MODEL_CONFIG.model_version,
                "model_checkpoint_sha256": MODEL_CONFIG.checkpoint_sha256,
                "model_input_size": MODEL_CONFIG.input_size,
                "model_threshold": MODEL_CONFIG.threshold,
                "tta_enabled": MODEL_CONFIG.tta_enabled,
                "tta_scales": list(MODEL_CONFIG.tta_scales),
                "tta_orientations": [
                    "original", "horizontal_flip", "vertical_flip", "rotate_90", "rotate_270"
                ],
                "postprocessing_enabled": MODEL_CONFIG.postprocessing_enabled,
                "summary_text": pipeline_result.summary_text,
                "error_code": None,
                "error_message": None,
                # The migration does not auto-update updated_at, so write it
                # explicitly on every record update (APIContract/P-02).
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            db_update_start = time.perf_counter()
            updated = self.repository.update(
                analysis_id=analysis_id,
                user_id=user_id,
                data=update_data,
                use_service_role=True,
            )
            db_update_dur = time.perf_counter() - db_update_start
            print(f"[TIMING] analysis_id={analysis_id} stage=db_update_completed duration_ms={db_update_dur * 1000:.1f}")
            if updated is None:
                raise RuntimeError("analysis database update returned no record")
            execute_total_dur = time.perf_counter() - execute_start
            print(f"[TIMING] analysis_id={analysis_id} stage=execute_pipeline_total duration_ms={execute_total_dur * 1000:.1f}")
        except Exception as error:
            for path in generated_paths:
                try:
                    self.storage_service.delete_file(
                        path, user_id=user_id, use_service_role=True
                    )
                except Exception:
                    pass
            # On failure, keep the last actual progress (status 'failed' is the
            # source of truth). Only stamp progress if it actually moved forward,
            # so we never overwrite a higher value already persisted.
            failure_data: Dict[str, Any] = {
                "status": "failed",
                "error_code": "AI_PIPELINE_ERROR",
                "error_message": "Analysis pipeline failed.",
                "gradcam_status": "failed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            if progress is not None and progress.percent > self._last_progress_percent(
                analysis_id, user_id
            ):
                failure_data["progress_percent"] = progress.percent
                if progress.last_step is not None:
                    failure_data["current_step"] = progress.last_step
            try:
                self.repository.update(
                    analysis_id=analysis_id,
                    user_id=user_id,
                    data=failure_data,
                    use_service_role=True,
                )
            except Exception as update_err:
                try:
                    logger.exception(
                        "Failed to update analysis status to failed for analysis_id=%s: %s",
                        analysis_id,
                        update_err,
                    )
                except Exception:
                    pass
            raise APIError("AI_PIPELINE_ERROR", "Analysis pipeline failed.", 500) from error
        finally:
            execute_total_dur = time.perf_counter() - execute_start
            print(f"[TIMING] analysis_id={analysis_id} stage=execute_pipeline_total duration_ms={execute_total_dur * 1000:.1f}")

    def _last_progress_percent(self, analysis_id: str, user_id: str) -> int:
        """Best-effort read of the stored progress_percent (0 when unknown)."""
        try:
            record = self.repository.get_by_id(
                analysis_id, user_id, use_service_role=True
            )
            value = (record or {}).get("progress_percent")
            return int(value) if value is not None else 0
        except Exception:
            return 0

    @staticmethod
    def _require_domain_accept(file_bytes: bytes) -> None:
        """Gate direct model-boundary calls on the domain ACCEPT requirement.

        ``run_segmentation`` and ``run_gradcam`` are callable outside the
        upload path, so they must enforce the same ACCEPT gate as
        ``create_analysis``. A ``REJECT`` or ``UNCERTAIN`` input stops here
        before any U-Net/TTA/Grad-CAM work, mirroring the upload boundary.
        """
        result = ColonoscopyDomainValidator().validate_bytes(file_bytes)
        if result.decision == DomainDecision.REJECT:
            raise APIError(
                "NOT_COLONOSCOPY_IMAGE",
                result.message or "Citra yang diunggah teridentifikasi bukan merupakan citra kolonoskopi saluran cerna.",
                400,
            )
        if result.decision == DomainDecision.UNCERTAIN:
            raise APIError(
                "UNCERTAIN_COLONOSCOPY_IMAGE",
                result.message or "Sistem tidak dapat memastikan citra yang diunggah merupakan citra kolonoskopi yang valid.",
                400,
            )

    @staticmethod
    def run_segmentation(file_bytes: bytes) -> SegmentationResult:
        """Expose the verified raw model boundary for the later AI lifecycle.

        TASK 10 intentionally does not persist AI assets or alter the API
        response; this hook keeps model execution out of Flask routes.
        Direct callers must pass a validated colonoscopy image (ACCEPT).
        """
        AnalysisService._require_domain_accept(file_bytes)
        try:
            with Image.open(io.BytesIO(file_bytes)) as image:
                return predict(image)
        except Exception as error:
            raise APIError("MODEL_INFERENCE_ERROR", "Model inference failed.", 500) from error

    @staticmethod
    def run_gradcam(file_bytes: bytes) -> GradCAMResult:
        """Expose the verified Grad-CAM boundary for later result integration.

        Direct callers must pass a validated colonoscopy image (ACCEPT).
        """
        AnalysisService._require_domain_accept(file_bytes)
        try:
            with Image.open(io.BytesIO(file_bytes)) as image:
                original = image.convert("RGB")
                tensor = prepare_image(original)
                return generate_gradcam(tensor, original_image=original)
        except Exception as error:
            raise APIError("GRADCAM_GENERATION_ERROR", "Grad-CAM generation failed.", 500) from error