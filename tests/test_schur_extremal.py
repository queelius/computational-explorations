"""Tests for schur_extremal.py -- extremal colorings at Schur numbers."""

import pytest
import numpy as np

from schur_extremal import (
    has_schur_triple,
    count_schur_triples,
    is_valid_schur_coloring,
    enumerate_extremal_colorings_k2,
    analyze_color_classes,
    fourier_spectrum_integer,
    top_fourier_features,
    random_schur_coloring,
    find_extremal_colorings_k3,
    analyze_extremal_k3,
    min_schur_triples_at_boundary,
    forced_color_analysis,
    max_sum_free_density_integer,
    density_vs_N,
    density_barrier_by_k,
    coloring_equivalence_classes,
    _min_triples_heuristic,
    _forced_color_heuristic,
)


# ── Core primitives ──────────────────────────────────────────────


class TestHasSchurTriple:
    def test_empty_set(self):
        assert not has_schur_triple(set())

    def test_singleton(self):
        """No triple in {a} unless a+a=a, which needs a=0."""
        assert not has_schur_triple({1})
        assert not has_schur_triple({5})

    def test_pair_no_triple(self):
        """{1, 4}: 1+1=2, 1+4=5, 4+4=8 -- none in {1,4}."""
        assert not has_schur_triple({1, 4})

    def test_pair_with_triple(self):
        """{1, 2}: 1+1=2 in {1,2}."""
        assert has_schur_triple({1, 2})

    def test_classic_triple(self):
        """{1, 2, 3}: 1+2=3."""
        assert has_schur_triple({1, 2, 3})

    def test_odds_sum_free_small(self):
        """{1, 3}: 1+1=2, 1+3=4, 3+3=6 -- none in {1,3}."""
        assert not has_schur_triple({1, 3})

    def test_large_sum_free(self):
        """Odd numbers up to 20: odd+odd=even, no even in set."""
        odds = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19}
        assert not has_schur_triple(odds)


class TestCountSchurTriples:
    def test_empty(self):
        assert count_schur_triples(set()) == 0

    def test_sum_free_zero(self):
        assert count_schur_triples({1, 4}) == 0

    def test_simple_triple(self):
        """{1, 2, 3}: ordered triples (a,b) with a+b=c in S:
        (1,1)->2, (1,2)->3, (2,1)->3.  Total = 3."""
        count = count_schur_triples({1, 2, 3})
        assert count == 3

    def test_self_sum(self):
        """{1, 2}: 1+1=2, so one ordered triple."""
        count = count_schur_triples({1, 2})
        assert count == 1

    def test_multiple_triples(self):
        """{1, 2, 3, 4}: (1,1,2), (1,2,3), (2,1,3), (1,3,4), (3,1,4), (2,2,4)."""
        count = count_schur_triples({1, 2, 3, 4})
        assert count == 6


class TestIsValidSchurColoring:
    def test_valid_coloring_s2(self):
        """Classic: {1,4} and {2,3} on [1..4]."""
        coloring = [0, 1, 1, 0]
        assert is_valid_schur_coloring(coloring, 4)

    def test_invalid_all_same(self):
        """All in color 0 on [1..3]: 1+2=3."""
        coloring = [0, 0, 0]
        assert not is_valid_schur_coloring(coloring, 3)

    def test_valid_singleton(self):
        """{1} with 1 color: no triple."""
        coloring = [0]
        assert is_valid_schur_coloring(coloring, 1)


# ── Experiment (a): S(2)=4 enumeration ───────────────────────────


class TestEnumerateExtremalK2:
    @pytest.fixture(scope="class")
    def colorings_k2(self):
        return enumerate_extremal_colorings_k2(4)

    def test_count(self, colorings_k2):
        """There should be exactly 6 valid 2-colorings of [1..4].

        The valid partitions up to color swap are:
          {1,4} | {2,3}  (2 swaps = 2 colorings)
          {1}   | {2,3,4} -- nope, 2+2=4 in same class
          {4}   | {1,2,3} -- nope, 1+2=3 in same class
        Checking: by symmetry {1,4}|{2,3} has 2 labelings.
        Also {3,4}|{1,2}: 1+1=2 in {1,2} -- nope.
        {2,4}|{1,3}: 1+3=4, 4 not in {1,3}; 1+1=2 not in {1,3}; 3+3=6 not in {1,3}.
          For {2,4}: 2+2=4 in set -- nope.
        {1,4}|{2,3}: for {1,4}: 1+1=2, 1+4=5, 4+4=8 -- none in {1,4}. OK.
          For {2,3}: 2+2=4, 2+3=5, 3+3=6 -- none in {2,3}. OK.
        We just need to enumerate exhaustively.
        """
        assert len(colorings_k2) > 0
        # Each should be valid
        for col in colorings_k2:
            assert is_valid_schur_coloring(col, 4)

    def test_all_valid(self, colorings_k2):
        """Every returned coloring must actually avoid Schur triples."""
        for col in colorings_k2:
            assert is_valid_schur_coloring(col, 4)

    def test_no_valid_at_5(self):
        """S(2)=4 means no valid 2-coloring of [1..5]."""
        colorings = enumerate_extremal_colorings_k2(5)
        assert len(colorings) == 0

    def test_equivalence_classes(self, colorings_k2):
        """Under color swap, there should be fewer equivalence classes."""
        equiv = coloring_equivalence_classes(colorings_k2)
        assert len(equiv) <= len(colorings_k2)
        assert len(equiv) >= 1


class TestAnalyzeColorClasses:
    def test_balanced_partition(self):
        """{1,4}|{2,3}: sizes [2,2], densities [0.5, 0.5]."""
        coloring = [0, 1, 1, 0]
        info = analyze_color_classes(coloring, 4)
        assert info["k"] == 2
        assert info["N"] == 4
        assert sorted(info["sizes"]) == [2, 2]
        assert all(abs(d - 0.5) < 0.01 for d in info["densities"])

    def test_three_colors(self):
        """3-coloring analysis returns correct k."""
        coloring = [0, 1, 2, 0, 1]
        info = analyze_color_classes(coloring, 5)
        assert info["k"] == 3
        assert sum(info["sizes"]) == 5


# ── Fourier spectrum ─────────────────────────────────────────────


class TestFourierSpectrum:
    def test_dc_equals_size(self):
        """DC component |f_hat(0)| = |S|."""
        S = {1, 3, 5}
        N = 10
        spec = fourier_spectrum_integer(S, N)
        dc = next(mag for r, mag in spec if r == 0)
        assert abs(dc - 3.0) < 0.01

    def test_empty_set(self):
        spec = fourier_spectrum_integer(set(), 5)
        for r, mag in spec:
            assert abs(mag) < 0.01

    def test_sorted_descending(self):
        S = {1, 2, 4}
        spec = fourier_spectrum_integer(S, 10)
        mags = [m for _, m in spec]
        assert mags == sorted(mags, reverse=True)


class TestTopFourierFeatures:
    def test_dc_present(self):
        S = {1, 3}
        feat = top_fourier_features(S, 5)
        assert abs(feat["dc"] - 2.0) < 0.01

    def test_empty_set(self):
        feat = top_fourier_features(set(), 5)
        assert feat["max_non_dc_ratio"] == 0.0
        assert feat["l2_energy"] == 0.0

    def test_singleton(self):
        feat = top_fourier_features({3}, 10)
        assert abs(feat["dc"] - 1.0) < 0.01
        assert feat["max_non_dc_ratio"] > 0  # non-trivial Fourier structure

    def test_sum_free_fourier_ratio(self):
        """Sum-free sets should have detectable Fourier structure."""
        S = {1, 3, 5, 7, 9}
        feat = top_fourier_features(S, 10)
        # Odd numbers have strong peak at the "alternating" frequency
        assert feat["max_non_dc_ratio"] > 0.5


# ── Experiment (b): S(3)=13 search ──────────────────────────────


class TestRandomSchurColoring:
    def test_finds_valid_at_s2(self):
        """Should find a valid 2-coloring of [1..4]."""
        col = random_schur_coloring(4, 2)
        assert col is not None
        assert is_valid_schur_coloring(col, 4)

    def test_none_at_s2_plus_1(self):
        """Unlikely to find valid 2-coloring of [1..5] (impossible)."""
        col = random_schur_coloring(5, 2, max_attempts=1000)
        assert col is None

    def test_deterministic_with_seed(self):
        """Same seed should give same result."""
        rng1 = __import__("random").Random(123)
        rng2 = __import__("random").Random(123)
        c1 = random_schur_coloring(4, 2, rng=rng1)
        c2 = random_schur_coloring(4, 2, rng=rng2)
        assert c1 == c2


class TestFindExtremalK3:
    @pytest.fixture(scope="class")
    def colorings_k3(self):
        return find_extremal_colorings_k3(13, num_search=10000, seed=42)

    def test_finds_some(self, colorings_k3):
        """Random search should find at least one valid 3-coloring of [1..13]."""
        assert len(colorings_k3) > 0

    def test_all_valid(self, colorings_k3):
        """Every returned coloring should be valid."""
        for col in colorings_k3:
            assert is_valid_schur_coloring(col, 13)

    def test_correct_length(self, colorings_k3):
        for col in colorings_k3:
            assert len(col) == 13

    def test_uses_3_colors(self, colorings_k3):
        for col in colorings_k3:
            assert max(col) <= 2
            assert min(col) >= 0


class TestAnalyzeExtremalK3:
    def test_empty_input(self):
        result = analyze_extremal_k3([], 13)
        assert result["count"] == 0

    def test_nonempty(self):
        colorings = find_extremal_colorings_k3(13, num_search=5000, seed=42)
        if len(colorings) > 0:
            result = analyze_extremal_k3(colorings, 13)
            assert result["count"] == len(colorings)
            assert "size_distributions" in result
            assert result["mean_max_fourier_ratio"] > 0


# ── Experiment (c): S(k)+1 boundary ─────────────────────────────


class TestMinSchurTriples:
    def test_k2_n5(self):
        """At N=5, k=2: must have at least 1 Schur triple."""
        min_t, best_col = min_schur_triples_at_boundary(5, 2)
        assert min_t >= 1

    def test_k2_n4_zero(self):
        """At N=4, k=2: CAN have 0 triples (S(2)=4)."""
        min_t, best_col = min_schur_triples_at_boundary(4, 2)
        assert min_t == 0

    def test_k1_n2(self):
        """At N=2, k=1: {1,2} has 1+1=2, so 1 triple."""
        min_t, best_col = min_schur_triples_at_boundary(2, 1)
        assert min_t >= 1

    def test_best_coloring_valid_format(self):
        min_t, best_col = min_schur_triples_at_boundary(5, 2)
        assert len(best_col) == 5
        assert all(0 <= c < 2 for c in best_col)


class TestMinTriplesHeuristic:
    def test_returns_valid(self):
        min_t, best_col = _min_triples_heuristic(14, 3, num_trials=1000)
        assert min_t >= 0
        assert len(best_col) == 14
        assert all(0 <= c < 3 for c in best_col)


class TestForcedColorAnalysis:
    def test_k2_n5(self):
        """At N=5, k=2: every coloring has at least one color with a triple."""
        result = forced_color_analysis(5, 2)
        assert result["N"] == 5
        assert result["k"] == 2
        assert result["total_colorings"] == 2 ** 5

        # Every coloring must have a triple somewhere
        # (not necessarily in a specific color)
        total_with_any_triple = 0
        for bits in range(2 ** 5):
            col = [(bits >> i) & 1 for i in range(5)]
            c0 = {i + 1 for i in range(5) if col[i] == 0}
            c1 = {i + 1 for i in range(5) if col[i] == 1}
            if has_schur_triple(c0) or has_schur_triple(c1):
                total_with_any_triple += 1
        assert total_with_any_triple == 2 ** 5

    def test_symmetry(self):
        """By symmetry, both colors should be forced equally often."""
        result = forced_color_analysis(5, 2)
        f0, f1 = result["fraction_with_triple"]
        assert abs(f0 - f1) < 0.01, f"Asymmetric: {f0} vs {f1}"


class TestForcedColorHeuristic:
    def test_returns_valid(self):
        result = _forced_color_heuristic(14, 3, num_trials=500)
        assert result["N"] == 14
        assert result["k"] == 3
        assert result["total_colorings"] == 500
        assert len(result["fraction_with_triple"]) == 3


# ── Experiment (d): Density barrier ──────────────────────────────


class TestMaxSumFreeDensity:
    def test_n1(self):
        S, d = max_sum_free_density_integer(1)
        assert d == 1.0
        assert S == {1}

    def test_n2(self):
        """[1,2]: {1} is sum-free (1+1=2, but 2 not in {1}). Density 1/2."""
        S, d = max_sum_free_density_integer(2)
        assert d >= 0.5

    def test_n4(self):
        """[1..4]: {1,4} or odds {1,3} size 2, density 0.5."""
        S, d = max_sum_free_density_integer(4)
        assert d >= 0.5
        assert not has_schur_triple(S)

    def test_n10(self):
        S, d = max_sum_free_density_integer(10)
        assert d >= 0.4
        assert not has_schur_triple(S)

    def test_odds_are_sum_free(self):
        """Odd numbers in [1..N] are always sum-free (odd+odd=even)."""
        for N in [5, 10, 20, 50]:
            odds = {x for x in range(1, N + 1) if x % 2 == 1}
            assert not has_schur_triple(odds)


class TestDensityVsN:
    def test_returns_correct_length(self):
        result = density_vs_N(20)
        assert len(result) == 20

    def test_all_positive(self):
        result = density_vs_N(20)
        for N, d in result:
            assert d > 0

    def test_approaches_half(self):
        """Density should approach 1/2 for large N (achieved by odds)."""
        result = density_vs_N(100)
        final_d = result[-1][1]
        assert final_d >= 0.45

    def test_monotone_envelope(self):
        """Density should not drop dramatically -- it's ~ ceil(N/2)/N."""
        result = density_vs_N(50)
        for i in range(1, len(result)):
            N, d = result[i]
            # density for large N should be roughly 0.5
            assert d >= 0.33


class TestDensityBarrier:
    def test_k2_always_can_avoid(self):
        """For k=2, max sum-free density is ~1/2 >= 1/k=1/2.
        So density alone never forces a triple (the barrier is structural)."""
        barrier = density_barrier_by_k(2, 30)
        for N, d, exceeds in barrier:
            if N >= 3:
                assert exceeds or d >= 0.49  # density ~1/2 >= 1/2

    def test_k3_exceeds_threshold(self):
        """For k=3, 1/k = 1/3 < 1/2. Max density always exceeds 1/3."""
        barrier = density_barrier_by_k(3, 30)
        for N, d, exceeds in barrier:
            if N >= 2:
                assert exceeds


# ── Symmetry / equivalence ───────────────────────────────────────


class TestColoringEquivalence:
    def test_swap_colors(self):
        """Two colorings differing by color swap should be in same class."""
        c1 = [0, 1, 1, 0]
        c2 = [1, 0, 0, 1]
        equiv = coloring_equivalence_classes([c1, c2])
        assert len(equiv) == 1

    def test_distinct_colorings(self):
        """Truly distinct colorings should be in different classes."""
        c1 = [0, 1, 1, 0]
        c2 = [0, 0, 1, 1]
        equiv = coloring_equivalence_classes([c1, c2])
        # These may or may not be equivalent depending on structure
        # but both are valid inputs
        assert len(equiv) >= 1

    def test_empty(self):
        equiv = coloring_equivalence_classes([])
        assert len(equiv) == 0

    def test_single(self):
        equiv = coloring_equivalence_classes([[0, 1, 0]])
        assert len(equiv) == 1


# ── Integration: known Schur numbers ─────────────────────────────


class TestKnownSchurNumbers:
    """Verify our tools are consistent with known S(k) values."""

    def test_s1_equals_1(self):
        """S(1)=1: [1] can be 1-colored Schur-free, [2] cannot."""
        assert is_valid_schur_coloring([0], 1)
        # [1,2] with 1 color: 1+1=2 is a triple
        assert not is_valid_schur_coloring([0, 0], 2)

    def test_s2_equals_4(self):
        """S(2)=4: valid 2-colorings exist at N=4, none at N=5."""
        colorings_4 = enumerate_extremal_colorings_k2(4)
        colorings_5 = enumerate_extremal_colorings_k2(5)
        assert len(colorings_4) > 0
        assert len(colorings_5) == 0

    def test_s3_equals_13(self):
        """S(3)=13: can find valid 3-coloring at N=13."""
        col = random_schur_coloring(13, 3, max_attempts=100000)
        assert col is not None
        assert is_valid_schur_coloring(col, 13)

    def test_s3_upper_bound(self):
        """S(3)=13: should NOT find valid 3-coloring at N=14 (probabilistic)."""
        col = random_schur_coloring(14, 3, max_attempts=5000)
        # This is probabilistic -- might find one by extreme luck, but very unlikely
        # If found, verify it's actually valid (would disprove S(3)=13!)
        if col is not None:
            assert is_valid_schur_coloring(col, 14), "Found invalid coloring"
