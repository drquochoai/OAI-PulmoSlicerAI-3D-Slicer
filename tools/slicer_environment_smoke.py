"""Headless Slicer preflight; contains no patient data and performs no inference."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import qt
import slicer


REQUIRED_MODULES = ("DICOM", "SegmentEditor", "TotalSegmentator")
RECOMMENDED_CAPABILITIES = {
    "SlicerVMTK": "ExtractCenterline",
    "SegmentEditorExtraEffects": "SegmentEditorDrawTube",
    "MarkupsToModel": "MarkupsToModel",
}


def _module_available(name: str) -> bool:
    return slicer.app.moduleManager().module(name) is not None


def run() -> int:
    app_version = str(slicer.app.applicationVersion)
    source_revision = str(slicer.app.repositoryRevision)
    results = {
        "slicer_version": app_version,
        "expected_slicer_build_revision": "34645",
        "slicer_source_revision": source_revision,
        "python_version": sys.version.split()[0],
        "required_modules": {name: _module_available(name) for name in REQUIRED_MODULES},
        "recommended_extensions": {
            extension: _module_available(capability)
            for extension, capability in RECOMMENDED_CAPABILITIES.items()
        },
        "pulmoslicer_module": _module_available("PulmoSlicerAI"),
        "patient_data_accessed": False,
    }
    compatible = (
        app_version == "5.12.4"
        and source_revision.startswith("4e21c19")
    )
    required_ok = all(results["required_modules"].values())
    results["compatible"] = compatible
    results["passed"] = compatible and required_ok and results["pulmoslicer_module"]
    output_path = os.environ.get("PULMOSLICER_SMOKE_OUTPUT")
    encoded = json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True)
    print("PULMOSLICER_SMOKE_RESULT=" + json.dumps(results, sort_keys=True), flush=True)
    if output_path:
        Path(output_path).write_text(encoded + "\n", encoding="utf-8")
    return 0 if results["passed"] else 2


def finish() -> None:
    slicer.app.exit(run())


# --python-script runs during startup. Delay until extension modules are registered.
qt.QTimer.singleShot(1500, finish)

