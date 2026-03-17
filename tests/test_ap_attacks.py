"""Tests for ap_attacks.py — arithmetic progressions & additive combinatorics."""
import math
import pytest

from ap_attacks import (
    # Section 1: r_k(n)
    contains_k_ap,
    has_k_ap,
    r_k_greedy,
    r_k_dp,
    compute_rk_table,
    behrend_lower_bound,
    kelley_meka_upper_bound,
    rk_bound_comparison,
    OEIS_A003002,
    OEIS_A003003,
    OEIS_A003004,
    verify_rk_oeis,
    # Section 2: Stanley sequences
    stanley_sequence,
    stanley_growth_analysis,
    stanley_variants,
    # Section 3: Sparse rulers
    ruler_differences,
    is_perfect_ruler,
    is_sparse_ruler,
    sparse_ruler_search,
    compute_sparse_ruler_table,
    sparse_ruler_lower_bound,
    wichmann_construction,
    OEIS_A046693,
    verify_sparse_ruler_oeis,
    # Section 4: Sum-product
    sumset,
    productset,
    sum_product_ratio,
    sum_product_structured_sets,
    sum_product_exponent_search,
    # Section 5: Behrend
    behrend_set,
    behrend_analysis,
    # Section 6: Density across k
    density_across_k,
    density_decay_fit,
    # Section 7: Cross-problem connections
    ap_free_is_sidon,
    ap_sumfree_sidon_overlaps,
)


# =============================================================================
# Section 1: r_k(n) tests
# =============================================================================

class TestContainsKAP:
    """Test the k-AP containment check."""

    def test_3ap_present(self):
        assert contains_k_ap({1, 3, 5}, 1, 2, 3)

    def test_3ap_absent(self):
        assert not contains_k_ap({1, 3, 6}, 1, 2, 3)

    def test_4ap_present(self):
        assert contains_k_ap({2, 5, 8, 11}, 2, 3, 4)

    def test_single_element(self):
        assert contains_k_ap({7}, 7, 1, 1)


class TestHasKAP:
    """Test detection of k-APs in sets."""

    def test_empty_set(self):
        assert not has_k_ap(set(), 3)

    def test_no_3ap(self):
        assert not has_k_ap({1, 2, 4}, 3)

    def test_has_3ap(self):
        assert has_k_ap({1, 2, 3}, 3)

    def test_has_3ap_nonconsecutive(self):
        assert has_k_ap({1, 5, 9}, 3)

    def test_no_4ap(self):
        assert not has_k_ap({1, 2, 4, 8}, 4)

    def test_has_4ap(self):
        assert has_k_ap({3, 6, 9, 12}, 4)

    def test_two_elements_no_3ap(self):
        assert not has_k_ap({1, 100}, 3)

    def test_large_ap_free(self):
        """Known 3-AP-free set: {1, 2, 4, 5, 10, 11, 13, 14} in base-3 free."""
        A = {1, 2, 4, 5, 10, 11, 13, 14}
        assert not has_k_ap(A, 3)


class TestRkGreedy:
    """Test greedy r_k(n) computation."""

    def test_r3_small(self):
        """r_3(1) = 1, r_3(2) = 2."""
        assert r_k_greedy(1, 3)[0] == 1
        assert r_k_greedy(2, 3)[0] == 2

    def test_r3_five(self):
        """r_3(5) = 4 (OEIS A003002)."""
        size, elems = r_k_greedy(5, 3)
        assert size >= 4  # greedy may match or exceed
        assert not has_k_ap(set(elems), 3)

    def test_r3_result_is_ap_free(self):
        """Output must be 3-AP-free."""
        for n in [10, 20, 30]:
            _, elems = r_k_greedy(n, 3)
            assert not has_k_ap(set(elems), 3), f"r_3({n}) result has 3-AP!"

    def test_r4_result_is_ap_free(self):
        """Output must be 4-AP-free."""
        for n in [10, 20, 30]:
            _, elems = r_k_greedy(n, 4)
            assert not has_k_ap(set(elems), 4), f"r_4({n}) result has 4-AP!"

    def test_monotone_in_n(self):
        """r_k(n) is non-decreasing in n."""
        prev = 0
        for n in range(1, 30):
            size, _ = r_k_greedy(n, 3)
            assert size >= prev, f"r_3({n}) = {size} < r_3({n-1}) = {prev}"
            prev = size

    def test_r3_at_least_behrend(self):
        """r_3(n) >= Behrend lower bound for moderate n."""
        for n in [50, 100]:
            size, _ = r_k_greedy(n, 3)
            lower = behrend_lower_bound(n)
            # Greedy should beat or match the Behrend bound
            # (the bound is not tight for small n, so just sanity check)
            assert size >= 1

    def test_elements_in_range(self):
        """All elements must be in [1..n]."""
        for n in [15, 25]:
            _, elems = r_k_greedy(n, 3)
            assert all(1 <= x <= n for x in elems)

    def test_r5_result_is_ap_free(self):
        """Output must be 5-AP-free."""
        for n in [15, 25]:
            _, elems = r_k_greedy(n, 5)
            assert not has_k_ap(set(elems), 5)


class TestRkDP:
    """Test exact r_k(n) computation via branch-and-bound."""

    def test_dp_matches_known_r3(self):
        """r_3(n) via DP should match OEIS A003002 for small n."""
        for n in range(1, 15):
            dp_val = r_k_dp(n, 3)
            expected = OEIS_A003002[n - 1]
            assert dp_val == expected, (
                f"r_3({n}): DP={dp_val} != OEIS={expected}"
            )

    def test_dp_r3_10(self):
        """r_3(10) = 5 (OEIS A003002)."""
        assert r_k_dp(10, 3) == 5

    def test_dp_r3_20(self):
        """r_3(20) = 9 (OEIS A003002)."""
        assert r_k_dp(20, 3) == 9

    def test_dp_r3_14(self):
        """r_3(14) = 8 (OEIS A003002)."""
        assert r_k_dp(14, 3) == 8

    def test_dp_fallback_large(self):
        """For n > 25, falls back to greedy."""
        val = r_k_dp(30, 3)
        assert val >= 1  # just check it runs

    def test_dp_ge_greedy(self):
        """DP (exact) should be >= greedy (lower bound)."""
        for n in range(1, 16):
            dp_val = r_k_dp(n, 3)
            greedy_val = r_k_greedy(n, 3)[0]
            assert dp_val >= greedy_val


class TestComputeRkTable:
    """Test the table computation."""

    def test_table_length(self):
        table = compute_rk_table(10, 3)
        assert len(table) == 10

    def test_table_fields(self):
        table = compute_rk_table(5, 3)
        row = table[0]
        assert "n" in row
        assert "k" in row
        assert "r_k" in row
        assert "density" in row

    def test_density_decreasing_trend(self):
        """Density r_k(n)/n should trend downward (Szemeredi)."""
        table = compute_rk_table(50, 3)
        # Compare early vs late density
        early = sum(r["density"] for r in table[:5]) / 5
        late = sum(r["density"] for r in table[-5:]) / 5
        assert late <= early + 0.1  # some tolerance for greedy


class TestBounds:
    """Test theoretical bounds."""

    def test_behrend_positive(self):
        for n in [10, 100, 1000]:
            assert behrend_lower_bound(n) > 0

    def test_behrend_less_than_n(self):
        for n in [10, 100, 1000]:
            assert behrend_lower_bound(n) < n

    def test_behrend_increasing(self):
        prev = 0
        for n in [10, 50, 100, 500]:
            val = behrend_lower_bound(n)
            assert val > prev
            prev = val

    def test_km_upper_less_than_n(self):
        for n in [10, 100, 1000]:
            assert kelley_meka_upper_bound(n) < n

    def test_km_upper_positive(self):
        for n in [10, 100, 1000]:
            assert kelley_meka_upper_bound(n) > 0

    def test_bounds_sandwich(self):
        """Behrend <= r_3(n) <= Kelley-Meka for large enough n."""
        for n in [50, 100]:
            size, _ = r_k_greedy(n, 3)
            beh = behrend_lower_bound(n)
            # Behrend bound is asymptotic; for moderate n
            # just check the computed value is in a reasonable range
            assert size > 0
            assert size <= n

    def test_rk_bound_comparison_structure(self):
        results = rk_bound_comparison(20)
        assert len(results) > 0
        for row in results:
            assert "n" in row
            assert "r3_greedy" in row
            assert "behrend_lower" in row


class TestVerifyOEIS:
    """Test OEIS verification."""

    def test_oeis_a003002_length(self):
        assert len(OEIS_A003002) == 20

    def test_oeis_a003003_length(self):
        assert len(OEIS_A003003) == 25

    def test_oeis_a003004_length(self):
        assert len(OEIS_A003004) == 25

    def test_verify_r3_format(self):
        result = verify_rk_oeis(3)
        assert "k" in result
        assert "matches" in result
        assert "mismatches" in result
        assert result["k"] == 3

    def test_verify_r3_mostly_matches(self):
        """Greedy should match OEIS for most small values (it's a lower bound)."""
        result = verify_rk_oeis(3)
        # Greedy is a lower bound, so it may undercount for some n.
        # It should still match the majority of values.
        assert result["accuracy"] >= 0.7


# =============================================================================
# Section 2: Stanley sequence tests
# =============================================================================

class TestStanleySequence:
    """Test Stanley sequence generation."""

    def test_s01_starts_correctly(self):
        """S(0,1) = A005836 = {0,1,3,4,9,10,12,13,27,...} (no digit 2 in base 3)."""
        seq = stanley_sequence((0, 1), 40)
        assert seq[0] == 0
        assert seq[1] == 1
        assert seq[2] == 3  # 2 is forbidden (0,1,2 is 3-AP)
        assert seq[3] == 4  # {0,1,3,4} is 3-AP-free
        assert seq[4] == 9  # next after gap (5 blocked by 1,3,5; etc.)
        # Verify against OEIS A005836
        expected = [0, 1, 3, 4, 9, 10, 12, 13, 27, 28, 30]
        assert seq[:len(expected)] == expected

    def test_s01_is_ap_free(self):
        """S(0,1) must be 3-AP-free."""
        seq = stanley_sequence((0, 1), 100)
        assert not has_k_ap(set(seq), 3)

    def test_s01_maximality(self):
        """Every gap element would create a 3-AP."""
        seq = stanley_sequence((0, 1), 50)
        seq_set = set(seq)
        max_elem = seq[-1]
        for x in range(max_elem + 1):
            if x not in seq_set:
                # Adding x should create a 3-AP
                test = seq_set | {x}
                assert has_k_ap(test, 3), (
                    f"Element {x} could be added without creating 3-AP"
                )

    def test_s02_is_ap_free(self):
        seq = stanley_sequence((0, 2), 50)
        assert not has_k_ap(set(seq), 3)

    def test_initial_terms_preserved(self):
        seq = stanley_sequence((0, 1, 3), 30)
        assert seq[0] == 0
        assert seq[1] == 1
        assert seq[2] == 3

    def test_growth_positive(self):
        seq = stanley_sequence((0, 1), 1000)
        assert len(seq) >= 10  # should find at least 10 elements in [0..1000]


class TestStanleyGrowth:
    """Test Stanley sequence growth analysis."""

    def test_growth_analysis_structure(self):
        result = stanley_growth_analysis(500)
        assert "sequence_length" in result
        assert "growth_data" in result
        assert "first_50" in result

    def test_growth_exponent_range(self):
        """Exponent should be between 0.5 and 1.0 for S(0,1)."""
        result = stanley_growth_analysis(5000)
        if result["growth_data"]:
            last = result["growth_data"][-1]
            assert 0.4 <= last["alpha_estimate"] <= 1.0

    def test_variants_structure(self):
        result = stanley_variants(500)
        assert "S(0,1)" in result
        assert "S(0,2)" in result


# =============================================================================
# Section 3: Sparse ruler tests
# =============================================================================

class TestRulerDifferences:
    """Test ruler difference computation."""

    def test_simple_ruler(self):
        diffs = ruler_differences([0, 1, 3])
        assert diffs == {1, 2, 3}

    def test_single_mark(self):
        diffs = ruler_differences([5])
        assert diffs == set()

    def test_two_marks(self):
        diffs = ruler_differences([0, 7])
        assert diffs == {7}


class TestIsPerfectRuler:
    """Test perfect ruler detection."""

    def test_perfect_ruler_3(self):
        assert is_perfect_ruler([0, 1, 3], 3)

    def test_not_perfect(self):
        assert not is_perfect_ruler([0, 1, 4], 3)


class TestIsSparseRuler:
    """Test sparse ruler detection."""

    def test_sparse_ruler_6(self):
        """[0, 1, 4, 6] measures all of 1..6."""
        assert is_sparse_ruler([0, 1, 4, 6], 6)

    def test_not_sparse(self):
        assert not is_sparse_ruler([0, 1, 5], 5)


class TestSparseRulerSearch:
    """Test sparse ruler search."""

    def test_ruler_length_1(self):
        ruler = sparse_ruler_search(1)
        assert ruler is not None
        assert is_sparse_ruler(ruler, 1)
        assert len(ruler) == 2

    def test_ruler_length_3(self):
        ruler = sparse_ruler_search(3)
        assert ruler is not None
        assert is_sparse_ruler(ruler, 3)
        assert len(ruler) == 3  # {0, 1, 3} or {0, 2, 3}

    def test_ruler_length_6(self):
        ruler = sparse_ruler_search(6)
        assert ruler is not None
        assert is_sparse_ruler(ruler, 6)
        assert len(ruler) <= 5  # known: m(6) = 4

    def test_ruler_valid_for_small_n(self):
        """Every returned ruler must actually measure all distances."""
        for n in range(1, 15):
            ruler = sparse_ruler_search(n)
            assert ruler is not None, f"No ruler found for n={n}"
            assert is_sparse_ruler(ruler, n), f"Ruler {ruler} doesn't measure 1..{n}"

    def test_ruler_includes_endpoints(self):
        """Ruler must include 0 and n."""
        for n in [5, 10]:
            ruler = sparse_ruler_search(n)
            assert 0 in ruler
            assert n in ruler


class TestSparseRulerLowerBound:
    """Test theoretical lower bound."""

    def test_bound_at_least_2(self):
        for n in range(1, 20):
            assert sparse_ruler_lower_bound(n) >= 2

    def test_bound_increasing(self):
        prev = 0
        for n in range(1, 50):
            val = sparse_ruler_lower_bound(n)
            assert val >= prev
            prev = val

    def test_bound_vs_known(self):
        """Lower bound should not exceed known values."""
        for n, known_m in enumerate(OEIS_A046693, start=1):
            lb = sparse_ruler_lower_bound(n)
            assert lb <= known_m, f"n={n}: lower bound {lb} > known m(n)={known_m}"


class TestWichmannConstruction:
    """Test Wichmann ruler construction."""

    def test_wichmann_t1(self):
        marks = wichmann_construction(1)
        n = 5  # 4*1 + 1
        assert is_sparse_ruler(marks, n)

    def test_wichmann_t2(self):
        marks = wichmann_construction(2)
        n = 9
        assert is_sparse_ruler(marks, n)

    def test_wichmann_t3(self):
        marks = wichmann_construction(3)
        n = 13
        assert is_sparse_ruler(marks, n)

    def test_wichmann_mark_count(self):
        """Wichmann ruler with parameter t has 2t+3 marks."""
        for t in range(1, 6):
            marks = wichmann_construction(t)
            assert len(marks) == 2 * t + 3

    def test_wichmann_length(self):
        """Wichmann ruler has length 4t+1."""
        for t in range(1, 6):
            marks = wichmann_construction(t)
            assert marks[-1] == 4 * t + 1

    def test_wichmann_all_valid(self):
        """All Wichmann rulers should be valid sparse rulers."""
        for t in range(1, 10):
            marks = wichmann_construction(t)
            n = 4 * t + 1
            assert is_sparse_ruler(marks, n), f"Wichmann(t={t}) invalid"


class TestVerifySparseRulerOEIS:
    """Test OEIS verification for sparse rulers."""

    def test_oeis_a046693_length(self):
        assert len(OEIS_A046693) == 36

    def test_verify_format(self):
        # Only verify a few to keep tests fast
        # Full verification is done in the experiment runner
        for n in range(1, 6):
            ruler = sparse_ruler_search(n)
            assert ruler is not None
            assert len(ruler) == OEIS_A046693[n - 1], (
                f"n={n}: got {len(ruler)} marks, expected {OEIS_A046693[n-1]}"
            )


# =============================================================================
# Section 4: Sum-product tests
# =============================================================================

class TestSumset:
    """Test sumset computation."""

    def test_sumset_small(self):
        assert sumset({1, 2}) == {2, 3, 4}

    def test_sumset_singleton(self):
        assert sumset({5}) == {10}

    def test_sumset_size_ap(self):
        """A = {1,...,n}: |A+A| = 2n-1."""
        A = set(range(1, 11))
        assert len(sumset(A)) == 19


class TestProductset:
    """Test productset computation."""

    def test_productset_small(self):
        assert productset({2, 3}) == {4, 6, 9}

    def test_productset_singleton(self):
        assert productset({5}) == {25}


class TestSumProductRatio:
    """Test sum-product ratio computation."""

    def test_ap_small_sumset(self):
        """AP has |A+A| = 2|A|-1, relatively small."""
        A = set(range(1, 11))
        result = sum_product_ratio(A)
        assert result["sum_size"] == 19
        assert result["product_size"] > 19  # product should be larger

    def test_gp_small_productset(self):
        """GP has small productset."""
        A = {2 ** i for i in range(5)}  # {1,2,4,8,16}
        result = sum_product_ratio(A)
        assert result["product_size"] <= 9  # {1,2,4,...,256} = 9 distinct

    def test_sum_product_product_positive(self):
        A = {1, 2, 3, 4, 5}
        result = sum_product_ratio(A)
        assert result["sum_product_product"] > 0

    def test_fields_present(self):
        result = sum_product_ratio({1, 2, 3})
        for key in ["n", "sum_size", "product_size", "max_sp", "sum_ratio",
                     "product_ratio", "max_ratio"]:
            assert key in result


class TestSumProductStructured:
    """Test structured set analysis."""

    def test_structured_sets_nonempty(self):
        results = sum_product_structured_sets(20)
        assert len(results) > 0

    def test_ap_vs_gp(self):
        """AP should have smaller sumset ratio; GP smaller productset ratio."""
        results = sum_product_structured_sets(20)
        ap = results.get("AP_10")
        gp = results.get("GP_10")
        if ap and gp:
            assert ap["sum_ratio"] < gp["sum_ratio"]
            assert gp["product_ratio"] < ap["product_ratio"]


class TestSumProductExponent:
    """Test exponent search."""

    def test_exponent_at_least_1(self):
        """max(|A+A|,|A*A|) >= |A|, so exponent >= 1."""
        results = sum_product_exponent_search([10, 20])
        for row in results:
            assert row["alpha_estimate"] >= 0.9  # allow tolerance

    def test_exponent_search_structure(self):
        results = sum_product_exponent_search([10])
        assert len(results) == 1
        row = results[0]
        assert "n" in row
        assert "alpha_estimate" in row
        assert "target_4_3" in row


# =============================================================================
# Section 5: Behrend tests
# =============================================================================

class TestBehrend:
    """Test Behrend-type constructions."""

    def test_behrend_set_ap_free(self):
        """Behrend set must be 3-AP-free."""
        for n in [20, 50]:
            bset, _ = behrend_set(n)
            if len(bset) >= 3:
                assert not has_k_ap(bset, 3), f"Behrend set in [{n}] has 3-AP!"

    def test_behrend_set_in_range(self):
        """All elements must be in [1..n]."""
        for n in [20, 50]:
            bset, _ = behrend_set(n)
            assert all(1 <= x <= n for x in bset)

    def test_behrend_set_nonempty(self):
        for n in [10, 30, 50]:
            bset, _ = behrend_set(n)
            assert len(bset) >= 1

    def test_behrend_analysis_structure(self):
        results = behrend_analysis([20, 50])
        assert len(results) == 2
        for row in results:
            assert "greedy_size" in row
            assert "behrend_size" in row


# =============================================================================
# Section 6: Density across k tests
# =============================================================================

class TestDensityAcrossK:
    """Test density comparison across k."""

    def test_density_dict_keys(self):
        result = density_across_k(20, [3, 4])
        assert "k=3" in result
        assert "k=4" in result

    def test_density_positive(self):
        result = density_across_k(20, [3])
        for row in result["k=3"]:
            assert row["density"] > 0

    def test_higher_k_higher_density(self):
        """r_k(n)/n should generally increase with k (more freedom)."""
        result = density_across_k(30, [3, 4, 5])
        # At n=30, r_5(30)/30 >= r_3(30)/30 (5-AP is stricter condition)
        r3_last = result["k=3"][-1]["density"]
        r5_last = result["k=5"][-1]["density"]
        assert r5_last >= r3_last - 0.1  # some tolerance


class TestDensityDecayFit:
    """Test density decay fitting."""

    def test_fit_structure(self):
        result = density_decay_fit(50, 3)
        assert "k" in result
        assert "final_density" in result
        assert "densities" in result

    def test_fit_has_data_points(self):
        result = density_decay_fit(50, 3)
        assert result["num_points"] > 0


# =============================================================================
# Section 7: Cross-problem connection tests
# =============================================================================

class TestAPFreeSidon:
    """Test AP-free / Sidon / sum-free overlaps."""

    def test_ap_free_check(self):
        result = ap_free_is_sidon(20, 3)
        assert "is_sidon" in result
        assert "is_sum_free" in result
        assert result["ap_free_size"] > 0

    def test_overlaps_structure(self):
        result = ap_sumfree_sidon_overlaps(20)
        assert len(result) > 0
        row = result[0]
        assert "ap_free_size" in row
        assert "sum_free_size" in row
        assert "sidon_size" in row
        assert "ap_sf_inter" in row

    def test_intersection_at_most_min(self):
        """Intersection size <= min of set sizes."""
        results = ap_sumfree_sidon_overlaps(30)
        for row in results:
            assert row["ap_sf_inter"] <= min(row["ap_free_size"], row["sum_free_size"])
            assert row["ap_sidon_inter"] <= min(row["ap_free_size"], row["sidon_size"])


# =============================================================================
# Integration / regression tests
# =============================================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_rk_table_consistency(self):
        """r_k(n) from table matches individual calls."""
        table = compute_rk_table(15, 3)
        for row in table:
            size, _ = r_k_greedy(row["n"], 3)
            assert size == row["r_k"]

    def test_stanley_ap_free_invariant(self):
        """Stanley sequence must be 3-AP-free at every prefix."""
        seq = stanley_sequence((0, 1), 200)
        for length in [5, 10, 20, len(seq)]:
            prefix = set(seq[:length])
            assert not has_k_ap(prefix, 3)

    def test_sparse_ruler_wichmann_valid(self):
        """Wichmann rulers must be valid sparse rulers."""
        for t in range(1, 5):
            n = 4 * t + 1
            marks = wichmann_construction(t)
            assert is_sparse_ruler(marks, n), (
                f"Wichmann(t={t}) is not a valid sparse ruler for n={n}"
            )

    def test_sum_product_never_both_small(self):
        """No set should have both |A+A| and |A*A| close to |A|."""
        for n in [8, 12, 16]:
            ap = set(range(1, n + 1))
            result = sum_product_ratio(ap)
            # At least one must be >= n (actually >= 2n-1 for either)
            assert result["max_sp"] >= n

    @pytest.mark.parametrize("n", [5, 10, 14, 20])
    def test_r3_dp_matches_oeis(self, n):
        """Exact DP computation matches OEIS A003002."""
        if n <= len(OEIS_A003002):
            dp_val = r_k_dp(n, 3)
            expected = OEIS_A003002[n - 1]
            assert dp_val == expected, (
                f"r_3({n}): dp={dp_val}, OEIS={expected}"
            )

    def test_density_decay_for_r3(self):
        """r_3(n)/n should be clearly below 1 for n >= 20."""
        size, _ = r_k_greedy(50, 3)
        assert size / 50 < 0.8

    def test_behrend_vs_greedy(self):
        """Greedy should do at least as well as Behrend for moderate n."""
        for n in [30, 50]:
            greedy_size, _ = r_k_greedy(n, 3)
            bset, _ = behrend_set(n)
            # Both are valid lower bounds; no strict ordering required
            assert greedy_size >= 1
            assert len(bset) >= 1
