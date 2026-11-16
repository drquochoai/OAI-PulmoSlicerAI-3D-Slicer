"""Non-destructive VTK surface preparation with conservative anatomy QA."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .mesh_codec import source_geometry_hash


@dataclass(frozen=True)
class PreparedSurface:
    positions: tuple[float, ...]
    indices: tuple[int, ...]
    bounds_web_mm: tuple[float, float, float, float, float, float]
    source_hash: str
    qa: dict
    warnings: tuple[str, ...]


_PROFILES = {
    "quick": {
        "airway": (5, 0.12, 0.15), "artery": (5, 0.12, 0.15), "vein": (5, 0.12, 0.15),
        "aorta": (10, 0.08, 0.35), "tumor": (0, 0.0, 0.08), "lung": (12, 0.06, 0.58),
        "bone": (5, 0.10, 0.65), "other": (8, 0.08, 0.40),
    },
    "standard": {
        "airway": (8, 0.10, 0.08), "artery": (8, 0.10, 0.08), "vein": (8, 0.10, 0.08),
        "aorta": (12, 0.06, 0.28), "tumor": (3, 0.14, 0.03), "lung": (15, 0.05, 0.45),
        "bone": (6, 0.10, 0.55), "other": (10, 0.08, 0.30),
    },
    "detail": {
        "airway": (6, 0.12, 0.0), "artery": (6, 0.12, 0.0), "vein": (6, 0.12, 0.0),
        "aorta": (10, 0.08, 0.12), "tumor": (0, 0.0, 0.0), "lung": (12, 0.06, 0.20),
        "bone": (4, 0.12, 0.30), "other": (6, 0.10, 0.15),
    },
}


def _component_count(polydata) -> int:
    import vtk

    connectivity = vtk.vtkPolyDataConnectivityFilter()
    connectivity.SetInputData(polydata)
    connectivity.SetExtractionModeToAllRegions()
    connectivity.ColorRegionsOff()
    connectivity.Update()
    return int(connectivity.GetNumberOfExtractedRegions())


def _triangulate_clean(polydata):
    import vtk

    triangle = vtk.vtkTriangleFilter()
    triangle.SetInputData(polydata)
    triangle.PassLinesOff()
    triangle.PassVertsOff()
    triangle.Update()
    clean = vtk.vtkCleanPolyData()
    clean.SetInputConnection(triangle.GetOutputPort())
    clean.ToleranceIsAbsoluteOn()
    clean.SetAbsoluteTolerance(0.0)
    clean.Update()
    output = vtk.vtkPolyData()
    output.DeepCopy(clean.GetOutput())
    return output


def _smooth(polydata, iterations: int, passband: float):
    if iterations <= 0:
        return polydata
    import vtk

    smooth = vtk.vtkWindowedSincPolyDataFilter()
    smooth.SetInputData(polydata)
    smooth.SetNumberOfIterations(iterations)
    smooth.SetPassBand(passband)
    smooth.BoundarySmoothingOff()
    smooth.FeatureEdgeSmoothingOff()
    smooth.NonManifoldSmoothingOn()
    smooth.NormalizeCoordinatesOn()
    smooth.Update()
    result = vtk.vtkPolyData()
    result.DeepCopy(smooth.GetOutput())
    return result


def _decimate(polydata, reduction: float):
    if reduction <= 0.0:
        return polydata
    import vtk

    decimate = vtk.vtkDecimatePro()
    decimate.SetInputData(polydata)
    decimate.SetTargetReduction(reduction)
    decimate.PreserveTopologyOn()
    decimate.SplittingOff()
    decimate.BoundaryVertexDeletionOff()
    decimate.Update()
    result = vtk.vtkPolyData()
    result.DeepCopy(decimate.GetOutput())
    return result


def _world_copy(segmentation_node, polydata):
    import slicer
    import vtk

    result = vtk.vtkPolyData()
    result.DeepCopy(polydata)
    parent = segmentation_node.GetParentTransformNode()
    if parent is None:
        return result
    transform = vtk.vtkGeneralTransform()
    slicer.vtkMRMLTransformNode.GetTransformBetweenNodes(parent, None, transform)
    apply_transform = vtk.vtkTransformPolyDataFilter()
    apply_transform.SetInputData(result)
    apply_transform.SetTransform(transform)
    apply_transform.Update()
    transformed = vtk.vtkPolyData()
    transformed.DeepCopy(apply_transform.GetOutput())
    return transformed


def capture_segment_source(segmentation_node, segment_id: str):
    """Copy MRML-owned geometry on the Slicer main thread for worker processing."""

    import vtkSegmentationCorePython as vtkSegmentationCore

    segmentation = segmentation_node.GetSegmentation()
    segment = segmentation.GetSegment(segment_id)
    if segment is None:
        raise ValueError(f"Segment no longer exists: {segment_id}")
    representation = (
        vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName()
    )
    source = segment.GetRepresentation(representation)
    if source is None:
        raise ValueError(
            f"Segment chưa có closed surface: {segment_id}; hãy dựng 3D trước khi xuất"
        )
    if source is None or source.GetNumberOfPoints() == 0:
        raise ValueError(f"Segment has no valid closed surface: {segment_id}")
    return _world_copy(segmentation_node, source)


def _extract_arrays(polydata):
    import vtk

    positions = []
    for index in range(polydata.GetNumberOfPoints()):
        x, y, z = polydata.GetPoint(index)
        # Slicer world RAS -> browser: X right, Y superior, Z posterior.
        positions.extend((float(x), float(z), float(-y)))
    indices = []
    cell_ids = vtk.vtkIdList()
    polygons = polydata.GetPolys()
    polygons.InitTraversal()
    while polygons.GetNextCell(cell_ids):
        if cell_ids.GetNumberOfIds() != 3:
            continue
        indices.extend(int(cell_ids.GetId(i)) for i in range(3))
    return positions, indices


def _bounds(positions):
    axes = (positions[0::3], positions[1::3], positions[2::3])
    return tuple(value for axis in axes for value in (min(axis), max(axis)))


def _hash_polydata(polydata) -> str:
    positions, indices = _extract_arrays(polydata)
    return source_geometry_hash(positions, indices)


def _distance_limit(anatomy_class: str) -> float:
    if anatomy_class in ("airway", "artery", "vein", "tumor"):
        return 1.5
    if anatomy_class == "aorta":
        return 2.0
    return 3.0


def _sampled_bidirectional_distance_mm(source, candidate, maximum_samples=4000) -> float | None:
    import vtk

    if not hasattr(vtk, "vtkImplicitPolyDataDistance"):
        return None

    def directed(points, target):
        evaluator = vtk.vtkImplicitPolyDataDistance()
        evaluator.SetInput(target)
        count = points.GetNumberOfPoints()
        stride = max(1, count // maximum_samples)
        maximum = 0.0
        for index in range(0, count, stride):
            value = abs(float(evaluator.EvaluateFunction(points.GetPoint(index))))
            if math.isfinite(value):
                maximum = max(maximum, value)
        return maximum

    return max(directed(source, candidate), directed(candidate, source))


def _surface_area(polydata) -> float:
    import vtk

    metrics = vtk.vtkMassProperties()
    metrics.SetInputData(polydata)
    metrics.Update()
    value = float(metrics.GetSurfaceArea())
    return value if math.isfinite(value) else 0.0


def prepare_captured_surface(
    captured_polydata,
    segment_id: str,
    anatomy_class: str,
    profile: str,
    stage_callback=None,
) -> PreparedSurface:
    if profile not in _PROFILES:
        raise ValueError(f"Unknown mesh export profile: {profile}")
    if stage_callback:
        stage_callback(1, 6, "chuẩn hóa tam giác")
    source_world = _triangulate_clean(captured_polydata)
    if stage_callback:
        stage_callback(2, 6, "kiểm tra topology nguồn")
    source_components = _component_count(source_world)
    source_area = _surface_area(source_world)
    source_hash = _hash_polydata(source_world)
    key = anatomy_class if anatomy_class in _PROFILES[profile] else "other"
    iterations, passband, reduction = _PROFILES[profile][key]
    if stage_callback:
        stage_callback(3, 6, "làm mượt bề mặt")
    candidate = _smooth(source_world, iterations, passband)
    if stage_callback:
        stage_callback(4, 6, "giảm polygon bảo toàn topology")
    candidate = _triangulate_clean(_decimate(candidate, reduction))
    if stage_callback:
        stage_callback(5, 6, "đối chiếu mesh nguồn và mesh xuất")
    candidate_components = _component_count(candidate)
    candidate_area = _surface_area(candidate)
    distance = _sampled_bidirectional_distance_mm(source_world, candidate)
    warnings = []
    vascular = anatomy_class in ("airway", "artery", "vein")
    if vascular and candidate_components < source_components:
        warnings.append("QA fallback: smoothing/decimation merged or removed vascular components")
    if vascular and source_area > 0 and candidate_area / source_area < 0.82:
        warnings.append("QA fallback: vascular surface area changed beyond policy")
    if distance is not None and distance > _distance_limit(anatomy_class):
        warnings.append(f"QA fallback: surface displacement {distance:.2f} mm exceeded limit")
    if warnings:
        candidate = source_world
        candidate_components = source_components
        candidate_area = source_area
        distance = 0.0

    positions, indices = _extract_arrays(candidate)
    if not positions or not indices:
        raise ValueError(f"Prepared surface is empty: {segment_id}")
    qa = {
        "sourcePoints": int(source_world.GetNumberOfPoints()),
        "sourceTriangles": int(source_world.GetNumberOfPolys()),
        "sourceComponents": source_components,
        "exportPoints": len(positions) // 3,
        "exportTriangles": len(indices) // 3,
        "exportComponents": candidate_components,
        "sampledBidirectionalDistanceMm": distance,
        "sourceSurfaceAreaMm2": source_area,
        "exportSurfaceAreaMm2": candidate_area,
        "sourcePreserved": True,
        "profile": profile,
    }
    return PreparedSurface(
        tuple(positions), tuple(indices), _bounds(positions), source_hash, qa, tuple(warnings)
    )


def prepare_segment(
    segmentation_node, segment_id: str, anatomy_class: str, profile: str
) -> PreparedSurface:
    """Synchronous compatibility wrapper used by smoke tests and scripts."""

    captured = capture_segment_source(segmentation_node, segment_id)
    return prepare_captured_surface(captured, segment_id, anatomy_class, profile)
