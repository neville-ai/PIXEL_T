"""Isu B — safe analysis deletion, deterministic lifecycle tests.

These tests pin the behaviour agreed for Tahap 6:

* tombstone in-memory marks an analysis while it is being deleted,
* waiting jobs are purged from the queue after the DB delete succeeds,
* active jobs observe cooperative cancellation at stage boundaries,
* every persistence write passes through a write-fence owned by ``delete_analysis``,
* storage cleanup is required post-delete, but the tombstone is retained when it fails.

All concurrency is driven by threading.Event/Lock/barrier primitives; no long
sleeps are used so the tests remain deterministic.
"""
import threading
import time
from types import SimpleNamespace

import pytest

from src.core.errors import APIError
from src.services.analysis_pipeline_service import AnalysisDeletionCancelled
from src.services.analysis_queue_service import AnalysisJobQueue
from src.services.analysis_service import AnalysisService
from src.services.storage_service import StorageService


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeRepository:
    def __init__(self, fail_delete=False):
        self.records = {}
        self.fail_delete = fail_delete
        self.events = []          # ("update"/"delete", analysis_id, status)
        self.updates = []         # (analysis_id, data copy)
        self.deleted_ids = []
        self.completed_event = threading.Event()
        self._on_update = None

    def set_on_update(self, fn):
        self._on_update = fn

    def create(self, user_id, data, use_service_role=False):
        self.records[data["id"]] = dict(data)
        return data

    def get_by_id(self, analysis_id, user_id, use_service_role=False):
        record = self.records.get(analysis_id)
        if record and record["user_id"] == user_id:
            return record
        return None

    def update(self, analysis_id, user_id, data, use_service_role=False):
        self.events.append(("update", analysis_id, data.get("status")))
        if self._on_update is not None:
            self._on_update(analysis_id, data)
        record = self.records.get(analysis_id)
        if not record or record["user_id"] != user_id:
            return None
        record.update(data)
        self.updates.append((analysis_id, dict(data)))
        if data.get("status") == "completed":
            self.completed_event.set()
        return record

    def delete(self, analysis_id, user_id, use_service_role=False):
        self.events.append(("delete", analysis_id, None))
        self.deleted_ids.append(analysis_id)
        if self.fail_delete:
            raise RuntimeError("private database detail")
        record = self.records.get(analysis_id)
        if record and record["user_id"] == user_id:
            del self.records[analysis_id]
            return True
        return False


class FakeStorage:
    def __init__(self, fail_upload=False, remove_result=True):
        self.uploads = []
        self.upload_calls = []
        self.removed = []
        self.remove_result = remove_result
        self.delete_raises = False
        self.fail_upload = fail_upload
        self.on_upload = None

    def generate_original_image_path(self, user_id, analysis_id, extension):
        return StorageService().generate_original_image_path(user_id, analysis_id, extension)

    def upload_file(self, path, file_bytes, content_type, user_id, use_service_role=False):
        if self.on_upload is not None:
            self.on_upload(path, file_bytes, content_type, user_id, use_service_role)
        self.uploads.append(path)
        self.upload_calls.append((path, file_bytes, content_type, user_id, use_service_role))
        if self.fail_upload:
            raise RuntimeError("private storage detail")
        return path

    def delete_file(self, path, user_id, use_service_role=False):
        return True

    def create_signed_url(self, path, expires_in, user_id, use_service_role=False):
        return f"signed://temporary/{path}"

    def generate_binary_mask_path(self, user_id, analysis_id):
        return StorageService().generate_binary_mask_path(user_id, analysis_id)

    def generate_segmentation_overlay_path(self, user_id, analysis_id):
        return StorageService().generate_segmentation_overlay_path(user_id, analysis_id)

    def generate_gradcam_heatmap_path(self, user_id, analysis_id):
        return StorageService().generate_gradcam_heatmap_path(user_id, analysis_id)

    def generate_gradcam_overlay_path(self, user_id, analysis_id):
        return StorageService().generate_gradcam_overlay_path(user_id, analysis_id)

    def delete_analysis_files(self, paths, user_id=None, use_service_role=False):
        self.removed.append((list(paths), user_id, use_service_role))
        if self.delete_raises:
            raise RuntimeError("private storage detail")
        return self.remove_result


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def image_bytes():
    import io
    from PIL import Image
    stream = io.BytesIO()
    Image.new("RGB", (23, 17), color=(20, 80, 120)).save(stream, format="PNG")
    return stream.getvalue()


def pipeline_result():
    png = image_bytes()
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


def make_record(analysis_id, user_id="user-a"):
    return {
        "id": analysis_id,
        "user_id": user_id,
        "status": "processing",
        "created_at": "2026-01-01T00:00:00Z",
        "original_filename": f"{analysis_id}.jpg",
        "original_image_path": f"analysis/{user_id}/{analysis_id}/original/input.jpg",
        "binary_mask_path": f"analysis/{user_id}/{analysis_id}/segmentation/mask.png",
        "segmentation_overlay_path": f"analysis/{user_id}/{analysis_id}/segmentation/overlay.png",
        "gradcam_heatmap_path": f"analysis/{user_id}/{analysis_id}/gradcam/heatmap.png",
        "gradcam_overlay_path": f"analysis/{user_id}/{analysis_id}/gradcam/overlay.png",
        "segmentation_status": "detected",
    }


def build_service(repository=None, storage=None, runner=None, auto_start=False):
    repository = repository or FakeRepository()
    storage = storage or FakeStorage()
    runner = runner or (lambda file_bytes, config=None, **kwargs: pipeline_result())
    service = AnalysisService(
        repository=repository,
        storage_service=storage,
        pipeline_runner=runner,
        auto_start_worker=auto_start,
    )
    return repository, storage, service


def job(analysis_id, user_id="user-a"):
    return {"analysis_id": analysis_id, "user_id": user_id, "file_bytes": b"x"}


def wait_until(predicate, timeout=10.0):
    """Short-poll helper for deterministic event-driven tests (no long sleeps)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


# ---------------------------------------------------------------------------
# 1. Delete job still waiting → purged from queue, record removed, 200
# ---------------------------------------------------------------------------

def test_delete_waiting_job_purges_queue_and_removes_record():
    repository, storage, service = build_service(auto_start=False)
    repository.records["a-1"] = make_record("a-1", "user-a")

    assert service.job_queue.try_enqueue(job("a-1")) is True
    assert service.job_queue.contains("a-1") is True
    assert service.job_queue.pending_count() == 1

    result = service.delete_analysis("a-1", "user-a")
    assert result is True

    assert service.job_queue.contains("a-1") is False
    assert service.job_queue.pending_count() == 0
    assert repository.get_by_id("a-1", "user-a") is None
    assert "a-1" in repository.deleted_ids
    # Clean deletion clears the tombstone again.
    assert service.is_marked_for_deletion("a-1") is False
    assert storage.removed[0][1] == "user-a"
    assert storage.removed[0][2] is True


# ---------------------------------------------------------------------------
# 2. Purged job never executed by worker
# ---------------------------------------------------------------------------

def test_purged_job_never_executed():
    runner_calls = []

    def runner(job):
        runner_calls.append(job["analysis_id"])

    q = AnalysisJobQueue(runner=runner, auto_start=False)
    q.try_enqueue({"analysis_id": "a-1", "user_id": "user-a", "file_bytes": b"x"})
    assert q.contains("a-1") is True

    assert q.purge_job("a-1") is True
    assert q.contains("a-1") is False
    assert q.pending_count() == 0

    assert q.drain_one() is False
    assert runner_calls == []


# ---------------------------------------------------------------------------
# 3. Delete active job → cancellation requested immediately
# ---------------------------------------------------------------------------

def test_delete_active_job_requests_cancellation():
    repository, storage, service = build_service(auto_start=True)
    repository.records["a-1"] = make_record("a-1", "user-a")

    started = threading.Event()
    release = threading.Event()
    calls = []

    def runner(file_bytes, config=None, analysis_id=None, **kwargs):
        calls.append(analysis_id)
        started.set()
        assert release.wait(10)
        return pipeline_result()

    service.pipeline_runner = runner

    execute_done = threading.Event()
    errors = []
    original_execute = service.pipeline_service.execute

    def wrapped_execute(**kwargs):
        try:
            original_execute(**kwargs)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
            raise
        finally:
            execute_done.set()

    service.pipeline_service.execute = wrapped_execute

    assert service.job_queue.try_enqueue(job("a-1")) is True
    assert started.wait(10)

    result = service.delete_analysis("a-1", "user-a")
    assert result is True
    # Cancellation request is visible before the worker is released; the
    # write-fence tombstone itself is released once deletion reached its safe
    # final state.
    assert service.is_cancelled_for_deletion("a-1") is True

    release.set()
    assert execute_done.wait(10)

    # Pipeline stopped at the cancellation boundary: nothing persisted.
    assert repository.get_by_id("a-1", "user-a") is None
    assert storage.uploads == []
    assert not any(data.get("status") == "completed" for _, data in repository.updates)
    assert service.is_marked_for_deletion("a-1") is False
    assert wait_until(lambda: service.is_cancelled_for_deletion("a-1") is False)
    assert any(isinstance(exc, AnalysisDeletionCancelled) for exc in errors)


# ---------------------------------------------------------------------------
# 4. Worker never starts a tombstoned job
# ---------------------------------------------------------------------------

def test_worker_does_not_start_tombstoned_job():
    repository, storage, service = build_service(auto_start=False)
    repository.records["a-1"] = make_record("a-1", "user-a")

    runner_calls = []

    def runner(file_bytes, config=None, **kwargs):
        runner_calls.append(kwargs.get("analysis_id", "unknown"))
        return pipeline_result()

    # The queue's runner is the service worker entry point (_run_analysis_job),
    # which performs the tombstone check itself.
    service.pipeline_runner = runner

    assert service.job_queue.try_enqueue(job("a-1")) is True
    assert service.job_queue.contains("a-1") is True

    # Tombstone lands between enqueue and dequeue.
    service._mark_for_deletion("a-1")

    assert service.job_queue.drain_one() is True
    assert runner_calls == []  # skipped because of the tombstone
    assert service.job_queue.contains("a-1") is False
    # No pipeline write happened against the record.
    assert repository.records["a-1"]["status"] == "processing"


# ---------------------------------------------------------------------------
# 5. Pipeline halts at cooperative cancellation (not an inference failure)
# ---------------------------------------------------------------------------

def test_pipeline_stops_at_cooperative_cancellation():
    repository, storage, service = build_service(auto_start=True)
    repository.records["a-1"] = make_record("a-1", "user-a")

    started = threading.Event()
    release = threading.Event()

    def runner(file_bytes, config=None, analysis_id=None, **kwargs):
        started.set()
        assert release.wait(10)
        return pipeline_result()

    service.pipeline_runner = runner

    execute_done = threading.Event()
    raised = []
    original_execute = service.pipeline_service.execute

    def wrapped_execute(**kwargs):
        try:
            original_execute(**kwargs)
        except AnalysisDeletionCancelled as exc:
            raised.append(exc)
            raise
        finally:
            execute_done.set()

    service.pipeline_service.execute = wrapped_execute

    assert service.job_queue.try_enqueue(job("a-1")) is True
    assert started.wait(10)

    assert service.delete_analysis("a-1", "user-a") is True
    release.set()
    assert execute_done.wait(10)

    assert len(raised) == 1
    assert isinstance(raised[0], AnalysisDeletionCancelled)
    assert repository.get_by_id("a-1", "user-a") is None
    assert storage.uploads == []
    assert not any(data.get("status") == "completed" for _, data in repository.updates)
    assert wait_until(lambda: service.is_cancelled_for_deletion("a-1") is False)


# ---------------------------------------------------------------------------
# 6. Cancelling one job leaves other jobs untouched
# ---------------------------------------------------------------------------

def test_cancellation_one_job_spare_another():
    repository, storage, service = build_service(auto_start=True)
    repository.records["a-1"] = make_record("a-1", "user-a")
    repository.records["b-1"] = make_record("b-1", "user-a")

    started_a = threading.Event()
    release_a = threading.Event()

    def runner(file_bytes, config=None, analysis_id=None, **kwargs):
        if analysis_id == "a-1":
            started_a.set()
            assert release_a.wait(10)
        return pipeline_result()

    service.pipeline_runner = runner

    assert service.job_queue.try_enqueue(job("a-1")) is True
    assert service.job_queue.try_enqueue(job("b-1")) is True
    assert started_a.wait(10)

    assert service.delete_analysis("a-1", "user-a") is True
    release_a.set()

    # b-1 must still complete normally.
    assert repository.completed_event.wait(10)
    assert repository.get_by_id("b-1", "user-a")["status"] == "completed"
    assert repository.get_by_id("a-1", "user-a") is None
    # A cancellation must not mark b-1 deleted or write completion for a-1.
    assert not any(data.get("status") == "completed" for aid, data in repository.updates if aid == "a-1")
    assert service.job_queue.contains("b-1") is False


# ---------------------------------------------------------------------------
# 7. Write-fence blocks artifact upload after deletion started
# ---------------------------------------------------------------------------

def test_write_fence_blocks_artifact_upload():
    repository, storage, service = build_service()
    repository.records["a-1"] = make_record("a-1", "user-a")

    with pytest.raises(AnalysisDeletionCancelled):
        service.pipeline_service.execute(
            analysis_id="a-1",
            user_id="user-a",
            file_bytes=b"x",
            pipeline_runner=lambda file_bytes, config=None, **kwargs: pipeline_result(),
            total_units_provider=lambda: 6,
            is_cancelled=lambda: False,
            write_gate=lambda write: False,
        )

    # No upload happened even though inference finished.
    assert storage.uploads == []
    assert not any(data.get("status") == "completed" for _, data in repository.updates)
    assert repository.get_by_id("a-1", "user-a")["status"] == "processing"


# ---------------------------------------------------------------------------
# 8. Write-fence blocks update completed after deletion started
# ---------------------------------------------------------------------------

def test_write_fence_blocks_completed_update():
    repository, storage, service = build_service()
    repository.records["a-1"] = make_record("a-1", "user-a")

    state = {"uploads": 0}

    def gate(write):
        if state["uploads"] < 4:
            state["uploads"] += 1
            write()
            return True
        return False

    with pytest.raises(AnalysisDeletionCancelled):
        service.pipeline_service.execute(
            analysis_id="a-1",
            user_id="user-a",
            file_bytes=b"x",
            pipeline_runner=lambda file_bytes, config=None, **kwargs: pipeline_result(),
            total_units_provider=lambda: 6,
            is_cancelled=lambda: False,
            write_gate=gate,
        )

    assert len(storage.uploads) == 4
    # Completed persistence was refused: nothing is marked completed/failed.
    assert not any(data.get("status") == "completed" for _, data in repository.updates)
    assert not any(data.get("status") == "failed" for _, data in repository.updates)
    assert repository.get_by_id("a-1", "user-a")["status"] == "processing"


# ---------------------------------------------------------------------------
# 9. Race: final persistence vs deletion — fence serialises them
# ---------------------------------------------------------------------------

def test_race_final_persistence_vs_deletion_no_resurrection():
    repository, storage, service = build_service(auto_start=True)
    repository.records["a-1"] = make_record("a-1", "user-a")

    at_final_write = threading.Event()
    release_final_write = threading.Event()

    def on_update(analysis_id, data):
        if analysis_id == "a-1" and data.get("status") == "completed":
            at_final_write.set()
            assert release_final_write.wait(10)

    repository.set_on_update(on_update)

    execute_done = threading.Event()
    original_execute = service.pipeline_service.execute

    def wrapped_execute(**kwargs):
        try:
            original_execute(**kwargs)
        finally:
            execute_done.set()

    service.pipeline_service.execute = wrapped_execute

    delete_done = threading.Event()
    delete_result = {}

    def delete_analysis_deleter():
        try:
            delete_result["value"] = service.delete_analysis("a-1", "user-a")
        finally:
            delete_done.set()

    assert service.job_queue.try_enqueue(job("a-1")) is True
    assert at_final_write.wait(10)

    deleter = threading.Thread(target=delete_analysis_deleter, daemon=True)
    deleter.start()

    release_final_write.set()
    assert execute_done.wait(10)
    assert delete_done.wait(10)

    # Serialised: final write happened first, then deletion removed the record.
    assert delete_result["value"] is True
    assert repository.get_by_id("a-1", "user-a") is None
    completed_index = next(
        index
        for index, event in enumerate(repository.events)
        if event[0] == "update" and event[2] == "completed"
    )
    delete_index = next(
        index for index, event in enumerate(repository.events) if event[0] == "delete"
    )
    assert completed_index < delete_index
    assert service.is_marked_for_deletion("a-1") is False


# ---------------------------------------------------------------------------
# 10. Race: enqueue while deletion in progress → job skipped after purge
# ---------------------------------------------------------------------------

def test_race_enqueue_vs_deletion_skip_tombstoned_job():
    repository, storage, service = build_service(auto_start=False)
    repository.records["a-1"] = make_record("a-1", "user-a")

    storage_delete_started = threading.Event()
    release_storage = threading.Event()

    def blocking_delete_analysis_files(paths, user_id=None, use_service_role=False):
        storage.removed.append((list(paths), user_id, use_service_role))
        storage_delete_started.set()
        assert release_storage.wait(10)
        return True

    storage.delete_analysis_files = blocking_delete_analysis_files
    storage.removed = []

    delete_done = threading.Event()
    delete_result = {}

    def delete_analysis_deleter():
        try:
            delete_result["value"] = service.delete_analysis("a-1", "user-a")
        finally:
            delete_done.set()

    deleter = threading.Thread(target=delete_analysis_deleter, daemon=True)
    deleter.start()

    assert storage_delete_started.wait(10)
    # Tombstone is held while storage cleanup is in flight.
    assert service.is_marked_for_deletion("a-1") is True

    # An enqueue that lands concurrently lands in a tombstoned bucket: the
    # worker pops it and skips the pipeline.
    assert service.job_queue.try_enqueue(job("a-1")) is True
    assert service.job_queue.drain_one() is True
    assert service.job_queue.contains("a-1") is False

    release_storage.set()
    assert delete_done.wait(10)
    assert delete_result["value"] is True
    assert repository.get_by_id("a-1", "user-a") is None
    assert service.is_marked_for_deletion("a-1") is False


# ---------------------------------------------------------------------------
# 11. Storage cleanup failure → tombstone retained
# ---------------------------------------------------------------------------

def test_storage_cleanup_failure_retains_tombstone():
    repository, storage, service = build_service(auto_start=False)
    storage.remove_result = False
    repository.records["a-1"] = make_record("a-1", "user-a")

    assert service.delete_analysis("a-1", "user-a") is True
    assert repository.get_by_id("a-1", "user-a") is None
    assert service.is_marked_for_deletion("a-1") is True  # protection kept
    # Writes are still refused while storage state is unresolved.
    write_happened = []
    allowed = service._persist_if_allowed("a-1", lambda: write_happened.append(True))
    assert allowed is False
    assert write_happened == []


# ---------------------------------------------------------------------------
# 12. Storage cleanup raises → same residual-risk behaviour, tombstone kept
# ---------------------------------------------------------------------------

def test_storage_cleanup_raises_retains_tombstone():
    repository, storage, service = build_service(auto_start=False)
    storage.delete_raises = True
    repository.records["a-1"] = make_record("a-1", "user-a")

    assert service.delete_analysis("a-1", "user-a") is True
    assert repository.get_by_id("a-1", "user-a") is None
    assert service.is_marked_for_deletion("a-1") is True


# ---------------------------------------------------------------------------
# 13. Tombstone cleared after successful deletion
# ---------------------------------------------------------------------------

def test_tombstone_cleared_after_successful_deletion():
    repository, storage, service = build_service(auto_start=False)
    repository.records["a-1"] = make_record("a-1", "user-a")

    assert service.delete_analysis("a-1", "user-a") is True
    assert service.is_marked_for_deletion("a-1") is False


def test_db_delete_failure_releases_tombstone_and_keeps_record():
    repository, storage, service = build_service(auto_start=False)
    repository.fail_delete = True
    repository.records["a-1"] = make_record("a-1", "user-a")
    assert service.job_queue.try_enqueue(job("a-1")) is True

    with pytest.raises(APIError) as excinfo:
        service.delete_analysis("a-1", "user-a")

    assert excinfo.value.status_code == 500
    assert excinfo.value.code == "DATABASE_ERROR"
    # Nothing destructive happened: record intact, queue untouched, storage
    # never called, and the fence is released so the queued job can proceed.
    assert repository.get_by_id("a-1", "user-a")["status"] == "processing"
    assert service.job_queue.contains("a-1") is True
    assert storage.removed == []
    assert service.is_marked_for_deletion("a-1") is False
    assert service.is_cancelled_for_deletion("a-1") is False


# ---------------------------------------------------------------------------
# 14. Ownership check still enforced
# ---------------------------------------------------------------------------

def test_delete_ownership_check_still_enforced():
    repository, storage, service = build_service(auto_start=False)
    repository.records["a-1"] = make_record("a-1", "user-b")

    with pytest.raises(APIError) as excinfo:
        service.delete_analysis("a-1", "user-a")

    assert excinfo.value.status_code == 404
    assert excinfo.value.code == "ANALYSIS_NOT_FOUND"
    assert repository.get_by_id("a-1", "user-b")["status"] == "processing"
    assert service.is_marked_for_deletion("a-1") is False
    assert storage.removed == []


# ---------------------------------------------------------------------------
# 15. Queue FIFO and capacity unchanged (1 active + 3 waiting)
# ---------------------------------------------------------------------------

def test_queue_fifo_and_capacity_unchanged():
    seen = []
    q = AnalysisJobQueue(
        runner=lambda job: seen.append(job["analysis_id"]),
        auto_start=False,
    )

    assert q.capacity == 4
    assert AnalysisJobQueue.MAX_WAITING == 3

    for i in range(4):
        assert q.try_enqueue({"analysis_id": f"j{i}", "user_id": "user-a", "file_bytes": b"x"}) is True
    # Full: at most one active + three waiting.
    assert q.try_enqueue({"analysis_id": "j5", "user_id": "user-a", "file_bytes": b"x"}) is False

    assert q.purge_job("j1") is True
    assert q.pending_count() == 3

    while q.drain_one():
        pass
    assert seen == ["j0", "j2", "j3"]  # FIFO order preserved across purge

    # Capacity is freed by the purge.
    assert q.try_enqueue({"analysis_id": "j6", "user_id": "user-a", "file_bytes": b"x"}) is True
    assert q.pending_count() == 1
    assert q.drain_one() is True
    assert seen == ["j0", "j2", "j3", "j6"]
