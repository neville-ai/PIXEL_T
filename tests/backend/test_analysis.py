import io
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
    return client


@pytest.fixture
def analysis_dependencies(monkeypatch):
    repository = FakeRepository()
    storage = FakeStorage()
    service = AnalysisService(
        repository=repository,
        storage_service=storage,
        pipeline_runner=lambda file_bytes, config: pipeline_result(),
    )
    monkeypatch.setattr(analysis_routes.controller, "service", service)
    return repository, storage


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
    repository, storage = analysis_dependencies
    response = upload(
        analysis_client,
        image_bytes(image_format),
        f"scope.{extension}",
        mime_type,
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True
    analysis_id = data["data"]["analysis_id"]
    assert data["data"]["status"] == "completed"

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
    _, storage = analysis_dependencies
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
    response = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = response.get_json()["data"]["analysis_id"]

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
    repository, storage = analysis_dependencies
    created = upload(analysis_client, image_bytes("JPEG"))
    analysis_id = created.get_json()["data"]["analysis_id"]
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
    repository, _ = analysis_dependencies
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
            pipeline_runner=lambda file_bytes, config: pipeline_result(),
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
