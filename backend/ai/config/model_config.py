"""Verified Scenario 1 U-Net + ResNet50 inference configuration."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

CHECKPOINT_FILENAME = "PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth"
CHECKPOINT_SHA256 = "46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581"


class ModelConfigurationError(ValueError):
    """Raised when the verified model configuration cannot be used safely."""


@dataclass(frozen=True)
class ModelConfig:
    architecture: str = "UNet"
    encoder: str = "resnet50"
    decoder_attention: str = "scse"
    gradcam_target_layer: str = "decoder.blocks.4.conv2.0"
    framework: str = "pytorch"
    library: str = "segmentation_models_pytorch"
    model_version: str = "Scenario 1 Ver.22"
    input_size: int = 512
    input_channels: int = 3
    threshold: float = 0.55
    tta_enabled: bool = True
    multiscale_enabled: bool = True
    tta_scales: tuple[float, ...] = (0.85, 0.95, 1.0, 1.05, 1.15)
    postprocessing_enabled: bool = True
    postprocessing_min_area: int = 25
    contour_smoothing: bool = True
    smoothing_epsilon: float = 0.005
    checkpoint_filename: str = CHECKPOINT_FILENAME
    checkpoint_sha256: str = CHECKPOINT_SHA256

    @property
    def checkpoint_path(self) -> Path:
        configured = os.getenv("MODEL_CHECKPOINT_PATH", "").strip()
        if configured:
            raw_path = Path(configured)
            if ".." in raw_path.parts:
                raise ModelConfigurationError("MODEL_CHECKPOINT_PATH contains an invalid path.")
            return raw_path.expanduser().resolve()
        return (Path(__file__).resolve().parents[1] / "models" / self.checkpoint_filename).resolve()

    def validate(self) -> None:
        if self.input_size <= 0 or self.input_channels != 3:
            raise ModelConfigurationError("Verified input configuration is invalid.")
        if not 0.0 < self.threshold < 1.0:
            raise ModelConfigurationError("MODEL_THRESHOLD must be between 0 and 1.")
        if not self.tta_scales or any(scale <= 0 for scale in self.tta_scales):
            raise ModelConfigurationError("Verified TTA scales are invalid.")
        if self.postprocessing_min_area < 0 or self.smoothing_epsilon < 0:
            raise ModelConfigurationError("Verified post-processing configuration is invalid.")

    def checkpoint_sha256_matches(self, path: Path | None = None) -> bool:
        checkpoint = path or self.checkpoint_path
        digest = hashlib.sha256()
        with checkpoint.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest().upper() == self.checkpoint_sha256.upper()


MODEL_CONFIG = ModelConfig()
MODEL_CONFIG.validate()
