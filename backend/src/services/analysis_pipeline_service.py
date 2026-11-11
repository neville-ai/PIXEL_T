"""Execution of the AI analysis pipeline for accepted analyses.

Extracted from ``analysis_service`` (refactoring stage 2) so that running the
pipeline and persisting its artifacts has a single responsibility.

The orchestration/service layer (``AnalysisService``) keeps owning the queue,
the analysis lifecycle (create/get/list/delete), image validation, and the
public interface used by callers; this service only runs the pipeline when
asked. No behavior is changed: the order of stages, every upload, every
progress write, every failure path, and every persisted field is identical to
the implementation that previously lived in ``AnalysisService._execute_pipeline``.
"""
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from src.core.errors import APIError
from src.repositories.analysis_repository import AnalysisRepository
from src.services.analysis_progress_service import AnalysisProgressReporter
from src.services.storage_service import StorageService

from ai.config.model_config import MODEL_CONFIG
from ai.inference.pipeline import PipelineResult

logger = logging.getLogger(__name__)

# Service-side phase vocabulary (English, matches APIContract current_step,
# whose documented example value is `inference`).
_STEP_UPLOADING_RESULTS = "uploading_results"
_STEP_COMPLETED = "completed"


class AnalysisDeletionCancelled(Exception):
    """Raised when a deletion tombstone cancels an in-progress pipeline.

    This is not an inference failure: the analysis record is being deleted, so
    the pipeline must stop at a safe stage boundary and must not persist any
    completion/failure state.
    """


class _WriteFencedRepository:
    """Proxy that runs repository updates through the deletion write-fence.

    Used for progress writes so a progress update cannot land after a deletion
    has acquired the fence. When the fence refuses the write, ``update``
    returns ``None`` (same shape as "record not found").
    """

    def __init__(self, repository, write_gate: Callable[[Callable[[], Any]], bool]):
        self._repository = repository
        self._write_gate = write_gate

    def update(self, **kwargs):
        holder: Dict[str, Any] = {}
        allowed = self._write_gate(
            lambda: holder.update(result=self._repository.update(**kwargs))
        )
        if not allowed:
            return None
        return holder.get("result")

    def __getattr__(self, name):
        return getattr(self._repository, name)


class AnalysisPipelineService:
    """Run the AI pipeline and persist its artifacts for one analysis.

    Responsibilities:
    - drive the pipeline runner (preprocessing, TTA inference, Grad-CAM),
      counting completed units for progress reporting;
    - upload all four generated artifacts sequentially;
    - persist the completed (or failed) record with ownership validation;
    - on partial failure, clean up uploaded artifacts and leave ``failed`` as
      the source of truth, carrying forward the last actual progress.

    Progress reporting is delegated to ``AnalysisProgressReporter`` (stage 1);
    its writes are best-effort and never affect the inference outcome.
    """

    def __init__(
        self,
        repository: Optional[AnalysisRepository] = None,
        storage_service: Optional[StorageService] = None,
    ) -> None:
        self.repository = repository or AnalysisRepository()
        self.storage_service = storage_service or StorageService()

    def execute(
        self,
        analysis_id: str,
        user_id: str,
        file_bytes: bytes,
        pipeline_runner: Callable[..., PipelineResult],
        total_units_provider: Callable[[], int],
        is_cancelled: Optional[Callable[[], bool]] = None,
        write_gate: Optional[Callable[[Callable[[], Any]], bool]] = None,
    ) -> None:
        """Run the pipeline and persist results for one accepted analysis.

        Executes in the background worker. On failure it persists
        ``status='failed'`` (with an explicit ``updated_at``) and re-raises so
        the caller decides how to surface the error. Ownership and service-role
        access mirror the original synchronous implementation.

        Isu B hooks (both optional and backward compatible):
        - ``is_cancelled``: cooperative cancellation checked at safe stage
          boundaries (before inference, between inference and uploads, before
          each artifact upload, and before the final persistence).
        - ``write_gate``: serialized final-persistence fence. The gate receives
          a zero-argument write callable and returns True when the write ran,
          False when a concurrent deletion refused it. All artifact uploads,
          progress writes, and completed/failed updates go through the gate.
        """
        def _check_cancelled() -> None:
            if is_cancelled is not None and is_cancelled():
                raise AnalysisDeletionCancelled(
                    f"analysis {analysis_id} was marked for deletion"
                )

        def _fenced(write: Callable[[], Any]) -> bool:
            if write_gate is None:
                write()
                return True
            return write_gate(write)

        generated_paths: List[str] = []
        # Progress reporter lives outside the try so the failure path can carry
        # forward the last *actual* progress (never 100%, never fabricated).
        progress: Optional[AnalysisProgressReporter] = None
        execute_start = time.perf_counter()
        try:
            _check_cancelled()
            # Progress reporter: counts completed units (phases + forward
            # passes) and writes throttled progress_percent/current_step. Its
            # writes are best-effort and never affect the inference outcome.
            # Units = 5 pipeline phases + 1 service-side artifact-upload phase
            # + one unit per TTA forward pass counted from the runtime config.
            total_units = total_units_provider()
            progress_repository = (
                _WriteFencedRepository(self.repository, write_gate)
                if write_gate is not None
                else self.repository
            )
            progress = AnalysisProgressReporter(
                repository=progress_repository,
                analysis_id=analysis_id,
                user_id=user_id,
                total_units=total_units,
            )
            pipeline_start = time.perf_counter()
            pipeline_result = pipeline_runner(
                file_bytes,
                config=MODEL_CONFIG,
                on_phase=progress.on_phase,
                on_pass=progress.on_pass,
                analysis_id=analysis_id,
            )
            pipeline_dur = time.perf_counter() - pipeline_start
            logger.info(f"[TIMING] analysis_id={analysis_id} stage=pipeline_ai duration_ms={pipeline_dur * 1000:.1f}")
            # Safe cancellation boundary: inference finished, no artifact has
            # been uploaded yet for this run.
            _check_cancelled()
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
            # Upload all 4 artifacts sequentially using StorageService
            # All must succeed before marking analysis as completed.
            # Isu B: cooperative cancellation checked before each artifact
            # upload; uploads are fenced through the deletion write-gate.
            upload_start = time.perf_counter()
            for path, (asset_bytes, content_type) in generated_assets.items():
                _check_cancelled()
                single_upload_start = time.perf_counter()
                uploaded = _fenced(
                    lambda p=path, b=asset_bytes, c=content_type, u=user_id: self.storage_service.upload_file(
                        path=p,
                        file_bytes=b,
                        content_type=c,
                        user_id=u,
                        use_service_role=True,
                    )
                )
                if not uploaded:
                    # Deletion owns the write-fence: stop uploading immediately
                    # and clean up whatever artifacts have been stored so far.
                    raise AnalysisDeletionCancelled(
                        f"analysis {analysis_id} was marked for deletion"
                    )
                generated_paths.append(path)
                single_upload_dur = time.perf_counter() - single_upload_start
                artifact_name = path.split("/")[-1]
                logger.info(f"[TIMING] analysis_id={analysis_id} stage=storage_upload artifact={artifact_name} duration_ms={single_upload_dur * 1000:.1f}")

            upload_total_dur = time.perf_counter() - upload_start
            logger.info(f"[TIMING] analysis_id={analysis_id} stage=storage_upload_total duration_ms={upload_total_dur * 1000:.1f}")

            # All 4 required artifacts are now stored: report the upload phase.
            _check_cancelled()
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
            updated: Any = None

            def _write_completed() -> None:
                nonlocal updated
                updated = self.repository.update(
                    analysis_id=analysis_id,
                    user_id=user_id,
                    data=update_data,
                    use_service_role=True,
                )

            if not _fenced(_write_completed):
                # Deletion owns the fence: persist nothing for this analysis.
                raise AnalysisDeletionCancelled(
                    f"analysis {analysis_id} was marked for deletion"
                )
            db_update_dur = time.perf_counter() - db_update_start
            logger.info(f"[TIMING] analysis_id={analysis_id} stage=db_update_completed duration_ms={db_update_dur * 1000:.1f}")
            if updated is None:
                raise RuntimeError("analysis database update returned no record")
            execute_total_dur = time.perf_counter() - execute_start
            logger.info(f"[TIMING] analysis_id={analysis_id} stage=execute_pipeline_total duration_ms={execute_total_dur * 1000:.1f}")
        except AnalysisDeletionCancelled as error:
            # Isu B: cancellation is not an inference failure. Clean up any
            # artifacts already uploaded, persist nothing, and let the worker
            # swallow the exception (the deletion owns the record).
            logger.info(f"[DELETION] pipeline cancelled for analysis_id={analysis_id}: {error}")
            for path in generated_paths:
                try:
                    self.storage_service.delete_file(
                        path, user_id=user_id, use_service_role=True
                    )
                except Exception:
                    pass
            raise
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

            def _write_failed() -> None:
                self.repository.update(
                    analysis_id=analysis_id,
                    user_id=user_id,
                    data=failure_data,
                    use_service_role=True,
                )

            try:
                if not _fenced(_write_failed):
                    # Deletion owns the write-fence: do not persist a failure
                    # state for an analysis that is being deleted.
                    logger.info(
                        f"[DELETION] failure status write refused for analysis_id={analysis_id}"
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
            logger.info(f"[TIMING] analysis_id={analysis_id} stage=execute_pipeline_total duration_ms={execute_total_dur * 1000:.1f}")

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
