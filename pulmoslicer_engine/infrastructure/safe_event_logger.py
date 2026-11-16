"""IN13: structured JSONL logger that excludes identifiers and patient paths."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Mapping


_ALLOWED = frozenset({"stage_id", "job_id", "error_code", "duration_ms", "model_sha256", "message"})
_CONTROL = re.compile(r"[\x00-\x1f\x7f\x9b]")
_UID = re.compile(r"\b(?:\d+\.){3,}\d+\b")
_WINDOWS_PATH = re.compile(r"(?i)(?:[a-z]:\\|\\\\)[^\s]+")
_MRN = re.compile(r"(?i)\b(?:mrn|patient(?:_?id|_?name)?)\s*[:=]\s*\S+")


class UnsafeEventError(ValueError):
    """Structured event contains a forbidden field or unsafe value."""


def sanitize_text(value: str) -> str:
    cleaned = _CONTROL.sub(" ", value)
    cleaned = _WINDOWS_PATH.sub("[REDACTED_PATH]", cleaned)
    cleaned = _UID.sub("[REDACTED_UID]", cleaned)
    cleaned = _MRN.sub("[REDACTED_IDENTIFIER]", cleaned)
    return cleaned[:1000]


def safe_event(event: Mapping[str, object]) -> dict[str, object]:
    forbidden = set(event) - _ALLOWED
    if forbidden:
        raise UnsafeEventError(f"event contains forbidden fields: {sorted(forbidden)}")
    output: dict[str, object] = {
        "contract_version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    for key, value in event.items():
        output[key] = sanitize_text(value) if isinstance(value, str) else value
    return output


class SafeEventLogger:
    def __init__(self, destination: Path) -> None:
        self.destination = Path(destination)

    def append(self, event: Mapping[str, object]) -> None:
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(safe_event(event), ensure_ascii=True, sort_keys=True)
        with self.destination.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded + "\n")

