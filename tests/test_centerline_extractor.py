import unittest

try:
    import numpy as np
except ImportError:  # Minimal repository test interpreter has no NumPy.
    np = None

from pulmoslicer_engine.adapters.graph.centerline_extractor import (
    CenterlineExtractionError,
    extract_reduced_graph,
)


@unittest.skipIf(np is None, "NumPy is tested in the Slicer runtime suite")
class CenterlineExtractorTests(unittest.TestCase):
    @staticmethod
    def identity(mask):
        return mask

    def test_y_branch_is_reduced_to_three_endpoints_and_one_junction(self):
        mask = np.zeros((7, 7, 7), dtype=bool)
        for point in ((3, 3, 1), (3, 3, 2), (3, 3, 3), (2, 3, 4), (1, 3, 5), (4, 3, 4), (5, 3, 5)):
            mask[point] = True

        graph = extract_reduced_graph(mask, skeletonizer=self.identity)

        self.assertEqual(len(graph.nodes_zyx), 4)
        self.assertEqual(len(graph.undirected_edges), 3)
        self.assertEqual(graph.findings, ())

    def test_disconnected_trees_are_not_artificially_joined(self):
        mask = np.zeros((9, 9, 9), dtype=bool)
        mask[1, 1, 1:4] = True
        mask[7, 7, 5:8] = True

        graph = extract_reduced_graph(mask, skeletonizer=self.identity)

        self.assertEqual(len(graph.nodes_zyx), 4)
        self.assertEqual(len(graph.undirected_edges), 2)

    def test_empty_and_overlarge_graphs_fail_closed(self):
        with self.assertRaisesRegex(CenterlineExtractionError, "empty"):
            extract_reduced_graph(np.zeros((3, 3, 3)), skeletonizer=self.identity)

        line = np.zeros((3, 3, 5), dtype=bool)
        line[1, 1, 1:4] = True
        with self.assertRaisesRegex(CenterlineExtractionError, "above PTL maximum"):
            extract_reduced_graph(line, skeletonizer=self.identity, maximum_nodes=1)


if __name__ == "__main__":
    unittest.main()
