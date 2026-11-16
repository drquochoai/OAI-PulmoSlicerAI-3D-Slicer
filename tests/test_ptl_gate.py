import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pulmoslicer_engine.adapters.graph.ptl_graph_parity_checker import GraphFixture, compare_graph_fixture
from pulmoslicer_engine.adapters.labeling.ptl_checkpoint_probe import (
    PTL_REPOSITORY_COMMIT, PtlBundleError, probe_ptl_bundle
)


class PtlGateTests(unittest.TestCase):
    def write_bundle(self, root: Path, reproduced=True, tamper=False):
        checkpoints = {}
        for role in ("airway", "artery", "vein"):
            path = root / f"{role}.pt"
            path.write_bytes(f"synthetic-{role}".encode())
            checkpoints[role] = {
                "file": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "license_id": "TEST-FIXTURE-ONLY",
            }
        if tamper:
            (root / "vein.pt").write_bytes(b"changed")
        manifest = root / "manifest.json"
        manifest.write_text(json.dumps({
            "repository_commit": PTL_REPOSITORY_COMMIT,
            "checkpoints": checkpoints,
            "graph_contract_version": "author-fixture/1.0.0",
            "original_reproduction": reproduced,
        }), encoding="utf-8")
        return manifest

    def test_all_three_hashes_and_reproduction_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = probe_ptl_bundle(self.write_bundle(root))
            self.assertEqual({item.role for item in bundle.checkpoints}, {"airway", "artery", "vein"})
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(PtlBundleError, "reproduction"):
                probe_ptl_bundle(self.write_bundle(Path(directory), reproduced=False))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(PtlBundleError, "mismatch"):
                probe_ptl_bundle(self.write_bundle(Path(directory), tamper=True))

    def test_graph_parity_rejects_edge_direction_and_coordinate_semantics(self):
        author = GraphFixture(((0, 0, 0), (1, 0, 0)), ((0, 1),), -10, "voxel_zyx", "minmax")
        exact = compare_graph_fixture(author, author)
        self.assertTrue(exact.passed)
        candidate = GraphFixture(((0, 0, 0), (1, 0, 0)), ((1, 0),), -10, "lps_mm", "minmax")
        report = compare_graph_fixture(author, candidate)
        self.assertFalse(report.passed)
        self.assertIn("EDGE_INDEX_ORIENTATION_MISMATCH", report.findings)
        self.assertIn("COORDINATE_SEMANTICS_MISMATCH", report.findings)


if __name__ == "__main__":
    unittest.main()
