"""IO02: explicit one-series selection and geometry consistency checks."""

from __future__ import annotations

import math

from .dicom_series_scanner import SeriesMetadata


class SeriesValidationError(ValueError):
    """Selected input is ambiguous, incomplete, or unsafe for measurement."""


def _normal(orientation: tuple[float, ...]) -> tuple[float, float, float]:
    row, column = orientation[:3], orientation[3:]
    return (
        row[1] * column[2] - row[2] * column[1],
        row[2] * column[0] - row[0] * column[2],
        row[0] * column[1] - row[1] * column[0],
    )


def validate_selected_series(
    series: tuple[SeriesMetadata, ...], selected_uid: str, spacing_tolerance_mm: float = 0.05
) -> SeriesMetadata:
    matches = [item for item in series if item.series_instance_uid == selected_uid]
    if len(matches) != 1:
        raise SeriesValidationError("AMBIGUOUS_SERIES: explicitly select one existing series")
    selected = matches[0]
    if selected.modality != "CT" or selected.slice_count < 2:
        raise SeriesValidationError("BLOCKED_INPUT: selected series is not a multi-slice CT")
    instances = selected.instances
    if len({item.sop_instance_uid for item in instances}) != len(instances):
        raise SeriesValidationError("BLOCKED_INPUT: duplicate SOPInstanceUID")
    reference = instances[0]
    if any(item.frame_of_reference_uid != reference.frame_of_reference_uid for item in instances):
        raise SeriesValidationError("BLOCKED_INPUT: mixed FrameOfReferenceUID")
    if any(
        item.rows != reference.rows
        or item.columns != reference.columns
        or item.pixel_spacing != reference.pixel_spacing
        or item.image_orientation_patient != reference.image_orientation_patient
        for item in instances
    ):
        raise SeriesValidationError("BLOCKED_INPUT: inconsistent per-slice geometry")
    normal = _normal(reference.image_orientation_patient)
    normal_length = math.sqrt(sum(value * value for value in normal))
    if abs(normal_length - 1.0) > 1e-4:
        raise SeriesValidationError("INVALID_GEOMETRY: orientation is not orthonormal")
    projected = sorted(
        sum(position * axis for position, axis in zip(item.image_position_patient, normal))
        for item in instances
    )
    gaps = [right - left for left, right in zip(projected, projected[1:])]
    if any(gap <= 0 for gap in gaps):
        raise SeriesValidationError("BLOCKED_INPUT: duplicate slice position")
    nominal = sum(gaps) / len(gaps)
    if any(abs(gap - nominal) > spacing_tolerance_mm for gap in gaps):
        raise SeriesValidationError("BLOCKED_INPUT: missing slice or variable spacing")
    return SeriesMetadata(
        selected.series_instance_uid,
        selected.modality,
        selected.slice_count,
        selected.description,
        tuple(sorted(instances, key=lambda item: sum(
            position * axis for position, axis in zip(item.image_position_patient, normal)
        ))),
    )

