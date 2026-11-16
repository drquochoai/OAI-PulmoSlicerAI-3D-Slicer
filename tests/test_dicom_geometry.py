import unittest
import tempfile
from pathlib import Path

from pulmoslicer_engine.adapters.dicom.dicom_affine_builder import DicomGeometryInput, build_case_geometry
from pulmoslicer_engine.adapters.dicom.dicom_series_scanner import scan_headers
from pulmoslicer_engine.adapters.dicom.dicom_series_validator import SeriesValidationError, validate_selected_series
from pulmoslicer_engine.adapters.dicom.dicom_volume_decoder import stored_values_to_hu
from pulmoslicer_engine.adapters.dicom.geometry_roundtrip_validator import validate_geometry_roundtrip


HASH = "b" * 64


def header(series="1.2.3", sop="1.2.3.1", z=0.0, x_direction=(1, 0, 0), y_direction=(0, 1, 0)):
    return {
        "SeriesInstanceUID": series,
        "SOPInstanceUID": sop,
        "FrameOfReferenceUID": "9.8.7",
        "Modality": "CT",
        "Rows": 4,
        "Columns": 5,
        "PixelSpacing": [0.8, 0.6],
        "ImageOrientationPatient": [*x_direction, *y_direction],
        "ImagePositionPatient": [100.0, 20.0, z],
        "RescaleSlope": 2,
        "RescaleIntercept": -1024,
    }


class DicomGeometryTests(unittest.TestCase):
    def series(self):
        scanned = scan_headers([header(sop="1.2.3.1", z=0), header(sop="1.2.3.2", z=1.5)])
        return validate_selected_series(scanned, "1.2.3")

    def test_header_scan_does_not_require_pixels(self):
        selected = self.series()
        self.assertEqual(selected.slice_count, 2)
        self.assertEqual(selected.instances[0].rescale_intercept, -1024)

    def test_explicit_series_choice_is_required(self):
        scanned = scan_headers([
            header(series="1.2.3", sop="1.2.3.1", z=0),
            header(series="1.2.3", sop="1.2.3.2", z=1),
            header(series="4.5.6", sop="4.5.6.1", z=0),
            header(series="4.5.6", sop="4.5.6.2", z=1),
        ])
        with self.assertRaisesRegex(SeriesValidationError, "AMBIGUOUS_SERIES"):
            validate_selected_series(scanned, "")

    def test_duplicate_sop_and_slice_gap_are_blocked(self):
        duplicate = scan_headers([header(sop="same", z=0), header(sop="same", z=1)])
        with self.assertRaisesRegex(SeriesValidationError, "duplicate SOP"):
            validate_selected_series(duplicate, "1.2.3")
        gap = scan_headers([
            header(sop="1", z=0), header(sop="2", z=1), header(sop="3", z=3)
        ])
        with self.assertRaisesRegex(SeriesValidationError, "missing slice"):
            validate_selected_series(gap, "1.2.3")

    def test_affine_uses_dicom_pixel_spacing_order(self):
        geometry = build_case_geometry(DicomGeometryInput(self.series(), HASH))
        self.assertEqual(geometry.shape_ijk, (5, 4, 2))
        self.assertEqual(geometry.spacing_mm, (0.6, 0.8, 1.5))
        self.assertEqual(geometry.index_to_lps((1, 1, 1)), (100.6, 20.8, 1.5))

    def test_oblique_affine_and_roundtrip(self):
        scanned = scan_headers([
            header(sop="1", z=0, x_direction=(0, 1, 0), y_direction=(0, 0, 1)),
            {**header(sop="2", z=0, x_direction=(0, 1, 0), y_direction=(0, 0, 1)),
             "ImagePositionPatient": [101.5, 20, 0]},
        ])
        geometry = build_case_geometry(DicomGeometryInput(validate_selected_series(scanned, "1.2.3"), HASH))
        point = geometry.index_to_lps((1, 2, 1))
        self.assertEqual(point, (101.5, 20.6, 1.6))
        recovered = geometry.lps_to_index(point)
        for actual, expected in zip(recovered, (1, 2, 1)):
            self.assertAlmostEqual(actual, expected)

    def test_asymmetric_marker_detects_mirror(self):
        geometry = build_case_geometry(DicomGeometryInput(self.series(), HASH))
        report = validate_geometry_roundtrip(
            geometry, [(0, 0, 0), (4, 3, 1)], left_marker_ijk=(4, 0, 0), right_marker_ijk=(0, 0, 0)
        )
        self.assertTrue(report.valid)
        mirrored = validate_geometry_roundtrip(
            geometry, [(0, 0, 0)], left_marker_ijk=(0, 0, 0), right_marker_ijk=(4, 0, 0)
        )
        self.assertIn("LEFT_RIGHT_MIRRORED", mirrored.findings)

    def test_hu_transform_preserves_stored_input(self):
        stored = (0, 500, 1024)
        self.assertEqual(stored_values_to_hu(stored, 2, -1024), (-1024.0, -24.0, 1024.0))
        self.assertEqual(stored, (0, 500, 1024))

    def test_real_pydicom_headers_are_scanned_without_pixel_decode(self):
        try:
            from pydicom.dataset import FileDataset, FileMetaDataset
            from pydicom.uid import ExplicitVRLittleEndian, CTImageStorage
        except ImportError:
            self.skipTest("pydicom integration dependency is not installed")
        from pulmoslicer_engine.adapters.dicom.dicom_series_scanner import scan_dicom_directory

        with tempfile.TemporaryDirectory() as directory:
            for number, z in enumerate((0.0, 1.0), start=1):
                meta = FileMetaDataset()
                meta.TransferSyntaxUID = ExplicitVRLittleEndian
                meta.MediaStorageSOPClassUID = CTImageStorage
                meta.MediaStorageSOPInstanceUID = f"1.2.826.0.1.3680043.10.999.{number}"
                dataset = FileDataset(None, {}, file_meta=meta, preamble=b"\0" * 128)
                dataset.SOPClassUID = CTImageStorage
                dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
                dataset.SeriesInstanceUID = "1.2.826.0.1.3680043.10.999.100"
                dataset.FrameOfReferenceUID = "1.2.826.0.1.3680043.10.999.200"
                dataset.Modality = "CT"
                dataset.Rows, dataset.Columns = 4, 5
                dataset.PixelSpacing = [0.8, 0.6]
                dataset.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
                dataset.ImagePositionPatient = [100, 20, z]
                dataset.RescaleSlope, dataset.RescaleIntercept = 2, -1024
                dataset.PatientName = "SYNTHETIC^PHANTOM"
                dataset.PixelData = b"not decoded by scanner"
                dataset.save_as(Path(directory) / f"slice-{number}.dcm", enforce_file_format=True)
            scanned = scan_dicom_directory(Path(directory))
            selected = validate_selected_series(scanned, scanned[0].series_instance_uid)
            self.assertEqual(selected.slice_count, 2)
            self.assertEqual(selected.instances[0].image_position_patient, (100.0, 20.0, 0.0))


if __name__ == "__main__":
    unittest.main()
