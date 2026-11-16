import sys
import unittest
from pathlib import Path
import os


MODULE_ROOT = Path(__file__).parents[1] / "slicer_extension" / "PulmoSlicerAI"
sys.path.insert(0, str(MODULE_ROOT))

from PulmoSlicerAILib.workflow import PulmonarySegmentationWorkflow


class _Segment:
    def __init__(self, name):
        self._name = name

    def GetName(self):
        return self._name


class _Segmentation:
    def __init__(self, names):
        self._names = list(names)

    def GetNumberOfSegments(self):
        return len(self._names)

    def GetNthSegmentID(self, index):
        return self._names[index]

    def GetSegment(self, segment_id):
        return _Segment(segment_id)


class _OutputNode:
    def __init__(self, names):
        self._segmentation = _Segmentation(names)

    def GetSegmentation(self):
        return self._segmentation


class _Logic:
    def __init__(self):
        self.calls = []
        self.omp_threads_during_process = None

    def process(self, *args, **kwargs):
        self.omp_threads_during_process = os.environ.get("OMP_NUM_THREADS")
        self.calls.append((args, kwargs))


class SlicerWorkflowTests(unittest.TestCase):
    def test_vessel_task_and_required_outputs(self):
        logic = _Logic()
        workflow = PulmonarySegmentationWorkflow(lambda: logic)
        output = _OutputNode(workflow.VESSEL_SEGMENTS)

        result = workflow.run_vessels(object(), output, quality="normal", cpu=True)

        self.assertEqual(result, workflow.VESSEL_SEGMENTS)
        self.assertEqual(logic.calls[0][1]["task"], "lung_vessels")
        self.assertEqual(logic.calls[0][1]["quality"], "normal")
        self.assertFalse(logic.calls[0][1]["interactive"])

    def test_lobe_task_requests_only_five_lobes(self):
        logic = _Logic()
        workflow = PulmonarySegmentationWorkflow(lambda: logic)
        output = _OutputNode(workflow.LOBE_SEGMENTS)

        workflow.run_lobes(object(), output)

        call = logic.calls[0][1]
        self.assertEqual(call["task"], "total")
        self.assertEqual(call["subset"], list(workflow.LOBE_SEGMENTS))
        self.assertFalse(call["interactive"])

    def test_thoracic_context_excludes_clavicle_scapula_and_costal_cartilage(self):
        logic = _Logic()
        workflow = PulmonarySegmentationWorkflow(lambda: logic)
        expected = workflow.context_segments("all")
        output = _OutputNode(expected)

        workflow.run_thoracic_context(object(), output, "all")

        subset = logic.calls[0][1]["subset"]
        self.assertIn("aorta", subset)
        self.assertIn("rib_right_1", subset)
        self.assertIn("vertebrae_T12", subset)
        self.assertNotIn("clavicula_left", subset)
        self.assertFalse(any("scapula" in name for name in subset))
        self.assertFalse(any("cartilage" in name for name in subset))

    def test_missing_segment_fails_closed(self):
        output = _OutputNode(("lung_airways", "lung_arteries"))
        with self.assertRaisesRegex(RuntimeError, "lung_veins"):
            PulmonarySegmentationWorkflow.verify_segments(
                output, PulmonarySegmentationWorkflow.VESSEL_SEGMENTS
            )

    def test_missing_input_is_rejected_before_inference(self):
        workflow = PulmonarySegmentationWorkflow(lambda: _Logic())
        with self.assertRaisesRegex(ValueError, "CT input"):
            workflow.run_vessels(None, _OutputNode(workflow.VESSEL_SEGMENTS))

    def test_vessel_fast_mode_is_rejected_instead_of_silently_ignored(self):
        workflow = PulmonarySegmentationWorkflow(lambda: _Logic())
        with self.assertRaisesRegex(ValueError, "chỉ hỗ trợ normal"):
            workflow.run_vessels(
                object(), _OutputNode(workflow.VESSEL_SEGMENTS), quality="fast"
            )

    def test_experimental_thread_override_is_scoped_to_child_run(self):
        logic = _Logic()
        workflow = PulmonarySegmentationWorkflow(lambda: logic)
        previous = os.environ.get("OMP_NUM_THREADS")
        try:
            os.environ["OMP_NUM_THREADS"] = "sentinel"
            workflow.run_vessels(
                object(),
                _OutputNode(workflow.VESSEL_SEGMENTS),
                thread_count=24,
            )
            self.assertEqual(logic.omp_threads_during_process, "24")
            self.assertEqual(os.environ["OMP_NUM_THREADS"], "sentinel")
        finally:
            if previous is None:
                os.environ.pop("OMP_NUM_THREADS", None)
            else:
                os.environ["OMP_NUM_THREADS"] = previous

    def test_totalsegmentator_worker_command_adds_supported_parallel_options(self):
        command = PulmonarySegmentationWorkflow._worker_command(
            ["PythonSlicer", "C:/Python/Scripts/TotalSegmentator.exe", "--device", "cpu"],
            "C:/Pulmo/totalseg_worker.py",
            2,
            4,
        )
        self.assertEqual(command[1], "C:/Pulmo/totalseg_worker.py")
        self.assertEqual(command[-4:], ["--nr_thr_resamp", "2", "--nr_thr_saving", "4"])

    def test_unrelated_console_command_is_not_modified(self):
        command = ["PythonSlicer", "another_tool.py"]
        self.assertEqual(
            PulmonarySegmentationWorkflow._worker_command(command, "wrapper.py", 4, 6),
            command,
        )


if __name__ == "__main__":
    unittest.main()
