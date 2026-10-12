from dataclasses import replace
from pathlib import Path

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
