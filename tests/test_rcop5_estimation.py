"""Tests for rcop5_estimation.py — R_cop(5) frontier estimation."""

import math
import sys
from pathlib import Path

import pytest
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rcop5_estimation import (
    coprime_adj_sets,
    coprime_edge_list,
    coprime_edge_count,
    enumerate_5cliques_containing,
    count_5cliques_up_to,
    sat_lower_bound,
    sat_timing_extrapolation,
    clique_counting_analysis,
    monte_carlo_avoiding_fraction,
    phase_transition_analysis,
    generate_report,
    KNOWN_RCOP,
    COPRIME_DENSITY,
    PRED_QUADRATIC,
    PRED_EXPONENTIAL,
    PRED_RATIO,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_known_rcop_values(self):
        assert KNOWN_RCOP == {2: 2, 3: 11, 4: 59}

    def test_coprime_density(self):
        assert abs(COPRIME_DENSITY - 6.0 / math.pi**2) < 1e-10

    def test_predictions_are_primes(self):
        """Predicted R_cop(5) values should be prime."""
        from sympy import isprime
        assert isprime(PRED_QUADRATIC)  # 157
        assert isprime(PRED_EXPONENTIAL)  # 241

    def test_prediction_values(self):
        assert PRED_QUADRATIC == 157
        assert PRED_EXPONENTIAL == 241
        assert PRED_RATIO == 316

    def test_prime_indices(self):
        """Verify p_37 = 157 and p_53 = 241."""
        from sympy import prime
        assert prime(37) == 157
        assert prime(53) == 241


# ---------------------------------------------------------------------------
# Graph infrastructure
# ---------------------------------------------------------------------------

class TestCoprimeGraph:
    def test_adj_symmetry(self):
        adj = coprime_adj_sets(20)
        for u in range(1, 21):
            for v in adj[u]:
                assert u in adj[v], f"Asymmetry: {u} -> {v} but not {v} -> {u}"

    def test_adj_coprimality(self):
        adj = coprime_adj_sets(15)
        for u in range(1, 16):
            for v in adj[u]:
                assert math.gcd(u, v) == 1, f"Non-coprime edge: ({u}, {v})"

    def test_edge_list_sorted(self):
        edges = coprime_edge_list(10)
        for i, j in edges:
            assert i < j, f"Unsorted edge: ({i}, {j})"

    def test_edge_count_matches_list(self):
        for n in [5, 10, 15, 20]:
            assert coprime_edge_count(n) == len(coprime_edge_list(n))

    def test_no_self_loops(self):
        adj = coprime_adj_sets(20)
        for v in range(1, 21):
            assert v not in adj[v]

    def test_1_adjacent_to_all(self):
        """Vertex 1 is coprime to everything."""
        adj = coprime_adj_sets(20)
        assert adj[1] == set(range(2, 21))


# ---------------------------------------------------------------------------
# 5-clique enumeration
# ---------------------------------------------------------------------------

class TestFiveCliqueEnumeration:
    def test_small_n_no_5cliques(self):
        """Need at least 5 vertices for a 5-clique."""
        count, _ = count_5cliques_up_to(4)
        assert count == 0

    def test_n5_check(self):
        """At n=5, {1,2,3,4,5}: check if there's a 5-clique.
        gcd(2,4)=2, so {1,2,3,4,5} is NOT a 5-clique."""
        count, _ = count_5cliques_up_to(5)
        # {1,2,3,5,*}: need 5 mutually coprime from {1,2,3,4,5}
        # 2 and 4 share factor 2 -> no 5-clique
        assert count == 0

    def test_n7_first_5cliques(self):
        """At n=7, {1,2,3,5,7} should be a 5-clique (all primes + 1)."""
        count, adj = count_5cliques_up_to(7)
        assert count >= 1
        # Verify {1,2,3,5,7} specifically
        for a in [1, 2, 3, 5, 7]:
            for b in [1, 2, 3, 5, 7]:
                if a != b:
                    assert math.gcd(a, b) == 1

    def test_incremental_consistency(self):
        """Incremental count should match direct enumeration."""
        count_inc, adj = count_5cliques_up_to(20)

        # Direct enumeration
        adj_direct = coprime_adj_sets(20)
        vertices = list(range(1, 21))
        count_direct = 0
        for combo in __import__('itertools').combinations(vertices, 5):
            if all(math.gcd(combo[i], combo[j]) == 1
                   for i in range(5) for j in range(i+1, 5)):
                count_direct += 1

        assert count_inc == count_direct

    def test_new_cliques_contain_vertex(self):
        """All new 5-cliques at vertex v should contain v."""
        adj = coprime_adj_sets(30)
        for v in range(5, 31):
            cliques = enumerate_5cliques_containing(v, adj)
            for c in cliques:
                assert v in c

    def test_new_cliques_are_valid(self):
        """All returned 5-cliques should be pairwise coprime."""
        adj = coprime_adj_sets(25)
        for v in range(5, 26):
            cliques = enumerate_5cliques_containing(v, adj)
            for c in cliques:
                assert len(c) == 5
                for i in range(5):
                    for j in range(i+1, 5):
                        assert math.gcd(c[i], c[j]) == 1, \
                            f"Non-coprime in clique {c}: ({c[i]}, {c[j]})"

    def test_5clique_count_monotone(self):
        """Total 5-clique count is non-decreasing with n."""
        counts = []
        for n in range(5, 25):
            c, _ = count_5cliques_up_to(n)
            counts.append(c)
        for i in range(1, len(counts)):
            assert counts[i] >= counts[i-1]


# ---------------------------------------------------------------------------
# SAT lower bound
# ---------------------------------------------------------------------------

class TestSATLowerBound:
    @pytest.fixture(scope="class")
    def small_sat_result(self):
        return sat_lower_bound(max_n=30, timeout_per_n=10.0, verbose=False)

    def test_returns_dict(self, small_sat_result):
        assert isinstance(small_sat_result, dict)
        assert 'result' in small_sat_result
        assert 'lower_bound' in small_sat_result or 'rcop5' in small_sat_result

    def test_lower_bound_at_least_59(self, small_sat_result):
        """R_cop(5) >= R_cop(4) = 59, but we only scan to 30 here."""
        lb = small_sat_result.get('lower_bound', 0)
        # At n=30, should be SAT (far below any prediction)
        assert lb >= 30 or small_sat_result.get('result') == 'exact'

    def test_scan_data_structure(self, small_sat_result):
        scan = small_sat_result.get('scan_data', [])
        assert len(scan) > 0
        for d in scan:
            assert 'n' in d
            assert 'sat' in d
            assert 'time' in d
            assert 'edges' in d

    def test_all_sat_below_rcop4(self, small_sat_result):
        """All n < 59 should be SAT for k=5."""
        scan = small_sat_result.get('scan_data', [])
        for d in scan:
            if d['n'] < 59 and d['n'] >= 5:
                assert d['sat'] is True, \
                    f"n={d['n']} should be SAT (below R_cop(4)=59)"

    def test_sat_times_positive(self, small_sat_result):
        scan = small_sat_result.get('scan_data', [])
        for d in scan:
            assert d['time'] >= 0

    def test_edge_count_matches(self, small_sat_result):
        """Verify reported edge counts match coprime_edge_count."""
        scan = small_sat_result.get('scan_data', [])
        for d in scan[:10]:  # Check first 10
            n = d['n']
            expected = coprime_edge_count(n)
            assert d['edges'] == expected, \
                f"n={n}: reported {d['edges']} edges, expected {expected}"


# ---------------------------------------------------------------------------
# Clique counting
# ---------------------------------------------------------------------------

class TestCliqueCounting:
    @pytest.fixture(scope="class")
    def small_clique_result(self):
        return clique_counting_analysis(max_n=50, verbose=False)

    def test_returns_dict(self, small_clique_result):
        assert 'data' in small_clique_result
        assert 'growth_exponent' in small_clique_result
        assert 'predictions' in small_clique_result

    def test_growth_exponent_reasonable(self, small_clique_result):
        """Should be around 5 for 5-cliques."""
        exp = small_clique_result['growth_exponent']
        assert exp is not None
        assert 3.0 < exp < 8.0, f"Growth exponent {exp} is unreasonable"

    def test_clique_count_positive(self, small_clique_result):
        data = small_clique_result['data']
        # After n=7 (first 5-clique), counts should be positive
        for d in data:
            if d['n'] >= 7:
                assert d['total_5cliques'] > 0

    def test_predictions_present(self, small_clique_result):
        preds = small_clique_result['predictions']
        assert 'quadratic' in preds
        assert 'exponential' in preds
        assert 'ratio' in preds

    def test_prediction_n_values(self, small_clique_result):
        preds = small_clique_result['predictions']
        assert preds['quadratic']['n'] == 157
        assert preds['exponential']['n'] == 241
        assert preds['ratio']['n'] == 316


# ---------------------------------------------------------------------------
# Monte Carlo
# ---------------------------------------------------------------------------

class TestMonteCarlo:
    @pytest.fixture(scope="class")
    def small_mc_result(self):
        return monte_carlo_avoiding_fraction(
            ns=[10, 15, 20, 25, 30],
            num_samples=200,
            verbose=False,
        )

    def test_returns_dict(self, small_mc_result):
        assert 'data' in small_mc_result

    def test_all_ns_present(self, small_mc_result):
        ns_found = [d['n'] for d in small_mc_result['data']]
        for n in [10, 15, 20, 25, 30]:
            assert n in ns_found

    def test_fraction_in_range(self, small_mc_result):
        for d in small_mc_result['data']:
            assert 0 <= d['fraction'] <= 1.0

    def test_small_n_high_fraction(self, small_mc_result):
        """At small n, most colorings avoid mono K_5."""
        for d in small_mc_result['data']:
            if d['n'] <= 15:
                assert d['fraction'] > 0.5, \
                    f"n={d['n']}: fraction {d['fraction']} unexpectedly low"

    def test_fraction_decreasing(self, small_mc_result):
        """Avoiding fraction should generally decrease with n."""
        data = sorted(small_mc_result['data'], key=lambda d: d['n'])
        fracs = [d['fraction'] for d in data]
        # Allow some noise but overall trend should be down
        assert fracs[0] >= fracs[-1]


# ---------------------------------------------------------------------------
# Phase transition
# ---------------------------------------------------------------------------

class TestSATTimingExtrapolation:
    def test_with_realistic_data(self):
        """Test timing extrapolation with data matching actual SAT run."""
        scan = [
            {'n': 50, 'sat': True, 'time': 0.184},
            {'n': 60, 'sat': True, 'time': 0.451},
            {'n': 70, 'sat': True, 'time': 1.219},
            {'n': 80, 'sat': True, 'time': 2.148},
            {'n': 90, 'sat': True, 'time': 20.538},
            {'n': 100, 'sat': True, 'time': 20.184},
            {'n': 103, 'sat': True, 'time': 173.751},
        ]
        result = sat_timing_extrapolation(scan, verbose=False)
        assert 'growth_rate' in result
        assert result['growth_rate'] > 0
        assert 'doubling_interval' in result
        assert result['doubling_interval'] > 0

    def test_extrapolations_present(self):
        scan = [
            {'n': 50, 'sat': True, 'time': 0.2},
            {'n': 60, 'sat': True, 'time': 0.5},
            {'n': 70, 'sat': True, 'time': 1.2},
            {'n': 80, 'sat': True, 'time': 3.0},
            {'n': 90, 'sat': True, 'time': 15.0},
            {'n': 100, 'sat': True, 'time': 40.0},
        ]
        result = sat_timing_extrapolation(scan, verbose=False)
        assert '1 hour' in result['extrapolations']
        assert '1 day' in result['extrapolations']

    def test_prediction_times_present(self):
        scan = [
            {'n': 50, 'sat': True, 'time': 0.2},
            {'n': 60, 'sat': True, 'time': 0.5},
            {'n': 70, 'sat': True, 'time': 1.2},
            {'n': 80, 'sat': True, 'time': 3.0},
            {'n': 90, 'sat': True, 'time': 15.0},
            {'n': 100, 'sat': True, 'time': 40.0},
        ]
        result = sat_timing_extrapolation(scan, verbose=False)
        assert 'quadratic' in result['prediction_times']
        assert 'exponential' in result['prediction_times']
        # Exponential prediction should take much longer than quadratic
        assert result['prediction_times']['exponential'] > result['prediction_times']['quadratic']

    def test_empty_data(self):
        result = sat_timing_extrapolation([], verbose=False)
        assert result == {}


class TestMonteCarloTwoTier:
    def test_exact_at_small_n(self):
        """Exact MC should work at small n."""
        result = monte_carlo_avoiding_fraction(
            ns=[10, 15], num_samples=100, clique_enum_limit=80, verbose=False)
        assert len(result['data']) == 2
        for d in result['data']:
            assert d['method'] == 'exact'

    def test_sampled_at_large_n(self):
        """Sampled MC should kick in above clique_enum_limit."""
        result = monte_carlo_avoiding_fraction(
            ns=[90], num_samples=50, clique_enum_limit=80, verbose=False)
        assert len(result['data']) == 1
        assert result['data'][0]['method'] == 'sampled'


class TestPhaseTransition:
    def test_empty_inputs(self):
        result = phase_transition_analysis(verbose=False)
        assert isinstance(result, dict)
        assert 'predictions' in result

    def test_with_sat_data(self):
        fake_sat = [
            {'n': 10, 'sat': True, 'time': 0.001, 'edges': 31},
            {'n': 20, 'sat': True, 'time': 0.01, 'edges': 127},
            {'n': 30, 'sat': True, 'time': 0.1, 'edges': 277},
            {'n': 40, 'sat': True, 'time': 0.5, 'edges': 489},
            {'n': 50, 'sat': True, 'time': 2.0, 'edges': 773},
        ]
        result = phase_transition_analysis(sat_data=fake_sat, verbose=False)
        assert result['sat_lower_bound'] == 50
        assert 'sat_slow_start' in result

    def test_predictions_present(self):
        result = phase_transition_analysis(verbose=False)
        preds = result['predictions']
        assert preds['quadratic (p_37)'] == 157
        assert preds['exponential (p_53)'] == 241


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

class TestReport:
    def test_report_generation(self):
        sat = {'result': 'lower_bound', 'lower_bound': 80,
               'total_time': 100, 'scan_data': []}
        clique = {'growth_exponent': 5.2, 'predictions': {
            'quadratic': {'n': 157, 'est_5cliques': 5000000, 'est_edges': 7444,
                          'est_clique_edge_ratio': 672},
        }, 'data': []}
        mc = {'data': []}
        phase = {'evidence_points': [], 'predictions': {
            'quadratic (p_37)': 157, 'exponential (p_53)': 241,
            'ratio extrapolation': 316,
        }}

        report = generate_report(sat, clique, mc, phase, verbose=False)
        assert isinstance(report, str)
        assert 'R_cop(5)' in report
        assert '157' in report
        assert '241' in report

    def test_report_exact_result(self):
        sat = {'result': 'exact', 'rcop5': 157, 'lower_bound': 156,
               'total_time': 1000, 'scan_data': []}
        clique = {'growth_exponent': 5.2, 'predictions': {}, 'data': []}
        mc = {'data': []}
        phase = {'evidence_points': [], 'predictions': {
            'quadratic (p_37)': 157, 'exponential (p_53)': 241,
        }}

        report = generate_report(sat, clique, mc, phase, verbose=False)
        assert 'EXACT' in report
        assert 'quadratic' in report.lower()


# ---------------------------------------------------------------------------
# Integration: verify known R_cop values
# ---------------------------------------------------------------------------

class TestKnownValues:
    def test_rcop2_is_2(self):
        """Verify R_cop(2) = 2: at n=2, edge (1,2) is coprime. Both colorings
        have a monochromatic K_2."""
        # At n=2, the single edge (1,2) has gcd(1,2)=1.
        # Any coloring of this edge gives a monochromatic K_2.
        assert KNOWN_RCOP[2] == 2

    def test_rcop3_is_11(self):
        """R_cop(3) = 11 is established by SAT."""
        assert KNOWN_RCOP[3] == 11

    def test_rcop4_is_59(self):
        """R_cop(4) = 59 is established by SAT + extension."""
        assert KNOWN_RCOP[4] == 59

    def test_all_rcop_are_prime(self):
        """All known R_cop values are prime."""
        from sympy import isprime
        for k, v in KNOWN_RCOP.items():
            assert isprime(v), f"R_cop({k}) = {v} is not prime"

    def test_rcop_increasing(self):
        """R_cop(k) is strictly increasing."""
        vals = [KNOWN_RCOP[k] for k in sorted(KNOWN_RCOP.keys())]
        for i in range(1, len(vals)):
            assert vals[i] > vals[i-1]

    def test_rcop5_lower_bound(self):
        """R_cop(5) > 40 (well below R_cop(4)=59, but within test timeout)."""
        result = sat_lower_bound(max_n=45, timeout_per_n=10.0, verbose=False)
        lb = result.get('lower_bound', 0)
        assert lb >= 40, f"R_cop(5) lower bound {lb} should be >= 40"
