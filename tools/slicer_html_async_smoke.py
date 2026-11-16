"""Verify that HTML export runs in a worker while the Slicer Qt loop remains live."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import traceback

import qt
import slicer
import vtk
import vtkSegmentationCorePython as vtkSegmentationCore


ROOT = Path(__file__).resolve().parents[1]
MODULE_ROOT = ROOT / "slicer_extension" / "PulmoSlicerAI"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(MODULE_ROOT))


def sphere(center, radius, resolution=80):
    source = vtk.vtkSphereSource()
    source.SetCenter(*center)
    source.SetRadius(radius)
    source.SetThetaResolution(resolution)
    source.SetPhiResolution(resolution)
    source.Update()
    output = vtk.vtkPolyData()
    output.DeepCopy(source.GetOutput())
    return output


def add_segment(node, segment_id, polydata):
    segment = vtkSegmentationCore.vtkSegment()
    segment.SetName(segment_id)
    representation = vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName()
    segment.AddRepresentation(representation, polydata)
    node.GetSegmentation().AddSegment(segment, segment_id)


def start():
    from PulmoSlicerAI import PulmoSlicerAIWidget
    from PulmoSlicerAILib.html_export import ExportOptions

    widget = PulmoSlicerAIWidget()
    widget.setup()
    lobes = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", "Async lobes")
    lobes.SetAttribute("PulmoSlicerAI.OutputRole", "lobes")
    add_segment(lobes, "lung_upper_lobe_right", sphere((30, 0, 30), 45))
    add_segment(lobes, "lung_lower_lobe_left", sphere((-30, 0, -30), 45))
    ptl = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", "Async PTL")
    ptl.SetAttribute("PulmoSlicerAI.OutputRole", "ptl")
    add_segment(ptl, "PTL_A_R_01", sphere((15, 0, 25), 8))
    add_segment(ptl, "PTL_B_R_01", sphere((18, 0, 25), 7))
    add_segment(ptl, "PTL_V_R_01", sphere((21, 0, 25), 7))
    widget.lobeSelector.setCurrentNode(lobes)
    widget.ptlSelector.setCurrentNode(ptl)
    widget.treeModeCombo.currentIndex = 5

    destination = ROOT / "build" / "html-async-smoke.html"
    destination.unlink(missing_ok=True)
    ticks = {"count": 0, "progress": [], "started": False}
    monitor = qt.QTimer()
    monitor.setInterval(50)

    def finish(success, error=""):
        monitor.stop()
        report = {
            "passed": success,
            "qt_timer_ticks": ticks["count"],
            "progress_values": sorted(set(ticks["progress"])),
            "output_exists": destination.is_file(),
            "output_bytes": destination.stat().st_size if destination.is_file() else 0,
            "error": error,
        }
        (ROOT / "build" / "html-async-smoke.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        widget.cleanup()
        slicer.app.exit(0 if success else 1)

    def poll():
        ticks["count"] += 1
        ticks["progress"].append(int(widget.progressPanel.progressBar.value))
        if ticks["started"] and widget._htmlExportState is None:
            success = destination.is_file() and ticks["count"] >= 4
            finish(success, "" if success else "worker ended without responsive ticks/output")
        elif ticks["count"] > 1200:
            finish(False, "timeout waiting for asynchronous export")

    monitor.connect("timeout()", poll)
    monitor.start()
    widget._exportInteractiveHtml(
        ExportOptions(destination, profile="standard"), False
    )
    ticks["started"] = True


try:
    qt.QTimer.singleShot(0, start)
except Exception:
    (ROOT / "build" / "html-async-smoke-error.txt").write_text(
        traceback.format_exc(), encoding="utf-8"
    )
    slicer.app.exit(1)
