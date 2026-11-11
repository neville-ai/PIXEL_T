"""Inference preprocessing matching the verified notebook validation transform."""

from __future__ import annotations

import numpy as np
import torch
from PIL import Image

from ai.config.model_config import MODEL_CONFIG, ModelConfig, ModelConfigurationError

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def prepare_image(image: Image.Image, config: ModelConfig = MODEL_CONFIG) -> torch.Tensor:
    """Convert an image to a normalized ``[1, 3, 512, 512]`` tensor."""
    if not isinstance(image, Image.Image):
        raise ModelConfigurationError("Inference input must be a decoded PIL image.")
    rgb_image = image.convert("RGB")
    resized = rgb_image.resize(
        (config.input_size, config.input_size), Image.Resampling.BILINEAR
    )
    pixels = np.asarray(resized, dtype=np.float32) / 255.0
    pixels = (pixels - np.asarray(IMAGENET_MEAN, dtype=np.float32)) / np.asarray(
        IMAGENET_STD, dtype=np.float32
    )
    tensor = torch.from_numpy(pixels.transpose(2, 0, 1).copy()).unsqueeze(0)
    return tensor
