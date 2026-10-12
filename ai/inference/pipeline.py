"""End-to-end AI artifact generation without persistence side effects."""

from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np
from PIL import Image

from ai.config.model_config import MODEL_CONFIG, ModelConfig
from ai.inference.gradcam import GradCAMResult, generate_gradcam
from ai.inference.postprocessing import measure_mask, postprocess_mask, resize_binary_mask
from ai.inference.preprocessing import prepare_image
from ai.inference.segmentation import predict


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
) -> PipelineResult:
    """Run segmentation, final-mask measurements, overlays, and Grad-CAM."""
    with Image.open(io.BytesIO(original_bytes)) as decoded:
        original = decoded.convert("RGB")
    original_width, original_height = original.size
    segmentation = predict(original, config=config)
    processed_512 = postprocess_mask(segmentation.binary_mask[0, 0].numpy(), config)
    final_mask = resize_binary_mask(processed_512, original_width, original_height)
    measurements = measure_mask(final_mask)
    measurements["area_percentage"] = float(measurements["area_ratio"]) * 100.0

    gradcam = generate_gradcam(
        prepare_image(original, config),
        original_image=original,
        config=config,
    )
    overlay = _segmentation_overlay(original, final_mask)
    mask_image = Image.fromarray((final_mask * 255).astype(np.uint8), mode="L")
    heatmap_image = _heatmap_image(gradcam.heatmap)
    summary = (
        "Model menghasilkan area segmentasi pada citra dengan cakupan "
        f"sekitar {measurements['area_percentage']:.2f}% dari area citra."
        if measurements["segmentation_status"] == "detected"
        else "Model tidak menghasilkan area segmentasi foreground pada citra."
    )
    return PipelineResult(
        binary_mask_png=_png_bytes(mask_image),
        segmentation_overlay_png=_png_bytes(overlay),
        gradcam_heatmap_png=_png_bytes(heatmap_image),
        gradcam_overlay_png=_png_bytes(Image.fromarray(gradcam.overlay, mode="RGB")),
        measurements=measurements,
        summary_text=summary,
        gradcam=gradcam,
    )
