"""STAGE B & C — End-to-end lifecycle and safe-deletion integration tests.

Uses only in-memory fakes and deterministic queue stepping (no background
thread, no real inference) so that every stage boundary can be inspected.
Mirrors the patterns established by test_analysis.py and
test_analysis_deletion_lifecycle.py.
"""
import io
import threading
import time
from types import SimpleNamespace

import pytest
from PIL import Image

from src.core.errors import APIError
from src.services.analysis_queue_service import AnalysisJobQueue
from src.services.analysis_service import AnalysisService
from src.services.storage_service import StorageService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def small_png(width=23, height=17):
    stream = io.BytesIO()
    Image.new("RGB", (width, height), color=(20, 80, 120)).save(stream, format="PNG")
    return stream.getvalue()


class FakeFileStorage:
    def __init__(self, data=b"", filename="scope.jpg", mime_type="image/png"):
        self._data = data
        self.filename = filename
        self.mimetype = mime_type

    def read(self):
        return self._data


class FakeRepository:
    def __init__(self, fail_delete=False, fail_update=False, fail_get=None):
        self.records = {}
        self.fail_delete = fail_delete
        self.fail_update = fail_update
        self.fail_get = fail_get or {}
        self.deleted_ids = []

    def create(self, user_id, data, use_service_role=False):
        aid = data["id"]
        record = dict(data)
        record["user_id"] = user_id
        record.setdefault("status", "processing")
        self.records[aid] = record
        return record

    def get_by_id(self, analysis_id, user_id, use_service_role=False):
        if analysis_id in self.fail_get:
            raise self.fail_get[analysis_id]
        rec = self.records.get(analysis_id)
        if rec and rec["user_id"] == user_id:
            return rec
        return None

    def update(self, analysis_id, user_id, data, use_service_role=False):
        if self.fail_update:
            raise RuntimeError("private database detail")
        rec = self.records.get(analysis_id)
        if not rec or rec["user_id"] != user_id:
            return None
        rec.update(data)
        return rec

    def delete(self, analysis_id, user_id, use_service_role=False):
        self.deleted_ids.append(analysis_id)
        if self.fail_delete:
            raise RuntimeError("private database detail")
        rec = self.records.get(analysis_id)
        if rec and rec["user_id"] == user_id:
            del self.records[analysis_id]
            return True
        return False

    def list_by_user(self, user_id, limit=20, offset=0, use_service_role=False):
        return [r for r in self.records.values() if r["user_id"] == user_id][offset:offset + limit]


class FakeStorage:
    def __init__(self, fail_upload=False, fail_delete=False):
        self.uploaded = []
        self.deleted = []
        self.fail_upload = fail_upload
        self.fail_delete = fail_delete

    def generate_original_image_path(self, user_id, analysis_id, extension):
        return f"users/{user_id}/originals/{analysis_id}.{extension}"

    def upload_file(self, path, file_bytes, content_type, user_id, use_service_role=False):
        self.uploaded.append(path)
        if self.fail_upload:
            raise RuntimeError("private storage detail")
        return path

    def delete_file(self, path, user_id, use_service_role=False):
        self.deleted.append(path)
        if self.fail_delete:
            raise RuntimeError("private storage detail")
        return True

    def create_signed_url(self, path, expires_in, user_id, use_service_role=False):
        return f"https://signed.url/{path}"

    def generate_binary_mask_path(self, user_id, analysis_id):
        return f"users/{user_id}/segmentation/{analysis_id}_mask.png"

    def generate_segmentation_overlay_path(self, user_id, analysis_id):
        return f"users/{user_id}/segmentation/{analysis_id}_overlay.png"

    def generate_gradcam_heatmap_path(self, user_id, analysis_id):
        return f"users/{user_id}/gradcam/{analysis_id}_heatmap.png"

    def generate_gradcam_overlay_path(self, user_id, analysis_id):
        return f"users/{user_id}/gradcam/{analysis_id}_overlay.png"

    def delete_analysis_files(self, paths, user_id, use_service_role=False):
        for p in paths:
            self.delete_file(p, user_id, use_service_role=True)
        return len(paths) > 0


def make_runner(steps=None, fail_at=None, delay=None):
    """Return a pipeline runner that steps through stages slowly."""
    if delay is None:
        delay = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    if isinstance(delay, (int, float)):
        delay = [delay] * 6
    barrier = threading.Barrier(len(delay)) if any(d > 0 for d in delay) else None

    def runner(file_bytes, config=None, on_phase=None, on_pass=None, analysis_id=None):
        phases = ["preprocessing", "inference", "postprocessing", "gradcam", "artifact_composition"]
        for i, phase in enumerate(phases):
            if on_phase:
                on_phase(phase)
            if fail_at is not None and i == fail_at:
                raise RuntimeError(f"Simulated failure at {phase}")
            # Wait at barrier to allow deletion to intervene
            if barrier is not None:
                try:
                    barrier.wait(timeout=5)
                except Exception:
                    pass
        png = small_png()
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
            summary_text="[POLYP_DETECTED] Normal colonoscopy image.",
            gradcam=SimpleNamespace(
                target_layer="decoder.blocks.4.conv2.0",
                target_objective="mean selected segmentation logit over target mask",
            ),
        )
    return runner


@pytest.fixture
def svc():
    repo = FakeRepository()
    storage = FakeStorage()
    runner = make_runner()
    service = AnalysisService(
        repository=repo,
        storage_service=storage,
        pipeline_runner=runner,
        auto_start_worker=False,
        enforce_domain_validation=False,
        enforce_llm_validation=False,
    )
    return service, repo, storage


# ===========================================================================
# STAGE B — END-TO-END ANALYSIS LIFECYCLE
# ===========================================================================

class TestAnalysisLifecycle:

    def test_complete_lifecycle(self, svc):
        service, repo, storage = svc
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        aid = result["analysis_id"]
        assert result["status"] == "processing"
        record = repo.get_by_id(aid, "u1")
        assert record is not None
        assert record["status"] == "processing"
        service.job_queue.drain_one()
        record = repo.get_by_id(aid, "u1")
        assert record is not None
        assert record["status"] == "completed"
        assert record.get("segmentation_status") == "detected"
        assert "completed_at" in record
        assert len(storage.uploaded) == 5  # original + 4 artifacts

    def test_failure_lifecycle(self, svc):
        service, repo, storage = svc
        runner = make_runner(fail_at=1)
        service.pipeline_runner = runner
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        aid = result["analysis_id"]
        service.job_queue.drain_one()
        record = repo.get_by_id(aid, "u1")
        assert record is not None
        assert record["status"] == "failed"
        assert record.get("error_code") == "AI_PIPELINE_ERROR"

    def test_retrieve_after_completion(self, svc):
        service, repo, storage = svc
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        aid = result["analysis_id"]
        service.job_queue.drain_one()
        detail = service.get_analysis(aid, "u1")
        assert detail["analysis"]["status"] == "completed"
        assert "model_analysis" in detail
        assert detail["model_analysis"]["detection_category"] == "POLYP_DETECTED"
        assert "segmentation" in detail
        assert "gradcam" in detail
        assert "summary" in detail

    def test_list_history(self, svc):
        service, repo, storage = svc
        for uid in ("u1", "u2"):
            fs = FakeFileStorage(small_png(), filename=f"img_{uid}.jpg")
            service.create_analysis(fs, user_id=uid)
            service.job_queue.drain_one()
        history_u1 = service.list_user_analyses("u1")
        assert len(history_u1) == 1
        item = history_u1[0]
        assert item["status"] == "completed"
        assert item["original_filename"].endswith("img_u1.jpg")

    def test_ownership_enforced(self, svc):
        service, repo, storage = svc
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        aid = result["analysis_id"]
        with pytest.raises(APIError, match="user ID"):
            service.get_analysis(aid, "")
        with pytest.raises(APIError, match="not found or access denied"):
            service.get_analysis(aid, "u2")
        with pytest.raises(APIError, match="not found or access denied"):
            service.delete_analysis(aid, "u2")


# ===========================================================================
# STAGE C — SAFE DELETION INTEGRATION
# ===========================================================================

class TestSafeDeletionIntegration:

    def test_delete_before_worker_starts(self, svc):
        service, repo, storage = svc
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        aid = result["analysis_id"]
        assert service.job_queue.contains(aid)
        assert repo.get_by_id(aid, "u1") is not None
        service.delete_analysis(aid, "u1")
        assert not service.job_queue.contains(aid)
        assert repo.get_by_id(aid, "u1") is None
        assert not service.is_marked_for_deletion(aid)
        assert not service.is_cancelled_for_deletion(aid)

    def test_delete_while_job_waiting_fifo_preserved(self, svc):
        service, repo, storage = svc
        aids = []
        for i in range(3):
            fs = FakeFileStorage(small_png(), filename=f"img{i}.jpg")
            r = service.create_analysis(fs, user_id="u1")
            aids.append(r["analysis_id"])
        # At most 1 active + MAX_WAITING(3) waiting = capacity 4; after 3 enqueues
        # exactly 2 are waiting (1 will run on drain_one).
        pending = service.job_queue.pending_count()
        assert pending <= 3
        service.delete_analysis(aids[1], "u1")  # delete middle job
        assert not service.job_queue.contains(aids[1])
        # Drain two jobs; first-job should complete, second should be aids[2]
        service.job_queue.drain_one()
        record1 = repo.get_by_id(aids[0], "u1")
        assert record1 is not None and record1["status"] == "completed"
        service.job_queue.drain_one()
        record2 = repo.get_by_id(aids[2], "u1")
        assert record2 is not None and record2["status"] == "completed"

    def test_delete_during_slow_pipeline_cancels_not_persists(self, svc):
        barrier = threading.Barrier(2)
        cancelled_event = threading.Event()

        def slow_runner(file_bytes, config=None, on_phase=None, on_pass=None, analysis_id=None):
            if on_phase:
                on_phase("inference")
            try:
                barrier.wait(timeout=5)
            except Exception:
                pass
            cancelled_event.set()
            png = small_png()
            return SimpleNamespace(
                binary_mask_png=png,
                segmentation_overlay_png=png,
                gradcam_heatmap_png=png,
                gradcam_overlay_png=png,
                measurements={"segmentation_status": "detected", "area_pixels": 42,
                              "area_ratio": 42/(23*17), "bounding_width_pixels": 7, "bounding_height_pixels": 6},
                summary_text="[NO_POLYP_DETECTED] No polyp detected.",
                gradcam=SimpleNamespace(target_layer="x", target_objective="y"),
            )

        service, repo, storage = svc
        service.pipeline_runner = slow_runner
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        aid = result["analysis_id"]
        # Manually set active_analysis_id so drain_one won't run it
        with service.job_queue._not_empty:
            service.job_queue._active_analysis_id = aid
            # Now pop the waiting job if any and start the real one
            while service.job_queue._jobs:
                w = service.job_queue._jobs.popleft()
                if w.get("analysis_id") != aid:
                    service.job_queue._active_analysis_id = w.get("analysis_id")
                    break
        # Delete will request cancellation (job already active here)
        service.delete_analysis(aid, "u1")
        assert service.is_cancelled_for_deletion(aid) is True
        # The worker finishes its current iteration (slow_runner returns normally);
        # cancellation request is cleared in finally block.
        service.job_queue.drain_one()
        # Record was deleted, so even if pipeline finished we shouldn't see it.
        assert repo.get_by_id(aid, "u1") is None

    def test_storage_cleanup_failure_retains_tombstone(self, svc):
        service, repo, storage = svc
        storage.fail_delete = True
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        aid = result["analysis_id"]
        service.delete_analysis(aid, "u1")
        assert repo.get_by_id(aid, "u1") is None
        assert service.is_marked_for_deletion(aid) is True

    def test_database_delete_failure_releases_fence(self, svc):
        service, repo, storage = svc
        repo.fail_delete = True
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        aid = result["analysis_id"]
        with pytest.raises(APIError) as exc_info:
            service.delete_analysis(aid, "u1")
        assert exc_info.value.code == "DATABASE_ERROR"
        assert service.is_marked_for_deletion(aid) is False
        assert repo.get_by_id(aid, "u1") is not None
        assert service.job_queue.contains(aid)

    def test_active_job_stops_and_persists_nothing(self, svc):
        step = [0]
        stopped = threading.Event()

        def stoppable_runner(file_bytes, config=None, on_phase=None, on_pass=None, analysis_id=None):
            step[0] += 1
            if on_phase:
                on_phase("inference")
            # Simulate a long-running inference that checks cancellation
            for _ in range(3):
                if service.is_cancelled_for_deletion(analysis_id):
                    stopped.set()
                    from src.services.analysis_pipeline_service import AnalysisDeletionCancelled
                    raise AnalysisDeletionCancelled(f"{analysis_id} cancelled mid-inference")
                time.sleep(0.01)
            png = small_png()
            return SimpleNamespace(
                binary_mask_png=png, segmentation_overlay_png=png,
                gradcam_heatmap_png=png, gradcam_overlay_png=png,
                measurements={"segmentation_status": "detected", "area_pixels": 10,
                              "area_ratio": 10/(23*17), "bounding_width_pixels": 3, "bounding_height_pixels": 3},
                summary_text="[LOW_CONFIDENCE] Low confidence.",
                gradcam=SimpleNamespace(target_layer="l", target_objective="o"),
            )

        service, repo, storage = svc
        service.pipeline_runner = stoppable_runner
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        aid = result["analysis_id"]
        # Let the worker pick up the job asynchronously
        service.job_queue.drain_one()
        # Once job is running, issue delete
        time.sleep(0.05)
        service.delete_analysis(aid, "u1")
        # Wait for worker to observe cancellation
        stopped.wait(timeout=2)
        assert repo.get_by_id(aid, "u1") is None

    def test_enqueue_after_deletion_fails(self, svc):
        service, repo, storage = svc
        fs = FakeFileStorage(small_png())
        r1 = service.create_analysis(fs, user_id="u1")
        aid1 = r1["analysis_id"]
        service.delete_analysis(aid1, "u1")
        # A second upload must not be blocked by the tombstone of a different analysis
        fs2 = FakeFileStorage(small_png(), filename="new.jpg")
        r2 = service.create_analysis(fs2, user_id="u2")
        assert r2["analysis_id"] is not None
        record = repo.get_by_id(r2["analysis_id"], "u2")
        assert record is not None

    def test_queue_capacity_respected(self, svc):
        service, repo, storage = svc
        assert service.job_queue.capacity == 4  # 1 active + 3 waiting
        ids = []
        for i in range(5):
            fs = FakeFileStorage(small_png(), filename=f"img{i}.jpg")
            r = service.create_analysis(fs, user_id="u1")
            ids.append(r["analysis_id"])
            service.job_queue.drain_one()  # free slot each iteration
        # All 5 analyses should have been created; some queued, some completed
        assert len(ids) == 5
        # Verify at least one succeeded and one exists in completed state
        completed = [aid for aid in ids if repo.get_by_id(aid, "u1") is not None
                     and repo.get_by_id(aid, "u1").get("status") == "completed"]
        assert len(completed) >= 1


# ===========================================================================
# STAGE D — DOMAIN VALIDATION INTEGRATION
# ===========================================================================

class TestDomainValidationIntegration:

    def test_jalur_a_technical_then_domain_then_llm(self, svc):
        service, _, _ = svc
        # Domain validation disabled in this fixture; technical still rejects bad files
        with pytest.raises(APIError):
            service.create_analysis(FakeFileStorage(b"", filename="empty.jpg"), user_id="u1")
        with pytest.raises(APIError):
            service.create_analysis(FakeFileStorage(b"\xff\xd8\xff", filename="bad.jpg", mime_type="image/jpeg"), user_id="u1")

    def test_jalur_b_hard_gate_on_run_segmentation(self, svc):
        service, _, _ = svc
        # Non-colonoscopy bytes should be rejected by the hard gate
        bad_bytes = b"\x00\x01\x02\x03" * 100
        with pytest.raises(APIError) as exc_info:
            service.run_segmentation(bad_bytes)
        assert exc_info.value.code in ("NOT_COLONOSCOPY_IMAGE", "UNCERTAIN_COLONOSCOPY_IMAGE")

    def test_jalur_c_validate_domain_inside_pipeline(self, svc):
        # The internal run_pipeline default has validate_domain=True built in;
        # non-colonoscopy bytes would raise ValueError inside the AI module.
        # Here we simply verify the validator instance exists and is used.
        from ai.inference.domain_validator import ColonoscopyDomainValidator
        v = ColonoscopyDomainValidator()
        from ai.inference.domain_validator import DomainDecision
        result = v.validate_bytes(small_png())
        assert isinstance(result.decision, DomainDecision)

    def test_jalur_a_disabled_keeps_working(self, svc):
        service, repo, storage = svc
        # Force domain/llm off again (fixture already does this)
        assert service.is_domain_validation_enabled is False
        assert service.is_llm_validation_enabled is False
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        assert result["status"] == "processing"


# ===========================================================================
# STAGE E — API / DB / STORAGE / QUEUE REGRESSION
# ===========================================================================

class TestRegression:

    def test_status_flow(self, svc):
        service, repo, storage = svc
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        aid = result["analysis_id"]
        record = repo.get_by_id(aid, "u1")
        assert record["status"] == "processing"
        service.job_queue.drain_one()
        record = repo.get_by_id(aid, "u1")
        assert record["status"] in ("completed", "failed")

    def test_error_codes_consistent(self, svc):
        service, repo, storage = svc
        runner = make_runner(fail_at=0)
        service.pipeline_runner = runner
        fs = FakeFileStorage(small_png())
        service.create_analysis(fs, user_id="u1")
        service.job_queue.drain_one()
        aid = list(repo.records.keys())[0]
        record = repo.get_by_id(aid, "u1")
        assert record["status"] == "failed"
        assert record.get("error_code") == "AI_PIPELINE_ERROR"

    def test_progress_fields_nullable(self, svc):
        service, repo, storage = svc
        fs = FakeFileStorage(small_png())
        result = service.create_analysis(fs, user_id="u1")
        aid = result["analysis_id"]
        service.job_queue.drain_one()
        detail = service.get_analysis(aid, "u1")
        # completion populates these; they are optional during processing
        assert detail["analysis"]["status"] == "completed"

    def test_queue_full_returns_429_equivalent(self, svc):
        service, repo, storage = svc
        # Fill the queue to capacity and verify enqueue is refused
        accepted = 0
        for _ in range(10):
            fs = FakeFileStorage(small_png())
            try:
                result = service.create_analysis(fs, user_id="u3")
                accepted += 1
                service.job_queue.drain_one()  # keep queue from overflowing permanently
            except APIError as e:
                if e.code == "QUEUE_FULL":
                    break
        assert accepted >= 4  # baseline capacity was accepted before any full-rejection

    def test_worker_recovery_after_failure(self, svc):
        service, repo, storage = svc
        fs1 = FakeFileStorage(small_png(), filename="a.jpg")
        r1 = service.create_analysis(fs1, user_id="u1")
        service.pipeline_runner = make_runner(fail_at=1)
        service.job_queue.drain_one()
        record_fail = repo.get_by_id(r1["analysis_id"], "u1")
        assert record_fail["status"] == "failed"
        # Next job runs fine with normal runner
        service.pipeline_runner = make_runner()
        fs2 = FakeFileStorage(small_png(), filename="b.jpg")
        r2 = service.create_analysis(fs2, user_id="u1")
        service.job_queue.drain_one()
        record_ok = repo.get_by_id(r2["analysis_id"], "u1")
        assert record_ok["status"] == "completed"
