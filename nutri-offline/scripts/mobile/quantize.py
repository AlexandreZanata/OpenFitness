"""int8 vector quantization for mobile index (N-08-06)."""

from __future__ import annotations

import numpy as np


def quantize_int8(vector: list[float], *, global_scale: float | None = None) -> tuple[bytes, float]:
    """Quantize a normalized float vector to int8 bytes + scale."""
    array = np.asarray(vector, dtype=np.float32)
    scale = global_scale
    if scale is None:
        peak = float(np.max(np.abs(array))) or 1.0
        scale = peak / 127.0
    quantized = np.clip(np.round(array / scale), -128, 127).astype(np.int8)
    return quantized.tobytes(), scale


def dequantize_int8(blob: bytes, scale: float, *, dims: int) -> list[float]:
    array = np.frombuffer(blob, dtype=np.int8, count=dims)
    return (array.astype(np.float32) * scale).tolist()
