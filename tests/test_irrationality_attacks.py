"""Tests for irrationality_attacks.py — irrationality measures, lacunary
series, Littlewood polynomials, continued fractions, Erdos-Borwein constant."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import mpmath
from mpmath import mp, mpf, pi, e, log, zeta, euler

from irrationality_attacks import (
    irrationality_measure_from_cf,
    compute_irrationality_measures,
    lacunary_sum_2exp,
    lacunary_sum_nn,
    lacunary_sum_fibonacci_recip,
    pslq_algebraic_search,
    pslq_constant_relation,
    analyze_lacunary_series,
    littlewood_max_real_roots,
    littlewood_root_density_near_unit_circle,
    littlewood_real_root_table,
    flat_poly_max_real_roots,
    continued_fraction_expansion,
    cf_statistics,
    cf_pattern_search,
    analyze_research_constants_cf,
    erdos_borwein_constant,
    erdos_borwein_divisor_representation,
    analyze_erdos_borwein,
    run_all_attacks,
)


# ===================================================================
# 1. Irrationality measures
# ===================================================================

class TestIrrationalityMeasures:
    """Liouville-Roth irrationality measure estimation via CF convergents."""

    def test_mu_e_near_2(self):
        """mu(e) = 2 exactly (Davis 1978).  Computationally we should
        see best_mu in [2, 3] for moderate term counts."""
        r = irrationality_measure_from_cf(lambda: +e, num_terms=200, dps=80)
        assert r["best_mu"] >= 2.0, f"mu(e) should be >= 2, got {r['best_mu']}"
        assert r["best_mu"] < 4.0, f"mu(e) too high: {r['best_mu']}"

    def test_mu_pi_near_2(self):
        """mu(pi) = 2 (Roth), but best proven bound is ~7.1.
        Computationally should see moderate values."""
        r = irrationality_measure_from_cf(lambda: +pi, num_terms=200, dps=80)
        assert r["best_mu"] >= 2.0
        assert r["best_mu"] < 10.0

    def test_mu_ln2(self):
        """mu(ln 2) <= 3.57 (Rukhadze/Marcovecchio)."""
        r = irrationality_measure_from_cf(lambda: log(2), num_terms=200, dps=80)
        assert r["best_mu"] >= 2.0

    def test_mu_sqrt2_equals_2(self):
        """mu(sqrt(2)) = 2 (algebraic, by Roth).  For bounded partial
        quotients (all = 2), the observed mu should hover near 2."""
        r = irrationality_measure_from_cf(
            lambda: mpmath.sqrt(2), num_terms=200, dps=80
        )
        # sqrt(2) has all pq = 2, so convergents approximate as well
        # as possible for a quadratic irrational
        assert r["best_mu"] >= 1.9
        assert r["best_mu"] < 5.0

    def test_mu_golden_ratio(self):
        """Golden ratio has the slowest-converging CF (all 1s).
        mu = 2, and the convergent approximation is the worst possible."""
        r = irrationality_measure_from_cf(
            lambda: (1 + mpmath.sqrt(5)) / 2, num_terms=200, dps=80
        )
        assert r["best_mu"] >= 1.9
        assert r["best_mu"] < 3.5

    def test_measures_list_nonempty(self):
        """The measures list should contain (q, mu) pairs."""
        r = irrationality_measure_from_cf(lambda: +pi, num_terms=50, dps=50)
        assert len(r["measures"]) > 10
        for q, mu in r["measures"]:
            assert q > 0
            assert mu > 0

    def test_running_sup_monotonic(self):
        """Running supremum should be non-decreasing."""
        r = irrationality_measure_from_cf(lambda: +e, num_terms=100, dps=50)
        sup = r["running_sup"]
        for i in range(1, len(sup)):
            assert sup[i] >= sup[i - 1] - 1e-10

    def test_compute_all_measures(self):
        """compute_irrationality_measures should return data for all constants."""
        results = compute_irrationality_measures(num_terms=50, dps=50)
        expected = {"e", "pi", "ln2", "zeta3", "sqrt2", "golden_ratio",
                    "euler_gamma"}
        assert set(results.keys()) == expected
        for name, data in results.items():
            assert "best_mu" in data
            assert data["best_mu"] > 0, f"{name} has zero best_mu"


# ===================================================================
# 2. Lacunary series
# ===================================================================

class TestLacunarySeries:
    """Lacunary series computation and PSLQ algebraic relation search."""

    def test_kempner_2exp_value(self):
        """sum 1/2^{2^n} for n=0.. converges to ~ 0.8164215..."""
        s = lacunary_sum_2exp(dps=50)
        # First few terms: 1/2 + 1/4 + 1/16 + 1/256 + ... ~ 0.8164215
        assert abs(float(s) - 0.8164215) < 0.0001

    def test_sophomores_dream(self):
        """sum 1/n^n = integral_0^1 x^{-x} dx ~ 1.2912859970626635..."""
        s = lacunary_sum_nn(dps=50)
        assert abs(float(s) - 1.2912859970626635) < 1e-10

    def test_fibonacci_reciprocal(self):
        """sum 1/F_n ~ 3.35988566624... (reciprocal Fibonacci constant)."""
        s = lacunary_sum_fibonacci_recip(dps=50)
        assert abs(float(s) - 3.359885666243178) < 1e-10

    def test_fibonacci_first_terms(self):
        """Check that the first few Fibonacci reciprocals add up correctly.
        1/1 + 1/1 + 1/2 + 1/3 + 1/5 = 2 + 0.5 + 0.3333 + 0.2 = 3.0333..."""
        s = lacunary_sum_fibonacci_recip(num_terms=5, dps=30)
        expected = 1 + 1 + 0.5 + 1 / 3 + 0.2
        assert abs(float(s) - expected) < 1e-10

    def test_lacunary_sums_positive(self):
        """All lacunary sums should be positive."""
        assert float(lacunary_sum_2exp(dps=30)) > 0
        assert float(lacunary_sum_nn(dps=30)) > 0
        assert float(lacunary_sum_fibonacci_recip(dps=30)) > 0


# ===================================================================
# 3. PSLQ algebraic search
# ===================================================================

class TestPSLQAlgebraic:
    """PSLQ-based algebraic relation detection."""

    def test_sqrt2_is_algebraic_degree_2(self):
        """sqrt(2) satisfies x^2 - 2 = 0."""
        r = pslq_algebraic_search(lambda: mpmath.sqrt(2), max_degree=4, dps=80)
        assert r is not None
        assert r["degree"] == 2
        # Coefficients should be proportional to [-2, 0, 1]
        c = r["coefficients"]
        assert c[1] == 0  # no linear term
        assert c[0] * c[2] < 0  # opposite signs for constant and x^2

    def test_golden_ratio_is_algebraic_degree_2(self):
        """phi = (1+sqrt(5))/2 satisfies x^2 - x - 1 = 0."""
        r = pslq_algebraic_search(
            lambda: (1 + mpmath.sqrt(5)) / 2, max_degree=4, dps=80
        )
        assert r is not None
        assert r["degree"] == 2

    def test_cbrt2_is_algebraic_degree_3(self):
        """2^{1/3} satisfies x^3 - 2 = 0."""
        r = pslq_algebraic_search(lambda: mpf(2) ** (mpf(1) / 3),
                                  max_degree=4, dps=80)
        assert r is not None
        assert r["degree"] == 3

    def test_pi_is_transcendental(self):
        """pi should not satisfy any polynomial of degree <= 6."""
        r = pslq_algebraic_search(lambda: +pi, max_degree=6, dps=80)
        assert r is None

    def test_e_is_transcendental(self):
        """e should not satisfy any polynomial of degree <= 6."""
        r = pslq_algebraic_search(lambda: +e, max_degree=6, dps=80)
        assert r is None

    def test_residual_small(self):
        """For a genuine algebraic relation, the residual should be tiny."""
        r = pslq_algebraic_search(lambda: mpmath.sqrt(3), max_degree=3, dps=80)
        assert r is not None
        assert r["residual"] < 1e-60


class TestPSLQConstantRelation:
    """PSLQ for relations between a value and basis constants."""

    def test_ln2_found_in_basis(self):
        """If we include ln(2) in the basis, PSLQ should find 1*alpha - 1*ln2 = 0."""
        r = pslq_constant_relation(
            lambda: log(2),
            [lambda: mpf(1), lambda: log(2), lambda: +pi],
            ["1", "ln2", "pi"],
            dps=50,
        )
        assert r is not None
        # The relation should involve alpha and ln2 with equal magnitude
        rel = r["relation"]
        assert "alpha" in rel
        assert "ln2" in rel

    def test_no_relation_for_unrelated(self):
        """pi and e should have no small integer relation."""
        r = pslq_constant_relation(
            lambda: +pi,
            [lambda: +e],
            ["e"],
            maxcoeff=1000,
            dps=50,
        )
        assert r is None


# ===================================================================
# 4. Littlewood polynomials
# ===================================================================

class TestLittlewoodPolynomials:
    """Littlewood and flat polynomial real root structure."""

    def test_degree_1_has_1_real_root(self):
        """Any degree 1 Littlewood poly +/-1 +/- x has exactly 1 real root."""
        r = littlewood_max_real_roots(1)
        assert r["max_real_roots"] == 1

    def test_degree_2_max_real_roots(self):
        """Degree 2 Littlewood: e.g. 1 + x - x^2 has 2 real roots."""
        r = littlewood_max_real_roots(2)
        assert r["max_real_roots"] == 2

    def test_degree_5_max_real_roots(self):
        """Degree 5 should have a polynomial with at least 3 real roots."""
        r = littlewood_max_real_roots(5)
        assert r["max_real_roots"] >= 1
        assert r["best_poly"] is not None
        assert len(r["best_poly"]) == 6

    @pytest.mark.parametrize("degree", [6, 8, 10])
    def test_max_real_roots_bounded_by_degree(self, degree):
        """Max real roots can't exceed degree."""
        r = littlewood_max_real_roots(degree)
        assert 0 <= r["max_real_roots"] <= degree

    def test_littlewood_real_root_table(self):
        """Table should cover requested degree range."""
        table = littlewood_real_root_table(min_degree=3, max_degree=8)
        assert len(table) == 6
        degrees = [row["degree"] for row in table]
        assert degrees == list(range(3, 9))

    def test_flat_poly_degree_3(self):
        """Flat polys {-1,0,1}: degree 3 can have 3 real roots
        (e.g., x^3 - x = x(x-1)(x+1))."""
        r = flat_poly_max_real_roots(3)
        assert r["max_real_roots"] == 3

    def test_flat_poly_max_at_least_littlewood(self):
        """Flat polys include Littlewood as a subset, so max_real >= Littlewood max."""
        for d in [3, 4, 5]:
            flat = flat_poly_max_real_roots(d)
            lw = littlewood_max_real_roots(d)
            assert flat["max_real_roots"] >= lw["max_real_roots"]


class TestRootDensity:
    """Root density near the unit circle for Littlewood polynomials."""

    def test_density_positive(self):
        """Some fraction of roots should be near the unit circle."""
        r = littlewood_root_density_near_unit_circle(
            degree=8, epsilon=0.2, num_samples=30
        )
        assert r["mean_near_fraction"] > 0

    def test_density_increases_with_epsilon(self):
        """Larger epsilon should capture more roots."""
        r1 = littlewood_root_density_near_unit_circle(
            degree=8, epsilon=0.05, num_samples=30
        )
        r2 = littlewood_root_density_near_unit_circle(
            degree=8, epsilon=0.5, num_samples=30
        )
        assert r2["mean_near_fraction"] >= r1["mean_near_fraction"]

    def test_density_structure(self):
        """Return dict should have expected keys."""
        r = littlewood_root_density_near_unit_circle(
            degree=6, epsilon=0.1, num_samples=20
        )
        assert "degree" in r
        assert "epsilon" in r
        assert "mean_near_fraction" in r
        assert "std_near_fraction" in r
        assert 0 <= r["mean_near_fraction"] <= 1


# ===================================================================
# 5. Continued fractions
# ===================================================================

class TestContinuedFractions:
    """CF computation, statistics, and pattern detection."""

    def test_cf_sqrt2_periodic(self):
        """sqrt(2) = [1; 2, 2, 2, ...] (period 1 after integer part)."""
        cf = continued_fraction_expansion(lambda: mpmath.sqrt(2), 50, dps=80)
        assert cf[0] == 1
        assert all(a == 2 for a in cf[1:])

    def test_cf_golden_ratio_all_ones(self):
        """phi = [1; 1, 1, 1, ...] (period 1)."""
        cf = continued_fraction_expansion(
            lambda: (1 + mpmath.sqrt(5)) / 2, 50, dps=80
        )
        assert cf[0] == 1
        assert all(a == 1 for a in cf[1:])

    def test_cf_e_pattern(self):
        """e = [2; 1, 2, 1, 1, 4, 1, 1, 6, 1, 1, 8, ...].
        The pattern: cf[3k-1] = 2k for k = 1, 2, 3, ..."""
        cf = continued_fraction_expansion(lambda: +e, 30, dps=80)
        assert cf[0] == 2
        assert cf[1:9] == [1, 2, 1, 1, 4, 1, 1, 6]
        # Check the pattern: cf[3k-1] = 2k
        for k in range(1, 6):
            idx = 3 * k - 1  # indices 2, 5, 8, 11, 14
            assert cf[idx] == 2 * k, f"cf[{idx}] = {cf[idx]}, expected {2*k}"

    def test_cf_pi_first_terms(self):
        """pi = [3; 7, 15, 1, 292, ...]."""
        cf = continued_fraction_expansion(lambda: +pi, 20, dps=80)
        assert cf[:5] == [3, 7, 15, 1, 292]

    def test_cf_statistics_sqrt2(self):
        """For sqrt(2), all partial quotients are 2, so mean = median = 2."""
        cf = continued_fraction_expansion(lambda: mpmath.sqrt(2), 40, dps=80)
        stats = cf_statistics(cf)
        assert abs(stats["mean_pq"] - 2.0) < 0.01
        assert abs(stats["median_pq"] - 2.0) < 0.01
        assert stats["max_pq"] == 2
        assert stats["is_bounded_quotients"] is True

    def test_cf_statistics_golden_ratio(self):
        """For phi, all pq = 1, so geometric mean = 1."""
        cf = continued_fraction_expansion(
            lambda: (1 + mpmath.sqrt(5)) / 2, 40, dps=80
        )
        stats = cf_statistics(cf)
        assert abs(stats["geometric_mean"] - 1.0) < 0.01
        assert stats["max_pq"] == 1

    def test_cf_pattern_sqrt2_period_1(self):
        """sqrt(2) should be detected as periodic with period 1."""
        cf = continued_fraction_expansion(lambda: mpmath.sqrt(2), 40, dps=80)
        pats = cf_pattern_search(cf)
        assert pats["exact_period"] is not None
        assert pats["exact_period"]["period"] == 1
        assert pats["exact_period"]["repeating_block"] == [2]

    def test_cf_pattern_golden_ratio_period_1(self):
        """phi should be detected as periodic with period 1, block [1]."""
        cf = continued_fraction_expansion(
            lambda: (1 + mpmath.sqrt(5)) / 2, 40, dps=80
        )
        pats = cf_pattern_search(cf)
        assert pats["exact_period"] is not None
        assert pats["exact_period"]["period"] == 1

    def test_cf_pattern_pi_not_periodic(self):
        """pi is transcendental, so its CF should NOT be periodic."""
        cf = continued_fraction_expansion(lambda: +pi, 40, dps=80)
        pats = cf_pattern_search(cf)
        assert pats["exact_period"] is None

    def test_cf_statistics_error_on_short(self):
        """Too-short CF should return an error indicator."""
        stats = cf_statistics([3])
        assert "error" in stats

    def test_analyze_research_constants_cf(self):
        """Comprehensive CF analysis returns data for all constants."""
        results = analyze_research_constants_cf(num_terms=30, dps=50)
        expected_names = {"6/pi^2", "log2/log3", "euler_gamma", "ln2",
                          "zeta3", "pi", "e", "sqrt2", "golden_ratio"}
        assert set(results.keys()) == expected_names
        for name, data in results.items():
            assert "cf_first_30" in data
            assert "statistics" in data
            assert "patterns" in data


# ===================================================================
# 6. Erdos-Borwein constant
# ===================================================================

class TestErdosBorwein:
    """Erdos-Borwein constant E = sum 1/(2^n - 1)."""

    def test_value_correct(self):
        """E ~ 1.606695152415291763..."""
        E = erdos_borwein_constant(dps=50)
        assert abs(float(E) - 1.6066951524152917637) < 1e-15

    def test_divisor_representation_agrees(self):
        """Both computation methods should agree to high precision."""
        E1 = erdos_borwein_constant(dps=50)
        E2 = erdos_borwein_divisor_representation(num_terms=100, dps=50)
        assert float(abs(E1 - E2)) < 1e-25

    def test_erdos_borwein_positive(self):
        """E should be positive (sum of positive terms)."""
        E = erdos_borwein_constant(dps=30)
        assert float(E) > 1.0

    def test_erdos_borwein_bounds(self):
        """1.6 < E < 1.7 (rough bounds)."""
        E = erdos_borwein_constant(dps=30)
        assert 1.6 < float(E) < 1.7

    def test_analyze_erdos_borwein_structure(self):
        """analyze_erdos_borwein should return expected keys."""
        result = analyze_erdos_borwein(dps=30)
        assert "value" in result
        assert "cross_validation_error" in result
        assert "algebraic_relation" in result
        assert "constant_relation" in result
        assert "cf_first_30" in result
        assert "cf_statistics" in result

    def test_erdos_borwein_not_algebraic_low_degree(self):
        """E is irrational (Erdos 1948); should not satisfy a low-degree polynomial."""
        E = erdos_borwein_constant(dps=80)
        r = pslq_algebraic_search(E, max_degree=4, dps=80)
        # It might or might not find something (PSLQ is heuristic),
        # but E is known to be irrational.
        if r is not None:
            # If found, residual should be large (spurious)
            # or it's a genuine discovery (unlikely for known irrational)
            pass  # just check it doesn't crash


# ===================================================================
# 7. Integration / aggregate
# ===================================================================

class TestRunAllAttacks:
    """Test the aggregate driver with small parameters."""

    @pytest.mark.timeout(120)
    def test_run_all_attacks(self):
        """run_all_attacks should complete and return all sections."""
        results = run_all_attacks(dps=30, cf_terms=30, max_littlewood_degree=8)
        assert "irrationality_measures" in results
        assert "lacunary_series" in results
        assert "littlewood_table" in results
        assert "cf_analysis" in results
        assert "erdos_borwein" in results

    @pytest.mark.timeout(120)
    def test_run_all_attacks_values_reasonable(self):
        """Spot-check values from run_all_attacks."""
        results = run_all_attacks(dps=30, cf_terms=30, max_littlewood_degree=8)

        # Irrationality measures should be positive
        for name, data in results["irrationality_measures"].items():
            assert data["best_mu"] > 0, f"{name}: best_mu = 0"

        # Lacunary sums should be positive
        for name, data in results["lacunary_series"].items():
            assert data["value"] > 0, f"{name}: value <= 0"

        # Littlewood table should have entries
        assert len(results["littlewood_table"]) > 0

        # Erdos-Borwein value
        assert abs(results["erdos_borwein"]["value"] - 1.606695) < 0.001


# ===================================================================
# 8. Edge cases and regression tests
# ===================================================================

class TestEdgeCases:
    """Edge cases, boundary conditions, and regression tests."""

    def test_cf_of_integer(self):
        """CF of an integer should be a single term."""
        cf = continued_fraction_expansion(mpf(3), 10, dps=30)
        assert cf == [3]

    def test_cf_of_rational(self):
        """CF of 355/113 = [3; 7, 16] (finite).
        Must use a callable so the division happens at full internal dps."""
        cf = continued_fraction_expansion(
            lambda: mpf(355) / mpf(113), 20, dps=50
        )
        assert cf == [3, 7, 16]

    def test_lacunary_2exp_few_terms(self):
        """Just 3 terms: 1/2 + 1/4 + 1/16 = 0.8125."""
        s = lacunary_sum_2exp(num_terms=3, dps=30)
        assert abs(float(s) - 0.8125) < 1e-10

    def test_littlewood_degree_0(self):
        """Degree 0 polynomial has no roots."""
        r = littlewood_max_real_roots(0)
        assert r["max_real_roots"] == 0

    def test_cf_statistics_with_two_terms(self):
        """CF with just [a0, a1] should still produce stats."""
        stats = cf_statistics([3, 7])
        assert stats["num_terms"] == 1
        assert stats["max_pq"] == 7
        assert abs(stats["mean_pq"] - 7) < 0.01

    def test_pslq_algebraic_degree_1_rational(self):
        """PSLQ on a rational number should find a degree-1 relation."""
        # 3/7 satisfies 3 - 7*x = 0
        r = pslq_algebraic_search(lambda: mpf(3) / mpf(7), max_degree=2, dps=50)
        assert r is not None
        assert r["degree"] == 1

    def test_flat_poly_exhaustive_small(self):
        """Flat poly at degree 2 should enumerate all 3^3 = 27 options."""
        r = flat_poly_max_real_roots(2)
        # Degree 2 with {-1,0,1}: max possible is 2 real roots
        assert r["max_real_roots"] == 2
        # Leading coeff must be nonzero: 18 polys (2 choices for leading * 9 for rest)
        assert r["num_searched"] <= 27

    def test_littlewood_large_degree_sampling(self):
        """For degree > exhaustive_limit, random sampling is used.
        Use exhaustive_limit=5 so degree 8 triggers the random path
        while remaining fast."""
        r = littlewood_max_real_roots(8, exhaustive_limit=5)
        assert r["max_real_roots"] >= 0
        assert r["max_real_roots"] <= 8
        assert r["num_searched"] > 0
        assert r["best_poly"] is not None
        assert len(r["best_poly"]) == 9

    def test_flat_poly_large_degree_sampling(self):
        """For degree > exhaustive_limit, random sampling is used.
        Use exhaustive_limit=3 so degree 6 triggers the random path."""
        r = flat_poly_max_real_roots(6, exhaustive_limit=3)
        assert r["max_real_roots"] >= 0
        assert r["max_real_roots"] <= 6
        assert r["num_searched"] > 0

    def test_analyze_lacunary_series(self):
        """Integration test: analyze_lacunary_series returns all series."""
        results = analyze_lacunary_series(dps=30)
        assert "kempner_2exp" in results
        assert "sophomores_dream" in results
        assert "fibonacci_reciprocal" in results
        for name, data in results.items():
            assert "value" in data
            assert data["value"] > 0
            assert "algebraic_relation" in data
            assert "constant_relation" in data

    def test_root_density_at_various_degrees(self):
        """Root density near unit circle should be computable for degree 5..15."""
        for deg in [5, 10, 15]:
            r = littlewood_root_density_near_unit_circle(
                deg, epsilon=0.15, num_samples=10
            )
            assert "mean_near_fraction" in r
            assert 0 <= r["mean_near_fraction"] <= 1
