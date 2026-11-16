"""Build and serialize the distributable native PTL graph adapter output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pulmoslicer_engine.adapters.graph.centerline_extractor import extract_reduced_graph


MAX_NODES = {"airway": 519, "artery": 1813, "vein": 1691}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=tuple(MAX_NODES))
    parser.add_argument("--volume", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    archive = np.load(args.volume)
    mask = archive[archive.files[0]] > 0
    started = time.perf_counter()
    graph = extract_reduced_graph(mask, maximum_nodes=MAX_NODES[args.role])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        nodes_zyx=np.asarray(graph.nodes_zyx),
        edges=np.asarray(graph.undirected_edges),
    )
    result = {
        "role": args.role,
        "skeleton_voxels": graph.skeleton_voxels,
        "reduced_nodes": len(graph.nodes_zyx),
        "reduced_edges": len(graph.undirected_edges),
        "findings": graph.findings,
        "elapsed_seconds": time.perf_counter() - started,
    }
    print("PTL_NATIVE_GRAPH=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
