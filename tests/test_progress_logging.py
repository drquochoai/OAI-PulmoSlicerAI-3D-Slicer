import json
import tempfile
import unittest
from pathlib import Path
import sys


MODULE_ROOT = Path(__file__).parents[1] / "slicer_extension" / "PulmoSlicerAI"
sys.path.insert(0, str(MODULE_ROOT))

from PulmoSlicerAILib.progress import ResearchRunLogger, parse_totalseg_progress


class ProgressLoggingTests(unittest.TestCase):
    def test_stage_message_is_mapped_to_vietnamese(self):
        update = parse_totalseg_progress("Predicting...")
        self.assertEqual(update.stage, "AI đang suy luận")
        self.assertIsNone(update.percent)

    def test_tqdm_progress_is_parsed(self):
        update = parse_totalseg_progress(" 42%|#### | 61/144 [01:20<02:00]")
        self.assertEqual(update.percent, 42)
        self.assertIn("42%", update.message)

    def test_unknown_or_path_message_is_not_logged_as_progress(self):
        self.assertIsNone(parse_totalseg_progress("Writing C:/Patient Name/CT.nii"))

    def test_ptl_and_surface_messages_are_visible_without_paths(self):
        ptl = parse_totalseg_progress("PTL artery: extracting centerline graph")
        surface = parse_totalseg_progress("3D surface: node 2/3, profile preview")
        self.assertEqual(ptl.stage, "PTL A/B/V")
        self.assertIn("artery", ptl.message)
        self.assertEqual(surface.percent, 33)

    def test_html_export_progress_replaces_current_structure(self):
        update = parse_totalseg_progress("HTML export: 3/8 — A6 Right")
        self.assertEqual(update.stage, "Tối ưu mesh HTML")
        self.assertEqual(update.percent, 27)
        self.assertIn("A6 Right", update.message)

        staged = parse_totalseg_progress(
            "HTML export: 1/8 stage 3/6 — A1 Right — làm mượt bề mặt"
        )
        self.assertEqual(staged.percent, 10)
        self.assertIn("làm mượt", staged.message)

        captured = parse_totalseg_progress("HTML capture: 5/10 — V3 Left")
        self.assertEqual(captured.stage, "Sao chép bề mặt nguồn")
        self.assertEqual(captured.percent, 2)

    def test_jsonl_logger_contains_no_implicit_patient_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            logger = ResearchRunLogger(
                "lung_vessels",
                {"backend": "cpu", "patient_data_recorded": False},
                root=Path(directory),
            )
            logger.write("progress", stage="AI đang suy luận", percent=50)
            records = [json.loads(line) for line in logger.path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(records[0]["task"], "lung_vessels")
            self.assertFalse(records[0]["patient_data_recorded"])
            self.assertNotIn("patient_name", logger.path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
