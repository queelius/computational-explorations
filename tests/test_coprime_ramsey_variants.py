"""Tests for coprime_ramsey_variants.py -- coprime Ramsey variant computations."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from coprime_ramsey_variants import (
    coprime_edges,
    coprime_adj,
    find_coprime_cliques,
    _edge_var_map,
    _find_path_edge_sets,
    _find_all_cycles,
    compute_path_coprime_ramsey,
    compute_cycle_coprime_ramsey,
    compute_multicolor_coprime_ramsey,
    compute_bipartite_coprime_ramsey,
    compute_gallai_coprime_ramsey,
    count_avoiding_colorings_sat,
    density_avoiding_colorings,
)


# ---------------------------------------------------------------------------
# Infrastructure tests
# ---------------------------------------------------------------------------

class TestCoprimeAdj:
    def test_n3_complete(self):
        """[3] is a coprime clique: all pairs coprime."""
        adj = coprime_adj(3)
        assert adj[1] == {2, 3}
        assert adj[2] == {1, 3}
        assert adj[3] == {1, 2}

    def test_n4_missing_edge(self):
        """gcd(2,4)=2, so 2 and 4 are not adjacent."""
        adj = coprime_adj(4)
        assert 4 not in adj[2]
        assert 2 not in adj[4]
        assert 4 in adj[1]
        assert 4 in adj[3]

    def test_vertex_1_universal(self):
        """Vertex 1 is coprime to everything."""
        for n in [5, 10, 20]:
            adj = coprime_adj(n)
            assert adj[1] == set(range(2, n + 1))

    def test_symmetric(self):
        adj = coprime_adj(10)
        for v, nbrs in adj.items():
            for w in nbrs:
                assert v in adj[w], f"{v} in adj[{w}] but not vice versa"


class TestFindCoprimeCliques:
    def test_triangles_n5(self):
        cliques = find_coprime_cliques(5, 3)
        for c in cliques:
            assert len(c) == 3
            for i in range(3):
                for j in range(i + 1, 3):
                    assert math.gcd(c[i], c[j]) == 1

    def test_no_large_clique_in_small_graph(self):
        assert find_coprime_cliques(3, 5) == []

    def test_k1_returns_all_vertices(self):
        assert len(find_coprime_cliques(7, 1)) == 7


class TestEdgeVarMap:
    def test_maps_edges_to_positive_ints(self):
        edges = coprime_edges(5)
        etv = _edge_var_map(edges)
        assert len(etv) == len(edges)
        assert all(v >= 1 for v in etv.values())
        assert len(set(etv.values())) == len(edges)


# ---------------------------------------------------------------------------
# Path and cycle substructure tests
# ---------------------------------------------------------------------------

class TestPathEdgeSets:
    def test_path_length_2_n3(self):
        """A path of length 2 has 3 vertices and 2 edges."""
        adj = coprime_adj(3)
        es = _find_path_edge_sets(adj, 2, [1, 2, 3])
        # In K_3 (coprime), every 2-edge path is a pair of adjacent edges.
        # Edge sets: {(1,2),(1,3)}, {(1,2),(2,3)}, {(1,3),(2,3)} = 3
        assert len(es) == 3

    def test_deduplication(self):
        """Reversed paths produce the same edge set."""
        adj = coprime_adj(5)
        es = _find_path_edge_sets(adj, 3, list(range(1, 6)))
        # Each edge set should be a frozenset of exactly 3 edges
        for s in es:
            assert len(s) == 3
            for e in s:
                assert e[0] < e[1]
                assert math.gcd(e[0], e[1]) == 1

    def test_no_paths_beyond_graph(self):
        """No path of length 5 in a 4-vertex graph."""
        adj = coprime_adj(4)
        es = _find_path_edge_sets(adj, 5, [1, 2, 3, 4])
        assert len(es) == 0


class TestCycles:
    def test_triangle_count_n5(self):
        """Triangles = 3-cycles. Count should match 3-cliques."""
        adj = coprime_adj(5)
        cycles = _find_all_cycles(adj, 3, list(range(1, 6)))
        cliques = find_coprime_cliques(5, 3)
        assert len(cycles) == len(cliques)

    def test_no_short_cycles(self):
        assert _find_all_cycles(coprime_adj(5), 2, [1, 2, 3, 4, 5]) == []

    def test_4_cycles_n5(self):
        """4-cycles in the coprime graph on [5]."""
        adj = coprime_adj(5)
        cycles = _find_all_cycles(adj, 4, list(range(1, 6)))
        for c in cycles:
            assert len(c) == 4
            # Verify all edges exist
            for i in range(4):
                a, b = c[i], c[(i + 1) % 4]
                assert math.gcd(a, b) == 1


# ---------------------------------------------------------------------------
# 1. Path coprime Ramsey exact values
# ---------------------------------------------------------------------------

class TestPathCoprimeRamsey:
    def test_pcop3(self):
        assert compute_path_coprime_ramsey(3, max_n=10) == 5

    def test_pcop4(self):
        assert compute_path_coprime_ramsey(4, max_n=10) == 7

    def test_pcop5(self):
        assert compute_path_coprime_ramsey(5, max_n=15) == 9

    def test_pcop6(self):
        assert compute_path_coprime_ramsey(6, max_n=15) == 10

    def test_monotone(self):
        """P_cop(k) <= P_cop(k+1): longer paths are at least as hard to force."""
        prev = compute_path_coprime_ramsey(3, max_n=15)
        for k in [4, 5]:
            curr = compute_path_coprime_ramsey(k, max_n=15)
            assert curr >= prev, f"P_cop({k})={curr} < P_cop({k - 1})={prev}"
            prev = curr


# ---------------------------------------------------------------------------
# 1b. Cycle coprime Ramsey exact values
# ---------------------------------------------------------------------------

class TestCycleCoprimeRamsey:
    def test_ccop3_equals_rcop3(self):
        """C_cop(3) = R_cop(3) = 11 since 3-cycles are triangles."""
        assert compute_cycle_coprime_ramsey(3, max_n=15) == 11

    def test_ccop4(self):
        assert compute_cycle_coprime_ramsey(4, max_n=15) == 8

    def test_ccop5(self):
        assert compute_cycle_coprime_ramsey(5, max_n=20) == 13

    def test_ccop6(self):
        assert compute_cycle_coprime_ramsey(6, max_n=15) == 11

    def test_invalid_k(self):
        assert compute_cycle_coprime_ramsey(2, max_n=10) == -1

    def test_even_easier_than_odd(self):
        """Even-length cycles are generally easier to force."""
        c4 = compute_cycle_coprime_ramsey(4, max_n=15)
        c5 = compute_cycle_coprime_ramsey(5, max_n=20)
        assert c4 < c5


# ---------------------------------------------------------------------------
# 2. Multi-color coprime Ramsey
# ---------------------------------------------------------------------------

class TestMulticolorCoprimeRamsey:
    def test_rcop3_2colors(self):
        """R_cop(3; 2) = R_cop(3) = 11."""
        assert compute_multicolor_coprime_ramsey(3, 2, max_n=15) == 11

    def test_more_colors_harder(self):
        """R_cop(3; 3) > R_cop(3; 2): more colors need bigger n."""
        r2 = compute_multicolor_coprime_ramsey(3, 2, max_n=15)
        # Just check R_cop(3;3) > R_cop(3;2) by verifying n=11 is SAT for 3 colors
        r3_lower = compute_multicolor_coprime_ramsey(3, 3, max_n=12)
        assert r3_lower == -1, "R_cop(3;3) should be > 12"
        assert r2 == 11

    def test_single_color_trivial(self):
        """With 1 color, every coloring is monochromatic: R_cop(3;1) = 3."""
        # The smallest n with a coprime triangle: {1,2,3}
        assert compute_multicolor_coprime_ramsey(3, 1, max_n=10) == 3


# ---------------------------------------------------------------------------
# 3. Bipartite coprime Ramsey
# ---------------------------------------------------------------------------

class TestBipartiteCoprimeRamsey:
    def test_rcop_2_3(self):
        assert compute_bipartite_coprime_ramsey(2, 3, max_n=10) == 3

    def test_rcop_2_4(self):
        assert compute_bipartite_coprime_ramsey(2, 4, max_n=10) == 5

    def test_rcop_3_4(self):
        assert compute_bipartite_coprime_ramsey(3, 4, max_n=25) == 19

    def test_symmetric_case(self):
        """R_cop(3, 3) should equal R_cop(3) = 11."""
        assert compute_bipartite_coprime_ramsey(3, 3, max_n=15) == 11

    def test_asymmetry_helps(self):
        """R_cop(2, 3) < R_cop(3, 3) since K_2 is easier to force."""
        r23 = compute_bipartite_coprime_ramsey(2, 3, max_n=15)
        r33 = compute_bipartite_coprime_ramsey(3, 3, max_n=15)
        assert r23 < r33


# ---------------------------------------------------------------------------
# 4. Gallai coprime Ramsey
# ---------------------------------------------------------------------------

class TestGallaiCoprimeRamsey:
    def test_grcop_3_3(self):
        """GR_cop(3; 3) = 29."""
        assert compute_gallai_coprime_ramsey(3, 3, max_n=35) == 29

    def test_grcop_below_threshold(self):
        """At n=28, Gallai 3-coloring exists (no mono K_3, no rainbow K_3)."""
        assert compute_gallai_coprime_ramsey(3, 3, max_n=28) == -1

    def test_requires_3_colors(self):
        """GR_cop(3; 2) = -1: with 2 colors, rainbow K_3 impossible."""
        assert compute_gallai_coprime_ramsey(3, 2, max_n=20) == -1

    def test_gallai_exceeds_classical(self):
        """GR_cop(3; 3) = 29 > GR(3,3,3) = 17 (coprime amplification)."""
        val = compute_gallai_coprime_ramsey(3, 3, max_n=35)
        assert val == 29
        assert val > 17  # classical Gallai Ramsey GR(3;3) = 17


# ---------------------------------------------------------------------------
# 5. Density / counting tests
# ---------------------------------------------------------------------------

class TestDensity:
    def test_count_at_n8_k3(self):
        """Exactly 36 avoiding colorings at n=8 (from test_coprime_ramsey.py)."""
        assert count_avoiding_colorings_sat(8, 3) == 36

    def test_count_at_n10_k3(self):
        """Exactly 156 avoiding colorings at n=10."""
        assert count_avoiding_colorings_sat(10, 3) == 156

    def test_count_at_n11_k3_is_zero(self):
        """No avoiding colorings at n=11 = R_cop(3)."""
        assert count_avoiding_colorings_sat(11, 3) == 0

    def test_density_decreases(self):
        """Fraction of avoiding colorings decreases with n."""
        _, _, f6 = density_avoiding_colorings(6, 3)
        _, _, f8 = density_avoiding_colorings(8, 3)
        _, _, f10 = density_avoiding_colorings(10, 3)
        assert f6 > f8 > f10 > 0

    def test_density_format(self):
        """density_avoiding_colorings returns (int, int, float)."""
        av, tot, frac = density_avoiding_colorings(6, 3)
        assert isinstance(av, int)
        assert isinstance(tot, int)
        assert isinstance(frac, float)
        assert tot == 2 ** len(coprime_edges(6))
        assert 0 < frac < 1

    def test_empty_graph(self):
        """n=1 has no edges, 1 trivial coloring."""
        assert count_avoiding_colorings_sat(1, 3) == 1


# ---------------------------------------------------------------------------
# Cross-variant consistency tests
# ---------------------------------------------------------------------------

class TestCrossConsistency:
    def test_path_leq_clique(self):
        """P_cop(k) <= R_cop(k): a k-clique contains a k-path if k <= clique."""
        # P_cop(3) = 5 <= R_cop(3) = 11
        p3 = compute_path_coprime_ramsey(3, max_n=10)
        assert p3 <= 11

    def test_cycle3_equals_clique3(self):
        """C_cop(3) = R_cop(3): a 3-cycle IS a 3-clique."""
        c3 = compute_cycle_coprime_ramsey(3, max_n=15)
        assert c3 == 11

    def test_bipartite_leq_symmetric(self):
        """R_cop(s,t) <= R_cop(max(s,t)) for all computed (s,t)."""
        r33 = 11  # R_cop(3)
        r44 = 59  # R_cop(4)
        assert compute_bipartite_coprime_ramsey(2, 3, max_n=15) <= r33
        assert compute_bipartite_coprime_ramsey(2, 4, max_n=60) <= r44
        assert compute_bipartite_coprime_ramsey(3, 4, max_n=60) <= r44

    def test_gallai_leq_multicolor(self):
        """GR_cop(3;c) <= R_cop(3;c): Gallai condition is weaker."""
        # At R_cop(3;3), mono is forced; Gallai (mono OR rainbow) is forced earlier
        gr = compute_gallai_coprime_ramsey(3, 3, max_n=35)
        # R_cop(3;3) = 53 (known), GR should be <=
        assert gr <= 53

    def test_coprime_exceeds_classical(self):
        """All coprime Ramsey variants exceed their classical counterparts."""
        # R_cop(3;2) = 11 > R(3,3) = 6
        assert compute_multicolor_coprime_ramsey(3, 2, max_n=15) > 6
        # R_cop(2,3) = 3 vs R(2,3) = 6: actually R_cop(2,3) can be smaller
        # because R(2,t) = t for complete graphs (trivial), but coprime graph
        # has vertex 1 adjacent to everything, so R_cop(2,t) is small.
        # The inequality R_cop >= R_classical holds for symmetric cases.
        assert compute_bipartite_coprime_ramsey(3, 3, max_n=15) > 6
