"""Tests for universal_patterns.py — cross-domain connections in coprime graph theory."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from universal_patterns import (
    sieve_primes,
    mobius,
    euler_totient,
    coprime_edges,
    coprime_edge_density,
    prime_index,
    nth_prime,
    zeta_partial,
    zeta_approx,
    kfree_density,
    kwise_coprime_density,
    lattice_visibility_density,
    zeta_connection_web,
    is_prime,
    prime_counting,
    rcop_prime_analysis,
    RCOP_KNOWN,
    RCOP_MULTICOLOR,
    stanley_sequence,
    sidon_set_greedy,
    growth_exponent_analysis,
    PHI,
    LOG2_LOG3,
    hamming_bound,
    gilbert_varshamov_bound,
    avoiding_coloring_count,
    coding_theory_connection,
    coprime_adjacency_matrix,
    partition_function_ising,
    free_energy_density,
    antiferromagnetic_clique_constraint,
    phase_transition_temperature,
    stat_mech_analysis,
    find_genuine_connections,
    run_all_experiments,
)


# ===========================================================================
# Utilities
# ===========================================================================

class TestSievePrimes:
    def test_small(self):
        assert sieve_primes(10) == [2, 3, 5, 7]

    def test_empty(self):
        assert sieve_primes(1) == []

    def test_prime_count_100(self):
        assert len(sieve_primes(100)) == 25

    def test_includes_boundary(self):
        assert 7 in sieve_primes(7)
        assert 7 not in sieve_primes(6)


class TestMobius:
    def test_mu_1(self):
        assert mobius(1) == 1

    def test_mu_primes(self):
        for p in [2, 3, 5, 7, 11]:
            assert mobius(p) == -1

    def test_mu_square_factor(self):
        assert mobius(4) == 0
        assert mobius(8) == 0
        assert mobius(12) == 0

    def test_mu_two_primes(self):
        assert mobius(6) == 1   # 2 * 3
        assert mobius(10) == 1  # 2 * 5
        assert mobius(15) == 1  # 3 * 5

    def test_mu_three_primes(self):
        assert mobius(30) == -1  # 2 * 3 * 5


class TestEulerTotient:
    def test_phi_1(self):
        assert euler_totient(1) == 1

    def test_phi_prime(self):
        assert euler_totient(7) == 6
        assert euler_totient(11) == 10

    def test_phi_prime_power(self):
        assert euler_totient(8) == 4    # 2^3: 8*(1-1/2) = 4
        assert euler_totient(9) == 6    # 3^2: 9*(1-1/3) = 6

    def test_phi_composite(self):
        assert euler_totient(12) == 4   # 12*(1-1/2)*(1-1/3) = 4


class TestPrimeIndex:
    def test_first_primes(self):
        assert prime_index(2) == 1
        assert prime_index(3) == 2
        assert prime_index(5) == 3
        assert prime_index(11) == 5

    def test_composite(self):
        assert prime_index(4) is None
        assert prime_index(6) is None

    def test_one(self):
        assert prime_index(1) is None


class TestNthPrime:
    def test_first_primes(self):
        assert nth_prime(1) == 2
        assert nth_prime(5) == 11
        assert nth_prime(17) == 59

    def test_roundtrip(self):
        for k in [1, 5, 10, 25]:
            p = nth_prime(k)
            assert prime_index(p) == k


class TestCoprimeEdges:
    def test_n3(self):
        edges = coprime_edges(3)
        assert len(edges) == 3  # all pairs coprime

    def test_n4(self):
        edges = coprime_edges(4)
        assert (2, 4) not in edges  # gcd = 2


class TestCoprimeDensity:
    def test_approaches_6_over_pi2(self):
        d = coprime_edge_density(200)
        expected = 6.0 / math.pi**2
        assert abs(d - expected) < 0.02


# ===========================================================================
# Experiment 1: zeta(2) connection web
# ===========================================================================

class TestZetaPartialSum:
    def test_zeta2_converges(self):
        """Partial sum of zeta(2) should approach pi^2/6."""
        partial = zeta_partial(2.0, 100000)
        expected = math.pi**2 / 6
        assert abs(partial - expected) < 0.001

    def test_zeta3_converges(self):
        """Partial sum of zeta(3) should approach Apery's constant."""
        partial = zeta_partial(3.0, 100000)
        apery = 1.2020569031595942
        assert abs(partial - apery) < 0.001


class TestZetaApprox:
    def test_zeta2(self):
        z = zeta_approx(2.0)
        assert abs(z - math.pi**2 / 6) < 0.0001

    def test_zeta4(self):
        z = zeta_approx(4.0)
        expected = math.pi**4 / 90
        assert abs(z - expected) < 0.001


class TestKfreeDensity:
    def test_squarefree(self):
        """Squarefree density should approach 6/pi^2."""
        d = kfree_density(2, 5000)
        expected = 6.0 / math.pi**2
        assert abs(d - expected) < 0.01

    def test_cubefree(self):
        """Cubefree density should approach 1/zeta(3)."""
        d = kfree_density(3, 5000)
        expected = 1.0 / zeta_approx(3.0)
        assert abs(d - expected) < 0.01

    def test_4free(self):
        """4-free density should approach 1/zeta(4)."""
        d = kfree_density(4, 5000)
        expected = 1.0 / zeta_approx(4.0)
        assert abs(d - expected) < 0.01

    def test_monotone(self):
        """k-free density should increase with k (fewer excluded)."""
        d2 = kfree_density(2, 1000)
        d3 = kfree_density(3, 1000)
        d4 = kfree_density(4, 1000)
        assert d2 < d3 < d4


class TestKwiseCoprimeGCD:
    def test_pair_gcd_is_zeta2(self):
        """P(gcd(a,b)=1) should approach 1/zeta(2) = 6/pi^2."""
        result = kwise_coprime_density(2, 2000, num_samples=50000)
        expected = 6.0 / math.pi**2
        assert abs(result["gcd_coprime"] - expected) < 0.02

    def test_triple_gcd_is_zeta3(self):
        """P(gcd(a,b,c)=1) should approach 1/zeta(3)."""
        result = kwise_coprime_density(3, 2000, num_samples=50000)
        expected = 1.0 / zeta_approx(3.0)
        assert abs(result["gcd_coprime"] - expected) < 0.02

    def test_pairwise_less_than_gcd(self):
        """Pairwise coprimality is stricter than gcd coprimality."""
        result = kwise_coprime_density(3, 2000, num_samples=30000)
        assert result["pairwise_coprime"] < result["gcd_coprime"]


class TestLatticeVisibility:
    def test_approaches_6_over_pi2(self):
        d = lattice_visibility_density(500)
        expected = 6.0 / math.pi**2
        assert abs(d - expected) < 0.01


class TestZetaConnectionWeb:
    @pytest.fixture(scope="module")
    def zeta_results(self):
        return zeta_connection_web(max_k=4, n=2000)

    def test_has_zeta_values(self, zeta_results):
        assert 2 in zeta_results["zeta_values"]
        assert 3 in zeta_results["zeta_values"]

    def test_kfree_matches(self, zeta_results):
        for k, data in zeta_results["kfree_densities"].items():
            assert data["rel_error"] < 0.02, f"k={k}: rel_error={data['rel_error']}"

    def test_gcd_coprime_matches_zeta(self, zeta_results):
        for k, data in zeta_results["coprime_k_tuple"].items():
            assert data["gcd_matches_zeta"], f"k={k}: gcd_coprime mismatch"


# ===========================================================================
# Experiment 2: prime counting in Ramsey theory
# ===========================================================================

class TestIsPrime:
    def test_small_primes(self):
        assert is_prime(2)
        assert is_prime(11)
        assert is_prime(59)

    def test_composites(self):
        assert not is_prime(1)
        assert not is_prime(4)
        assert not is_prime(57)  # 3 * 19


class TestPrimeCounting:
    def test_pi_10(self):
        assert prime_counting(10) == 4

    def test_pi_100(self):
        assert prime_counting(100) == 25


class TestRcopKnownValues:
    def test_all_prime(self):
        """All known R_cop(k) are prime."""
        for k, v in RCOP_KNOWN.items():
            assert is_prime(v), f"R_cop({k})={v} is not prime"

    def test_multicolor_prime(self):
        """R_cop(3;3) = 53 is prime."""
        assert is_prime(53)


class TestRcopPrimeAnalysis:
    @pytest.fixture(scope="module")
    def analysis(self):
        return rcop_prime_analysis()

    def test_prime_indices(self, analysis):
        """pi(R_cop(2))=1, pi(R_cop(3))=5, pi(R_cop(4))=17."""
        assert analysis["prime_indices"][2] == 1
        assert analysis["prime_indices"][3] == 5
        assert analysis["prime_indices"][4] == 17

    def test_quadratic_formula_fits(self, analysis):
        """4k^2 - 16k + 17 should match all known values."""
        check = analysis["quadratic_fit"]["check_known"]
        for k, matches in check.items():
            assert matches, f"Quadratic formula fails at k={k}"

    def test_quadratic_prediction_k5(self, analysis):
        """Predicts pi(R_cop(5)) = 4*25-80+17 = 37, so R_cop(5) = p_37."""
        preds = analysis["quadratic_fit"]["predictions"]
        assert preds[5]["pi_Rcop"] == 37
        assert preds[5]["predicted_Rcop"] == nth_prime(37)

    def test_log_log_fit(self, analysis):
        """R_cop(k) grows super-linearly."""
        ll = analysis.get("log_log_fit", {})
        # slope > 1 means super-linear
        assert ll.get("slope", 0) > 1


# ===========================================================================
# Experiment 3: golden ratio and Fibonacci
# ===========================================================================

class TestStanleySequence:
    def test_starts_correctly(self):
        seq = stanley_sequence(1)
        assert seq[0] == 0
        assert seq[1] == 1

    def test_no_3ap(self):
        """No three terms of the sequence form an arithmetic progression."""
        seq = stanley_sequence(2)
        seq_set = set(seq)
        for i in range(len(seq)):
            for j in range(i + 1, len(seq)):
                # If (a, b) are in the seq, then 2b-a should not be
                mid = (seq[i] + seq[j])
                if mid % 2 == 0 and mid // 2 in seq_set:
                    # i, mid//2, j form a 3-AP only if they're distinct
                    if seq[i] != mid // 2 != seq[j]:
                        pytest.fail(f"3-AP found: {seq[i]}, {mid//2}, {seq[j]}")


class TestSidonSetGreedy:
    def test_is_sidon(self):
        """Greedy Sidon set should have all pairwise sums distinct."""
        s = sidon_set_greedy(100)
        sums = set()
        for i, a in enumerate(s):
            for b in s[i:]:
                total = a + b
                assert total not in sums, f"Duplicate sum {total}"
                sums.add(total)

    def test_growth(self):
        """Size should grow roughly as sqrt(n)."""
        s100 = sidon_set_greedy(100)
        s1000 = sidon_set_greedy(1000)
        # sqrt(1000)/sqrt(100) = sqrt(10) ~ 3.16
        ratio = len(s1000) / len(s100)
        assert 1.5 < ratio < 5.0


class TestGrowthExponentAnalysis:
    @pytest.fixture(scope="module")
    def growth_results(self):
        return growth_exponent_analysis()

    def test_sidon_exponent_near_half(self, growth_results):
        """Sidon set growth exponent should be near 0.5."""
        for data in growth_results["sidon"]:
            assert abs(data["measured_exponent"] - 0.5) < 0.1

    def test_schur_ratios_increase(self, growth_results):
        """Schur ratios S(k+1)/S(k) should be increasing."""
        ratios = growth_results["schur_fibonacci"]["schur_ratios"]
        assert len(ratios) >= 2
        assert ratios[-1] > ratios[0]


# ===========================================================================
# Experiment 4: coding theory
# ===========================================================================

class TestHammingBound:
    def test_known_value(self):
        """Hamming bound for (7,3,2): 2^7/V(7,1) = 128/8 = 16."""
        assert hamming_bound(7, 3, 2) == 16.0

    def test_larger_d_gives_smaller_bound(self):
        assert hamming_bound(15, 7, 2) < hamming_bound(15, 5, 2)


class TestGilbertVarshamov:
    def test_lower_bound(self):
        """GV bound should be positive."""
        assert gilbert_varshamov_bound(7, 3, 2) > 0

    def test_gv_leq_hamming(self):
        """GV bound <= Hamming bound (for interesting parameters)."""
        gv = gilbert_varshamov_bound(10, 3, 2)
        hb = hamming_bound(10, 3, 2)
        assert gv <= hb


class TestAvoidingColoringCount:
    def test_k3_n3(self):
        """At n=3 with k=3: single triangle {1,2,3}. 2 avoiding out of 8."""
        count = avoiding_coloring_count(3, 3)
        # Edges: (1,2), (1,3), (2,3). Only all-0 and all-1 are monochromatic.
        # Wait -- 2^3 = 8 total. Mono K_3 requires all 3 edges same color.
        # All-0: mono K_3 color 0. All-1: mono K_3 color 1. => 6 avoiding.
        assert count == 6

    def test_k3_n8(self):
        """At n=8 there are exactly 36 avoiding colorings for k=3."""
        count = avoiding_coloring_count(8, 3)
        assert count == 36

    def test_k3_n7_positive(self):
        """At n=7 < R_cop(3)=11, avoiding colorings still exist."""
        count = avoiding_coloring_count(7, 3)
        assert count > 0

    def test_k2_n2(self):
        """At n=2, k=2: single edge, both colorings give mono K_2."""
        count = avoiding_coloring_count(2, 2)
        assert count == 0

    def test_too_large(self):
        """Should return -1 for large edge counts."""
        count = avoiding_coloring_count(20, 3)
        assert count == -1


class TestCodingTheoryConnection:
    @pytest.fixture(scope="module")
    def coding_results(self):
        return coding_theory_connection(max_n=9)

    def test_has_k3_data(self, coding_results):
        assert 3 in coding_results["avoiding_codes"]
        assert len(coding_results["avoiding_codes"][3]) > 0

    def test_rate_decreases(self, coding_results):
        """Rate should generally decrease as n increases."""
        data = coding_results["avoiding_codes"][3]
        if len(data) >= 3:
            first_rate = data[1]["rate"] if data[1]["num_edges"] > 0 else 1
            last_rate = data[-1]["rate"]
            assert last_rate <= first_rate + 0.1  # allow some noise

    def test_fraction_decreases(self, coding_results):
        """Fraction of avoiding colorings decreases toward R_cop."""
        data = coding_results["avoiding_codes"][3]
        fracs = [d["fraction_of_all"] for d in data if d["num_edges"] > 0]
        if len(fracs) >= 3:
            assert fracs[-1] < fracs[0]


# ===========================================================================
# Experiment 5: statistical mechanics
# ===========================================================================

class TestCoprimelAdjacencyMatrix:
    def test_symmetric(self):
        A = coprime_adjacency_matrix(5)
        assert np.allclose(A, A.T)

    def test_zero_diagonal(self):
        A = coprime_adjacency_matrix(5)
        assert np.allclose(np.diag(A), 0)

    def test_correct_entries(self):
        A = coprime_adjacency_matrix(4)
        # gcd(1,2)=1: A[0,1]=1
        assert A[0, 1] == 1
        # gcd(2,4)=2: A[1,3]=0
        assert A[1, 3] == 0

    def test_edge_count(self):
        n = 6
        A = coprime_adjacency_matrix(n)
        assert int(np.sum(A) / 2) == len(coprime_edges(n))


class TestPartitionFunctionIsing:
    def test_beta_zero(self):
        """At beta=0 (infinite temperature), Z = 2^n."""
        A = coprime_adjacency_matrix(4)
        Z = partition_function_ising(A, 0.0)
        assert abs(Z - 2**4) < 0.01

    def test_positive_for_positive_beta(self):
        A = coprime_adjacency_matrix(5)
        Z = partition_function_ising(A, 1.0)
        assert Z > 0


class TestAntiferromagneticConstraint:
    def test_small_n(self):
        result = antiferromagnetic_clique_constraint(5, 3, 2.0)
        assert result["n"] == 5
        assert result["num_edges"] > 0
        assert result["num_avoiding"] >= 0

    def test_avoiding_count_matches(self):
        """Avoiding count from stat mech should match direct count."""
        result = antiferromagnetic_clique_constraint(6, 3, 2.0)
        direct = avoiding_coloring_count(6, 3)
        assert result["num_avoiding"] == direct

    def test_partition_data_length(self):
        result = antiferromagnetic_clique_constraint(5, 3, 2.0)
        assert len(result["partition_data"]) == 20  # 20 beta values

    def test_too_large(self):
        result = antiferromagnetic_clique_constraint(20, 3, 2.0)
        assert result["status"] == "too_large_for_exact"


class TestPhaseTransition:
    @pytest.fixture(scope="module")
    def phase_data(self):
        return phase_transition_temperature(3, max_n=9)

    def test_k_value(self, phase_data):
        assert phase_data["k"] == 3

    def test_fraction_decreases(self, phase_data):
        """Avoiding fraction should decrease as n grows."""
        data = phase_data["data"]
        fracs = [d["fraction_avoiding"] for d in data if d["num_edges"] > 0]
        if len(fracs) >= 3:
            assert fracs[-1] < fracs[0]

    def test_zero_T_entropy_decreases(self, phase_data):
        """Zero-temperature entropy should decrease as n approaches R_cop(3)."""
        data = phase_data["data"]
        ents = [d["zero_T_entropy"] for d in data
                if d["num_edges"] > 0 and d["num_avoiding"] > 0]
        if len(ents) >= 3:
            assert ents[-1] <= ents[0] + 0.05


class TestStatMechAnalysis:
    @pytest.fixture(scope="module")
    def results(self):
        return stat_mech_analysis()

    def test_has_ising_spectrum(self, results):
        assert len(results["ising_spectrum"]) > 0

    def test_top_eigenvalue_positive(self, results):
        for n, data in results["ising_spectrum"].items():
            assert data["top_eigenvalue"] > 0

    def test_spectral_gap_positive(self, results):
        for n, data in results["ising_spectrum"].items():
            assert data["spectral_gap"] > 0


# ===========================================================================
# Synthesis
# ===========================================================================

class TestFindGenuineConnections:
    def test_finds_zeta_universality(self):
        """Should find the 1/zeta(k) universality connection."""
        zeta_results = {
            "coprime_k_tuple": {
                2: {"gcd_coprime": 0.608, "pairwise_coprime": 0.608,
                    "theoretical_gcd": 0.6079, "gcd_matches_zeta": True},
            },
        }
        prime_results = {"all_values_prime": True,
                         "quadratic_fit": {"check_known": {2: True, 3: True, 4: True},
                                           "predictions": {5: {"pi_Rcop": 37,
                                                                "predicted_Rcop": 157}}}}
        growth_results = {}
        coding_results = {"rate_comparison": {}}
        stat_mech_results = {"phase_transitions": {}, "ising_spectrum": {}}

        connections = find_genuine_connections(
            zeta_results, prime_results, growth_results, coding_results, stat_mech_results
        )
        types = [c["type"] for c in connections]
        assert "zeta_universality" in types
        assert "rcop_primality" in types

    def test_rejects_without_evidence(self):
        """Without matching data, should not find spurious connections."""
        empty = {"coprime_k_tuple": {}}
        connections = find_genuine_connections(
            empty,
            {"all_values_prime": False, "quadratic_fit": {"check_known": {}}},
            {}, {"rate_comparison": {}},
            {"phase_transitions": {}, "ising_spectrum": {}},
        )
        # Should not claim zeta universality or primality
        types = [c["type"] for c in connections]
        assert "zeta_universality" not in types
        assert "rcop_primality" not in types


class TestRunAllExperiments:
    @pytest.fixture(scope="module")
    def full_results(self):
        return run_all_experiments()

    def test_has_all_sections(self, full_results):
        assert "zeta_web" in full_results
        assert "prime_analysis" in full_results
        assert "growth_analysis" in full_results
        assert "coding_theory" in full_results
        assert "stat_mech" in full_results
        assert "connections" in full_results

    def test_connections_nonempty(self, full_results):
        """Should find at least 2 genuine connections."""
        assert len(full_results["connections"]) >= 2

    def test_zeta_universality_found(self, full_results):
        types = [c["type"] for c in full_results["connections"]]
        assert "zeta_universality" in types

    def test_primality_found(self, full_results):
        types = [c["type"] for c in full_results["connections"]]
        assert "rcop_primality" in types
