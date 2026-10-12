"""Lazy, strict loader for the verified Scenario 1 segmentation model."""

from __future__ import annotations

import os
from threading import Lock
from typing import Any

import torch
import segmentation_models_pytorch as smp

from ai.config.model_config import MODEL_CONFIG, ModelConfig, ModelConfigurationError


class ModelLoadError(RuntimeError):
    """Raised when the verified checkpoint cannot be loaded safely."""


class ModelService:
    """Load the exact SMP model once and reuse it for inference requests."""

    def __init__(self, config: ModelConfig = MODEL_CONFIG):
        self.config = config
        self._model: torch.nn.Module | None = None
        self._device: torch.device | None = None
        self._lock = Lock()

    @property
    def device(self) -> torch.device:
        if self._device is None:
            self._device = self._select_device()
        return self._device

    @staticmethod
    def _select_device() -> torch.device:
        requested = os.getenv("MODEL_DEVICE", "auto").strip().lower()
        if requested == "cpu":
            return torch.device("cpu")
        if requested in {"cuda", "gpu"} and torch.cuda.is_available():
            return torch.device("cuda")
        if requested in {"cuda", "gpu"} and not torch.cuda.is_available():
            return torch.device("cpu")
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _build_model(self) -> torch.nn.Module:
        return smp.Unet(
            encoder_name=self.config.encoder,
            encoder_weights=None,
            in_channels=self.config.input_channels,
            classes=1,
            activation=None,
            decoder_attention_type=self.config.decoder_attention,
        )

    def load(self) -> torch.nn.Module:
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            try:
                checkpoint_path = self.config.checkpoint_path
                if not checkpoint_path.is_file():
                    raise ModelLoadError("Verified model checkpoint was not found.")
                if not self.config.checkpoint_sha256_matches(checkpoint_path):
                    raise ModelLoadError("MODEL_CHECKPOINT_MISMATCH")
                state_dict: Any = torch.load(
                    checkpoint_path, map_location="cpu", weights_only=True
                )
                if not isinstance(state_dict, dict):
                    raise ModelLoadError("Checkpoint does not contain a state dictionary.")
                model = self._build_model()
                model.load_state_dict(state_dict, strict=True)
                model.to(self.device)
                model.eval()
                self._model = model
                return model
            except ModelLoadError:
                raise
            except (OSError, RuntimeError, ValueError, KeyError) as error:
                raise ModelLoadError("MODEL_LOAD_ERROR") from error

    def metadata(self) -> dict[str, Any]:
        self.load()
        return {
            "architecture": self.config.architecture,
            "encoder": self.config.encoder,
            "gradcam_target_layer": self.config.gradcam_target_layer,
            "model_version": self.config.model_version,
            "checkpoint_filename": self.config.checkpoint_filename,
            "checkpoint_sha256": self.config.checkpoint_sha256,
            "input_size": self.config.input_size,
            "threshold": self.config.threshold,
            "tta_enabled": self.config.tta_enabled,
            "multiscale_enabled": self.config.multiscale_enabled,
            "tta_scales": list(self.config.tta_scales),
            "device": str(self.device),
        }

    def predict_logits(self, tensor: torch.Tensor) -> torch.Tensor:
        model = self.load()
        if (
            tensor.ndim != 4
            or tensor.shape[1] != self.config.input_channels
            or tensor.shape[2] < 32
            or tensor.shape[3] < 32
            or tensor.shape[2] % 32 != 0
            or tensor.shape[3] % 32 != 0
        ):
            raise ModelConfigurationError("Input tensor shape does not match the model contract.")
        with torch.inference_mode():
            output = model(tensor.to(self.device))
        if output.ndim != 4 or output.shape[1] != 1:
            raise ModelLoadError("Model output does not contain one segmentation channel.")
        return output

    def get_gradcam_target_layer(self) -> torch.nn.Module:
        """Resolve the verified target layer; never accept a request value."""
        model = self.load()
        modules = dict(model.named_modules())
        target = modules.get(self.config.gradcam_target_layer)
        if not isinstance(target, torch.nn.Conv2d):
            raise ModelLoadError("GRADCAM_TARGET_LAYER_ERROR")
        return target
