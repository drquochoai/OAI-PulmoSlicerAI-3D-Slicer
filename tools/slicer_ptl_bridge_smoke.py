"""Exercise the PTL-to-MRML bridge in a headless Slicer scene.

No network, checkpoint, or patient data is used.  A deterministic fake PTL
predictor verifies segment IDs, voxel transfer, role mapping, and 3-D display.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys

import numpy as np
import qt
import slicer
import vtkSegmentationCorePython as vtkSegmentationCore

# Source-tree smoke runs before packaging, so make the engine import explicit.
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from PulmoSlicerAILib.workflow import PulmonarySegmentationWorkflow
from pulmoslicer_engine.adapters.labeling.ptl_inference import PtlPrediction


@dataclass(frozen=True)
class _Ready:
    ready: bool = True
    message: str = "synthetic PTL runtime"


class _FakeSetup:
    def ensure(self, callback=None):
        if callback:
            callback("PTL bridge smoke: fake runtime ready")
        return _Ready()

    def paths_for(self, role):
        return role


def _fake_predictor(mask, role, runtime, progress_callback=None):
    del runtime
    labels = np.zeros(mask.shape, dtype=np.uint8)
    foreground = np.argwhere(mask)
    labels[tuple(foreground[0])] = 1
    labels[tuple(foreground[-1])] = 19
    if progress_callback:
        progress_callback(f"PTL bridge smoke: {role}")
    return PtlPrediction(role, labels, 4, 3, len(foreground), ())


def _add_source_segment(node, segment_id, mask, reference):
    segment = vtkSegmentationCore.vtkSegment()
    segment.SetName(segment_id)
    node.GetSegmentation().AddSegment(segment, segment_id)
    slicer.util.updateSegmentBinaryLabelmapFromArray(
        mask.astype(np.uint8), node, segment_id, reference
    )


def _find_tree_item(parent, text):
    for index in range(parent.childCount()):
        child = parent.child(index)
        if child.text(0) == text:
            return child
        nested = _find_tree_item(child, text)
        if nested is not None:
            return nested
    return None


def _sh_child(sh_node, parent, name):
    return sh_node.GetItemChildWithName(parent, name)


def run() -> None:
    result = {"passed": False, "patient_data_accessed": False}
    try:
        volume = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLScalarVolumeNode", "Synthetic PTL CT"
        )
        slicer.util.updateVolumeFromArray(volume, np.zeros((8, 8, 8), dtype=np.int16))
        source = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLSegmentationNode", "Synthetic A-V-B"
        )
        source.SetReferenceImageGeometryParameterFromVolumeNode(volume)
        mask = np.zeros((8, 8, 8), dtype=np.uint8)
        mask[2:6, 2:6, 2:6] = 1
        for segment_id in PulmonarySegmentationWorkflow.VESSEL_SEGMENTS:
            _add_source_segment(source, segment_id, mask, volume)

        output = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLSegmentationNode", "Synthetic PTL output"
        )
        workflow = PulmonarySegmentationWorkflow(
            ptl_setup_factory=_FakeSetup,
            ptl_predictor=_fake_predictor,
        )
        messages = []
        names = workflow.run_ptl_labels(volume, source, output, messages.append)
        display_message = workflow.show_3d([output])
        smooth_display_message = workflow.show_3d([output], "balanced")
        smooth_regeneration_ready = (
            output.GetAttribute("PulmoSlicerAI.SurfaceProfile") == "balanced"
            and output.GetSegmentation().ContainsRepresentation("Closed surface")
        )
        ids = {
            output.GetSegmentation().GetNthSegmentID(index)
            for index in range(output.GetSegmentation().GetNumberOfSegments())
        }
        expected_ids = {
            "PTL_B_R_01",
            "PTL_B_C_19",
            "PTL_A_R_01",
            "PTL_A_C_19",
            "PTL_V_R_01",
            "PTL_V_C_19",
        }
        artery_only = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLSegmentationNode", "Synthetic PTL artery only"
        )
        artery_names = workflow.run_ptl_labels(
            volume, source, artery_only, messages.append, roles=("artery",)
        )
        artery_ids = {
            artery_only.GetSegmentation().GetNthSegmentID(index)
            for index in range(artery_only.GetSegmentation().GetNumberOfSegments())
        }

        module = slicer.app.moduleManager().module("PulmoSlicerAI")
        widget = module.widgetRepresentation().self()
        lobes = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLSegmentationNode", "Synthetic lobes"
        )
        lobes.SetReferenceImageGeometryParameterFromVolumeNode(volume)
        for segment_id in workflow.LOBE_SEGMENTS:
            _add_source_segment(lobes, segment_id, mask, volume)
        widget.vesselSelector.setCurrentNode(source)
        widget.lobeSelector.setCurrentNode(lobes)
        widget.ptlSelector.setCurrentNode(artery_only)
        widget._organizeOutputs()
        widget._refreshAnatomyTree()
        artery_item = _find_tree_item(widget.anatomyTree.invisibleRootItem(), "A1 Right")
        hierarchy_ready = all(
            _find_tree_item(widget.anatomyTree.invisibleRootItem(), label) is not None
            for label in ("Right", "Upper", "A — Động mạch", "S1", "A1 Right")
        )
        visibility_toggle_ready = False
        if artery_item is not None:
            artery_item.setCheckState(0, qt.Qt.Unchecked)
            display = artery_only.GetDisplayNode()
            visibility_toggle_ready = bool(display) and not bool(
                display.GetSegmentVisibility("PTL_A_R_01")
            )
        sh_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(
            slicer.mrmlScene
        )
        sh_root = _sh_child(sh_node, sh_node.GetSceneItemID(), "PulmoSlicer AI Results")
        sh_right = _sh_child(sh_node, sh_root, "Right")
        sh_upper = _sh_child(sh_node, sh_right, "Upper")
        sh_a = _sh_child(sh_node, sh_upper, "A")
        sh_lung = _sh_child(sh_node, sh_upper, "Lung")
        subject_hierarchy_ready = bool(
            sh_a
            and sh_lung
            and _sh_child(sh_node, sh_a, "A1 Right")
            and _sh_child(sh_node, sh_lung, "lung_upper_lobe_right")
        )
        result.update(
            {
                "passed": (
                    ids == expected_ids
                    and len(names) == 6
                    and artery_ids == {"PTL_A_R_01", "PTL_A_C_19"}
                    and len(artery_names) == 2
                    and hierarchy_ready
                    and visibility_toggle_ready
                    and smooth_regeneration_ready
                    and subject_hierarchy_ready
                ),
                "segment_ids": sorted(ids),
                "artery_only_ids": sorted(artery_ids),
                "created_names": list(names),
                "progress_messages": messages,
                "display_message": display_message,
                "smooth_display_message": smooth_display_message,
                "smooth_regeneration_ready": smooth_regeneration_ready,
                "hierarchy_ready": hierarchy_ready,
                "visibility_toggle_ready": visibility_toggle_ready,
                "subject_hierarchy_ready": subject_hierarchy_ready,
            }
        )
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
    print("PULMOSLICER_PTL_BRIDGE_SMOKE=" + json.dumps(result, sort_keys=True))
    slicer.mrmlScene.Clear(0)
    slicer.app.exit(0 if result["passed"] else 1)


qt.QTimer.singleShot(1500, run)
