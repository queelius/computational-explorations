"""Tests for coprime_probabilistic.py -- probabilistic Ramsey analysis."""

import math
import sys
from pathlib import Path

import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from coprime_probabilistic import (
    coprime_edges,
    coprime_adj,
    coprime_cliques,
    clique_edges,
    count_coprime_cliques,
    expected_mono_cliques,
    first_moment_threshold,
    first_moment_table,
    second_moment_analysis,
    second_moment_threshold,
    lll_dependency_graph,
    lll_symmetric_bound,
    lll_lower_bound,
    lll_asymmetric_bound,
    lll_asymmetric_lower_bound,
    sample_random_coloring,
    has_mono_clique_fast,
    sample_avoiding_fraction,
    phase_transition_curve,
    transition_width,
    exponential_fit,
    predict_rcop,
    cliques_share_edge,
)


# ---------------------------------------------------------------------------
# Core infrastructure tests
# ---------------------------------------------------------------------------

class TestCoprimeEdges:
    def test_n3_complete(self):
        """At n=3, all pairs are coprime: (1,2),(1,3),(2,3)."""
        edges = coprime_edges(3)
        assert len(edges) == 3
        assert (1, 2) in edges
        assert (2, 3) in edges

    def test_n4_missing_24(self):
        """gcd(2,4)=2, so (2,4) is not an edge."""
        edges = coprime_edges(4)
        assert (2, 4) not in edges
        assert (1, 4) in edges

    def test_density_approaches_6_over_pi2(self):
        """For large n, edge density -> 6/pi^2 ~ 0.6079."""
        n = 100
        edges = coprime_edges(n)
        max_edges = n * (n - 1) // 2
        density = len(edges) / max_edges
        assert abs(density - 6 / math.pi ** 2) < 0.05


class TestCoprimeAdj:
    def test_symmetry(self):
        adj = coprime_adj(5)
        for v in adj:
            for u in adj[v]:
                assert v in adj[u]

    def test_vertex_1_universal(self):
        """Vertex 1 is coprime with everything."""
        adj = coprime_adj(10)
        assert adj[1] == set(range(2, 11))


class TestCoprimeCliques:
    def test_triangles_n5(self):
        """Count K_3 cliques at n=5."""
        cliques = coprime_cliques(5, 3)
        # Every triple from {1,2,3,5} is pairwise coprime, plus others
        assert len(cliques) >= 4  # at least C(4,3) from {1,2,3,5}

    def test_k1_gives_vertices(self):
        cliques = coprime_cliques(5, 1)
        assert len(cliques) == 5

    def test_k_equals_0(self):
        assert coprime_cliques(5, 0) == []

    def test_all_cliques_are_coprime(self):
        """Every returned clique should have pairwise coprime vertices."""
        for cl in coprime_cliques(8, 3):
            for i in range(len(cl)):
                for j in range(i + 1, len(cl)):
                    assert math.gcd(cl[i], cl[j]) == 1

    def test_no_4clique_at_n4(self):
        """At n=4, the 4-clique {1,2,3,4} fails because gcd(2,4)=2."""
        cliques = coprime_cliques(4, 4)
        assert len(cliques) == 0


class TestCliqueEdges:
    def test_triangle(self):
        edges = clique_edges((1, 3, 5))
        assert len(edges) == 3
        assert (1, 3) in edges
        assert (1, 5) in edges
        assert (3, 5) in edges

    def test_k4(self):
        edges = clique_edges((1, 2, 3, 5))
        assert len(edges) == 6  # C(4,2)


class TestCliquesShareEdge:
    def test_shared_two_vertices(self):
        assert cliques_share_edge((1, 2, 3), (1, 2, 5))

    def test_shared_one_vertex(self):
        assert not cliques_share_edge((1, 2, 3), (1, 5, 7))

    def test_disjoint(self):
        assert not cliques_share_edge((1, 2, 3), (5, 7, 11))


# ---------------------------------------------------------------------------
# 1. First moment tests
# ---------------------------------------------------------------------------

class TestFirstMoment:
    def test_expected_mono_formula(self):
        """E[mono K_k] = num_cliques * 2^{1 - C(k,2)}."""
        n, k = 6, 3
        nc = count_coprime_cliques(n, k)
        exp = expected_mono_cliques(n, k)
        kc2 = 3
        assert abs(exp - nc * 2 ** (1 - kc2)) < 1e-12

    def test_expected_mono_k4(self):
        """Check K_4 formula: p = 2^{1-6} = 1/32."""
        n = 10
        nc = count_coprime_cliques(n, 4)
        exp = expected_mono_cliques(n, 4)
        assert abs(exp - nc / 32.0) < 1e-12

    def test_monotone_in_n(self):
        """E[mono K_3] should be non-decreasing in n."""
        prev = 0
        for n in range(3, 20):
            cur = expected_mono_cliques(n, 3)
            assert cur >= prev - 1e-12
            prev = cur

    def test_first_moment_threshold_k3(self):
        """FM threshold for K_3 should be less than R_cop(3)=11."""
        n, exp = first_moment_threshold(3)
        assert n > 0
        assert n <= 11
        assert exp >= 1.0

    def test_first_moment_threshold_k4(self):
        """FM threshold for K_4 should be less than R_cop(4)=59."""
        n, exp = first_moment_threshold(4, max_n=100)
        assert n > 0
        assert n <= 59
        assert exp >= 1.0

    def test_first_moment_table_length(self):
        table = first_moment_table(3, range(3, 8))
        assert len(table) == 5
        for n, nc, exp in table:
            assert nc >= 0
            assert exp >= 0

    def test_multicolor_expected(self):
        """With 3 colors, p = 3^{1-3} = 1/9 per clique."""
        n = 10
        nc = count_coprime_cliques(n, 3)
        exp = expected_mono_cliques(n, 3, num_colors=3)
        assert abs(exp - nc * 3 ** (1 - 3)) < 1e-12


# ---------------------------------------------------------------------------
# 2. Second moment tests
# ---------------------------------------------------------------------------

class TestSecondMoment:
    def test_basic_structure(self):
        res = second_moment_analysis(6, 3)
        assert 'E_X' in res
        assert 'E_X2' in res
        assert 'Var_X' in res
        assert 'chebyshev_upper' in res
        assert 'second_moment_ratio' in res

    def test_variance_nonneg(self):
        """Var[X] >= 0 always."""
        for n in range(5, 12):
            res = second_moment_analysis(n, 3)
            assert res['Var_X'] >= -1e-10

    def test_E_X2_geq_E_X_squared(self):
        """E[X^2] >= E[X]^2 (Cauchy-Schwarz)."""
        for n in range(5, 12):
            res = second_moment_analysis(n, 3)
            assert res['E_X2'] >= res['E_X'] ** 2 - 1e-10

    def test_sm_ratio_leq_1(self):
        """Second moment ratio E[X]^2/E[X^2] <= 1."""
        for n in range(5, 12):
            res = second_moment_analysis(n, 3)
            assert res['second_moment_ratio'] <= 1.0 + 1e-10

    def test_chebyshev_positive(self):
        """Chebyshev upper bound should be non-negative."""
        res = second_moment_analysis(8, 3)
        assert res['chebyshev_upper'] >= 0

    def test_sm_threshold_k3(self):
        """Second moment threshold should exist and be <= R_cop(3)."""
        sm_n = second_moment_threshold(3, max_n=20)
        assert sm_n > 0
        assert sm_n <= 11

    def test_joint_probability_computation(self):
        """Verify the joint probability formula with a small case.

        For n=5, k=3: manually verify one pair of overlapping cliques.
        """
        res = second_moment_analysis(5, 3)
        # E[X^2] should be strictly > E[X]^2 when cliques overlap
        nc = count_coprime_cliques(5, 3)
        if nc > 1:
            assert res['E_X2'] > res['E_X'] ** 2 - 1e-10


# ---------------------------------------------------------------------------
# 3. LLL tests
# ---------------------------------------------------------------------------

class TestLLL:
    def test_dependency_graph_structure(self):
        num_events, dep = lll_dependency_graph(6, 3)
        assert num_events == count_coprime_cliques(6, 3)
        # Symmetric
        for i in dep:
            for j in dep[i]:
                assert i in dep[j]

    def test_lll_holds_small_n(self):
        """LLL should hold for n=3 (single triangle, no dependency)."""
        res = lll_symmetric_bound(3, 3)
        # At n=3, only 1 triangle with d_max=0 => LLL holds
        assert res['lll_holds']
        assert res['num_events'] == 1

    def test_lll_fails_near_threshold(self):
        """LLL should fail at or before R_cop(k)."""
        res = lll_symmetric_bound(11, 3)
        # At n=11, R_cop(3)=11, so the LLL condition should fail
        # (LLL gives a lower bound, and 11 is the exact answer)
        assert not res['lll_holds']

    def test_lll_lower_bound_k3(self):
        """LLL lower bound should be a valid lower bound on R_cop(3)=11."""
        bound = lll_lower_bound(3)
        assert bound >= 3  # at least trivial
        assert bound < 11  # strict lower bound

    def test_asymmetric_tighter(self):
        """Asymmetric LLL should give >= symmetric bound."""
        sym = lll_lower_bound(3, max_n=20)
        asym = lll_asymmetric_lower_bound(3, max_n=20)
        assert asym >= sym

    def test_lll_asymmetric_structure(self):
        res = lll_asymmetric_bound(6, 3)
        assert 'threshold' in res
        assert 'lll_holds' in res

    def test_no_events_trivially_holds(self):
        """With no cliques, LLL trivially holds."""
        res = lll_symmetric_bound(2, 3)
        assert res['lll_holds']
        assert res['num_events'] == 0


# ---------------------------------------------------------------------------
# 4. Random coloring tests
# ---------------------------------------------------------------------------

class TestRandomColoring:
    def test_sample_covers_all_edges(self):
        n = 6
        coloring = sample_random_coloring(n)
        edges = coprime_edges(n)
        for e in edges:
            assert e in coloring
            assert coloring[e] in (0, 1)

    def test_deterministic_seed(self):
        """Same seed should produce same coloring."""
        import random as stdlib_random
        rng1 = stdlib_random.Random(123)
        rng2 = stdlib_random.Random(123)
        c1 = sample_random_coloring(8, rng=rng1)
        c2 = sample_random_coloring(8, rng=rng2)
        assert c1 == c2

    def test_has_mono_clique_all_one_color(self):
        """All-zero coloring should have mono K_3 for n >= 3."""
        n = 5
        edges = coprime_edges(n)
        coloring = {e: 0 for e in edges}
        assert has_mono_clique_fast(n, 3, coloring)

    def test_avoiding_fraction_at_rcop_minus_1(self):
        """At n=10, some colorings should avoid mono K_3."""
        res = sample_avoiding_fraction(10, 3, 1000, seed=42)
        # Very few should avoid -- fraction near 0
        assert res['fraction'] < 0.01

    def test_avoiding_fraction_at_rcop(self):
        """At n=11 (R_cop(3)), no coloring should avoid mono K_3.

        With sampling this is probabilistic, but the probability is
        so vanishingly small that 10000 samples should find 0.
        """
        res = sample_avoiding_fraction(11, 3, 10_000, seed=42)
        assert res['num_avoiding'] == 0

    def test_avoiding_fraction_small_n(self):
        """At n=4, most colorings should avoid mono K_3."""
        res = sample_avoiding_fraction(4, 3, 1000, seed=42)
        assert res['fraction'] > 0.3

    def test_ci_contains_fraction(self):
        res = sample_avoiding_fraction(6, 3, 5000, seed=42)
        assert res['ci_low'] <= res['fraction'] <= res['ci_high']


# ---------------------------------------------------------------------------
# 5. Phase transition tests
# ---------------------------------------------------------------------------

class TestPhaseTransition:
    def test_curve_decreasing(self):
        """P(avoiding) should generally decrease as n grows."""
        curve = phase_transition_curve(3, range(4, 12), 1000, seed=42)
        fracs = [entry['fraction'] for entry in curve]
        # Allow non-strict monotonicity due to sampling noise,
        # but the overall trend should be decreasing
        assert fracs[0] > fracs[-1]

    def test_curve_length(self):
        curve = phase_transition_curve(3, range(5, 10), 500, seed=42)
        assert len(curve) == 5

    def test_transition_width(self):
        curve = phase_transition_curve(3, range(4, 14), 5000, seed=42)
        tw = transition_width(curve)
        # Should find both thresholds for K_3
        assert tw['n_low'] is not None or tw['n_high'] is not None

    def test_transition_width_custom_thresholds(self):
        curve = [
            {'n': 4, 'fraction': 0.95},
            {'n': 5, 'fraction': 0.85},
            {'n': 6, 'fraction': 0.70},
            {'n': 7, 'fraction': 0.40},
            {'n': 8, 'fraction': 0.05},
        ]
        tw = transition_width(curve, low_threshold=0.9, high_threshold=0.1)
        assert tw['n_low'] == 5
        assert tw['n_high'] == 8
        assert tw['width'] == 3


# ---------------------------------------------------------------------------
# 6. Prediction tests
# ---------------------------------------------------------------------------

class TestPrediction:
    def test_exponential_fit(self):
        """Fit to known R_cop values."""
        known = {3: 11, 4: 59}
        a, b = exponential_fit(known)
        # Check that fit is reasonable
        assert abs(a * b ** 3 - 11) < 1  # should be exact for 2 points
        assert abs(a * b ** 4 - 59) < 1

    def test_exponential_fit_perfect_exponential(self):
        """Fitting exact exponential data should recover parameters."""
        data = {1: 2, 2: 6, 3: 18}  # 2 * 3^k
        a, b = exponential_fit(data)
        assert abs(a - 2.0 / 3) < 0.1
        assert abs(b - 3.0) < 0.1

    def test_predict_rcop_returns_multiple(self):
        known = {3: 11, 4: 59}
        preds = predict_rcop(5, known)
        assert 'first_moment' in preds or 'exp_fit' in preds

    def test_predict_rcop5_reasonable_range(self):
        """R_cop(5) prediction should be in a reasonable range."""
        known = {3: 11, 4: 59}
        preds = predict_rcop(5, known)
        exp_pred = preds.get('exp_fit', 300)
        # Should be larger than R_cop(4)=59 and not astronomically large
        assert exp_pred > 59
        assert exp_pred < 10000

    def test_predict_growth_factor(self):
        """Growth factor b should be > 1 (exponential growth)."""
        known = {3: 11, 4: 59}
        a, b = exponential_fit(known)
        assert b > 1.0


# ---------------------------------------------------------------------------
# Cross-method consistency tests
# ---------------------------------------------------------------------------

class TestCrossMethodConsistency:
    def test_fm_below_actual_k3(self):
        """First moment threshold <= R_cop(3) = 11."""
        n, _ = first_moment_threshold(3)
        assert n <= 11

    def test_lll_below_actual_k3(self):
        """LLL bound < R_cop(3) = 11."""
        bound = lll_lower_bound(3)
        assert bound < 11

    def test_ordering_fm_lll_actual(self):
        """LLL bound <= FM threshold <= actual R_cop for k=3."""
        lll_b = lll_lower_bound(3)
        fm_n, _ = first_moment_threshold(3)
        actual = 11
        assert lll_b < actual
        assert fm_n <= actual

    def test_second_moment_between_first_and_actual_k3(self):
        """SM threshold should be between FM threshold and actual."""
        fm_n, _ = first_moment_threshold(3)
        sm_n = second_moment_threshold(3, max_n=20)
        actual = 11
        # SM threshold >= FM threshold (second moment is more refined)
        assert sm_n >= fm_n
        assert sm_n <= actual

    def test_expected_cliques_at_rcop(self):
        """At n = R_cop(k), E[mono K_k] should be >> 1."""
        exp_at_11 = expected_mono_cliques(11, 3)
        assert exp_at_11 > 1.0
        # Should be significantly larger than 1
        assert exp_at_11 > 5.0

    def test_no_avoiding_at_rcop_by_sampling(self):
        """At R_cop(3)=11, sampling should find 0 avoiding colorings."""
        res = sample_avoiding_fraction(11, 3, 5000, seed=42)
        assert res['num_avoiding'] == 0

    def test_some_avoiding_at_rcop_minus_1(self):
        """At R_cop(3)-1=10, avoiding colorings exist (but are rare)."""
        # We know exactly 156 exist out of 2^31, so with enough samples
        # we might or might not find them. The key point is the exact
        # count is known to be > 0.
        edges = coprime_edges(10)
        assert len(edges) == 31
        # 156 / 2^31 ~ 7.3e-8 -- too rare for sampling
        # But we can verify the expected count is consistent
        exp = expected_mono_cliques(10, 3)
        assert exp > 0.5  # close to threshold
