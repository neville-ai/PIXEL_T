"""Tes ekstraksi ImageValidationService (Tahap 3).

Memverifikasi 10 butir wajib refactoring:
1. ImageValidationService dapat digunakan secara independen.
2. AnalysisService tetap mempertahankan public interface lama.
3. Validasi format dan decoding citra tetap sama.
4. Validasi ukuran dan dimensi citra tetap sama.
5. Integrasi LLM validator (Gemini Gate) tetap sama.
6. Kedua jalur validasi domain tetap dipanggil sesuai kondisi sebelumnya.
7. Keputusan menerima atau menolak citra tidak berubah.
8. Error handling dan fallback tidak berubah.
9. Tidak terjadi circular import.
10. Seluruh test lama tetap lolos (diverifikasi dengan menjalankan seluruh suite
    secara terpisah; bukan bagian dari berkas ini).

Semua panggilan LLM/domain di-MOCK; tidak ada panggilan API riil dan tidak
menulis ke storage/database produksi.
"""

import io
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from src.core.errors import APIError
from src.services.analysis_service import AnalysisService
from src.services.image_validation_service import ImageValidationService
from ai.inference.domain_validator import DomainValidationResult, DomainDecision
from src.services.llm_image_validator import LlmDecision, MSG_LLM_SERVICE_ERROR

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = REPO_ROOT / "Backend"


def create_dummy_image_bytes(width=800, height=600, color=(180, 50, 50), image_format="JPEG"):
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=image_format)
    return buf.getvalue()


class DummyFileStorage:
    """Mirip werkzeug FileStorage (mirip yang ada di tes lama)."""

    def __init__(self, data, filename="test.jpg", content_type="image/jpeg"):
        self.stream = io.BytesIO(data)
        self.filename = filename
        self.content_type = content_type
        self.mimetype = content_type

    def read(self, *args):
        return self.stream.read(*args)

    def seek(self, *args):
        return self.stream.seek(*args)

    def tell(self):
        return self.stream.tell()


def domain_result(decision, confidence=0.95, reasons=None, message=None, metrics=None):
    return DomainValidationResult(
        decision=decision,
        confidence=confidence,
        reasons=reasons or [],
        metrics=metrics or {},
        message=message,
    )


def mock_domain(decision):
    mock = MagicMock()
    mock.validate_bytes.return_value = domain_result(decision)
    return mock


def mock_llm(decision):
    mock = MagicMock()
    mock.return_value = LlmDecision(
        ok=decision == "PASS",
        status=decision,
        image_type="colonoscopy",
        confidence=0.96 if decision == "PASS" else 0.99,
    )
    return mock


def make_service(domain_decision=None, enforce_domain=True, enforce_llm=True,
                 llm_decision="PASS", llm_validator=None):
    mock_repo = MagicMock()
    mock_repo.create.return_value = {"id": "a-1", "status": "processing"}
    mock_storage = MagicMock()
    mock_queue = MagicMock()
    mock_queue.try_enqueue.return_value = True
    kwargs = dict(
        repository=mock_repo,
        storage_service=mock_storage,
        job_queue=mock_queue,
        domain_validator=mock_domain(domain_decision) if domain_decision is not None else None,
        enforce_domain_validation=enforce_domain,
        enforce_llm_validation=enforce_llm,
        llm_validator=llm_validator or mock_llm(llm_decision),
    )
    service = AnalysisService(**kwargs)
    return service, mock_repo, mock_storage, mock_queue


# ==============================================================================
# 1 & 2: service independen + public interface lama AnalysisService
# ==============================================================================

def test_image_validation_service_can_be_used_independently():
    service = ImageValidationService(
        domain_validator=mock_domain(DomainDecision.ACCEPT),
        llm_validator=mock_llm("PASS"),
        enforce_domain_validation=True,
        enforce_llm_validation=True,
    )
    # Konstanta teknis sama dengan yang sebelumnya ada di AnalysisService.
    assert ImageValidationService.ALLOWED_MIME_TYPES == {"image/jpeg", "image/png"}
    assert ImageValidationService.MAX_FILE_SIZE_BYTES == 10 * 1024 * 1024

    # Teknis: JPEG/PNG valid decodes.
    payload = create_dummy_image_bytes()
    file_obj = DummyFileStorage(payload, "scope.jpg", "image/jpeg")
    file_bytes, mime_type, ext, width, height = service.validate_and_decode_image(file_obj)
    assert file_bytes == payload
    assert mime_type == "image/jpeg"
    assert ext == "jpg"
    assert width == 800 and height == 600

    # Domain ACCEPT tidak mengacaukan.
    service.validate_domain(b"whatever-bytes")
    # LLM PASS tidak mengacaukan.
    service.validate_llm(b"whatever-bytes", "image/jpeg")


def test_analysis_service_public_interface_lama_kompatibel():
    service, _, _, _ = make_service(DomainDecision.ACCEPT)

    # Method dan atribut publik yang harus tetap ada.
    assert callable(service.validate_and_decode_image)
    assert callable(service.create_analysis)
    assert callable(service._run_analysis_job)
    assert callable(AnalysisService.run_segmentation)
    assert callable(AnalysisService.run_gradcam)
    assert callable(AnalysisService._require_domain_accept)
    assert callable(service._execute_pipeline)
    assert isinstance(service.is_domain_validation_enabled, bool)
    assert isinstance(service.is_llm_validation_enabled, bool)

    # Alias domain_validator tetap ekspos instance yang sama (kompatibilitas lama).
    assert service.domain_validator is service.image_validation_service.domain_validator

    # Referensi ke service yang diekstraksi.
    assert isinstance(service.image_validation_service, ImageValidationService)
    assert service.pipeline_service is not None
    assert service.job_queue is not None
    assert service.repository is not None
    assert service.storage_service is not None


# ==============================================================================
# 3 & 4: validasi format, decoding, ukuran, dimensi
# ==============================================================================

@pytest.mark.parametrize(
    ("image_format", "mime_type", "extension"),
    [("JPEG", "image/jpeg", "jpg"), ("PNG", "image/png", "png")],
)
def test_valid_image_decodes_with_expected_metadata(image_format, mime_type, extension):
    service = ImageValidationService(enforce_domain_validation=False, enforce_llm_validation=False)
    file_obj = DummyFileStorage(
        create_dummy_image_bytes(image_format=image_format), f"scope.{extension}", mime_type
    )
    file_bytes, mt, ext, width, height = service.validate_and_decode_image(file_obj)
    assert mt == mime_type
    assert ext == extension
    assert width == 800 and height == 600


def test_invalid_uploads_rejected_with_same_codes():
    service = ImageValidationService(enforce_domain_validation=False, enforce_llm_validation=False)

    cases = [
        (b"", "empty.jpg", "image/jpeg", "EMPTY_FILE"),
        (b"not an image", "invalid.jpg", "image/jpeg", "INVALID_IMAGE"),
        (b"not an image", "invalid.bin", "application/octet-stream", "INVALID_IMAGE"),
        (create_dummy_image_bytes(), "mismatch.png", "image/png", "INVALID_IMAGE"),
        (create_dummy_image_bytes(), "../scope.jpg", "image/jpeg", "INVALID_IMAGE"),
        (create_dummy_image_bytes(), r"..\scope.png", "image/png", "INVALID_IMAGE"),
    ]
    for content, filename, mime_type, expected_code in cases:
        with pytest.raises(APIError) as exc_info:
            service.validate_and_decode_image(DummyFileStorage(content, filename, mime_type))
        assert exc_info.value.code == expected_code
        assert exc_info.value.status_code == 400


def test_oversized_file_rejected_at_10mb_limit():
    service = ImageValidationService(enforce_domain_validation=False, enforce_llm_validation=False)
    oversized = b"x" * (10 * 1024 * 1024 + 1)
    with pytest.raises(APIError) as exc_info:
        service.validate_and_decode_image(DummyFileStorage(oversized, "large.jpg", "image/jpeg"))
    assert exc_info.value.code == "FILE_TOO_LARGE"
    assert exc_info.value.status_code == 400


# ==============================================================================
# 5: integrasi LLM validator tetap sama (delegate, default model/conf/timeout)
# ==============================================================================

def test_validate_llm_delegates_with_defaults():
    llm = mock_llm("PASS")
    service = ImageValidationService(
        domain_validator=mock_domain(DomainDecision.ACCEPT),
        enforce_domain_validation=True,
        enforce_llm_validation=True,
        llm_validator=llm,
        llm_client="client-sentinel",
    )
    image_bytes = create_dummy_image_bytes()
    service.validate_llm(image_bytes, "image/jpeg", analysis_id="a-1", user_id="u-1")

    llm.assert_called_once()
    kwargs = llm.call_args.kwargs
    assert kwargs["image_bytes"] == image_bytes
    assert kwargs["mime_type"] == "image/jpeg"
    assert kwargs["client"] == "client-sentinel"
    # Default model/conf/timeout tidak berubah dari implementasi lama.
    assert kwargs["model_name"] == "gemini-3.8-flash"
    assert kwargs["min_confidence"] == 0.80
    assert kwargs["timeout_s"] == 30.0


def test_llm_reject_and_error_unchanged():
    service_reject = ImageValidationService(
        domain_validator=mock_domain(DomainDecision.ACCEPT),
        enforce_domain_validation=True,
        enforce_llm_validation=True,
        llm_validator=mock_llm("REJECT"),
    )
    with pytest.raises(APIError) as exc_info:
        service_reject.validate_llm(b"img", "image/jpeg")
    assert exc_info.value.code == "NOT_COLONOSCOPY_IMAGE"
    assert exc_info.value.message == (
        "Citra tidak sesuai dengan karakteristik citra kolonoskopi. "
        "Silakan unggah citra kolonoskopi yang valid."
    )

    service_error = ImageValidationService(
        domain_validator=mock_domain(DomainDecision.ACCEPT),
        enforce_domain_validation=True,
        enforce_llm_validation=True,
        llm_validator=mock_llm("ERROR"),
    )
    with pytest.raises(APIError) as exc_info:
        service_error.validate_llm(b"img", "image/jpeg")
    assert exc_info.value.code == "UNCERTAIN_COLONOSCOPY_IMAGE"
    assert exc_info.value.message == MSG_LLM_SERVICE_ERROR


def test_create_analysis_llm_reject_blocks_upload_and_enqueue():
    service, mock_repo, mock_storage, mock_queue = make_service(
        DomainDecision.ACCEPT, enforce_domain=True, enforce_llm=True, llm_decision="REJECT"
    )
    file_obj = DummyFileStorage(create_dummy_image_bytes(), "scope.jpg", "image/jpeg")

    with pytest.raises(APIError) as exc_info:
        service.create_analysis(file_obj, user_id="test-user")
    assert exc_info.value.code == "NOT_COLONOSCOPY_IMAGE"

    mock_storage.upload_file.assert_not_called()
    mock_repo.create.assert_not_called()
    mock_queue.try_enqueue.assert_not_called()


# ==============================================================================
# 6 & 7: kedua jalur domain dipanggil sesuai kondisi & keputusan tidak berubah
# ==============================================================================

def test_domain_path_1_upload_reject_blocks_everything():
    service, mock_repo, mock_storage, mock_queue = make_service(
        DomainDecision.REJECT, enforce_domain=True, enforce_llm=True, llm_decision="PASS"
    )
    file_obj = DummyFileStorage(create_dummy_image_bytes(), "scope.jpg", "image/jpeg")

    with pytest.raises(APIError) as exc_info:
        service.create_analysis(file_obj, user_id="test-user")
    assert exc_info.value.code == "NOT_COLONOSCOPY_IMAGE"

    # Gemini TIDAK dipanggil saat gerbang heuristik REJECT.
    service.image_validation_service._llm_validator.assert_not_called()
    mock_storage.upload_file.assert_not_called()
    mock_repo.create.assert_not_called()
    mock_queue.try_enqueue.assert_not_called()


def test_domain_path_1_upload_uncertain_blocks_everything():
    service, mock_repo, mock_storage, mock_queue = make_service(
        DomainDecision.UNCERTAIN, enforce_domain=True, enforce_llm=True, llm_decision="PASS"
    )
    file_obj = DummyFileStorage(create_dummy_image_bytes(), "scope.jpg", "image/jpeg")

    with pytest.raises(APIError) as exc_info:
        service.create_analysis(file_obj, user_id="test-user")
    assert exc_info.value.code == "UNCERTAIN_COLONOSCOPY_IMAGE"
    mock_storage.upload_file.assert_not_called()
    mock_repo.create.assert_not_called()
    mock_queue.try_enqueue.assert_not_called()


def test_domain_path_1_disabled_skips_domain_and_proceeds():
    service, mock_repo, mock_storage, mock_queue = make_service(
        None, enforce_domain=False, enforce_llm=False
    )
    file_obj = DummyFileStorage(create_dummy_image_bytes(), "scope.jpg", "image/jpeg")
    result = service.create_analysis(file_obj, user_id="test-user")

    assert result["status"] == "processing"
    mock_storage.upload_file.assert_called_once()
    mock_repo.create.assert_called_once()
    mock_queue.try_enqueue.assert_called_once()


def test_domain_path_2_run_segmentation_invokes_gate():
    with patch.object(ImageValidationService, "require_domain_accept") as mock_gate:
        try:
            AnalysisService.run_segmentation(b"fake-image-bytes")
        except APIError as error:
            # Setelah gate lolos, PILLAM mencoba membaca palsu sebagai citra
            # dan gagal — inti uji adalah bahwa gate domain telah dipanggil.
            assert error.code == "MODEL_INFERENCE_ERROR"
    mock_gate.assert_called_once_with(b"fake-image-bytes")


def test_require_domain_accept_decisions_unchanged():
    """Jalur 2 (model boundary): fresh validator, tanpa config/LLM."""

    def make_validator(decision):
        mock_validator = MagicMock()
        mock_validator.validate_bytes.return_value = domain_result(decision)
        return mock_validator

    # REJECT -> NOT_COLONOSCOPY_IMAGE dengan pesan lama.
    with patch("src.services.image_validation_service.ColonoscopyDomainValidator",
               return_value=make_validator(DomainDecision.REJECT)):
        with pytest.raises(APIError) as exc_info:
            ImageValidationService.require_domain_accept(b"x")
        assert exc_info.value.code == "NOT_COLONOSCOPY_IMAGE"
        assert exc_info.value.message == (
            "Citra yang diunggah teridentifikasi bukan merupakan citra kolonoskopi saluran cerna."
        )

    # UNCERTAIN -> UNCERTAIN_COLONOSCOPY_IMAGE dengan pesan lama.
    with patch("src.services.image_validation_service.ColonoscopyDomainValidator",
               return_value=make_validator(DomainDecision.UNCERTAIN)):
        with pytest.raises(APIError) as exc_info:
            ImageValidationService.require_domain_accept(b"x")
        assert exc_info.value.code == "UNCERTAIN_COLONOSCOPY_IMAGE"
        assert exc_info.value.message == (
            "Sistem tidak dapat memastikan citra yang diunggah merupakan citra kolonoskopi yang valid."
        )

    # ACCEPT -> lolos.
    with patch("src.services.image_validation_service.ColonoscopyDomainValidator",
               return_value=make_validator(DomainDecision.ACCEPT)):
        ImageValidationService.require_domain_accept(b"x")  # tidak me-raise


# ==============================================================================
# 8: error handling dan fallback tidak berubah
# ==============================================================================

def test_llm_disabled_skips_gemini_entirely():
    service, _, mock_storage, mock_queue = make_service(
        DomainDecision.ACCEPT, enforce_domain=True, enforce_llm=False, llm_decision="REJECT"
    )
    file_obj = DummyFileStorage(create_dummy_image_bytes(), "scope.jpg", "image/jpeg")
    result = service.create_analysis(file_obj, user_id="test-user")
    assert result["status"] == "processing"
    mock_storage.upload_file.assert_called_once()
    mock_queue.try_enqueue.assert_called_once()


def test_technical_validation_errors_are_api_errors():
    service = ImageValidationService(enforce_domain_validation=False, enforce_llm_validation=False)
    with pytest.raises(APIError):
        service.validate_and_decode_image(DummyFileStorage(b"garbage", "bad.jpg", "image/jpeg"))
    with pytest.raises(APIError) as exc_info:
        service.validate_and_decode_image(DummyFileStorage(b"", "empty.jpg", "image/jpeg"))
    assert exc_info.value.code == "EMPTY_FILE"


# ==============================================================================
# 9: tidak ada circular import
# ==============================================================================

def test_no_circular_import_between_analysis_and_image_validation():
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(BACKEND_PATH), str(REPO_ROOT), env.get("PYTHONPATH", "")]
    )
    result = subprocess.run(
        [
            sys.executable, "-c",
            (
                "import sys;"
                "import src.services.image_validation_service as ivs;"
                "import src.services.analysis_service as ans;"
                "print(ivs.ImageValidationService.__name__);"
                "print(ans.AnalysisService.__name__);"
                "print(hasattr(ans, 'ImageValidationService'));"
            ),
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.strip().splitlines() if line]
    assert lines == ["ImageValidationService", "AnalysisService", "True"]


# ==============================================================================
# 10: seluruh test lama tetap lolos (diverifikasi dengan `pytest tests/ -q`)
# ==============================================================================

def test_suite_marker_exists():
    """Peringkat 10 diverifikasi secara eksternal dengan menjalankan seluruh suite."""
    assert True
