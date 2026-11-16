"""LB02-LB04: shared CPU inference adapter for official PTL IPGN weights."""

from __future__ import annotations

from dataclasses import dataclass
import gc
import json
from pathlib import Path
import sys
from typing import Callable

from pulmoslicer_engine.adapters.graph.centerline_extractor import extract_reduced_graph


MAX_NODES = {"airway": 519, "artery": 1813, "vein": 1691}


@dataclass(frozen=True)
class PtlRuntimePaths:
    source: Path
    site_packages: Path
    checkpoint: Path


@dataclass(frozen=True)
class PtlPrediction:
    role: str
    labels_zyx: object
    graph_nodes: int
    graph_edges: int
    foreground_voxels: int
    findings: tuple[str, ...]


class PtlInferenceError(RuntimeError):
    pass


def _notify(callback: Callable[[str], None] | None, message: str) -> None:
    if callback is not None:
        callback(message)


def predict_ptl(
    mask,
    role: str,
    runtime: PtlRuntimePaths,
    *,
    progress_callback: Callable[[str], None] | None = None,
    seed: int = 0,
) -> PtlPrediction:
    import numpy as np

    if role not in MAX_NODES:
        raise PtlInferenceError(f"unsupported PTL role: {role}")
    binary = np.asarray(mask, dtype=bool)
    foreground = np.argwhere(binary)
    if len(foreground) < 16000:
        raise PtlInferenceError(
            f"{role} mask has {len(foreground)} voxels; PTL requires at least 16000"
        )
    _notify(progress_callback, f"PTL {role}: extracting centerline graph")
    graph = extract_reduced_graph(binary, maximum_nodes=MAX_NODES[role])

    site_packages = str(runtime.site_packages.resolve())
    source = str(runtime.source.resolve())
    if site_packages not in sys.path:
        sys.path.append(site_packages)
    if source not in sys.path:
        sys.path.insert(0, source)

    try:
        import torch
        from model.pg_model import IPGN
    except Exception as exc:
        raise PtlInferenceError("PTL Python runtime is incomplete") from exc

    _notify(progress_callback, f"PTL {role}: preparing deterministic point/graph tensors")
    rng = np.random.default_rng(seed)
    sampled = foreground[rng.permutation(len(foreground))]
    points = sampled[:6000].astype(np.float64)
    implicit_points = sampled[6000:16000].astype(np.float64)
    nodes = np.asarray(graph.nodes_zyx, dtype=np.float64)
    combined = np.concatenate((nodes, points, implicit_points), axis=0)
    minimum = np.amin(combined, axis=0)
    span = np.amax(combined, axis=0) - minimum
    if np.any(span == 0):
        raise PtlInferenceError(f"{role} mask has a degenerate coordinate axis")
    normalized = (combined - minimum) / span
    normalized_nodes = normalized[: len(nodes)]
    normalized_points = normalized[len(nodes) : len(nodes) + 6000]

    padded_nodes = np.full((MAX_NODES[role], 3), -10.0, dtype=np.float64)
    padded_nodes[: len(nodes)] = normalized_nodes
    directed_edges = []
    for left, right in graph.undirected_edges:
        directed_edges.extend(((left, right), (right, left)))

    query_minimum = np.amin(foreground, axis=0)
    query_span = np.amax(foreground, axis=0) - query_minimum
    normalized_query = (foreground - query_minimum) / query_span
    accelerator = bool(torch.cuda.is_available())
    device = torch.device("cuda:0" if accelerator else "cpu")
    backend = "AMD ROCm" if accelerator and getattr(torch.version, "hip", None) else (
        "CUDA" if accelerator else "CPU"
    )
    _notify(progress_callback, f"PTL {role}: compute backend {backend}")
    query_tensor = torch.from_numpy(normalized_query).unsqueeze(0)
    points_tensor = torch.from_numpy(normalized_points).float().unsqueeze(0).to(device)
    nodes_tensor = torch.from_numpy(padded_nodes).float().unsqueeze(0).to(device)
    edges_tensor = (
        torch.tensor(directed_edges, dtype=torch.long).transpose(0, 1).to(device)
    )

    specs_path = runtime.source / "specs" / "network_specs.json"
    specs = json.loads(specs_path.read_text(encoding="utf-8"))
    _notify(progress_callback, f"PTL {role}: loading verified checkpoint")
    model = IPGN(specs, num_class=19, max_node=MAX_NODES[role], device=str(device))
    state = torch.load(runtime.checkpoint, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    model.to(device)
    model.point_graph_network.implicit_inference_mode()
    model.eval()
    _notify(progress_callback, f"PTL {role}: classifying {len(foreground)} voxels")
    with torch.inference_mode():
        prediction = model(
            query_tensor,
            points_tensor,
            nodes_tensor,
            edges_tensor,
            full_voxel=True,
        ) + 1

    labelmap = np.zeros(binary.shape, dtype=np.uint8)
    labelmap[
        foreground[:, 0], foreground[:, 1], foreground[:, 2]
    ] = prediction.astype(np.uint8)
    del model, state, query_tensor, points_tensor, nodes_tensor, edges_tensor
    gc.collect()
    return PtlPrediction(
        role,
        labelmap,
        len(graph.nodes_zyx),
        len(graph.undirected_edges),
        len(foreground),
        graph.findings,
    )
