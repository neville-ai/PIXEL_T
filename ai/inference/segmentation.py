"""Raw segmentation probability, TTA, thresholding, and basic mask output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import torch
import torch.nn.functional as F
from PIL import Image

from ai.config.model_config import MODEL_CONFIG, ModelConfig
from ai.inference.model_service import ModelService
from ai.inference.preprocessing import prepare_image

_DEFAULT_MODEL_SERVICE = ModelService(MODEL_CONFIG)

# Number of fixed TTA orientations the active loop actually executes.
# NOTE: the runtime loop in ``_predict_scale`` always runs these five; the
# ``tta_enabled`` config flag is NOT read by the active code path.
ORIENTATION_COUNT = 5


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


def count_forward_passes(config: ModelConfig = MODEL_CONFIG) -> int:
    """Return the number of forward passes the active TTA loop will run.

    Derived from the code that actually executes: the outer loop runs over
    ``config.tta_scales`` when ``multiscale_enabled`` is true (else a single
    1.0 scale), and the inner loop always runs ``ORIENTATION_COUNT`` forward
    passes. The ``tta_enabled`` flag is intentionally not consulted because the
    active loop does not read it.
    """
    scales = config.tta_scales if config.multiscale_enabled else (1.0,)
    return len(scales) * ORIENTATION_COUNT


def _predict_scale(
    model_service: ModelService,
    tensor: torch.Tensor,
    config: ModelConfig,
    target_size: tuple[int, int],
    on_pass: Optional[Callable[[], None]] = None,
    scale: float = 1.0,
) -> list[torch.Tensor]:
    import time
    predictions: list[torch.Tensor] = []
    forward_pass_times: list[float] = []
    orientations = (
        ("original", tensor),
        ("horizontal", torch.flip(tensor, dims=[3])),
        ("vertical", torch.flip(tensor, dims=[2])),
        ("rotate90", torch.rot90(tensor, k=1, dims=[2, 3])),
        ("rotate270", torch.rot90(tensor, k=3, dims=[2, 3])),
    )
    for orientation, transformed in orientations:
        pass_start = time.perf_counter()
        logits = model_service.predict_logits(transformed)
        pass_dur = time.perf_counter() - pass_start
        forward_pass_times.append(pass_dur)
        probabilities = torch.sigmoid(logits)
        probabilities = _restore_orientation(probabilities, orientation)
        if probabilities.shape[-2:] != target_size:
            probabilities = F.interpolate(
                probabilities, size=target_size, mode="bilinear", align_corners=False
            )
        predictions.append(probabilities)
        # Report a completed pass only after this forward pass succeeded. Any
        # exception from predict_logits above propagates and never reaches here,
        # so a failed pass is never counted as completed.
        if on_pass is not None:
            on_pass()
    # Log forward pass timing summary for this scale
    total = sum(forward_pass_times)
    avg = total / len(forward_pass_times) if forward_pass_times else 0.0
    print(f"[TIMING] stage=forward_pass scale={scale} duration_ms={total * 1000:.1f} avg_ms={avg * 1000:.1f} passes={len(forward_pass_times)} device={model_service.device}")
    return predictions


def predict(image: Image.Image, model_service: ModelService | None = None,
            config: ModelConfig = MODEL_CONFIG,
            on_pass: Optional[Callable[[], None]] = None) -> SegmentationResult:
    """Run verified TTA inference and return a thresholded basic mask.

    Post-processing is intentionally not applied here; complete post-processing
    and measurement persistence belong to the later pipeline task.

    ``on_pass`` is an optional progress callback invoked once after each
    successful forward pass. It is purely observational: it receives no tensor
    and cannot alter predictions, masks, or results.
    """
    import time
    predict_start = time.perf_counter()
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
        probability_maps.extend(
            _predict_scale(service, scaled, config, target_size, on_pass=on_pass, scale=scale)
        )
    probability_map = torch.stack(probability_maps).mean(dim=0).cpu()
    binary_mask = (probability_map >= config.threshold).to(torch.uint8)
    predict_dur = time.perf_counter() - predict_start
    print(f"[TIMING] stage=predict_total duration_ms={predict_dur * 1000:.1f} scales={len(scales)} device={service.device}")
    return SegmentationResult(
        probability_map=probability_map,
        binary_mask=binary_mask,
        threshold=config.threshold,
    )
