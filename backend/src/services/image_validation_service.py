"""Validation of uploaded images before storage and analysis.

Extracted from ``analysis_service`` (refactoring stage 3) so that image
validation has a single responsibility. The analysis service keeps owning
orchestration (upload, persistence, queue) and delegates every validation step
to this service.

Three distinct layers are preserved exactly as before:
- technical validation (filenames, size, MIME, full decode, dimensions);
- heuristic colonoscopy domain validation (``ColonoscopyDomainValidator``);
- secondary LLM domain verification (Gemini gate, fail-closed).

Two domain-validation entry points exist and are intentionally kept separate
(design issue C, documented in the stage-3 report):
- ``validate_domain`` is called from the upload path (``create_analysis``) and
  respects the ``DOMAIN_VALIDATION_ENABLED`` configuration;
- ``require_domain_accept`` is the defensive gate used by direct model-boundary
  calls (``run_segmentation`` / ``run_gradcam``); it always constructs a fresh
  validator and does not consult configuration or the LLM gate.
"""
import io
import logging
import warnings
from typing import Any, Callable, Optional, Tuple

from PIL import Image

from src.core.errors import APIError

from ai.inference.domain_validator import ColonoscopyDomainValidator, DomainDecision

logger = logging.getLogger(__name__)


class ImageValidationService:
    """Validate uploaded images and decide whether they may be analyzed.

    All technical constants and the domain/LLM gates live here so the
    orchestration layer never duplicates validation logic.
    """

    ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png'}
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

    def __init__(
        self,
        domain_validator: Optional[ColonoscopyDomainValidator] = None,
        llm_validator: Optional[Callable[..., Any]] = None,
        llm_client: Optional[Any] = None,
        enforce_domain_validation: Optional[bool] = None,
        enforce_llm_validation: Optional[bool] = None,
    ) -> None:
        self.domain_validator = domain_validator or ColonoscopyDomainValidator()
        # ``None`` means "use the real validator" (resolved at call time).
        self._llm_validator = llm_validator
        self._llm_client = llm_client
        self._enforce_domain_validation = enforce_domain_validation
        self._enforce_llm_validation = enforce_llm_validation

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

    def validate_and_decode_image(self, file_storage) -> Tuple[bytes, str, str, int, int]:
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

    def validate_domain(
        self, file_bytes: bytes, analysis_id: str = "", user_id: str = ""
    ) -> None:
        """Heuristic colonoscopy domain gate used by the upload path.

        Raises APIError (NOT_COLONOSCOPY_IMAGE / UNCERTAIN_COLONOSCOPY_IMAGE)
        on REJECT / UNCERTAIN. Skipped entirely when domain validation is
        disabled by configuration.
        """
        if not self.is_domain_validation_enabled:
            return

        domain_result = self.domain_validator.validate_bytes(file_bytes)
        feature_summary = ", ".join(
            f"{k}={v:.4f}" for k, v in sorted(domain_result.metrics.items())
        )
        logger.info(
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

    def validate_llm(
        self,
        image_bytes: bytes,
        mime_type: str,
        analysis_id: str = "",
        user_id: str = "",
    ) -> None:
        """Secondary LLM domain verification (Gemini Gate), fail-closed.

        Only runs when LLM validation is enabled. REJECT raises
        NOT_COLONOSCOPY_IMAGE; ERROR/failure raises
        UNCERTAIN_COLONOSCOPY_IMAGE.
        """
        if not self.is_llm_validation_enabled:
            return

        from src.services.llm_image_validator import validate_with_llm, MSG_LLM_SERVICE_ERROR

        validator_fn = self._llm_validator or validate_with_llm
        model_name = "gemini-3.8-flash"
        min_conf = 0.80
        # Default sementara konsisten dengan Config/validate_with_llm (30 s);
        # nilai aktual di-override dari current_app.config di bawah.
        timeout_s = 30.0
        try:
            from flask import current_app
            model_name = current_app.config.get("LLM_VALIDATION_MODEL", model_name)
            min_conf = float(current_app.config.get("LLM_VALIDATION_MIN_CONF", min_conf))
            timeout_s = float(current_app.config.get("LLM_VALIDATION_TIMEOUT_S", timeout_s))
        except (ImportError, RuntimeError):
            pass

        llm_result = validator_fn(
            image_bytes=image_bytes,
            mime_type=mime_type,
            client=self._llm_client,
            model_name=model_name,
            min_confidence=min_conf,
            timeout_s=timeout_s,
        )

        logger.info(
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

    @staticmethod
    def require_domain_accept(file_bytes: bytes) -> None:
        """Gate direct model-boundary calls on the domain ACCEPT requirement.

        ``run_segmentation`` and ``run_gradcam`` are callable outside the
        upload path, so they must enforce the same ACCEPT gate as
        ``create_analysis``. A ``REJECT`` or ``UNCERTAIN`` input stops here
        before any U-Net/TTA/Grad-CAM work, mirroring the upload boundary.

        This path intentionally does NOT consult ``DOMAIN_VALIDATION_ENABLED``
        and does NOT run the LLM gate (unchanged from the pre-extraction code).
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
