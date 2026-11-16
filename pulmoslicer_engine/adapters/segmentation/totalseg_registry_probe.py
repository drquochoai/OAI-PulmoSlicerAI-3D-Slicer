"""IO07: verify TotalSegmentator capabilities without loading models."""

from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from typing import Mapping


AVB_CLASSES = frozenset({"lung_airways", "lung_airways_wall", "lung_arteries", "lung_veins"})
LOBE_CLASSES = frozenset(
    {
        "lung_upper_lobe_left",
        "lung_lower_lobe_left",
        "lung_upper_lobe_right",
        "lung_middle_lobe_right",
        "lung_lower_lobe_right",
    }
)


class TotalSegProbeError(ValueError):
    """TotalSegmentator registry is absent or has an incompatible class map."""


@dataclass(frozen=True)
class TotalSegTask:
    task_name: str
    version: str
    modality: str
    license_required: bool
    class_map: Mapping[int, str]


def parse_registry(payload: Mapping[str, object], task_name: str, expected: frozenset[str]) -> TotalSegTask:
    version = payload.get("totalsegmentator_version")
    tasks = payload.get("tasks")
    if not isinstance(version, str) or not isinstance(tasks, Mapping):
        raise TotalSegProbeError("invalid totalseg_info registry envelope")
    task = tasks.get(task_name)
    if not isinstance(task, Mapping):
        raise TotalSegProbeError(f"TotalSegmentator task is unavailable: {task_name}")
    classes = task.get("classes")
    if not isinstance(classes, Mapping):
        raise TotalSegProbeError("task class map is missing")
    try:
        class_map = {int(index): str(name) for index, name in classes.items()}
    except (TypeError, ValueError) as exc:
        raise TotalSegProbeError("task class map is invalid") from exc
    if set(class_map.values()) != set(expected):
        raise TotalSegProbeError(
            f"incompatible {task_name} classes: {sorted(class_map.values())}"
        )
    return TotalSegTask(
        task_name=task_name,
        version=version,
        modality=str(task.get("modality", "")),
        license_required=bool(task.get("license_required", False)),
        class_map=class_map,
    )


def probe_installed_task(task_name: str, expected: frozenset[str]) -> TotalSegTask:
    try:
        completed = subprocess.run(
            ["totalseg_info", "--json"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )
        payload = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise TotalSegProbeError("MODEL_MISSING: totalseg_info probe failed") from exc
    return parse_registry(payload, task_name, expected)

