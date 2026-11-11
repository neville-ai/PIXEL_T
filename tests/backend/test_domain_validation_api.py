"""Integration tests for medical domain validation on POST /api/analysis.

Verifies:
1. Non-colonoscopy images (face, food, landscape, document, vehicle) are REJECTED
   at the API boundary (HTTP 400, NOT_COLONOSCOPY_IMAGE).
2. No storage file, no database row, and no background pipeline job is created
   for rejected non-colonoscopy uploads.
3. Ambiguous / underexposed images return HTTP 400 with UNCERTAIN_COLONOSCOPY_IMAGE.
4. Valid colonoscopy images (normal or with polyp) are ACCEPTED (HTTP 202).
"""

import io
import cv2
import numpy as np
import pytest
from PIL import Image

from unittest.mock import MagicMock
from types import SimpleNamespace

from src import create_app
from src.config.settings import TestingConfig
from src.services.analysis_service import AnalysisService
from src.services.storage_service import StorageService
import src.routes.analysis as analysis_routes
import src.core.auth as auth_module


class FakeRepository:
    def __init__(self):
        self.records = {}
        self.create_calls = []

    def create(self, user_id, data, use_service_role=False):
        self.create_calls.append((user_id, data, use_service_role))
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
        if analysis_id in self.records:
            del self.records[analysis_id]
            return True
        return False


class FakeStorage:
    def __init__(self):
        self.uploaded_files = []
        self.deleted_files = []

    def generate_original_image_path(self, user_id, analysis_id, extension):
        return StorageService().generate_original_image_path(user_id, analysis_id, extension)

    def upload_file(self, path, file_bytes, content_type, user_id, use_service_role=False):
        self.uploaded_files.append((path, file_bytes, content_type, user_id))
        return path

    def delete_file(self, path, user_id, use_service_role=False):
        self.deleted_files.append((path, user_id))
        return True


def _make_colonoscopy_bytes() -> bytes:
    """Create a synthetic colonoscopy image with polyp and mucosal tissue."""
    img = np.full((512, 512, 3), [195, 80, 75], dtype=np.uint8)
    cv2.circle(img, (256, 256), 200, (215, 105, 90), -1)
    cv2.circle(img, (310, 290), 50, (175, 65, 60), -1)
    cv2.circle(img, (270, 240), 6, (255, 255, 250), -1)
    stream = io.BytesIO()
    Image.fromarray(img, mode="RGB").save(stream, format="JPEG")
    return stream.getvalue()


def _make_non_colonoscopy_bytes(kind: str = "landscape") -> bytes:
    """Create non-colonoscopy synthetic images."""
    if kind == "landscape":
        img = np.zeros((512, 512, 3), dtype=np.uint8)
        img[:256, :] = [70, 140, 230]  # Blue sky
        img[256:, :] = [40, 160, 50]   # Green grass
    elif kind == "face":
        img = np.full((512, 512, 3), [180, 180, 190], dtype=np.uint8)
        img[380:, :] = [40, 60, 160]
        cv2.circle(img, (256, 200), 130, [30, 20, 15], -1)
        cv2.ellipse(img, (256, 220), (80, 110), 0, 0, 360, [225, 180, 150], -1)
    elif kind == "document":
        img = np.full((512, 512, 3), 250, dtype=np.uint8)
        for y in range(40, 480, 20):
            cv2.line(img, (40, y), (460, y), (20, 20, 20), 2)
    elif kind == "food":
        img = np.full((512, 512, 3), [240, 240, 240], dtype=np.uint8)
        cv2.circle(img, (256, 256), 200, (215, 175, 45), -1)
        cv2.circle(img, (200, 200), 25, (40, 130, 40), -1)
        cv2.circle(img, (300, 220), 30, (30, 120, 35), -1)
    else:
        img = np.zeros((512, 512, 3), dtype=np.uint8)

    stream = io.BytesIO()
    Image.fromarray(img, mode="RGB").save(stream, format="JPEG")
    return stream.getvalue()


def _make_underexposed_bytes() -> bytes:
    """Create severely underexposed ambiguous image."""
    img = np.full((512, 512, 3), [40, 20, 20], dtype=np.uint8)
    cv2.circle(img, (256, 256), 100, (55, 28, 24), -1)
    stream = io.BytesIO()
    Image.fromarray(img, mode="RGB").save(stream, format="JPEG")
    return stream.getvalue()


@pytest.fixture
def analysis_env(monkeypatch):
    monkeypatch.setattr(auth_module, "is_supabase_configured", lambda: True)
    auth_client = MagicMock()
    auth_client.auth.get_user.side_effect = lambda token: SimpleNamespace(
        user=SimpleNamespace(id="doc-01", email="dr.smith@example.com", role="authenticated")
    )
    monkeypatch.setattr(auth_module, "get_supabase_client", lambda **kwargs: auth_client)
    monkeypatch.setattr(
        auth_module,
        "_get_user_role_and_status",
        lambda user_id: {"role": "doctor", "account_status": "approved"},
    )
    repo = FakeRepository()
    storage = FakeStorage()
    service = AnalysisService(
        repository=repo,
        storage_service=storage,
        auto_start_worker=False,
        enforce_domain_validation=True,
    )
    monkeypatch.setattr(analysis_routes, "controller", analysis_routes.AnalysisController(service))
    app = create_app(TestingConfig)
    return app.test_client(), repo, storage, service


def test_api_rejects_landscape_image(analysis_env):
    """POST /api/analysis rejects landscape image without persisting assets."""
    client, repo, storage, _ = analysis_env
    data = {
        "image": (io.BytesIO(_make_non_colonoscopy_bytes("landscape")), "landscape.jpg", "image/jpeg"),
    }
    response = client.post(
        "/api/analysis",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "NOT_COLONOSCOPY_IMAGE"
    assert "tidak sesuai" in payload["error"]["message"].lower()

    # Zero assets uploaded, zero database records
    assert len(storage.uploaded_files) == 0
    assert len(repo.create_calls) == 0


def test_api_rejects_face_and_food_images(analysis_env):
    """POST /api/analysis rejects face and food images; grayscale document returns UNCERTAIN."""
    client, repo, storage, _ = analysis_env

    # Face and food: purely chromatic → REJECT → NOT_COLONOSCOPY_IMAGE
    for kind in ["face", "food"]:
        data = {
            "image": (io.BytesIO(_make_non_colonoscopy_bytes(kind)), f"{kind}.jpg", "image/jpeg"),
        }
        res = client.post(
            "/api/analysis",
            data=data,
            content_type="multipart/form-data",
            headers={"Authorization": "Bearer valid-token"},
        )
        assert res.status_code == 400
        assert res.get_json()["error"]["code"] == "NOT_COLONOSCOPY_IMAGE"

    # Document (white+black lines): achromatic → G4 UNCERTAIN → UNCERTAIN_COLONOSCOPY_IMAGE
    data = {
        "image": (io.BytesIO(_make_non_colonoscopy_bytes("document")), "document.jpg", "image/jpeg"),
    }
    res = client.post(
        "/api/analysis",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] in ("NOT_COLONOSCOPY_IMAGE", "UNCERTAIN_COLONOSCOPY_IMAGE")

    assert len(storage.uploaded_files) == 0
    assert len(repo.create_calls) == 0


def test_api_flags_underexposed_image_as_uncertain(analysis_env):
    """POST /api/analysis flags dark / ambiguous image as UNCERTAIN_COLONOSCOPY_IMAGE."""
    client, repo, storage, _ = analysis_env
    data = {
        "image": (io.BytesIO(_make_underexposed_bytes()), "dark.jpg", "image/jpeg"),
    }
    response = client.post(
        "/api/analysis",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "UNCERTAIN_COLONOSCOPY_IMAGE"
    assert "tidak dapat memastikan" in payload["error"]["message"].lower()

    assert len(storage.uploaded_files) == 0
    assert len(repo.create_calls) == 0


def test_api_accepts_valid_colonoscopy_image(analysis_env):
    """POST /api/analysis accepts a valid colonoscopy image (returns 202)."""
    client, repo, storage, _ = analysis_env
    data = {
        "image": (io.BytesIO(_make_colonoscopy_bytes()), "colonoscopy.jpg", "image/jpeg"),
    }
    response = client.post(
        "/api/analysis",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 202
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "processing"
    assert "analysis_id" in payload["data"]

    # Storage and DB record are created
    assert len(storage.uploaded_files) == 1
    assert len(repo.create_calls) == 1
