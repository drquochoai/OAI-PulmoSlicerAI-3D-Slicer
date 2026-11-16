"""IO04: geometry roundtrip and asymmetric left/right phantom checks."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from pulmoslicer_engine.domain.case_geometry import CaseGeometry


@dataclass(frozen=True)
class GeometryValidationReport:
    valid: bool
    max_roundtrip_error_voxels: float
    left_right_preserved: bool
    findings: tuple[str, ...]


def validate_geometry_roundtrip(
    geometry: CaseGeometry,
    indices: Iterable[tuple[float, float, float]],
    left_marker_ijk: tuple[float, float, float],
    right_marker_ijk: tuple[float, float, float],
    tolerance_voxels: float = 1e-6,
) -> GeometryValidationReport:
    errors = []
    for index in indices:
        recovered = geometry.lps_to_index(geometry.index_to_lps(index))
        errors.append(math.sqrt(sum((a - b) ** 2 for a, b in zip(index, recovered))))
    maximum = max(errors, default=0.0)
    left_lps = geometry.index_to_lps(left_marker_ijk)
    right_lps = geometry.index_to_lps(right_marker_ijk)
    preserved = left_lps[0] > right_lps[0]  # DICOM LPS: +X points to patient left.
    findings = []
    if maximum > tolerance_voxels:
        findings.append("GEOMETRY_ROUNDTRIP_FAILED")
    if not preserved:
        findings.append("LEFT_RIGHT_MIRRORED")
    return GeometryValidationReport(not findings, maximum, preserved, tuple(findings))

