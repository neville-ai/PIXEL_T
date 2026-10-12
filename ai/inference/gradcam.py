"""Custom segmentation Grad-CAM for the verified U-Net checkpoint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from ai.config.model_config import MODEL_CONFIG, ModelConfig
from ai.inference.model_service import ModelLoadError, ModelService


class GradCAMError(RuntimeError):
    """Base error for controlled Grad-CAM failures."""


class GradCAMTargetLayerError(GradCAMError):
    pass


class GradCAMObjectiveError(GradCAMError):
    pass


class GradCAMGradientError(GradCAMError):
    pass


class GradCAMGenerationError(GradCAMError):
    pass


@dataclass(frozen=True)
class GradCAMResult:
    heatmap: np.ndarray
    overlay: np.ndarray
    target_layer: str
    target_objective: str
    target_mask_empty: bool


def _normalize_heatmap(heatmap: torch.Tensor) -> np.ndarray:
    values = heatmap.detach().float().cpu().numpy()
    values = np.maximum(values, 0.0)
    if not np.isfinite(values).all():
        raise GradCAMGenerationError("GRADCAM_GENERATION_ERROR")
    minimum = float(values.min())
    maximum = float(values.max())
    if maximum > minimum:
        values = (values - minimum) / (maximum - minimum)
    else:
        values = np.zeros_like(values, dtype=np.float32)
    return np.clip(values, 0.0, 1.0).astype(np.float32)


def _jet_colormap(normalized: np.ndarray) -> np.ndarray:
    """Create a deterministic heatmap without introducing another dependency."""
    red = np.clip(1.5 - np.abs(4.0 * normalized - 3.0), 0.0, 1.0)
    green = np.clip(1.5 - np.abs(4.0 * normalized - 2.0), 0.0, 1.0)
    blue = np.clip(1.5 - np.abs(4.0 * normalized - 1.0), 0.0, 1.0)
    return (np.stack((red, green, blue), axis=-1) * 255.0).round().astype(np.uint8)


def _to_rgb_array(image: Image.Image, size: tuple[int, int]) -> np.ndarray:
    rgb = image.convert("RGB").resize(size, Image.Resampling.BILINEAR)
    return np.asarray(rgb, dtype=np.uint8)


def _resize_heatmap(heatmap: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    resized = Image.fromarray((heatmap * 255.0).round().astype(np.uint8), mode="L")
    return np.asarray(resized.resize(size, Image.Resampling.BILINEAR), dtype=np.float32) / 255.0


def _prepare_target_mask(
    logits: torch.Tensor,
    target_mask: torch.Tensor | np.ndarray | None,
    threshold: float,
) -> torch.Tensor:
    if target_mask is None:
        mask = torch.sigmoid(logits) >= threshold
    else:
        mask = torch.as_tensor(target_mask, device=logits.device)
        if mask.ndim == 2:
            mask = mask.unsqueeze(0).unsqueeze(0)
        elif mask.ndim == 3:
            mask = mask.unsqueeze(1)
        if mask.ndim != 4 or mask.shape[0] != logits.shape[0] or mask.shape[1] != 1:
            raise GradCAMObjectiveError("GRADCAM_OBJECTIVE_ERROR")
        if mask.shape[-2:] != logits.shape[-2:]:
            mask = F.interpolate(mask.float(), size=logits.shape[-2:], mode="nearest")
        mask = mask > 0
    return mask.to(device=logits.device, dtype=torch.bool)


def generate_gradcam(
    image_tensor: torch.Tensor,
    model_service: ModelService | None = None,
    target_mask: torch.Tensor | np.ndarray | None = None,
    original_image: Image.Image | None = None,
    config: ModelConfig = MODEL_CONFIG,
    overlay_alpha: float = 0.45,
) -> GradCAMResult:
    """Generate segmentation Grad-CAM on the canonical, non-TTA branch.

    Objective: mean selected segmentation logit over ``target_mask``.
    When the predicted/ supplied mask is empty, the objective is a zero scalar
    connected to the graph, producing a deterministic all-zero heatmap.
    """
    service = model_service or ModelService(config)
    try:
        target_layer = service.get_gradcam_target_layer()
    except ModelLoadError as error:
        raise GradCAMTargetLayerError("GRADCAM_TARGET_LAYER_ERROR") from error
    if image_tensor.ndim != 4:
        raise GradCAMObjectiveError("GRADCAM_OBJECTIVE_ERROR")

    model = service.load()
    activations: dict[str, torch.Tensor] = {}
    gradients: dict[str, torch.Tensor] = {}

    def capture_activation(_module: torch.nn.Module, _inputs: tuple[Any, ...], output: torch.Tensor) -> None:
        activations["value"] = output
        if output.requires_grad:
            output.register_hook(lambda gradient: gradients.__setitem__("value", gradient))

    handle = target_layer.register_forward_hook(capture_activation)
    try:
        model.zero_grad(set_to_none=True)
        with torch.enable_grad():
            logits = model(image_tensor.to(service.device))
            if logits.ndim != 4 or logits.shape[1] != 1:
                raise GradCAMObjectiveError("GRADCAM_OBJECTIVE_ERROR")
            mask = _prepare_target_mask(logits, target_mask, config.threshold)
            selected = logits.masked_select(mask)
            target_mask_empty = selected.numel() == 0
            objective = logits.sum() * 0.0 if target_mask_empty else selected.mean()
            if objective.numel() != 1:
                raise GradCAMObjectiveError("GRADCAM_OBJECTIVE_ERROR")
            objective.backward()
    except GradCAMError:
        raise
    except RuntimeError as error:
        raise GradCAMGradientError("GRADCAM_GRADIENT_ERROR") from error
    finally:
        handle.remove()
        model.zero_grad(set_to_none=True)

    activation = activations.get("value")
    gradient = gradients.get("value")
    if activation is None or gradient is None:
        raise GradCAMGradientError("GRADCAM_GRADIENT_ERROR")
    if activation.ndim != 4 or gradient.shape != activation.shape:
        raise GradCAMGradientError("GRADCAM_GRADIENT_ERROR")

    weights = gradient.mean(dim=(2, 3), keepdim=True)
    cam = torch.relu((weights * activation).sum(dim=1, keepdim=False))
    normalized = _normalize_heatmap(cam[0])
    if original_image is None:
        original_rgb = np.zeros((*normalized.shape, 3), dtype=np.uint8)
    else:
        original_size = original_image.convert("RGB").size
        normalized = _resize_heatmap(normalized, original_size)
        original_rgb = _to_rgb_array(original_image, original_size)
    heatmap_rgb = _jet_colormap(normalized)
    overlay = (
        original_rgb.astype(np.float32) * (1.0 - overlay_alpha)
        + heatmap_rgb.astype(np.float32) * overlay_alpha
    ).clip(0, 255).astype(np.uint8)
    return GradCAMResult(
        heatmap=normalized,
        overlay=overlay,
        target_layer=config.gradcam_target_layer,
        target_objective="mean selected segmentation logit over target mask",
        target_mask_empty=target_mask_empty,
    )
