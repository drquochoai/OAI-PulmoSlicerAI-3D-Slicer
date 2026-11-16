"""Slicer-facing orchestration for interactive HTML export."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .anatomy import describe_segment
from .color_templates import color_for
from .contracts import ExportOptions, HtmlExportResult, MeshRecord
from .html_writer import write_atomic_html
from .mesh_codec import encode_mesh
from .mesh_pipeline import capture_segment_source, prepare_captured_surface


@dataclass(frozen=True)
class CapturedAnatomy:
    segment_id: str
    descriptor: object
    polydata: object


class InteractiveHtmlExporter:
    """Export allowlisted anatomy without changing the MRML source scene."""

    OUTPUT_ROLE_ATTRIBUTE = "PulmoSlicerAI.OutputRole"

    @classmethod
    def apply_slicer_colors(cls, segmentation_nodes, template_id: str) -> int:
        """Apply the same palette to Slicer display without changing geometry."""

        updated = 0
        for node, segment_id, descriptor in cls._candidates(segmentation_nodes):
            rgba = color_for(template_id, descriptor.anatomy_class)
            segment = node.GetSegmentation().GetSegment(segment_id)
            if segment is None:
                continue
            segment.SetColor(*rgba[:3])
            node.CreateDefaultDisplayNodes()
            display = node.GetDisplayNode()
            if display and hasattr(display, "SetSegmentOpacity3D"):
                display.SetSegmentOpacity3D(segment_id, rgba[3])
            updated += 1
        return updated

    def export(
        self,
        segmentation_nodes: Iterable,
        options: ExportOptions,
        progress_callback: Callable[[str], None] | None = None,
    ) -> HtmlExportResult:
        options.validate()
        captured = self.capture(segmentation_nodes, progress_callback)
        return self.export_captured(captured, options, progress_callback)

    def capture(self, segmentation_nodes, progress_callback=None):
        """Capture MRML-owned surfaces; call only from Slicer's main thread."""

        candidates = self._candidates(segmentation_nodes)
        if not candidates:
            raise ValueError("Không tìm thấy cấu trúc PulmoSlicer hợp lệ để xuất")
        captured = []
        failures = []
        for index, (node, segment_id, descriptor) in enumerate(candidates, start=1):
            if progress_callback:
                progress_callback(
                    f"HTML capture: {index}/{len(candidates)} — {descriptor.display_name}"
                )
            try:
                polydata = capture_segment_source(node, segment_id)
                captured.append(CapturedAnatomy(segment_id, descriptor, polydata))
            except Exception as exc:
                failures.append(
                    f"{descriptor.display_name}: {' '.join(str(exc).split())[:180]}"
                )
        if not captured:
            raise RuntimeError("Không sao chép được closed surface hợp lệ nào")
        return tuple(captured), tuple(failures)

    def export_captured(
        self,
        captured_bundle,
        options: ExportOptions,
        progress_callback: Callable[[str], None] | None = None,
        cancellation_check: Callable[[], bool] | None = None,
    ) -> HtmlExportResult:
        """Run detached VTK optimization and packaging in a background thread."""

        options.validate()
        captured, capture_warnings = captured_bundle
        records = []
        warnings = list(capture_warnings)
        used_ids = set()
        total = len(captured)
        for index, item in enumerate(captured, start=1):
            if cancellation_check and cancellation_check():
                raise RuntimeError("HTML export đã được người dùng hủy")
            segment_id, descriptor = item.segment_id, item.descriptor
            if descriptor.stable_id in used_ids:
                warnings.append(f"Bỏ qua stable ID trùng: {descriptor.stable_id}")
                continue
            try:
                def stage(current, stage_total, label):
                    if progress_callback:
                        progress_callback(
                            f"HTML export: {index}/{total} stage {current}/{stage_total} — "
                            f"{descriptor.display_name} — {label}"
                        )
                    if cancellation_check and cancellation_check():
                        raise RuntimeError("HTML export đã được người dùng hủy")

                surface = prepare_captured_surface(
                    item.polydata,
                    segment_id,
                    descriptor.anatomy_class,
                    options.profile,
                    stage_callback=stage,
                )
                stage(6, 6, "nén payload và tính SHA-256")
                payload, payload_hash, payload_bytes, _ = encode_mesh(surface.positions, surface.indices)
            except Exception as exc:
                if "người dùng hủy" in str(exc):
                    raise
                warnings.append(f"{descriptor.display_name}: {' '.join(str(exc).split())[:180]}")
                continue
            rgba = color_for(options.color_template_id, descriptor.anatomy_class)
            records.append(
                MeshRecord(
                    stable_id=descriptor.stable_id,
                    display_name=descriptor.display_name,
                    hierarchy_path=descriptor.path,
                    anatomy_class=descriptor.anatomy_class,
                    color=rgba[:3],
                    opacity=rgba[3],
                    visible=options.show_all_on_open,
                    payload_b64=payload,
                    payload_sha256=payload_hash,
                    payload_bytes=payload_bytes,
                    vertex_count=len(surface.positions) // 3,
                    triangle_count=len(surface.indices) // 3,
                    bounds_web_mm=surface.bounds_web_mm,
                    source_hash=surface.source_hash,
                    qa=surface.qa,
                )
            )
            used_ids.add(descriptor.stable_id)
            warnings.extend(f"{descriptor.display_name}: {warning}" for warning in surface.warnings)
        if not records:
            raise RuntimeError("Mọi cấu trúc đều thất bại trong bước chuẩn bị mesh")
        if progress_callback:
            progress_callback("HTML export: đóng gói, quét PHI và kiểm tra integrity")
        records_tuple = tuple(records)
        digest, size, validation = write_atomic_html(options, records_tuple, tuple(warnings))
        return HtmlExportResult(
            options.output_path,
            len(records_tuple),
            sum(record.triangle_count for record in records_tuple),
            size,
            digest,
            tuple(warnings),
            validation,
        )

    @classmethod
    def _candidates(cls, segmentation_nodes):
        result = []
        for node in segmentation_nodes:
            if node is None or not node.IsA("vtkMRMLSegmentationNode"):
                continue
            role = node.GetAttribute(cls.OUTPUT_ROLE_ATTRIBUTE) or ""
            segmentation = node.GetSegmentation()
            for index in range(segmentation.GetNumberOfSegments()):
                segment_id = segmentation.GetNthSegmentID(index)
                descriptor = describe_segment(role, segment_id)
                if descriptor is not None:
                    result.append((node, segment_id, descriptor))
        return result
