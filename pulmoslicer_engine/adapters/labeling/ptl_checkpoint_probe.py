"""LB01: verify a locally acquired PTL bundle before any unsafe model loading."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping


PTL_REPOSITORY_COMMIT = "27fdace577293a29480bce4f00efba7501cadd20"
REQUIRED_ROLES = frozenset({"airway", "artery", "vein"})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PtlBundleError(ValueError):
    """PTL source/spec/checkpoint evidence is absent or inconsistent."""


@dataclass(frozen=True)
class PtlCheckpoint:
    role: str
    path: Path
    sha256: str
    license_id: str


@dataclass(frozen=True)
class PtlBundle:
    repository_commit: str
    checkpoints: tuple[PtlCheckpoint, ...]
    graph_contract_version: str
    reproduced_original: bool


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_ptl_bundle(manifest_path: Path, require_reproduction: bool = True) -> PtlBundle:
    try:
        payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PtlBundleError("PTL bundle manifest is unreadable") from exc
    if payload.get("repository_commit") != PTL_REPOSITORY_COMMIT:
        raise PtlBundleError("PTL source commit is not the reviewed revision")
    entries = payload.get("checkpoints")
    if not isinstance(entries, Mapping) or set(entries) != set(REQUIRED_ROLES):
        raise PtlBundleError("exactly airway, artery, and vein checkpoints are required")
    checkpoints = []
    root = Path(manifest_path).resolve().parent
    for role in sorted(REQUIRED_ROLES):
        entry = entries[role]
        if not isinstance(entry, Mapping):
            raise PtlBundleError(f"invalid checkpoint entry: {role}")
        relative = Path(str(entry.get("file", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise PtlBundleError("checkpoint path must remain within the bundle")
        path = (root / relative).resolve()
        if root not in path.parents or not path.is_file():
            raise PtlBundleError(f"checkpoint is missing: {role}")
        expected_hash = entry.get("sha256")
        if not isinstance(expected_hash, str) or not _SHA256.fullmatch(expected_hash):
            raise PtlBundleError(f"checkpoint SHA256 is invalid: {role}")
        if _sha256(path) != expected_hash:
            raise PtlBundleError(f"checkpoint SHA256 mismatch: {role}")
        license_id = str(entry.get("license_id", "")).strip()
        if not license_id or license_id == "UNKNOWN":
            raise PtlBundleError(f"checkpoint license is unresolved: {role}")
        checkpoints.append(PtlCheckpoint(role, path, expected_hash, license_id))
    reproduced = payload.get("original_reproduction") is True
    if require_reproduction and not reproduced:
        raise PtlBundleError("PTL author-original reproduction evidence is required")
    graph_contract = payload.get("graph_contract_version")
    if not isinstance(graph_contract, str) or not graph_contract:
        raise PtlBundleError("PTL graph contract version is required")
    return PtlBundle(PTL_REPOSITORY_COMMIT, tuple(checkpoints), graph_contract, reproduced)

