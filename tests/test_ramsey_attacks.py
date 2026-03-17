"""Tests for ramsey_attacks.py — Ramsey theory and graph coloring attacks."""

import math
import sys
from itertools import combinations
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ramsey_attacks import (
    KNOWN_RAMSEY,
    RAMSEY_BOUNDS,
    complete_graph_edges,
    ramsey_sat_check,
    RamseySATEncoder,
    compute_ramsey_sat,
    verify_known_ramsey,
    ramsey_lower_bound_coloring,
    coprime_graph_edges,
    coprime_graph_adjacency,
    find_coprime_cliques,
    coprime_ramsey_multicolor_sat,
    compute_coprime_ramsey_multicolor,
    coprime_ramsey_k4_lower_bound,
    kneser_graph_edges,
    kneser_graph_vertex_list,
    kneser_chromatic_number_theoretical,
    greedy_coloring,
    chromatic_number_sat,
    kneser_chromatic_number_computed,
    cayley_graph_cyclic,
    cayley_circulant_chromatic,
    cayley_distance_graph,
    petersen_kneser_family,
    circulant_chromatic_sweep,
    ramsey_number_table,
)


# ======================================================================
# Part 1: Classical Ramsey via SAT
# ======================================================================

class TestCompleteGraphEdges:
    def test_k1_no_edges(self):
        assert complete_graph_edges(1) == []

    def test_k2_single_edge(self):
        edges = complete_graph_edges(2)
        assert edges == [(0, 1)]

    def test_k3_triangle(self):
        edges = complete_graph_edges(3)
        assert len(edges) == 3
        assert (0, 1) in edges
        assert (0, 2) in edges
        assert (1, 2) in edges

    def test_k4_edge_count(self):
        edges = complete_graph_edges(4)
        assert len(edges) == 6  # C(4,2) = 6

    def test_kn_edge_count(self):
        for n in range(1, 8):
            edges = complete_graph_edges(n)
            assert len(edges) == n * (n - 1) // 2


class TestRamseySATCheck:
    def test_r33_at_5_is_sat(self):
        """R(3,3) = 6, so n=5 should be SAT (avoiding coloring exists)."""
        sat, coloring = ramsey_sat_check(5, 3, 3)
        assert sat
        assert coloring is not None

    def test_r33_at_6_is_unsat(self):
        """R(3,3) = 6, so n=6 should be UNSAT (every coloring forced)."""
        sat, coloring = ramsey_sat_check(6, 3, 3)
        assert not sat
        assert coloring is None

    def test_r34_at_8_is_sat(self):
        """R(3,4) = 9, so n=8 should be SAT."""
        sat, coloring = ramsey_sat_check(8, 3, 4)
        assert sat

    def test_r34_at_9_is_unsat(self):
        """R(3,4) = 9, so n=9 should be UNSAT."""
        sat, coloring = ramsey_sat_check(9, 3, 4)
        assert not sat

    def test_n1_trivially_sat(self):
        """n=1 has no edges, always SAT."""
        sat, coloring = ramsey_sat_check(1, 3, 3)
        assert sat

    def test_coloring_is_valid_at_sat(self):
        """When SAT, the returned coloring should be a valid avoiding coloring."""
        sat, coloring = ramsey_sat_check(5, 3, 3)
        assert sat
        # Check all color values are 0 or 1.
        for edge, c in coloring.items():
            assert c in (0, 1)
        # Check no monochromatic K_3 in color 0.
        for triple in ((0, 1, 2), (0, 1, 3), (0, 1, 4), (0, 2, 3),
                       (0, 2, 4), (0, 3, 4), (1, 2, 3), (1, 2, 4),
                       (1, 3, 4), (2, 3, 4)):
            edges = [(triple[i], triple[j])
                     for i in range(3) for j in range(i + 1, 3)]
            colors = {coloring[e] for e in edges}
            assert len(colors) > 1 or 0 not in colors or 1 not in colors
            # Actually: must NOT have all color 0 AND must NOT have all color 1.
            # But they can all be same color if that doesn't violate either constraint.
            # For R(3,3): both s=t=3, so neither color can have K_3.
            assert colors != {0}, f"Monochromatic K_3 in color 0: {triple}"
            assert colors != {1}, f"Monochromatic K_3 in color 1: {triple}"


class TestComputeRamseySAT:
    def test_r22(self):
        assert compute_ramsey_sat(2, 2) == 2

    def test_r23(self):
        assert compute_ramsey_sat(2, 3) == 3

    def test_r33(self):
        assert compute_ramsey_sat(3, 3, max_n=10) == 6

    def test_r34(self):
        assert compute_ramsey_sat(3, 4, max_n=12) == 9

    def test_r44_lower_bound(self):
        """R(4,4) = 18: verify an avoiding coloring exists at n=10.
        The SAT instance at n=17 and UNSAT proof at n=18 are expensive
        for basic CDCL encoding. We verify an intermediate lower bound."""
        sat, coloring = ramsey_sat_check(10, 4, 4)
        assert sat
        assert coloring is not None
        # Validate witness: no monochromatic K_4 in either color.
        for q in combinations(range(10), 4):
            edges = [(q[i], q[j]) for i in range(4) for j in range(i + 1, 4)]
            colors = {coloring[e] for e in edges}
            assert colors != {0}, f"Mono K_4 color 0: {q}"
            assert colors != {1}, f"Mono K_4 color 1: {q}"

    def test_not_found_if_max_n_too_small(self):
        result = compute_ramsey_sat(3, 3, max_n=4)
        assert result == -1


class TestVerifyKnownRamsey:
    def test_r33_and_r34(self):
        results = verify_known_ramsey(max_s=3, max_t=4)
        assert (3, 3) in results
        assert results[(3, 3)]["match"]
        assert (3, 4) in results
        assert results[(3, 4)]["match"]

    def test_r35_lower_bound(self):
        """R(3,5) = 14: verify an avoiding coloring exists at n=13.
        The UNSAT proof at n=14 is computationally expensive for basic
        CDCL encoding and not suitable for CI tests."""
        sat, coloring = ramsey_sat_check(13, 3, 5)
        assert sat
        assert coloring is not None


class TestRamseySATEncoder:
    def test_incremental_r33(self):
        """Incremental encoder should find R(3,3) = 6."""
        enc = RamseySATEncoder(3, 3)
        assert enc.extend_to(5)   # SAT at n=5
        assert not enc.extend_to(6)  # UNSAT at n=6
        enc.close()

    def test_incremental_r34(self):
        """Incremental encoder should find R(3,4) = 9."""
        enc = RamseySATEncoder(3, 4)
        assert enc.extend_to(8)   # SAT at n=8
        assert not enc.extend_to(9)  # UNSAT at n=9
        enc.close()

    def test_incremental_agrees_with_oneshot(self):
        """Incremental and one-shot should agree on SAT/UNSAT for R(3,3)."""
        enc = RamseySATEncoder(3, 3)
        for n in range(3, 8):
            inc_sat = enc.extend_to(n)
            os_sat, _ = ramsey_sat_check(n, 3, 3)
            assert inc_sat == os_sat, f"Mismatch at n={n}"
        enc.close()


class TestRamseyLowerBoundColoring:
    def test_exists_at_5_for_r33(self):
        coloring = ramsey_lower_bound_coloring(5, 3, 3)
        assert coloring is not None

    def test_none_at_6_for_r33(self):
        coloring = ramsey_lower_bound_coloring(6, 3, 3)
        assert coloring is None


# ======================================================================
# Part 2: Coprime Ramsey extensions
# ======================================================================

class TestCoprimeGraphEdges:
    def test_n1_empty(self):
        assert coprime_graph_edges(1) == []

    def test_n2(self):
        assert coprime_graph_edges(2) == [(1, 2)]

    def test_n4_excludes_2_4(self):
        edges = coprime_graph_edges(4)
        assert (2, 4) not in edges
        assert (1, 4) in edges
        assert (3, 4) in edges

    def test_count_matches_direct(self):
        for n in range(1, 15):
            edges = coprime_graph_edges(n)
            expected = sum(1 for i in range(1, n + 1)
                           for j in range(i + 1, n + 1)
                           if math.gcd(i, j) == 1)
            assert len(edges) == expected


class TestCoprimeGraphAdjacency:
    def test_symmetric(self):
        adj = coprime_graph_adjacency(10)
        for v, neighbors in adj.items():
            for u in neighbors:
                assert v in adj[u]

    def test_n4_structure(self):
        adj = coprime_graph_adjacency(4)
        # 1 is coprime with everything.
        assert adj[1] == {2, 3, 4}
        # 2 and 4 are NOT coprime.
        assert 4 not in adj[2]
        assert 2 not in adj[4]
        # 3 and 4 are coprime.
        assert 4 in adj[3]


class TestFindCoprimeCliques:
    def test_triangles_n5(self):
        cliques = find_coprime_cliques(5, 3)
        assert len(cliques) > 0
        for c in cliques:
            assert len(c) == 3
            for i in range(3):
                for j in range(i + 1, 3):
                    assert math.gcd(c[i], c[j]) == 1

    def test_edges_match(self):
        for n in [4, 6, 8]:
            cliques = find_coprime_cliques(n, 2)
            edges = coprime_graph_edges(n)
            assert len(cliques) == len(edges)

    def test_k1(self):
        assert len(find_coprime_cliques(5, 1)) == 5

    def test_k0(self):
        assert find_coprime_cliques(5, 0) == []


class TestCoprimeRamseyMulticolorSAT:
    def test_2color_k3_at_10_sat(self):
        """R_cop(3) = 11, so n=10 with 2 colors should be SAT."""
        sat, coloring = coprime_ramsey_multicolor_sat(10, 3, 2)
        assert sat
        assert coloring is not None

    def test_2color_k3_at_11_unsat(self):
        """R_cop(3) = 11, so n=11 with 2 colors should be UNSAT."""
        sat, coloring = coprime_ramsey_multicolor_sat(11, 3, 2)
        assert not sat

    def test_3color_k3_at_11_sat(self):
        """With 3 colors, n=11 should be SAT (more colors = easier to avoid)."""
        sat, coloring = coprime_ramsey_multicolor_sat(11, 3, 3)
        assert sat

    def test_coloring_valid_values(self):
        """Returned coloring should have valid color values."""
        sat, coloring = coprime_ramsey_multicolor_sat(8, 3, 3)
        assert sat
        for edge, c in coloring.items():
            assert c in (0, 1, 2)

    def test_multicolor_coloring_avoids_monochromatic(self):
        """Verify the returned 3-coloring has no monochromatic K_3."""
        sat, coloring = coprime_ramsey_multicolor_sat(10, 3, 3)
        assert sat
        cliques = find_coprime_cliques(10, 3)
        for clique in cliques:
            vlist = sorted(clique)
            edge_colors = set()
            for i in range(len(vlist)):
                for j in range(i + 1, len(vlist)):
                    e = (vlist[i], vlist[j])
                    edge_colors.add(coloring[e])
            assert len(edge_colors) > 1, f"Monochromatic K_3: {clique}"

    def test_no_edges_trivially_sat(self):
        """n=1 has no coprime edges; any coloring trivially avoids K_k."""
        sat, coloring = coprime_ramsey_multicolor_sat(1, 3, 2)
        assert sat


class TestComputeCoprimeRamseyMulticolor:
    def test_2color_k3_is_11(self):
        """R_cop(3; 2 colors) = 11."""
        result = compute_coprime_ramsey_multicolor(3, 2, max_n=15)
        assert result == 11

    def test_3color_k3_larger_than_20(self):
        """R_cop(3; 3 colors) > 20: with 3 colors, we can still avoid
        monochromatic K_3 on coprime edges up to at least n=20.
        (Classical R(3,3,3) = 17 on the complete graph, but the coprime
        graph is sparser, so R_cop(3; 3col) > 20.)"""
        sat, _ = coprime_ramsey_multicolor_sat(20, 3, 3)
        assert sat

    def test_not_found_small_max(self):
        """With max_n=8, R_cop(3) = 11 is not found."""
        result = compute_coprime_ramsey_multicolor(3, 2, max_n=8)
        assert result == -1

    def test_2color_k2_is_2(self):
        """R_cop(2; 2 colors) = 2: any single coprime edge forces mono K_2."""
        result = compute_coprime_ramsey_multicolor(2, 2, max_n=5)
        assert result == 2


class TestCoprimeRamseyK4LowerBound:
    def test_lower_bound_at_least_10(self):
        """R_cop(4) > 10 at minimum (coprime graph on [10] has many 4-cliques
        but 2-coloring can still avoid monochromatic K_4)."""
        lb = coprime_ramsey_k4_lower_bound(max_n=12)
        assert lb >= 10


# ======================================================================
# Part 3: Graph coloring
# ======================================================================

class TestKneserGraph:
    def test_petersen_graph(self):
        """KG(5,2) is the Petersen graph: 10 vertices, 15 edges."""
        verts = kneser_graph_vertex_list(5, 2)
        assert len(verts) == 10  # C(5,2)
        edges = kneser_graph_edges(5, 2)
        assert len(edges) == 15

    def test_kneser_vertex_count(self):
        """KG(n,k) has C(n,k) vertices."""
        for n, k in [(4, 1), (4, 2), (5, 2), (6, 2), (6, 3)]:
            verts = kneser_graph_vertex_list(n, k)
            expected = math.comb(n, k)
            assert len(verts) == expected

    def test_kneser_edges_disjoint(self):
        """All edges connect disjoint sets."""
        edges = kneser_graph_edges(5, 2)
        for a, b in edges:
            assert not a & b

    def test_no_edges_when_n_lt_2k(self):
        """KG(3,2): all 2-subsets of {0,1,2} overlap."""
        edges = kneser_graph_edges(3, 2)
        assert len(edges) == 0


class TestKneserChromaticTheoretical:
    def test_petersen_chi_3(self):
        assert kneser_chromatic_number_theoretical(5, 2) == 3

    def test_kg_n_1(self):
        """KG(n,1) = K_n, so chi = n."""
        for n in range(2, 7):
            assert kneser_chromatic_number_theoretical(n, 1) == n

    def test_edgeless_when_small(self):
        """n < 2k: no edges, chi = 1."""
        assert kneser_chromatic_number_theoretical(3, 2) == 1

    def test_odd_graph(self):
        """Odd graph O_k = KG(2k-1,k-1) has chi = 3 for k >= 2."""
        # O_2 = KG(3,1) = K_3, chi=3
        assert kneser_chromatic_number_theoretical(3, 1) == 3
        # O_3 = KG(5,2), chi=3
        assert kneser_chromatic_number_theoretical(5, 2) == 3
        # O_4 = KG(7,3), chi=3
        assert kneser_chromatic_number_theoretical(7, 3) == 3


class TestGreedyColoring:
    def test_triangle(self):
        adj = {0: {1, 2}, 1: {0, 2}, 2: {0, 1}}
        coloring = greedy_coloring(adj, [0, 1, 2])
        # Need 3 colors for triangle.
        assert len(set(coloring.values())) == 3

    def test_bipartite(self):
        # Path 0-1-2.
        adj = {0: {1}, 1: {0, 2}, 2: {1}}
        coloring = greedy_coloring(adj, [0, 1, 2])
        assert len(set(coloring.values())) <= 2

    def test_empty_graph(self):
        adj = {0: set(), 1: set(), 2: set()}
        coloring = greedy_coloring(adj, [0, 1, 2])
        assert all(c == 0 for c in coloring.values())

    def test_valid_coloring(self):
        """No adjacent vertices share a color."""
        adj = {0: {1, 2}, 1: {0, 3}, 2: {0, 3}, 3: {1, 2}}
        coloring = greedy_coloring(adj, [0, 1, 2, 3])
        for v, neighbors in adj.items():
            for u in neighbors:
                assert coloring[v] != coloring[u]


class TestChromaticNumberSAT:
    def test_triangle_chi_3(self):
        adj = {0: {1, 2}, 1: {0, 2}, 2: {0, 1}}
        chi = chromatic_number_sat(adj, [0, 1, 2], 5)
        assert chi == 3

    def test_path_chi_2(self):
        adj = {0: {1}, 1: {0, 2}, 2: {1}}
        chi = chromatic_number_sat(adj, [0, 1, 2], 5)
        assert chi == 2

    def test_single_vertex_chi_1(self):
        adj = {0: set()}
        chi = chromatic_number_sat(adj, [0], 5)
        assert chi == 1

    def test_k4_chi_4(self):
        adj = {i: set(range(4)) - {i} for i in range(4)}
        chi = chromatic_number_sat(adj, [0, 1, 2, 3], 6)
        assert chi == 4

    def test_cycle_5_chi_3(self):
        """C_5 (odd cycle) has chromatic number 3."""
        adj = {i: {(i - 1) % 5, (i + 1) % 5} for i in range(5)}
        chi = chromatic_number_sat(adj, list(range(5)), 5)
        assert chi == 3

    def test_cycle_6_chi_2(self):
        """C_6 (even cycle) has chromatic number 2."""
        adj = {i: {(i - 1) % 6, (i + 1) % 6} for i in range(6)}
        chi = chromatic_number_sat(adj, list(range(6)), 5)
        assert chi == 2


class TestKneserChromaticComputed:
    def test_petersen_chi_3(self):
        """KG(5,2) = Petersen graph, chi = 3."""
        chi = kneser_chromatic_number_computed(5, 2)
        assert chi == 3

    def test_kg_4_1_is_k4(self):
        """KG(4,1) = K_4, chi = 4."""
        chi = kneser_chromatic_number_computed(4, 1)
        assert chi == 4

    def test_edgeless_chi_1(self):
        """KG(3,2) is edgeless, chi = 1."""
        chi = kneser_chromatic_number_computed(3, 2)
        assert chi == 1

    def test_matches_lovasz(self):
        """Computed chi matches Lovász bound for small parameters."""
        for n, k in [(4, 1), (5, 1), (5, 2), (6, 2)]:
            computed = kneser_chromatic_number_computed(n, k)
            theoretical = kneser_chromatic_number_theoretical(n, k)
            assert computed == theoretical, \
                f"KG({n},{k}): computed={computed}, theoretical={theoretical}"


class TestCayleyGraph:
    def test_cycle_graph(self):
        """Cay(Z/nZ, {1, n-1}) is the cycle C_n."""
        for n in range(3, 8):
            adj = cayley_graph_cyclic(n, {1, n - 1})
            for v in range(n):
                assert len(adj[v]) == 2
                assert (v + 1) % n in adj[v]
                assert (v - 1) % n in adj[v]

    def test_complete_graph(self):
        """Cay(Z/nZ, {1,2,...,n-1}) = K_n."""
        n = 5
        adj = cayley_graph_cyclic(n, set(range(1, n)))
        for v in range(n):
            assert len(adj[v]) == n - 1

    def test_symmetric(self):
        adj = cayley_graph_cyclic(10, {1, 3, 7, 9})
        for v, neighbors in adj.items():
            for u in neighbors:
                assert v in adj[u]


class TestCayleyCirculantChromatic:
    def test_cycle_odd(self):
        """Cay(Z/5Z, {1,4}) = C_5, chi = 3."""
        chi = cayley_circulant_chromatic(5, {1, 4}, max_colors=5)
        assert chi == 3

    def test_cycle_even(self):
        """Cay(Z/6Z, {1,5}) = C_6, chi = 2."""
        chi = cayley_circulant_chromatic(6, {1, 5}, max_colors=5)
        assert chi == 2


class TestCayleyDistanceGraph:
    def test_distance_1_is_cycle(self):
        """Distance graph with D={1} on Z/nZ is the cycle C_n."""
        for n in range(3, 8):
            adj = cayley_distance_graph(n, {1})
            for v in range(n):
                assert len(adj[v]) == 2

    def test_distance_graph_symmetric(self):
        adj = cayley_distance_graph(10, {1, 3})
        for v, neighbors in adj.items():
            for u in neighbors:
                assert v in adj[u]


class TestPetersenKneserFamily:
    def test_returns_results(self):
        results = petersen_kneser_family(max_n=6)
        assert len(results) > 0

    def test_all_match_lovasz(self):
        """All computed values should match the theoretical Lovász bound."""
        results = petersen_kneser_family(max_n=7)
        for r in results:
            assert r["match"], \
                f"KG({r['n']},{r['k']}): computed={r['computed_chi']} != theory={r['theoretical_chi']}"

    def test_contains_petersen(self):
        """Should include the Petersen graph KG(5,2)."""
        results = petersen_kneser_family(max_n=6)
        petersen = [r for r in results if r["n"] == 5 and r["k"] == 2]
        assert len(petersen) == 1
        assert petersen[0]["computed_chi"] == 3


class TestCirculantChromaticSweep:
    def test_returns_results(self):
        results = circulant_chromatic_sweep(range(5, 10), [{1}])
        assert len(results) > 0

    def test_chi_at_least_2(self):
        """All distance graphs with nonempty D should have chi >= 2."""
        results = circulant_chromatic_sweep(range(5, 10), [{1}, {1, 2}])
        for r in results:
            assert r["chi"] >= 2


class TestRamseyNumberTable:
    def test_r33_in_table(self):
        table = ramsey_number_table(max_s=3, max_t=4)
        r33 = [r for r in table if r["s"] == 3 and r["t"] == 3]
        assert len(r33) == 1
        assert r33[0]["match"]
        assert r33[0]["computed"] == 6

    def test_r34_in_table(self):
        table = ramsey_number_table(max_s=3, max_t=4)
        r34 = [r for r in table if r["s"] == 3 and r["t"] == 4]
        assert len(r34) == 1
        assert r34[0]["match"]
        assert r34[0]["computed"] == 9


# ======================================================================
# Edge cases and integration
# ======================================================================

class TestEdgeCases:
    def test_ramsey_sat_empty_graph(self):
        """n=0 has no edges."""
        sat, coloring = ramsey_sat_check(0, 3, 3)
        assert sat

    def test_coprime_multicolor_1_color_always_unsat_for_k2(self):
        """With 1 color, any edge is monochromatic, so UNSAT at n >= 2."""
        sat, _ = coprime_ramsey_multicolor_sat(3, 2, 1)
        assert not sat

    def test_coprime_multicolor_many_colors_sat(self):
        """With enough colors, can always avoid monochromatic cliques."""
        # 10 colors, k=3, n=10 — trivially avoidable.
        sat, _ = coprime_ramsey_multicolor_sat(10, 3, 10)
        assert sat

    def test_kneser_empty_vertex_list(self):
        """KG(0,1) has no vertices."""
        verts = kneser_graph_vertex_list(0, 1)
        assert len(verts) == 0

    def test_greedy_coloring_single_vertex(self):
        adj = {0: set()}
        coloring = greedy_coloring(adj, [0])
        assert coloring == {0: 0}

    def test_chromatic_number_sat_no_edges(self):
        """Edgeless graph on 5 vertices has chi = 1."""
        adj = {i: set() for i in range(5)}
        chi = chromatic_number_sat(adj, list(range(5)), 5)
        assert chi == 1


class TestConsistencyWithExistingCode:
    """Ensure our coprime graph functions agree with coprime_ramsey.py."""

    def test_edges_match_original(self):
        from coprime_ramsey import coprime_edges as original_edges
        for n in range(1, 15):
            ours = coprime_graph_edges(n)
            theirs = original_edges(n)
            assert ours == theirs, f"Edge mismatch at n={n}"

    def test_cliques_match_original(self):
        from coprime_ramsey_sat import find_coprime_cliques as original_cliques
        for n in [5, 8, 10]:
            ours = sorted(find_coprime_cliques(n, 3))
            theirs = sorted(original_cliques(n, 3))
            assert ours == theirs, f"Clique mismatch at n={n}"

    def test_rcop3_agrees_with_sat_module(self):
        """Our multi-color SAT with 2 colors matches the dedicated SAT solver."""
        from coprime_ramsey_sat import compute_rcop_sat
        our_result = compute_coprime_ramsey_multicolor(3, 2, max_n=15)
        their_result = compute_rcop_sat(3, max_n=15, verbose=False)
        assert our_result == their_result == 11
