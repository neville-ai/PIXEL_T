"""Scenario 1 Ver.22 mask post-processing and deterministic measurements."""

from __future__ import annotations

import cv2
import numpy as np
from scipy.ndimage import binary_fill_holes

from ai.config.model_config import MODEL_CONFIG, ModelConfig


def smooth_contours(mask: np.ndarray, epsilon_ratio: float) -> np.ndarray:
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return mask.astype(np.uint8)
    smoothed = np.zeros_like(mask, dtype=np.uint8)
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue
        polygon = cv2.approxPolyDP(contour, epsilon_ratio * perimeter, True)
        cv2.drawContours(smoothed, [polygon], -1, color=1, thickness=cv2.FILLED)
    return smoothed


def postprocess_mask(mask: np.ndarray, config: ModelConfig = MODEL_CONFIG) -> np.ndarray:
    """Apply the verified close/open, area filter, hole fill, and smoothing order."""
    binary = (np.asarray(mask) > 0).astype(np.uint8)
    kernel = np.ones((3, 3), dtype=np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    cleaned = np.zeros_like(binary)
    for label in range(1, count):
        if stats[label, cv2.CC_STAT_AREA] >= config.postprocessing_min_area:
            cleaned[labels == label] = 1
    if cleaned.any():
        cleaned = binary_fill_holes(cleaned).astype(np.uint8)
    if config.contour_smoothing and cleaned.any():
        cleaned = smooth_contours(cleaned, config.smoothing_epsilon)
    return (cleaned > 0).astype(np.uint8)


def resize_binary_mask(mask: np.ndarray, width: int, height: int) -> np.ndarray:
    resized = cv2.resize(mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST)
    return (resized > 0).astype(np.uint8)


def measure_mask(mask: np.ndarray) -> dict[str, object]:
    final_mask = (np.asarray(mask) > 0).astype(np.uint8)
    height, width = final_mask.shape
    area_pixels = int(np.count_nonzero(final_mask))
    area_ratio = float(area_pixels / (width * height)) if width and height else 0.0
    if area_pixels == 0:
        bounding_box = None
        bounding_width = None
        bounding_height = None
    else:
        ys, xs = np.nonzero(final_mask)
        x_min, x_max = int(xs.min()), int(xs.max())
        y_min, y_max = int(ys.min()), int(ys.max())
        bounding_box = {
            "x_min": x_min,
            "y_min": y_min,
            "x_max": x_max,
            "y_max": y_max,
        }
        bounding_width = x_max - x_min + 1
        bounding_height = y_max - y_min + 1
    return {
        "segmentation_status": "detected" if area_pixels else "not_detected",
        "area_pixels": area_pixels,
        "area_ratio": area_ratio,
        "bounding_box": bounding_box,
        "bounding_width_pixels": bounding_width,
        "bounding_height_pixels": bounding_height,
    }
