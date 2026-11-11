import io
import logging
import re
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional, Dict, Any
from PIL import Image

logger = logging.getLogger(__name__)

from src.core.errors import APIError
from src.repositories.analysis_repository import AnalysisRepository
from src.services.storage_service import StorageService

# Re-exported for backward compatibility: historical callers import these from
# ``src.services.analysis_service`` (refactoring stages 1-2).
from src.services.analysis_progress_service import AnalysisProgressReporter
from src.services.analysis_queue_service import AnalysisJobQueue
from src.services.analysis_pipeline_service import (
    AnalysisDeletionCancelled,
    AnalysisPipelineService,
)
from src.services.image_validation_service import ImageValidationService

from ai.inference.gradcam import GradCAMResult, generate_gradcam
from ai.config.model_config import MODEL_CONFIG
from ai.inference.domain_validator import ColonoscopyDomainValidator
from ai.inference.pipeline import PipelineResult, run_pipeline
from ai.inference.segmentation import SegmentationResult, count_forward_passes, predict
from ai.inference.preprocessing import prepare_image


# A 'processing' record this process is NOT working on and that is older than
# this threshold is flagged (non-mutating) as potentially stuck for inspection.
# It never changes `status` and never marks a locally queued job stale, however
# long that job runs. Tunable; conservative to avoid false marks.
STALE_THRESHOLD = timedelta(minutes=15)


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


class AnalysisService:
    """Service handling analysis orchestration, secure image validation, and persistence.

    Strictly complies with TASK 08 boundaries:
    - Validates image dimensions, MIME type, and bytes via Pillow.
    - Persists original image to Supabase Storage.
    - Creates analysis record with status 'processing'.
    - Performs cleanup on partial failures.
    - NO AI inference, NO mock segmentation, NO Grad-CAM generation.
    """

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
        # Pipeline execution is delegated to its own service (stage 2).
        self.pipeline_service = AnalysisPipelineService(
            repository=self.repository,
            storage_service=self.storage_service,
        )
        # Image validation is delegated to its own service (stage 3). The
        # domain validator stays exposed on this service for backward
        # compatibility with historical callers/tests.
        self.image_validation_service = ImageValidationService(
            domain_validator=domain_validator,
            llm_validator=llm_validator,
            llm_client=llm_client,
            enforce_domain_validation=enforce_domain_validation,
            enforce_llm_validation=enforce_llm_validation,
        )
        self.domain_validator = self.image_validation_service.domain_validator
        # Deletion tombstone + write-fence (Isu B). The lock guards both the set
        # of analyses currently being deleted and the critical final
        # persistence operations of the pipeline, so deletion and final writes
        # cannot interleave (see ``_persist_if_allowed``).
        self._deletion_lock = threading.Lock()
        self._deletion_tombstones: set[str] = set()
        # Cooperative-cancellation requests live in their own set because they
        # have a different lifetime than the write-fence tombstone: the fence is
        # cleared once deletion reached a safe final state, while a cancellation
        # request must survive that point so an already-running job still stops
        # at its next stage boundary. It is cleared when the job leaves the
        # worker (see ``_run_analysis_job``), so it cannot accumulate.
        self._cancellation_requests: set[str] = set()
        # The queue runner defers to the bound method so tests can inject a
        # synchronous pipeline_runner and step the queue deterministically.
        self.job_queue = job_queue or AnalysisJobQueue(
            runner=lambda job: self._run_analysis_job(job),
            auto_start=auto_start_worker,
        )

    @property
    def is_domain_validation_enabled(self) -> bool:
        return self.image_validation_service.is_domain_validation_enabled

    @property
    def is_llm_validation_enabled(self) -> bool:
        return self.image_validation_service.is_llm_validation_enabled

    def validate_and_decode_image(self, file_storage) -> tuple[bytes, str, str, int, int]:
        """Delegate image validation/decoding to ``ImageValidationService``."""
        return self.image_validation_service.validate_and_decode_image(file_storage)

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

        logger.info(f"[CORRELATION] user_id={user_id} stage=create_analysis_service start")
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
        self.image_validation_service.validate_domain(
            file_bytes, analysis_id=analysis_id, user_id=user_id
        )

        # 2b. Secondary LLM domain verification (Gemini Gate).
        # Only runs if heuristic validation produced ACCEPT.
        # Fail-closed: REJECT raises NOT_COLONOSCOPY_IMAGE, ERROR/failure raises UNCERTAIN_COLONOSCOPY_IMAGE.
        self.image_validation_service.validate_llm(
            file_bytes, mime_type, analysis_id=analysis_id, user_id=user_id
        )

        logger.info(f"[CORRELATION] analysis_id={analysis_id} user_id={user_id} stage=create_analysis_service validation_done")

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
            logger.info(f"[CORRELATION] analysis_id={analysis_id} stage=storage_upload_original duration_ms={upload_dur:.1f}")
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
            logger.info(f"[CORRELATION] analysis_id={analysis_id} stage=db_create duration_ms={db_dur:.1f}")
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
        logger.info(f"[CORRELATION] analysis_id={analysis_id} stage=queue_enqueue duration_ms={queue_dur:.1f}")

        total_dur = (time.perf_counter() - start_time) * 1000
        logger.info(f"[CORRELATION] analysis_id={analysis_id} user_id={user_id} stage=create_analysis_service end duration_ms={total_dur:.1f}")

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

        logger.info(f"[CORRELATION] analysis_id={analysis_id} user_id={user_id} stage=get_analysis_service start")
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
        logger.info(f"[CORRELATION] analysis_id={analysis_id} user_id={user_id} stage=get_analysis_service end duration_ms={duration_ms:.1f}")

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

        Ownership is verified first. The write-fence tombstone is acquired
        before any destructive mutation so the pipeline cannot final-write
        results afterwards. The record is removed from the database before
        storage cleanup so a database failure leaves the stored assets intact
        and retryable. Storage cleanup is a required post-delete step; when it
        fails the tombstone is retained so the analysis can never receive new
        pipeline work again while its storage state is unresolved.
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

        # Isu B: acquire the write-fence before any destructive mutation so the
        # pipeline either refuses its final writes (if it has not written yet)
        # or the worker skips a queued job it may still pop.
        self._mark_for_deletion(analysis_id)

        try:
            deleted = self.repository.delete(
                analysis_id, user_id, use_service_role=True
            )
        except Exception as error:
            # Deletion aborted before any destructive step: keep the record
            # usable, do not purge the queue, do not touch storage, and release
            # the fence so the pipeline may proceed normally.
            self._clear_deletion_mark(analysis_id)
            raise APIError(
                "DATABASE_ERROR", "Failed to delete analysis record.", 500
            ) from error

        if not deleted:
            # Same as above: nothing destructive happened, release the fence.
            self._clear_deletion_mark(analysis_id)
            raise APIError(
                "ANALYSIS_NOT_FOUND", "Analysis not found or access denied.", 404
            )

        # The record is gone, so a still-waiting job can no longer produce a
        # usable result. Purge it only after the DB delete succeeded, so a DB
        # failure never leaves a purged job behind an intact "processing"
        # record.
        self.job_queue.purge_job(analysis_id)
        if self.job_queue.contains(analysis_id):
            # The job is already owned by the worker (purge cannot pull it out
            # of the active slot). Ask it to stop cooperatively at its next
            # safe stage boundary. This request outlives the write-fence
            # tombstone: the tombstone is released once deletion reaches a safe
            # final state, but the running job must still stop and persist
            # nothing. ``_run_analysis_job`` clears the request afterwards.
            self._request_cancellation(analysis_id)
            if not self.job_queue.contains(analysis_id):
                # The job finished between the request and this re-check, so no
                # worker remains to consume it. Drop it to keep the set
                # bounded.
                self._clear_cancellation(analysis_id)

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
                logger.warning(
                    "[DELETION] storage cleanup raised for analysis_id=%s; "
                    "record already removed",
                    analysis_id,
                    exc_info=True,
                )
                storage_cleanup_ok = False

        if storage_cleanup_ok:
            # Deletion reached a safe final state: the record is gone and no
            # storage objects were left behind. Release the fence.
            self._clear_deletion_mark(analysis_id)
        else:
            # Residual risk (DECISION A): orphaned storage objects may remain.
            # They are unreachable via the API (record deleted, paths are
            # ownership-scoped). No resurrection is attempted: re-inserting
            # the record could produce a more inconsistent state.
            #
            # The tombstone is *retained* on purpose: this analysis must never
            # accept new pipeline work while its storage state is unresolved,
            # and there is deliberately no finally/general cleanup that clears
            # the mark on this path.
            logger.warning(
                "[DELETION] storage cleanup incomplete for analysis_id=%s; "
                "tombstone retained",
                analysis_id,
            )

        return True

    def _run_analysis_job(self, job: Dict[str, Any]) -> None:
        """Background worker entry point: run the pipeline, swallow the error.

        The failure is already persisted as status='failed' by
        ``_execute_pipeline``; there is no HTTP caller to respond to, so the
        terminal APIError is intentionally not re-raised here.
        """
        analysis_id = job.get("analysis_id", "unknown")
        try:
            if self.is_cancelled_for_deletion(analysis_id):
                # Isu B: a delete may land between enqueue and dequeue. The
                # purge normally removes waiting jobs, but if the worker
                # already popped this one, honor the cancellation and skip the
                # pipeline entirely.
                logger.info(
                    f"[DELETION] skipping pipeline for cancelled analysis_id={analysis_id}"
                )
                return
            self._execute_pipeline(
                analysis_id=job["analysis_id"],
                user_id=job["user_id"],
                file_bytes=job["file_bytes"],
            )
        except AnalysisDeletionCancelled as exc:
            # Cooperative cancellation is a lifecycle event, not a pipeline
            # failure: the deletion owns the record and nothing was persisted.
            logger.info(
                f"[DELETION] pipeline stopped for analysis_id={analysis_id}: {exc}"
            )
        except Exception as exc:
            # Log the exception with traceback for debugging before swallowing
            logger.error(
                f"[ERROR] _run_analysis_job failed for analysis_id={analysis_id}: {exc}",
                exc_info=True,
            )
        finally:
            # Isu B: the cooperative-cancellation request only needs to survive
            # while this job is using the worker; drop it once the job stops so
            # the request set cannot accumulate across deletions.
            self._clear_cancellation(analysis_id)

    def _execute_pipeline(self, analysis_id: str, user_id: str, file_bytes: bytes) -> None:
        """Delegate AI pipeline execution to ``AnalysisPipelineService``.

        Kept on the orchestration layer so the queue worker and existing
        callers keep their entry point, while the execution itself lives in
        the extracted pipeline service. ``pipeline_runner`` and the
        total-unit counter are resolved at call time so injected runners and
        monkeypatched counters keep working exactly as before.
        """
        self.pipeline_service.execute(
            analysis_id=analysis_id,
            user_id=user_id,
            file_bytes=file_bytes,
            pipeline_runner=self.pipeline_runner,
            total_units_provider=lambda: 6 + count_forward_passes(MODEL_CONFIG),
            # Isu B: cooperative cancellation + write-fence hooks.
            is_cancelled=lambda: self.is_cancelled_for_deletion(analysis_id),
            write_gate=lambda write: self._persist_if_allowed(analysis_id, write),
        )

    # ------------------------------------------------------------------
    # Deletion tombstone + write-fence (Isu B — Tahap 6 implementation)
    # ------------------------------------------------------------------
    def is_marked_for_deletion(self, analysis_id: str) -> bool:
        """Return True when this analysis is flagged for deletion.

        Thread-safe read of the in-memory tombstone set.
        """
        with self._deletion_lock:
            return analysis_id in self._deletion_tombstones

    def _mark_for_deletion(self, analysis_id: str) -> None:
        """Mark an analysis for deletion (write-fence acquisition).

        Called by ``delete_analysis`` before any destructive mutation so the
        pipeline can no longer final-write results for this analysis.
        """
        with self._deletion_lock:
            self._deletion_tombstones.add(analysis_id)

    def _clear_deletion_mark(self, analysis_id: str) -> None:
        """Clear a deletion mark once the deletion reached a safe final state."""
        with self._deletion_lock:
            self._deletion_tombstones.discard(analysis_id)

    def _request_cancellation(self, analysis_id: str) -> None:
        """Request cooperative cancellation for a running (active) job."""
        with self._deletion_lock:
            self._cancellation_requests.add(analysis_id)

    def _clear_cancellation(self, analysis_id: str) -> None:
        """Drop a cooperative-cancellation request once its job has finished."""
        with self._deletion_lock:
            self._cancellation_requests.discard(analysis_id)

    def is_cancelled_for_deletion(self, analysis_id: str) -> bool:
        """True when this analysis is being deleted and must not proceed.

        Combines the write-fence tombstone (already acquired by a deletion
        that may still be running) with the cooperative-cancellation request.
        """
        with self._deletion_lock:
            return (
                analysis_id in self._deletion_tombstones
                or analysis_id in self._cancellation_requests
            )

    def _persist_if_allowed(self, analysis_id: str, write: Callable[[], Any]) -> bool:
        """Run a persistence write only while the analysis is not being deleted.

        The tombstone check and the write happen under the same lock that
        ``_mark_for_deletion`` uses, so a concurrent delete either:

        - acquires the lock first, sets the tombstone, releases, then removes
          the record → this write is refused; or
        - runs this write first, releases, then the delete marks the tombstone
          and removes the record → the record is gone afterwards anyway, so no
          resurrection can occur.

        Returns True when the write was executed, False when refused.
        """
        with self._deletion_lock:
            if analysis_id in self._deletion_tombstones:
                return False
            write()
            return True

    @staticmethod
    def _require_domain_accept(file_bytes: bytes) -> None:
        """Gate direct model-boundary calls on the domain ACCEPT requirement.

        ``run_segmentation`` and ``run_gradcam`` are callable outside the
        upload path, so they must enforce the same ACCEPT gate as
        ``create_analysis``. A ``REJECT`` or ``UNCERTAIN`` input stops here
        before any U-Net/TTA/Grad-CAM work, mirroring the upload boundary.

        Delegates to ``ImageValidationService.require_domain_accept`` (stage 3);
        behavior is unchanged (fresh validator, no config/LLM consultation).
        """
        ImageValidationService.require_domain_accept(file_bytes)

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