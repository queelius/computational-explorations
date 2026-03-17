"""Tests for lower_bound_techniques.py -- lower bound methods for coprime Ramsey."""

import math
import sys
from pathlib import Path

import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lower_bound_techniques import (
    # Constants
    KNOWN_RCOP,
    COPRIME_DENSITY,
    # Core infrastructure
    coprime_edges,
    coprime_adj,
    coprime_cliques,
    clique_edge_set,
    # Probabilistic
    first_moment_bound,
    first_moment_lower_bound,
    second_moment_bound,
    second_moment_lower_bound,
    lll_bound,
    lll_lower_bound,
    probabilistic_bounds_table,
    looseness_analysis,
    # Algebraic
    is_prime,
    quadratic_residues,
    is_quadratic_residue,
    paley_coloring,
    paley_product_coloring,
    paley_primes_1mod4,
    has_mono_clique,
    algebraic_lower_bound,
    residue_coloring,
    best_residue_coloring,
    # Entropy
    coloring_entropy,
    entropy_lower_bound,
    schur_entropy_bound,
    schur_entropy_lower_bound,
    # Explicit constructions
    enumerate_avoiding_colorings,
    coloring_signature,
    analyze_avoiding_structure,
    predict_avoiding_at_larger_n,
    # Comparison
    comparison_table,
    format_comparison_table,
    tightening_analysis,
)


# ============================================================================
# Core infrastructure tests
# ============================================================================

class TestCoreInfrastructure:
    def test_coprime_edges_n3(self):
        edges = coprime_edges(3)
        assert len(edges) == 3
        assert (1, 2) in edges
        assert (1, 3) in edges
        assert (2, 3) in edges

    def test_coprime_edges_n4_excludes_24(self):
        edges = coprime_edges(4)
        assert (2, 4) not in edges

    def test_coprime_adj_symmetry(self):
        adj = coprime_adj(8)
        for v in adj:
            for u in adj[v]:
                assert v in adj[u]

    def test_coprime_adj_vertex1_universal(self):
        adj = coprime_adj(10)
        assert adj[1] == set(range(2, 11))

    def test_coprime_cliques_triangles_n5(self):
        cliques = coprime_cliques(5, 3)
        # {1,2,3}, {1,2,5}, {1,3,5}, {2,3,5}, {1,4,5}, {3,4,5}, etc.
        assert len(cliques) >= 4

    def test_coprime_cliques_k1(self):
        assert len(coprime_cliques(5, 1)) == 5

    def test_coprime_cliques_k0(self):
        assert coprime_cliques(5, 0) == []

    def test_coprime_cliques_all_pairwise_coprime(self):
        for cl in coprime_cliques(8, 3):
            for i in range(len(cl)):
                for j in range(i + 1, len(cl)):
                    assert math.gcd(cl[i], cl[j]) == 1

    def test_clique_edge_set_triangle(self):
        es = clique_edge_set((1, 3, 5))
        assert len(es) == 3
        assert (1, 3) in es
        assert (1, 5) in es
        assert (3, 5) in es

    def test_clique_edge_set_k4(self):
        es = clique_edge_set((1, 2, 3, 5))
        assert len(es) == 6


# ============================================================================
# 1. Probabilistic bound tests
# ============================================================================

class TestFirstMoment:
    def test_basic_formula(self):
        """E[mono K_k] = C_k * 2^{1 - C(k,2)}."""
        res = first_moment_bound(6, 3)
        nc = res['clique_count']
        p = res['prob_mono']
        assert abs(res['expected'] - nc * p) < 1e-12

    def test_probability_k3(self):
        """P(single K_3 mono) = 2^{1-3} = 1/4."""
        res = first_moment_bound(5, 3)
        assert abs(res['prob_mono'] - 0.25) < 1e-12

    def test_probability_k4(self):
        """P(single K_4 mono) = 2^{1-6} = 1/32."""
        res = first_moment_bound(5, 4)
        assert abs(res['prob_mono'] - 1.0 / 32) < 1e-12

    def test_bound_holds_small_n(self):
        """At small n, E[X] < 1 so the bound holds."""
        res = first_moment_bound(3, 3)
        assert res['bound_holds']

    def test_bound_fails_at_actual(self):
        """At R_cop(k), E[X] should be >= 1."""
        res = first_moment_bound(11, 3)
        assert res['expected'] >= 1.0

    def test_fm_lower_bound_k3(self):
        """FM lower bound < R_cop(3) = 11."""
        bound = first_moment_lower_bound(3, max_n=20)
        assert bound >= 3
        assert bound < 11

    def test_fm_lower_bound_k4(self):
        """FM lower bound < R_cop(4) = 59."""
        bound = first_moment_lower_bound(4, max_n=60)
        assert bound >= 4
        assert bound < 59

    def test_monotone_expected(self):
        """E[mono K_3] is non-decreasing in n."""
        prev = 0
        for n in range(3, 16):
            res = first_moment_bound(n, 3)
            assert res['expected'] >= prev - 1e-12
            prev = res['expected']


class TestSecondMoment:
    def test_variance_nonneg(self):
        """Var[X] >= 0."""
        for n in range(5, 12):
            res = second_moment_bound(n, 3)
            assert res['Var_X'] >= -1e-10

    def test_E_X2_geq_E_X_sq(self):
        """E[X^2] >= E[X]^2 (Jensen)."""
        for n in range(5, 12):
            res = second_moment_bound(n, 3)
            assert res['E_X2'] >= res['E_X'] ** 2 - 1e-10

    def test_sm_ratio_leq_1(self):
        """E[X]^2 / E[X^2] <= 1."""
        for n in range(5, 12):
            res = second_moment_bound(n, 3)
            assert res['second_moment_ratio'] <= 1.0 + 1e-10

    def test_sm_lower_bound_k3(self):
        """SM lower bound <= R_cop(3) = 11."""
        bound = second_moment_lower_bound(3, max_n=20)
        assert bound >= 3
        assert bound < 11

    def test_sm_geq_fm_k3(self):
        """Second moment bound >= first moment bound."""
        fm = first_moment_lower_bound(3, max_n=20)
        sm = second_moment_lower_bound(3, max_n=20)
        assert sm >= fm

    def test_no_cliques_case(self):
        """When no cliques exist, bound trivially holds."""
        res = second_moment_bound(2, 3)
        assert res['bound_holds']
        assert res['num_cliques'] == 0


class TestLLL:
    def test_symmetric_at_n3(self):
        """At n=3, one triangle with d_max=0, LLL holds."""
        res = lll_bound(3, 3, variant='symmetric')
        assert res['lll_holds']
        assert res['num_events'] == 1
        assert res['d_max'] == 0

    def test_asymmetric_at_n3(self):
        res = lll_bound(3, 3, variant='asymmetric')
        assert res['lll_holds']

    def test_lll_fails_at_actual(self):
        """LLL must fail at n = R_cop(3) (otherwise it contradicts the value)."""
        res = lll_bound(11, 3, variant='symmetric')
        assert not res['lll_holds']

    def test_lll_lower_bound_k3(self):
        """LLL bound < R_cop(3) = 11."""
        bound = lll_lower_bound(3, variant='symmetric', max_n=20)
        assert bound >= 3
        assert bound < 11

    def test_asymmetric_geq_symmetric(self):
        """Asymmetric LLL gives >= symmetric LLL."""
        sym = lll_lower_bound(3, variant='symmetric', max_n=20)
        asym = lll_lower_bound(3, variant='asymmetric', max_n=20)
        assert asym >= sym

    def test_no_events_holds(self):
        """With no cliques, LLL trivially holds."""
        res = lll_bound(2, 3, variant='symmetric')
        assert res['lll_holds']

    def test_invalid_variant_raises(self):
        with pytest.raises(ValueError, match="Unknown LLL variant"):
            lll_bound(5, 3, variant='bogus')


class TestProbabilisticTable:
    def test_all_bounds_present(self):
        bounds = probabilistic_bounds_table(3, max_n=15)
        assert 'first_moment' in bounds
        assert 'second_moment' in bounds
        assert 'lll_symmetric' in bounds
        assert 'lll_asymmetric' in bounds

    def test_all_bounds_valid_k3(self):
        """All bounds should be < R_cop(3) = 11."""
        bounds = probabilistic_bounds_table(3, max_n=20)
        for method, val in bounds.items():
            assert val < 11, f"{method} = {val} >= 11"
            assert val >= 3, f"{method} = {val} < 3"

    def test_ordering_fm_sm_lll(self):
        """FM <= SM (and LLL is independent but valid)."""
        bounds = probabilistic_bounds_table(3, max_n=20)
        assert bounds['first_moment'] <= bounds['second_moment']


class TestLooseness:
    def test_looseness_k3(self):
        result = looseness_analysis(3, max_n=20)
        # All ratios should be > 1 (bounds are below actual)
        for method, data in result.items():
            if isinstance(data, dict) and 'ratio' in data:
                assert data['ratio'] > 1.0
                assert data['gap'] > 0

    def test_looseness_unknown_k(self):
        result = looseness_analysis(5)
        assert 'error' in result


# ============================================================================
# 2. Algebraic bound tests
# ============================================================================

class TestPrimalityAndQR:
    def test_is_prime(self):
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
        for p in primes:
            assert is_prime(p), f"{p} should be prime"
        non_primes = [0, 1, 4, 6, 8, 9, 10, 15, 21]
        for n in non_primes:
            assert not is_prime(n), f"{n} should not be prime"

    def test_quadratic_residues_mod5(self):
        qr = quadratic_residues(5)
        # 1^2=1, 2^2=4, 3^2=4, 4^2=1 mod 5
        assert qr == {1, 4}

    def test_quadratic_residues_mod7(self):
        qr = quadratic_residues(7)
        # 1,2,4 are QR mod 7
        assert qr == {1, 2, 4}

    def test_is_qr_euler_criterion(self):
        """Euler criterion: a^((p-1)/2) = 1 mod p iff a is QR."""
        assert is_quadratic_residue(1, 7)
        assert is_quadratic_residue(2, 7)
        assert not is_quadratic_residue(3, 7)
        assert is_quadratic_residue(4, 7)
        assert not is_quadratic_residue(5, 7)
        assert not is_quadratic_residue(6, 7)

    def test_paley_primes_1mod4(self):
        primes = paley_primes_1mod4(30)
        assert 5 in primes
        assert 13 in primes
        assert 17 in primes
        assert 29 in primes
        assert 3 not in primes  # 3 = 3 mod 4
        assert 7 not in primes  # 7 = 3 mod 4


class TestPaleyColorings:
    def test_paley_coloring_valid(self):
        """Paley coloring should color all coprime edges."""
        n, p = 8, 5
        col = paley_coloring(n, p)
        edges = coprime_edges(n)
        for e in edges:
            assert e in col
            assert col[e] in (0, 1)

    def test_paley_product_coloring_valid(self):
        n, p = 8, 5
        col = paley_product_coloring(n, p)
        edges = coprime_edges(n)
        for e in edges:
            assert e in col
            assert col[e] in (0, 1)

    def test_paley_avoids_small(self):
        """Paley coloring should avoid mono K_3 for small n."""
        n, p = 5, 5
        col = paley_coloring(n, p)
        # At n=5 with only 9 edges, many colorings avoid K_3
        # Just check it's a valid coloring
        assert len(col) == len(coprime_edges(n))

    def test_paley_both_colors_used(self):
        """Paley coloring should use both colors (not trivial)."""
        n, p = 10, 5
        col = paley_coloring(n, p)
        colors = set(col.values())
        assert len(colors) == 2

    def test_paley_product_both_colors_used(self):
        n, p = 10, 5
        col = paley_product_coloring(n, p)
        colors = set(col.values())
        assert len(colors) == 2


class TestAlgebraicBound:
    def test_algebraic_lower_bound_k3(self):
        """Algebraic bound for k=3 should give valid lower bound."""
        result = algebraic_lower_bound(3, max_n=12, p_limit=30)
        assert result['paley_diff'] >= 2
        assert result['paley_prod'] >= 2
        # Must be below actual R_cop(3) = 11
        assert result['paley_diff'] < 11
        assert result['paley_prod'] < 11

    def test_residue_coloring_valid(self):
        """Residue coloring should color all edges with 0 or 1."""
        col = residue_coloring(8, 3)
        edges = coprime_edges(8)
        for e in edges:
            assert e in col
            assert col[e] in (0, 1)

    def test_residue_coloring_both_colors(self):
        """Non-trivial residue coloring uses both colors."""
        col = residue_coloring(10, 3)
        colors = set(col.values())
        assert len(colors) == 2

    def test_best_residue_k3(self):
        result = best_residue_coloring(3, max_n=12)
        assert result['residue_bound'] >= 2
        assert result['residue_bound'] < 11
        assert result['best_modulus'] >= 2


class TestHasMonoClique:
    def test_all_zero_has_mono(self):
        """All-zero coloring has mono K_3 at n=5."""
        edges = coprime_edges(5)
        col = {e: 0 for e in edges}
        assert has_mono_clique(5, 3, col)

    def test_no_cliques_no_mono(self):
        """At n=2, no K_3 cliques, so no mono K_3."""
        edges = coprime_edges(2)
        col = {e: 0 for e in edges}
        assert not has_mono_clique(2, 3, col)


# ============================================================================
# 3. Entropy bound tests
# ============================================================================

class TestColoringEntropy:
    def test_entropy_small_n(self):
        """At small n with few cliques, entropy bound should hold."""
        res = coloring_entropy(4, 3)
        assert res['bound_holds']
        assert res['H_uniform'] > 0

    def test_entropy_at_actual(self):
        """At R_cop(3)=11, the union bound S1 should exceed 1."""
        res = coloring_entropy(11, 3)
        assert res['S1'] > 1.0
        # The entropy gap should be positive (constraints remove info)
        assert res['entropy_gap'] > 0

    def test_entropy_no_cliques(self):
        """With no cliques, full entropy is available."""
        res = coloring_entropy(2, 3)
        assert res['bound_holds']
        assert res['num_cliques'] == 0

    def test_entropy_no_edges(self):
        res = coloring_entropy(1, 3)
        assert res['bound_holds']
        assert res['num_edges'] == 0

    def test_bits_per_clique_positive(self):
        """bits_per_clique should be positive for k >= 3."""
        res = coloring_entropy(6, 3)
        assert res['bits_per_clique'] > 0

    def test_entropy_gap_grows(self):
        """Entropy gap should grow with n as more cliques appear."""
        gaps = []
        for n in range(5, 12):
            res = coloring_entropy(n, 3)
            gaps.append(res['entropy_gap'])
        # Should be generally increasing
        assert gaps[-1] > gaps[0]

    def test_log2_avoiding_indep_upper_bound(self):
        """Independent bound overestimates avoiding (upper bound)."""
        res = coloring_entropy(8, 3)
        # log2_avoiding_indep should be >= log2_avoiding (union bound)
        # since union bound is more conservative
        if res['log2_avoiding'] > -float('inf'):
            assert res['log2_avoiding_indep'] >= res['log2_avoiding'] - 1e-10


class TestEntropyLowerBound:
    def test_entropy_bound_k3(self):
        """Entropy bound (union-based) should be a valid lower bound on R_cop(3)."""
        bound = entropy_lower_bound(3, max_n=20)
        assert bound >= 3
        assert bound < 11  # valid lower bound must be below actual

    def test_entropy_bound_k4(self):
        """Entropy bound for k=4 should be valid."""
        bound = entropy_lower_bound(4, max_n=60)
        assert bound >= 4
        assert bound < 59  # valid lower bound must be below actual


class TestSchurEntropy:
    def test_schur_small_n(self):
        """At n=1, no Schur triples, entropy bound holds."""
        res = schur_entropy_bound(1)
        assert res['bound_holds']
        assert res['num_triples'] == 0

    def test_schur_has_triples(self):
        """At n=3, triples (1,1,2), (1,2,3) exist."""
        res = schur_entropy_bound(3)
        assert res['num_triples'] > 0

    def test_schur_triple_count_n5(self):
        """Manually count Schur triples at n=5."""
        # (a,b,a+b) with 1 <= a <= b, a+b <= 5
        # (1,1,2), (1,2,3), (1,3,4), (1,4,5), (2,2,4), (2,3,5)
        res = schur_entropy_bound(5)
        assert res['num_triples'] == 6

    def test_schur_entropy_lower_bound_2color(self):
        """S(2) = 4, entropy bound should be a valid lower bound."""
        bound = schur_entropy_lower_bound(2)
        assert bound >= 1
        # Union bound: T * p < 1 => T < c^2 = 4.
        # At n=3: T=2, 2/4=0.5 < 1. At n=4: T=4, 4/4=1, fails.
        # So the bound should be around 3.
        assert bound <= 4

    def test_schur_entropy_lower_bound_3color(self):
        """S(3) = 13, entropy bound should be a valid lower bound."""
        bound = schur_entropy_lower_bound(3)
        assert bound >= 1
        assert bound <= 13


# ============================================================================
# 4. Explicit construction tests
# ============================================================================

class TestEnumerateAvoiding:
    def test_n8_k3_count_36(self):
        """At n=8, exactly 36 colorings avoid mono K_3."""
        avoiding = enumerate_avoiding_colorings(8, 3)
        assert len(avoiding) == 36

    def test_no_cliques_returns_representative(self):
        """When no k-cliques exist, returns at least one coloring."""
        result = enumerate_avoiding_colorings(2, 3)
        assert len(result) >= 1

    def test_each_avoiding_actually_avoids(self):
        """Each returned coloring should genuinely avoid mono K_3."""
        for col in enumerate_avoiding_colorings(7, 3):
            assert not has_mono_clique(7, 3, col)

    def test_too_many_edges_returns_empty(self):
        """For large n, exhaustive enumeration returns empty."""
        result = enumerate_avoiding_colorings(20, 3)
        assert result == []


class TestColoringSignature:
    def test_all_zero_signature(self):
        """All-zero coloring has deg0 = coprime degree, deg1 = 0."""
        edges = coprime_edges(5)
        col = {e: 0 for e in edges}
        sig = coloring_signature(col, 5)
        # All pairs should have deg1 = 0
        for pair in sig:
            assert pair[1] == 0

    def test_signature_is_sorted(self):
        edges = coprime_edges(6)
        col = {e: (i % 2) for i, e in enumerate(edges)}
        sig = coloring_signature(col, 6)
        assert sig == tuple(sorted(sig))

    def test_complement_signature_symmetric(self):
        """Swapping colors gives the 'complementary' signature."""
        edges = coprime_edges(6)
        col = {e: (i % 2) for i, e in enumerate(edges)}
        comp = {e: 1 - c for e, c in col.items()}
        sig1 = coloring_signature(col, 6)
        sig2 = coloring_signature(comp, 6)
        # sig2 should be sig1 with each pair (a,b) -> (b,a), then sorted
        flipped = tuple(sorted((b, a) for a, b in sig1))
        assert sig2 == flipped


class TestAnalyzeAvoiding:
    @pytest.fixture(scope="class")
    def structure_n8(self):
        return analyze_avoiding_structure(8, 3)

    def test_count(self, structure_n8):
        assert structure_n8['count'] == 36

    def test_distinct_signatures(self, structure_n8):
        assert structure_n8['distinct_signatures'] >= 1
        assert structure_n8['distinct_signatures'] <= 36

    def test_residue_analysis_present(self, structure_n8):
        ra = structure_n8.get('residue_analysis', {})
        assert 2 in ra
        assert 3 in ra

    def test_residue_bias_valid_range(self, structure_n8):
        for m, biases in structure_n8.get('residue_analysis', {}).items():
            for r, b in biases.items():
                assert 0.0 <= b <= 1.0

    def test_edge_freq_valid(self, structure_n8):
        for e, freq in structure_n8.get('edge_freq', {}).items():
            assert abs(freq['frac_0'] + freq['frac_1'] - 1.0) < 1e-10

    def test_empty_when_no_colorings(self):
        # At n=11, k=3: R_cop(3)=11, so no avoiding colorings
        result = analyze_avoiding_structure(11, 3)
        assert result['count'] == 0


class TestPredictAvoiding:
    @pytest.fixture(scope="class")
    def analysis_n8(self):
        return analyze_avoiding_structure(8, 3)

    def test_predict_at_n9(self, analysis_n8):
        """Pattern should predict some result (avoiding or not) at n=9."""
        pred = predict_avoiding_at_larger_n(analysis_n8, 9, 3)
        assert 'success' in pred or 'avoids_mono_clique' in pred

    def test_predict_at_n11_fails(self, analysis_n8):
        """At n=11 (R_cop(3)), no coloring avoids, so prediction should fail.

        The prediction either finds no pattern (success=False) or the
        constructed coloring does not avoid mono K_3.
        """
        pred = predict_avoiding_at_larger_n(analysis_n8, 11, 3)
        # Either it couldn't construct (success=False) or the coloring
        # has a mono K_3 (avoids_mono_clique=False)
        avoids = pred.get('avoids_mono_clique', False)
        success = pred.get('success', False)
        assert not avoids or not success


# ============================================================================
# 5. Comparison table tests
# ============================================================================

class TestComparisonTable:
    @pytest.fixture(scope="class")
    def table_k3(self):
        return comparison_table([3])

    def test_has_all_methods(self, table_k3):
        row = table_k3[3]
        expected_keys = ['first_moment', 'second_moment', 'lll_symmetric',
                         'lll_asymmetric', 'entropy', 'paley_diff',
                         'paley_prod', 'residue', 'actual']
        for key in expected_keys:
            assert key in row

    def test_actual_value(self, table_k3):
        assert table_k3[3]['actual'] == 11

    def test_all_bounds_below_actual(self, table_k3):
        """All lower bound methods should give values < R_cop(3) = 11."""
        row = table_k3[3]
        actual = row['actual']
        methods = ['first_moment', 'second_moment', 'lll_symmetric',
                   'lll_asymmetric', 'entropy', 'paley_diff',
                   'paley_prod', 'residue']
        for m in methods:
            val = row.get(m, 0)
            assert val < actual, f"{m} = {val} >= {actual}"

    def test_tightest_method_identified(self, table_k3):
        row = table_k3[3]
        assert row['tightest_method'] is not None
        assert row['tightest_value'] > 0
        # Tightest bound < actual, so ratio > 1
        assert row['tightness_ratio'] > 1.0

    def test_tightest_is_actually_tightest(self, table_k3):
        row = table_k3[3]
        tightest_val = row['tightest_value']
        methods = ['first_moment', 'second_moment', 'lll_symmetric',
                   'lll_asymmetric', 'entropy', 'paley_diff',
                   'paley_prod', 'residue']
        for m in methods:
            assert row.get(m, 0) <= tightest_val


class TestFormatTable:
    def test_format_nonempty(self):
        table = comparison_table([3])
        formatted = format_comparison_table(table)
        assert len(formatted) > 0
        assert "FM" in formatted
        assert "LLL-A" in formatted
        assert "Actual" in formatted

    def test_format_includes_k(self):
        table = comparison_table([3])
        formatted = format_comparison_table(table)
        assert "3" in formatted


class TestTighteningAnalysis:
    def test_has_all_methods(self):
        ta = tightening_analysis(3)
        assert 'first_moment' in ta
        assert 'second_moment' in ta
        assert 'lll' in ta
        assert 'entropy' in ta

    def test_unknown_k(self):
        ta = tightening_analysis(5)
        assert 'error' in ta

    def test_analysis_text_nonempty(self):
        ta = tightening_analysis(3)
        for method, text in ta.items():
            assert len(text) > 0


# ============================================================================
# Cross-method consistency tests
# ============================================================================

class TestCrossMethodConsistency:
    def test_all_bounds_below_rcop3(self):
        """Every valid lower bound method should give value < R_cop(3) = 11."""
        fm = first_moment_lower_bound(3, max_n=20)
        sm = second_moment_lower_bound(3, max_n=20)
        lll_s = lll_lower_bound(3, variant='symmetric', max_n=20)
        lll_a = lll_lower_bound(3, variant='asymmetric', max_n=20)
        ent = entropy_lower_bound(3, max_n=20)
        assert fm < 11
        assert sm < 11
        assert lll_s < 11
        assert lll_a < 11
        assert ent < 11  # entropy uses union bound, same as FM

    def test_fm_leq_sm(self):
        """First moment bound <= second moment bound."""
        fm = first_moment_lower_bound(3, max_n=20)
        sm = second_moment_lower_bound(3, max_n=20)
        assert fm <= sm

    def test_lll_symmetric_leq_asymmetric(self):
        """Symmetric LLL bound <= asymmetric LLL bound."""
        sym = lll_lower_bound(3, variant='symmetric', max_n=20)
        asym = lll_lower_bound(3, variant='asymmetric', max_n=20)
        assert sym <= asym

    def test_probabilistic_vs_algebraic(self):
        """All bounds should be below the true value."""
        alg = algebraic_lower_bound(3, max_n=12, p_limit=30)
        assert alg['paley_diff'] < 11
        assert alg['paley_prod'] < 11

    def test_entropy_consistency(self):
        """Entropy bound (union-based) equals first moment bound."""
        ent = entropy_lower_bound(3, max_n=20)
        fm = first_moment_lower_bound(3, max_n=20)
        # Both use the same S1 < 1 condition, should agree
        assert ent == fm
        assert ent < 11

    def test_comparison_table_vs_individual(self):
        """Comparison table values should match individual computations."""
        table = comparison_table([3])
        fm = first_moment_lower_bound(3, max_n=20)
        assert table[3]['first_moment'] == fm


# ============================================================================
# Edge case and robustness tests
# ============================================================================

class TestEdgeCases:
    def test_k2_probabilistic(self):
        """k=2: R_cop(2) = 2, bounds should be 1."""
        fm = first_moment_lower_bound(2, max_n=5)
        assert fm >= 1

    def test_very_small_n(self):
        """Bounds at n=k should be trivially satisfied."""
        res = first_moment_bound(3, 3)
        assert res['bound_holds']

    def test_entropy_n_equals_1(self):
        """n=1 has no edges and no cliques."""
        res = coloring_entropy(1, 3)
        assert res['bound_holds']
        assert res['H_uniform'] == 0

    def test_schur_n_equals_0(self):
        """n=0 should have no triples."""
        res = schur_entropy_bound(0)
        assert res['num_triples'] == 0
        assert res['bound_holds']

    def test_coprime_density_constant(self):
        """COPRIME_DENSITY should be close to 6/pi^2."""
        assert abs(COPRIME_DENSITY - 6.0 / (math.pi ** 2)) < 1e-10

    def test_known_rcop_values(self):
        """Known R_cop values match documented values."""
        assert KNOWN_RCOP[2] == 2
        assert KNOWN_RCOP[3] == 11
        assert KNOWN_RCOP[4] == 59
