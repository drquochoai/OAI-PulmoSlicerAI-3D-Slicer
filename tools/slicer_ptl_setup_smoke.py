"""Run the first-use PTL installer in an ignored local test directory."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import qt
import slicer


_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) in sys.path:
    sys.path.remove(str(_ROOT))
sys.path.insert(0, str(_ROOT))
_MODULE = _ROOT / "slicer_extension" / "PulmoSlicerAI"
if str(_MODULE) in sys.path:
    sys.path.remove(str(_MODULE))
sys.path.insert(0, str(_MODULE))
for _name in tuple(sys.modules):
    if _name == "PulmoSlicerAILib" or _name.startswith("PulmoSlicerAILib."):
        del sys.modules[_name]

from PulmoSlicerAILib.ptl_setup import PtlRuntimeSetup


def run() -> None:
    messages = []
    result = {"passed": False, "patient_data_accessed": False}
    try:
        setup = PtlRuntimeSetup(_ROOT / ".tools" / "ptl-setup-smoke")
        status = setup.ensure(messages.append)
        # Keep the public result free of local absolute paths.
        result.update(
            {
                "passed": status.ready,
                "status": status.message,
                "messages": messages,
                "roles_ready": [
                    role for role in ("airway", "artery", "vein")
                    if setup.paths_for(role).checkpoint.is_file()
                ],
            }
        )
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
    print("PULMOSLICER_PTL_SETUP_SMOKE=" + json.dumps(result, sort_keys=True))
    slicer.app.exit(0 if result["passed"] else 1)


qt.QTimer.singleShot(1500, run)
