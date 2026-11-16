"""Progress parsing, resource telemetry, and PHI-safe JSONL run logs."""

from __future__ import annotations

from dataclasses import dataclass
import ctypes
import json
import os
from pathlib import Path
import re
import time
import uuid


@dataclass(frozen=True)
class ProgressUpdate:
    stage: str
    message: str
    percent: int | None = None


_STAGES = (
    ("Downloading model", "Tải model"),
    ("Generating rough segmentation", "Khoanh vùng phổi"),
    ("Writing input file", "Chuẩn bị CT"),
    ("Creating segmentations", "Khởi động mô hình"),
    ("Predicting", "AI đang suy luận"),
    ("Resampling", "Đưa kết quả về CT gốc"),
    ("Saving segmentations", "Lưu mask tạm"),
    ("Importing segmentation", "Nhập kết quả vào Slicer"),
    ("Processing completed", "Hoàn tất TotalSegmentator"),
)
_PERCENT = re.compile(r"(?<!\d)(\d{1,3})%\|.*?(\d+)/(\d+)")


def parse_totalseg_progress(text: str) -> ProgressUpdate | None:
    line = " ".join(str(text).split())
    if not line:
        return None
    if line.startswith("PTL "):
        role = next((name for name in ("airway", "artery", "vein") if name in line), "tree")
        if "extracting centerline" in line:
            message = f"PTL {role}: đang tạo graph tâm tuyến"
        elif "loading verified checkpoint" in line:
            message = f"PTL {role}: đang nạp checkpoint đã xác minh"
        elif "classifying" in line:
            message = f"PTL {role}: đang phân lớp voxel"
        elif "exporting" in line:
            message = f"PTL {role}: đang lấy mask từ Slicer"
        else:
            message = f"PTL {role}: đang xử lý"
        return ProgressUpdate("PTL A/B/V", message)
    if line.startswith("3D surface:"):
        match = re.search(r"node (\d+)/(\d+)", line)
        message = "Đang dựng bề mặt 3D"
        percent = None
        if match:
            current, total = int(match.group(1)), int(match.group(2))
            percent = int(100 * (current - 1) / max(1, total))
            message += f": {current}/{total}"
        return ProgressUpdate("Dựng bề mặt 3D", message, percent)
    if line.startswith("HTML capture:"):
        match = re.search(r"(\d+)/(\d+)", line)
        if match:
            current, total = int(match.group(1)), int(match.group(2))
            detail = line.split("—", 1)[-1].strip() if "—" in line else line
            return ProgressUpdate(
                "Sao chép bề mặt nguồn",
                f"Sao chép {current}/{total}: {detail}",
                max(1, int(5 * current / max(1, total))),
            )
    if line.startswith("HTML export:"):
        node_match = re.search(r"(\d+)/(\d+)", line)
        stage_match = re.search(r"stage (\d+)/(\d+)", line)
        if node_match:
            current, total = int(node_match.group(1)), int(node_match.group(2))
            stage_fraction = 0.0
            if stage_match:
                stage_fraction = int(stage_match.group(1)) / max(
                    1, int(stage_match.group(2))
                )
            percent = min(
                96,
                5 + int(90 * ((current - 1) + stage_fraction) / max(1, total)),
            )
            detail = line.split("—", 1)[-1].strip() if "—" in line else line
            return ProgressUpdate(
                "Tối ưu mesh HTML",
                f"Cấu trúc {current}/{total}: {detail}",
                percent,
            )
        return ProgressUpdate(
            "Đóng gói HTML",
            line.removeprefix("HTML export:").strip(),
            98,
        )
    for marker, stage in _STAGES:
        if marker.lower() in line.lower():
            return ProgressUpdate(stage, stage, 100 if marker == "Processing completed" else None)
    match = _PERCENT.search(line)
    if match:
        percent = min(100, int(match.group(1)))
        return ProgressUpdate("AI đang suy luận", f"Tiến độ tác vụ con: {percent}%", percent)
    if "Collecting results" in line:
        return ProgressUpdate("Ghép kết quả", "Đang ghép các khối dự đoán")
    return None


class _MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("length", ctypes.c_ulong),
        ("memory_load", ctypes.c_ulong),
        ("total_phys", ctypes.c_ulonglong),
        ("avail_phys", ctypes.c_ulonglong),
        ("total_page", ctypes.c_ulonglong),
        ("avail_page", ctypes.c_ulonglong),
        ("total_virtual", ctypes.c_ulonglong),
        ("avail_virtual", ctypes.c_ulonglong),
        ("avail_extended_virtual", ctypes.c_ulonglong),
    ]


class SystemResourceSampler:
    """Samples system-wide CPU and RAM without adding a package dependency."""

    def __init__(self) -> None:
        self._last_times = self._system_times()

    @staticmethod
    def _system_times():
        if os.name != "nt":
            return None
        idle, kernel, user = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
        ok = ctypes.windll.kernel32.GetSystemTimes(
            ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
        )
        return (idle.value, kernel.value, user.value) if ok else None

    def sample(self) -> dict[str, float | int | None]:
        cpu_percent = None
        current = self._system_times()
        if current and self._last_times:
            idle_delta = current[0] - self._last_times[0]
            total_delta = (current[1] - self._last_times[1]) + (current[2] - self._last_times[2])
            if total_delta > 0:
                cpu_percent = round(100.0 * (total_delta - idle_delta) / total_delta, 1)
        self._last_times = current

        memory_percent = None
        available_gb = None
        if os.name == "nt":
            status = _MemoryStatus()
            status.length = ctypes.sizeof(_MemoryStatus)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                memory_percent = float(status.memory_load)
                available_gb = round(status.avail_phys / (1024**3), 2)
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "available_memory_gb": available_gb,
            "logical_cpus": os.cpu_count(),
        }


class ResearchRunLogger:
    """Append-only structured log that never records patient names or source paths."""

    def __init__(self, task: str, metadata: dict | None = None, root: Path | None = None) -> None:
        base = root or Path(os.environ.get("LOCALAPPDATA", Path.home())) / "PulmoSlicerAI" / "logs"
        base.mkdir(parents=True, exist_ok=True)
        self.run_id = uuid.uuid4().hex
        self.path = base / f"run-{time.strftime('%Y%m%d-%H%M%S')}-{self.run_id[:8]}.jsonl"
        self._start = time.monotonic()
        self.write("run_started", task=task, **(metadata or {}))

    def write(self, event: str, **fields) -> None:
        payload = {
            "schema": "pulmoslicer.runlog/1.0",
            "run_id": self.run_id,
            "event": event,
            "elapsed_seconds": round(time.monotonic() - self._start, 3),
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
