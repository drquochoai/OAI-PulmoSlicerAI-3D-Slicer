"""DM01: immutable image geometry in the DICOM-native LPS-mm frame."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Iterable


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class GeometryError(ValueError):
    """Image geometry is incomplete, inconsistent, or unsafe."""


def _finite_tuple(values: Iterable[float], count: int, name: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if len(result) != count or not all(math.isfinite(value) for value in result):
        raise GeometryError(f"{name} must contain {count} finite values")
    return result


@dataclass(frozen=True)
class CaseGeometry:
    """IJK-to-LPS affine and source lineage; measurements are millimetres."""

    shape_ijk: tuple[int, int, int]
    spacing_mm: tuple[float, float, float]
    ijk_to_lps: tuple[float, ...]
    frame_of_reference_uid: str
    source_volume_sha256: str
    coordinate_system: str = "LPS"
    units: str = "mm"
    contract_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if len(self.shape_ijk) != 3 or any(
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
            for value in self.shape_ijk
        ):
            raise GeometryError("shape_ijk must contain three positive integers")
        spacing = _finite_tuple(self.spacing_mm, 3, "spacing_mm")
        affine = _finite_tuple(self.ijk_to_lps, 16, "ijk_to_lps")
        if any(value <= 0 for value in spacing):
            raise GeometryError("spacing_mm must be positive")
        if self.coordinate_system != "LPS" or self.units != "mm":
            raise GeometryError("exchange geometry must use LPS millimetres")
        if not self.frame_of_reference_uid.strip():
            raise GeometryError("FrameOfReferenceUID is required")
        if not _SHA256.fullmatch(self.source_volume_sha256):
            raise GeometryError("source_volume_sha256 must be lowercase SHA256")
        if affine[12:] != (0.0, 0.0, 0.0, 1.0):
            raise GeometryError("affine last row must be [0, 0, 0, 1]")
        determinant = (
            affine[0] * (affine[5] * affine[10] - affine[6] * affine[9])
            - affine[1] * (affine[4] * affine[10] - affine[6] * affine[8])
            + affine[2] * (affine[4] * affine[9] - affine[5] * affine[8])
        )
        if abs(determinant) < 1e-12:
            raise GeometryError("IJK-to-LPS affine is singular")
        object.__setattr__(self, "spacing_mm", spacing)
        object.__setattr__(self, "ijk_to_lps", affine)

    def index_to_lps(self, index_ijk: Iterable[float]) -> tuple[float, float, float]:
        i, j, k = _finite_tuple(index_ijk, 3, "index_ijk")
        m = self.ijk_to_lps
        return (
            m[0] * i + m[1] * j + m[2] * k + m[3],
            m[4] * i + m[5] * j + m[6] * k + m[7],
            m[8] * i + m[9] * j + m[10] * k + m[11],
        )

    def index_to_ras(self, index_ijk: Iterable[float]) -> tuple[float, float, float]:
        left, posterior, superior = self.index_to_lps(index_ijk)
        return (-left, -posterior, superior)

    def lps_to_index(self, point_lps: Iterable[float]) -> tuple[float, float, float]:
        """Apply the analytic inverse affine without an optional NumPy dependency."""
        x, y, z = _finite_tuple(point_lps, 3, "point_lps")
        m = self.ijk_to_lps
        a, b, c, d, e, f, g, h, i = (
            m[0], m[1], m[2], m[4], m[5], m[6], m[8], m[9], m[10]
        )
        determinant = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
        inverse = (
            (e * i - f * h) / determinant,
            (c * h - b * i) / determinant,
            (b * f - c * e) / determinant,
            (f * g - d * i) / determinant,
            (a * i - c * g) / determinant,
            (c * d - a * f) / determinant,
            (d * h - e * g) / determinant,
            (b * g - a * h) / determinant,
            (a * e - b * d) / determinant,
        )
        relative = (x - m[3], y - m[7], z - m[11])
        return tuple(
            inverse[row * 3] * relative[0]
            + inverse[row * 3 + 1] * relative[1]
            + inverse[row * 3 + 2] * relative[2]
            for row in range(3)
        )  # type: ignore[return-value]


