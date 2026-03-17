#!/usr/bin/env python3
"""Tests for IP-Ramsey experiments (Erdős Problem #948)."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from ip_ramsey import (
    fs_set, fs_set_incremental,
    galvin_coloring, padic_coloring, irrational_rotation_coloring, random_coloring,
    experiment_galvin_fs, greedy_minimize_fs_coverage,
    compare_colorings, growth_phase_transition,
    deep_phase_transition, multi_scheme_phase_transition, phase_transition_summary,
    higher_k_phase_transition, fine_grid_phase_transition,
)


# ── FS-Set Tests ──────────────────────────────────────────────────────

class TestFSSet:
    """Test FS-set (finite subset sum) computation."""

    def test_singleton(self):
        """FS-set of {a} = {a}."""
        assert fs_set([5]) == {5}

    def test_pair(self):
        """FS-set of {a,b} = {a, b, a+b}."""
        assert fs_set([2, 3]) == {2, 3, 5}

    def test_triple(self):
        """FS-set of {1,2,4} = {1,2,4,3,5,6,7}."""
        result = fs_set([1, 2, 4])
        expected = {1, 2, 4, 1+2, 1+4, 2+4, 1+2+4}
        assert result == expected

    def test_max_size_limits_subsets(self):
        """max_size=1 gives only singletons."""
        result = fs_set([1, 2, 3], max_size=1)
        assert result == {1, 2, 3}

    def test_max_size_2(self):
        """max_size=2 gives singletons and pairs."""
        result = fs_set([1, 2, 4], max_size=2)
        assert result == {1, 2, 4, 3, 5, 6}  # no triple sum 7

    def test_empty(self):
        """FS-set of empty sequence is empty."""
        assert fs_set([]) == set()

    def test_fs_size_bound(self):
        """FS-set of n elements has at most 2^n - 1 elements."""
        seq = [1, 3, 9, 27]  # powers of 3 (all sums are distinct)
        result = fs_set(seq)
        assert len(result) == 2**len(seq) - 1

    def test_powers_of_3_all_distinct(self):
        """Powers of 3 yield a Sidon-like FS-set (all sums distinct)."""
        seq = [1, 3, 9, 27, 81]
        result = fs_set(seq)
        assert len(result) == 2**5 - 1  # 31 distinct sums


class TestFSSetIncremental:
    """Test the incremental FS-set computation."""

    def test_matches_combinatorial(self):
        """Incremental and combinatorial methods agree."""
        seq = [2, 5, 11, 23]
        assert fs_set_incremental(seq) == fs_set(seq)

    def test_singleton(self):
        assert fs_set_incremental([7]) == {7}

    def test_pair(self):
        assert fs_set_incremental([3, 5]) == {3, 5, 8}

    def test_empty(self):
        assert fs_set_incremental([]) == set()

    def test_large_sequence(self):
        """Incremental handles large sequences efficiently."""
        seq = list(range(1, 20))
        result = fs_set_incremental(seq)
        assert len(result) > 0
        # Contains all singletons
        for a in seq:
            assert a in result
        # Contains sum of all
        assert sum(seq) in result

    def test_powers_of_2(self):
        """FS-set of {1,2,4,...,2^k} = {1,...,2^(k+1)-1}."""
        seq = [2**i for i in range(5)]  # [1,2,4,8,16]
        result = fs_set_incremental(seq)
        assert result == set(range(1, 32))  # {1,...,31}


# ── Colouring Tests ───────────────────────────────────────────────────

class TestGalvinColoring:
    """Test Galvin (2-adic valuation) colouring."""

    def test_powers_of_2(self):
        """v₂(2^k) = k, so colour = k mod k_colours."""
        assert galvin_coloring(1, 3) == 0   # v₂(1) = 0
        assert galvin_coloring(2, 3) == 1   # v₂(2) = 1
        assert galvin_coloring(4, 3) == 2   # v₂(4) = 2
        assert galvin_coloring(8, 3) == 0   # v₂(8) = 3 mod 3 = 0

    def test_odd_numbers(self):
        """All odd numbers have v₂ = 0."""
        for n in [1, 3, 5, 7, 9, 11, 13]:
            assert galvin_coloring(n, 5) == 0

    def test_zero(self):
        """Special case: 0 maps to colour 0."""
        assert galvin_coloring(0, 3) == 0

    def test_k2(self):
        """2-colouring: odd → 0, 2·odd → 1, 4·odd → 0, etc."""
        assert galvin_coloring(6, 2) == 1   # 6 = 2·3
        assert galvin_coloring(12, 2) == 0  # 12 = 4·3

    def test_range_covers_all_colours(self):
        """In 1..100, all k colours appear for small k."""
        for k in [2, 3, 4]:
            colours = {galvin_coloring(n, k) for n in range(1, 101)}
            assert colours == set(range(k))


class TestPadicColoring:
    """Test p-adic valuation colouring."""

    def test_3adic(self):
        """v₃(9) = 2, v₃(27) = 3."""
        assert padic_coloring(9, 3, 5) == 2
        assert padic_coloring(27, 3, 5) == 3

    def test_matches_galvin_for_p2(self):
        """p-adic with p=2 should match Galvin."""
        for n in range(1, 50):
            assert padic_coloring(n, 2, 3) == galvin_coloring(n, 3)

    def test_coprime_to_p(self):
        """Numbers coprime to p have v_p = 0."""
        for n in [1, 2, 4, 5, 7, 8]:
            assert padic_coloring(n, 3, 5) == 0


class TestIrrationalRotationColoring:
    """Test Katznelson-style irrational rotation colouring."""

    def test_range(self):
        """All colours are in {0,...,k-1}."""
        for n in range(1, 100):
            c = irrational_rotation_coloring(n, 5)
            assert 0 <= c < 5

    def test_equidistribution(self):
        """For large range, colours should be roughly equidistributed."""
        N = 10000
        k = 3
        counts = [0] * k
        for n in range(1, N + 1):
            counts[irrational_rotation_coloring(n, k)] += 1
        # Each colour should get roughly N/k ± 10%
        for c in counts:
            assert abs(c - N / k) < 0.1 * N / k

    def test_custom_theta(self):
        """Custom θ works."""
        c = irrational_rotation_coloring(7, 3, theta=math.sqrt(2))
        assert 0 <= c < 3


class TestRandomColoring:
    """Test pseudorandom colouring."""

    def test_deterministic(self):
        """Same seed gives same results."""
        for n in range(1, 20):
            assert random_coloring(n, 5, seed=42) == random_coloring(n, 5, seed=42)

    def test_different_seeds(self):
        """Different seeds give different results (with high probability)."""
        results_42 = [random_coloring(n, 10, seed=42) for n in range(1, 50)]
        results_99 = [random_coloring(n, 10, seed=99) for n in range(1, 50)]
        assert results_42 != results_99

    def test_range(self):
        """All colours in valid range."""
        for n in range(1, 100):
            c = random_coloring(n, 7, seed=42)
            assert 0 <= c < 7


# ── Experiment Tests ──────────────────────────────────────────────────

class TestExperimentGalvinFS:
    """Test Experiment 1: Galvin FS-set coverage."""

    def test_returns_required_keys(self):
        r = experiment_galvin_fs(N=50, k=2, growth="polynomial")
        for key in ["N", "k", "growth", "seq_len", "fs_size",
                     "colour_counts", "colours_hit", "colours_missed"]:
            assert key in r

    def test_polynomial_growth(self):
        r = experiment_galvin_fs(N=100, k=2, growth="polynomial")
        assert r["seq_len"] >= 1
        assert r["fs_size"] > 0
        assert r["colours_hit"] <= r["k"]

    def test_linear_growth(self):
        r = experiment_galvin_fs(N=100, k=3, growth="linear")
        assert r["growth"] == "linear"
        assert r["seq_len"] <= 20  # capped at 20

    def test_lacunary_growth(self):
        r = experiment_galvin_fs(N=100, k=3, growth="lacunary")
        assert r["growth"] == "lacunary"

    def test_log_growth(self):
        r = experiment_galvin_fs(N=100, k=2, growth="log")
        assert r["growth"] == "log"
        assert r["seq_len"] >= 1

    def test_default_growth(self):
        r = experiment_galvin_fs(N=50, k=2, growth="unknown")
        assert r["seq_len"] <= 15

    def test_all_colours_hit_under_galvin(self):
        """Galvin colouring typically hits all colours for k=2."""
        r = experiment_galvin_fs(N=200, k=2, growth="polynomial")
        assert r["colours_hit"] == 2  # both colours hit


class TestGreedyMinimize:
    """Test Experiment 2: Greedy minimization."""

    def test_returns_required_keys(self):
        r = greedy_minimize_fs_coverage(N=20, k=2, seq_len=5)
        for key in ["N", "k", "best_coverage", "best_seq", "all_colours_hit"]:
            assert key in r

    def test_small_k2(self):
        r = greedy_minimize_fs_coverage(N=30, k=2, seq_len=6)
        assert r["best_coverage"] <= 2
        assert r["best_coverage"] >= 0

    def test_colouring_sample_present(self):
        r = greedy_minimize_fs_coverage(N=20, k=2)
        assert "colouring_sample" in r
        assert len(r["colouring_sample"]) == 20


class TestCompareColorings:
    """Test Experiment 3: Colouring scheme comparison."""

    def test_returns_list(self):
        results = compare_colorings(N=50, k=2)
        assert isinstance(results, list)
        assert len(results) == 4  # 4 schemes

    def test_scheme_names(self):
        results = compare_colorings(N=50, k=2)
        names = {r["scheme"] for r in results}
        assert "galvin" in names
        assert "random_42" in names

    def test_fractions_valid(self):
        results = compare_colorings(N=50, k=2)
        for r in results:
            assert 0.0 <= r["frac_all_hit"] <= 1.0
            assert r["all_colours_hit"] + r["missed_at_least_one"] == r["total_seqs"]


class TestGrowthPhaseTransition:
    """Test Experiment 4: Growth rate phase transition."""

    def test_returns_list(self):
        results = growth_phase_transition(N=100, k=2)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_alpha_range(self):
        results = growth_phase_transition(N=100, k=2)
        alphas = [r["alpha"] for r in results]
        assert min(alphas) == pytest.approx(1.0)
        assert max(alphas) == pytest.approx(3.0)

    def test_fractions_valid(self):
        results = growth_phase_transition(N=100, k=2)
        for r in results:
            assert 0.0 <= r["frac_all_hit"] <= 1.0

    def test_low_alpha_high_coverage(self):
        """Linear growth (α=1) should hit all colours with high probability."""
        results = growth_phase_transition(N=200, k=2)
        linear = next(r for r in results if r["alpha"] == pytest.approx(1.0))
        assert linear["frac_all_hit"] >= 0.8


class TestDeepPhaseTransition:
    """Test Experiment 5: Deep phase transition around α=2."""

    def test_returns_list(self):
        results = deep_phase_transition(N=200, k=2, alpha_steps=5, trials=10)
        assert isinstance(results, list)
        assert len(results) == 5

    def test_alpha_range(self):
        results = deep_phase_transition(
            N=200, k=2, alpha_min=1.8, alpha_max=2.2, alpha_steps=5, trials=10,
        )
        alphas = [r["alpha"] for r in results]
        assert min(alphas) == pytest.approx(1.8)
        assert max(alphas) == pytest.approx(2.2)

    def test_required_keys(self):
        results = deep_phase_transition(N=200, k=2, alpha_steps=3, trials=10)
        for r in results:
            for key in ["alpha", "total", "all_hit", "frac_all_hit",
                        "avg_seq_len", "avg_fs_size", "miss_examples", "coloring"]:
                assert key in r

    def test_coloring_schemes(self):
        """Each scheme name is recorded in results."""
        for scheme in ["galvin", "3-adic", "rotation", "random"]:
            results = deep_phase_transition(
                N=100, k=2, alpha_steps=3, trials=5, coloring=scheme,
            )
            assert all(r["coloring"] == scheme for r in results)

    def test_unknown_coloring_defaults_to_galvin(self):
        results = deep_phase_transition(
            N=100, k=2, alpha_steps=3, trials=5, coloring="nonexistent",
        )
        galvin_results = deep_phase_transition(
            N=100, k=2, alpha_steps=3, trials=5, coloring="galvin",
        )
        # Same fractions since same colouring
        for r, g in zip(results, galvin_results):
            assert r["frac_all_hit"] == g["frac_all_hit"]

    def test_low_alpha_full_coverage(self):
        """At α=1.5 with sufficient N, coverage should be 100%."""
        results = deep_phase_transition(
            N=500, k=2, alpha_min=1.5, alpha_max=1.5, alpha_steps=1, trials=30,
        )
        assert results[0]["frac_all_hit"] == 1.0

    def test_miss_examples_structure(self):
        """Miss examples should have required fields when coverage < 100%."""
        # Use high alpha and k=3 to increase chance of misses
        results = deep_phase_transition(
            N=200, k=3, alpha_min=2.5, alpha_max=2.5, alpha_steps=1, trials=50,
        )
        r = results[0]
        for ex in r["miss_examples"]:
            assert "seq_prefix" in ex
            assert "seq_len" in ex
            assert "fs_size" in ex
            assert "colours_hit" in ex
            assert "missed_colours" in ex
            assert len(ex["missed_colours"]) >= 1

    def test_k3_harder_than_k2(self):
        """k=3 should have lower coverage than k=2 at high alpha."""
        r2 = deep_phase_transition(
            N=500, k=2, alpha_min=2.3, alpha_max=2.3, alpha_steps=1, trials=50,
        )
        r3 = deep_phase_transition(
            N=500, k=3, alpha_min=2.3, alpha_max=2.3, alpha_steps=1, trials=50,
        )
        assert r3[0]["frac_all_hit"] <= r2[0]["frac_all_hit"]


class TestMultiSchemePhaseTransition:
    """Test multi-scheme comparison."""

    def test_returns_all_schemes(self):
        results = multi_scheme_phase_transition(N=100, k=2)
        assert set(results.keys()) == {"galvin", "3-adic", "rotation", "random"}

    def test_each_scheme_has_results(self):
        results = multi_scheme_phase_transition(N=100, k=2)
        for scheme, data in results.items():
            assert isinstance(data, list)
            assert len(data) > 0


class TestPhaseTransitionSummary:
    """Test summary statistics computation."""

    def test_with_full_coverage(self):
        results = [{"alpha": 1.5, "frac_all_hit": 1.0},
                   {"alpha": 2.0, "frac_all_hit": 1.0}]
        summary = phase_transition_summary(results)
        assert summary["alpha_95"] is None
        assert summary["alpha_50"] is None
        assert summary["min_frac"] == 1.0

    def test_with_transition(self):
        results = [
            {"alpha": 1.5, "frac_all_hit": 1.0},
            {"alpha": 2.0, "frac_all_hit": 0.9},
            {"alpha": 2.5, "frac_all_hit": 0.4},
        ]
        summary = phase_transition_summary(results)
        assert summary["alpha_95"] == 2.0
        assert summary["alpha_50"] == 2.5
        assert summary["min_frac"] == pytest.approx(0.4)
        assert summary["min_alpha"] == 2.5

    def test_returns_alpha_and_frac_arrays(self):
        results = [{"alpha": 1.0, "frac_all_hit": 1.0},
                   {"alpha": 2.0, "frac_all_hit": 0.8}]
        summary = phase_transition_summary(results)
        assert summary["alphas"] == [1.0, 2.0]
        assert summary["fracs"] == [1.0, 0.8]


# ── Mathematical Properties ──────────────────────────────────────────

class TestFSSetProperties:
    """Test mathematical properties of FS-sets."""

    def test_hindman_structure(self):
        """FS-set is closed under adding the generating element to existing sums."""
        seq = [3, 7, 15]
        result = fs_set_incremental(seq)
        # For each a in seq, {a} ⊂ result
        for a in seq:
            assert a in result
        # For each a in seq, a + (sum of rest) should be in result
        assert 3 + 7 in result
        assert 3 + 15 in result
        assert 7 + 15 in result
        assert 3 + 7 + 15 in result

    def test_galvin_obstruction(self):
        """Galvin colouring prevents monochromatic FS-sets for powers of 2.

        FS({2^0, 2^1, ..., 2^k}) hits all valuations 0..k, hence all k+1
        colours in a (k+1)-colouring.
        """
        seq = [2**i for i in range(5)]  # [1, 2, 4, 8, 16]
        sums = fs_set_incremental(seq)
        k = 5
        colours = {galvin_coloring(s, k) for s in sums}
        assert colours == set(range(k))

    def test_ip_set_growth(self):
        """FS-set of n elements grows at least linearly."""
        for n in range(2, 10):
            seq = list(range(1, n + 1))
            result = fs_set_incremental(seq)
            # At minimum, n singletons + (n choose 2) pairs (if distinct)
            assert len(result) >= n

    def test_lacunary_fs_size(self):
        """Lacunary sequences (ratio > 2) yield FS-sets of size exactly 2^n - 1."""
        seq = [1, 3, 10, 40, 200]  # each > 2× sum of previous
        result = fs_set_incremental(seq)
        assert len(result) == 2**len(seq) - 1


class TestColoringConsistency:
    """Test consistency between colouring schemes."""

    def test_galvin_is_2adic(self):
        """Galvin with k colours is equivalent to p-adic with p=2."""
        for n in range(1, 200):
            for k in [2, 3, 5]:
                assert galvin_coloring(n, k) == padic_coloring(n, 2, k)

    def test_rotation_covers_all(self):
        """Irrational rotation covers all colours for large enough range."""
        k = 5
        colours = {irrational_rotation_coloring(n, k) for n in range(1, 1000)}
        assert colours == set(range(k))

    def test_random_covers_all(self):
        """Random colouring covers all colours for large enough range."""
        k = 7
        colours = {random_coloring(n, k, seed=42) for n in range(1, 200)}
        assert colours == set(range(k))


# ── Experiment 6 Tests: Higher colour counts ─────────────────────────

class TestHigherKPhaseTransition:
    """Test Experiment 6: k=4,5 phase transition under Galvin."""

    def test_returns_dict_with_requested_k(self):
        """Result dict has entries for each requested k value."""
        results = higher_k_phase_transition(
            N=100, k_values=[4, 5], alpha_steps=3, trials=5,
        )
        assert isinstance(results, dict)
        assert set(results.keys()) == {4, 5}

    def test_per_alpha_result_keys(self):
        """Each per-α entry has the expected schema."""
        results = higher_k_phase_transition(
            N=100, k_values=[4], alpha_steps=3, trials=5,
        )
        for r in results[4]:
            for key in ["alpha", "k", "total", "all_hit", "frac_all_hit",
                        "avg_seq_len", "avg_fs_size", "miss_examples", "coloring"]:
                assert key in r
            assert r["k"] == 4
            assert r["coloring"] == "galvin"

    def test_coverage_values_in_unit_interval(self):
        """frac_all_hit must be in [0, 1]."""
        results = higher_k_phase_transition(
            N=100, k_values=[4, 5], alpha_steps=5, trials=10,
        )
        for k_val, data in results.items():
            for r in data:
                assert 0.0 <= r["frac_all_hit"] <= 1.0

    def test_alpha_range_correct(self):
        """Alpha values span the requested range."""
        results = higher_k_phase_transition(
            N=100, k_values=[4], alpha_min=1.0, alpha_max=3.0,
            alpha_steps=5, trials=5,
        )
        alphas = [r["alpha"] for r in results[4]]
        assert alphas[0] == pytest.approx(1.0)
        assert alphas[-1] == pytest.approx(3.0)
        assert len(alphas) == 5

    def test_alpha_95_in_reasonable_range(self):
        """alpha_95 (if it exists) should be between 1.0 and 4.0."""
        results = higher_k_phase_transition(
            N=200, k_values=[4], alpha_min=1.0, alpha_max=3.0,
            alpha_steps=11, trials=20,
        )
        summary = phase_transition_summary(results[4])
        if summary["alpha_95"] is not None:
            assert 1.0 <= summary["alpha_95"] <= 4.0

    def test_single_k(self):
        """Works with a single k value."""
        results = higher_k_phase_transition(
            N=100, k_values=[3], alpha_steps=3, trials=5,
        )
        assert 3 in results
        assert len(results) == 1

    def test_default_k_values(self):
        """Default k_values are [4, 5]."""
        results = higher_k_phase_transition(
            N=100, alpha_steps=3, trials=5,
        )
        assert set(results.keys()) == {4, 5}

    def test_higher_k_harder(self):
        """More colours should make full coverage harder at high alpha."""
        results = higher_k_phase_transition(
            N=200, k_values=[3, 5], alpha_min=2.5, alpha_max=2.5,
            alpha_steps=1, trials=30,
        )
        frac_3 = results[3][0]["frac_all_hit"]
        frac_5 = results[5][0]["frac_all_hit"]
        # k=5 at least as hard (or harder) than k=3
        assert frac_5 <= frac_3 + 0.1  # small tolerance for stochasticity


# ── Experiment 7 Tests: Fine alpha grid ──────────────────────────────

class TestFineGridPhaseTransition:
    """Test Experiment 7: fine-grained α sweep for k=2."""

    def test_returns_dict_with_requested_schemes(self):
        """Result dict has entries for each colouring scheme."""
        results = fine_grid_phase_transition(
            N=100, alpha_steps=5, trials=5,
            schemes=["galvin", "3-adic", "random"],
        )
        assert isinstance(results, dict)
        assert set(results.keys()) == {"galvin", "3-adic", "random"}

    def test_correct_number_of_alpha_steps(self):
        """Each scheme has exactly alpha_steps entries."""
        results = fine_grid_phase_transition(
            N=100, alpha_steps=11, trials=5, schemes=["galvin"],
        )
        assert len(results["galvin"]) == 11

    def test_coverage_values_in_unit_interval(self):
        """frac_all_hit must be in [0, 1]."""
        results = fine_grid_phase_transition(
            N=100, alpha_steps=5, trials=10, schemes=["galvin", "random"],
        )
        for scheme, data in results.items():
            for r in data:
                assert 0.0 <= r["frac_all_hit"] <= 1.0

    def test_fine_spacing(self):
        """51 steps over [1.5, 2.5] gives ~0.02 spacing."""
        results = fine_grid_phase_transition(
            N=100, alpha_min=1.5, alpha_max=2.5,
            alpha_steps=51, trials=5, schemes=["galvin"],
        )
        alphas = [r["alpha"] for r in results["galvin"]]
        assert len(alphas) == 51
        assert alphas[0] == pytest.approx(1.5)
        assert alphas[-1] == pytest.approx(2.5)
        # Check spacing is uniform ~0.02
        spacings = [alphas[i+1] - alphas[i] for i in range(len(alphas) - 1)]
        for s in spacings:
            assert s == pytest.approx(0.02, abs=0.005)

    def test_alpha_95_in_reasonable_range(self):
        """alpha_95 for each scheme should fall in [1.0, 4.0] when present."""
        results = fine_grid_phase_transition(
            N=200, alpha_steps=11, trials=20,
            schemes=["galvin", "3-adic", "random"],
        )
        for scheme, data in results.items():
            summary = phase_transition_summary(data)
            if summary["alpha_95"] is not None:
                assert 1.0 <= summary["alpha_95"] <= 4.0

    def test_default_schemes(self):
        """Default schemes are galvin, 3-adic, random."""
        results = fine_grid_phase_transition(
            N=100, alpha_steps=3, trials=5,
        )
        assert set(results.keys()) == {"galvin", "3-adic", "random"}

    def test_per_alpha_keys(self):
        """Each entry has the deep_phase_transition schema."""
        results = fine_grid_phase_transition(
            N=100, alpha_steps=3, trials=5, schemes=["galvin"],
        )
        for r in results["galvin"]:
            for key in ["alpha", "total", "all_hit", "frac_all_hit",
                        "avg_seq_len", "avg_fs_size", "miss_examples", "coloring"]:
                assert key in r

    def test_single_scheme(self):
        """Works with a single scheme."""
        results = fine_grid_phase_transition(
            N=100, alpha_steps=3, trials=5, schemes=["3-adic"],
        )
        assert list(results.keys()) == ["3-adic"]
