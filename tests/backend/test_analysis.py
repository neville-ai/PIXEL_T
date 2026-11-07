import io
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PIL import Image

from app import create_app
from app.core.config import TestingConfig
from app.services.analysis_service import AnalysisService
from app.services.storage_service import StorageService
import app.routes.analysis as analysis_routes
import app.core.auth as auth_module


class FakeRepository:
    def __init__(self, fail_create=False):
        self.records = {}
        self.create_calls = []
        self.delete_calls = []
        self.fail_create = fail_create

    def create(self, user_id, data, use_service_role=False):
        self.create_calls.append((user_id, data, use_service_role))
        if self.fail_create:
            raise RuntimeError("private database detail")
        self.records[data["id"]] = dict(data)
        return data

    def get_by_id(self, analysis_id, user_id, use_service_role=False):
        record = self.records.get(analysis_id)
        if record and record["user_id"] == user_id:
            return record
        return None

    def update(self, analysis_id, user_id, data, use_service_role=False):
        record = self.records.get(analysis_id)
        if not record or record["user_id"] != user_id:
            return None
        record.update(data)
        return record

    def delete(self, analysis_id, user_id, use_service_role=False):
        self.delete_calls.append((analysis_id, user_id, use_service_role))
        record = self.records.get(analysis_id)
        if record and record["user_id"] == user_id:
            del self.records[analysis_id]
            return True
        return False


class FakeStorage:
    def __init__(self, fail_upload=False):
        self.paths = []
        self.deleted_paths = []
        self.signed_paths = []
        self.fail_upload = fail_upload

    def generate_original_image_path(self, user_id, analysis_id, extension):
        return StorageService().generate_original_image_path(user_id, analysis_id, extension)

    def upload_file(self, path, file_bytes, content_type, user_id, use_service_role=False):
        self.paths.append((path, file_bytes, content_type, user_id, use_service_role))
        if self.fail_upload:
            raise RuntimeError("private storage detail")
        return path

    def delete_file(self, path, user_id, use_service_role=False):
        self.deleted_paths.append((path, user_id, use_service_role))
        return True

    def create_signed_url(self, path, expires_in, user_id, use_service_role=False):
        self.signed_paths.append((path, expires_in, user_id, use_service_role))
        return f"signed://temporary/{path}"

    def generate_binary_mask_path(self, user_id, analysis_id):
        return StorageService().generate_binary_mask_path(user_id, analysis_id)

    def generate_segmentation_overlay_path(self, user_id, analysis_id):
        return StorageService().generate_segmentation_overlay_path(user_id, analysis_id)

    def generate_gradcam_heatmap_path(self, user_id, analysis_id):
        return StorageService().generate_gradcam_heatmap_path(user_id, analysis_id)

    def generate_gradcam_overlay_path(self, user_id, analysis_id):
        return StorageService().generate_gradcam_overlay_path(user_id, analysis_id)


def image_bytes(image_format):
    stream = io.BytesIO()
    Image.new("RGB", (23, 17), color=(20, 80, 120)).save(stream, format=image_format)
    return stream.getvalue()


def pipeline_result():
    png = image_bytes("PNG")
    return SimpleNamespace(
        binary_mask_png=png,
        segmentation_overlay_png=png,
        gradcam_heatmap_png=png,
        gradcam_overlay_png=png,
        measurements={
            "segmentation_status": "detected",
            "area_pixels": 42,
            "area_ratio": 42 / (23 * 17),
            "bounding_width_pixels": 7,
            "bounding_height_pixels": 6,
        },
        summary_text="Persisted summary.",
        gradcam=SimpleNamespace(
            target_layer="decoder.blocks.4.conv2.0",
            target_objective="mean selected segmentation logit over target mask",
        ),
    )


@pytest.fixture
def analysis_client(client, monkeypatch):
    monkeypatch.setattr(auth_module, "is_supabase_configured", lambda: True)
    auth_client = MagicMock()
    auth_client.auth.get_user.side_effect = lambda token: SimpleNamespace(
        user=SimpleNamespace(id=token.removesuffix("-token"), email=None, role="authenticated")
    )
    monkeypatch.setattr(auth_module, "get_supabase_client", lambda **kwargs: auth_client)
    # Simulate approved doctor role for require_approved_doctor decorator
    monkeypatch.setattr(
        auth_module,
        "_get_user_role_and_status",
        lambda user_id: {"role": "doctor", "account_status": "approved"},
    )
    return client


@pytest.fixture
def analysis_dependencies(monkeypatch):
    repository = FakeRepository()
    storage = FakeStorage()
    service = AnalysisService(
        repository=repository,
        storage_service=storage,
        pipeline_runner=lambda file_bytes, config, **kwargs: pipeline_result(),
        # Deterministic: jobs only run when the test steps the queue via
        # service.job_queue.drain_one(), never on a background thread.
        auto_start_worker=False,
    )
    monkeypatch.setattr(analysis_routes.controller, "service", service)
    return repository, storage, service


def auth_headers(user_id="user-a"):
    return {"Authorization": f"Bearer {user_id}-token"}


def upload(client, data, filename="scope.jpg", mime_type="image/jpeg", user_id="user-a"):
    return client.post(
        "/api/analysis",
        data={"image": (io.BytesIO(data), filename, mime_type)},
        headers=auth_headers(user_id),
        content_type="multipart/form-data",
    )


def test_unauthorized_post_is_rejected(client):
    response = client.post("/api/analysis")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_missing_file_is_rejected(analysis_client, analysis_dependencies):
    response = analysis_client.post("/api/analysis", headers=auth_headers())
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MISSING_FILE"


def test_unauthorized_get_is_rejected(client):
    response = client.get("/api/analysis/analysis-id")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize(
    ("content", "filename", "mime_type"),
    [
        (b"", "empty.jpg", "image/jpeg"),
        (b"not an image", "invalid.jpg", "image/jpeg"),
        (b"not an image", "invalid.bin", "application/octet-stream"),
        (image_bytes("JPEG"), "mismatch.png", "image/png"),
        (image_bytes("JPEG"), "../scope.jpg", "image/jpeg"),
        (image_bytes("PNG"), r"..\scope.png", "image/png"),
    ],
    ids=["empty", "malformed", "unsupported-mime", "mime-mismatch", "posix-traversal", "windows-traversal"],
)
def test_invalid_uploads_are_rejected(
    analysis_client, analysis_dependencies, content, filename, mime_type
):
    response = upload(analysis_client, content, filename, mime_type)
    assert response.status_code == 400
    assert response.get_json()["success"] is False
    assert response.get_json()["error"]["code"] in {
        "EMPTY_FILE",
        "INVALID_IMAGE",
    }


def test_oversized_file_is_rejected(analysis_client, analysis_dependencies):
    response = upload(
        analysis_client,
        b"x" * (10 * 1024 * 1024 + 1),
        "large.jpg",
        "image/jpeg",
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "FILE_TOO_LARGE"


def test_oversized_request_body_uses_standard_error_envelope(analysis_client):
    response = upload(
        analysis_client,
        b"x" * (12 * 1024 * 1024),
        "large.jpg",
        "image/jpeg",
    )
    assert response.status_code == 413
    assert response.get_json()["error"]["code"] == "FILE_TOO_LARGE"


@pytest.mark.parametrize(
    ("image_format", "mime_type", "extension"),
    [("JPEG", "image/jpeg", "jpg"), ("PNG", "image/png", "png")],
)
def test_valid_upload_persists_processing_record_and_metadata(
    analysis_client, analysis_dependencies, image_format, mime_type, extension
):
    repository, storage, _service = analysis_dependencies
    response = upload(
        analysis_client,
        image_bytes(image_format),
        f"scope.{extension}",
        mime_type,
    )

    assert response.status_code == 202
    data = response.get_json()
    assert data["success"] is True
    analysis_id = data["data"]["analysis_id"]
    assert data["data"]["status"] == "processing"

    user_id, record, service_role = repository.create_calls[0]
    assert user_id == "user-a"
    assert service_role is True
    assert record["status"] == "processing"
    assert record["original_filename"] == f"scope.{extension}"
    assert record["original_mime_type"] == mime_type
    assert record["original_width"] == 23
    assert record["original_height"] == 17
    assert record["original_image_path"] == (
        f"analysis/user-a/{analysis_id}/original/input.{extension}"
    )
    assert storage.paths[0][2:] == (mime_type, "user-a", True)
    assert set(record).isdisjoint(
        {
            "binary_mask_path",
            "segmentation_overlay_path",
            "segmentation_status",
            "area_pixels",
            "area_ratio",
            "bounding_width_pixels",
            "bounding_height_pixels",
            "gradcam_heatmap_path",
            "gradcam_overlay_path",
            "gradcam_target_layer",
            "summary_text",
        }
    )


def test_cross_user_get_is_hidden_as_not_found(analysis_client, analysis_dependencies):
    _, storage, _service = analysis_dependencies
    response = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = response.get_json()["data"]["analysis_id"]

    detail = analysis_client.get(
        f"/api/analysis/{analysis_id}", headers=auth_headers("user-b")
    )
    assert detail.status_code == 404
    assert detail.get_json()["error"]["code"] == "ANALYSIS_NOT_FOUND"
    assert storage.signed_paths == []


def test_nonexistent_analysis_returns_not_found(analysis_client, analysis_dependencies):
    detail = analysis_client.get(
        "/api/analysis/nonexistent-id", headers=auth_headers()
    )
    assert detail.status_code == 404
    assert detail.get_json() == {
        "success": False,
        "error": {
            "code": "ANALYSIS_NOT_FOUND",
            "message": "Analysis not found or access denied.",
        },
    }


def test_get_returns_only_processing_metadata(analysis_client, analysis_dependencies):
    _repository, _storage, service = analysis_dependencies
    response = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = response.get_json()["data"]["analysis_id"]
    # Step the background queue so the 'processing' record completes.
    assert service.job_queue.drain_one() is True

    detail = analysis_client.get(
        f"/api/analysis/{analysis_id}", headers=auth_headers()
    )
    assert detail.status_code == 200
    data = detail.get_json()["data"]
    assert data["analysis"]["status"] == "completed"
    assert data["analysis"]["original_filename"] == "scope.jpg"
    assert data["input"]["original_image_url"].startswith(
        "signed://temporary/analysis/user-a/"
    )
    assert data["input"]["width"] == 23
    assert data["input"]["height"] == 17
    assert data["model_analysis"]["segmentation_status"] == "detected"
    assert "segmentation" in data
    assert "gradcam" in data
    assert "confidence" not in data


def test_completed_analysis_returns_only_persisted_assets_and_metadata(
    analysis_client, analysis_dependencies
):
    repository, storage, service = analysis_dependencies
    created = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = created.get_json()["data"]["analysis_id"]
    # Run the enqueued job so the generated asset paths are persisted.
    assert service.job_queue.drain_one() is True
    record = repository.records[analysis_id]
    record.update(
        {
            "status": "completed",
            "completed_at": "2026-09-30T12:00:00Z",
            "segmentation_overlay_path": (
                f"analysis/user-a/{analysis_id}/segmentation/overlay.png"
            ),
            "gradcam_heatmap_path": f"analysis/user-a/{analysis_id}/gradcam/heatmap.png",
            "segmentation_status": "detected",
            "area_pixels": 42,
            "model_version": "runtime-version-1",
            "summary_text": "Persisted summary text.",
        }
    )

    detail = analysis_client.get(
        f"/api/analysis/{analysis_id}", headers=auth_headers()
    )
    assert detail.status_code == 200
    payload = detail.get_json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["analysis"]["status"] == "completed"
    assert data["input"]["original_image_url"].startswith(
        "signed://temporary/analysis/user-a/"
    )
    assert data["segmentation"]["binary_mask_url"] == record["binary_mask_path"].replace(
        "analysis/user-a/", "signed://temporary/analysis/user-a/", 1
    )
    assert data["segmentation"]["overlay_url"] == record["segmentation_overlay_path"].replace(
        "analysis/user-a/", "signed://temporary/analysis/user-a/", 1
    )
    assert data["gradcam"]["heatmap_url"].endswith("/gradcam/heatmap.png")
    assert data["gradcam"]["overlay_url"].endswith("/gradcam/overlay.png")
    assert data["model_analysis"] == {
        "segmentation_status": "detected",
        "area_pixels": 42,
        "area_ratio": 42 / (23 * 17),
        "bounding_width_pixels": 7,
        "bounding_height_pixels": 6,
    }
    assert data["model"]["version"] == "runtime-version-1"
    assert data["model"]["architecture"] == "UNet"
    assert data["model"]["threshold"] == 0.55
    assert data["model"]["input_size"] == 512
    assert data["model"]["tta_enabled"] is True
    assert data["model"]["postprocessing_enabled"] is True
    assert data["model"]["gradcam_target_layer"] == "decoder.blocks.4.conv2.0"
    assert data["model"]["gradcam_status"] == "completed"
    assert data["model"]["checkpoint_sha256"] == (
        "46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581"
    )
    assert data["summary"] == {"text": "Persisted summary text."}
    assert "original_image_path" not in data["analysis"]
    assert record["original_image_path"] in data["input"]["original_image_url"]
    assert all(path.startswith("analysis/user-a/") for path, *_ in storage.signed_paths)


def test_failed_analysis_hides_raw_failure_details(
    analysis_client, analysis_dependencies
):
    repository, _, _service = analysis_dependencies
    created = upload(analysis_client, image_bytes("PNG"), "scope.png", "image/png")
    analysis_id = created.get_json()["data"]["analysis_id"]
    repository.records[analysis_id].update(
        {
            "status": "failed",
            "error_code": "DATABASE_ERROR",
            "error_message": "C:\\private\\server\\traceback.log",
        }
    )

    detail = analysis_client.get(
        f"/api/analysis/{analysis_id}", headers=auth_headers()
    )
    assert detail.status_code == 200
    data = detail.get_json()["data"]["analysis"]
    assert data["status"] == "failed"
    assert data["error_code"] == "ANALYSIS_FAILED"
    assert data["error_message"] == "Analysis could not be completed. Please try again."
    assert "private" not in detail.get_data(as_text=True)


def test_storage_failure_cleans_attempted_object_without_creating_record(
    analysis_client, monkeypatch
):
    repository = FakeRepository()
    storage = FakeStorage(fail_upload=True)
    monkeypatch.setattr(
        analysis_routes.controller,
        "service",
        AnalysisService(
            repository=repository,
            storage_service=storage,
            pipeline_runner=lambda file_bytes, config, **kwargs: pipeline_result(),
        ),
    )

    response = upload(analysis_client, image_bytes("JPEG"))
    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == "STORAGE_ERROR"
    assert "private storage detail" not in response.get_data(as_text=True)
    assert repository.create_calls == []
    path, _, _, user_id, _ = storage.paths[0]
    assert storage.deleted_paths == [(path, user_id, True)]


def test_database_failure_cleans_uploaded_object_and_scoped_record(
    analysis_client, monkeypatch
):
    repository = FakeRepository(fail_create=True)
    storage = FakeStorage()
    monkeypatch.setattr(
        analysis_routes.controller,
        "service",
        AnalysisService(repository=repository, storage_service=storage),
    )

    response = upload(analysis_client, image_bytes("PNG"), "scope.png", "image/png")
    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == "DATABASE_ERROR"
    assert "private database detail" not in response.get_data(as_text=True)
    path, _, _, user_id, _ = storage.paths[0]
    analysis_id = repository.create_calls[0][1]["id"]
    assert storage.deleted_paths == [(path, user_id, True)]
    assert repository.delete_calls == [(analysis_id, user_id, True)]


def test_storage_path_generator_rejects_traversal_and_foreign_paths():
    service = StorageService()
    with pytest.raises(ValueError):
        service.generate_asset_path("user-a", "analysis-a", "original", "../secret.jpg")
    with pytest.raises(ValueError):
        service.generate_asset_path("user-a", "analysis-a", "original", r"..\secret.jpg")
    assert not service.validate_path_ownership(
        "analysis/user-a/../user-b/original/input.jpg", "user-a"
    )
    assert not service.validate_path_ownership(
        "analysis/user-ab/analysis-a/original/input.jpg", "user-a"
    )


def test_storage_migration_keeps_bucket_private_and_checks_user_folder():
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[2]
        / "database"
        / "migrations"
        / "001_create_analyses_and_storage.sql"
    ).read_text(encoding="utf-8")
    assert "'analysis-assets',\n    'analysis-assets',\n    false" in migration
    assert "(storage.foldername(name))[2] = auth.uid()::text" in migration


def test_processing_rows_do_not_get_unavailable_model_defaults():
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[2]
        / "database"
        / "migrations"
        / "001_create_analyses_and_storage.sql"
    ).read_text(encoding="utf-8")
    assert "gradcam_method VARCHAR(50)," in migration
    assert "model_architecture VARCHAR(100)," in migration
    assert "tta_enabled BOOLEAN," in migration
    assert "postprocessing_enabled BOOLEAN," in migration


def test_two_phase_accept_returns_id_then_completes_on_drain(
    analysis_client, analysis_dependencies
):
    """POST returns 202 + stable id while the record is still 'processing',
    GET reads 'processing' before the worker runs, and 'completed' after it."""
    _repository, _storage, service = analysis_dependencies
    created = upload(analysis_client, image_bytes("JPEG"))
    assert created.status_code == 202
    payload = created.get_json()
    assert payload["success"] is True
    analysis_id = payload["data"]["analysis_id"]
    assert payload["data"]["status"] == "processing"

    # Before the pipeline runs, GET reports processing (no progress fields yet).
    detail = analysis_client.get(
        f"/api/analysis/{analysis_id}", headers=auth_headers()
    )
    analysis = detail.get_json()["data"]["analysis"]
    assert analysis["status"] == "processing"
    assert "current_step" not in analysis
    assert "progress_percent" not in analysis

    # Deterministically step the queue: the job now completes.
    assert service.job_queue.drain_one() is True

    detail = analysis_client.get(
        f"/api/analysis/{analysis_id}", headers=auth_headers()
    )
    analysis = detail.get_json()["data"]["analysis"]
    assert analysis["status"] == "completed"
    assert analysis["completed_at"] is not None


def test_pipeline_failure_marks_record_failed_and_masks_details(
    analysis_client, monkeypatch
):
    def _boom(file_bytes, config, **kwargs):
        raise RuntimeError("private pipeline traceback")

    repository = FakeRepository()
    storage = FakeStorage()
    service = AnalysisService(
        repository=repository,
        storage_service=storage,
        pipeline_runner=_boom,
        auto_start_worker=False,
    )
    monkeypatch.setattr(analysis_routes.controller, "service", service)

    created = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = created.get_json()["data"]["analysis_id"]
    assert service.job_queue.drain_one() is True

    record = repository.records[analysis_id]
    assert record["status"] == "failed"
    assert record["error_code"] == "AI_PIPELINE_ERROR"
    assert record["gradcam_status"] == "failed"
    assert record["updated_at"] is not None

    detail = analysis_client.get(
        f"/api/analysis/{analysis_id}", headers=auth_headers()
    )
    analysis = detail.get_json()["data"]["analysis"]
    assert analysis["status"] == "failed"
    assert analysis["error_code"] == "ANALYSIS_FAILED"
    assert "private" not in detail.get_data(as_text=True)


def test_queue_full_returns_429_and_leaves_no_misleading_record(
    analysis_client, analysis_dependencies
):
    repository, storage, service = analysis_dependencies
    capacity = service.job_queue.capacity
    accepted_ids = []
    for _ in range(capacity):
        response = upload(analysis_client, image_bytes("JPEG"))
        assert response.status_code == 202
        accepted_ids.append(response.get_json()["data"]["analysis_id"])
    assert service.job_queue.pending_count() == capacity

    rejected = upload(analysis_client, image_bytes("JPEG"))
    assert rejected.status_code == 429
    assert rejected.get_json()["error"]["code"] == "QUEUE_FULL"

    # Enqueue-failure compensation: the rejected record must not linger as a
    # misleading 'processing' row, and its uploaded original is cleaned up.
    rejected_id = repository.create_calls[-1][1]["id"]
    assert rejected_id not in repository.records
    assert all(record_id in repository.records for record_id in accepted_ids)
    rejected_original = repository.create_calls[-1][1]["original_image_path"]
    assert (rejected_original, "user-a", True) in storage.deleted_paths


def test_job_is_executed_exactly_once(analysis_client, analysis_dependencies):
    _repository, _storage, service = analysis_dependencies
    calls = []

    def _counting_pipeline(file_bytes, config, **kwargs):
        calls.append(1)
        return pipeline_result()

    service.pipeline_runner = _counting_pipeline
    created = upload(analysis_client, image_bytes("JPEG"))
    assert created.status_code == 202

    assert service.job_queue.drain_one() is True
    assert calls == [1]
    # Draining again finds an empty queue and does not re-run the job.
    assert service.job_queue.drain_one() is False
    assert calls == [1]


def test_background_job_preserves_owner_and_completes(analysis_client, analysis_dependencies):
    repository, _storage, service = analysis_dependencies
    created = upload(analysis_client, image_bytes("JPEG"), user_id="user-a")
    analysis_id = created.get_json()["data"]["analysis_id"]

    assert service.job_queue.drain_one() is True
    record = repository.records[analysis_id]
    assert record["user_id"] == "user-a"
    assert record["status"] == "completed"
    assert record["binary_mask_path"].startswith("analysis/user-a/")
    # Cross-user reads remain hidden as 404 (isolation preserved).
    detail = analysis_client.get(
        f"/api/analysis/{analysis_id}", headers=auth_headers("user-b")
    )
    assert detail.status_code == 404


def test_nullable_progress_fields_surface_when_set_and_absent_when_null(
    analysis_client, analysis_dependencies
):
    repository, _storage, _service = analysis_dependencies
    created = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = created.get_json()["data"]["analysis_id"]

    # Old/uninstrumented record: progress keys are absent, not null.
    detail = analysis_client.get(
        f"/api/analysis/{analysis_id}", headers=auth_headers()
    )
    analysis = detail.get_json()["data"]["analysis"]
    assert "current_step" not in analysis
    assert "progress_percent" not in analysis

    # Simulate P-03 instrumentation writing real progress values.
    repository.records[analysis_id].update(
        {"current_step": "inference", "progress_percent": 40}
    )
    detail = analysis_client.get(
        f"/api/analysis/{analysis_id}", headers=auth_headers()
    )
    analysis = detail.get_json()["data"]["analysis"]
    assert analysis["current_step"] == "inference"
    assert analysis["progress_percent"] == 40


def test_stale_flag_marks_untracked_old_processing_record_without_mutating(
    analysis_client, analysis_dependencies
):
    repository, _storage, _service = analysis_dependencies
    old = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    repository.records["orphan-1"] = {
        "id": "orphan-1",
        "user_id": "user-a",
        "status": "processing",
        "created_at": old,
        "original_filename": "scope.jpg",
    }

    detail = analysis_client.get("/api/analysis/orphan-1", headers=auth_headers())
    analysis = detail.get_json()["data"]["analysis"]
    # Flagged for inspection, but status is NOT changed to failed.
    assert analysis["status"] == "processing"
    assert analysis["stale"] is True


def test_queued_job_is_not_marked_stale_despite_age(analysis_client, analysis_dependencies):
    repository, _storage, service = analysis_dependencies
    created = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = created.get_json()["data"]["analysis_id"]
    old = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    repository.records[analysis_id].update({"created_at": old})

    # This process still holds the job in its queue: never stale, however old.
    detail = analysis_client.get(
        f"/api/analysis/{analysis_id}", headers=auth_headers()
    )
    analysis = detail.get_json()["data"]["analysis"]
    assert analysis["status"] == "processing"
    assert "stale" not in analysis
    assert service.job_queue.contains(analysis_id) is True


# ---------------------------------------------------------------------------
# Batch P-03: service-level progress instrumentation contract.
# ---------------------------------------------------------------------------


def _install_progress_pipeline(service, phases=None, passes=0):
    """Replace the service pipeline with one that drives real progress writes.

    Emits ``passes`` successful forward passes plus the named phases (in order)
    through the reporter the service injects, mimicking the real pipeline's
    callback usage without running the model.
    """
    from ai.inference.pipeline import PHASE_PREPROCESSING

    def _pipeline(file_bytes, config, on_phase=None, on_pass=None, **kwargs):
        for _ in range(passes):
            if on_pass is not None:
                on_pass()
        for name in (phases or [PHASE_PREPROCESSING]):
            if on_phase is not None:
                on_phase(name)
        return pipeline_result()

    service.pipeline_runner = _pipeline


def test_progress_is_monotonic_and_100_percent_only_after_completion(
    analysis_client, analysis_dependencies
):
    from ai.inference.pipeline import (
        PHASE_ARTIFACT_COMPOSITION,
        PHASE_GRADCAM,
        PHASE_INFERENCE,
    )

    repository, storage, service = analysis_dependencies
    _install_progress_pipeline(
        service,
        phases=[PHASE_INFERENCE, PHASE_GRADCAM, PHASE_ARTIFACT_COMPOSITION],
        passes=5,
    )
    created = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = created.get_json()["data"]["analysis_id"]

    # Record one unified timeline of artifact uploads and progress writes to
    # prove monotonicity, that 100% appears only on the final persisted write,
    # and that every required artifact was stored before that write.
    timeline = []
    original_update = repository.update
    original_upload = storage.upload_file

    def _spy_update(analysis_id, user_id, data, use_service_role=False):
        record = original_update(analysis_id, user_id, data, use_service_role)
        if record is not None and "progress_percent" in data:
            timeline.append(("progress", data["progress_percent"]))
        return record

    def _spy_upload(path, file_bytes, content_type, user_id, use_service_role=False):
        timeline.append(("upload", path))
        return original_upload(
            path, file_bytes, content_type, user_id, use_service_role
        )

    repository.update = _spy_update
    storage.upload_file = _spy_upload
    assert service.job_queue.drain_one() is True
    repository.update = original_update
    storage.upload_file = original_upload

    record = repository.records[analysis_id]
    assert record["status"] == "completed"
    assert record["progress_percent"] == 100
    assert record["current_step"] == "completed"

    observed = [value for kind, value in timeline if kind == "progress"]
    # Every reported percent is within 0-100 and never decreases.
    assert all(0 <= p <= 100 for p in observed)
    assert observed == sorted(observed)
    # 100 is written only on the final (completed) update, never earlier.
    assert observed.count(100) == 1
    assert observed[-1] == 100
    # Progress actually advanced (not a single jump straight to completion).
    assert len(observed) > 1

    # 100% may only be persisted after ALL 4 required artifacts were stored.
    upload_indices = [
        i for i, (kind, _value) in enumerate(timeline) if kind == "upload"
    ]
    hundred_index = next(
        i
        for i, (kind, value) in enumerate(timeline)
        if kind == "progress" and value == 100
    )
    assert len(upload_indices) == 4
    assert max(upload_indices) < hundred_index


def test_progress_reporting_db_failure_does_not_fail_analysis(
    analysis_client, analysis_dependencies
):
    from ai.inference.pipeline import PHASE_INFERENCE

    repository, _storage, service = analysis_dependencies
    _install_progress_pipeline(service, phases=[PHASE_INFERENCE], passes=0)
    created = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = created.get_json()["data"]["analysis_id"]

    # Make only progress (current_step) writes fail; the terminal completed
    # update (which carries no current_step) still succeeds.
    original_update = repository.update

    def _flaky_update(analysis_id, user_id, data, use_service_role=False):
        if "current_step" in data and data.get("current_step") != "completed":
            raise RuntimeError("progress write failed")
        return original_update(analysis_id, user_id, data, use_service_role)

    repository.update = _flaky_update
    assert service.job_queue.drain_one() is True
    repository.update = original_update

    record = repository.records[analysis_id]
    # A reporting failure must never turn a successful analysis into a failure.
    assert record["status"] == "completed"
    assert record["progress_percent"] == 100
    assert record["error_code"] is None


def test_pipeline_failure_preserves_last_progress_and_failed_status(
    analysis_client, analysis_dependencies
):
    from ai.inference.pipeline import PHASE_INFERENCE

    repository, _storage, service = analysis_dependencies

    def _partial_then_fail(file_bytes, config, on_phase=None, on_pass=None, **kwargs):
        if on_phase is not None:
            on_phase(PHASE_INFERENCE)  # one real completed phase
        raise RuntimeError("private pipeline traceback")

    service.pipeline_runner = _partial_then_fail
    created = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = created.get_json()["data"]["analysis_id"]
    assert service.job_queue.drain_one() is True

    record = repository.records[analysis_id]
    # status 'failed' is the source of truth; last real progress is retained.
    assert record["status"] == "failed"
    assert record["error_code"] == "AI_PIPELINE_ERROR"
    assert record["current_step"] == PHASE_INFERENCE
    assert 0 <= record["progress_percent"] < 100


def test_execute_pipeline_early_failure_does_not_raise_unbound_local_error(
    analysis_dependencies, monkeypatch
):
    import app.services.analysis_service as analysis_service_mod
    from app.core.errors import APIError

    repository, _storage, service = analysis_dependencies

    # Simulate an exception on line 800 before pipeline execution starts
    def _fail_count(*args, **kwargs):
        raise ValueError("simulated early failure before pipeline")

    monkeypatch.setattr(analysis_service_mod, "count_forward_passes", _fail_count)

    with pytest.raises(APIError) as exc_info:
        service._execute_pipeline(
            analysis_id="test-early-fail",
            user_id="user-a",
            file_bytes=b"dummy_bytes",
        )

    assert exc_info.value.code == "AI_PIPELINE_ERROR"
    assert isinstance(exc_info.value.__cause__, ValueError)
    assert "simulated early failure before pipeline" in str(exc_info.value.__cause__)


def test_execute_pipeline_failed_status_update_error_is_logged(
    analysis_dependencies, caplog
):
    import logging
    from app.core.errors import APIError

    repository, _storage, service = analysis_dependencies

    # Force pipeline to fail
    def _failing_pipeline(*args, **kwargs):
        raise RuntimeError("simulated pipeline execution error")

    service.pipeline_runner = _failing_pipeline

    # Make repository.update fail when updating to status='failed'
    original_update = repository.update

    def _fail_on_status_failed(analysis_id, user_id, data, use_service_role=False):
        if data.get("status") == "failed":
            raise RuntimeError("simulated database update failure")
        return original_update(analysis_id, user_id, data, use_service_role)

    repository.update = _fail_on_status_failed

    with caplog.at_level(logging.ERROR):
        with pytest.raises(APIError) as exc_info:
            service._execute_pipeline(
                analysis_id="test-update-fail-id",
                user_id="user-a",
                file_bytes=b"dummy_bytes",
            )

    # The original pipeline error must still be raised wrapped in APIError
    assert exc_info.value.code == "AI_PIPELINE_ERROR"
    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert "simulated pipeline execution error" in str(exc_info.value.__cause__)

    # The repository failure must be logged with traceback and analysis_id
    error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
    assert any(
        "Failed to update analysis status to failed for analysis_id=test-update-fail-id"
        in record.getMessage()
        for record in error_logs
    )
    assert any(
        record.exc_info is not None and "simulated database update failure" in str(record.exc_info[1])
        for record in error_logs
    )


def test_artifact_uploads_are_strictly_sequential(analysis_client, analysis_dependencies):
    """Artifact uploads must be strictly sequential (concurrency == 1) to avoid HTTP/2 disconnects."""
    from ai.inference.pipeline import (
        PHASE_ARTIFACT_COMPOSITION,
        PHASE_GRADCAM,
        PHASE_INFERENCE,
    )

    repository, storage, service = analysis_dependencies
    _install_progress_pipeline(
        service,
        phases=[PHASE_INFERENCE, PHASE_GRADCAM, PHASE_ARTIFACT_COMPOSITION],
        passes=1,
    )

    created = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = created.get_json()["data"]["analysis_id"]

    active_concurrent = 0
    max_concurrent = 0
    uploaded_artifact_paths = []
    original_upload = storage.upload_file

    def _instrumented_upload(path, file_bytes, content_type, user_id, use_service_role=False):
        nonlocal active_concurrent, max_concurrent
        active_concurrent += 1
        if active_concurrent > max_concurrent:
            max_concurrent = active_concurrent
        time.sleep(0.005)
        try:
            res = original_upload(path, file_bytes, content_type, user_id, use_service_role)
            uploaded_artifact_paths.append(path)
            return res
        finally:
            active_concurrent -= 1

    storage.upload_file = _instrumented_upload
    assert service.job_queue.drain_one() is True
    storage.upload_file = original_upload

    record = repository.records[analysis_id]
    assert record["status"] == "completed"
    assert record["progress_percent"] == 100
    assert len(uploaded_artifact_paths) == 4
    assert max_concurrent == 1


def test_artifact_upload_failure_triggers_cleanup_and_status_failed(analysis_client, analysis_dependencies):
    """When an artifact upload fails, partial artifacts are deleted and status is set to failed."""
    from ai.inference.pipeline import (
        PHASE_ARTIFACT_COMPOSITION,
        PHASE_GRADCAM,
        PHASE_INFERENCE,
    )

    repository, storage, service = analysis_dependencies
    _install_progress_pipeline(
        service,
        phases=[PHASE_INFERENCE, PHASE_GRADCAM, PHASE_ARTIFACT_COMPOSITION],
        passes=1,
    )

    created = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = created.get_json()["data"]["analysis_id"]

    call_count = 0
    original_upload = storage.upload_file
    uploaded_before_failure = []

    def _failing_upload(path, file_bytes, content_type, user_id, use_service_role=False):
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            raise RuntimeError("simulated storage network disconnect")
        uploaded_before_failure.append(path)
        return original_upload(path, file_bytes, content_type, user_id, use_service_role)

    storage.upload_file = _failing_upload
    # Background worker catches exception and marks record failed
    assert service.job_queue.drain_one() is True
    storage.upload_file = original_upload

    record = repository.records[analysis_id]
    assert record["status"] == "failed"
    assert record["error_code"] == "AI_PIPELINE_ERROR"

    # Any artifacts uploaded before failure must have been deleted
    deleted_paths = [path for path, _user, _role in storage.deleted_paths]
    for partial_path in uploaded_before_failure:
        assert partial_path in deleted_paths
