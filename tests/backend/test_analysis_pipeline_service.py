"""Focused tests for the extracted AnalysisPipelineService (refactoring stage 2).

Covers the mandatory refactoring contract items: the pipeline is callable from
its new service, receives the same parameters, keeps the same stage order and
persistence behavior, still uses the stage-1 reporter and queue, and introduces
no circular import or public-interface break.
"""
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from ai.config.model_config import MODEL_CONFIG
from src.core.errors import APIError
from src.services.analysis_pipeline_service import AnalysisPipelineService
from src.services.analysis_queue_service import AnalysisJobQueue
from src.services.analysis_service import AnalysisService
from src.services.storage_service import StorageService

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = REPO_ROOT / "Backend"


class FakeRepository:
    def __init__(self):
        self.records = {}
        self.updates = []

    def create(self, user_id, data, use_service_role=False):
        record = dict(data)
        self.records[data["id"]] = record
        return record

    def get_by_id(self, analysis_id, user_id, use_service_role=False):
        record = self.records.get(analysis_id)
        if record and record.get("user_id") == user_id:
            return record
        return None

    def update(self, analysis_id, user_id, data, use_service_role=False):
        record = self.records.get(analysis_id)
        if not record or record.get("user_id") != user_id:
            return None
        record.update(data)
        self.updates.append(dict(data))
        return record


class FakeStorage:
    """Path generation delegates to the real StorageService (faithful shapes)."""

    def __init__(self):
        self.uploads = []
        self.deleted_paths = []

    def generate_original_image_path(self, user_id, analysis_id, extension):
        return StorageService().generate_original_image_path(user_id, analysis_id, extension)

    def generate_binary_mask_path(self, user_id, analysis_id):
        return StorageService().generate_binary_mask_path(user_id, analysis_id)

    def generate_segmentation_overlay_path(self, user_id, analysis_id):
        return StorageService().generate_segmentation_overlay_path(user_id, analysis_id)

    def generate_gradcam_heatmap_path(self, user_id, analysis_id):
        return StorageService().generate_gradcam_heatmap_path(user_id, analysis_id)

    def generate_gradcam_overlay_path(self, user_id, analysis_id):
        return StorageService().generate_gradcam_overlay_path(user_id, analysis_id)

    def upload_file(self, path, file_bytes, content_type, user_id, use_service_role=False):
        self.uploads.append((path, file_bytes, content_type, user_id, use_service_role))
        return path

    def delete_file(self, path, user_id, use_service_role=False):
        self.deleted_paths.append((path, user_id, use_service_role))
        return True

    def create_signed_url(self, path, expires_in, user_id, use_service_role=False):
        return f"signed://temporary/{path}"


def image_bytes(image_format):
    import io
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


def _build_service():
    """AnalysisService wired the same way the API layer wires it (no worker)."""
    repository = FakeRepository()
    storage = FakeStorage()
    service = AnalysisService(
        repository=repository,
        storage_service=storage,
        pipeline_runner=lambda file_bytes, config, **kwargs: pipeline_result(),
        # Deterministic: jobs only run when the test steps the queue.
        auto_start_worker=False,
    )
    return repository, storage, service


def test_pipeline_service_is_wired_with_shared_dependencies():
    repository, storage, service = _build_service()

    assert isinstance(service.pipeline_service, AnalysisPipelineService)
    assert service.pipeline_service.repository is repository
    assert service.pipeline_service.storage_service is storage


def test_queue_still_uses_stage1_implementation():
    _repository, _storage, service = _build_service()

    assert isinstance(service.job_queue, AnalysisJobQueue)
    assert service.job_queue.capacity == 4
    assert service.job_queue.pending_count() == 0


def test_pipeline_receives_the_same_parameters_as_before():
    repository, _storage, service = _build_service()

    captured = {}

    def runner(file_bytes, config, on_phase=None, on_pass=None, analysis_id=None, **kwargs):
        captured.update(
            file_bytes=file_bytes,
            config=config,
            on_phase=on_phase,
            on_pass=on_pass,
            analysis_id=analysis_id,
        )
        return pipeline_result()

    service.pipeline_runner = runner
    repository.create(
        user_id="user-a",
        data={"id": "a-1", "user_id": "user-a", "status": "processing"},
        use_service_role=True,
    )
    service._execute_pipeline(analysis_id="a-1", user_id="user-a", file_bytes=b"data")

    assert captured["file_bytes"] == b"data"
    assert captured["config"] is MODEL_CONFIG
    assert captured["analysis_id"] == "a-1"
    assert callable(captured["on_phase"])
    assert callable(captured["on_pass"])


def test_completed_record_is_written_after_all_four_artifacts():
    repository, storage, service = _build_service()
    repository.create(
        user_id="user-a",
        data={"id": "a-1", "user_id": "user-a", "status": "processing"},
        use_service_role=True,
    )

    timeline = []
    original_update = repository.update
    original_upload = storage.upload_file

    def spy_update(analysis_id, user_id, data, use_service_role=False):
        timeline.append(("update", dict(data)))
        return original_update(analysis_id, user_id, data, use_service_role)

    def spy_upload(path, file_bytes, content_type, user_id, use_service_role=False):
        timeline.append(("upload", path))
        return original_upload(path, file_bytes, content_type, user_id, use_service_role)

    repository.update = spy_update
    storage.upload_file = spy_upload
    service._execute_pipeline(analysis_id="a-1", user_id="user-a", file_bytes=b"data")

    record = repository.records["a-1"]
    assert record["status"] == "completed"
    assert record["progress_percent"] == 100
    assert record["current_step"] == "completed"

    uploads = [entry for entry in timeline if entry[0] == "upload"]
    assert len(uploads) == 4
    # The completed update must be the terminal event, after every artifact.
    final_entry = timeline[-1]
    assert final_entry[0] == "update"
    assert final_entry[1]["status"] == "completed"
    # Persisted artifact paths match the uploaded artifacts.
    uploaded_paths = {entry[1] for entry in uploads}
    assert record["binary_mask_path"] in uploaded_paths
    assert record["segmentation_overlay_path"] in uploaded_paths
    assert record["gradcam_heatmap_path"] in uploaded_paths
    assert record["gradcam_overlay_path"] in uploaded_paths


def test_pipeline_failure_marks_failed_and_keeps_last_progress():
    repository, _storage, service = _build_service()
    repository.create(
        user_id="user-a",
        data={"id": "a-1", "user_id": "user-a", "status": "processing"},
        use_service_role=True,
    )

    def boom(file_bytes, config, on_phase=None, on_pass=None, **kwargs):
        if on_phase is not None:
            on_phase("inference")
        raise RuntimeError("private pipeline traceback")

    service.pipeline_runner = boom

    try:
        service._execute_pipeline(analysis_id="a-1", user_id="user-a", file_bytes=b"data")
    except APIError as error:
        assert error.code == "AI_PIPELINE_ERROR"
        assert isinstance(error.__cause__, RuntimeError)
    else:
        raise AssertionError("expected APIError from a failing pipeline")

    record = repository.records["a-1"]
    assert record["status"] == "failed"
    assert record["error_code"] == "AI_PIPELINE_ERROR"
    assert record["gradcam_status"] == "failed"
    assert 0 <= record["progress_percent"] < 100


def test_progress_reporting_still_works_through_pipeline_service():
    repository, _storage, service = _build_service()
    repository.create(
        user_id="user-a",
        data={"id": "a-1", "user_id": "user-a", "status": "processing"},
        use_service_role=True,
    )

    from ai.inference.pipeline import (
        PHASE_ARTIFACT_COMPOSITION,
        PHASE_GRADCAM,
        PHASE_INFERENCE,
    )

    def progress_pipeline(file_bytes, config, on_phase=None, on_pass=None, **kwargs):
        for _ in range(5):
            if on_pass is not None:
                on_pass()
        for name in (PHASE_INFERENCE, PHASE_GRADCAM, PHASE_ARTIFACT_COMPOSITION):
            if on_phase is not None:
                on_phase(name)
        return pipeline_result()

    service.pipeline_runner = progress_pipeline
    service._execute_pipeline(analysis_id="a-1", user_id="user-a", file_bytes=b"data")

    percents = [update["progress_percent"] for update in repository.updates
                if "progress_percent" in update]
    assert percents, "expected progress writes"
    assert all(0 <= value <= 100 for value in percents)
    assert percents == sorted(percents)
    assert percents.count(100) == 1
    assert percents[-1] == 100


def test_public_interface_lama_tetap_kompatibel():
    from src.services.analysis_service import (
        AnalysisJobQueue as QueueReexport,
        AnalysisProgressReporter as ReporterReexport,
    )

    repository, _storage, service = _build_service()

    # Old entry point still exists on the service and delegates to the new one.
    assert callable(service._execute_pipeline)
    calls = []
    service.pipeline_service.execute = (
        lambda **kwargs: calls.append(kwargs)
    )
    service._execute_pipeline(analysis_id="a-1", user_id="user-a", file_bytes=b"data")
    assert len(calls) == 1
    assert calls[0]["analysis_id"] == "a-1"
    assert calls[0]["user_id"] == "user-a"
    assert calls[0]["file_bytes"] == b"data"
    assert callable(calls[0]["pipeline_runner"])
    assert callable(calls[0]["total_units_provider"])

    # Stage-1 re-exports are unchanged.
    assert QueueReexport is AnalysisJobQueue
    assert ReporterReexport.__name__ == "AnalysisProgressReporter"


def test_pipeline_service_import_has_no_circular_import():
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(BACKEND_PATH), str(REPO_ROOT), env.get("PYTHONPATH", "")]
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys;"
                "import src.services.analysis_service as a;"
                "import src.services.analysis_pipeline_service as p;"
                "print(a.AnalysisService.__name__);"
                "print(p.AnalysisPipelineService.__name__);"
                "print(hasattr(p, 'AnalysisService'));"
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
    assert lines == ["AnalysisService", "AnalysisPipelineService", "False"]
