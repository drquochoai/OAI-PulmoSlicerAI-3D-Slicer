"""IO10: validate source linkage, geometry, class completeness, and nonempty masks."""

from __future__ import annotations

from dataclasses import dataclass

from pulmoslicer_engine.domain.case_geometry import CaseGeometry


@dataclass(frozen=True)
class MaskMetadata:
    class_name: str
    shape_ijk: tuple[int, int, int]
    ijk_to_lps: tuple[float, ...]
    foreground_voxels: int
    source_volume_sha256: str


@dataclass(frozen=True)
class MaskValidationReport:
    valid: bool
    findings: tuple[str, ...]


def validate_masks(
    masks: tuple[MaskMetadata, ...],
    expected_classes: frozenset[str],
    geometry: CaseGeometry,
    affine_tolerance: float = 1e-5,
) -> MaskValidationReport:
    findings: list[str] = []
    names = [mask.class_name for mask in masks]
    if set(names) != set(expected_classes) or len(names) != len(set(names)):
        findings.append("CLASS_MAP_MISMATCH")
    for mask in masks:
        if mask.source_volume_sha256 != geometry.source_volume_sha256:
            findings.append(f"SOURCE_MISMATCH:{mask.class_name}")
        if mask.shape_ijk != geometry.shape_ijk:
            findings.append(f"SHAPE_MISMATCH:{mask.class_name}")
        if len(mask.ijk_to_lps) != 16 or any(
            abs(actual - expected) > affine_tolerance
            for actual, expected in zip(mask.ijk_to_lps, geometry.ijk_to_lps)
        ):
            findings.append(f"AFFINE_MISMATCH:{mask.class_name}")
        if mask.foreground_voxels <= 0:
            findings.append(f"EMPTY_MASK:{mask.class_name}")
    return MaskValidationReport(not findings, tuple(findings))

