"""Headless smoke test for a packaged PulmoSlicer AI module path."""

import json
from pathlib import Path

import qt
import slicer
import vtkSegmentationCorePython as vtkSegmentationCore


def run() -> None:
    module = slicer.app.moduleManager().module("PulmoSlicerAI")
    total_segmentator = slicer.app.moduleManager().module("TotalSegmentator")
    module_title = module.title if module is not None else ""
    module_categories = list(module.categories) if module is not None else []
    widget_ready = False
    ptl_status = ""
    backend_status = ""
    tooltips_ready = False
    rolling_progress_ready = False
    mode_note_ready = False
    performance_controls_ready = False
    output_role_isolation_ready = False
    html_export_ready = False
    error = ""
    if module is not None:
        try:
            widget = module.widgetRepresentation().self()
            widget_ready = all(
                hasattr(widget, name)
                for name in (
                    "inputSelector",
                    "vesselSelector",
                    "lobeSelector",
                    "ptlSelector",
                    "contextSelector",
                    "ptlButton",
                    "treeModeCombo",
                    "anatomyTree",
                    "backendCombo",
                    "backendStatusLabel",
                    "surfaceCombo",
                    "workflow",
                    "progressPanel",
                    "threadCombo",
                    "branchGateLabel",
                    "modeExplanationLabel",
                    "runAllButton",
                    "vesselButton",
                    "lobeButton",
                    "showButton",
                    "slicePolicyCombo",
                    "resourcePolicyCombo",
                    "resampleWorkersCombo",
                    "savingWorkersCombo",
                    "performancePlanLabel",
                    "contextModeCombo",
                    "contextButton",
                    "htmlExportPanel",
                )
            )
            ptl_status = widget.workflow.ptl_status()
            backend_status = widget.backendStatusLabel.text
            tooltips_ready = all(
                bool(control.toolTip)
                for control in (
                    widget.inputSelector,
                    widget.treeModeCombo,
                    widget.runAllButton,
                    widget.vesselButton,
                    widget.lobeButton,
                    widget.showButton,
                    widget.ptlButton,
                    widget.contextButton,
                    widget.htmlExportPanel.exportButton,
                )
            )
            mode_note_ready = "TotalSegmentator" in widget.modeExplanationLabel.text
            performance_controls_ready = (
                int(widget.slicePolicyCombo.currentData) == 1
                and "stride 1" in widget.performancePlanLabel.text
                and int(widget._threadCount()) > 0
                and int(widget._resampleWorkers()) > 0
                and int(widget._savingWorkers()) > 0
            )
            shared = slicer.mrmlScene.AddNewNodeByClass(
                "vtkMRMLSegmentationNode", "Shared selector regression fixture"
            )
            for segment_id in widget.workflow.LOBE_SEGMENTS:
                segment = vtkSegmentationCore.vtkSegment()
                segment.SetName(segment_id)
                shared.GetSegmentation().AddSegment(segment, segment_id)
            widget.vesselSelector.setCurrentNode(shared)
            widget.lobeSelector.setCurrentNode(shared)
            widget.ptlSelector.setCurrentNode(shared)
            source_output = widget._output(
                widget.vesselSelector, "PulmoSlicer A-V-B smoke", "source"
            )
            lobe_output = widget._output(
                widget.lobeSelector, "PulmoSlicer Lobes smoke", "lobes"
            )
            ptl_output = widget._output(
                widget.ptlSelector, "PulmoSlicer PTL smoke", "ptl"
            )
            output_role_isolation_ready = (
                lobe_output.GetID() == shared.GetID()
                and len({source_output.GetID(), lobe_output.GetID(), ptl_output.GetID()}) == 3
                and source_output.GetAttribute(widget.OUTPUT_ROLE_ATTRIBUTE) == "source"
                and lobe_output.GetAttribute(widget.OUTPUT_ROLE_ATTRIBUTE) == "lobes"
                and ptl_output.GetAttribute(widget.OUTPUT_ROLE_ATTRIBUTE) == "ptl"
            )
            html_export_ready = (
                widget.htmlExportPanel.allStructures.checked
                and not widget.htmlExportPanel.allStructures.enabled
                and str(widget.htmlExportPanel.qualityCombo.currentData) == "standard"
                and str(widget.htmlExportPanel.colorCombo.currentData)
                == "pulmoslicer-surgical-contrast-v1"
                and widget.contextModeCombo.count == 5
            )
            widget.progressPanel.begin(
                "lung_vessels",
                {"patient_data_recorded": False, "smoke": True},
                log_root=Path(__file__).resolve().parents[1] / "build" / "smoke-logs",
            )
            widget.progressPanel.set_subtask("TotalSegmentator — A/V/B nguồn")
            for percent in (50, 62, 75, 88, 100):
                widget.progressPanel.on_message(
                    f" {percent}%|#### | {percent}/100 [00:01<00:01]"
                )
            visible_log = widget.progressPanel.logView.toPlainText()
            rolling_progress_ready = (
                visible_log.count("Tiến độ tác vụ con") == 1
                and "100%" in visible_log
                and "88%" not in visible_log
            )
            widget.progressPanel.finish(True, "Smoke progress complete")
        except Exception as exc:
            error = type(exc).__name__ + ": " + str(exc)
    result = {
        "passed": (
            module is not None
            and total_segmentator is not None
            and widget_ready
            and tooltips_ready
            and rolling_progress_ready
            and mode_note_ready
            and performance_controls_ready
            and output_role_isolation_ready
            and html_export_ready
            and module_title == "PulmoSlicer AI for segmentectomy"
            and "Chest by bsquochoainew" in module_categories
        ),
        "module": module is not None,
        "module_title": module_title,
        "module_categories": module_categories,
        "total_segmentator": total_segmentator is not None,
        "widget_ready": widget_ready,
        "ptl_status": ptl_status,
        "backend_status": backend_status,
        "tooltips_ready": tooltips_ready,
        "rolling_progress_ready": rolling_progress_ready,
        "mode_note_ready": mode_note_ready,
        "performance_controls_ready": performance_controls_ready,
        "output_role_isolation_ready": output_role_isolation_ready,
        "html_export_ready": locals().get("html_export_ready", False),
        "error": error,
        "slicer_version": slicer.app.applicationVersion,
        "slicer_revision": slicer.app.repositoryRevision,
        "patient_data_accessed": False,
    }
    report_path = Path(__file__).resolve().parents[1] / "build" / "package-smoke.json"
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PULMOSLICER_PACKAGE_SMOKE=" + json.dumps(result, sort_keys=True))
    slicer.app.exit(0 if result["passed"] else 1)


qt.QTimer.singleShot(1200, run)
