"""Small Slicer bridge for TotalSegmentator pulmonary outputs."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import os


class PulmonarySegmentationWorkflow:
    VESSEL_SEGMENTS = ("lung_airways", "lung_arteries", "lung_veins")
    LOBE_SEGMENTS = (
        "lung_upper_lobe_left",
        "lung_lower_lobe_left",
        "lung_upper_lobe_right",
        "lung_middle_lobe_right",
        "lung_lower_lobe_right",
    )
    AORTA_SEGMENTS = ("aorta",)
    ARCH_BRANCH_SEGMENTS = (
        "brachiocephalic_trunk",
        "common_carotid_artery_right",
        "common_carotid_artery_left",
        "subclavian_artery_right",
        "subclavian_artery_left",
    )
    CHEST_WALL_SEGMENTS = (
        *(f"rib_right_{index}" for index in range(1, 13)),
        *(f"rib_left_{index}" for index in range(1, 13)),
        "sternum",
        *(f"vertebrae_T{index}" for index in range(1, 13)),
    )

    PTL_SOURCE_SEGMENTS = {
        "airway": "lung_airways",
        "artery": "lung_arteries",
        "vein": "lung_veins",
    }

    SURFACE_PROFILES = {
        "preview": ("0.0", "0.0"),
        "balanced": ("0.1", "0.25"),
        "detailed": ("0.5", "0.0"),
    }

    def __init__(
        self,
        logic_factory: Callable | None = None,
        ptl_setup_factory: Callable | None = None,
        ptl_predictor: Callable | None = None,
        backend_probe_factory: Callable | None = None,
    ) -> None:
        self._logic_factory = logic_factory
        self._ptl_setup_factory = ptl_setup_factory
        self._ptl_predictor = ptl_predictor
        self._backend_probe_factory = backend_probe_factory

    @staticmethod
    def _module_available(name: str) -> bool:
        import slicer

        return slicer.app.moduleManager().module(name) is not None

    def environment_status(self) -> str:
        required = ("DICOM", "SegmentEditor", "TotalSegmentator")
        missing = [name for name in required if not self._module_available(name)]
        if missing:
            return "Thiếu thành phần bắt buộc: " + ", ".join(missing)
        decision = self.resolve_backend("auto")
        return "Sẵn sàng: DICOM, Segment Editor và TotalSegmentator. " + decision.message

    def resolve_backend(self, preference="auto"):
        from pulmoslicer_engine.infrastructure.compute_backend import (
            probe_torch_backend,
            select_backend,
        )

        if self._backend_probe_factory is not None:
            probe = self._backend_probe_factory()
        else:
            import torch

            probe = probe_torch_backend(torch)
        return select_backend(probe, preference)

    def _logic(self):
        if self._logic_factory is not None:
            return self._logic_factory()
        from TotalSegmentator import TotalSegmentatorLogic

        return TotalSegmentatorLogic()

    @staticmethod
    def _worker_command(command, wrapper_path, resample_workers, saving_workers):
        command = list(command)
        if len(command) < 2 or "TotalSegmentator" not in os.path.basename(command[1]):
            return command
        command[1] = wrapper_path
        command.extend(["--nr_thr_resamp", str(resample_workers)])
        command.extend(["--nr_thr_saving", str(saving_workers)])
        return command

    def _process(
        self,
        progress_callback=None,
        thread_count=None,
        resample_workers=1,
        saving_workers=6,
        **kwargs,
    ) -> None:
        logic = self._logic()
        logic.logCallback = progress_callback
        variables = (
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "PULMOSLICER_CPU_THREADS",
        )
        previous = {name: os.environ.get(name) for name in variables}
        original_launcher = None
        try:
            if thread_count is not None:
                for name in variables:
                    os.environ[name] = str(thread_count)
            if self._logic_factory is None:
                import slicer

                original_launcher = slicer.util.launchConsoleProcess
                wrapper_path = os.path.join(os.path.dirname(__file__), "totalseg_worker.py")

                def launch_with_performance(command, *args, **launch_kwargs):
                    tuned = self._worker_command(
                        command, wrapper_path, resample_workers, saving_workers
                    )
                    return original_launcher(tuned, *args, **launch_kwargs)

                slicer.util.launchConsoleProcess = launch_with_performance
            logic.process(**kwargs)
        finally:
            if original_launcher is not None:
                import slicer

                slicer.util.launchConsoleProcess = original_launcher
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

    @staticmethod
    def _validate_nodes(input_volume, output_segmentation) -> None:
        if input_volume is None:
            raise ValueError("CT input volume is required")
        if output_segmentation is None:
            raise ValueError("Output segmentation node is required")

    @staticmethod
    def _segment_ids(output_segmentation) -> set[str]:
        segmentation = output_segmentation.GetSegmentation()
        segment_ids: set[str] = set()
        for index in range(segmentation.GetNumberOfSegments()):
            segment_ids.add(segmentation.GetNthSegmentID(index))
        return segment_ids

    @classmethod
    def verify_segments(cls, output_segmentation, expected: Iterable[str]) -> tuple[str, ...]:
        # TotalSegmentator may localize display names, but keeps stable class names as segment IDs.
        actual = cls._segment_ids(output_segmentation)
        expected_tuple = tuple(expected)
        missing = sorted(set(expected_tuple) - actual)
        if missing:
            raise RuntimeError("TotalSegmentator output thiếu segment: " + ", ".join(missing))
        return expected_tuple

    def run_vessels(
        self,
        input_volume,
        output_segmentation,
        quality="normal",
        cpu=False,
        progress_callback=None,
        thread_count=None,
        resample_workers=1,
        saving_workers=6,
    ):
        self._validate_nodes(input_volume, output_segmentation)
        if quality != "normal":
            raise ValueError(
                "TotalSegmentator 2.14 lung_vessels chỉ hỗ trợ normal; Fast trước đây bị bỏ qua."
            )
        self._process(
            inputVolume=input_volume,
            outputSegmentation=output_segmentation,
            quality=quality,
            cpu=cpu,
            task="lung_vessels",
            # All quality/backend choices are made in PulmoSlicer before the run.
            # Never pause an unattended run with TotalSegmentator's Fast dialog.
            interactive=False,
            progress_callback=progress_callback,
            thread_count=thread_count,
            resample_workers=resample_workers,
            saving_workers=saving_workers,
        )
        return self.verify_segments(output_segmentation, self.VESSEL_SEGMENTS)

    def run_lobes(
        self,
        input_volume,
        output_segmentation,
        quality="normal",
        cpu=False,
        progress_callback=None,
        thread_count=None,
        resample_workers=1,
        saving_workers=6,
    ):
        self._validate_nodes(input_volume, output_segmentation)
        self._process(
            inputVolume=input_volume,
            outputSegmentation=output_segmentation,
            quality=quality,
            cpu=cpu,
            task="total",
            subset=list(self.LOBE_SEGMENTS),
            interactive=False,
            progress_callback=progress_callback,
            thread_count=thread_count,
            resample_workers=resample_workers,
            saving_workers=saving_workers,
        )
        return self.verify_segments(output_segmentation, self.LOBE_SEGMENTS)

    @classmethod
    def context_segments(cls, mode: str) -> tuple[str, ...]:
        choices = {
            "aorta": cls.AORTA_SEGMENTS,
            "aorta_branches": cls.AORTA_SEGMENTS + cls.ARCH_BRANCH_SEGMENTS,
            "chest_wall": cls.CHEST_WALL_SEGMENTS,
            "all": cls.AORTA_SEGMENTS + cls.ARCH_BRANCH_SEGMENTS + cls.CHEST_WALL_SEGMENTS,
        }
        if mode not in choices:
            raise ValueError(f"Unsupported thoracic context mode: {mode}")
        return choices[mode]

    def run_thoracic_context(
        self,
        input_volume,
        output_segmentation,
        mode,
        quality="normal",
        cpu=False,
        progress_callback=None,
        thread_count=None,
        resample_workers=1,
        saving_workers=6,
    ):
        self._validate_nodes(input_volume, output_segmentation)
        expected = self.context_segments(mode)
        self._process(
            inputVolume=input_volume,
            outputSegmentation=output_segmentation,
            quality=quality,
            cpu=cpu,
            task="total",
            subset=list(expected),
            interactive=False,
            progress_callback=progress_callback,
            thread_count=thread_count,
            resample_workers=resample_workers,
            saving_workers=saving_workers,
        )
        return self.verify_segments(output_segmentation, expected)

    def _ptl_setup(self):
        if self._ptl_setup_factory is not None:
            return self._ptl_setup_factory()
        from .ptl_setup import PtlRuntimeSetup

        return PtlRuntimeSetup()

    def ptl_status(self) -> str:
        status = self._ptl_setup().status()
        return status.message

    def setup_ptl(self, progress_callback=None) -> str:
        status = self._ptl_setup().ensure(progress_callback)
        return status.message

    @staticmethod
    def _ptl_color(role: str, class_id: int):
        strength = 0.62 + (class_id % 5) * 0.07
        if role == "airway":
            return (strength, 0.48, 0.12)
        if role == "artery":
            return (strength, 0.12, 0.12)
        return (0.12, 0.32, strength)

    def run_ptl_labels(
        self,
        input_volume,
        vessel_segmentation,
        output_segmentation,
        progress_callback=None,
        roles=None,
    ):
        self._validate_nodes(input_volume, vessel_segmentation)
        if output_segmentation is None:
            raise ValueError("PTL output segmentation node is required")
        self.verify_segments(vessel_segmentation, self.VESSEL_SEGMENTS)
        setup = self._ptl_setup()
        setup.ensure(progress_callback)

        import numpy as np
        import slicer
        import vtkSegmentationCorePython as vtkSegmentationCore

        from pulmoslicer_engine.adapters.labeling.ptl_inference import predict_ptl
        from pulmoslicer_engine.adapters.labeling.ptl_labels import (
            ptl_class_labels,
            ptl_region_metadata,
            ptl_segment_id,
        )

        predictor = self._ptl_predictor or predict_ptl
        selected_roles = tuple(self.PTL_SOURCE_SEGMENTS if roles is None else roles)
        invalid_roles = sorted(set(selected_roles) - set(self.PTL_SOURCE_SEGMENTS))
        if invalid_roles or not selected_roles:
            raise ValueError("PTL roles must contain airway, artery, and/or vein")
        segmentation = output_segmentation.GetSegmentation()
        segmentation.RemoveAllSegments()
        output_segmentation.SetReferenceImageGeometryParameterFromVolumeNode(input_volume)
        created = []
        for role in selected_roles:
            source_segment_id = self.PTL_SOURCE_SEGMENTS[role]
            if progress_callback:
                progress_callback(f"PTL {role}: exporting TotalSegmentator mask")
            mask = slicer.util.arrayFromSegmentBinaryLabelmap(
                vessel_segmentation, source_segment_id, input_volume
            )
            prediction = predictor(
                np.asarray(mask, dtype=bool),
                role,
                setup.paths_for(role),
                progress_callback=progress_callback,
            )
            labels = ptl_class_labels(role)
            for class_id in range(1, 20):
                class_mask = np.asarray(prediction.labels_zyx == class_id, dtype=np.uint8)
                if not class_mask.any():
                    continue
                stable_id = ptl_segment_id(role, class_id)
                segment = vtkSegmentationCore.vtkSegment()
                segment.SetName(labels[class_id])
                segment.SetColor(*self._ptl_color(role, class_id))
                segment.SetTag("PulmoSlicerAI.PTLClass", str(class_id))
                metadata = ptl_region_metadata(class_id)
                segment.SetTag("PulmoSlicerAI.Side", metadata["side"])
                segment.SetTag("PulmoSlicerAI.Lobe", metadata["lobe"])
                segment.SetTag("PulmoSlicerAI.Region", metadata["region"])
                segment.SetTag("PulmoSlicerAI.System", role)
                segment.SetTag("PulmoSlicerAI.ResearchOnly", "true")
                segmentation.AddSegment(segment, stable_id)
                slicer.util.updateSegmentBinaryLabelmapFromArray(
                    class_mask, output_segmentation, stable_id, input_volume
                )
                created.append(labels[class_id])
        if not created:
            raise RuntimeError("PTL did not create any segmental labels")
        return tuple(created)

    @staticmethod
    def _subject_hierarchy_folder(sh_node, parent_item, name):
        item = sh_node.GetItemChildWithName(parent_item, name)
        if item:
            return item
        return sh_node.CreateFolderItem(parent_item, name)

    @staticmethod
    def _move_segment_item(sh_node, segmentation_node, segment_id, parent_item):
        """Move a segment's virtual SH item without copying its voxel data."""

        import vtk

        segment = segmentation_node.GetSegmentation().GetSegment(segment_id)
        if segment is None:
            return False
        segmentation_item = sh_node.GetItemByDataNode(segmentation_node)
        children = vtk.vtkIdList()
        sh_node.GetItemChildren(segmentation_item, children, False)
        for index in range(children.GetNumberOfIds()):
            item = children.GetId(index)
            if sh_node.GetItemName(item) == segment.GetName():
                sh_node.SetItemAttribute(item, "PulmoSlicerAI.SegmentID", segment_id)
                sh_node.SetItemParent(item, parent_item)
                return True
        # An already organized item is intentionally left where it is.
        return False

    @classmethod
    def organize_subject_hierarchy(
        cls, lobe_node=None, ptl_node=None, source_node=None, context_node=None
    ):
        """Create the real Slicer Data tree: side → lobe → B/A/V/Lung."""

        import slicer

        sh_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(
            slicer.mrmlScene
        )
        scene_item = sh_node.GetSceneItemID()
        root = cls._subject_hierarchy_folder(sh_node, scene_item, "PulmoSlicer AI Results")
        internal = cls._subject_hierarchy_folder(sh_node, root, "Internal sources")
        anatomy = {
            "Right": ("Upper", "Middle", "Lower"),
            "Left": ("Upper", "Lower"),
        }
        folders = {}
        for side, lobes in anatomy.items():
            side_item = cls._subject_hierarchy_folder(sh_node, root, side)
            folders[(side, None, None)] = side_item
            for lobe in lobes:
                lobe_item = cls._subject_hierarchy_folder(sh_node, side_item, lobe)
                folders[(side, lobe, None)] = lobe_item
                for system in ("B", "A", "V", "Lung"):
                    folders[(side, lobe, system)] = cls._subject_hierarchy_folder(
                        sh_node, lobe_item, system
                    )

        lobe_map = {
            "lung_upper_lobe_right": ("Right", "Upper"),
            "lung_middle_lobe_right": ("Right", "Middle"),
            "lung_lower_lobe_right": ("Right", "Lower"),
            "lung_upper_lobe_left": ("Left", "Upper"),
            "lung_lower_lobe_left": ("Left", "Lower"),
        }
        if lobe_node:
            for segment_id, (side, lobe) in lobe_map.items():
                cls._move_segment_item(
                    sh_node, lobe_node, segment_id, folders[(side, lobe, "Lung")]
                )

        if ptl_node:
            from pulmoslicer_engine.adapters.labeling.ptl_labels import ptl_region_metadata

            segmentation = ptl_node.GetSegmentation()
            for index in range(segmentation.GetNumberOfSegments()):
                segment_id = segmentation.GetNthSegmentID(index)
                parts = segment_id.split("_")
                if len(parts) != 4 or parts[0] != "PTL":
                    continue
                metadata = ptl_region_metadata(int(parts[3]))
                if metadata["side"] not in anatomy:
                    central = cls._subject_hierarchy_folder(
                        sh_node, internal, "Central or out-of-lung"
                    )
                    target = cls._subject_hierarchy_folder(sh_node, central, parts[1])
                else:
                    target = folders[(metadata["side"], metadata["lobe"], parts[1])]
                cls._move_segment_item(sh_node, ptl_node, segment_id, target)

        if source_node:
            source_folder = cls._subject_hierarchy_folder(
                sh_node, internal, "TotalSegmentator A-V-B source masks"
            )
            for segment_id in cls.VESSEL_SEGMENTS:
                cls._move_segment_item(sh_node, source_node, segment_id, source_folder)

        if context_node:
            aorta_folder = cls._subject_hierarchy_folder(sh_node, root, "Aorta")
            chest_folder = cls._subject_hierarchy_folder(sh_node, root, "Chest wall")
            right_ribs = cls._subject_hierarchy_folder(sh_node, chest_folder, "Right ribs")
            left_ribs = cls._subject_hierarchy_folder(sh_node, chest_folder, "Left ribs")
            spine = cls._subject_hierarchy_folder(sh_node, chest_folder, "Thoracic spine T1-T12")
            segment_ids = cls._segment_ids(context_node)
            for segment_id in segment_ids:
                if segment_id in cls.AORTA_SEGMENTS + cls.ARCH_BRANCH_SEGMENTS:
                    target = aorta_folder
                elif segment_id.startswith("rib_right_"):
                    target = right_ribs
                elif segment_id.startswith("rib_left_"):
                    target = left_ribs
                elif segment_id.startswith("vertebrae_T"):
                    target = spine
                elif segment_id == "sternum":
                    target = chest_folder
                else:
                    continue
                cls._move_segment_item(sh_node, context_node, segment_id, target)

        for node in (source_node, lobe_node, ptl_node, context_node):
            if node:
                node_item = sh_node.GetItemByDataNode(node)
                if node_item:
                    sh_node.SetItemParent(node_item, internal)
        sh_node.SetItemExpanded(root, True)
        for side in anatomy:
            sh_node.SetItemExpanded(folders[(side, None, None)], True)
        return root

    @classmethod
    def show_3d(
        cls,
        segmentation_nodes,
        surface_profile="preview",
        progress_callback=None,
    ) -> str:
        if not segmentation_nodes:
            raise ValueError("Chưa có segmentation để hiển thị.")
        if surface_profile not in cls.SURFACE_PROFILES:
            raise ValueError(f"unknown 3D surface profile: {surface_profile}")
        smoothing, decimation = cls.SURFACE_PROFILES[surface_profile]
        import slicer

        for index, node in enumerate(segmentation_nodes, start=1):
            if progress_callback:
                progress_callback(
                    f"3D surface: node {index}/{len(segmentation_nodes)}, profile {surface_profile}"
                )
            node.CreateDefaultDisplayNodes()
            segmentation = node.GetSegmentation()
            segmentation.SetConversionParameter("Smoothing factor", smoothing)
            segmentation.SetConversionParameter("Decimation factor", decimation)
            if node.GetAttribute("PulmoSlicerAI.SurfaceProfile") != surface_profile:
                node.RemoveClosedSurfaceRepresentation()
            node.CreateClosedSurfaceRepresentation()
            node.SetAttribute("PulmoSlicerAI.SurfaceProfile", surface_profile)
            node.GetDisplayNode().SetVisibility3D(True)
            slicer.app.processEvents()
        return f"Đã dựng bề mặt 3D cho {len(segmentation_nodes)} segmentation."
