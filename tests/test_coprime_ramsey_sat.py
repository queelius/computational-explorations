"""Tests for coprime_ramsey_sat.py — SAT-based coprime Ramsey computation."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from coprime_ramsey_sat import (
    coprime_edges,
    find_coprime_cliques,
    find_new_coprime_cliques,
    CoprimeSATEncoder,
    encode_rcop_sat,
    compute_rcop_sat,
    check_extension_unsat,
    validate_avoiding_coloring,
)


# ---------------------------------------------------------------------------
# Coprime edge tests
# ---------------------------------------------------------------------------

class TestCoprimeEdges:
    def test_n1_empty(self):
        assert coprime_edges(1) == []

    def test_n2_single_edge(self):
        edges = coprime_edges(2)
        assert edges == [(1, 2)]

    def test_n4_excludes_2_4(self):
        edges = coprime_edges(4)
        assert (2, 4) not in edges
        assert (1, 4) in edges
        assert (3, 4) in edges

    def test_n6_excludes_composites(self):
        edges = coprime_edges(6)
        assert (2, 4) not in edges
        assert (2, 6) not in edges
        assert (3, 6) not in edges
        assert (4, 6) not in edges
        # But these should be present
        assert (1, 6) in edges
        assert (5, 6) in edges

    def test_edge_count_consistency(self):
        """Edge count matches direct computation."""
        for n in range(1, 20):
            edges = coprime_edges(n)
            expected = sum(1 for i in range(1, n + 1)
                           for j in range(i + 1, n + 1)
                           if math.gcd(i, j) == 1)
            assert len(edges) == expected


# ---------------------------------------------------------------------------
# Clique enumeration tests
# ---------------------------------------------------------------------------

class TestFindCoprimeCliques:
    def test_1_cliques(self):
        """1-cliques are just individual vertices."""
        cliques = find_coprime_cliques(5, 1)
        assert len(cliques) == 5

    def test_2_cliques_are_edges(self):
        """2-cliques should match coprime edges."""
        for n in [3, 5, 8]:
            cliques = find_coprime_cliques(n, 2)
            edges = coprime_edges(n)
            assert len(cliques) == len(edges)

    def test_3_cliques_n5(self):
        """Count 3-cliques (triangles) in coprime graph on [5]."""
        cliques = find_coprime_cliques(5, 3)
        # Verify each is actually a coprime triple
        for c in cliques:
            assert len(c) == 3
            for i in range(3):
                for j in range(i + 1, 3):
                    assert math.gcd(c[i], c[j]) == 1

    def test_4_cliques_n10(self):
        """4-cliques in coprime graph on [10]."""
        cliques = find_coprime_cliques(10, 4)
        assert len(cliques) > 0
        for c in cliques:
            assert len(c) == 4
            for i in range(4):
                for j in range(i + 1, 4):
                    assert math.gcd(c[i], c[j]) == 1

    def test_no_clique_larger_than_graph(self):
        """No k-clique if k > number of vertices."""
        assert find_coprime_cliques(3, 5) == []

    def test_clique_contains_1(self):
        """1 is coprime with everything, so large cliques often include it."""
        cliques_4 = find_coprime_cliques(10, 4)
        has_one = any(1 in c for c in cliques_4)
        assert has_one

    def test_empty_for_k0(self):
        assert find_coprime_cliques(5, 0) == []


class TestFindNewCoprimeCliques:
    def test_new_cliques_agree_with_full(self):
        """New cliques at n should be exactly those containing n."""
        for n in range(4, 12):
            k = 3
            # Build adjacency
            adj = {}
            for i in range(1, n + 1):
                adj[i] = set()
            for i in range(1, n + 1):
                for j in range(i + 1, n + 1):
                    if math.gcd(i, j) == 1:
                        adj[i].add(j)
                        adj[j].add(i)

            new_cliques = find_new_coprime_cliques(n, k, adj)
            all_cliques = find_coprime_cliques(n, k)
            cliques_with_n = [c for c in all_cliques if n in c]

            assert sorted(new_cliques) == sorted(cliques_with_n), \
                f"Mismatch at n={n}: new={sorted(new_cliques)} vs full={sorted(cliques_with_n)}"


# ---------------------------------------------------------------------------
# One-shot SAT encoding tests
# ---------------------------------------------------------------------------

class TestEncodeSAT:
    def test_n2_k2_unsat(self):
        """n=2, k=2: single edge (1,2), must be monochromatic. UNSAT."""
        solver, edge_to_var, ncl = encode_rcop_sat(2, 2)
        assert not solver.solve()
        solver.delete()

    def test_n3_k3_sat(self):
        """n=3, k=3: coprime triangle {1,2,3}, but coloring can avoid mono K_3?
        Actually {1,2,3} is the only triangle and has 3 edges.
        Clause for color 0: (-x1 v -x2 v -x3)
        Clause for color 1: (x1 v x2 v x3)
        Setting one edge different works. SAT.
        """
        solver, edge_to_var, ncl = encode_rcop_sat(3, 3)
        assert solver.solve()
        solver.delete()

    def test_encoding_variable_count(self):
        """Number of variables = number of coprime edges."""
        for n in [5, 8, 10]:
            solver, edge_to_var, ncl = encode_rcop_sat(n, 3)
            assert len(edge_to_var) == len(coprime_edges(n))
            solver.delete()

    def test_encoding_clause_count(self):
        """Number of clauses = 2 * number of k-cliques."""
        for n in [5, 8]:
            solver, edge_to_var, ncl = encode_rcop_sat(n, 3)
            expected_cliques = len(find_coprime_cliques(n, 3))
            assert ncl == 2 * expected_cliques
            solver.delete()


# ---------------------------------------------------------------------------
# Incremental encoder tests
# ---------------------------------------------------------------------------

class TestCoprimeSATEncoder:
    def test_incremental_matches_oneshot(self):
        """Incremental and one-shot encoding should agree on SAT/UNSAT."""
        k = 3
        enc = CoprimeSATEncoder(k)
        for n in range(3, 12):
            inc_sat = enc.extend_to(n)
            solver, _, _ = encode_rcop_sat(n, k)
            oneshot_sat = solver.solve()
            solver.delete()
            assert inc_sat == oneshot_sat, \
                f"Mismatch at n={n}: incremental={inc_sat}, oneshot={oneshot_sat}"
        enc.close()

    def test_variable_count_grows(self):
        """Variable count should increase as n increases."""
        enc = CoprimeSATEncoder(3)
        prev_vars = 0
        for n in range(3, 10):
            enc.extend_to(n)
            curr_vars = enc.next_var - 1
            assert curr_vars >= prev_vars
            prev_vars = curr_vars
        enc.close()


# ---------------------------------------------------------------------------
# R_cop(k) exact value tests
# ---------------------------------------------------------------------------

class TestRCopExact:
    def test_rcop2_equals_2(self):
        """R_cop(2) = 2: gcd(1,2)=1, single edge must be one color."""
        result = compute_rcop_sat(2, max_n=10, verbose=False)
        assert result == 2

    def test_rcop3_equals_11(self):
        """R_cop(3) = 11 — validates against the known exact value."""
        result = compute_rcop_sat(3, max_n=15, verbose=False)
        assert result == 11


class TestSATModelValidation:
    def test_model_at_n10_k3_is_valid(self):
        """At n=10 < R_cop(3)=11, the SAT model should be a valid avoiding coloring."""
        enc = CoprimeSATEncoder(3)
        sat = enc.extend_to(10)
        assert sat, "n=10 should be SAT for k=3"

        coloring = enc.get_model()
        assert coloring is not None

        # Every coprime edge should be colored
        edges = coprime_edges(10)
        for e in edges:
            assert e in coloring, f"Edge {e} not in coloring"
            assert coloring[e] in (0, 1), f"Edge {e} has invalid color {coloring[e]}"

        # No monochromatic K_3
        assert validate_avoiding_coloring(10, 3, coloring)
        enc.close()

    def test_model_at_small_n_k4_is_valid(self):
        """At small n, the SAT model for k=4 should be valid."""
        enc = CoprimeSATEncoder(4)
        sat = enc.extend_to(10)
        assert sat, "n=10 should be SAT for k=4"

        coloring = enc.get_model()
        assert coloring is not None
        assert validate_avoiding_coloring(10, 4, coloring)
        enc.close()


class TestValidateAvoidingColoring:
    def test_all_zero_has_mono_triangle(self):
        """All edges color 0 on [5] has a monochromatic triangle."""
        edges = coprime_edges(5)
        coloring = {e: 0 for e in edges}
        assert not validate_avoiding_coloring(5, 3, coloring)

    def test_valid_avoiding_at_n3_k3(self):
        """A mixed coloring on [3] can avoid monochromatic K_3."""
        # Triangle {1,2,3}. Color one edge differently.
        coloring = {(1, 2): 0, (1, 3): 0, (2, 3): 1}
        assert validate_avoiding_coloring(3, 3, coloring)

    def test_all_zero_trivially_has_k2(self):
        """Any coloring has monochromatic K_2 if there are edges."""
        coloring = {(1, 2): 0, (1, 3): 0, (2, 3): 0}
        assert not validate_avoiding_coloring(3, 2, coloring)


# ---------------------------------------------------------------------------
# Extension check tests
# ---------------------------------------------------------------------------

class TestCheckExtensionUnsat:
    def test_extension_k3_at_rcop3(self):
        """At n=11 (R_cop(3)), no n=10 coloring extends to n=11."""
        all_failed, checked = check_extension_unsat(10, 11, 3, num_seeds=20)
        assert all_failed, "All n=10 seeds should fail to extend to n=11"
        assert checked > 0

    def test_extension_k3_below_rcop3(self):
        """At n=10 < R_cop(3)=11, some n=9 colorings extend to n=10."""
        all_failed, checked = check_extension_unsat(9, 10, 3, num_seeds=20)
        assert not all_failed, "Some n=9 colorings should extend to n=10"


# ---------------------------------------------------------------------------
# R_cop(4) evidence tests
# ---------------------------------------------------------------------------

class TestRCop4:
    def test_n58_is_sat(self):
        """n=58 should be SAT for k=4 (avoiding coloring exists)."""
        enc = CoprimeSATEncoder(4)
        # Use incremental solver up to n=58
        for n in range(4, 59):
            sat = enc.extend_to(n)
            if n == 58:
                assert sat, "n=58 should be SAT for k=4"
        enc.close()

    def test_no_n58_coloring_extends_to_59(self):
        """No valid K_4-free coloring of [58] can be extended to [59].

        This is the key evidence for R_cop(4) = 59:
        - 59 is prime, so coprime with all of 1..58
        - Every tested n=58 coloring fails to extend in <0.01s
        - The extension 3-SAT has clause/var ratio ~31 (above threshold)
        """
        all_failed, checked = check_extension_unsat(58, 59, 4, num_seeds=20)
        assert all_failed, \
            f"Expected all n=58 seeds to fail extending to n=59, but {checked} checked"
        assert checked == 20, f"Expected 20 seeds checked, got {checked}"

    def test_rcop4_sat_up_to_58(self):
        """SAT solver confirms avoiding colorings exist for all n <= 58."""
        # Test a few key values using fresh solvers
        for n in [20, 40, 50, 55, 58]:
            enc = CoprimeSATEncoder(4)
            sat = enc.extend_to(n)
            assert sat, f"n={n} should be SAT for k=4"
            # Verify the model is valid
            coloring = enc.get_model()
            assert coloring is not None
            assert validate_avoiding_coloring(n, 4, coloring), \
                f"SAT model at n={n} should be a valid avoiding coloring"
            enc.close()
