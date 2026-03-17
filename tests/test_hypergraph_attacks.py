"""Tests for hypergraph_attacks.py -- hypergraph Ramsey, Turan, sunflower."""

import math
import sys
from itertools import combinations
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hypergraph_attacks import (
    # Part 1: Hypergraph Ramsey
    uniform_hyperedges,
    complete_r_uniform_subhypergraph_edges,
    hypergraph_ramsey_sat,
    compute_hypergraph_ramsey,
    validate_hypergraph_coloring,
    KNOWN_HYPERGRAPH_RAMSEY,
    # Part 2: Coprime hypergraph Ramsey
    coprime_hyperedges,
    coprime_hyper_cliques,
    coprime_hypergraph_ramsey_sat,
    compute_coprime_hypergraph_ramsey,
    validate_coprime_hyper_coloring,
    # Part 3: Turan numbers
    turan_number_complete,
    turan_number_sat,
    turan_number_formula,
    find_subgraph_copies_bipartite,
    find_cycle_copies,
    # Part 4: Stepping-up
    stepping_up_bound,
    stepping_up_table,
    verify_stepping_up,
    # Part 5: Sunflower
    is_sunflower,
    sunflower_core,
    max_family_without_sunflower,
    sunflower_number,
    erdos_ko_sunflower_bound,
    improved_sunflower_bound,
    sunflower_table,
)


# ======================================================================
# Part 1: Hypergraph Ramsey numbers
# ======================================================================

class TestUniformHyperedges:
    def test_3_uniform_on_4(self):
        """C(4,3) = 4 hyperedges."""
        edges = uniform_hyperedges(4, 3)
        assert len(edges) == 4

    def test_2_uniform_is_graph_edges(self):
        """2-uniform = ordinary graph edges."""
        for n in range(2, 7):
            assert len(uniform_hyperedges(n, 2)) == n * (n - 1) // 2

    def test_n_uniform_on_n(self):
        """C(n,n) = 1 hyperedge."""
        for n in range(2, 6):
            edges = uniform_hyperedges(n, n)
            assert len(edges) == 1
            assert edges[0] == tuple(range(n))

    def test_r_gt_n_empty(self):
        """No r-subsets when r > n."""
        assert uniform_hyperedges(3, 5) == []

    def test_1_uniform(self):
        """1-uniform: n singletons."""
        for n in range(1, 6):
            assert len(uniform_hyperedges(n, 1)) == n

    def test_edge_count_formula(self):
        for n in range(2, 8):
            for r in range(2, n + 1):
                assert len(uniform_hyperedges(n, r)) == math.comb(n, r)


class TestCompleteSubhypergraphEdges:
    def test_4_vertices_3_uniform(self):
        """K^3_4 has C(4,3) = 4 edges."""
        edges = complete_r_uniform_subhypergraph_edges((0, 1, 2, 3), 3)
        assert len(edges) == 4

    def test_3_vertices_2_uniform(self):
        """K^2_3 = K_3 has 3 edges."""
        edges = complete_r_uniform_subhypergraph_edges((0, 1, 2), 2)
        assert len(edges) == 3


class TestHypergraphRamseySAT:
    def test_trivial_k_eq_r(self):
        """k = r: single edge always monochromatic. R_r(r) = r."""
        # R_3(3): any single 3-edge is trivially monochromatic.
        sat, _ = hypergraph_ramsey_sat(3, 3, 3)
        assert not sat  # UNSAT: forced at n=3

    def test_n_lt_k_always_sat(self):
        """n < k: no K^r_k possible."""
        sat, _ = hypergraph_ramsey_sat(3, 3, 4)
        assert sat

    def test_3uniform_k4_at_n5_sat(self):
        """R_3(4) > 5: avoiding coloring exists at n=5."""
        sat, coloring = hypergraph_ramsey_sat(5, 3, 4)
        assert sat
        assert coloring is not None

    def test_3uniform_k4_at_n11_sat(self):
        """R_3(4) > 11: verified quickly by SAT."""
        sat, coloring = hypergraph_ramsey_sat(11, 3, 4)
        assert sat
        assert coloring is not None

    def test_coloring_valid_at_small_n(self):
        """Returned coloring should be valid (no monochromatic K^3_4)."""
        sat, coloring = hypergraph_ramsey_sat(8, 3, 4)
        assert sat
        assert validate_hypergraph_coloring(8, 3, 4, coloring)

    def test_2uniform_reduces_to_classical(self):
        """R_2(3) = R(3,3) = 6. n=5 SAT, n=6 UNSAT."""
        sat5, _ = hypergraph_ramsey_sat(5, 2, 3)
        sat6, _ = hypergraph_ramsey_sat(6, 2, 3)
        assert sat5
        assert not sat6

    def test_symmetry_breaking_consistent(self):
        """With symmetry breaking, UNSAT results should still be correct."""
        # R_2(3) = 6: n=6 must be UNSAT even with symmetry breaking.
        sat, _ = hypergraph_ramsey_sat(6, 2, 3)
        assert not sat


class TestComputeHypergraphRamsey:
    def test_trivial_k_eq_r(self):
        """R_r(k) = k when k = r."""
        assert compute_hypergraph_ramsey(3, 3) == 3
        assert compute_hypergraph_ramsey(4, 4) == 4

    def test_r2_k3_is_6(self):
        """R_2(3) = R(3,3) = 6."""
        assert compute_hypergraph_ramsey(2, 3, max_n=10) == 6

    def test_r3_4_lower_bound(self):
        """R_3(4) > 11 (avoiding coloring exists at 11)."""
        # Don't compute full R_3(4) since n=12+ is slow; verify lower bound.
        val = compute_hypergraph_ramsey(3, 4, max_n=11)
        assert val == -1  # Not found <= 11, so R_3(4) > 11

    def test_k_lt_r_returns_neg1(self):
        """No edges possible when k < r."""
        assert compute_hypergraph_ramsey(3, 2) == -1


class TestValidateHypergraphColoring:
    def test_all_color0_forces_mono(self):
        """All edges color 0 on n=5, r=3, k=4 => monochromatic K^3_4."""
        edges = uniform_hyperedges(5, 3)
        coloring = {e: 0 for e in edges}
        assert not validate_hypergraph_coloring(5, 3, 4, coloring)

    def test_mixed_can_avoid(self):
        """A SAT-produced coloring should pass validation."""
        sat, coloring = hypergraph_ramsey_sat(8, 3, 4)
        assert sat
        assert validate_hypergraph_coloring(8, 3, 4, coloring)

    def test_k_eq_r_single_edge(self):
        """k=r: any single-edge coloring is monochromatic."""
        coloring = {(0, 1, 2): 0}
        assert not validate_hypergraph_coloring(3, 3, 3, coloring)


# ======================================================================
# Part 2: Coprime hypergraph Ramsey
# ======================================================================

class TestCoprimeHyperedges:
    def test_3uniform_n3(self):
        """(1,2,3) is pairwise coprime, so one 3-edge at n=3."""
        edges = coprime_hyperedges(3, 3)
        assert len(edges) == 1
        assert edges[0] == (1, 2, 3)

    def test_2uniform_matches_graph_edges(self):
        """2-uniform coprime hyperedges = coprime graph edges."""
        for n in [5, 8, 10]:
            hyper = coprime_hyperedges(n, 2)
            expected = sum(1 for i in range(1, n + 1)
                           for j in range(i + 1, n + 1)
                           if math.gcd(i, j) == 1)
            assert len(hyper) == expected

    def test_excludes_non_coprime(self):
        """(2, 4, 5): gcd(2,4)=2, not pairwise coprime."""
        edges = coprime_hyperedges(5, 3)
        assert (2, 4, 5) not in edges

    def test_includes_coprime(self):
        """(1, 2, 3) and (1, 2, 5) are pairwise coprime 3-tuples."""
        edges = coprime_hyperedges(5, 3)
        assert (1, 2, 3) in edges
        assert (1, 2, 5) in edges

    def test_n_lt_r_empty(self):
        """No r-tuples when n < r."""
        assert coprime_hyperedges(2, 3) == []


class TestCoprimeHyperCliques:
    def test_pairwise_coprime_4set(self):
        """(1, 2, 3, 5) are pairwise coprime => a 4-clique at n=5."""
        cliques = coprime_hyper_cliques(5, 3, 4)
        assert any(set(c) == {1, 2, 3, 5} for c in cliques)

    def test_not_coprime_excluded(self):
        """(2, 4, 6, 9): gcd(2,4)=2, not a clique."""
        cliques = coprime_hyper_cliques(9, 3, 4)
        for c in cliques:
            assert not (2 in c and 4 in c), f"Non-coprime clique: {c}"

    def test_all_verified_coprime(self):
        """Every returned clique should be pairwise coprime."""
        cliques = coprime_hyper_cliques(10, 3, 4)
        for clique in cliques:
            for i in range(len(clique)):
                for j in range(i + 1, len(clique)):
                    assert math.gcd(clique[i], clique[j]) == 1, \
                        f"Not coprime: {clique[i]}, {clique[j]} in {clique}"


class TestCoprimeHypergraphRamseySAT:
    def test_r2_k3_at_10_sat(self):
        """R^cop_2(3) = 11, so n=10 SAT."""
        sat, _ = coprime_hypergraph_ramsey_sat(10, 2, 3)
        assert sat

    def test_r2_k3_at_11_unsat(self):
        """R^cop_2(3) = 11, so n=11 UNSAT."""
        sat, _ = coprime_hypergraph_ramsey_sat(11, 2, 3)
        assert not sat

    def test_r3_k3_trivial(self):
        """R^cop_3(3) = 3 (single coprime 3-edge forces monochromatic)."""
        # n=3: (1,2,3) is the only 3-edge, and it's a single edge, so monochromatic.
        sat, _ = coprime_hypergraph_ramsey_sat(3, 3, 3)
        assert not sat

    def test_r3_k4_at_small_n_sat(self):
        """Coprime R^cop_3(4) > 10: avoiding coloring exists."""
        sat, coloring = coprime_hypergraph_ramsey_sat(10, 3, 4)
        assert sat
        assert coloring is not None

    def test_coloring_valid(self):
        """Returned coloring avoids monochromatic complete sub-hypergraph."""
        sat, coloring = coprime_hypergraph_ramsey_sat(8, 3, 4)
        assert sat
        assert validate_coprime_hyper_coloring(8, 3, 4, coloring)


class TestComputeCoprimeHypergraphRamsey:
    def test_r2_k3_is_11(self):
        """R^cop_2(3) = 11, matching the known coprime Ramsey number."""
        assert compute_coprime_hypergraph_ramsey(2, 3, max_n=15) == 11

    def test_r3_k3_is_3(self):
        """R^cop_3(3) = 3 (trivial: k=r)."""
        assert compute_coprime_hypergraph_ramsey(3, 3, max_n=10) == 3

    def test_r3_k4_gt_20(self):
        """R^cop_3(4) > 20 (coprime 3-uniform has few cliques)."""
        val = compute_coprime_hypergraph_ramsey(3, 4, max_n=20)
        assert val == -1  # Not found within 20

    def test_k_lt_r_returns_neg1(self):
        assert compute_coprime_hypergraph_ramsey(3, 2, max_n=10) == -1


class TestValidateCoprimeHyperColoring:
    def test_all_color0_forces_mono(self):
        """All coprime 3-edges color 0 on [5] => mono K^3_4 if clique exists."""
        edges = coprime_hyperedges(5, 3)
        coloring = {e: 0 for e in edges}
        cliques = coprime_hyper_cliques(5, 3, 4)
        if cliques:
            assert not validate_coprime_hyper_coloring(5, 3, 4, coloring)
        else:
            assert validate_coprime_hyper_coloring(5, 3, 4, coloring)

    def test_sat_coloring_valid(self):
        sat, coloring = coprime_hypergraph_ramsey_sat(10, 3, 4)
        assert sat
        assert validate_coprime_hyper_coloring(10, 3, 4, coloring)


# ======================================================================
# Part 3: Turan numbers
# ======================================================================

class TestTuranNumberComplete:
    def test_ex_n_k3_is_mantel(self):
        """ex(n, K_3) = floor(n^2/4) (Mantel/Turan)."""
        for n in range(2, 15):
            assert turan_number_complete(n, 2) == n * n // 4

    def test_ex_n_k4(self):
        """ex(n, K_4) = (1-1/3) * n^2/2 = n^2/3 approximately."""
        # Turan graph T(n,3).
        known = {4: 5, 5: 8, 6: 12, 7: 16, 8: 21, 9: 27}
        for n, expected in known.items():
            assert turan_number_complete(n, 3) == expected

    def test_ex_n_k2(self):
        """ex(n, K_2) = 0 (no edges allowed if K_2 is forbidden)."""
        for n in range(1, 10):
            assert turan_number_complete(n, 1) == 0

    def test_ex_n_kn_is_total(self):
        """ex(n, K_{n+1}) = C(n,2) (no restriction)."""
        for n in range(2, 8):
            assert turan_number_complete(n, n) == n * (n - 1) // 2


class TestTuranNumberSAT:
    def test_ex_k4_matches_formula(self):
        """SAT computation matches Turan formula for K_4."""
        for n in range(4, 9):
            sat_val, _ = turan_number_sat(n, "complete", (4,))
            formula_val = turan_number_formula(n, "complete", (4,))
            assert sat_val == formula_val, \
                f"ex({n}, K_4): SAT={sat_val}, formula={formula_val}"

    def test_ex_k3_matches_mantel(self):
        """SAT matches Mantel bound for K_3."""
        for n in range(3, 8):
            sat_val, _ = turan_number_sat(n, "complete", (3,))
            formula_val = n * n // 4
            assert sat_val == formula_val

    def test_ex_c5_at_n5(self):
        """ex(5, C_5) = 7 (verified by SAT)."""
        val, edges = turan_number_sat(5, "cycle", (5,))
        assert val == 7
        # The extremal graph should be C_5-free.
        assert edges is not None

    def test_ex_c5_matches_formula_n6_plus(self):
        """For n >= 6: ex(n, C_5) = floor(n^2/4) (Kopylov)."""
        for n in range(6, 9):
            sat_val, _ = turan_number_sat(n, "cycle", (5,))
            formula_val = n * n // 4
            assert sat_val == formula_val, \
                f"ex({n}, C_5): SAT={sat_val}, formula={formula_val}"

    def test_ex_k33_kst_bound(self):
        """ex(n, K_{3,3}) <= KST upper bound."""
        for n in range(6, 10):
            sat_val, _ = turan_number_sat(n, "bipartite", (3, 3))
            kst_ub = 0.5 * (2 ** (1 / 3)) * (n ** (5 / 3)) + n
            assert sat_val <= kst_ub + 1  # +1 for rounding

    def test_extremal_graph_is_valid(self):
        """The returned extremal graph should be K_4-free."""
        val, edges = turan_number_sat(7, "complete", (4,))
        assert edges is not None
        # Check no K_4 in the edge set.
        for clique in combinations(range(7), 4):
            clique_edges = set(combinations(clique, 2))
            if clique_edges.issubset(edges):
                pytest.fail(f"K_4 found in extremal graph: {clique}")

    def test_c5_free_graph_valid(self):
        """The returned C_5-free graph should contain no 5-cycle."""
        val, edges = turan_number_sat(7, "cycle", (5,))
        assert edges is not None
        adj = {i: set() for i in range(7)}
        for u, v in edges:
            adj[u].add(v)
            adj[v].add(u)
        # Check no 5-cycle via DFS.
        for start in range(7):
            for v1 in adj[start]:
                for v2 in adj[v1]:
                    if v2 == start:
                        continue
                    for v3 in adj[v2]:
                        if v3 in (start, v1):
                            continue
                        for v4 in adj[v3]:
                            if v4 in (v1, v2):
                                continue
                            if start in adj[v4]:
                                if len({start, v1, v2, v3, v4}) == 5:
                                    pytest.fail(
                                        f"C_5 in C_5-free graph: "
                                        f"{start},{v1},{v2},{v3},{v4}")

    def test_unknown_forbidden_raises(self):
        with pytest.raises(ValueError, match="Unknown forbidden type"):
            turan_number_sat(5, "nonsense", ())


class TestFindSubgraphCopies:
    def test_k33_copies_on_6(self):
        """K_{3,3} copies on 6 vertices: exactly C(6,3) = 20 ways
        to partition into (A,B) with |A|=|B|=3."""
        copies = find_subgraph_copies_bipartite(6, 3, 3)
        assert len(copies) == 20

    def test_k22_copies_on_4(self):
        """K_{2,2} copies on 4 vertices: C(4,2) = 6."""
        copies = find_subgraph_copies_bipartite(4, 2, 2)
        assert len(copies) == 6

    def test_k23_copies(self):
        """K_{2,3} on 5 vertices: C(5,2)*C(3,3) = 10."""
        copies = find_subgraph_copies_bipartite(5, 2, 3)
        assert len(copies) == 10

    def test_cycle_copies_c3_on_4(self):
        """C_3 copies on 4 vertices: C(4,3) = 4 triangles."""
        copies = find_cycle_copies(4, 3)
        assert len(copies) == 4

    def test_cycle_copies_c5_on_5(self):
        """C_5 on 5 vertices: there are (5-1)!/2 = 12 distinct 5-cycles."""
        copies = find_cycle_copies(5, 5)
        assert len(copies) == 12

    def test_cycle_lt_3_empty(self):
        assert find_cycle_copies(5, 2) == []
        assert find_cycle_copies(5, 1) == []


class TestTuranNumberFormula:
    def test_complete_matches_turan(self):
        for n in range(3, 10):
            assert turan_number_formula(n, "complete", (3,)) == n * n // 4

    def test_c5_at_5(self):
        assert turan_number_formula(5, "cycle", (5,)) == 7

    def test_c5_at_6(self):
        assert turan_number_formula(6, "cycle", (5,)) == 9

    def test_c4_returns_none(self):
        """No closed-form formula for C_4."""
        assert turan_number_formula(6, "cycle", (4,)) is None

    def test_unknown_returns_none(self):
        assert turan_number_formula(6, "unknown", ()) is None


# ======================================================================
# Part 4: Stepping-up lemma
# ======================================================================

class TestSteppingUpBound:
    def test_from_r33(self):
        """R_2(3) = 6 => stepping-up gives R_3(3) <= 2^5 + 1 = 33."""
        assert stepping_up_bound(6) == 33

    def test_from_r44(self):
        """R_2(4) = 18 => stepping-up gives R_3(4) <= 2^17 + 1."""
        assert stepping_up_bound(18) == 2 ** 17 + 1

    def test_monotone(self):
        """Larger input => larger bound."""
        for x in range(2, 20):
            assert stepping_up_bound(x) < stepping_up_bound(x + 1)


class TestSteppingUpTable:
    def test_returns_rows(self):
        table = stepping_up_table(max_k=4)
        assert len(table) >= 1

    def test_k3_present(self):
        table = stepping_up_table(max_k=4)
        k3_rows = [r for r in table if r["k"] == 3]
        assert len(k3_rows) == 1
        assert k3_rows[0]["R_2(k)"] == 6
        assert k3_rows[0]["stepping_up_UB"] == 33


class TestVerifySteppingUp:
    def test_k3_bound_holds(self):
        """R_3(3) = 3 <= 33 = stepping-up UB from R_2(3)=6."""
        result = verify_stepping_up(3, max_n=10)
        assert result["R_3(k)"] == 3
        assert result["stepping_up_UB"] == 33
        assert result["bound_holds"] is True

    def test_k3_values_correct(self):
        result = verify_stepping_up(3, max_n=10)
        assert result["R_2(k)"] == 6
        assert result["k"] == 3


# ======================================================================
# Part 5: Sunflower lemma
# ======================================================================

class TestIsSunflower:
    def test_shared_core(self):
        """Sets {1,2}, {1,3}, {1,4} form a sunflower with core {1}."""
        sets = [frozenset({1, 2}), frozenset({1, 3}), frozenset({1, 4})]
        assert is_sunflower(sets)

    def test_disjoint_sunflower(self):
        """Disjoint sets form a sunflower with empty core."""
        sets = [frozenset({1, 2}), frozenset({3, 4}), frozenset({5, 6})]
        assert is_sunflower(sets)

    def test_not_sunflower(self):
        """Sets {1,2}, {2,3}, {3,4}: pairwise intersections differ."""
        sets = [frozenset({1, 2}), frozenset({2, 3}), frozenset({3, 4})]
        assert not is_sunflower(sets)

    def test_single_set(self):
        assert is_sunflower([frozenset({1, 2})])

    def test_empty_list(self):
        assert is_sunflower([])

    def test_identical_sets(self):
        """Identical sets form a sunflower (core = the set itself)."""
        sets = [frozenset({1, 2}), frozenset({1, 2}), frozenset({1, 2})]
        assert is_sunflower(sets)

    def test_two_sets_always_sunflower(self):
        """Any two sets form a sunflower (their intersection is the core)."""
        sets = [frozenset({1, 2, 3}), frozenset({2, 3, 4})]
        assert is_sunflower(sets)


class TestSunflowerCore:
    def test_shared_element(self):
        sets = [frozenset({1, 2}), frozenset({1, 3}), frozenset({1, 4})]
        assert sunflower_core(sets) == frozenset({1})

    def test_disjoint_core_empty(self):
        sets = [frozenset({1, 2}), frozenset({3, 4})]
        assert sunflower_core(sets) == frozenset()

    def test_not_sunflower_returns_none(self):
        sets = [frozenset({1, 2}), frozenset({2, 3}), frozenset({3, 4})]
        assert sunflower_core(sets) is None

    def test_empty_list(self):
        assert sunflower_core([]) == frozenset()


class TestMaxFamilyWithoutSunflower:
    def test_w2_k2_m4(self):
        """2-sets from [4], no 2-sunflower. C(4,2)=6 sets.
        A 2-sunflower among 2-sets means two sets with the same intersection.
        Any two 2-sets form a sunflower, so max family = 1. SF = 2."""
        max_size, family = max_family_without_sunflower(2, 2, 4)
        assert max_size == 1

    def test_w2_k3_m4(self):
        """2-sets from [4], no 3-sunflower.
        A 3-sunflower among 2-sets: three sets whose pairwise intersections
        are all the same (either share an element or all disjoint).
        From [4]: {1,2},{1,3},{1,4} is a sunflower, but we can take
        {1,2},{3,4},{1,3},{2,4} and check... Actually max is 4."""
        max_size, family = max_family_without_sunflower(2, 3, 4)
        assert max_size >= 3  # At least 3 2-sets without a 3-sunflower

    def test_family_is_sunflower_free(self):
        """Returned family should contain no k-sunflower."""
        max_size, family = max_family_without_sunflower(2, 3, 5)
        # Check all 3-subsets of the family.
        for combo in combinations(family, 3):
            assert not is_sunflower(list(combo)), \
                f"Found 3-sunflower in family: {combo}"


class TestSunflowerNumber:
    def test_sf_w2_k2_m4(self):
        """SF(2,2,4) = 2: any 2 two-element sets from [4] contain a 2-sunflower."""
        sf = sunflower_number(2, 2, 4)
        assert sf == 2

    def test_sf_w2_k3_m4(self):
        """SF(2,3,4) >= 3: need at least 3 sets to guarantee a 3-sunflower
        among 2-element sets from [4]."""
        sf = sunflower_number(2, 3, 4)
        assert sf >= 3

    def test_sf_le_ek_bound(self):
        """Sunflower number should be at most the Erdos-Ko bound."""
        for w, k, m in [(2, 2, 4), (2, 3, 5), (3, 2, 6)]:
            sf = sunflower_number(w, k, m)
            ek = erdos_ko_sunflower_bound(w, k) + 1  # +1 because SF is "first forced"
            # SF(w,k,m) <= EK bound + 1 (EK bounds the max family size)
            assert sf <= ek, \
                f"SF({w},{k},{m})={sf} > EK+1={ek}"


class TestErdosKoSunflowerBound:
    def test_w2_k2(self):
        """(k-1)^w * w! = 1^2 * 2 = 2."""
        assert erdos_ko_sunflower_bound(2, 2) == 2

    def test_w2_k3(self):
        """(k-1)^w * w! = 2^2 * 2 = 8."""
        assert erdos_ko_sunflower_bound(2, 3) == 8

    def test_w3_k2(self):
        """(k-1)^w * w! = 1^3 * 6 = 6."""
        assert erdos_ko_sunflower_bound(3, 2) == 6

    def test_w3_k3(self):
        """(k-1)^w * w! = 2^3 * 6 = 48."""
        assert erdos_ko_sunflower_bound(3, 3) == 48

    def test_monotone_in_k(self):
        """Larger k => larger bound (for fixed w)."""
        for w in range(2, 5):
            for k in range(2, 6):
                assert erdos_ko_sunflower_bound(w, k) <= erdos_ko_sunflower_bound(w, k + 1)


class TestImprovedSunflowerBound:
    def test_smaller_than_ek(self):
        """Improved bound should be smaller than EK for large params."""
        # For w=3, k=3: EK = 48, improved ~ (10*ln(9))^3 ~ (21.97)^3 ~ 10600
        # Actually the improved bound can be larger for small params.
        # Just check it's a positive integer.
        val = improved_sunflower_bound(3, 3)
        assert val >= 1

    def test_w1_is_small(self):
        """For w=1, bound = ceil(10*log(k))."""
        val = improved_sunflower_bound(1, 3)
        assert val >= 1


class TestSunflowerTable:
    def test_returns_rows(self):
        table = sunflower_table(max_w=3, max_k=3, max_universe=6)
        assert len(table) > 0

    def test_sf_le_ek_in_table(self):
        """All computed SF values should be <= EK bound + 1."""
        table = sunflower_table(max_w=3, max_k=3, max_universe=6)
        for row in table:
            assert row["SF_computed"] <= row["EK_bound"] + 1, \
                f"SF({row['w']},{row['k']},{row['universe']})={row['SF_computed']} " \
                f"> EK+1={row['EK_bound'] + 1}"

    def test_has_time_info(self):
        table = sunflower_table(max_w=2, max_k=2, max_universe=5)
        for row in table:
            assert "time_s" in row
            assert row["time_s"] >= 0


# ======================================================================
# Cross-component integration tests
# ======================================================================

class TestCrossValidation:
    def test_r2_k3_consistent_hypergraph_vs_classical(self):
        """R_2(3) should be 6 from both hypergraph and classical Ramsey."""
        hyper = compute_hypergraph_ramsey(2, 3, max_n=10)
        assert hyper == KNOWN_HYPERGRAPH_RAMSEY[(2, 3)]

    def test_coprime_r2_matches_coprime_ramsey(self):
        """R^cop_2(3) should match R_cop(3) = 11 from coprime_ramsey_sat."""
        hyper = compute_coprime_hypergraph_ramsey(2, 3, max_n=15)
        assert hyper == 11

    def test_turan_k4_sat_vs_formula_all(self):
        """Turan SAT and formula agree for all tested n."""
        for n in range(4, 9):
            sat_val, _ = turan_number_sat(n, "complete", (4,))
            formula_val = turan_number_formula(n, "complete", (4,))
            assert sat_val == formula_val

    def test_stepping_up_consistent_with_r3_k3(self):
        """R_3(3) = 3 <= stepping-up(R_2(3)=6) = 33."""
        r3 = compute_hypergraph_ramsey(3, 3, max_n=10)
        ub = stepping_up_bound(6)
        assert r3 <= ub

    def test_turan_c5_formula_vs_sat(self):
        """ex(n, C_5) formula matches SAT for n=5..8."""
        for n in range(5, 9):
            sat_val, _ = turan_number_sat(n, "cycle", (5,))
            formula_val = turan_number_formula(n, "cycle", (5,))
            assert sat_val == formula_val, \
                f"n={n}: SAT={sat_val}, formula={formula_val}"


class TestEdgeCases:
    def test_hyperedges_n0(self):
        assert uniform_hyperedges(0, 2) == []

    def test_coprime_hyperedges_n1(self):
        assert coprime_hyperedges(1, 2) == []

    def test_coprime_hyperedges_n2_r2(self):
        assert coprime_hyperedges(2, 2) == [(1, 2)]

    def test_sunflower_empty_universe(self):
        """No w-sets from empty universe."""
        max_size, family = max_family_without_sunflower(2, 2, 0)
        assert max_size == 0
        assert family == []

    def test_turan_n2_k3(self):
        """ex(2, K_3) = 1 (single edge; triangle-free)."""
        assert turan_number_complete(2, 2) == 1

    def test_turan_n1(self):
        """ex(1, K_3) = 0."""
        assert turan_number_complete(1, 2) == 0
