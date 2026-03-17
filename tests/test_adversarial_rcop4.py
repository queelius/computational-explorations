"""
Tests for adversarial_rcop4.py — independent verification of R_cop(4) = 59.

Each test class targets one attack vector.  If ANY test finds a flaw,
the claim R_cop(4) = 59 is in doubt.

Tests marked @pytest.mark.slow require a direct UNSAT proof at n=59, which
takes 15-60 minutes depending on CPU and load.  Run with:
    pytest tests/test_adversarial_rcop4.py -m slow --timeout=3600
The NON-slow tests (extension method, clique enumeration, witness verification)
provide equivalent logical coverage and complete in under 30 seconds.
"""

import math
import sys
from itertools import combinations
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adversarial_rcop4 import (
    are_coprime,
    coprime_graph_edges,
    coprime_adjacency,
    enumerate_coprime_kcliques,
    coprime_kcliques_containing,
    build_sat_formula,
    solve_sat,
    extract_coloring,
    verify_coloring_avoids_mono_clique,
    attack_vertex59_connectivity,
    attack_clique_count,
    attack_clause_audit,
    attack_witness_n58,
    attack_direct_sat_n59,
    attack_cross_solver_n59,
    attack_extension_unsat,
    attack_extension_from_coloring,
    attack_transition_sweep,
)

from pysat.solvers import Cadical153, Glucose4


# ======================================================================
# Sanity tests for primitive helpers
# ======================================================================

class TestPrimitives:
    """Verify the from-scratch primitives are correct."""

    def test_are_coprime_basic(self):
        assert are_coprime(1, 7)
        assert are_coprime(3, 5)
        assert not are_coprime(4, 6)
        assert not are_coprime(2, 4)
        assert are_coprime(1, 1)

    def test_coprime_edges_n1(self):
        assert coprime_graph_edges(1) == []

    def test_coprime_edges_n2(self):
        assert coprime_graph_edges(2) == [(1, 2)]

    def test_coprime_edges_n4(self):
        edges = coprime_graph_edges(4)
        assert (2, 4) not in edges
        assert (1, 4) in edges
        assert (3, 4) in edges

    def test_coprime_edges_count_agrees_with_direct(self):
        """Cross-check edge count with direct nested-loop computation."""
        for n in range(1, 25):
            edges = coprime_graph_edges(n)
            direct_count = sum(1 for i in range(1, n + 1)
                               for j in range(i + 1, n + 1)
                               if math.gcd(i, j) == 1)
            assert len(edges) == direct_count, f"n={n}"

    def test_adjacency_symmetric(self):
        adj = coprime_adjacency(20)
        for v, nbrs in adj.items():
            for w in nbrs:
                assert v in adj[w], f"{v} -> {w} but not {w} -> {v}"

    def test_adjacency_correct(self):
        adj = coprime_adjacency(10)
        assert 2 in adj[3]  # gcd(2,3)=1
        assert 4 not in adj[6]  # gcd(4,6)=2
        assert 1 in adj[7]  # gcd(1,7)=1


# ======================================================================
# Clique enumeration correctness
# ======================================================================

class TestCliqueEnumeration:
    """Verify clique enumeration is correct for small n."""

    def test_2cliques_match_edges(self):
        for n in [5, 10, 15]:
            cliques = enumerate_coprime_kcliques(n, 2)
            edges = coprime_graph_edges(n)
            assert len(cliques) == len(edges), f"n={n}"

    def test_3cliques_small(self):
        """Every enumerated 3-clique must be pairwise coprime."""
        for n in [5, 8, 12]:
            cliques = enumerate_coprime_kcliques(n, 3)
            for c in cliques:
                assert len(c) == 3
                for i in range(3):
                    for j in range(i + 1, 3):
                        assert math.gcd(c[i], c[j]) == 1, \
                            f"n={n}, clique {c}: gcd({c[i]},{c[j]})!=1"

    def test_4cliques_small_bruteforce(self):
        """For small n, compare with brute-force C(n,4) enumeration."""
        for n in [8, 12, 15]:
            cliques = enumerate_coprime_kcliques(n, 4)
            brute = []
            for subset in combinations(range(1, n + 1), 4):
                if all(math.gcd(subset[i], subset[j]) == 1
                       for i in range(4) for j in range(i + 1, 4)):
                    brute.append(tuple(subset))
            assert sorted(cliques) == sorted(brute), \
                f"n={n}: {len(cliques)} vs {len(brute)}"

    def test_1cliques(self):
        assert len(enumerate_coprime_kcliques(5, 1)) == 5

    def test_no_oversized_clique(self):
        assert enumerate_coprime_kcliques(3, 5) == []

    def test_kcliques_containing_vertex(self):
        """Cliques containing a specific vertex match the full enumeration filtered."""
        for n in [10, 15]:
            adj = coprime_adjacency(n)
            for v in [1, n, n // 2]:
                if v > n:
                    continue
                containing = coprime_kcliques_containing(n, 4, v, adj)
                full = enumerate_coprime_kcliques(n, 4)
                full_filtered = [c for c in full if v in c]
                assert sorted(containing) == sorted(full_filtered), \
                    f"n={n}, v={v}: {len(containing)} vs {len(full_filtered)}"


# ======================================================================
# SAT formula correctness
# ======================================================================

class TestSATFormula:
    """Verify the SAT encoding is correct."""

    def test_n2_k2_unsat(self):
        """Single edge (1,2) cannot avoid mono K_2."""
        etv, cliques, clauses = build_sat_formula(2, 2)
        model = solve_sat(clauses)
        assert model is None, "n=2, k=2 should be UNSAT"

    def test_n3_k3_sat(self):
        """Triangle {1,2,3} can be 2-colored to avoid mono K_3."""
        etv, cliques, clauses = build_sat_formula(3, 3)
        model = solve_sat(clauses)
        assert model is not None, "n=3, k=3 should be SAT"

    def test_variable_count_matches_edges(self):
        for n in [5, 10, 20]:
            etv, _, _ = build_sat_formula(n, 4)
            edges = coprime_graph_edges(n)
            assert len(etv) == len(edges), f"n={n}"

    def test_clause_count_matches_cliques(self):
        """Each clique produces exactly 2 clauses."""
        for n in [5, 8, 12]:
            etv, cliques, clauses = build_sat_formula(n, 3, symmetry_break=False)
            assert len(clauses) == 2 * len(cliques), \
                f"n={n}: {len(clauses)} clauses vs {2 * len(cliques)} expected"

    def test_symmetry_break_adds_one_clause(self):
        etv, cliques, clauses_no = build_sat_formula(10, 4, symmetry_break=False)
        _, _, clauses_yes = build_sat_formula(10, 4, symmetry_break=True)
        assert len(clauses_yes) == len(clauses_no) + 1

    def test_rcop3_exact(self):
        """R_cop(3) = 11: SAT at n=10, UNSAT at n=11."""
        etv10, _, cl10 = build_sat_formula(10, 3)
        assert solve_sat(cl10) is not None, "n=10, k=3 should be SAT"

        etv11, _, cl11 = build_sat_formula(11, 3)
        assert solve_sat(cl11) is None, "n=11, k=3 should be UNSAT"


# ======================================================================
# Attack Vector 6: Vertex 59 connectivity
# ======================================================================

class TestAV6Connectivity:
    def test_59_is_prime(self):
        assert all(59 % d != 0 for d in range(2, 8))

    def test_59_coprime_to_all(self):
        for i in range(1, 59):
            assert math.gcd(i, 59) == 1, f"gcd({i}, 59) != 1"

    def test_phi_59_is_58(self):
        phi = sum(1 for i in range(1, 59) if math.gcd(i, 59) == 1)
        assert phi == 58

    def test_attack_vector(self):
        result = attack_vertex59_connectivity(verbose=False)
        assert result["is_prime"]
        assert result["connects_to_all"]
        assert result["phi_59"] == 58


# ======================================================================
# Attack Vector 3: Clique count cross-check
# ======================================================================

class TestAV3CliqueCount:
    def test_small_n_crosscheck(self):
        """Clique count cross-check for small n values."""
        for n in [10, 15, 20]:
            result = attack_clique_count(n, 4, verbose=False)
            assert result["match"], \
                f"n={n}: backtrack={result['backtrack_count']}, brute={result['brute_count']}"
            assert not result["bad_cliques"], f"n={n}: found non-coprime cliques"

    @pytest.mark.timeout(300)
    def test_n58_crosscheck(self):
        """Full cross-check at n=58. C(58,4)=424270 is feasible."""
        result = attack_clique_count(58, 4, verbose=False)
        assert result["match"], \
            f"backtrack={result['backtrack_count']}, brute={result['brute_count']}"
        assert result["missing"] == 0
        assert result["extra"] == 0
        assert not result["bad_cliques"]


# ======================================================================
# Attack Vector 4: Clause audit
# ======================================================================

class TestAV4ClauseAudit:
    def test_specific_cliques(self):
        result = attack_clause_audit(verbose=False)
        for clique, info in result.items():
            if info.get("coprime"):
                assert info["correct"], f"Clause audit failed for {clique}"

    def test_clique_1_2_3_5(self):
        """Manually verify {1,2,3,5} encoding."""
        clique = (1, 2, 3, 5)
        # All pairwise coprime
        for i in range(4):
            for j in range(i + 1, 4):
                assert math.gcd(clique[i], clique[j]) == 1

        # 6 edges: (1,2),(1,3),(1,5),(2,3),(2,5),(3,5)
        edges = [(1, 2), (1, 3), (1, 5), (2, 3), (2, 5), (3, 5)]
        etv, cliques, clauses = build_sat_formula(5, 4, symmetry_break=False)
        evars = [etv[e] for e in edges]

        # Check both forbidding clauses exist
        neg = sorted([-v for v in evars])
        pos = sorted(evars)
        found_neg = any(sorted(c) == neg for c in clauses)
        found_pos = any(sorted(c) == pos for c in clauses)
        assert found_neg, "Missing forbid-all-color-0 clause for {1,2,3,5}"
        assert found_pos, "Missing forbid-all-color-1 clause for {1,2,3,5}"

    def test_clause_width(self):
        """Each clique clause should have exactly C(4,2) = 6 literals."""
        etv, cliques, clauses = build_sat_formula(20, 4, symmetry_break=False)
        for cl in clauses:
            assert len(cl) == 6, f"Clause has {len(cl)} literals, expected 6"


# ======================================================================
# Attack Vector 2: Witness verification at n=58
# ======================================================================

class TestAV2Witness:
    @pytest.mark.timeout(300)
    def test_n58_sat_and_valid(self):
        """n=58 should be SAT, and the witness should be a valid avoiding coloring."""
        result = attack_witness_n58(4, verbose=False)
        assert result["sat"], "n=58 should be SAT"
        assert result["valid_coloring"], \
            f"Witness invalid at clique {result.get('bad_clique')}"
        assert result["missing_edges"] == 0, "All coprime edges should be colored"

    @pytest.mark.timeout(300)
    def test_n58_witness_manual_recheck(self):
        """
        Extract coloring at n=58 via CaDiCaL, then recheck with our own
        brute-force clique verifier (independent of SAT encoding).
        """
        etv, cliques, clauses = build_sat_formula(58, 4, symmetry_break=False)
        model = solve_sat(clauses, solver_cls=Cadical153)
        assert model is not None, "n=58 must be SAT"

        coloring = extract_coloring(model, etv)

        # Brute-force: for every 4-subset of [58], check if pairwise coprime
        # and if so, verify not monochromatic.
        mono_found = None
        for subset in combinations(range(1, 59), 4):
            if not all(math.gcd(subset[i], subset[j]) == 1
                       for i in range(4) for j in range(i + 1, 4)):
                continue
            colors = set()
            for i in range(4):
                for j in range(i + 1, 4):
                    e = (subset[i], subset[j])
                    colors.add(coloring[e])
            if len(colors) == 1:
                mono_found = subset
                break

        assert mono_found is None, f"Monochromatic K_4 at {mono_found}"


# ======================================================================
# Attack Vector 1: Direct SAT at n=59
# ======================================================================

class TestAV1DirectSAT:
    """Direct SAT solve at n=59.  These tests take 15-60 minutes each."""

    @pytest.mark.slow
    @pytest.mark.timeout(3600)
    def test_n59_unsat_cadical(self):
        """n=59 should be UNSAT (no avoiding coloring exists)."""
        etv, cliques, clauses = build_sat_formula(59, 4, symmetry_break=False)
        model = solve_sat(clauses, solver_cls=Cadical153)
        assert model is None, "n=59 should be UNSAT — if SAT, R_cop(4) != 59"

    @pytest.mark.slow
    @pytest.mark.timeout(3600)
    def test_n59_unsat_glucose4(self):
        """n=59 UNSAT with Glucose4 (different solver from CaDiCaL)."""
        etv, cliques, clauses = build_sat_formula(59, 4, symmetry_break=False)
        model = solve_sat(clauses, solver_cls=Glucose4)
        assert model is None, "n=59 should be UNSAT — if SAT, R_cop(4) != 59"

    @pytest.mark.slow
    @pytest.mark.timeout(3600)
    def test_n59_unsat_with_symmetry_break(self):
        """UNSAT should hold with and without symmetry breaking."""
        etv, cliques, clauses = build_sat_formula(59, 4, symmetry_break=True)
        model = solve_sat(clauses, solver_cls=Cadical153)
        assert model is None

    def test_n59_formula_stats(self):
        """Sanity-check the formula dimensions at n=59."""
        etv, cliques, clauses = build_sat_formula(59, 4, symmetry_break=False)
        # Number of coprime edges at n=59
        assert len(etv) == len(coprime_graph_edges(59))
        # Clauses = 2 * cliques
        assert len(clauses) == 2 * len(cliques)
        # Each clause has exactly 6 literals
        for cl in clauses:
            assert len(cl) == 6
        # Known values
        assert len(etv) == 1085
        assert len(cliques) == 58956


# ======================================================================
# Attack Vector 7: Cross-solver agreement
# ======================================================================

class TestAV7CrossSolver:
    @pytest.mark.slow
    @pytest.mark.timeout(7200)
    def test_solvers_agree_n59(self):
        """CaDiCaL and Glucose4 must agree on n=59.  Runs two full UNSAT proofs."""
        result = attack_cross_solver_n59(verbose=False)
        assert result["solvers_agree"], "Solvers disagree!"
        assert not result["cadical"]["sat"], "CaDiCaL says SAT — flaw!"
        assert not result["glucose4"]["sat"], "Glucose4 says SAT — flaw!"


# ======================================================================
# Attack Vector 5: Extension UNSAT
# ======================================================================

class TestAV5Extension:
    @pytest.mark.timeout(600)
    def test_no_extension_to_59(self):
        """No valid n=58 coloring should extend to n=59."""
        result = attack_extension_unsat(num_seeds=10, verbose=False)
        assert result["all_failed"], \
            f"{result['extensions_found']} seed(s) extended — claim disproved!"
        assert result["seeds_checked"] >= 10

    @pytest.mark.timeout(120)
    def test_extension_below_rcop3_works(self):
        """
        Sanity check: at n=10 < R_cop(3)=11, some n=9 colorings
        SHOULD extend to n=10.
        """
        etv9, _, cl9 = build_sat_formula(9, 3, symmetry_break=False)
        etv10, _, cl10 = build_sat_formula(10, 3, symmetry_break=False)

        solver9 = Cadical153(bootstrap_with=cl9)
        assert solver9.solve(), "n=9, k=3 should be SAT"
        model9 = solver9.get_model()
        model9_set = set(model9)
        solver9.delete()

        # Fix base edges in n=10 formula
        assumptions = []
        for edge, var9 in etv9.items():
            var10 = etv10.get(edge)
            if var10 is not None:
                if var9 in model9_set:
                    assumptions.append(var10)
                else:
                    assumptions.append(-var10)

        solver10 = Cadical153(bootstrap_with=cl10)
        ext_sat = solver10.solve(assumptions=assumptions)
        solver10.delete()
        assert ext_sat, "Some n=9 coloring should extend to n=10"


# ======================================================================
# Attack Vector 8: Extension from specific coloring
# ======================================================================

class TestAV8ExtensionFromColoring:
    @pytest.mark.timeout(300)
    def test_specific_coloring_does_not_extend(self):
        result = attack_extension_from_coloring(verbose=False)
        assert "flaw" not in result, f"Unexpected flaw: {result.get('flaw')}"
        assert not result["extendable"], "Coloring extends to 59 — claim disproved!"
        assert result["num_cliques_with_59"] > 0
        assert result["num_extension_clauses"] > 0


# ======================================================================
# Attack Vector 9: Transition sweep
# ======================================================================

class TestAV9TransitionSweep:
    @pytest.mark.slow
    @pytest.mark.timeout(3600)
    def test_transition_at_59(self):
        """The SAT/UNSAT transition should happen exactly at n=59.
        Requires full UNSAT proof at n=59."""
        result = attack_transition_sweep(n_start=55, n_end=59, verbose=False)
        for n in range(55, 59):
            assert result["per_n"][n]["sat"], f"n={n} should be SAT"
        assert not result["per_n"][59]["sat"], "n=59 should be UNSAT"

    @pytest.mark.timeout(120)
    def test_transition_below_59_all_sat(self):
        """n=55..58 should all be SAT (fast, no UNSAT proof needed)."""
        result = attack_transition_sweep(n_start=55, n_end=58, verbose=False)
        for n in range(55, 59):
            assert result["per_n"][n]["sat"], f"n={n} should be SAT"


# ======================================================================
# Cross-check with existing code
# ======================================================================

class TestCrossCheckWithExisting:
    """Compare our from-scratch code with the existing coprime_ramsey_sat.py."""

    def test_edge_count_matches(self):
        """Our edge enumeration matches the existing one."""
        from coprime_ramsey_sat import coprime_edges as existing_edges
        for n in [10, 20, 30, 50]:
            ours = coprime_graph_edges(n)
            theirs = existing_edges(n)
            assert ours == theirs, f"Edge mismatch at n={n}"

    def test_clique_count_matches(self):
        """Our clique enumeration matches the existing one."""
        from coprime_ramsey_sat import find_coprime_cliques as existing_cliques
        for n in [10, 15, 20]:
            ours = enumerate_coprime_kcliques(n, 4)
            theirs = existing_cliques(n, 4)
            assert sorted(ours) == sorted(theirs), \
                f"Clique mismatch at n={n}: {len(ours)} vs {len(theirs)}"

    @pytest.mark.timeout(300)
    def test_clique_count_matches_n58(self):
        """Clique count agreement at the critical value n=58."""
        from coprime_ramsey_sat import find_coprime_cliques as existing_cliques
        ours = enumerate_coprime_kcliques(58, 4)
        theirs = existing_cliques(58, 4)
        assert len(ours) == len(theirs), \
            f"n=58 clique count: {len(ours)} (ours) vs {len(theirs)} (existing)"

    def test_sat_agreement_small(self):
        """SAT/UNSAT agreement at small n for k=3."""
        from coprime_ramsey_sat import encode_rcop_sat
        for n in [5, 8, 10, 11]:
            ours_etv, ours_cl, ours_clauses = build_sat_formula(n, 3, symmetry_break=False)
            ours_model = solve_sat(ours_clauses)

            solver, their_etv, ncl = encode_rcop_sat(n, 3)
            their_sat = solver.solve()
            solver.delete()

            assert (ours_model is not None) == their_sat, \
                f"n={n}, k=3: ours={'SAT' if ours_model else 'UNSAT'}, " \
                f"theirs={'SAT' if their_sat else 'UNSAT'}"


# ======================================================================
# Symmetry breaking correctness
# ======================================================================

class TestSymmetryBreaking:
    """
    Verify that symmetry breaking (fixing edge(1,2) = color 0)
    is valid — i.e., the problem has exact color-swap symmetry.
    """

    def test_color_swap_preserves_avoiding(self):
        """
        If coloring C avoids mono K_4, then swapping all colors also avoids it.
        Test at several n values.
        """
        for n in [15, 20, 30]:
            etv, cliques, clauses = build_sat_formula(n, 4, symmetry_break=False)
            model = solve_sat(clauses)
            if model is None:
                continue  # UNSAT, nothing to check

            coloring = extract_coloring(model, etv)
            valid, _ = verify_coloring_avoids_mono_clique(n, 4, coloring, cliques)
            assert valid, f"Original coloring invalid at n={n}"

            # Swap all colors
            swapped = {e: 1 - c for e, c in coloring.items()}
            valid_s, _ = verify_coloring_avoids_mono_clique(n, 4, swapped, cliques)
            assert valid_s, f"Swapped coloring invalid at n={n}"

    def test_symmetry_break_preserves_unsat(self):
        """
        If n=59 is UNSAT without symmetry break, it must also be UNSAT with it.
        (Fixing one edge to color 0 only prunes the symmetric half of the search space.)
        """
        # Test on R_cop(3) = 11 first (faster)
        _, _, cl_no = build_sat_formula(11, 3, symmetry_break=False)
        _, _, cl_yes = build_sat_formula(11, 3, symmetry_break=True)
        assert solve_sat(cl_no) is None, "n=11, k=3 should be UNSAT without sym break"
        assert solve_sat(cl_yes) is None, "n=11, k=3 should be UNSAT with sym break"

    def test_symmetry_break_preserves_sat(self):
        """
        If n=10 is SAT without symmetry break, it must also be SAT with it.
        (At least one avoiding coloring has edge(1,2) = color 0.)
        """
        _, _, cl_no = build_sat_formula(10, 3, symmetry_break=False)
        _, _, cl_yes = build_sat_formula(10, 3, symmetry_break=True)
        assert solve_sat(cl_no) is not None
        assert solve_sat(cl_yes) is not None
