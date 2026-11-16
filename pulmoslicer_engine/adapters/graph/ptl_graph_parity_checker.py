"""GR04: field-by-field PTL graph parity report against an author fixture."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class GraphFixture:
    nodes: tuple[tuple[float, float, float], ...]
    directed_edges: tuple[tuple[int, int], ...]
    padding_value: float
    coordinate_semantics: str
    normalization: str


@dataclass(frozen=True)
class GraphParityReport:
    passed: bool
    findings: tuple[str, ...]
    maximum_node_error: float


def compare_graph_fixture(
    author: GraphFixture, candidate: GraphFixture, coordinate_tolerance: float = 1e-6
) -> GraphParityReport:
    findings: list[str] = []
    if author.coordinate_semantics != candidate.coordinate_semantics:
        findings.append("COORDINATE_SEMANTICS_MISMATCH")
    if author.normalization != candidate.normalization:
        findings.append("NORMALIZATION_MISMATCH")
    if author.padding_value != candidate.padding_value:
        findings.append("PADDING_VALUE_MISMATCH")
    if len(author.nodes) != len(candidate.nodes):
        findings.append("NODE_COUNT_MISMATCH")
    if author.directed_edges != candidate.directed_edges:
        findings.append("EDGE_INDEX_ORIENTATION_MISMATCH")
    errors = [
        math.sqrt(sum((left - right) ** 2 for left, right in zip(expected, actual)))
        for expected, actual in zip(author.nodes, candidate.nodes)
    ]
    maximum_error = max(errors, default=0.0)
    if maximum_error > coordinate_tolerance:
        findings.append("NODE_COORDINATE_MISMATCH")
    return GraphParityReport(not findings, tuple(findings), maximum_error)

