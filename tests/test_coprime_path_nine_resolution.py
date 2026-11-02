"""Independent finite checks supporting the nine-edge-path proof.

These tests check the boundary witness and small auxiliary claims. They do
not replace the published graph theorems or verify the written deduction.
"""
from itertools import combinations, permutations
import json
from pathlib import Path

import pytest

from coprime_path_certificates import PathProblem, validate_witness


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'docs/audits/coprime-path-nine-resolution-2026-10-18'


def test_complete_lower_boundary_coloring():
    record = json.loads((AUDIT / 'lower-n16-k9.json').read_text())
    assert (record['n'], record['path_edges']) == (16, 9)
    assert len(record['coloring']) == 79
    assert validate_witness(PathProblem(16, 9), record['coloring']) == (8, 8)


@pytest.mark.parametrize('faults', range(4))
def test_hall_slots_have_distinct_representatives(faults):
    # All labeled K(4,5) faults, hence all orders of the four-vertex side
    # by relabeling. Brute-force representatives are independent of Hall's
    # theorem and of the counting argument in the proof.
    edges = set((a, b) for a in range(4) for b in range(5))
    assignments = list(permutations(range(5), 4))
    checked = 0
    for missing in combinations(sorted(edges), faults):
        remaining = edges - set(missing)
        slots = [{b for b in range(5) if (a, b) in remaining
                  and (a + 1, b) in remaining} for a in range(3)]
        slots.append({b for b in range(5) if (3, b) in remaining})
        assert any(all(b in slot for b, slot in zip(assignment, slots))
                   for assignment in assignments)
        checked += 1
    assert checked == (1, 20, 190, 1140)[faults]


def _path_from(adjacency, start, vertices):
    """Enumerate simple paths for these small abstract graphs."""
    pending = [(start,)]
    while pending:
        path = pending.pop()
        if len(path) == vertices:
            return path
        pending.extend(path + (v,) for v in adjacency[path[-1]] if v not in path)
    return None


@pytest.mark.parametrize('attachments', range(8))
def test_three_vertex_cover_core_endpoint_paths(attachments):
    # A joins a clique C and independent B; each prior attachment joins A.
    a, c = set(range(3)), set(range(3, 6))
    b = set(range(6, 10 + attachments))
    vertices = a | b | c
    edges = {frozenset((u, v)) for u, v in combinations(vertices, 2)
             if u in a or v in a or {u, v} <= c}
    adjacency = {u: {v for v in vertices if frozenset((u, v)) in edges}
                 for u in vertices}
    for vertex in vertices - a:
        assert _path_from(adjacency, vertex, 9) is not None
    if attachments == 7:
        remaining = vertices - a - {3}
        assert sum(edge <= remaining for edge in edges) == 1
        assert len(edges) == 48


@pytest.mark.parametrize('internal_edges,expected', [(1, 0), (2, 90), (3, 15)])
def test_nonempty_six_vertex_closure_cases_are_hamiltonian(internal_edges, expected):
    # In the i=5 closure case, A is K5, B has <=3 edges, and m=e(B)+3
    # cross edges are missing. The closed-degree inequalities imply that
    # all missing edges lie in one A row when e(B)>0. Fix that row by
    # symmetry, enumerate B and its missing columns, and find an actual
    # Hamilton cycle for every surviving closed graph.
    a, b = set(range(5)), set(range(5, 11))
    checked = 0
    for internal in combinations(combinations(sorted(b), 2), internal_edges):
        for missing_columns in combinations(sorted(b), internal_edges + 3):
            edges = {frozenset(pair) for pair in combinations(sorted(a), 2)}
            edges.update(frozenset(pair) for pair in internal)
            edges.update(frozenset((u, v)) for u in a for v in b
                         if u != 4 or v not in missing_columns)
            adjacency = {u: {v for v in a | b if frozenset((u, v)) in edges}
                         for u in a | b}
            if max(len(adjacency[v]) for v in b) > 5:
                continue
            if any(len(adjacency[u]) + len(adjacency[v]) >= 11
                   for u, v in combinations(sorted(a | b), 2)
                   if v not in adjacency[u]):
                continue
            assert len(edges) == 37
            assert max(len(adjacency[v]) for v in b) <= 5
            # Vertex 0 is universal, so a spanning path from it closes.
            path = _path_from(adjacency, 0, 11)
            assert path is not None and path[-1] in adjacency[0]
            checked += 1
    assert checked == expected
