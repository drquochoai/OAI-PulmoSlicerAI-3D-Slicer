"""Headless Slicer smoke test for the interactive HTML exporter."""

from __future__ import annotations

import json
import traceback
from pathlib import Path
import sys

import slicer
import vtk
import vtkSegmentationCorePython as vtkSegmentationCore


ROOT = Path(__file__).resolve().parents[1]
MODULE_ROOT = ROOT / "slicer_extension" / "PulmoSlicerAI"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(MODULE_ROOT))

from PulmoSlicerAILib.html_export import ExportOptions, InteractiveHtmlExporter


def sphere(center, radius):
    source = vtk.vtkSphereSource()
    source.SetCenter(*center)
    source.SetRadius(radius)
    source.SetThetaResolution(28)
    source.SetPhiResolution(20)
    source.Update()
    output = vtk.vtkPolyData()
    output.DeepCopy(source.GetOutput())
    return output


def add_surface_segment(node, segment_id, name, polydata):
    segment = vtkSegmentationCore.vtkSegment()
    segment.SetName(name)
    representation = vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName()
    segment.AddRepresentation(representation, polydata)
    node.GetSegmentation().AddSegment(segment, segment_id)


def main():
    lobe_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", "Synthetic lobes")
    lobe_node.SetAttribute("PulmoSlicerAI.OutputRole", "lobes")
    add_surface_segment(lobe_node, "lung_upper_lobe_right", "Right upper lobe", sphere((30, 0, 35), 42))
    add_surface_segment(lobe_node, "lung_lower_lobe_left", "Left lower lobe", sphere((-30, 0, -30), 44))

    ptl_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", "Synthetic PTL")
    ptl_node.SetAttribute("PulmoSlicerAI.OutputRole", "ptl")
    add_surface_segment(ptl_node, "PTL_A_R_01", "A1 Right", sphere((20, -10, 35), 8))
    add_surface_segment(ptl_node, "PTL_B_R_01", "B1 Right", sphere((16, -4, 32), 6))
    add_surface_segment(ptl_node, "PTL_V_R_01", "V1 Right", sphere((25, 2, 32), 6))

    destination = ROOT / "build" / "html-export-smoke.html"
    result = InteractiveHtmlExporter().export(
        (lobe_node, ptl_node),
        ExportOptions(destination, profile="quick"),
        progress_callback=lambda message: print(message, flush=True),
    )
    document = destination.read_text(encoding="utf-8")
    assert result.node_count == 5
    assert "A1 Right" in document and "B1 Right" in document and "V1 Right" in document
    assert "<script src=" not in document.lower()
    print(json.dumps({
        "path": str(destination),
        "nodes": result.node_count,
        "triangles": result.triangle_count,
        "bytes": result.byte_count,
        "sha256": result.file_sha256,
        "warnings": list(result.warnings),
    }, ensure_ascii=False), flush=True)


try:
    main()
    slicer.app.exit(0)
except Exception:
    error_path = ROOT / "build" / "html-export-smoke-error.txt"
    error_path.write_text(traceback.format_exc(), encoding="utf-8")
    slicer.app.exit(1)
