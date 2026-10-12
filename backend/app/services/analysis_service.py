import io
import re
import uuid
import warnings
from datetime import datetime, timezone
from typing import Callable, Optional, Dict, Any
from PIL import Image

from app.core.errors import APIError
from app.repositories.analysis_repository import AnalysisRepository
from app.services.storage_service import StorageService

from ai.inference.gradcam import GradCAMResult, generate_gradcam
from ai.config.model_config import MODEL_CONFIG
from ai.inference.pipeline import PipelineResult, run_pipeline
from ai.inference.segmentation import SegmentationResult, predict
from ai.inference.preprocessing import prepare_image


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
    ):
        self.repository = repository or AnalysisRepository()
        self.storage_service = storage_service or StorageService()
        self.pipeline_runner = pipeline_runner or run_pipeline

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
        """Run the complete synchronous analysis lifecycle for one upload."""
        if not user_id:
            raise APIError("UNAUTHORIZED", "Authenticated user ID is required.", 401)

        # 1. Validate and decode image
        file_bytes, mime_type, extension, width, height = self.validate_and_decode_image(
            file_storage
        )

        analysis_id = str(uuid.uuid4())
        safe_original_filename = file_storage.filename.strip()[:255]

        # 2. Generate ownership-aware storage path
        original_image_path = self.storage_service.generate_original_image_path(
            user_id=user_id, analysis_id=analysis_id, extension=extension
        )

        # 3. Upload to private Supabase Storage
        try:
            self.storage_service.upload_file(
                path=original_image_path,
                file_bytes=file_bytes,
                content_type=mime_type,
                user_id=user_id,
                use_service_role=True,
            )
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
            self.repository.create(
                user_id=user_id, data=record_data, use_service_role=True
            )
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

        generated_paths: list[str] = []
        try:
            pipeline_result = self.pipeline_runner(file_bytes, config=MODEL_CONFIG)
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
            for path, (asset, content_type) in generated_assets.items():
                self.storage_service.upload_file(
                    path=path,
                    file_bytes=asset,
                    content_type=content_type,
                    user_id=user_id,
                    use_service_role=True,
                )
                generated_paths.append(path)

            measurements = pipeline_result.measurements
            update_data = {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
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
            }
            updated = self.repository.update(
                analysis_id=analysis_id,
                user_id=user_id,
                data=update_data,
                use_service_role=True,
            )
            if updated is None:
                raise RuntimeError("analysis database update returned no record")
        except Exception as error:
            for path in generated_paths:
                try:
                    self.storage_service.delete_file(
                        path, user_id=user_id, use_service_role=True
                    )
                except Exception:
                    pass
            try:
                self.repository.update(
                    analysis_id=analysis_id,
                    user_id=user_id,
                    data={
                        "status": "failed",
                        "error_code": "AI_PIPELINE_ERROR",
                        "error_message": "Analysis pipeline failed.",
                        "gradcam_status": "failed",
                    },
                    use_service_role=True,
                )
            except Exception:
                pass
            raise APIError("AI_PIPELINE_ERROR", "Analysis pipeline failed.", 500) from error

        return {
            "analysis_id": analysis_id,
            "status": "completed",
        }

    def get_analysis(self, analysis_id: str, user_id: str) -> Dict[str, Any]:
        """Retrieve analysis details verifying user ownership.

        Returns persisted metadata and short-lived URLs for assets owned by the user.
        """
        if not user_id:
            raise APIError("UNAUTHORIZED", "Authenticated user ID is required.", 401)

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
            data["summary"] = {"text": record["summary_text"]}

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

    @staticmethod
    def run_segmentation(file_bytes: bytes) -> SegmentationResult:
        """Expose the verified raw model boundary for the later AI lifecycle.

        TASK 10 intentionally does not persist AI assets or alter the API
        response; this hook keeps model execution out of Flask routes.
        """
        try:
            with Image.open(io.BytesIO(file_bytes)) as image:
                return predict(image)
        except Exception as error:
            raise APIError("MODEL_INFERENCE_ERROR", "Model inference failed.", 500) from error

    @staticmethod
    def run_gradcam(file_bytes: bytes) -> GradCAMResult:
        """Expose the verified Grad-CAM boundary for later result integration."""
        try:
            with Image.open(io.BytesIO(file_bytes)) as image:
                original = image.convert("RGB")
                tensor = prepare_image(original)
                return generate_gradcam(tensor, original_image=original)
        except Exception as error:
            raise APIError("GRADCAM_GENERATION_ERROR", "Grad-CAM generation failed.", 500) from error
