"""Algorithmic domain validation for colonoscopy images in PIXEL-T.

Ensures only endoscopic colonoscopy images (both normal mucosa and polyp lesions)
proceed to the U-Net + ResNet50 segmentation pipeline. Non-colonoscopy inputs
(e.g., human faces, food, animals, landscapes, vehicles, documents, text screenshots,
and non-endoscopic medical images) are rejected or flagged as uncertain prior to
model inference.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image


class DomainDecision(str, Enum):
    """Three-state validation outcome for incoming images."""
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True)
class DomainValidationResult:
    """Detailed result of domain validation."""
    decision: DomainDecision
    confidence: float
    reasons: List[str]
    metrics: Dict[str, float]
    message: str


class ColonoscopyDomainValidator:
    """Multi-feature domain validator for colonoscopy endoscopic images.

    Candidate 2 Configuration (verified on calibration set calib):
    - Canonical scale 256 for Hough line detection (decouples resolution correlation).
    - Threshold G5 warm = 12.0 (extreme cutoff with smooth confidence penalty).
    - Grayscale / achromatic check (G4) routes to UNCERTAIN with educational guidance.
    - Neutral clinical messaging without non-medical object claims.
    Reference: docs/audit/01_tindak_lanjut_fase_b.md

    Evaluates:
    1. Active tissue region (endoscopic circular aperture / vignetting detection).
    2. Mucosal chromaticity concordance in CIE L*a*b* and HSV color spaces.
    3. Cool-hue penalty (detecting blue/cyan/green).
    4. Achromaticity / grayscale check (detecting monochrome images).
    5. High-frequency rectilinear edge density on canonical scale 256.
    6. Luminance & saturation distribution (detecting underexposure or extreme washout).
    """

    def __init__(
        self,
        min_width: int = 150,
        min_height: int = 150,
        max_aspect_ratio: float = 2.8,
        mucosal_accept_threshold: float = 0.55,
        mucosal_reject_threshold: float = 0.32,
        cool_hue_reject_threshold: float = 0.30,
        straight_edge_reject_threshold: float = 1.0,
        straight_edge_warm_threshold: float = 12.0,
        min_chroma_threshold: float = 10.0,
        min_saturation_threshold: float = 0.10,
        min_luminance_threshold: float = 0.18,
        norm_scale: int = 256,
    ):
        self.min_width = min_width
        self.min_height = min_height
        self.max_aspect_ratio = max_aspect_ratio
        self.mucosal_accept_threshold = mucosal_accept_threshold
        self.mucosal_reject_threshold = mucosal_reject_threshold
        self.cool_hue_reject_threshold = cool_hue_reject_threshold
        self.straight_edge_reject_threshold = straight_edge_reject_threshold
        self.straight_edge_warm_threshold = straight_edge_warm_threshold
        self.min_chroma_threshold = min_chroma_threshold
        self.min_saturation_threshold = min_saturation_threshold
        self.min_luminance_threshold = min_luminance_threshold
        self.norm_scale = norm_scale

    def validate_bytes(self, image_bytes: bytes) -> DomainValidationResult:
        """Validate raw image bytes."""
        try:
            with Image.open(io.BytesIO(image_bytes)) as pil_img:
                return self.validate_image(pil_img)
        except Exception as exc:
            return DomainValidationResult(
                decision=DomainDecision.REJECT,
                confidence=0.0,
                reasons=[f"File decoding error: {str(exc)}"],
                metrics={},
                message="Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.",
            )

    def validate_image(self, image: Image.Image) -> DomainValidationResult:
        """Validate a decoded PIL Image object."""
        width, height = image.size
        reasons: List[str] = []
        metrics: Dict[str, float] = {
            "width": float(width),
            "height": float(height),
        }

        # 1. Technical dimension and aspect ratio checks
        if width < self.min_width or height < self.min_height:
            return DomainValidationResult(
                decision=DomainDecision.REJECT,
                confidence=0.0,
                reasons=[f"Dimensi citra terlalu kecil ({width}x{height} px, min {self.min_width}x{self.min_height} px)"],
                metrics=metrics,
                message="Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.",
            )

        aspect_ratio = max(width / height, height / width)
        metrics["aspect_ratio"] = float(aspect_ratio)
        if aspect_ratio > self.max_aspect_ratio:
            return DomainValidationResult(
                decision=DomainDecision.REJECT,
                confidence=0.0,
                reasons=[f"Rasio aspek tidak wajar untuk citra medis ({aspect_ratio:.2f}:1)"],
                metrics=metrics,
                message="Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.",
            )

        # Convert to numpy RGB
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)

        # 2. Active tissue detection (exclude dark endoscopic circular border)
        active_mask = gray > 18
        active_pixels = int(np.sum(active_mask))
        total_pixels = width * height
        active_ratio = active_pixels / total_pixels
        metrics["active_ratio"] = float(active_ratio)

        if active_pixels < (total_pixels * 0.12):
            return DomainValidationResult(
                decision=DomainDecision.REJECT,
                confidence=0.0,
                reasons=["Citra hampir seluruhnya gelap atau kosong."],
                metrics=metrics,
                message="Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.",
            )

        h_chan = hsv[:, :, 0]
        s_chan = hsv[:, :, 1]
        v_chan = hsv[:, :, 2]
        a_chan = lab[:, :, 1]
        b_chan = lab[:, :, 2]

        # 3. Saturation and Chroma
        mean_v = float(np.mean(v_chan[active_mask])) / 255.0
        std_v = float(np.std(v_chan[active_mask]))
        mean_s = float(np.mean(s_chan[active_mask])) / 255.0
        a_dev = a_chan[active_mask].astype(np.float32) - 128.0
        b_dev = b_chan[active_mask].astype(np.float32) - 128.0
        mean_chroma = float(np.mean(np.sqrt(a_dev**2 + b_dev**2)))
        metrics["mean_luminance"] = mean_v
        metrics["std_luminance"] = std_v
        metrics["mean_saturation"] = mean_s
        metrics["mean_chroma"] = mean_chroma

        # 4. Mucosal chromaticity concordance
        # HSV: Hue in warm mucosal band: [0..22] or [160..180], with moderate S and V
        warm_hue_mask = ((h_chan <= 22) | (h_chan >= 160)) & (s_chan >= 28) & (v_chan >= 28)
        # Lab: positive a* (red/pink, a >= 134) and positive b* (warm yellow, b >= 130)
        lab_mucosal_mask = (a_chan >= 134) & (b_chan >= 130)
        mucosal_mask = (warm_hue_mask | lab_mucosal_mask) & active_mask
        mucosal_ratio = float(np.sum(mucosal_mask)) / active_pixels
        metrics["mucosal_ratio"] = mucosal_ratio

        # 5. Cool hue penalty (blue/cyan/green)
        cool_mask = ((h_chan >= 36) & (h_chan <= 140)) & (s_chan >= 35) & (v_chan >= 30) & active_mask
        cool_ratio = float(np.sum(cool_mask)) / active_pixels
        metrics["cool_ratio"] = cool_ratio

        # 6. Straight line / rectilinear edge density (Hough transform) on canonical 256 scale
        # Normalized canonical resolution (shortest side = 256) eliminates resolution dependency
        # (Pearson r reduced from +0.2896 to +0.0404, p=0.651). Calibration reference: docs/audit/01_tindak_lanjut_fase_b.md
        min_dim = min(width, height)
        scale = float(self.norm_scale) / float(min_dim)
        w_n = max(1, int(round(width * scale)))
        h_n = max(1, int(round(height * scale)))
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        gray_n = cv2.resize(gray, (w_n, h_n), interpolation=interp)
        edges = cv2.Canny(gray_n, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40, minLineLength=25, maxLineGap=8)
        line_count = len(lines) if lines is not None else 0
        line_density = (line_count * 25.0) / (2.0 * (w_n + h_n))
        metrics["line_density"] = float(line_density)

        # 7. Specular glint (endoscope light reflection on wet mucosa)
        glint_mask = (v_chan >= 240) & (s_chan <= 45) & active_mask
        glint_ratio = float(np.sum(glint_mask)) / active_pixels
        metrics["glint_ratio"] = glint_ratio

        # --- Hard Rejection Gates ---
        if cool_ratio > self.cool_hue_reject_threshold:
            reasons.append(f"Dominasi warna non-endoskopi (cool ratio {cool_ratio*100:.1f}%).")
            return DomainValidationResult(
                decision=DomainDecision.REJECT,
                confidence=0.10,
                reasons=reasons,
                metrics=metrics,
                message="Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.",
            )

        if mean_chroma < self.min_chroma_threshold or mean_s < self.min_saturation_threshold:
            reasons.append(f"Citra monokromatik / akromatik (chroma {mean_chroma:.1f}, saturasi {mean_s:.2f}).")
            return DomainValidationResult(
                decision=DomainDecision.UNCERTAIN,
                confidence=0.40,
                reasons=reasons,
                metrics=metrics,
                message="Citra tampak hitam-putih. Silakan unggah citra kolonoskopi berwarna.",
            )

        # Line rejection: only when mucosal_ratio is low (< self.mucosal_accept_threshold).
        # Real colonoscopy with timestamps, scope metadata, haustral tissue folds, and vascular networks
        # maintains high mucosal_ratio (>= 0.55) and must not be rejected for biological folds.
        if line_density > self.straight_edge_reject_threshold and mucosal_ratio < self.mucosal_accept_threshold:
            reasons.append(f"Kepadatan garis lurus tinggi ({line_density:.3f}) dengan mukosa rendah ({mucosal_ratio*100:.1f}%).")
            return DomainValidationResult(
                decision=DomainDecision.REJECT,
                confidence=0.15,
                reasons=reasons,
                metrics=metrics,
                message="Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.",
            )

        # Extreme line density cutoff on warm mucosal tissue. Ambiguous cases below this threshold stay UNCERTAIN via confidence penalty.
        if line_density > self.straight_edge_warm_threshold and mucosal_ratio > self.mucosal_accept_threshold:
            reasons.append(f"Kepadatan garis lurus sangat tinggi ({line_density:.2f}) pada area bermukosa.")
            return DomainValidationResult(
                decision=DomainDecision.REJECT,
                confidence=0.15,
                reasons=reasons,
                metrics=metrics,
                message="Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.",
            )

        if mucosal_ratio < self.mucosal_reject_threshold:
            reasons.append(f"Kesesuaian kromatisitas mukosa sangat rendah ({mucosal_ratio*100:.1f}%).")
            return DomainValidationResult(
                decision=DomainDecision.REJECT,
                confidence=0.20,
                reasons=reasons,
                metrics=metrics,
                message="Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.",
            )

        # Flat uniform red surface check
        if std_v < 8.5 and glint_ratio < 0.0001:
            reasons.append(f"Pencahayaan seragam datar (std_v={std_v:.1f}) tanpa gradien rongga lumen.")
            return DomainValidationResult(
                decision=DomainDecision.UNCERTAIN,
                confidence=0.45,
                reasons=reasons,
                metrics=metrics,
                message="Sistem tidak dapat memastikan bahwa citra ini adalah kolonoskopi. Silakan unggah citra yang lebih jelas.",
            )

        # --- Lighting / Ambiguity Assessment ---
        if mean_v < self.min_luminance_threshold:
            reasons.append(f"Pencahayaan sangat rendah (luminance {mean_v:.2f}).")
            return DomainValidationResult(
                decision=DomainDecision.UNCERTAIN,
                confidence=0.48,
                reasons=reasons,
                metrics=metrics,
                message="Sistem tidak dapat memastikan bahwa citra ini adalah kolonoskopi. Silakan unggah citra yang lebih jelas.",
            )

        if mucosal_ratio < self.mucosal_accept_threshold:
            reasons.append(f"Kesesuaian mukosa berada pada batas ambang marjinal ({mucosal_ratio*100:.1f}%).")
            return DomainValidationResult(
                decision=DomainDecision.UNCERTAIN,
                confidence=0.52,
                reasons=reasons,
                metrics=metrics,
                message="Sistem tidak dapat memastikan bahwa citra ini adalah kolonoskopi. Silakan unggah citra yang lebih jelas.",
            )

        # Compute composite confidence score (smooth continuous line penalty for Candidate 2)
        cool_penalty = min(0.60, cool_ratio * 2.0)
        line_penalty = min(0.40, max(0.0, line_density - 2.5) * 0.10)
        confidence = float(mucosal_ratio * (1.0 - cool_penalty) * (1.0 - line_penalty))
        confidence = max(0.0, min(1.0, confidence))

        if confidence >= 0.55:
            reasons.append(f"Kromatisitas mukosa terverifikasi ({mucosal_ratio*100:.1f}%), tidak ada anomali non-endoskopi.")
            return DomainValidationResult(
                decision=DomainDecision.ACCEPT,
                confidence=round(confidence, 2),
                reasons=reasons,
                metrics=metrics,
                message="Citra teridentifikasi sebagai citra kolonoskopi yang valid.",
            )

        return DomainValidationResult(
            decision=DomainDecision.UNCERTAIN,
            confidence=round(confidence, 2),
            reasons=["Skor keyakinan domain berada di rentang intermediet."],
            metrics=metrics,
            message="Sistem tidak dapat memastikan bahwa citra ini adalah kolonoskopi. Silakan unggah citra yang lebih jelas.",
        )

