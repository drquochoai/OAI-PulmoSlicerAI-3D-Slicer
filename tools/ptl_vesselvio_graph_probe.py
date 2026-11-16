"""Build a PTL graph with the exact VesselVio family used by the paper.

VesselVio is GPLv3 and intentionally remains an external research dependency
under ``.tools``; this probe does not copy it into the extension package.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
import types


def _prepare_external_runtime(runtime: Path, vesselvio: Path) -> None:
    # Load the external stack first so numba sees its supported NumPy version.
    sys.path.insert(0, str(runtime.resolve()))
    sys.path.insert(1, str(vesselvio.resolve()))

    from skimage import morphology

    if not hasattr(morphology, "skeletonize_3d"):
        morphology.skeletonize_3d = lambda image: morphology.skeletonize(
            image, method="lee"
        )

    # VesselVio's core modules import GUI-heavy helpers even in headless mode.
    # The graph path used here needs only these two helper contracts.
    helpers = types.ModuleType("library.helpers")
    helpers.unix_check = lambda: False
    helpers.get_cwd = lambda: str(vesselvio.resolve())
    helpers.multiprocessing_input = lambda *args, **kwargs: (_ for _ in ()).throw(
        RuntimeError("multiprocessing is disabled in the deterministic probe")
    )
    image_processing = types.ModuleType("library.image_processing")
    image_processing.min_resolution = 1.0
    sys.modules["library.helpers"] = helpers
    sys.modules["library.image_processing"] = image_processing


def run(args) -> dict:
    _prepare_external_runtime(args.runtime, args.vesselvio)

    import numpy as np
    from library import feature_extraction as features
    from library import graph_processing as graphs
    from library import volume_processing as volumes

    archive = np.load(args.volume)
    source = archive[archive.files[0]] > 0
    started = time.perf_counter()
    bounded, minimum = volumes.volume_prep(source)
    padded = volumes.pad_volume(bounded)
    points = volumes.skeletonize(padded, verbose=args.verbose)
    resolution = np.asarray([1.0, 1.0, 1.0], dtype=np.float64)
    radii, visual_radii = volumes.radii_calc_input(
        padded, points, resolution, gen_vis_radii=True, verbose=args.verbose
    )
    graph = graphs.create_graph(
        padded.shape, radii, visual_radii, points, minimum, verbose=args.verbose
    )
    centerline_vertices = graph.vcount()
    centerline_edges = graph.ecount()
    features.feature_input(
        graph,
        resolution,
        args.volume.name,
        image_dim=3,
        image_shape=source.shape,
        reduce_graph=True,
        verbose=args.verbose,
    )

    nodes = np.asarray(graph.vs["v_coords"], dtype=np.float64)
    edges = np.asarray(graph.get_edgelist(), dtype=np.int64)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output, nodes_zyx=nodes, edges=edges)
    return {
        "source": args.volume.name,
        "source_shape": list(source.shape),
        "foreground_voxels": int(source.sum()),
        "centerline_vertices": int(centerline_vertices),
        "centerline_edges": int(centerline_edges),
        "reduced_nodes": int(len(nodes)),
        "reduced_edges": int(len(edges)),
        "elapsed_seconds": time.perf_counter() - started,
        "output": str(args.output.resolve()),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vesselvio", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print("PTL_VESSELVIO_GRAPH=" + json.dumps(result, sort_keys=True))
