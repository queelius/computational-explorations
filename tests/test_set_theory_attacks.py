"""Tests for set_theory_attacks.py -- set theory & extremal combinatorics."""
import math
import pytest

from set_theory_attacks import (
    # Section 1: Hales-Jewett
    combinatorial_lines,
    has_monochromatic_line,
    check_hj,
    hj_sat,
    compute_hj,
    hj_table,
    hj_lower_bound_witness,
    # Section 2: Sunflower
    is_sunflower,
    find_sunflower,
    sunflower_free_family,
    compute_sunflower_number,
    sunflower_number_sat,
    sunflower_table,
    # Section 3: Bounds
    erdos_rado_bound,
    alwz_bound,
    rao_bound,
    sunflower_bound_comparison,
    sunflower_bound_crossover,
    verify_sunflower_bounds,
    # Section 4: Intersection
    family_avoids_intersection,
    max_family_avoiding_intersection,
    max_family_sat,
    ray_chaudhuri_wilson_bound,
    frankl_wilson_bound,
    intersection_spectrum,
    erdos_ko_rado,
    max_t_intersecting_family,
    set_intersection_table,
    # Section 5: Partition calculus
    check_arrow,
    check_arrow_sat,
    compute_ramsey,
    compute_ramsey_table,
    hypergraph_ramsey_bounds,
    partition_calculus_examples,
    # Synthesis
    run_all_experiments,
)


# =============================================================================
# Section 1: Hales-Jewett Numbers
# =============================================================================

class TestCombinatorialLines:
    """Test enumeration of combinatorial lines."""

    def test_lines_2_1(self):
        """[2]^1 has 1 line: (0), (1)."""
        lines = combinatorial_lines(2, 1)
        assert len(lines) == 1
        assert lines[0] == [(0,), (1,)]

    def test_lines_2_2(self):
        """[2]^2 has 5 lines: 2 rows, 2 cols, 1 diagonal."""
        lines = combinatorial_lines(2, 2)
        # Rows: fix coord 0, vary coord 1; fix coord 1, vary coord 0
        # Diag: vary both
        assert len(lines) == 5

    def test_lines_3_1(self):
        """[3]^1 has 1 line: (0), (1), (2)."""
        lines = combinatorial_lines(3, 1)
        assert len(lines) == 1
        assert lines[0] == [(0,), (1,), (2,)]

    def test_lines_empty(self):
        lines = combinatorial_lines(0, 3)
        assert lines == []
        lines = combinatorial_lines(3, 0)
        assert lines == []

    def test_each_line_has_n_points(self):
        """Every line in [n]^N has exactly n points."""
        for n in [2, 3]:
            for N in [1, 2, 3]:
                lines = combinatorial_lines(n, N)
                for line in lines:
                    assert len(line) == n

    def test_points_are_distinct(self):
        """All points in a line are distinct."""
        lines = combinatorial_lines(3, 2)
        for line in lines:
            assert len(set(line)) == len(line)

    def test_line_count_formula(self):
        """Number of lines in [n]^N = ((n+1)^N - n^N) / 1 for n=2."""
        # For n=2: lines = 3^N - 2^N (each line determined by 3^N assignments
        # minus those where no coordinate varies).
        for N in [1, 2, 3]:
            lines = combinatorial_lines(2, N)
            expected = 3**N - 2**N
            assert len(lines) == expected


class TestHasMonochromaticLine:

    def test_monochromatic_exists(self):
        """All-same coloring always has a monochromatic line."""
        points = [(0,), (1,)]
        lines = [[(0,), (1,)]]
        coloring = {(0,): 0, (1,): 0}
        assert has_monochromatic_line(coloring, lines)

    def test_no_monochromatic(self):
        """Alternating coloring of [2]^1 avoids monochromatic lines."""
        lines = [[(0,), (1,)]]
        coloring = {(0,): 0, (1,): 1}
        assert not has_monochromatic_line(coloring, lines)


class TestHaleJewett:
    """Test Hales-Jewett number computation."""

    def test_hj_1_n(self):
        """HJ(1, n) = 1 for all n: single color, any point is a line."""
        for n in [2, 3, 4]:
            assert compute_hj(1, n, max_N=3) == 1

    def test_hj_2_2(self):
        """HJ(2, 2) = 2 (tic-tac-toe in 2D is trivially forced)."""
        assert compute_hj(2, 2, max_N=4) == 2

    def test_hj_2_3_known(self):
        """HJ(2, 3) = 4 (equivalent to Van der Waerden W(3;2))."""
        assert compute_hj(2, 3, max_N=5) == 4

    def test_hj_sat_witness_n3(self):
        """HJ(2,3) > 3: SAT should find an avoiding 2-coloring of [3]^3."""
        avoiding, coloring = hj_sat(2, 3, 3)
        assert avoiding
        assert coloring is not None
        # Verify the coloring is valid
        lines = combinatorial_lines(3, 3)
        assert not has_monochromatic_line(coloring, lines)

    def test_hj_sat_no_witness_n4(self):
        """HJ(2,3) <= 4: SAT should find no avoiding coloring of [3]^4."""
        avoiding, coloring = hj_sat(2, 3, 4)
        assert not avoiding
        assert coloring is None

    def test_hj_lower_bound_witness(self):
        """Lower bound witness: 2-coloring of [3]^2 avoiding all lines."""
        w = hj_lower_bound_witness(2, 3, 2)
        assert w is not None
        lines = combinatorial_lines(3, 2)
        assert not has_monochromatic_line(w, lines)

    def test_hj_table_contains_known(self):
        """Table includes known values."""
        table = hj_table(max_k=2, max_n=3, max_N=5)
        assert table[(1, 2)] == 1
        assert table[(2, 2)] == 2
        assert table[(2, 3)] == 4


class TestCheckHJBruteForce:
    """Test brute-force HJ checker for tiny instances."""

    def test_trivial_n1(self):
        """n=1: always forced."""
        assert check_hj(2, 1, 1)

    def test_2_2_at_N1(self):
        """HJ(2,2) <= 2: at N=2 every 2-coloring has a mono line."""
        assert check_hj(2, 2, 2)

    def test_2_2_not_at_N1(self):
        """HJ(2,2) > 1: at N=1 there exists avoiding 2-coloring."""
        assert not check_hj(2, 2, 1)


# =============================================================================
# Section 2: Sunflower Numbers
# =============================================================================

class TestIsSunflower:
    """Test sunflower detection."""

    def test_two_sets_always_sunflower(self):
        """Any two distinct sets form a 2-sunflower."""
        fam = [frozenset({1, 2}), frozenset({2, 3})]
        assert is_sunflower(fam, 2) is not None

    def test_three_disjoint_pairs(self):
        """Three disjoint pairs form a 3-sunflower with empty kernel."""
        fam = [frozenset({1, 2}), frozenset({3, 4}), frozenset({5, 6})]
        result = is_sunflower(fam, 3)
        assert result is not None

    def test_three_pairs_through_vertex(self):
        """Three pairs through vertex 1 form a 3-sunflower with kernel {1}."""
        fam = [frozenset({1, 2}), frozenset({1, 3}), frozenset({1, 4})]
        indices = is_sunflower(fam, 3)
        assert indices is not None

    def test_not_sunflower(self):
        """Triangle of pairs: no 3-sunflower."""
        fam = [frozenset({1, 2}), frozenset({2, 3}), frozenset({1, 3})]
        # {1,2} & {2,3} = {2}, {1,2} & {1,3} = {1}, {2,3} & {1,3} = {3}
        # Not a sunflower since pairwise intersections differ.
        assert is_sunflower(fam, 3) is None

    def test_too_few_sets(self):
        fam = [frozenset({1, 2})]
        assert is_sunflower(fam, 3) is None


class TestFindSunflower:
    """Test sunflower finding with kernel extraction."""

    def test_finds_kernel(self):
        fam = [frozenset({1, 2}), frozenset({1, 3}), frozenset({1, 4})]
        result = find_sunflower(fam, 3)
        assert result is not None
        indices, kernel = result
        assert kernel == frozenset({1})
        assert len(indices) == 3

    def test_empty_kernel(self):
        fam = [frozenset({1, 2}), frozenset({3, 4}), frozenset({5, 6})]
        result = find_sunflower(fam, 3)
        assert result is not None
        _, kernel = result
        assert kernel == frozenset()


class TestSunflowerNumbers:
    """Test exact sunflower number computation."""

    def test_f_1_r(self):
        """f(1, r) = r (pigeonhole on singletons)."""
        for r in range(2, 6):
            val, _ = compute_sunflower_number(1, r)
            assert val == r

    def test_f_k_2(self):
        """f(k, 2) = 2 for all k >= 1 (any two sets form a 2-sunflower)."""
        for k in range(1, 5):
            val, _ = compute_sunflower_number(k, 2)
            assert val == 2

    def test_f_2_3(self):
        """f(2, 3) = 7 (maximum sunflower-free family of pairs has 6 sets)."""
        val, best = compute_sunflower_number(2, 3, max_universe=12)
        assert val == 7
        assert best == 6

    def test_f_3_3(self):
        """f(3, 3): computed value should be <= Erdos-Rado bound 49."""
        val, _ = compute_sunflower_number(3, 3, max_universe=20)
        assert 2 <= val <= erdos_rado_bound(3, 3)

    def test_sunflower_table_monotonicity(self):
        """f(k, r) is non-decreasing in both k and r."""
        table = sunflower_table(max_k=2, max_r=4)
        for k in [1, 2]:
            for r in range(2, 4):
                assert table[(k, r)] <= table[(k, r + 1)]
        for r in [2, 3, 4]:
            assert table[(1, r)] <= table[(2, r)]


class TestSunflowerSAT:
    """Test SAT-based sunflower number computation."""

    def test_sat_f_2_3_lower(self):
        """SAT confirms: family of 6 pairs with no 3-sunflower exists."""
        exists, family = sunflower_number_sat(2, 3, 6, universe_size=8)
        assert exists
        assert len(family) >= 6

    def test_sat_f_2_3_upper(self):
        """SAT confirms: no family of 7 pairs in [8] avoids 3-sunflower."""
        exists, _ = sunflower_number_sat(2, 3, 7, universe_size=8)
        assert not exists

    def test_sat_witness_is_valid(self):
        """SAT witness family actually avoids sunflowers."""
        exists, family = sunflower_number_sat(2, 3, 6, universe_size=8)
        assert exists
        assert is_sunflower(family, 3) is None


class TestSunflowerFreeFamilyGreedy:

    def test_greedy_respects_constraint(self):
        """Greedy family has no r-sunflower."""
        fam = sunflower_free_family(2, 3, 10)
        assert is_sunflower(fam, 3) is None

    def test_greedy_nonempty(self):
        fam = sunflower_free_family(2, 3, 5)
        assert len(fam) > 0


# =============================================================================
# Section 3: Sunflower Bound Comparison
# =============================================================================

class TestErdosRadoBound:

    def test_k1(self):
        """k=1: f(1, r) <= 1! * (r-1)^1 + 1 = r."""
        for r in range(2, 6):
            assert erdos_rado_bound(1, r) == r

    def test_k2_r3(self):
        """k=2, r=3: 2! * 2^2 + 1 = 9."""
        assert erdos_rado_bound(2, 3) == 9

    def test_k3_r3(self):
        """k=3, r=3: 3! * 2^3 + 1 = 49."""
        assert erdos_rado_bound(3, 3) == 49


class TestALWZBound:

    def test_alwz_finite(self):
        """ALWZ bound is finite for k,r >= 1."""
        for k in range(1, 6):
            for r in range(2, 6):
                assert alwz_bound(k, r) >= 1

    def test_alwz_monotone_in_r(self):
        """ALWZ bound is non-decreasing in r."""
        for k in [2, 3, 4]:
            for r in range(2, 5):
                assert alwz_bound(k, r) <= alwz_bound(k, r + 1)

    def test_alwz_edge_cases(self):
        assert alwz_bound(0, 3) == 1
        assert alwz_bound(3, 1) == 1


class TestRaoBound:

    def test_rao_finite(self):
        for k in range(1, 6):
            for r in range(2, 6):
                assert rao_bound(k, r) >= 1

    def test_rao_smaller_than_alwz(self):
        """Rao's tighter constant should give smaller bounds."""
        for k in range(2, 8):
            for r in [3, 4]:
                assert rao_bound(k, r) <= alwz_bound(k, r)


class TestBoundComparison:

    def test_comparison_structure(self):
        result = sunflower_bound_comparison(max_k=3, max_r=3)
        assert 'erdos_rado' in result
        assert 'alwz' in result
        assert 'rao' in result
        assert (2, 3) in result['erdos_rado']

    def test_verification_all_valid(self):
        """All upper bounds should be >= exact values."""
        verif = verify_sunflower_bounds(max_k=2, max_r=3)
        for entry in verif:
            assert entry['er_valid'], f"ER invalid at k={entry['k']}, r={entry['r']}"

    def test_crossover_none_for_r3_c10(self):
        """With C=10, ALWZ never beats ER for r=3 in small k range."""
        # The constant C=10 is too large; crossover requires huge k
        result = sunflower_bound_crossover(r=3, max_k=20)
        # Could be None or very large
        if result is not None:
            assert result >= 2


# =============================================================================
# Section 4: Set Intersection Problems
# =============================================================================

class TestFamilyAvoidsIntersection:

    def test_intersecting_family(self):
        """Star family: all sets contain element 1 -> avoids |cap|=0."""
        fam = [frozenset({1, 2}), frozenset({1, 3}), frozenset({1, 4})]
        assert family_avoids_intersection(fam, {0})

    def test_not_intersecting(self):
        """Disjoint pair fails to avoid |cap|=0."""
        fam = [frozenset({1, 2}), frozenset({3, 4})]
        assert not family_avoids_intersection(fam, {0})

    def test_avoids_specific_size(self):
        """Two disjoint sets avoid |cap|=1."""
        fam = [frozenset({1, 2}), frozenset({3, 4})]
        assert family_avoids_intersection(fam, {1})


class TestMaxFamilyAvoiding:

    def test_intersecting_3_family_in_6(self):
        """Max intersecting 3-family in [6]: C(5,2) = 10 by EKR."""
        size, fam = max_family_avoiding_intersection(6, 3, {0})
        assert size == 10

    def test_intersecting_3_family_in_7(self):
        """Max intersecting 3-family in [7]: C(6,2) = 15 by EKR."""
        size, fam = max_family_avoiding_intersection(7, 3, {0})
        assert size == 15

    def test_family_is_valid(self):
        """Returned family actually avoids the forbidden intersection."""
        size, fam = max_family_avoiding_intersection(6, 2, {1})
        assert family_avoids_intersection(fam, {1})


class TestMaxFamilySAT:

    def test_sat_matches_greedy(self):
        """SAT optimizer should match or beat greedy for small instances."""
        for n in [5, 6]:
            size_g, _ = max_family_avoiding_intersection(n, 2, {0})
            size_s, _ = max_family_sat(n, 2, {0})
            assert size_s >= size_g

    def test_sat_family_valid(self):
        """SAT family is valid."""
        size, fam = max_family_sat(5, 2, {1})
        assert family_avoids_intersection(fam, {1})


class TestIntersectionSpectrum:

    def test_disjoint_pairs(self):
        fam = [frozenset({1, 2}), frozenset({3, 4})]
        spec = intersection_spectrum(fam)
        assert spec == {0: 1}

    def test_star_family(self):
        fam = [frozenset({1, 2}), frozenset({1, 3}), frozenset({1, 4})]
        spec = intersection_spectrum(fam)
        assert spec == {1: 3}  # all three pairs intersect in 1 element

    def test_complete_overlap(self):
        fam = [frozenset({1, 2, 3}), frozenset({1, 2, 3})]
        spec = intersection_spectrum(fam)
        assert spec == {3: 1}


class TestEKR:

    def test_ekr_n4_k2(self):
        """EKR(4, 2) = C(3, 1) = 3."""
        assert erdos_ko_rado(4, 2) == 3

    def test_ekr_n6_k2(self):
        """EKR(6, 2) = C(5, 1) = 5."""
        assert erdos_ko_rado(6, 2) == 5

    def test_ekr_small_n(self):
        """n < 2k: all k-subsets are intersecting."""
        assert erdos_ko_rado(3, 2) == math.comb(3, 2)  # = 3
        assert erdos_ko_rado(5, 3) == math.comb(5, 3)  # = 10

    def test_ekr_matches_computation(self):
        """EKR formula matches brute force for small cases."""
        for n in [4, 5, 6]:
            ekr = erdos_ko_rado(n, 2)
            computed, _ = max_family_avoiding_intersection(n, 2, {0})
            assert computed == ekr


class TestMaxTIntersecting:

    def test_t0_gives_all(self):
        """t=0: no intersection requirement -> all k-subsets."""
        assert max_t_intersecting_family(6, 3, 0) == math.comb(6, 3)

    def test_t_exceeds_k(self):
        assert max_t_intersecting_family(6, 3, 4) == 0

    def test_t1_k3(self):
        """t=1, k=3, large n: C(n-1, 2) by EKR generalization."""
        n = 8
        result = max_t_intersecting_family(n, 3, 1)
        assert result == math.comb(n - 1, 3 - 1)


class TestRCWBound:

    def test_rcw(self):
        assert ray_chaudhuri_wilson_bound(10, 2) == math.comb(10, 2)
        assert ray_chaudhuri_wilson_bound(10, 3) == math.comb(10, 3)

    def test_frankl_wilson(self):
        assert frankl_wilson_bound(10, 2) == math.comb(10, 1)


class TestSetIntersectionTable:

    def test_table_nonempty(self):
        table = set_intersection_table(max_n=6, k=2)
        assert len(table) > 0

    def test_table_values_positive(self):
        table = set_intersection_table(max_n=6, k=2)
        for val in table.values():
            assert val >= 1


# =============================================================================
# Section 5: Partition Calculus
# =============================================================================

class TestCheckArrow:
    """Test brute-force arrow notation check."""

    def test_m_gt_n_arrow_fails(self):
        """n -> (m)^r_k fails when m > n: no m-subsets exist."""
        assert not check_arrow(2, 3, 2, 2)

    def test_m_gt_n_sat_consistent(self):
        """SAT and brute force agree: arrow fails when m > n."""
        holds, _ = check_arrow_sat(2, 3, 2, 2)
        assert not holds

    def test_5_not_arrow_3_2_2(self):
        """5 -/-> (3)^2_2: witness exists (R(3,3) = 6)."""
        assert not check_arrow(5, 3, 2, 2)


class TestCheckArrowSAT:
    """Test SAT-based arrow notation."""

    def test_r33_lower(self):
        """5 -/-> (3)^2_2."""
        holds, coloring = check_arrow_sat(5, 3, 2, 2)
        assert not holds
        assert coloring is not None

    def test_r33_exact(self):
        """6 -> (3)^2_2 (R(3,3) = 6)."""
        holds, _ = check_arrow_sat(6, 3, 2, 2)
        assert holds

    def test_witness_valid(self):
        """Avoiding coloring at n=5 is valid: no mono K_3."""
        holds, coloring = check_arrow_sat(5, 3, 2, 2)
        assert not holds
        # Every 3-subset should have edges with both colors
        from itertools import combinations
        for triple in combinations(range(5), 3):
            edges = list(combinations(triple, 2))
            colors = {coloring[e] for e in edges}
            assert len(colors) > 1  # not monochromatic

    def test_pigeonhole(self):
        """R(m; 1, k) = (m-1)*k + 1: pigeonhole on 1-subsets."""
        # R(3; 1, 2) = 5
        holds4, _ = check_arrow_sat(4, 3, 1, 2)
        holds5, _ = check_arrow_sat(5, 3, 1, 2)
        assert not holds4
        assert holds5


class TestComputeRamsey:

    def test_r33(self):
        """R(3, 3) = R(3; 2, 2) = 6."""
        assert compute_ramsey(3, 2, 2, max_n=10) == 6

    def test_pigeonhole_r1(self):
        """R(3; 1, 2) = 5."""
        assert compute_ramsey(3, 1, 2, max_n=10) == 5

    def test_pigeonhole_r1_k3(self):
        """R(3; 1, 3) = 7."""
        assert compute_ramsey(3, 1, 3, max_n=10) == 7


class TestHypergraphRamseyBounds:

    def test_pigeonhole(self):
        """R(m; 1, k) is exact: (m-1)*k + 1."""
        lo, hi = hypergraph_ramsey_bounds(3, 1, 2)
        assert lo == hi == 5

    def test_classical_2color(self):
        """Classical R(m, m) bounds are valid."""
        lo, hi = hypergraph_ramsey_bounds(3, 2, 2)
        assert lo <= 6 <= hi  # R(3,3) = 6

    def test_hypergraph_tower(self):
        """r >= 3 gives tower-type lower bounds."""
        lo, hi = hypergraph_ramsey_bounds(3, 3, 2)
        assert lo >= 8  # tower(1, 3) = 2^3 = 8

    def test_bounds_ordered(self):
        for m in [3, 4, 5]:
            for r in [1, 2, 3]:
                lo, hi = hypergraph_ramsey_bounds(m, r, 2)
                assert lo <= hi


class TestPartitionCalculusExamples:

    def test_examples_return_list(self):
        results = partition_calculus_examples()
        assert isinstance(results, list)
        assert len(results) > 0

    def test_r33_in_examples(self):
        """R(3,3)=6 is confirmed in examples."""
        results = partition_calculus_examples()
        r33_results = [r for r in results if '(3)^2_2' in r['notation']]
        # n=5 should not hold, n=6 should hold
        for r in r33_results:
            if r['notation'] == '5 -> (3)^2_2':
                assert not r['holds']
            elif r['notation'] == '6 -> (3)^2_2':
                assert r['holds']


class TestComputeRamseyTable:

    def test_table_contains_r33(self):
        table = compute_ramsey_table(max_m=3, max_k=2)
        assert (3, 2) in table
        assert table[(3, 2)] == 6


# =============================================================================
# Integration / Synthesis
# =============================================================================

class TestRunAllExperiments:

    def test_runs_without_error(self):
        results = run_all_experiments(verbose=False)
        assert 'hales_jewett' in results
        assert 'sunflower' in results
        assert 'sunflower_bounds' in results
        assert 'intersection' in results
        assert 'partition_calculus' in results

    def test_hj_known_values(self):
        results = run_all_experiments(verbose=False)
        hj = results['hales_jewett']
        assert hj[(1, 2)] == 1
        assert hj[(2, 2)] == 2
        assert hj[(2, 3)] == 4

    def test_sunflower_known_values(self):
        results = run_all_experiments(verbose=False)
        sf = results['sunflower']
        assert sf[(1, 2)] == 2
        assert sf[(1, 3)] == 3
        assert sf[(2, 2)] == 2
        assert sf[(2, 3)] == 7


# =============================================================================
# Edge cases and consistency
# =============================================================================

class TestEdgeCases:

    def test_empty_family_sunflower(self):
        assert is_sunflower([], 2) is None

    def test_single_set_no_sunflower(self):
        assert is_sunflower([frozenset({1, 2})], 2) is None

    def test_erdos_rado_k0(self):
        """k=0: 0! * (r-1)^0 + 1 = 2."""
        assert erdos_rado_bound(0, 3) == 2  # 0! * 2^0 + 1 = 2

    def test_intersection_empty_L(self):
        """No forbidden intersections: all k-sets allowed."""
        size, fam = max_family_avoiding_intersection(5, 2, set())
        assert size == math.comb(5, 2)  # all 10 pairs

    def test_hj_trivial_k1(self):
        """Single color always gives monochromatic line."""
        assert compute_hj(1, 5, max_N=2) == 1


class TestConsistency:
    """Cross-check different computation methods."""

    def test_hj_sat_matches_brute(self):
        """SAT and brute force agree on HJ(2,2)."""
        brute = check_hj(2, 2, 2)  # HJ(2,2) <= 2
        avoiding, _ = hj_sat(2, 2, 2)
        assert brute == (not avoiding)

    def test_sunflower_greedy_vs_sat(self):
        """Greedy and SAT agree on f(2,3) = 7."""
        greedy_val, _ = compute_sunflower_number(2, 3, max_universe=10)
        # SAT: family of 6 exists, family of 7 does not
        exists_6, _ = sunflower_number_sat(2, 3, 6, universe_size=8)
        exists_7, _ = sunflower_number_sat(2, 3, 7, universe_size=8)
        assert exists_6 and not exists_7
        assert greedy_val == 7

    def test_ekr_vs_brute(self):
        """EKR formula matches brute force computation."""
        for n in [4, 5, 6, 7]:
            ekr = erdos_ko_rado(n, 2)
            brute, _ = max_family_avoiding_intersection(n, 2, {0})
            assert ekr == brute, f"EKR mismatch at n={n}: formula={ekr}, brute={brute}"

    def test_arrow_sat_vs_brute(self):
        """SAT and brute force agree for small instances."""
        # 5 -/-> (3)^2_2
        brute = check_arrow(5, 3, 2, 2)
        sat_holds, _ = check_arrow_sat(5, 3, 2, 2)
        assert brute == sat_holds
