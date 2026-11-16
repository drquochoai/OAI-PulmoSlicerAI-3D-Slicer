"""Print the local Slicer subject-hierarchy and TotalSegmentator API surface."""

import json

import qt
import slicer
import vtk
import vtkSegmentationCorePython as vtkSegmentationCore


def run():
    sh_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    module = slicer.app.moduleManager().module("TotalSegmentator")
    segmentation_node = slicer.mrmlScene.AddNewNodeByClass(
        "vtkMRMLSegmentationNode", "Subject hierarchy probe"
    )
    for segment_id in ("PTL_A_R_01", "PTL_B_R_01"):
        segment = vtkSegmentationCore.vtkSegment()
        segment.SetName(segment_id)
        segmentation_node.GetSegmentation().AddSegment(segment, segment_id)
    node_item = sh_node.GetItemByDataNode(segmentation_node)
    children = vtk.vtkIdList()
    sh_node.GetItemChildren(node_item, children, False)
    right_folder = sh_node.CreateFolderItem(sh_node.GetSceneItemID(), "Probe Right")
    original_parent = sh_node.GetItemParent(children.GetId(0)) if children.GetNumberOfIds() else 0
    moved_parent = 0
    moved_data_node_id = ""
    if children.GetNumberOfIds():
        sh_node.SetItemParent(children.GetId(0), right_folder)
        moved_parent = sh_node.GetItemParent(children.GetId(0))
        moved_data_node = sh_node.GetItemDataNode(children.GetId(0))
        moved_data_node_id = moved_data_node.GetID() if moved_data_node else ""
    result = {
        "subject_hierarchy_methods": sorted(
            name
            for name in dir(sh_node)
            if any(token in name for token in ("Folder", "Item", "Parent", "Attribute"))
        ),
        "total_segmentator_path": getattr(module, "path", "") if module else "",
        "total_segmentator_installed": module is not None,
        "segmentation_item_children": children.GetNumberOfIds(),
        "segment_original_parent": original_parent,
        "segment_moved_parent": moved_parent,
        "segment_moved_data_node_id": moved_data_node_id,
        "segmentation_node_id": segmentation_node.GetID(),
        "folder_item": right_folder,
    }
    print("PULMOSLICER_SH_PROBE=" + json.dumps(result, sort_keys=True))
    slicer.app.exit(0)


qt.QTimer.singleShot(1200, run)
