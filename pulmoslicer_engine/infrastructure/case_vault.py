"""IN01: protected per-case workspace without PHI-bearing path components."""

from __future__ import annotations

from pathlib import Path
import re
from uuid import UUID


_LAYOUT = ("source", "derived", "jobs", "revisions", "exports", "audit", "trash_quarantine")
_SAFE_PART = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class VaultSecurityError(ValueError):
    """A vault operation would escape containment or expose unsafe naming."""


class CaseVault:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve(strict=False)
        if self.root == Path(self.root.anchor):
            raise VaultSecurityError("vault root cannot be a filesystem root")

    @staticmethod
    def validate_case_id(case_id: str) -> str:
        try:
            parsed = UUID(case_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise VaultSecurityError("case_id must be a UUID") from exc
        if parsed.version != 4:
            raise VaultSecurityError("case_id must be a random UUIDv4")
        return str(parsed)

    def create_case(self, case_id: str) -> Path:
        safe_id = self.validate_case_id(case_id)
        case_path = self.root / safe_id
        case_path.mkdir(parents=True, exist_ok=True)
        for directory in _LAYOUT:
            (case_path / directory).mkdir(exist_ok=True)
        return case_path

    def contained_path(self, case_id: str, area: str, filename: str) -> Path:
        safe_id = self.validate_case_id(case_id)
        if area not in _LAYOUT:
            raise VaultSecurityError("unknown vault area")
        if not _SAFE_PART.fullmatch(filename) or filename in {".", ".."}:
            raise VaultSecurityError("unsafe filename")
        candidate = (self.root / safe_id / area / filename).resolve(strict=False)
        expected_parent = (self.root / safe_id / area).resolve(strict=False)
        if candidate.parent != expected_parent:
            raise VaultSecurityError("path escapes case vault")
        return candidate

