"""Headless construction smoke test for the PulmoSlicer HTML export UI."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import traceback

import slicer


ROOT = Path(__file__).resolve().parents[1]
MODULE_ROOT = ROOT / "slicer_extension" / "PulmoSlicerAI"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(MODULE_ROOT))


def main():
    from PulmoSlicerAI import PulmoSlicerAIWidget

    widget = PulmoSlicerAIWidget()
    widget.setup()
    assert widget.htmlExportPanel.exportButton.text == "Xuất một file HTML 3D all-in-one"
    assert widget.htmlExportPanel.allStructures.checked
    assert not widget.htmlExportPanel.allStructures.enabled
    assert widget.contextModeCombo.count == 5
    assert widget.contextModeCombo.itemData(0) == "none"
    assert not widget.htmlExportPanel.cancelButton.enabled
    report = {
        "html_export_button": widget.htmlExportPanel.exportButton.text,
        "default_all_structures": bool(widget.htmlExportPanel.allStructures.checked),
        "default_profile": str(widget.htmlExportPanel.qualityCombo.currentData),
        "default_color_template": str(widget.htmlExportPanel.colorCombo.currentData),
        "context_modes": widget.contextModeCombo.count,
        "cancel_button": widget.htmlExportPanel.cancelButton.text,
    }
    (ROOT / "build" / "html-ui-smoke.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    widget.cleanup()


try:
    main()
    slicer.app.exit(0)
except Exception:
    (ROOT / "build" / "html-ui-smoke-error.txt").write_text(
        traceback.format_exc(), encoding="utf-8"
    )
    slicer.app.exit(1)
