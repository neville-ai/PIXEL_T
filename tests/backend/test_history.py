"""TASK 17 — History/List + Delete endpoint tests (Cases A–E).

Covers:
- GET /api/history authentication, ownership scoping, contract shape,
  and raw-storage-path non-exposure.
- DELETE /api/history/<id> ownership enforcement and the locked
  DECISION A failure semantics:
    A. DB delete fails      -> 500 DATABASE_ERROR, record kept, storage untouched
    B. DB + storage succeed -> 200, record and assets removed
    C. Storage returns False-> 200, record stays deleted (residual risk)
    D. Storage raises       -> 200, record stays deleted (residual risk)
    E. Missing/foreign ID   -> 404 ANALYSIS_NOT_FOUND, nothing touched
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.analysis_service import AnalysisService
import app.routes.analysis as analysis_routes
import app.core.auth as auth_module


def make_record(analysis_id, user_id, **overrides):
    record = {
        "id": analysis_id,
        "user_id": user_id,
        "status": "completed",
        "created_at": "2026-09-30T12:00:00Z",
        "completed_at": "2026-09-30T12:01:00Z",
        "original_filename": f"{analysis_id}.jpg",
        "original_image_path": f"analysis/{user_id}/{analysis_id}/original/input.jpg",
        "binary_mask_path": f"analysis/{user_id}/{analysis_id}/segmentation/mask.png",
        "segmentation_overlay_path": f"analysis/{user_id}/{analysis_id}/segmentation/overlay.png",
        "gradcam_heatmap_path": f"analysis/{user_id}/{analysis_id}/gradcam/heatmap.png",
        "gradcam_overlay_path": f"analysis/{user_id}/{analysis_id}/gradcam/overlay.png",
        "segmentation_status": "detected",
    }
    record.update(overrides)
    return record


class FakeHistoryRepository:
    def __init__(self, fail_delete=False):
        self.records = {}
        self.fail_delete = fail_delete
        self.list_calls = []

    def get_by_id(self, analysis_id, user_id, use_service_role=False):
        record = self.records.get(analysis_id)
        if record and record["user_id"] == user_id:
            return record
        return None

    def list_by_user(self, user_id, limit=20, offset=0, use_service_role=False):
        self.list_calls.append((user_id, limit, offset, use_service_role))
        if not user_id:
            return []
        owned = [r for r in self.records.values() if r["user_id"] == user_id]
        owned.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return owned[offset:offset + limit]

    def delete(self, analysis_id, user_id, use_service_role=False):
        if self.fail_delete:
            raise RuntimeError("private database detail")
        record = self.records.get(analysis_id)
        if record and record["user_id"] == user_id:
            del self.records[analysis_id]
            return True
        return False


class FakeHistoryStorage:
    def __init__(self, fail_signed=False, fail_remove=False, remove_result=True):
        self.removed = []
        self.signed = []
        self.fail_signed = fail_signed
        self.fail_remove = fail_remove
        self.remove_result = remove_result

    def create_signed_url(self, path, expires_in, user_id, use_service_role=False):
        self.signed.append((path, expires_in, user_id, use_service_role))
        if self.fail_signed:
            raise RuntimeError("private storage detail")
        return f"signed://temporary/{path}"

    def delete_analysis_files(self, paths, user_id=None, use_service_role=False):
        self.removed.append((list(paths), user_id, use_service_role))
        if self.fail_remove:
            raise RuntimeError("private storage detail")
        return self.remove_result


@pytest.fixture
def history_client(client, monkeypatch):
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
def history_dependencies(monkeypatch):
    repository = FakeHistoryRepository()
    storage = FakeHistoryStorage()
    service = AnalysisService(repository=repository, storage_service=storage)
    monkeypatch.setattr(analysis_routes.controller, "service", service)
    return repository, storage


def auth_headers(user_id="user-a"):
    return {"Authorization": f"Bearer {user_id}-token"}


def seed(repository, *records):
    for record in records:
        repository.records[record["id"]] = record


# ---------------------------------------------------------------------------
# GET /api/history
# ---------------------------------------------------------------------------

def test_history_requires_authentication(client):
    response = client.get("/api/history")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_history_returns_only_authenticated_user_records(history_client, history_dependencies):
    repository, _ = history_dependencies
    seed(
        repository,
        make_record("a-1", "user-a"),
        make_record("a-2", "user-a"),
        make_record("b-1", "user-b"),
    )

    response = history_client.get("/api/history", headers=auth_headers("user-a"))

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    ids = [item["id"] for item in payload["data"]["items"]]
    assert sorted(ids) == ["a-1", "a-2"]


def test_history_ignores_client_supplied_user_id(history_client, history_dependencies):
    repository, _ = history_dependencies
    seed(repository, make_record("a-1", "user-a"), make_record("b-1", "user-b"))

    response = history_client.get(
        "/api/history?user_id=user-b", headers=auth_headers("user-a")
    )

    assert response.status_code == 200
    ids = [item["id"] for item in response.get_json()["data"]["items"]]
    assert ids == ["a-1"]


def test_history_empty_returns_empty_items(history_client, history_dependencies):
    response = history_client.get("/api/history", headers=auth_headers("user-a"))

    assert response.status_code == 200
    assert response.get_json()["data"]["items"] == []


def test_history_item_shape_matches_contract_and_hides_raw_paths(
    history_client, history_dependencies
):
    repository, storage = history_dependencies
    seed(repository, make_record("a-1", "user-a"))

    response = history_client.get("/api/history", headers=auth_headers("user-a"))

    assert response.status_code == 200
    (item,) = response.get_json()["data"]["items"]
    assert item["id"] == "a-1"
    assert item["created_at"] == "2026-09-30T12:00:00Z"
    assert item["status"] == "completed"
    assert item["thumbnail_url"] == (
        "signed://temporary/analysis/user-a/a-1/original/input.jpg"
    )
    assert item["segmentation_status"] == "detected"
    # Raw private storage paths must never leak into the list payload.
    for leaked in (
        "original_image_path",
        "binary_mask_path",
        "segmentation_overlay_path",
        "gradcam_heatmap_path",
        "gradcam_overlay_path",
    ):
        assert leaked not in item
    assert "analysis/user-a/" not in response.get_data(as_text=True).replace(
        "signed://temporary/analysis/user-a/", ""
    )
    assert storage.signed[0][2:] == ("user-a", True)


def test_history_signed_url_failure_degrades_to_null_thumbnail(
    history_client, monkeypatch
):
    repository = FakeHistoryRepository()
    storage = FakeHistoryStorage(fail_signed=True)
    monkeypatch.setattr(
        analysis_routes.controller,
        "service",
        AnalysisService(repository=repository, storage_service=storage),
    )
    repository.records["a-1"] = make_record("a-1", "user-a")

    response = history_client.get("/api/history", headers=auth_headers("user-a"))

    assert response.status_code == 200
    (item,) = response.get_json()["data"]["items"]
    assert item["thumbnail_url"] is None


# ---------------------------------------------------------------------------
# DELETE /api/history/<id> — Cases A–E
# ---------------------------------------------------------------------------

def test_delete_requires_authentication(client):
    response = client.delete("/api/history/some-id")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_delete_case_b_success_removes_record_and_all_assets(
    history_client, history_dependencies
):
    repository, storage = history_dependencies
    seed(repository, make_record("a-1", "user-a"))

    response = history_client.delete(
        "/api/history/a-1", headers=auth_headers("user-a")
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "success": True,
        "message": "Analysis deleted successfully",
    }
    assert "a-1" not in repository.records
    removed_paths, removed_user, service_role = storage.removed[0]
    assert removed_user == "user-a"
    assert service_role is True
    assert sorted(removed_paths) == sorted(
        [
            "analysis/user-a/a-1/original/input.jpg",
            "analysis/user-a/a-1/segmentation/mask.png",
            "analysis/user-a/a-1/segmentation/overlay.png",
            "analysis/user-a/a-1/gradcam/heatmap.png",
            "analysis/user-a/a-1/gradcam/overlay.png",
        ]
    )


def test_delete_case_e_missing_id_returns_not_found(
    history_client, history_dependencies
):
    repository, storage = history_dependencies

    response = history_client.delete(
        "/api/history/does-not-exist", headers=auth_headers("user-a")
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "success": False,
        "error": {
            "code": "ANALYSIS_NOT_FOUND",
            "message": "Analysis not found or access denied.",
        },
    }
    assert storage.removed == []


def test_delete_case_e_foreign_id_is_hidden_as_not_found(
    history_client, history_dependencies
):
    repository, storage = history_dependencies
    seed(repository, make_record("b-1", "user-b"))

    response = history_client.delete(
        "/api/history/b-1", headers=auth_headers("user-a")
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "ANALYSIS_NOT_FOUND"
    # Foreign record and foreign storage are untouched.
    assert "b-1" in repository.records
    assert storage.removed == []


def test_delete_case_a_database_failure_keeps_record_and_storage(
    history_client, monkeypatch
):
    repository = FakeHistoryRepository(fail_delete=True)
    storage = FakeHistoryStorage()
    monkeypatch.setattr(
        analysis_routes.controller,
        "service",
        AnalysisService(repository=repository, storage_service=storage),
    )
    repository.records["a-1"] = make_record("a-1", "user-a")

    response = history_client.delete(
        "/api/history/a-1", headers=auth_headers("user-a")
    )

    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == "DATABASE_ERROR"
    assert "private database detail" not in response.get_data(as_text=True)
    assert "a-1" in repository.records
    assert storage.removed == []


def test_delete_case_c_storage_false_still_returns_success_record_deleted(
    history_client, monkeypatch
):
    repository = FakeHistoryRepository()
    storage = FakeHistoryStorage(remove_result=False)
    monkeypatch.setattr(
        analysis_routes.controller,
        "service",
        AnalysisService(repository=repository, storage_service=storage),
    )
    repository.records["a-1"] = make_record("a-1", "user-a")

    response = history_client.delete(
        "/api/history/a-1", headers=auth_headers("user-a")
    )

    # DECISION A: storage cleanup failure is a non-fatal residual risk.
    assert response.status_code == 200
    assert response.get_json()["success"] is True
    assert "a-1" not in repository.records


def test_delete_case_d_storage_exception_still_returns_success_record_deleted(
    history_client, monkeypatch
):
    repository = FakeHistoryRepository()
    storage = FakeHistoryStorage(fail_remove=True)
    monkeypatch.setattr(
        analysis_routes.controller,
        "service",
        AnalysisService(repository=repository, storage_service=storage),
    )
    repository.records["a-1"] = make_record("a-1", "user-a")

    response = history_client.delete(
        "/api/history/a-1", headers=auth_headers("user-a")
    )

    # DECISION A: storage exception is swallowed (no internal leak),
    # the record stays deleted, and no resurrection is attempted.
    assert response.status_code == 200
    assert response.get_json()["success"] is True
    assert "private storage detail" not in response.get_data(as_text=True)
    assert "a-1" not in repository.records
