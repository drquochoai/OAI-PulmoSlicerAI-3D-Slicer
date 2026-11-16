"""IO09: five-lobe TotalSegmentator command using the verified total class map."""

from __future__ import annotations

from pathlib import Path

from .totalseg_inference_adapter import TotalSegInferenceError
from .totalseg_registry_probe import LOBE_CLASSES, TotalSegTask


def build_lobe_command(
    input_volume: Path, output_directory: Path, capability: TotalSegTask
) -> tuple[str, ...]:
    if capability.task_name != "total" or not LOBE_CLASSES.issubset(capability.class_map.values()):
        raise TotalSegInferenceError("MODEL_INCOMPATIBLE: five-lobe class map mismatch")
    command = [
        "TotalSegmentator",
        "-i",
        str(Path(input_volume)),
        "-o",
        str(Path(output_directory)),
        "--task",
        "total",
        "--device",
        "cpu",
        "--roi_subset",
        *sorted(LOBE_CLASSES),
        "--report",
        str(Path(output_directory) / "run_report.json"),
    ]
    return tuple(command)

