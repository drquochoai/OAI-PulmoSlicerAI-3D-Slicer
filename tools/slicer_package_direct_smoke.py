"""Load the newest staged ZIP content directly, avoiding an older installed module."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import traceback

import slicer


ROOT = Path(__file__).resolve().parents[1]


def main():
    candidates = list(
        (ROOT / "build" / "slicer-package-staging").glob(
            "PulmoSlicerAI-*/lib/Slicer-5.12/qt-scripted-modules"
        )
    )
    if not candidates:
        raise RuntimeError("No staged PulmoSlicerAI package was found")
    module_root = max(candidates, key=lambda path: path.stat().st_mtime)
    sys.path.insert(0, str(module_root))
    from PulmoSlicerAI import PulmoSlicerAIWidget
    from PulmoSlicerAILib.html_export.html_writer import DISCLAIMER

    widget = PulmoSlicerAIWidget()
    widget.setup()
    asset_root = module_root / "PulmoSlicerAILib" / "html_export" / "assets"
    report = {
        "passed": all(
            (
                widget.htmlExportPanel.allStructures.checked,
                str(widget.htmlExportPanel.qualityCombo.currentData) == "standard",
                str(widget.htmlExportPanel.colorCombo.currentData)
                == "pulmoslicer-surgical-contrast-v1",
                widget.contextModeCombo.count == 5,
                not widget.htmlExportPanel.cancelButton.enabled,
                (asset_root / "viewer_bundle.js").is_file(),
                (asset_root / "viewer.css").is_file(),
                bool(DISCLAIMER),
            )
        ),
        "module_root": str(module_root),
        "viewer_bundle_bytes": (asset_root / "viewer_bundle.js").stat().st_size,
        "default_all_valid": bool(widget.htmlExportPanel.allStructures.checked),
        "default_profile": str(widget.htmlExportPanel.qualityCombo.currentData),
        "default_color_template": str(widget.htmlExportPanel.colorCombo.currentData),
        "context_modes": widget.contextModeCombo.count,
        "cancel_button": widget.htmlExportPanel.cancelButton.text,
    }
    (ROOT / "build" / "package-direct-smoke.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    widget.cleanup()
    slicer.app.exit(0 if report["passed"] else 1)


try:
    main()
except Exception:
    (ROOT / "build" / "package-direct-smoke-error.txt").write_text(
        traceback.format_exc(), encoding="utf-8"
    )
    slicer.app.exit(1)
