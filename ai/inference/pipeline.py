"""End-to-end AI artifact generation without persistence side effects."""

from __future__ import annotations

import io
import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
from PIL import Image

from ai.config.model_config import MODEL_CONFIG, ModelConfig
from ai.inference.domain_validator import ColonoscopyDomainValidator, DomainDecision
from ai.inference.gradcam import GradCAMResult, generate_gradcam
from ai.inference.postprocessing import measure_mask, postprocess_mask, resize_binary_mask
from ai.inference.preprocessing import prepare_image
from ai.inference.segmentation import predict, _DEFAULT_MODEL_SERVICE

# Pipeline phases reported, in execution order. Each completed phase counts as
# one work unit alongside the individual inference forward passes.
PHASE_PREPROCESSING = "preprocessing"
PHASE_INFERENCE = "inference"
PHASE_POSTPROCESSING = "postprocessing"
PHASE_GRADCAM = "gradcam"
PHASE_ARTIFACT_COMPOSITION = "artifact_composition"

# Convenience reporter: forward a fixed phase name as a completed unit.
PhaseCallback = Callable[[str], None]

# Timing instrumentation logger
_timing_logger = logging.getLogger("pixelt.timing")


class _Timer:
    """Context manager for timing code blocks."""
    def __init__(self, analysis_id: str, stage: str, logger: logging.Logger, extra: dict | None = None):
        self.analysis_id = analysis_id
        self.stage = stage
        self.logger = logger
        self.extra = extra or {}
        self.start = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc):
        dur = time.perf_counter() - self.start
        self.logger.info(
            "TIMING analysis_id=%s stage=%s duration_ms=%.1f %s",
            self.analysis_id, self.stage, dur * 1000,
            " ".join(f"{k}={v}" for k, v in self.extra.items()) if self.extra else ""
        )


def _phase(name: str, on_phase: Optional[PhaseCallback]) -> None:
    if on_phase is not None:
        on_phase(name)


@dataclass(frozen=True)
class PipelineResult:
    binary_mask_png: bytes
    segmentation_overlay_png: bytes
    gradcam_heatmap_png: bytes
    gradcam_overlay_png: bytes
    measurements: dict[str, object]
    summary_text: str
    gradcam: GradCAMResult


def _png_bytes(image: Image.Image) -> bytes:
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def _segmentation_overlay(original: Image.Image, mask: np.ndarray) -> Image.Image:
    rgb = np.asarray(original.convert("RGB"), dtype=np.uint8)
    overlay = rgb.astype(np.float32)
    region = mask.astype(bool)
    color = np.zeros_like(overlay)
    color[..., 1] = 190.0
    color[..., 2] = 120.0
    overlay[region] = overlay[region] * 0.55 + color[region] * 0.45
    return Image.fromarray(overlay.clip(0, 255).astype(np.uint8), mode="RGB")


def _heatmap_image(heatmap: np.ndarray) -> Image.Image:
    values = (np.clip(heatmap, 0.0, 1.0) * 255.0).round().astype(np.uint8)
    grayscale = Image.fromarray(values, mode="L")
    array = np.asarray(grayscale, dtype=np.float32) / 255.0
    red = np.clip(1.5 - np.abs(4.0 * array - 3.0), 0.0, 1.0)
    green = np.clip(1.5 - np.abs(4.0 * array - 2.0), 0.0, 1.0)
    blue = np.clip(1.5 - np.abs(4.0 * array - 1.0), 0.0, 1.0)
    rgb = (np.stack((red, green, blue), axis=-1) * 255.0).round().astype(np.uint8)
    return Image.fromarray(rgb, mode="RGB")


def run_pipeline(
    original_bytes: bytes,
    config: ModelConfig = MODEL_CONFIG,
    on_phase: Optional[PhaseCallback] = None,
    on_pass: Optional[Callable[[], None]] = None,
    *,
    analysis_id: str = "",
    validate_domain: bool = True,
) -> PipelineResult:
    """Run segmentation, final-mask measurements, overlays, and Grad-CAM.

    Medical domain validation is enforced on every call: the input must be
    classified ``ACCEPT`` by :class:`ColonoscopyDomainValidator` before any
    preprocessing, U-Net/TTA inference, or Grad-CAM work begins. ``REJECT`` and
    ``UNCERTAIN`` raise immediately, so this boundary cannot be bypassed even by
    a direct caller (the ``validate_domain`` parameter is retained for signature
    compatibility but no longer disables the gate).

    ``on_phase`` and ``on_pass`` are optional, purely observational progress
    callbacks. ``on_phase`` fires once after each named phase completes;
    ``on_pass`` fires once per successful inference forward pass (forwarded to
    ``predict``). Neither callback receives tensors nor can alter results, and
    neither fires for work that did not complete: on the first exception the
    pipeline propagates without reporting further progress. Callbacks must not
    raise — progress-write (database) failures are caught and recorded by the
    callback owner (the analysis service reporter), so reporting can never turn
    a successful inference into a failure.
    """
    pipeline_start = time.perf_counter()
    with _Timer(analysis_id, "pipeline_total", _timing_logger):
        with Image.open(io.BytesIO(original_bytes)) as decoded:
            original = decoded.convert("RGB")
        val_result = ColonoscopyDomainValidator().validate_image(original)
        if val_result.decision != DomainDecision.ACCEPT:
            raise ValueError(
                f"Domain validation failed ({val_result.decision.value}): {val_result.message}"
            )
        with _Timer(analysis_id, "preprocessing", _timing_logger):
            _phase(PHASE_PREPROCESSING, on_phase)
        original_width, original_height = original.size
        with _Timer(analysis_id, "segmentation_inference", _timing_logger):
            segmentation = predict(original, config=config, on_pass=on_pass)
        _phase(PHASE_INFERENCE, on_phase)
        with _Timer(analysis_id, "postprocessing", _timing_logger):
            processed_512 = postprocess_mask(segmentation.binary_mask[0, 0].numpy(), config)
            final_mask = resize_binary_mask(processed_512, original_width, original_height)
            prob_map = segmentation.probability_map[0, 0].numpy() if segmentation.probability_map is not None else None
            measurements = measure_mask(final_mask, probability_map=prob_map)
            measurements["area_percentage"] = float(measurements["area_ratio"]) * 100.0
        _phase(PHASE_POSTPROCESSING, on_phase)
        with _Timer(analysis_id, "gradcam", _timing_logger):
            gradcam = generate_gradcam(
                prepare_image(original, config),
                original_image=original,
                config=config,
                model_service=_DEFAULT_MODEL_SERVICE,
            )
        _phase(PHASE_GRADCAM, on_phase)
        with _Timer(analysis_id, "artifact_composition", _timing_logger):
            overlay = _segmentation_overlay(original, final_mask)
            mask_image = Image.fromarray((final_mask * 255).astype(np.uint8), mode="L")
            heatmap_image = _heatmap_image(gradcam.heatmap)
            summary = str(measurements.get("summary_text") or (
                "Model menghasilkan area segmentasi pada citra dengan cakupan "
                f"sekitar {measurements['area_percentage']:.2f}% dari area citra."
                if measurements["segmentation_status"] == "detected"
                else "Model tidak menghasilkan area segmentasi foreground pada citra."
            ))
            result = PipelineResult(
                binary_mask_png=_png_bytes(mask_image),
                segmentation_overlay_png=_png_bytes(overlay),
                gradcam_heatmap_png=_png_bytes(heatmap_image),
                gradcam_overlay_png=_png_bytes(Image.fromarray(gradcam.overlay, mode="RGB")),
                measurements=measurements,
                summary_text=summary,
                gradcam=gradcam,
            )
        _phase(PHASE_ARTIFACT_COMPOSITION, on_phase)
    return result
