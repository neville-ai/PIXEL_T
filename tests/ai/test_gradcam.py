from dataclasses import replace

import numpy as np
import pytest
import torch
from PIL import Image

from ai.config.model_config import MODEL_CONFIG
from ai.inference.gradcam import (
    GradCAMTargetLayerError,
    generate_gradcam,
)
from ai.inference.model_service import ModelLoadError, ModelService
from ai.inference.preprocessing import prepare_image


def _service(monkeypatch):
    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    return ModelService(replace(MODEL_CONFIG, tta_enabled=False, multiscale_enabled=False))


def test_target_layer_exists_and_is_convolution(monkeypatch):
    service = _service(monkeypatch)
    layer = service.get_gradcam_target_layer()
    assert isinstance(layer, torch.nn.Conv2d)
    assert layer.out_channels == 16
    assert service.config.gradcam_target_layer == "decoder.blocks.4.conv2.0"


def test_target_layer_failure_does_not_fallback(monkeypatch):
    service = ModelService(
        replace(MODEL_CONFIG, gradcam_target_layer="decoder.blocks.4.not_a_layer")
    )
    monkeypatch.setenv("MODEL_DEVICE", "cpu")
    with pytest.raises(ModelLoadError, match="GRADCAM_TARGET_LAYER_ERROR"):
        service.get_gradcam_target_layer()


def test_real_checkpoint_gradcam_smoke(monkeypatch):
    service = _service(monkeypatch)
    image = Image.new("RGB", (512, 512), color=(80, 100, 120))
    tensor = prepare_image(image)
    result = generate_gradcam(tensor, model_service=service, original_image=image)

    assert result.target_layer == "decoder.blocks.4.conv2.0"
    assert result.target_objective == "mean selected segmentation logit over target mask"
    assert result.heatmap.shape == (512, 512)
    assert result.overlay.shape == (512, 512, 3)
    assert np.isfinite(result.heatmap).all()
    assert result.heatmap.min() >= 0.0
    assert result.heatmap.max() <= 1.0
    assert result.overlay.dtype == np.uint8


def test_empty_target_returns_deterministic_zero_heatmap(monkeypatch):
    service = _service(monkeypatch)
    image = Image.new("RGB", (512, 512), color=(80, 100, 120))
    tensor = prepare_image(image)
    empty_mask = torch.zeros((1, 1, 512, 512), dtype=torch.uint8)
    result = generate_gradcam(
        tensor,
        model_service=service,
        target_mask=empty_mask,
        original_image=image,
    )

    assert result.target_mask_empty is True
    assert np.isfinite(result.heatmap).all()
    assert np.array_equal(result.heatmap, np.zeros((512, 512), dtype=np.float32))
    assert result.overlay.shape == (512, 512, 3)


def test_overlay_aligns_to_non_square_original_image(monkeypatch):
    service = _service(monkeypatch)
    image = Image.new("RGB", (300, 200), color=(80, 100, 120))
    result = generate_gradcam(
        prepare_image(image), model_service=service, original_image=image
    )

    assert result.heatmap.shape == (200, 300)
    assert result.overlay.shape == (200, 300, 3)
