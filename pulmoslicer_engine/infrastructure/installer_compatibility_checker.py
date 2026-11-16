"""IN15: deterministic target-system compatibility checks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TargetSystem:
    windows_build: int
    architecture: str
    slicer_version: str
    slicer_revision: int
    embedded_python: tuple[int, int]
    ram_gib: float


@dataclass(frozen=True)
class CompatibilityReport:
    supported: bool
    profile: str
    findings: tuple[str, ...]
    contract_version: str = "1.0.0"


def check_compatibility(target: TargetSystem) -> CompatibilityReport:
    findings: list[str] = []
    if target.architecture.lower() not in {"amd64", "x86_64"}:
        findings.append("UNSUPPORTED_ARCHITECTURE")
    if target.windows_build < 22000:
        findings.append("UNSUPPORTED_WINDOWS_BUILD")
    if target.slicer_version != "5.12.4" or target.slicer_revision != 34645:
        findings.append("UNSUPPORTED_SLICER_VERSION")
    if target.embedded_python < (3, 9) or target.embedded_python >= (3, 14):
        findings.append("UNSUPPORTED_EMBEDDED_PYTHON")
    if target.ram_gib < 16:
        profile = "BLOCKED"
        findings.append("INSUFFICIENT_RAM")
    elif target.ram_gib < 32:
        profile = "LITE"
    elif target.ram_gib < 64:
        profile = "STANDARD"
    else:
        profile = "PERFORMANCE"
    return CompatibilityReport(not findings, profile, tuple(findings))

