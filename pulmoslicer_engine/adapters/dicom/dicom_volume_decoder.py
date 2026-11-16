"""IO05: deterministic stored-pixel to Hounsfield Unit conversion."""

from __future__ import annotations

import math
from typing import Iterable


class PixelDecodeError(ValueError):
    """Pixel rescale metadata or stored values are not safe to convert."""


def stored_values_to_hu(
    stored_values: Iterable[int | float], slope: float, intercept: float
) -> tuple[float, ...]:
    slope, intercept = float(slope), float(intercept)
    if not math.isfinite(slope) or slope == 0 or not math.isfinite(intercept):
        raise PixelDecodeError("RescaleSlope/Intercept are invalid")
    output = tuple(float(value) * slope + intercept for value in stored_values)
    if not all(math.isfinite(value) for value in output):
        raise PixelDecodeError("HU conversion produced a non-finite value")
    return output

