import base64
import gzip
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[1]
MODULE_ROOT = REPOSITORY_ROOT / "slicer_extension" / "PulmoSlicerAI"
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(MODULE_ROOT))

from PulmoSlicerAILib.html_export.anatomy import AnatomyDescriptor, describe_segment
from PulmoSlicerAILib.html_export.color_templates import color_for, template_names
from PulmoSlicerAILib.html_export.contracts import ExportOptions, MeshRecord
from PulmoSlicerAILib.html_export.html_writer import render_html, write_atomic_html
from PulmoSlicerAILib.html_export.mesh_codec import MAGIC, encode_mesh
from PulmoSlicerAILib.html_export.privacy import scan_html_for_phi, validate_case_title
from PulmoSlicerAILib.html_export.exporter import CapturedAnatomy, InteractiveHtmlExporter


def _mesh_record(payload, digest, size):
    return MeshRecord(
        stable_id="ptl-a-r-01",
        display_name="A1 Right",
        hierarchy_path=("Lungs", "Right", "Upper", "Pulmonary arteries", "S1"),
        anatomy_class="artery",
        color=(0.93, 0.25, 0.23),
        opacity=1.0,
        visible=True,
        payload_b64=payload,
        payload_sha256=digest,
        payload_bytes=size,
        vertex_count=3,
        triangle_count=1,
        bounds_web_mm=(0.0, 1.0, 0.0, 1.0, 0.0, 0.0),
        source_hash="a" * 64,
        qa={"sourcePreserved": True},
    )


class MeshCodecTests(unittest.TestCase):
    def test_roundtrip_header_and_counts(self):
        payload, digest, size, raw = encode_mesh(
            (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
            (0, 1, 2),
        )
        decoded = gzip.decompress(base64.b64decode(payload))
        self.assertEqual(decoded, raw)
        self.assertEqual(decoded[:8], MAGIC)
        self.assertEqual(struct.unpack("<II", decoded[8:16]), (3, 3))
        self.assertEqual(len(digest), 64)
        self.assertEqual(size, len(base64.b64decode(payload)))

    def test_invalid_index_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            encode_mesh((0.0, 0.0, 0.0), (0, 1, 2))


class AnatomyAllowlistTests(unittest.TestCase):
    def test_ptl_and_lobe_have_stable_hierarchy(self):
        artery = describe_segment("ptl", "PTL_A_R_01")
        lobe = describe_segment("lobes", "lung_upper_lobe_right")
        self.assertEqual(artery.display_name, "A1 Right")
        self.assertEqual(artery.path[:3], ("Lungs", "Right", "Upper"))
        self.assertEqual(lobe.anatomy_class, "lobe_right_upper")

    def test_excluded_and_unknown_anatomy_never_exports(self):
        self.assertIsNone(describe_segment("chest_wall", "clavicula_left"))
        self.assertIsNone(describe_segment("chest_wall", "scapula_right"))
        self.assertIsNone(describe_segment("chest_wall", "costal_cartilage_1"))
        self.assertIsNone(describe_segment("", "Patient Name Segment"))


class HtmlWriterTests(unittest.TestCase):
    def setUp(self):
        payload, digest, size, _ = encode_mesh(
            (0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
            (0, 1, 2),
        )
        self.mesh = _mesh_record(payload, digest, size)

    def test_single_file_contains_viewer_payload_and_default_all(self):
        with tempfile.TemporaryDirectory() as directory:
            options = ExportOptions(Path(directory) / "case.html")
            document = render_html(options, (self.mesh,))
        self.assertIn("viewerVersion", document)
        self.assertIn("selectAllValid", document)
        self.assertIn("mesh-ptl-a-r-01", document)
        self.assertNotIn("<script src=", document.lower())
        self.assertNotIn("<link href=", document.lower())
        self.assertIn("connect-src 'none'", document)

    def test_atomic_writer_reports_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "case.html"
            digest, size, report = write_atomic_html(
                ExportOptions(destination), (self.mesh,)
            )
            self.assertTrue(destination.exists())
            self.assertFalse(destination.with_suffix(".html.partial").exists())
            self.assertEqual(len(digest), 64)
            self.assertGreater(size, 100_000)
            self.assertEqual(report["phiScan"], "PASS")

    def test_privacy_checks_reject_obvious_identifiers(self):
        with self.assertRaisesRegex(ValueError, "định danh"):
            validate_case_title("Patient MRN 123")
        self.assertEqual(scan_html_for_phi("PatientName=Example"), ("patientname",))

    def test_templates_are_complete_for_core_systems(self):
        self.assertGreaterEqual(len(template_names()), 4)
        for anatomy in ("airway", "artery", "vein", "aorta", "tumor", "bone"):
            self.assertEqual(len(color_for("pulmoslicer-surgical-contrast-v1", anatomy)), 4)

    def test_background_export_honors_cancellation_before_vtk_work(self):
        descriptor = AnatomyDescriptor(
            "ptl-a-r-01", "A1 Right", ("Lungs", "Right"), "artery"
        )
        captured = ((CapturedAnatomy("PTL_A_R_01", descriptor, object()),), ())
        with tempfile.TemporaryDirectory() as directory:
            options = ExportOptions(Path(directory) / "cancelled.html")
            with self.assertRaisesRegex(RuntimeError, "người dùng hủy"):
                InteractiveHtmlExporter().export_captured(
                    captured, options, cancellation_check=lambda: True
                )


if __name__ == "__main__":
    unittest.main()
