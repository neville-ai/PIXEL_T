"""Raw segmentation probability, TTA, thresholding, and basic mask output."""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F
from PIL import Image

from ai.config.model_config import MODEL_CONFIG, ModelConfig
from ai.inference.model_service import ModelService
from ai.inference.preprocessing import prepare_image

_DEFAULT_MODEL_SERVICE = ModelService(MODEL_CONFIG)


@dataclass(frozen=True)
class SegmentationResult:
    probability_map: torch.Tensor
    binary_mask: torch.Tensor
    threshold: float


def _restore_orientation(probabilities: torch.Tensor, orientation: str) -> torch.Tensor:
    if orientation == "horizontal":
        return torch.flip(probabilities, dims=[3])
    if orientation == "vertical":
        return torch.flip(probabilities, dims=[2])
    if orientation == "rotate90":
        return torch.rot90(probabilities, k=-1, dims=[2, 3])
    if orientation == "rotate270":
        return torch.rot90(probabilities, k=-3, dims=[2, 3])
    return probabilities


def _predict_scale(
    model_service: ModelService,
    tensor: torch.Tensor,
    config: ModelConfig,
    target_size: tuple[int, int],
) -> list[torch.Tensor]:
    predictions: list[torch.Tensor] = []
    orientations = (
        ("original", tensor),
        ("horizontal", torch.flip(tensor, dims=[3])),
        ("vertical", torch.flip(tensor, dims=[2])),
        ("rotate90", torch.rot90(tensor, k=1, dims=[2, 3])),
        ("rotate270", torch.rot90(tensor, k=3, dims=[2, 3])),
    )
    for orientation, transformed in orientations:
        logits = model_service.predict_logits(transformed)
        probabilities = torch.sigmoid(logits)
        probabilities = _restore_orientation(probabilities, orientation)
        if probabilities.shape[-2:] != target_size:
            probabilities = F.interpolate(
                probabilities, size=target_size, mode="bilinear", align_corners=False
            )
        predictions.append(probabilities)
    return predictions


def predict(image: Image.Image, model_service: ModelService | None = None,
            config: ModelConfig = MODEL_CONFIG) -> SegmentationResult:
    """Run verified TTA inference and return a thresholded basic mask.

    Post-processing is intentionally not applied here; complete post-processing
    and measurement persistence belong to the later pipeline task.
    """
    service = model_service or _DEFAULT_MODEL_SERVICE
    tensor = prepare_image(image, config)
    target_size = (config.input_size, config.input_size)
    scales = config.tta_scales if config.multiscale_enabled else (1.0,)
    probability_maps: list[torch.Tensor] = []
    for scale in scales:
        scaled = tensor
        if scale != 1.0:
            size = max(32, round(config.input_size * scale / 32) * 32)
            scaled = F.interpolate(tensor, size=(size, size), mode="bilinear", align_corners=False)
        probability_maps.extend(_predict_scale(service, scaled, config, target_size))
    probability_map = torch.stack(probability_maps).mean(dim=0).cpu()
    binary_mask = (probability_map >= config.threshold).to(torch.uint8)
    return SegmentationResult(
        probability_map=probability_map,
        binary_mask=binary_mask,
        threshold=config.threshold,
    )
