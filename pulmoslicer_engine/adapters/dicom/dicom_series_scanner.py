"""IO01: scan DICOM headers without decoding patient pixel data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


class DicomScanError(ValueError):
    """No safe, usable CT series metadata could be obtained."""


@dataclass(frozen=True)
class InstanceMetadata:
    sop_instance_uid: str
    frame_of_reference_uid: str
    rows: int
    columns: int
    pixel_spacing: tuple[float, float]
    image_orientation_patient: tuple[float, ...]
    image_position_patient: tuple[float, ...]
    rescale_slope: float
    rescale_intercept: float


@dataclass(frozen=True)
class SeriesMetadata:
    series_instance_uid: str
    modality: str
    slice_count: int
    description: str
    instances: tuple[InstanceMetadata, ...]


def _get(header: Mapping[str, object], name: str, default: object = None) -> object:
    value = header.get(name, default)
    return getattr(value, "value", value)


def _numbers(value: object, count: int, name: str) -> tuple[float, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != count:
        raise DicomScanError(f"{name} must contain {count} values")
    try:
        return tuple(float(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise DicomScanError(f"{name} contains a non-numeric value") from exc


def scan_headers(headers: Iterable[Mapping[str, object]]) -> tuple[SeriesMetadata, ...]:
    """Group already-read datasets; useful for deterministic fixtures and pydicom."""
    grouped: dict[str, list[InstanceMetadata]] = {}
    descriptions: dict[str, str] = {}
    modalities: dict[str, str] = {}
    for header in headers:
        series_uid = str(_get(header, "SeriesInstanceUID", "")).strip()
        sop_uid = str(_get(header, "SOPInstanceUID", "")).strip()
        modality = str(_get(header, "Modality", "")).upper()
        frame_uid = str(_get(header, "FrameOfReferenceUID", "")).strip()
        if not series_uid or not sop_uid or not frame_uid:
            raise DicomScanError("series, SOP, and FrameOfReference UIDs are required")
        try:
            instance = InstanceMetadata(
                sop_instance_uid=sop_uid,
                frame_of_reference_uid=frame_uid,
                rows=int(_get(header, "Rows")),
                columns=int(_get(header, "Columns")),
                pixel_spacing=_numbers(_get(header, "PixelSpacing"), 2, "PixelSpacing"),
                image_orientation_patient=_numbers(
                    _get(header, "ImageOrientationPatient"), 6, "ImageOrientationPatient"
                ),
                image_position_patient=_numbers(
                    _get(header, "ImagePositionPatient"), 3, "ImagePositionPatient"
                ),
                rescale_slope=float(_get(header, "RescaleSlope", 1.0)),
                rescale_intercept=float(_get(header, "RescaleIntercept", 0.0)),
            )
        except (TypeError, ValueError) as exc:
            raise DicomScanError("invalid numeric DICOM geometry metadata") from exc
        grouped.setdefault(series_uid, []).append(instance)
        descriptions[series_uid] = str(_get(header, "SeriesDescription", ""))[:120]
        modalities[series_uid] = modality
    if not grouped:
        raise DicomScanError("no DICOM headers found")
    return tuple(
        SeriesMetadata(uid, modalities[uid], len(instances), descriptions[uid], tuple(instances))
        for uid, instances in sorted(grouped.items())
    )


def scan_dicom_directory(directory: Path) -> tuple[SeriesMetadata, ...]:
    """Read headers with pydicom and explicitly stop before pixel data."""
    root = Path(directory).resolve(strict=True)
    if not root.is_dir():
        raise DicomScanError("DICOM input must be a directory")
    try:
        import pydicom
    except ImportError as exc:
        raise DicomScanError("pydicom runtime dependency is unavailable") from exc
    headers = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            dataset = pydicom.dcmread(path, stop_before_pixels=True, force=False)
        except Exception:
            continue
        headers.append(dataset)
    return scan_headers(headers)

