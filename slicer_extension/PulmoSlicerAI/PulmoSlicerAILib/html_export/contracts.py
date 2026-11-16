"""Versioned contracts for the interactive HTML export capability."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "1.0.0"
VIEWER_VERSION = "1.0.0"
SUPPORTED_PROFILES = ("quick", "standard", "detail")


@dataclass(frozen=True)
class ExportOptions:
    output_path: Path
    profile: str = "standard"
    color_template_id: str = "pulmoslicer-surgical-contrast-v1"
    case_title: str = "PulmoSlicer Case"
    select_all_valid: bool = True
    show_all_on_open: bool = True
    anonymize: bool = True

    def validate(self) -> None:
        if self.profile not in SUPPORTED_PROFILES:
            raise ValueError(f"Unsupported HTML quality profile: {self.profile}")
        if self.output_path.suffix.lower() != ".html":
            raise ValueError("Interactive export must use a .html file")
        if not self.anonymize:
            raise ValueError("HTML export requires anonymization in this release")
        if not self.case_title.strip():
            raise ValueError("Case title must not be empty")


@dataclass(frozen=True)
class MeshRecord:
    stable_id: str
    display_name: str
    hierarchy_path: tuple[str, ...]
    anatomy_class: str
    color: tuple[float, float, float]
    opacity: float
    visible: bool
    payload_b64: str
    payload_sha256: str
    payload_bytes: int
    vertex_count: int
    triangle_count: int
    bounds_web_mm: tuple[float, float, float, float, float, float]
    source_hash: str
    qa: dict[str, Any] = field(default_factory=dict)

    def manifest_entry(self) -> dict[str, Any]:
        return {
            "id": self.stable_id,
            "name": self.display_name,
            "path": list(self.hierarchy_path),
            "class": self.anatomy_class,
            "color": list(self.color),
            "opacity": self.opacity,
            "visible": self.visible,
            "payloadId": f"mesh-{self.stable_id}",
            "payloadSha256": self.payload_sha256,
            "payloadBytes": self.payload_bytes,
            "vertexCount": self.vertex_count,
            "triangleCount": self.triangle_count,
            "boundsWebMm": list(self.bounds_web_mm),
            "sourceHash": self.source_hash,
            "qa": self.qa,
        }


@dataclass(frozen=True)
class HtmlExportResult:
    output_path: Path
    node_count: int
    triangle_count: int
    byte_count: int
    file_sha256: str
    warnings: tuple[str, ...]
    validation_report: dict[str, Any]
