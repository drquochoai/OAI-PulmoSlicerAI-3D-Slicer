"""IO08: one CPU-first TotalSegmentator lung_vessels invocation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess

from .totalseg_registry_probe import AVB_CLASSES, TotalSegTask


class TotalSegInferenceError(RuntimeError):
    """Inference did not produce a complete, machine-reported AVB result."""


@dataclass(frozen=True)
class TotalSegRunResult:
    output_directory: Path
    report: dict[str, object]
    mask_files: tuple[Path, ...]


def build_lung_vessels_command(
    input_volume: Path, output_directory: Path, capability: TotalSegTask
) -> tuple[str, ...]:
    if capability.task_name != "lung_vessels" or set(capability.class_map.values()) != set(AVB_CLASSES):
        raise TotalSegInferenceError("MODEL_INCOMPATIBLE: lung_vessels capability mismatch")
    report = output_directory / "run_report.json"
    return (
        "TotalSegmentator",
        "-i",
        str(Path(input_volume)),
        "-o",
        str(Path(output_directory)),
        "--task",
        "lung_vessels",
        "--device",
        "cpu",
        "--report",
        str(report),
    )


def run_lung_vessels(
    input_volume: Path, output_directory: Path, capability: TotalSegTask
) -> TotalSegRunResult:
    output_directory.mkdir(parents=True, exist_ok=False)
    command = build_lung_vessels_command(input_volume, output_directory, capability)
    try:
        subprocess.run(command, check=True, timeout=None, shell=False)
        report_path = output_directory / "run_report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise TotalSegInferenceError("TotalSegmentator lung_vessels failed") from exc
    masks = tuple(output_directory / f"{name}.nii.gz" for name in sorted(AVB_CLASSES))
    if not all(path.is_file() for path in masks):
        raise TotalSegInferenceError("TotalSegmentator result is missing one or more AVB masks")
    return TotalSegRunResult(output_directory, report, masks)

