"""DICOM discovery, selection, geometry, and pixel transforms."""

from .dicom_affine_builder import DicomGeometryInput, build_case_geometry
from .dicom_series_scanner import SeriesMetadata, scan_dicom_directory, scan_headers
from .dicom_series_validator import SeriesValidationError, validate_selected_series

__all__ = [
    "DicomGeometryInput",
    "SeriesMetadata",
    "SeriesValidationError",
    "build_case_geometry",
    "scan_dicom_directory",
    "scan_headers",
    "validate_selected_series",
]

