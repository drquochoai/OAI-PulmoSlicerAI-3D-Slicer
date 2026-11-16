"""IN02: single-writer staged artifacts promoted by atomic same-volume rename."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Iterator


class ArtifactStoreError(RuntimeError):
    """Artifact staging, validation, or atomic promotion failed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class AtomicArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve(strict=False)
        self.root.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def stage(self, artifact_id: str) -> Iterator[Path]:
        if not artifact_id or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for char in artifact_id):
            raise ArtifactStoreError("unsafe artifact ID")
        partial = self.root / f".{artifact_id}.partial"
        final = self.root / artifact_id
        if partial.exists() or final.exists():
            raise ArtifactStoreError("artifact already exists or is being written")
        partial.mkdir()
        try:
            yield partial
        except Exception:
            raise
        else:
            files = sorted(path for path in partial.rglob("*") if path.is_file())
            if not files:
                raise ArtifactStoreError("cannot commit an empty artifact")
            manifest = {
                "contract_version": "1.0.0",
                "artifact_id": artifact_id,
                "files": {
                    str(path.relative_to(partial)).replace("\\", "/"): sha256_file(path)
                    for path in files
                },
            }
            manifest_path = partial / "result.manifest.json"
            manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
            with manifest_path.open("r+b") as stream:
                stream.flush()
                os.fsync(stream.fileno())
            partial.replace(final)

    def verify(self, artifact_id: str) -> bool:
        final = self.root / artifact_id
        try:
            manifest = json.loads((final / "result.manifest.json").read_text(encoding="utf-8"))
            return all(sha256_file(final / relative) == digest for relative, digest in manifest["files"].items())
        except (OSError, KeyError, TypeError, json.JSONDecodeError):
            return False

    def quarantine_partial(self, artifact_id: str, quarantine: Path) -> Path | None:
        partial = self.root / f".{artifact_id}.partial"
        if not partial.exists():
            return None
        quarantine.mkdir(parents=True, exist_ok=True)
        target = quarantine / partial.name
        if target.exists():
            raise ArtifactStoreError("quarantine target already exists")
        shutil.move(str(partial), str(target))
        return target

