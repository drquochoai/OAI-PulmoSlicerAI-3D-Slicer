"""Allowlist-oriented privacy checks for shareable HTML artifacts."""

from __future__ import annotations

import re


_FORBIDDEN_KEYS = (
    "patientname",
    "patientid",
    "patientbirth",
    "medicalrecord",
    "studyinstanceuid",
    "seriesinstanceuid",
    "sopinstanceuid",
    "dicom.",
    "users\\",
    "users/",
    "appdata",
)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def safe_text(value: str, maximum: int = 120) -> str:
    cleaned = _CONTROL.sub("", " ".join(str(value).split()))
    return cleaned[:maximum]


def validate_case_title(title: str) -> str:
    cleaned = safe_text(title, 80)
    if not cleaned:
        return "PulmoSlicer Case"
    lowered = cleaned.lower()
    if any(token in lowered for token in ("mrn", "patient", "bệnh nhân")):
        raise ValueError("Tên ca có thể chứa thông tin định danh; hãy dùng mã ẩn danh")
    return cleaned


def scan_html_for_phi(html: str) -> tuple[str, ...]:
    lowered = html.lower()
    return tuple(token for token in _FORBIDDEN_KEYS if token in lowered)
