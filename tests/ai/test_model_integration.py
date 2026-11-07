from dataclasses import replace
from pathlib import Path

import pytest
import torch
from PIL import Image

from ai.config.model_config import MODEL_CONFIG, ModelConfig, ModelConfigurationError
from ai.inference.model_service import ModelService
from ai.inference.preprocessing import IMAGENET_MEAN, IMAGENET_STD, prepare_image
from ai.inference.segmentation import predict


def test_verified_model_checkpoint_hash_and_strict_load_cpu(monkeypatch):
    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    service = ModelService(MODEL_CONFIG)
    model = service.load()

    assert MODEL_CONFIG.checkpoint_path.is_file()
    assert MODEL_CONFIG.checkpoint_sha256_matches()
    assert service.device.type == "cpu"
    assert model.training is False
    metadata = service.metadata()
    assert metadata["checkpoint_sha256"] == (
        "46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581"
    )
    assert metadata["threshold"] == 0.55
    assert service.load() is model


def test_model_configuration_matches_verified_runtime():
    assert MODEL_CONFIG.architecture == "UNet"
    assert MODEL_CONFIG.encoder == "resnet50"
    assert MODEL_CONFIG.decoder_attention == "scse"
    assert MODEL_CONFIG.input_size == 512
    assert MODEL_CONFIG.input_channels == 3
    assert MODEL_CONFIG.threshold == 0.55
    assert MODEL_CONFIG.tta_enabled is True
    assert MODEL_CONFIG.multiscale_enabled is True
    assert MODEL_CONFIG.tta_scales == (0.85, 0.95, 1.0, 1.05, 1.15)
    assert MODEL_CONFIG.postprocessing_min_area == 25
    assert MODEL_CONFIG.contour_smoothing is True
    assert MODEL_CONFIG.smoothing_epsilon == 0.005


def test_checkpoint_path_traversal_is_rejected(monkeypatch):
    monkeypatch.setenv("MODEL_CHECKPOINT_PATH", "ai/models/../secret.pth")
    config = ModelConfig()
    try:
        _ = config.checkpoint_path
    except ModelConfigurationError:
        return
    raise AssertionError("checkpoint traversal path was accepted")


def test_preprocessing_returns_verified_tensor_shape_and_normalization():
    image = Image.new("L", (37, 19), color=128)
    tensor = prepare_image(image)

    assert tensor.shape == (1, 3, 512, 512)
    assert tensor.dtype == torch.float32
    expected = (128 / 255 - IMAGENET_MEAN[0]) / IMAGENET_STD[0]
    assert torch.isclose(tensor[0, 0, 0, 0], torch.tensor(expected), atol=1e-6)
    assert torch.equal(tensor[0, 0], tensor[0, 1]) is False


def test_real_checkpoint_raw_inference_contract(monkeypatch):
    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    config = replace(MODEL_CONFIG, tta_enabled=False, multiscale_enabled=False)
    service = ModelService(config)
    image = Image.new("RGB", (512, 512), color=(80, 100, 120))
    result = predict(image, model_service=service, config=config)

    assert result.probability_map.shape == (1, 1, 512, 512)
    assert torch.all(result.probability_map >= 0)
    assert torch.all(result.probability_map <= 1)
    assert result.binary_mask.shape == (1, 1, 512, 512)
    assert set(torch.unique(result.binary_mask).tolist()).issubset({0, 1})
    assert result.threshold == 0.55


def test_checkpoint_file_has_locked_name():
    assert MODEL_CONFIG.checkpoint_path.name == (
        "PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth"
    )
    assert Path(MODEL_CONFIG.checkpoint_path).suffix == ".pth"


# ---------------------------------------------------------------------------
# Batch P-03: progress-instrumentation contract for segmentation/pipeline.
# ---------------------------------------------------------------------------


def test_count_forward_passes_matches_executed_loops():
    """The reported total must equal the loops that actually run.

    The active ``predict``/``_predict_scale`` code always runs the 5 fixed
    orientations and never reads ``tta_enabled``, so the count is derived from
    the scale loop plus ORIENTATION_COUNT — not from any config flag.
    """
    from ai.inference.segmentation import ORIENTATION_COUNT, count_forward_passes

    assert ORIENTATION_COUNT == 5
    assert count_forward_passes(MODEL_CONFIG) == len(MODEL_CONFIG.tta_scales) * 5
    # multiscale off -> single scale -> exactly one orientation block.
    single = replace(MODEL_CONFIG, multiscale_enabled=False)
    assert count_forward_passes(single) == ORIENTATION_COUNT


def test_predict_reports_one_unit_per_successful_forward_pass(monkeypatch):
    """on_pass fires once per completed forward pass, and the count is exact."""
    from ai.inference.segmentation import count_forward_passes

    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    config = replace(MODEL_CONFIG, multiscale_enabled=True)
    service = ModelService(config)
    image = Image.new("RGB", (256, 256), color=(80, 100, 120))

    calls = []
    result = predict(
        image, model_service=service, config=config, on_pass=lambda: calls.append(1)
    )

    assert result.binary_mask.shape == (1, 1, config.input_size, config.input_size)
    assert len(calls) == count_forward_passes(config)


def test_predict_without_callback_unchanged(monkeypatch):
    """A legacy call (no on_pass) still works and yields identical output."""
    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    config = replace(MODEL_CONFIG, multiscale_enabled=False)
    service = ModelService(config)
    image = Image.new("RGB", (256, 256), color=(110, 60, 30))

    with_cb = predict(
        image, model_service=service, config=config, on_pass=lambda: None
    )
    without_cb = predict(image, model_service=service, config=config)

    assert torch.equal(with_cb.probability_map, without_cb.probability_map)
    assert torch.equal(with_cb.binary_mask, without_cb.binary_mask)


def test_failed_forward_pass_is_not_reported_as_completed(monkeypatch):
    """A pass that raises must not fire on_pass (no false 'completed' unit)."""
    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    config = replace(MODEL_CONFIG, multiscale_enabled=False)
    service = ModelService(config)
    # Break the model contract so every forward pass raises.
    monkeypatch.setattr(
        service, "predict_logits", lambda tensor: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    image = Image.new("RGB", (256, 256), color=(80, 100, 120))

    calls = []
    with pytest.raises(RuntimeError):
        predict(image, model_service=service, config=config, on_pass=lambda: calls.append(1))

    assert calls == []


def test_pipeline_reports_phases_then_inference_order(monkeypatch):
    """run_pipeline reports the phases in execution order and the passes."""
    import io as _io

    from ai.inference import pipeline as pipeline_mod

    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    config = replace(MODEL_CONFIG, multiscale_enabled=False)
    service = ModelService(config)
    # Route the pipeline's internal predict to our small-config service.
    monkeypatch.setattr(
        pipeline_mod, "predict",
        lambda image, config=None, on_pass=None: predict(
            image, model_service=service, config=config, on_pass=on_pass
        ),
    )

    stream = _io.BytesIO()
    Image.new("RGB", (64, 64), color=(20, 80, 120)).save(stream, format="PNG")

    phases = []
    passes = []
    result = pipeline_mod.run_pipeline(
        stream.getvalue(),
        config=config,
        on_phase=lambda name: phases.append(name),
        on_pass=lambda: passes.append(1),
    )

    assert result.measurements["segmentation_status"] in {"detected", "not_detected"}
    assert phases == [
        pipeline_mod.PHASE_PREPROCESSING,
        pipeline_mod.PHASE_INFERENCE,
        pipeline_mod.PHASE_POSTPROCESSING,
        pipeline_mod.PHASE_GRADCAM,
        pipeline_mod.PHASE_ARTIFACT_COMPOSITION,
    ]
    assert len(passes) == 5  # multiscale off -> 1 scale x 5 orientations


def test_pipeline_callback_does_not_change_artifacts(monkeypatch):
    """Callbacks are observational: identical artifacts with and without them."""
    import io as _io

    from ai.inference import pipeline as pipeline_mod

    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    config = replace(MODEL_CONFIG, multiscale_enabled=False)
    service = ModelService(config)
    monkeypatch.setattr(
        pipeline_mod, "predict",
        lambda image, config=None, on_pass=None: predict(
            image, model_service=service, config=config, on_pass=on_pass
        ),
    )

    stream = _io.BytesIO()
    Image.new("RGB", (64, 64), color=(20, 80, 120)).save(stream, format="PNG")
    payload = stream.getvalue()

    with_cb = pipeline_mod.run_pipeline(
        payload, config=config, on_phase=lambda n: None, on_pass=lambda: None
    )
    without_cb = pipeline_mod.run_pipeline(payload, config=config)

    assert with_cb.binary_mask_png == without_cb.binary_mask_png
    assert with_cb.segmentation_overlay_png == without_cb.segmentation_overlay_png
    assert with_cb.gradcam_heatmap_png == without_cb.gradcam_heatmap_png
    assert with_cb.gradcam_overlay_png == without_cb.gradcam_overlay_png
    assert with_cb.summary_text == without_cb.summary_text
    assert with_cb.measurements == without_cb.measurements
