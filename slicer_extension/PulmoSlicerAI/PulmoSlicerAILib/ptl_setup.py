"""Install and verify the external research PTL runtime on first use."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

from pulmoslicer_engine.adapters.labeling.ptl_checkpoint_probe import probe_ptl_bundle
from pulmoslicer_engine.adapters.labeling.ptl_inference import PtlRuntimePaths


PTL_COMMIT = "27fdace577293a29480bce4f00efba7501cadd20"
PTL_SOURCE_URL = (
    "https://github.com/HINTLab/pulmonary-tree-labeling/archive/"
    + PTL_COMMIT
    + ".zip"
)
PTL_SOURCE_SHA256 = "3081003d761687c6dc7f63f3632d03f435bdec568195a56a0ed9bef1450ea37e"
CHECKPOINTS = {
    "airway": (
        "1wL8UuVHZmwT9CLXdzIGf4fTfAL7-8RaU",
        "728b45ab71f84975231e98f062934e2dfe2ec966d65eef5874161d9bae222a4c",
    ),
    "artery": (
        "1PqBnxJKVpuSyW8a-K_h6I6YIqq9VOak0",
        "95c0f0fdba2bfd9157b8b7abbe5495720c4695b4171ed1964a6360c5c09ccc59",
    ),
    "vein": (
        "1KuVUO1XmGZ0eHAiF19_f34urUfZW_SOs",
        "18248cef574421289744efb595de0391d1b4bc186320c85eae150aef665310a6",
    ),
}


@dataclass(frozen=True)
class PtlSetupStatus:
    ready: bool
    message: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class PtlRuntimeSetup:
    def __init__(self, root: Path | None = None) -> None:
        local = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
        self.root = Path(root) if root else Path(local) / "PulmoSlicerAI" / "ptl-v1"
        self.site_packages = self.root / "site-packages"
        self.source = self.root / f"pulmonary-tree-labeling-{PTL_COMMIT}"
        self.checkpoint_root = self.root / "checkpoints"
        self.manifest = self.root / "ptl-bundle.json"

    def status(self) -> PtlSetupStatus:
        try:
            probe_ptl_bundle(self.manifest)
            if not (self.source / "model" / "pg_model.py").is_file():
                return PtlSetupStatus(False, "PTL source is missing")
            if not (self.site_packages / "torch_geometric").is_dir():
                return PtlSetupStatus(False, "torch-geometric is missing")
        except Exception as exc:
            return PtlSetupStatus(False, str(exc))
        return PtlSetupStatus(True, "PTL airway/artery/vein runtime is verified")

    @staticmethod
    def _notify(callback, message: str) -> None:
        if callback:
            callback(message)

    def _install_python_runtime(self, callback) -> None:
        if (self.site_packages / "torch_geometric").is_dir() and (
            self.site_packages / "gdown"
        ).is_dir():
            return
        self._notify(callback, "PTL setup: installing torch-geometric and downloader")
        import slicer

        python = Path(slicer.app.slicerHome) / "bin" / "PythonSlicer.exe"
        command = [
            str(python),
            "-m",
            "pip",
            "install",
            "--target",
            str(self.site_packages),
            "torch-geometric==2.6.1",
            "gdown==6.5.1",
        ]
        flags = 0x08000000 if sys.platform == "win32" else 0
        subprocess.check_call(command, creationflags=flags)

    def _download_source(self, callback) -> None:
        archive = self.root / "ptl-source.zip"
        source_ready = (self.source / "model" / "pg_model.py").is_file()
        archive_ready = archive.is_file() and _sha256(archive) == PTL_SOURCE_SHA256
        if source_ready and archive_ready:
            return
        self._notify(callback, "PTL setup: downloading pinned author source")
        partial = archive.with_suffix(".partial")
        with urllib.request.urlopen(PTL_SOURCE_URL, timeout=120) as response:
            with partial.open("wb") as output:
                shutil.copyfileobj(response, output, 1024 * 1024)
        if _sha256(partial) != PTL_SOURCE_SHA256:
            raise RuntimeError("PTL source archive SHA256 mismatch")
        partial.replace(archive)
        if source_ready:
            return
        with zipfile.ZipFile(archive) as bundle:
            members = bundle.namelist()
            root = self.root.resolve()
            for member in members:
                destination = (self.root / member).resolve()
                if destination != root and root not in destination.parents:
                    raise RuntimeError("unsafe path in PTL source archive")
            top = members[0].split("/")[0]
            bundle.extractall(self.root)
        extracted = self.root / top
        if extracted != self.source:
            if self.source.exists():
                shutil.rmtree(self.source)
            extracted.replace(self.source)
        if not (self.source / "model" / "pg_model.py").is_file():
            raise RuntimeError("downloaded PTL source archive is incomplete")

    def _download_checkpoints(self, callback) -> None:
        if str(self.site_packages) not in sys.path:
            sys.path.append(str(self.site_packages))
        import gdown

        for role, (file_id, expected_hash) in CHECKPOINTS.items():
            target = self.checkpoint_root / role / "Implicit_Point_Graph_Network"
            if target.is_file() and _sha256(target) == expected_hash:
                continue
            self._notify(callback, f"PTL setup: downloading verified {role} checkpoint")
            target.parent.mkdir(parents=True, exist_ok=True)
            partial = target.with_suffix(".partial")
            gdown.download(
                id=file_id,
                output=str(partial),
                quiet=True,
                use_cookies=False,
                resume=True,
            )
            if not partial.is_file() or _sha256(partial) != expected_hash:
                raise RuntimeError(f"PTL {role} checkpoint SHA256 mismatch")
            partial.replace(target)

    def _write_manifest(self) -> None:
        checkpoints = {}
        for role, (file_id, expected_hash) in CHECKPOINTS.items():
            relative = Path("checkpoints") / role / "Implicit_Point_Graph_Network"
            checkpoints[role] = {
                "file": relative.as_posix(),
                "sha256": expected_hash,
                "license_id": "UPSTREAM-CHECKPOINT-LICENSE-NOT-STATED",
                "source_file_id": file_id,
                "redistributable": False,
            }
        payload = {
            "repository_commit": PTL_COMMIT,
            "source_url": PTL_SOURCE_URL,
            "source_archive_sha256": PTL_SOURCE_SHA256,
            "checkpoints": checkpoints,
            "original_reproduction": True,
            "graph_contract_version": "native-reduced-graph-v1",
            "research_only": True,
        }
        temporary = self.manifest.with_suffix(".partial")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary.replace(self.manifest)

    def ensure(self, callback=None) -> PtlSetupStatus:
        self.root.mkdir(parents=True, exist_ok=True)
        self.site_packages.mkdir(parents=True, exist_ok=True)
        self._install_python_runtime(callback)
        self._download_source(callback)
        self._download_checkpoints(callback)
        self._write_manifest()
        status = self.status()
        if not status.ready:
            raise RuntimeError(status.message)
        self._notify(callback, "PTL setup: all three checkpoints verified")
        return status

    def paths_for(self, role: str) -> PtlRuntimePaths:
        status = self.status()
        if not status.ready:
            raise RuntimeError(status.message)
        if role not in CHECKPOINTS:
            raise ValueError(f"unsupported PTL role: {role}")
        return PtlRuntimePaths(
            self.source,
            self.site_packages,
            self.checkpoint_root / role / "Implicit_Point_Graph_Network",
        )
