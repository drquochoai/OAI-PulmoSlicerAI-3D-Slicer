"""IO03: construct DICOM IJK-to-LPS affine from a validated classic CT series."""

from __future__ import annotations

from dataclasses import dataclass
import math

from pulmoslicer_engine.domain.case_geometry import CaseGeometry, GeometryError
from .dicom_series_scanner import SeriesMetadata


@dataclass(frozen=True)
class DicomGeometryInput:
    series: SeriesMetadata
    source_volume_sha256: str


def build_case_geometry(source: DicomGeometryInput) -> CaseGeometry:
    instances = source.series.instances
    if len(instances) < 2:
        raise GeometryError("at least two validated slices are required")
    first, second = instances[0], instances[1]
    row_direction = first.image_orientation_patient[:3]
    column_direction = first.image_orientation_patient[3:]
    normal = (
        row_direction[1] * column_direction[2] - row_direction[2] * column_direction[1],
        row_direction[2] * column_direction[0] - row_direction[0] * column_direction[2],
        row_direction[0] * column_direction[1] - row_direction[1] * column_direction[0],
    )
    delta = tuple(b - a for a, b in zip(first.image_position_patient, second.image_position_patient))
    slice_spacing = abs(sum(value * axis for value, axis in zip(delta, normal)))
    if not math.isfinite(slice_spacing) or slice_spacing <= 0:
        raise GeometryError("slice spacing is invalid")
    row_spacing, column_spacing = first.pixel_spacing
    origin = first.image_position_patient
    affine = (
        row_direction[0] * column_spacing,
        column_direction[0] * row_spacing,
        normal[0] * slice_spacing,
        origin[0],
        row_direction[1] * column_spacing,
        column_direction[1] * row_spacing,
        normal[1] * slice_spacing,
        origin[1],
        row_direction[2] * column_spacing,
        column_direction[2] * row_spacing,
        normal[2] * slice_spacing,
        origin[2],
        0.0,
        0.0,
        0.0,
        1.0,
    )
    return CaseGeometry(
        shape_ijk=(first.columns, first.rows, len(instances)),
        spacing_mm=(column_spacing, row_spacing, slice_spacing),
        ijk_to_lps=affine,
        frame_of_reference_uid=first.frame_of_reference_uid,
        source_volume_sha256=source.source_volume_sha256,
    )

