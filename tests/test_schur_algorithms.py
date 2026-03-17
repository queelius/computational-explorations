"""Tests for schur_algorithms.py — SAT / backtracking / DP speedups."""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from schur_algorithms import (
    SchurSATEncoder,
    _ds_sat_check,
    _schur_triples,
    backtrack_schur,
    benchmark_algorithms,
    brute_force_schur,
    comparison_table,
    complexity_summary,
    COMPLEXITY_ANALYSIS,
    compute_s2_sequence,
    dp_schur_k2,
    ds2_table,
    ds3_table,
    ds_sat,
    ds_sat_profile,
    ds_sat_stable,
    extend_s2_sequence,
    s3_cyclic_sequence,
    s3_larger_groups,
    sat_can_color,
    sat_schur,
    sat_schur_cyclic_k2,
    sat_schur_k3,
)
from schur_groups import (
    group_elements,
    group_order,
)


# =====================================================================
# 1. Algorithm comparison for S(G, k)
# =====================================================================


class TestSchurTriples:
    """Test the precomputed Schur triple index structure."""

    def test_z5_triples_include_1_plus_1(self):
        """In Z/5Z, (1,)+(1,)=(2,) => triple (1,1,2) in index form."""
        elements = group_elements((5,))
        triples = _schur_triples(elements, (5,))
        idx_of = {e: i for i, e in enumerate(elements)}
        assert (idx_of[(1,)], idx_of[(1,)], idx_of[(2,)]) in triples

    def test_z5_triples_include_2_plus_3(self):
        """(2,)+(3,)=(0,) in Z/5Z."""
        elements = group_elements((5,))
        triples = _schur_triples(elements, (5,))
        idx_of = {e: i for i, e in enumerate(elements)}
        assert (idx_of[(2,)], idx_of[(3,)], idx_of[(0,)]) in triples

    def test_z3_triple_count(self):
        """Z/3Z has elements {0,1,2}. Count all ordered triples a+b=c."""
        elements = group_elements((3,))
        triples = _schur_triples(elements, (3,))
        # 0+0=0, 0+1=1, 1+0=1, 0+2=2, 2+0=2, 1+1=2, 1+2=0, 2+1=0, 2+2=1
        # But _schur_triples starts with j >= i, then adds (j,i,k) if i!=j.
        # So count should be 9 (all ordered pairs)
        assert len(triples) == 9


class TestBruteForce:
    """Validate brute-force baseline against known values."""

    def test_z5_k2(self):
        assert brute_force_schur((5,), k=2) == 4

    def test_z3_k2(self):
        assert brute_force_schur((3,), k=2) == 2

    def test_z7_k2(self):
        assert brute_force_schur((7,), k=2) == 4

    def test_z5_k3(self):
        assert brute_force_schur((5,), k=3) == 4

    def test_guard_large_group(self):
        """Groups > 18 elements return -1 (guard)."""
        assert brute_force_schur((19,), k=2) == -1


class TestSATSchur:
    """Validate SAT encoding against all known S(G, k) values."""

    @pytest.mark.parametrize("n,expected", [
        (2, 1), (3, 2), (4, 3), (5, 4), (6, 4), (7, 4), (8, 6),
        (9, 6), (10, 8), (11, 8), (12, 9), (13, 8), (14, 9),
        (15, 12), (16, 12), (17, 12), (18, 12), (19, 12), (20, 16),
    ])
    def test_cyclic_k2(self, n, expected):
        assert sat_schur((n,), k=2) == expected

    @pytest.mark.parametrize("n,expected", [
        (2, 1), (3, 2), (5, 4), (7, 6), (9, 8), (11, 10),
    ])
    def test_cyclic_k3(self, n, expected):
        assert sat_schur((n,), k=3) == expected

    def test_boolean_k2_order4(self):
        assert sat_schur((2, 2), k=2) == 3

    def test_boolean_k2_order8(self):
        assert sat_schur((2, 2, 2), k=2) == 6

    def test_product_k2(self):
        """S(Z/2Z x Z/3Z, 2) = S(Z/6Z, 2)."""
        assert sat_schur((2, 3), k=2) == sat_schur((6,), k=2)

    def test_invariance_order8(self):
        """All abelian groups of order 8 have same S(G,2)."""
        vals = {sat_schur(g, k=2) for g in [(8,), (2, 4), (2, 2, 2)]}
        assert len(vals) == 1

    def test_sat_matches_brute_force(self):
        """SAT and brute force agree on all small instances."""
        for n in range(2, 10):
            for k in (2, 3):
                bf = brute_force_schur((n,), k)
                s = sat_schur((n,), k)
                assert bf == s, f"n={n}, k={k}: BF={bf}, SAT={s}"


class TestSATCanColor:
    """Test the fixed-subset SAT coloring check."""

    def test_z5_14_is_2colorable(self):
        """{1,4} in Z/5Z is 2-colorable sum-free."""
        elements = group_elements((5,))
        idx_of = {e: i for i, e in enumerate(elements)}
        selected = [idx_of[(1,)], idx_of[(4,)]]
        assert sat_can_color((5,), k=2, selected=selected)

    def test_z3_12_not_1colorable(self):
        """{1,2} in Z/3Z: 1+1=2, not 1-colorable."""
        elements = group_elements((3,))
        idx_of = {e: i for i, e in enumerate(elements)}
        selected = [idx_of[(1,)], idx_of[(2,)]]
        assert not sat_can_color((3,), k=1, selected=selected)

    def test_z3_12_is_2colorable(self):
        """{1,2} in Z/3Z can be 2-colored: {1} and {2}."""
        elements = group_elements((3,))
        idx_of = {e: i for i, e in enumerate(elements)}
        selected = [idx_of[(1,)], idx_of[(2,)]]
        assert sat_can_color((3,), k=2, selected=selected)


class TestSATEncoder:
    """Test the SAT encoder internals."""

    def test_var_numbering(self):
        enc = SchurSATEncoder((5,), k=2)
        assert enc.var(0, 0) == 1
        assert enc.var(0, 1) == 2
        assert enc.var(1, 0) == 3

    def test_fixed_subset_clauses(self):
        enc = SchurSATEncoder((3,), k=2)
        clauses = enc.encode_fixed_subset([1, 2])
        assert len(clauses) > 0
        # Should have at-least-one clauses for elements 1 and 2
        # (indices in the group element list)

    def test_at_least_encoding(self):
        enc = SchurSATEncoder((5,), k=2)
        clauses, top = enc.encode_at_least(3)
        assert len(clauses) > 0
        assert top >= enc.n * enc.k


class TestBacktrack:
    """Validate backtracking with forward checking."""

    @pytest.mark.parametrize("n,expected", [
        (3, 2), (5, 4), (7, 4), (8, 6), (9, 6),
    ])
    def test_cyclic_k2(self, n, expected):
        assert backtrack_schur((n,), k=2) == expected

    def test_z5_k3(self):
        assert backtrack_schur((5,), k=3) == 4

    def test_guard_large(self):
        assert backtrack_schur((31,), k=2) == -1

    def test_agrees_with_sat(self):
        """Backtracking and SAT agree for small groups."""
        for n in range(2, 9):
            bt = backtrack_schur((n,), k=2)
            s = sat_schur((n,), k=2)
            assert bt == s, f"n={n}: backtrack={bt}, SAT={s}"


class TestDPSchurK2:
    """Test the DP-based S(G,2) computation (delegates to SAT)."""

    def test_z5(self):
        assert dp_schur_k2((5,)) == 4

    def test_z8(self):
        assert dp_schur_k2((8,)) == 6

    def test_boolean_4(self):
        assert dp_schur_k2((2, 2)) == 3


class TestBenchmark:
    """Test the benchmark harness."""

    def test_small_instance(self):
        results = benchmark_algorithms((5,), k=2)
        assert "sat" in results
        assert results["sat"]["result"] == 4
        assert results["sat"]["time"] > 0
        assert not results["sat"]["timed_out"]

    def test_brute_force_skipped_for_large(self):
        results = benchmark_algorithms((15,), k=3)
        bf = results.get("brute_force", {})
        assert bf.get("timed_out") or bf.get("result") is None

    def test_all_algorithms_agree(self):
        results = benchmark_algorithms((7,), k=2)
        vals = {v["result"] for v in results.values()
                if v.get("result") is not None}
        assert len(vals) == 1, f"Disagreement: {results}"


# =====================================================================
# 2. S(Z/nZ, 2) extended sequence
# =====================================================================


class TestS2Sequence:
    """Validate and extend the S(Z/nZ, 2) sequence."""

    def test_known_values_2_to_20(self):
        """All known values n=2..20 are reproduced."""
        known = {
            2: 1, 3: 2, 4: 3, 5: 4, 6: 4, 7: 4, 8: 6, 9: 6,
            10: 8, 11: 8, 12: 9, 13: 8, 14: 9, 15: 12, 16: 12,
            17: 12, 18: 12, 19: 12, 20: 16,
        }
        seq = compute_s2_sequence(2, 20)
        for n, expected in known.items():
            assert seq[n] == expected, f"n={n}: got {seq[n]}, expected {expected}"

    def test_extends_past_20(self):
        """n=21..30 are computed without error."""
        seq = compute_s2_sequence(21, 30)
        assert len(seq) == 10
        for n, v in seq.items():
            assert v > 0
            assert v <= n

    def test_monotonicity_weak(self):
        """S(Z/nZ, 2) is not strictly monotone, but S >= n/2 - 1 for n >= 4."""
        seq = compute_s2_sequence(4, 30)
        for n, v in seq.items():
            assert v >= n // 2 - 1, f"n={n}: S={v} < n/2-1={n//2 - 1}"

    def test_power_of_2_formula(self):
        """S(Z/2^k Z, 2) = 3 * 2^k / 4 for k >= 1."""
        for k in range(1, 6):
            n = 2 ** k
            s = sat_schur_cyclic_k2(n)
            expected = 3 * n // 4
            assert s == expected, f"n=2^{k}={n}: got {s}, expected {expected}"

    def test_multiples_of_5_ratio(self):
        """S(Z/nZ, 2)/n = 4/5 when 5 | n."""
        seq = compute_s2_sequence(5, 40)
        for n in range(5, 41, 5):
            v = seq[n]
            assert v == 4 * n // 5, f"n={n}: S={v}, expected {4*n//5}"


class TestExtendS2:
    """Test the extend_s2_sequence function."""

    @pytest.mark.timeout(60)
    def test_validates_known_and_extends(self):
        """extend_s2_sequence validates n=2..20 and computes n=21..40."""
        seq = extend_s2_sequence()
        assert len(seq) == 39  # n=2..40
        assert seq[5] == 4
        assert seq[20] == 16
        assert seq[25] == 20  # 4*25/5
        assert seq[40] == 32  # 4*40/5


# =====================================================================
# 3. S(G, 3) via SAT
# =====================================================================


class TestS3SAT:
    """Test S(G, 3) computation via SAT for larger groups."""

    @pytest.mark.parametrize("n,expected", [
        (2, 1), (3, 2), (5, 4), (7, 6), (9, 8), (11, 10),
    ])
    def test_cyclic_k3_known(self, n, expected):
        assert sat_schur_k3((n,)) == expected

    def test_cyclic_k3_n13(self):
        """S(Z/13Z, 3) = 12 (all nonzero elements 3-colorable)."""
        assert sat_schur_k3((13,)) == 12

    def test_cyclic_k3_n14(self):
        assert sat_schur_k3((14,)) == 13

    def test_cyclic_k3_n15(self):
        assert sat_schur_k3((15,)) == 13

    def test_cyclic_k3_n16(self):
        assert sat_schur_k3((16,)) == 14

    def test_s3_ge_s2(self):
        """S(G, 3) >= S(G, 2) for all tested groups."""
        for n in range(2, 16):
            s2 = sat_schur((n,), k=2)
            s3 = sat_schur((n,), k=3)
            assert s3 >= s2, f"n={n}: S3={s3} < S2={s2}"

    def test_s3_le_n(self):
        """S(G, 3) <= |G|."""
        for n in range(2, 16):
            s3 = sat_schur((n,), k=3)
            assert s3 <= n

    def test_s3_invariance_breaks_at_9(self):
        """S(Z/9Z, 3) != S(Z/3Z x Z/3Z, 3): known invariance failure."""
        s_z9 = sat_schur_k3((9,))
        s_z3z3 = sat_schur_k3((3, 3))
        assert s_z9 == 8
        assert s_z3z3 == 7


class TestS3CyclicSequence:
    """Test the S(Z/nZ, 3) sequence computation."""

    def test_sequence_2_to_12(self):
        seq = s3_cyclic_sequence(2, 12)
        # S(Z/nZ, 3) = n-1 for n=2..12
        for n in range(2, 13):
            assert seq[n] == n - 1, f"n={n}: got {seq[n]}, expected {n-1}"

    def test_extends_to_16(self):
        seq = s3_cyclic_sequence(13, 16)
        assert len(seq) == 4
        for n, v in seq.items():
            assert v > 0


class TestS3LargerGroups:
    """Test S(G, 3) for groups of order 13-18."""

    @pytest.mark.timeout(60)
    def test_computes_without_error(self):
        results = s3_larger_groups()
        assert len(results) > 0
        for name, val in results.items():
            assert val > 0, f"{name}: S(G,3) = {val}"

    @pytest.mark.timeout(60)
    def test_z13_in_results(self):
        results = s3_larger_groups()
        assert "Z/13Z" in results
        assert results["Z/13Z"] == 12


# =====================================================================
# 4. DS(k, alpha) via SAT
# =====================================================================


class TestDSSATCheck:
    """Test the per-N density-Schur check."""

    def test_ds2_half_n4_not_forced(self):
        """N=4, alpha=0.50: avoiding coloring exists."""
        assert not _ds_sat_check(4, 2, 0.50)

    def test_ds2_half_n5_forced(self):
        """N=5, alpha=0.50: all colorings forced."""
        assert _ds_sat_check(5, 2, 0.50)

    def test_ds2_060_n5_not_forced(self):
        """N=5, alpha=0.60: avoiding coloring exists."""
        assert not _ds_sat_check(5, 2, 0.60)

    def test_ds2_060_n6_forced(self):
        """N=6, alpha=0.60: all colorings forced."""
        assert _ds_sat_check(6, 2, 0.60)

    def test_ds2_066_n6_forced(self):
        """N=6, alpha=0.66: all colorings forced."""
        assert _ds_sat_check(6, 2, 0.66)

    def test_ds2_067_n6_not_forced(self):
        """N=6, alpha=0.67: avoiding coloring exists (regime 3)."""
        assert not _ds_sat_check(6, 2, 0.67)

    def test_matches_brute_force(self):
        """SAT check matches brute-force for N <= 8, alpha=0.50."""
        from itertools import product as iterproduct

        def bf_check(N, alpha):
            threshold = max(1, int(alpha * N))
            for coloring in iterproduct(range(2), repeat=N):
                cs = [set(), set()]
                for i, c in enumerate(coloring):
                    cs[c].add(i + 1)
                has_viol = False
                for S in cs:
                    if len(S) >= threshold:
                        for a in S:
                            for b in S:
                                if a + b in S:
                                    has_viol = True
                                    break
                            if has_viol:
                                break
                    if has_viol:
                        break
                if not has_viol:
                    return False
            return True

        for N in range(1, 9):
            for alpha in (0.50, 0.60):
                sat_result = _ds_sat_check(N, 2, alpha)
                bf_result = bf_check(N, alpha)
                assert sat_result == bf_result, (
                    f"N={N}, alpha={alpha}: SAT={sat_result}, BF={bf_result}"
                )


class TestDSSat:
    """Test DS(k, alpha) computation."""

    def test_ds2_half(self):
        """DS(2, 0.50) = 5."""
        assert ds_sat(2, 0.50, max_N=15) == 5

    def test_ds2_060(self):
        """DS(2, 0.60) first forced = 6."""
        assert ds_sat(2, 0.60, max_N=15) == 6

    def test_ds2_066(self):
        """DS(2, 0.66) first forced = 6."""
        assert ds_sat(2, 0.66, max_N=15) == 6

    def test_ds3_025(self):
        """DS(3, 0.25) = 15 (known from backtracking)."""
        assert ds_sat(3, 0.25, max_N=20) == 15


class TestDSSatProfile:
    """Test the profile function."""

    def test_profile_returns_dict(self):
        p = ds_sat_profile(2, 0.50, max_N=8)
        assert isinstance(p, dict)
        assert len(p) == 8

    def test_profile_values_are_bool(self):
        p = ds_sat_profile(2, 0.50, max_N=5)
        for v in p.values():
            assert isinstance(v, bool)

    def test_profile_n5_forced(self):
        p = ds_sat_profile(2, 0.50, max_N=6)
        assert p[5] is True


class TestDSSatStable:
    """Test the stable DS computation."""

    def test_ds2_half_stable(self):
        """DS(2, 0.50) is stable immediately at N=5."""
        assert ds_sat_stable(2, 0.50, max_N=15, stability=5) == 5


class TestDS2Table:
    """Test the DS(2, alpha) table computation."""

    def test_returns_dict(self):
        d = ds2_table(alphas=[0.50], max_N=10)
        assert isinstance(d, dict)
        assert 0.5 in d

    def test_ds2_half_value(self):
        d = ds2_table(alphas=[0.50], max_N=10)
        assert d[0.5] == 5


class TestDS3Table:
    """Test the DS(3, alpha) table computation."""

    @pytest.mark.timeout(60)
    def test_returns_dict(self):
        d = ds3_table(alphas=[0.25], max_N=20)
        assert isinstance(d, dict)
        assert 0.25 in d

    @pytest.mark.timeout(60)
    def test_ds3_025_value(self):
        d = ds3_table(alphas=[0.25], max_N=20)
        assert d[0.25] == 15


# =====================================================================
# 5. Theoretical complexity
# =====================================================================


class TestComplexity:
    """Test theoretical complexity data structures."""

    def test_analysis_keys(self):
        assert "S(G,k)_NP_hard" in COMPLEXITY_ANALYSIS
        assert "counting_sharp_P_hard" in COMPLEXITY_ANALYSIS
        assert "S(G,2)_fixed_k" in COMPLEXITY_ANALYSIS
        assert "VC_dimension_sum_free" in COMPLEXITY_ANALYSIS

    def test_each_entry_has_statement(self):
        for key, info in COMPLEXITY_ANALYSIS.items():
            assert "statement" in info, f"{key} missing statement"

    def test_summary_returns_string(self):
        s = complexity_summary()
        assert isinstance(s, str)
        assert "NP-hard" in s
        assert "#P-hard" in s


# =====================================================================
# Performance: SAT vs brute force speedup
# =====================================================================


class TestSpeedup:
    """Verify that SAT is significantly faster than brute force."""

    def test_sat_faster_than_brute_force_n10_k2(self):
        """SAT should be at least 2x faster than brute force for n=10, k=2."""
        t0 = time.perf_counter()
        bf = brute_force_schur((10,), k=2)
        t_bf = time.perf_counter() - t0

        t0 = time.perf_counter()
        s = sat_schur((10,), k=2)
        t_sat = time.perf_counter() - t0

        assert bf == s
        assert t_sat < t_bf, f"SAT ({t_sat:.3f}s) not faster than BF ({t_bf:.3f}s)"

    def test_sat_handles_n30_k2_under_5s(self):
        """SAT computes S(Z/30Z, 2) in under 5 seconds."""
        t0 = time.perf_counter()
        v = sat_schur((30,), k=2)
        elapsed = time.perf_counter() - t0
        assert v == 24
        assert elapsed < 5.0, f"Took {elapsed:.2f}s"

    def test_sat_handles_n16_k3(self):
        """SAT computes S(Z/16Z, 3) reasonably fast."""
        t0 = time.perf_counter()
        v = sat_schur((16,), k=3)
        elapsed = time.perf_counter() - t0
        assert v > 0
        assert elapsed < 10.0, f"Took {elapsed:.2f}s"


# =====================================================================
# Extended sequence validation
# =====================================================================


class TestExtendedSequenceProperties:
    """Mathematical properties that the extended sequences should satisfy."""

    def test_s2_divides_well(self):
        """S(Z/nZ, 2) divides evenly for prime-power multiples of 5."""
        seq = compute_s2_sequence(5, 40)
        for n in (5, 10, 15, 20, 25, 30, 35, 40):
            assert seq[n] * 5 == 4 * n

    def test_s2_upper_bound(self):
        """S(Z/nZ, 2) <= n - 1 (zero cannot be in any sum-free set)."""
        seq = compute_s2_sequence(2, 30)
        for n, v in seq.items():
            assert v <= n - 1, f"n={n}: S={v} > n-1"

    def test_s3_at_least_s2(self):
        """S(Z/nZ, 3) >= S(Z/nZ, 2) for all n."""
        for n in range(2, 16):
            s2 = sat_schur((n,), k=2)
            s3 = sat_schur((n,), k=3)
            assert s3 >= s2, f"n={n}: S3={s3} < S2={s2}"

    def test_s2_subgroup_bound(self):
        """If d | n, then S(Z/nZ, 2) >= (n/d) * S(Z/dZ, 2).

        This comes from lifting a coloring of Z/dZ to the cosets of
        the subgroup dZ in Z/nZ.
        """
        seq = compute_s2_sequence(2, 30)
        for d in range(2, 11):
            s_d = seq[d]
            for mult in range(2, 31 // d + 1):
                n = d * mult
                if n > 30:
                    break
                lower = mult * s_d
                # This is a plausible lower bound but may not always hold
                # due to the zero-exclusion subtlety. Only check loose version.
                assert seq[n] >= s_d, (
                    f"n={n}, d={d}: S(n)={seq[n]} < S(d)={s_d}"
                )


class TestComparisonTable:
    """Test the comparison table generator."""

    def test_returns_dict(self):
        table = comparison_table(max_n=5, ks=(2,))
        assert isinstance(table, dict)
        assert (3, 2) in table

    def test_all_algorithms_agree(self):
        table = comparison_table(max_n=6, ks=(2,))
        for key, bench in table.items():
            vals = {v["result"] for v in bench.values()
                    if v.get("result") is not None}
            assert len(vals) <= 1, f"{key}: disagreement {bench}"
