"""Unit tests for Post-Segmentation Validation in PIXEL-T.

Tests the second stage of the two-stage validation system:
1. NO_POLYP_DETECTED: when mask area is 0 (valid colonoscopy, but no polyp detected).
   Must explicitly state that it is not a normal diagnosis.
2. POLYP_DETECTED: when mask area is substantial and probability meets solid confidence.
3. LOW_CONFIDENCE: when mask area is tiny (<100 px) or probabilities hover barely over threshold (<0.70 max or <0.62 mean).
"""

import numpy as np
import pytest

from ai.inference.postprocessing import measure_mask


def test_no_polyp_detected_category_for_empty_mask():
    """Empty mask produces NO_POLYP_DETECTED with explicit disclaimer."""
    mask = np.zeros((512, 512), dtype=np.uint8)
    prob_map = np.full((512, 512), 0.12, dtype=np.float32)

    result = measure_mask(mask, probability_map=prob_map)

    assert result["segmentation_status"] == "not_detected"
    assert result["detection_category"] == "NO_POLYP_DETECTED"
    assert result["area_pixels"] == 0
    assert result["mean_probability"] == 0.0
    # Must explicitly state it is not a normal diagnosis
    assert "bukan merupakan diagnosis medis normal" in result["summary_text"].lower()


def test_polyp_detected_category_for_solid_mask():
    """Solid polyp mask with high probability produces POLYP_DETECTED."""
    mask = np.zeros((512, 512), dtype=np.uint8)
    mask[200:300, 200:300] = 1  # 10,000 pixels
    prob_map = np.full((512, 512), 0.05, dtype=np.float32)
    prob_map[200:300, 200:300] = 0.88

    result = measure_mask(mask, probability_map=prob_map)

    assert result["segmentation_status"] == "detected"
    assert result["detection_category"] == "POLYP_DETECTED"
    assert result["area_pixels"] == 10000
    assert result["max_probability"] == 0.88
    assert result["mean_probability"] == 0.88
    assert "mendeteksi adanya area polip" in result["summary_text"].lower()


def test_low_confidence_category_for_weak_probabilities():
    """Mask with probabilities barely over threshold (<0.70 max, <0.62 mean) triggers LOW_CONFIDENCE."""
    mask = np.zeros((512, 512), dtype=np.uint8)
    mask[200:250, 200:250] = 1  # 2,500 pixels
    prob_map = np.full((512, 512), 0.05, dtype=np.float32)
    prob_map[200:250, 200:250] = 0.58  # hovering barely over 0.55 threshold

    result = measure_mask(mask, probability_map=prob_map)

    assert result["segmentation_status"] == "detected"
    assert result["detection_category"] == "LOW_CONFIDENCE"
    assert result["max_probability"] == 0.58
    assert result["mean_probability"] == 0.58
    assert "tingkat keyakinan rendah" in result["summary_text"].lower()
    assert "kurang meyakinkan" in result["summary_text"].lower()


def test_low_confidence_category_for_tiny_speckle():
    """Mask with tiny area (<100 pixels) triggers LOW_CONFIDENCE despite high probability."""
    mask = np.zeros((512, 512), dtype=np.uint8)
    mask[250:255, 250:255] = 1  # 25 pixels (tiny speckle artifact)
    prob_map = np.full((512, 512), 0.05, dtype=np.float32)
    prob_map[250:255, 250:255] = 0.85

    result = measure_mask(mask, probability_map=prob_map)

    assert result["segmentation_status"] == "detected"
    assert result["detection_category"] == "LOW_CONFIDENCE"
    assert result["area_pixels"] == 25


def test_measure_mask_backward_compatibility_without_prob_map():
    """measure_mask still works safely when called without probability_map."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[10:60, 10:60] = 1  # 2500 pixels

    result = measure_mask(mask)

    assert result["segmentation_status"] == "detected"
    assert result["detection_category"] == "POLYP_DETECTED"
    assert result["area_pixels"] == 2500

