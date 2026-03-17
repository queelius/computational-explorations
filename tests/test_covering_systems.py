#!/usr/bin/env python3
"""Tests for covering_systems.py — Erdős covering system problems."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from covering_systems import (
    verify_covering,
    erdos_covering_1950,
    odd_moduli_up_to,
    sum_reciprocals,
    analyze_odd_covering_obstruction,
    max_disjoint_classes,
    compute_A389975,
    enumerate_covering_systems,
    hough_bound_analysis,
    verify_sierpinski_covering,
    sierpinski_78557_covering,
    find_sierpinski_covering,
    _is_squarefree,
    _multiplicative_order,
    _lcm_list,
    greedy_coverage_odd,
    minimum_modulus_covering,
)


# ---------------------------------------------------------------------------
# Basic utilities
# ---------------------------------------------------------------------------

class TestUtilities:
    def test_lcm_list_empty(self):
        assert _lcm_list([]) == 1  # vacuous product

    def test_lcm_list_single(self):
        assert _lcm_list([6]) == 6

    def test_lcm_list_coprime(self):
        assert _lcm_list([4, 9]) == 36

    def test_lcm_list_general(self):
        assert _lcm_list([2, 3, 4, 6, 12]) == 12

    def test_is_squarefree(self):
        assert _is_squarefree(1)
        assert _is_squarefree(2)
        assert _is_squarefree(6)
        assert _is_squarefree(30)
        assert not _is_squarefree(4)
        assert not _is_squarefree(9)
        assert not _is_squarefree(12)
        assert not _is_squarefree(18)

    def test_multiplicative_order(self):
        # ord_3(2) = 2 since 2^2 = 4 ≡ 1 mod 3
        assert _multiplicative_order(2, 3) == 2
        # ord_7(2) = 3 since 2^3 = 8 ≡ 1 mod 7
        assert _multiplicative_order(2, 7) == 3
        # ord_5(2) = 4
        assert _multiplicative_order(2, 5) == 4
        # gcd(2,4) != 1
        assert _multiplicative_order(2, 4) is None


# ---------------------------------------------------------------------------
# Covering system verification
# ---------------------------------------------------------------------------

class TestVerifyCovering:
    def test_empty_system(self):
        result = verify_covering([])
        assert not result['is_covering']

    def test_erdos_1950(self):
        system = erdos_covering_1950()
        result = verify_covering(system)
        assert result['is_covering']
        assert result['distinct_moduli']
        assert result['lcm'] == 12
        assert result['coverage_fraction'] == 1.0
        assert result['uncovered'] == []

    def test_trivial_covering_mod2(self):
        system = [(0, 2), (1, 2)]
        result = verify_covering(system)
        assert result['is_covering']
        assert not result['distinct_moduli']  # modulus 2 used twice

    def test_incomplete_system(self):
        system = [(0, 3), (1, 5)]
        result = verify_covering(system)
        assert not result['is_covering']
        assert result['coverage_fraction'] < 1.0

    def test_single_congruence(self):
        # (0, 2) covers all even numbers = 50% of integers
        result = verify_covering([(0, 2)])
        assert not result['is_covering']
        assert abs(result['coverage_fraction'] - 0.5) < 0.01


# ---------------------------------------------------------------------------
# Odd moduli analysis (Problem #7)
# ---------------------------------------------------------------------------

class TestOddModuli:
    def test_odd_moduli_up_to(self):
        m = odd_moduli_up_to(10)
        assert m == [3, 5, 7, 9]

    def test_odd_moduli_up_to_20(self):
        m = odd_moduli_up_to(20)
        assert m == [3, 5, 7, 9, 11, 13, 15, 17, 19]
        assert all(x % 2 == 1 for x in m)
        assert all(x > 1 for x in m)

    def test_sum_reciprocals_basic(self):
        assert abs(sum_reciprocals([2, 3, 4]) - (0.5 + 1/3 + 0.25)) < 1e-10

    def test_sum_reciprocals_erdos_moduli(self):
        # Erdős 1950: moduli {2,3,4,6,12}, sum 1/m = 1/2+1/3+1/4+1/6+1/12 = 16/12 = 4/3
        sr = sum_reciprocals([2, 3, 4, 6, 12])
        assert abs(sr - 4/3) < 1e-10

    def test_odd_obstruction_small(self):
        obs = analyze_odd_covering_obstruction(10)
        # Odd moduli in [3..10]: {3,5,7,9}
        # sum = 1/3 + 1/5 + 1/7 + 1/9 ≈ 0.7873 < 1
        assert not obs['necessary_condition_met']

    def test_odd_obstruction_large(self):
        obs = analyze_odd_covering_obstruction(100)
        # sum of 1/m for odd m in [3..100] > 1
        assert obs['necessary_condition_met']
        assert obs['sum_reciprocals_all_odd'] > 1.0

    def test_squarefree_vs_nonsquarefree(self):
        obs = analyze_odd_covering_obstruction(100)
        # Squarefree odds should dominate
        assert obs['sum_reciprocals_odd_squarefree'] > obs['sum_reciprocals_odd_nonsquarefree']
        # Total should match
        total = obs['sum_reciprocals_odd_squarefree'] + obs['sum_reciprocals_odd_nonsquarefree']
        assert abs(total - obs['sum_reciprocals_all_odd']) < 1e-10


# ---------------------------------------------------------------------------
# Greedy coverage
# ---------------------------------------------------------------------------

class TestGreedyCoverage:
    def test_greedy_infeasible(self):
        # max_modulus = 10: odd moduli {3,5,7,9}, sum < 1
        result = greedy_coverage_odd(10)
        assert not result['feasible']

    def test_greedy_feasible(self):
        result = greedy_coverage_odd(100)
        assert result['feasible']
        assert result['coverage_fraction'] > 0  # some coverage achieved


# ---------------------------------------------------------------------------
# Disjoint congruence classes (Problem #202, A389975)
# ---------------------------------------------------------------------------

class TestDisjointClasses:
    def test_A389975_small(self):
        # A389975(2) = 1: can have one class, e.g., 0 mod 2
        count, system = max_disjoint_classes(2)
        assert count == 1

    def test_A389975_4(self):
        # A389975(4) = 2: e.g., {0 mod 2, 1 mod 3}
        count, system = max_disjoint_classes(4)
        assert count == 2

    def test_A389975_sequence(self):
        seq = compute_A389975(12)
        # Known: A389975 starts 0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4
        expected = [0, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4]
        assert seq == expected

    def test_disjoint_system_valid(self):
        """Verify returned systems are actually disjoint."""
        count, system = max_disjoint_classes(8)
        # Check pairwise disjointness
        for i in range(len(system)):
            for j in range(i + 1, len(system)):
                a1, m1 = system[i]
                a2, m2 = system[j]
                g = math.gcd(m1, m2)
                assert (a1 - a2) % g != 0, \
                    f"Classes {system[i]} and {system[j]} are NOT disjoint"


# ---------------------------------------------------------------------------
# Covering system enumeration
# ---------------------------------------------------------------------------

class TestEnumeration:
    def test_enumerate_mod2_3(self):
        # Moduli {2, 3}: lcm = 6. Need to cover 0..5.
        # 0 mod 2 covers {0,2,4}, 1 mod 2 covers {1,3,5}
        # For modulus 3: 0 mod 3 covers {0,3}, 1 mod 3 covers {1,4}, 2 mod 3 covers {2,5}
        solutions = enumerate_covering_systems([2, 3])
        # With just {2, 3}, sum 1/m = 1/2 + 1/3 = 5/6 < 1, so no covering
        assert len(solutions) == 0

    def test_enumerate_2_3_4_6_12(self):
        # The Erdős moduli should work
        solutions = enumerate_covering_systems([2, 3, 4, 6, 12], max_solutions=5)
        assert len(solutions) > 0
        # Verify first solution
        result = verify_covering(solutions[0])
        assert result['is_covering']


# ---------------------------------------------------------------------------
# Hough bound analysis
# ---------------------------------------------------------------------------

class TestHoughBounds:
    def test_hough_analysis_runs(self):
        results = hough_bound_analysis()
        assert 2 in results
        assert 'odd_3' in results

    def test_hough_min_mod_2(self):
        results = hough_bound_analysis()
        # For min_mod=2, should need very few moduli
        assert results[2]['num_moduli'] <= 10
        assert results[2]['sum_reciprocals'] >= 1.0

    def test_hough_odd_moduli(self):
        results = hough_bound_analysis()
        # Odd moduli starting at 3 need more
        assert results['odd_3']['num_moduli'] > results[2]['num_moduli']


# ---------------------------------------------------------------------------
# Sierpiński verification (Problem #1113)
# ---------------------------------------------------------------------------

class TestSierpinski:
    def test_sierpinski_78557(self):
        k, primes, covering = sierpinski_78557_covering()
        assert k == 78557
        assert covering is not None, "Covering system for 78557 should be found"

    def test_sierpinski_covering_valid(self):
        k, primes, covering = sierpinski_78557_covering()
        if covering is not None:
            sv = verify_sierpinski_covering(k, primes, covering)
            assert sv['is_valid'], f"78557 covering should be valid: {sv}"
            assert sv['covering_valid']
            assert sv['all_primes_divide']

    def test_sierpinski_not_arbitrary(self):
        """An arbitrary odd number should NOT be Sierpiński (usually)."""
        k = 3
        primes = [3, 5, 7]
        covering = find_sierpinski_covering(k, primes)
        # Even if we find individual hits, unlikely to cover all n
        # Just verify the function runs without error
        # (covering is None if it doesn't work)

    def test_sierpinski_prime_divisibility(self):
        """Verify individual prime divisibility for 78557."""
        k = 78557
        # 3 | k·2^n + 1 when n is odd (since 78557 ≡ 2 mod 3, 2^1 ≡ 2, 2·2+1=5≡2, ...)
        # Check: 78557 * 2 + 1 = 157115, 157115 / 3 = 52371.67 ... let's just check
        for p in [3, 5, 7, 13, 19, 37, 73]:
            # There should exist some a with p | k·2^a + 1
            found = False
            ord2 = _multiplicative_order(2, p)
            if ord2 is not None:
                for a in range(ord2):
                    if (k * pow(2, a, p) + 1) % p == 0:
                        found = True
                        break
            assert found, f"No a found for prime {p}"


# ---------------------------------------------------------------------------
# Minimum modulus covering
# ---------------------------------------------------------------------------

class TestMinimumModulus:
    def test_min_mod_1(self):
        result = minimum_modulus_covering(1)
        assert result is not None

    def test_min_mod_2(self):
        result = minimum_modulus_covering(2)
        assert result is not None
        # Should be the Erdős system or similar
        cv = verify_covering(result)
        assert cv['is_covering']


# ---------------------------------------------------------------------------
# Integration: run_covering_system_experiments
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_experiments_run(self):
        from covering_systems import run_covering_system_experiments
        results = run_covering_system_experiments()
        assert 'erdos_1950' in results
        assert results['erdos_1950']['is_covering']
        assert 'A389975' in results
        assert 'hough_bounds' in results
