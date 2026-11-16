"""GR01/GR02: deterministic binary-mask skeleton and reduced graph extraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ReducedGraph:
    """Voxel-space branch graph consumed by the PTL feature builder."""

    nodes_zyx: tuple[tuple[float, float, float], ...]
    undirected_edges: tuple[tuple[int, int], ...]
    skeleton_voxels: int
    findings: tuple[str, ...] = ()


class CenterlineExtractionError(ValueError):
    pass


_HALF_NEIGHBOR_OFFSETS = tuple(
    (dz, dy, dx)
    for dz in (-1, 0, 1)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if (dz, dy, dx) != (0, 0, 0) and (dz, dy, dx) > (0, 0, 0)
)


def _default_skeletonizer(mask):
    from skimage.morphology import skeletonize

    return skeletonize(mask, method="lee")


def extract_reduced_graph(
    mask,
    *,
    skeletonizer: Callable | None = None,
    maximum_nodes: int | None = None,
) -> ReducedGraph:
    """Convert a 3-D binary mask into a branch/end-point graph.

    Coordinates stay in NumPy/Slicer array order ``(z, y, x)``. Junction
    voxel cliques are collapsed to one representative and degree-two chains
    become edges. No disconnected component is silently joined to another.
    """

    import numpy as np

    binary = np.asarray(mask, dtype=bool)
    if binary.ndim != 3:
        raise CenterlineExtractionError("PTL mask must be a 3-D array")
    if not binary.any():
        raise CenterlineExtractionError("PTL mask is empty")

    skeleton = np.asarray((skeletonizer or _default_skeletonizer)(binary), dtype=bool)
    coordinates = np.argwhere(skeleton)
    if not len(coordinates):
        raise CenterlineExtractionError("skeletonization produced no centerline")

    coordinate_keys = [tuple(int(value) for value in row) for row in coordinates]
    lookup = {coordinate: index for index, coordinate in enumerate(coordinate_keys)}
    adjacency = [set() for _ in coordinate_keys]
    for index, (z, y, x) in enumerate(coordinate_keys):
        for dz, dy, dx in _HALF_NEIGHBOR_OFFSETS:
            neighbor = lookup.get((z + dz, y + dy, x + dx))
            if neighbor is not None:
                adjacency[index].add(neighbor)
                adjacency[neighbor].add(index)

    degrees = [len(neighbors) for neighbors in adjacency]
    junction_voxels = {index for index, degree in enumerate(degrees) if degree > 2}
    endpoint_voxels = [index for index, degree in enumerate(degrees) if degree < 2]

    junction_components = []
    unseen = set(junction_voxels)
    while unseen:
        seed = min(unseen)
        stack = [seed]
        component = set()
        while stack:
            current = stack.pop()
            if current not in unseen:
                continue
            unseen.remove(current)
            component.add(current)
            stack.extend(adjacency[current] & junction_voxels & unseen)
        junction_components.append(tuple(sorted(component)))

    members = [(index,) for index in endpoint_voxels]
    members.extend(junction_components)
    members.sort(key=lambda group: min(coordinate_keys[index] for index in group))
    voxel_to_node = {
        voxel: node_index
        for node_index, group in enumerate(members)
        for voxel in group
    }

    node_coordinates = []
    for group in members:
        group_coordinates = coordinates[list(group)].astype(float)
        mean = group_coordinates.mean(axis=0)
        representative = min(
            group,
            key=lambda index: (
                float(np.sum((coordinates[index] - mean) ** 2)),
                coordinate_keys[index],
            ),
        )
        node_coordinates.append(tuple(float(v) for v in coordinates[representative]))

    visited_voxel_edges = set()
    reduced_edges = set()
    for source_node, group in enumerate(members):
        for source_voxel in group:
            for neighbor in sorted(adjacency[source_voxel]):
                key = tuple(sorted((source_voxel, neighbor)))
                if key in visited_voxel_edges:
                    continue
                visited_voxel_edges.add(key)
                target_node = voxel_to_node.get(neighbor)
                if target_node is not None:
                    if source_node != target_node:
                        reduced_edges.add(tuple(sorted((source_node, target_node))))
                    continue

                previous, current = source_voxel, neighbor
                while current not in voxel_to_node:
                    candidates = sorted(adjacency[current] - {previous})
                    if len(candidates) != 1:
                        raise CenterlineExtractionError(
                            "unexpected centerline topology while tracing a branch"
                        )
                    following = candidates[0]
                    visited_voxel_edges.add(tuple(sorted((current, following))))
                    previous, current = current, following
                target_node = voxel_to_node[current]
                if source_node != target_node:
                    reduced_edges.add(tuple(sorted((source_node, target_node))))

    untraced = sum(
        1
        for left, neighbors in enumerate(adjacency)
        for right in neighbors
        if left < right and (left, right) not in visited_voxel_edges
    )
    findings = ("UNATTACHED_CYCLE_PRESENT",) if untraced else ()
    if not node_coordinates or not reduced_edges:
        raise CenterlineExtractionError("mask does not contain a usable branch graph")
    if maximum_nodes is not None and len(node_coordinates) > maximum_nodes:
        raise CenterlineExtractionError(
            f"graph has {len(node_coordinates)} nodes, above PTL maximum {maximum_nodes}"
        )
    return ReducedGraph(
        tuple(node_coordinates),
        tuple(sorted(reduced_edges)),
        len(coordinates),
        findings,
    )
