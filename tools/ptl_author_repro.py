"""Reproduce an official PTL checkpoint on one public author fixture.

This is a research/evidence tool, not a clinical inference entry point.  It
mirrors the input construction in the reviewed upstream ``pygeo_dataset.py``
at commit 27fdace577293a29480bce4f00efba7501cadd20.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


MAX_NODES = {"airway": 519, "artery": 1813, "vein": 1691}


def _macro_dice(prediction, target, class_count=19):
    import numpy as np

    scores = []
    for label in range(1, class_count + 1):
        predicted = prediction == label
        expected = target == label
        denominator = int(predicted.sum()) + int(expected.sum())
        if denominator:
            scores.append(2.0 * int((predicted & expected).sum()) / denominator)
    return float(np.mean(scores)) if scores else 0.0


def _load_author_input(
    volume_path: Path,
    graph_path: Path | None,
    derived_graph_path: Path | None,
    role: str,
    seed: int,
):
    import networkx as nx
    import numpy as np
    import torch

    archive = np.load(volume_path)
    volume = archive[archive.files[0]]
    if derived_graph_path is not None:
        derived = np.load(derived_graph_path)
        nodes = np.asarray(derived["nodes_zyx"], dtype=np.float64)
        undirected_edges = np.asarray(derived["edges"], dtype=np.int64)
        edges = []
        for start, endpoint in undirected_edges:
            if start != endpoint:
                edges.extend(((int(start), int(endpoint)), (int(endpoint), int(start))))
    else:
        graph = nx.read_graphml(graph_path)
        edges = []
        for start in graph._adj:
            for endpoint in graph._adj[start]:
                if start != endpoint:
                    edges.append((int(start[1:]), int(endpoint[1:])))

        nodes = []
        for node in graph._node:
            attributes = graph._node[node]
            nodes.append(
                [
                    int(float(attributes["Z"])),
                    int(float(attributes["Y"])),
                    int(float(attributes["X"])),
                ]
            )
        nodes = np.asarray(nodes, dtype=np.float64)
    if len(nodes) > MAX_NODES[role]:
        raise RuntimeError(f"{role} graph exceeds author Max_Node")

    foreground = np.transpose(np.nonzero(volume))
    if len(foreground) < 16000:
        raise RuntimeError(f"{role} fixture has fewer than 16000 foreground voxels")
    rng = np.random.default_rng(seed)
    shuffled = foreground[rng.permutation(len(foreground))]
    points = shuffled[:6000].astype(np.float64)
    implicit_points = shuffled[6000:16000].astype(np.float64)

    # Exact author transform: jointly normalize real nodes, sampled points and
    # implicit training points; keep padded graph nodes at sentinel -10.
    combined = np.concatenate((nodes, points, implicit_points), axis=0)
    minimum = np.amin(combined, axis=0)
    maximum = np.amax(combined, axis=0)
    span = maximum - minimum
    if np.any(span == 0):
        raise RuntimeError(f"{role} fixture has a degenerate coordinate axis")
    combined = (combined - minimum) / span
    normalized_nodes = combined[: len(nodes)]
    normalized_points = combined[len(nodes) : len(nodes) + len(points)]

    padded_nodes = np.full((MAX_NODES[role], 3), -10.0, dtype=np.float64)
    padded_nodes[: len(nodes)] = normalized_nodes
    edge_index = torch.tensor(edges, dtype=torch.long).transpose(0, 1).contiguous()

    query_minimum = np.amin(foreground, axis=0)
    query_span = np.amax(foreground, axis=0) - query_minimum
    normalized_query = (foreground - query_minimum) / query_span
    return (
        volume,
        foreground,
        torch.from_numpy(normalized_query).unsqueeze(0),
        torch.from_numpy(normalized_points).float().unsqueeze(0),
        torch.from_numpy(padded_nodes).float().unsqueeze(0),
        edge_index,
        len(nodes),
    )


def run(args) -> dict:
    sys.path.append(str(args.runtime.resolve()))
    sys.path.insert(0, str(args.upstream.resolve()))

    import numpy as np
    import torch
    from model.pg_model import IPGN

    role = args.role
    started = time.perf_counter()
    (
        volume,
        foreground,
        query,
        points,
        nodes,
        edge_index,
        node_count,
    ) = _load_author_input(
        args.volume, args.graph, args.derived_graph, role, args.seed
    )

    specs = json.loads((args.upstream / "specs" / "network_specs.json").read_text())
    model = IPGN(specs, num_class=19, max_node=MAX_NODES[role], device="cpu")
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    model.point_graph_network.implicit_inference_mode()
    model.eval()

    with torch.inference_mode():
        prediction = model(query, points, nodes, edge_index, full_voxel=True) + 1
    target = volume[
        foreground[:, 0], foreground[:, 1], foreground[:, 2]
    ].astype(np.int64)
    prediction = prediction.astype(np.int64)

    elapsed = time.perf_counter() - started
    return {
        "role": role,
        "fixture": args.volume.name,
        "foreground_voxels": int(len(foreground)),
        "graph_nodes": int(node_count),
        "directed_edges": int(edge_index.shape[1]),
        "accuracy": float(np.mean(prediction == target)),
        "macro_dice_present_classes": _macro_dice(prediction, target),
        "predicted_classes": sorted(int(value) for value in np.unique(prediction)),
        "target_classes": sorted(int(value) for value in np.unique(target)),
        "elapsed_seconds": elapsed,
        "seed": args.seed,
        "device": "cpu",
        "passed_execution": True,
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=tuple(MAX_NODES))
    parser.add_argument("--volume", type=Path, required=True)
    graph_group = parser.add_mutually_exclusive_group(required=True)
    graph_group.add_argument("--graph", type=Path)
    graph_group.add_argument("--derived-graph", type=Path)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print("PTL_AUTHOR_REPRO=" + json.dumps(result, sort_keys=True))
