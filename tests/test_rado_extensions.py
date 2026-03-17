"""Tests for rado_extensions.py: Rado numbers, modular Schur,
2D Schur, multiplicative Schur, and mixed constraints."""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rado_extensions import (
    RamseySAT,
    find_rado_number,
    schur_triples,
    ap_triples,
    sum_of_three_quads,
    asymmetric_triples,
    compute_rado_numbers,
    modular_schur_triples,
    modular_schur_colorable,
    max_modular_sum_free,
    compute_modular_schur_table,
    grid_schur_triples,
    grid_schur_colorable,
    compute_2d_schur_number,
    compute_grid_schur_table,
    multiplicative_triples,
    mult_schur_colorable,
    mult_schur_witness,
    compute_mult_schur,
    mult_schur_predicted,
    mixed_triples,
    mixed_colorable,
    mixed_witness,
    compute_mixed_number,
    _can_color_mod_subset,
)


# =====================================================================
# Section 0: SAT framework
# =====================================================================

class TestRamseySAT:
    """Test the general SAT framework."""

    def test_trivial_sat(self):
        """N=1, k=2, no forbidden tuples: always satisfiable."""
        sat_solver = RamseySAT(1, 2)
        sat, _ = sat_solver.solve([])
        assert sat

    def test_trivial_unsat(self):
        """N=1, k=1, forbidden singleton (1,): unsatisfiable."""
        # Element 1 must get color 0, but (1,) is forbidden mono.
        # Actually (1,) as a 1-tuple means: element 1 in any color is forbidden.
        # With k=1, element 1 must be color 0, and (1,) forbids it.
        sat_solver = RamseySAT(1, 1)
        sat, _ = sat_solver.solve([(1,)])
        assert not sat

    def test_two_elements_two_colors(self):
        """N=2, k=2, forbid (1,2) mono: solvable by different colors."""
        sat_solver = RamseySAT(2, 2)
        sat, witness = sat_solver.solve([(1, 2)], extract_witness=True)
        assert sat
        assert witness is not None
        assert witness[1] != witness[2]

    def test_witness_extraction(self):
        """Verify witness is a valid coloring."""
        sat_solver = RamseySAT(5, 2)
        triples = schur_triples(5)
        sat, witness = sat_solver.solve(triples, extract_witness=True)
        # N=5 with Schur triples and k=2 should be UNSAT (S(2)=4)
        assert not sat
        assert witness is None

    def test_witness_valid_coloring(self):
        """When SAT, witness should assign each element exactly one color."""
        sat_solver = RamseySAT(4, 2)
        triples = schur_triples(4)
        sat, witness = sat_solver.solve(triples, extract_witness=True)
        assert sat
        assert witness is not None
        assert set(witness.keys()) == {1, 2, 3, 4}
        assert all(c in {0, 1} for c in witness.values())


# =====================================================================
# Section 1: Rado numbers for linear equations
# =====================================================================

class TestSchurTriples:
    """Test Schur triple generation."""

    def test_schur_triples_5(self):
        triples = schur_triples(5)
        assert (1, 1, 2) in triples
        assert (1, 2, 3) in triples
        assert (2, 3, 5) in triples
        assert (1, 4, 5) in triples

    def test_schur_triples_count(self):
        """Number of Schur triples in [1..N]."""
        assert len(schur_triples(4)) == 4  # (1,1,2),(1,2,3),(1,3,4),(2,2,4)
        assert len(schur_triples(1)) == 0

    def test_no_triples_above_range(self):
        triples = schur_triples(5)
        for t in triples:
            assert all(1 <= x <= 5 for x in t)


class TestAPTriples:
    """Test AP triple generation."""

    def test_ap_triples_basic(self):
        triples = ap_triples(9)
        # (1, 3, 2) is an AP: 1+3 = 2*2
        assert (1, 3, 2) in triples

    def test_ap_distinctness(self):
        """All elements in each AP triple should be distinct."""
        for t in ap_triples(20):
            assert len(set(t)) == 3


class TestSumOfThreeQuads:
    """Test a+b+c=d quadruple generation."""

    def test_basic_quad(self):
        quads = sum_of_three_quads(10)
        # 1+1+1=3
        assert (1, 1, 1, 3) in quads
        # 1+2+3=6
        assert (1, 2, 3, 6) in quads

    def test_ordering(self):
        """a <= b <= c < d in all quadruples."""
        for a, b, c, d in sum_of_three_quads(20):
            assert a <= b <= c < d


class TestAsymmetricTriples:
    """Test a+2b=3c triple generation."""

    def test_basic(self):
        triples = asymmetric_triples(20)
        # a=1, b=1: 1+2=3, c=1. But c=a, skip.
        # a=3, b=3: 3+6=9, c=3. But c=a=b, skip.
        # a=1, b=4: 1+8=9, c=3. (1,4,3) should be present.
        assert (1, 4, 3) in triples

    def test_equation_satisfied(self):
        """All triples satisfy a + 2b = 3c."""
        for a, b, c in asymmetric_triples(30):
            assert a + 2 * b == 3 * c


class TestRadoNumbers:
    """Test exact Rado number computation."""

    def test_schur_k1(self):
        """R(a+b=c, 1) = 2: can't 1-color {1}? No, {1} has no Schur triple.
        R(a+b=c, 1) = min N with forced mono triple in 1 color = 2.
        1+1=2 forces it."""
        val = find_rado_number(schur_triples, 1, lo=1, hi=10)
        assert val == 2

    def test_schur_k2(self):
        """R(a+b=c, 2) = 5 = S(2) + 1."""
        val = find_rado_number(schur_triples, 2, lo=1, hi=20)
        assert val == 5

    def test_schur_k3(self):
        """R(a+b=c, 3) = 14 = S(3) + 1."""
        val = find_rado_number(schur_triples, 3, lo=1, hi=50)
        assert val == 14

    def test_ap_k2(self):
        """R(a+b=2c, 2) = W(2;3) = 9."""
        val = find_rado_number(ap_triples, 2, lo=1, hi=20)
        assert val == 9

    def test_ap_k3(self):
        """R(a+b=2c, 3) = W(3;3) = 27."""
        val = find_rado_number(ap_triples, 3, lo=1, hi=50)
        assert val == 27

    def test_sum3_k2(self):
        """R(a+b+c=d, 2) = 11."""
        val = find_rado_number(sum_of_three_quads, 2, lo=1, hi=20)
        assert val == 11

    def test_sum3_k3(self):
        """R(a+b+c=d, 3) = 43."""
        val = find_rado_number(sum_of_three_quads, 3, lo=1, hi=80)
        assert val == 43

    def test_asymmetric_k2(self):
        """R(a+2b=3c, 2) = 13."""
        val = find_rado_number(asymmetric_triples, 2, lo=1, hi=30)
        assert val == 13

    def test_rado_monotone_in_k(self):
        """Rado numbers increase with k for each equation."""
        for fn in [schur_triples, ap_triples, sum_of_three_quads]:
            prev = 0
            for k in range(1, 4):
                val = find_rado_number(fn, k, lo=1, hi=200)
                if val > 0:
                    assert val > prev, f"Non-monotone at k={k}"
                    prev = val

    def test_compute_rado_numbers_dict(self):
        """compute_rado_numbers returns a dict with all equations."""
        result = compute_rado_numbers(max_k=2)
        assert "a+b=c (Schur)" in result
        assert "a+b=2c (AP/vdW)" in result
        assert result["a+b=c (Schur)"][2] == 5
        assert result["a+b=2c (AP/vdW)"][2] == 9


class TestRadoSatAt1:
    """Boundary tests: N just below the Rado number is always SAT."""

    def test_schur_below(self):
        sat_solver = RamseySAT(4, 2)
        sat, w = sat_solver.solve(schur_triples(4), extract_witness=True)
        assert sat
        # Verify witness: no monochromatic Schur triple
        for a, b, c in schur_triples(4):
            assert not (w[a] == w[b] == w[c])

    def test_ap_below(self):
        sat_solver = RamseySAT(8, 2)
        sat, w = sat_solver.solve(ap_triples(8), extract_witness=True)
        assert sat
        for a, b, c in ap_triples(8):
            assert not (w[a] == w[b] == w[c])


# =====================================================================
# Section 2: Modular Schur
# =====================================================================

class TestModularSchurTriples:
    """Test modular Schur triple generation."""

    def test_z5_triples(self):
        triples = modular_schur_triples(5)
        # 1+1 = 2 mod 5: (1,1,2)
        assert (1, 1, 2) in triples
        # 2+3 = 0 mod 5: NOT included (0 is excluded)
        assert all(c != 0 for _, _, c in triples)

    def test_no_zero_in_triples(self):
        """Modular Schur triples exclude element 0."""
        for p in [3, 5, 7, 11]:
            for a, b, c in modular_schur_triples(p):
                assert a > 0 and b > 0 and c > 0

    def test_modular_equation(self):
        """All triples satisfy a+b = c mod p."""
        for p in [5, 7, 11]:
            for a, b, c in modular_schur_triples(p):
                assert (a + b) % p == c


class TestModularSchurColorable:
    """Test modular Schur colorability."""

    def test_z3_k1_not_colorable(self):
        """Z/3Z has nonzero elements {1,2}. 1+1=2 mod 3.
        So {1,2} is not sum-free. Max sum-free: {1} or {2}, size 1."""
        # k=1: can we avoid Schur triple on {1,2}? No: 1+1=2.
        # Only if we exclude one element.
        assert not modular_schur_colorable(3, 1)

    def test_z5_k2_colorable(self):
        """Z/5Z nonzero elements can be 2-colored sum-free."""
        assert modular_schur_colorable(5, 2)

    def test_z5_k1_not_colorable(self):
        """Z/5Z nonzero = {1,2,3,4}. 1-coloring all 4: 1+4=0 (ok, not in set),
        but 1+1=2 in set, 2+3=0 (ok), 2+2=4 in set. Not sum-free.
        modular_schur_colorable checks if ALL nonzero elements fit in k colors."""
        assert not modular_schur_colorable(5, 1)


class TestMaxModularSumFree:
    """Test max modular sum-free subset sizes."""

    def test_z3_k1(self):
        """Max sum-free in Z/3Z nonzero = 1."""
        assert max_modular_sum_free(3, 1) == 1

    def test_z5_k1(self):
        """Max sum-free in Z/5Z nonzero = 2 (e.g., {1,4})."""
        assert max_modular_sum_free(5, 1) == 2

    def test_z7_k1(self):
        """Max sum-free in Z/7Z nonzero = 2."""
        assert max_modular_sum_free(7, 1) == 2

    def test_z11_k1(self):
        """Max sum-free in Z/11Z nonzero = 4."""
        assert max_modular_sum_free(11, 1) == 4

    def test_z5_k2(self):
        """S_mod(5, 2) = 4 = all nonzero elements."""
        assert max_modular_sum_free(5, 2) == 4

    def test_z7_k2(self):
        """S_mod(7, 2) = 4."""
        assert max_modular_sum_free(7, 2) == 4

    def test_s_mod_doubling(self):
        """Key finding: S_mod(p, 2) = 2 * S_mod(p, 1) for primes."""
        for p in [3, 5, 7, 11, 13]:
            s1 = max_modular_sum_free(p, 1)
            s2 = max_modular_sum_free(p, 2)
            assert s2 == 2 * s1, f"p={p}: S_mod(p,2)={s2} != 2*S_mod(p,1)={2*s1}"

    def test_ratio_approaches_one_third(self):
        """S_mod(p, 1) / (p-1) decreases toward 1/3."""
        prev_ratio = 1.0
        for p in [5, 7, 11, 13, 17, 19, 23, 29, 31]:
            s = max_modular_sum_free(p, 1)
            ratio = s / (p - 1)
            assert ratio >= 1 / 3 - 0.01, f"p={p}: ratio {ratio} < 1/3"
            assert ratio <= prev_ratio + 0.01  # roughly decreasing


class TestModularSchurTable:
    """Test the compute_modular_schur_table function."""

    def test_table_structure(self):
        table = compute_modular_schur_table([3, 5, 7], max_k=2)
        assert len(table) == 6  # 3 primes x 2 values of k
        for row in table:
            assert "p" in row
            assert "k" in row
            assert "S_mod" in row
            assert "ratio" in row

    def test_table_values(self):
        table = compute_modular_schur_table([5], max_k=1)
        assert len(table) == 1
        assert table[0]["S_mod"] == 2


class TestCanColorModSubset:
    """Test the internal _can_color_mod_subset function."""

    def test_zero_elements(self):
        """Selecting 0 elements is always possible."""
        triples = modular_schur_triples(5)
        assert _can_color_mod_subset(4, 0, 2, triples)

    def test_all_elements_z5(self):
        """All 4 nonzero elements of Z/5Z can be 2-colored sum-free."""
        triples = modular_schur_triples(5)
        assert _can_color_mod_subset(4, 4, 2, triples)

    def test_exceeds_max(self):
        """Cannot select more elements than exist."""
        triples = modular_schur_triples(3)
        # Z/3Z has 2 nonzero elements; asking for 3 should return False
        assert not _can_color_mod_subset(2, 3, 1, triples)

    def test_zero_elements_trivial(self):
        """Selecting 0 elements returns True without solver invocation."""
        assert _can_color_mod_subset(5, 0, 2, [])


# =====================================================================
# Section 3: Multi-dimensional Schur (2D grid)
# =====================================================================

class TestGridSchurTriples:
    """Test 2D Schur triple generation."""

    def test_2x2_triples(self):
        triples, num = grid_schur_triples(2, 2)
        assert num == 3  # (0,0) excluded, leaving (0,1), (1,0), (1,1)
        # (0,1) + (1,0) = (1,1): should produce a triple
        assert len(triples) > 0

    def test_1x1_no_triples(self):
        triples, num = grid_schur_triples(1, 1)
        assert num == 0
        assert len(triples) == 0

    def test_triple_validity(self):
        """All triples reference valid point indices."""
        triples, num = grid_schur_triples(3, 3)
        for t in triples:
            for idx in t:
                assert 1 <= idx <= num


class TestGridSchurColorable:
    """Test 2D grid colorability."""

    def test_1x5_colorable(self):
        """1x5 grid: equivalent to 1D [0..4], which is [1..4] after removing 0.
        S(2)=4, so [1..4] is 2-colorable."""
        assert grid_schur_colorable(1, 5, 2)

    def test_1x6_not_colorable(self):
        """1x6 grid: equivalent to [1..5], which forces Schur in 2 colors."""
        assert not grid_schur_colorable(1, 6, 2)

    def test_3x3_colorable(self):
        """3x3 grid is 2-colorable."""
        assert grid_schur_colorable(3, 3, 2)

    def test_4x4_not_colorable(self):
        """4x4 grid forces monochromatic {a, b, a+b}."""
        assert not grid_schur_colorable(4, 4, 2)

    def test_2x4_colorable(self):
        """2x4 grid (7 points) is 2-colorable."""
        assert grid_schur_colorable(2, 4, 2)

    def test_2x5_not_colorable(self):
        """2x5 grid (9 points) forces Schur in 2 colors."""
        assert not grid_schur_colorable(2, 5, 2)

    def test_3x4_not_colorable(self):
        """3x4 grid forces Schur."""
        assert not grid_schur_colorable(3, 4, 2)


class TestCompute2DSchur:
    """Test 2D Schur number computation."""

    def test_2d_schur_k2(self):
        """2D Schur number for k=2 is 4."""
        assert compute_2d_schur_number(k=2) == 4

    def test_2d_schur_k1(self):
        """With 1 color, 2D Schur number should be small."""
        val = compute_2d_schur_number(k=1, max_side=10)
        assert val >= 2  # At least 2x2 forces it with 1 color

    def test_not_found(self):
        """Returns -1 if max_side is too small."""
        # k=3 with max_side=3 won't force it
        val = compute_2d_schur_number(k=3, max_side=3)
        assert val == -1


class TestGridSchurTable:
    """Test grid Schur table computation."""

    def test_table_nonempty(self):
        table = compute_grid_schur_table(max_m=3, max_n=3, k=2)
        assert len(table) > 0

    def test_table_structure(self):
        table = compute_grid_schur_table(max_m=2, max_n=3, k=2)
        for row in table:
            assert "m" in row
            assert "n" in row
            assert "points" in row
            assert "colorable" in row
            assert isinstance(row["colorable"], bool)

    def test_table_includes_1x1(self):
        """1x1 grid has 0 points (origin excluded), always colorable."""
        table = compute_grid_schur_table(max_m=1, max_n=1, k=2)
        assert len(table) == 1
        assert table[0]["colorable"] is True


# =====================================================================
# Section 4: Multiplicative Schur
# =====================================================================

class TestMultiplicativeTriples:
    """Test multiplicative triple generation."""

    def test_basic_triples(self):
        triples = multiplicative_triples(10)
        # 2*2=4: should produce (1, 1, 3) in 1-indexed (2->1, 4->3)
        assert (1, 1, 3) in triples
        # 2*3=6: (1, 2, 5) in 1-indexed (2->1, 3->2, 6->5)
        assert (1, 2, 5) in triples

    def test_no_triples_below_4(self):
        """[2..3] has no multiplicative triple (2*2=4 > 3)."""
        assert multiplicative_triples(3) == []

    def test_product_in_range(self):
        """All products a*b should be <= N."""
        N = 20
        triples = multiplicative_triples(N)
        elems = list(range(2, N + 1))
        for ai, bi, ci in triples:
            a, b, c = elems[ai - 1], elems[bi - 1], elems[ci - 1]
            assert a * b == c


class TestMultSchurColorable:
    """Test multiplicative Schur colorability."""

    def test_ms1_below(self):
        """[2..3] has no multiplicative triple, so 1-colorable."""
        assert mult_schur_colorable(3, 1)

    def test_ms1_at_boundary(self):
        """[2..3] is 1-colorable (MS(1) = 3)."""
        assert mult_schur_colorable(3, 1)

    def test_ms1_above(self):
        """[2..4]: 2*2=4 forces mono triple in 1 color."""
        assert not mult_schur_colorable(4, 1)

    def test_ms2_at_boundary(self):
        """[2..31] is 2-colorable (MS(2) = 31)."""
        assert mult_schur_colorable(31, 2)

    def test_ms2_above(self):
        """[2..32] forces mono multiplicative triple in 2 colors."""
        assert not mult_schur_colorable(32, 2)

    def test_ms3_at_boundary(self):
        """[2..16383] is 3-colorable (MS(3) = 16383)."""
        assert mult_schur_colorable(16383, 3)

    @pytest.mark.timeout(300)
    def test_ms3_above(self):
        """[2..16384] forces mono multiplicative triple in 3 colors."""
        assert not mult_schur_colorable(16384, 3)

    def test_n1_trivially_colorable(self):
        """N=1: [2..1] is empty, trivially colorable."""
        assert mult_schur_colorable(1, 1)

    def test_n2_single_element(self):
        """N=2: [2..2] = {2}, always colorable."""
        assert mult_schur_colorable(2, 1)


class TestMultSchurWitness:
    """Test witness extraction for multiplicative Schur."""

    def test_witness_ms2(self):
        """Witness for [2..31] with 2 colors should be valid."""
        w = mult_schur_witness(31, 2)
        assert w is not None
        assert set(w.keys()) == set(range(2, 32))
        # Verify: no mono {a, b, ab}
        for a in range(2, 32):
            for b in range(a, 32):
                c = a * b
                if c <= 31:
                    assert not (w[a] == w[b] == w[c]), (
                        f"Mono triple: {a}*{b}={c}, all color {w[a]}")

    def test_witness_unsat(self):
        """No witness when UNSAT (N = MS(2) + 1 = 32)."""
        assert mult_schur_witness(32, 2) is None

    def test_witness_empty(self):
        """N=1: empty witness."""
        w = mult_schur_witness(1, 2)
        assert w == {}


class TestMultSchurFormula:
    """Test the discovered formula MS(k) = 2^((3^k + 1) / 2) - 1."""

    def test_ms1_formula(self):
        """MS(1) = 2^2 - 1 = 3."""
        assert mult_schur_predicted(1) == 3

    def test_ms2_formula(self):
        """MS(2) = 2^5 - 1 = 31."""
        assert mult_schur_predicted(2) == 31

    def test_ms3_formula(self):
        """MS(3) = 2^14 - 1 = 16383."""
        assert mult_schur_predicted(3) == 16383

    def test_exponent_recurrence(self):
        """Exponents satisfy f(k) = 3*f(k-1) - 1 with f(1) = 2."""
        f = [0, 2]  # f[0] unused, f[1] = 2
        for k in range(2, 5):
            f.append(3 * f[-1] - 1)
        assert f[1:4] == [2, 5, 14]

    def test_exponent_closed_form(self):
        """f(k) = (3^k + 1) / 2."""
        for k in range(1, 6):
            assert (3 ** k + 1) // 2 == (3 ** k + 1) / 2  # integer
            # Check the formula produces correct MS values for k=1,2,3
            if k <= 3:
                expected = {1: 3, 2: 31, 3: 16383}[k]
                assert 2 ** ((3 ** k + 1) // 2) - 1 == expected

    def test_ms4_prediction(self):
        """MS(4) predicted = 2^41 - 1 (too large to compute, just check formula)."""
        assert mult_schur_predicted(4) == 2 ** 41 - 1


class TestComputeMultSchur:
    """Test the compute_mult_schur function."""

    def test_ms1(self):
        assert compute_mult_schur(1, max_N=100) == 3

    def test_ms2(self):
        assert compute_mult_schur(2, max_N=100) == 31

    def test_ms1_equals_predicted(self):
        """compute_mult_schur(1) matches the formula prediction."""
        assert compute_mult_schur(1, max_N=100) == mult_schur_predicted(1)

    def test_ms2_equals_predicted(self):
        """compute_mult_schur(2) matches the formula prediction."""
        assert compute_mult_schur(2, max_N=100) == mult_schur_predicted(2)


# =====================================================================
# Section 5: Mixed additive-multiplicative
# =====================================================================

class TestMixedTriples:
    """Test mixed triple generation."""

    def test_includes_additive(self):
        """Mixed triples include additive Schur triples."""
        triples = mixed_triples(5)
        assert (1, 1, 2) in triples  # 1+1=2

    def test_includes_multiplicative(self):
        """Mixed triples include multiplicative triples."""
        triples = mixed_triples(10)
        assert (2, 2, 4) in triples  # 2*2=4

    def test_both_constraints(self):
        """Mixed triples for N=4 include both 1+1=2 and 2*2=4."""
        triples = mixed_triples(4)
        assert (1, 1, 2) in triples
        assert (2, 2, 4) in triples


class TestMixedColorable:
    """Test mixed constraint colorability."""

    def test_mixed_1_not_colorable_at_2(self):
        """1+1=2 forces in 1 color at N=2."""
        assert not mixed_colorable(2, 1)

    def test_mixed_1_colorable_at_1(self):
        """[1] has no triple, 1-colorable."""
        assert mixed_colorable(1, 1)

    def test_mixed_2_colorable_at_4(self):
        """[1..4] is 2-colorable under mixed constraints."""
        assert mixed_colorable(4, 2)

    def test_mixed_2_not_colorable_at_5(self):
        """[1..5] forces in 2 colors (same as Schur)."""
        assert not mixed_colorable(5, 2)


class TestMixedWitness:
    """Test mixed witness extraction."""

    def test_witness_at_4(self):
        """Valid 2-coloring of [1..4] avoiding mixed triples."""
        w = mixed_witness(4, 2)
        assert w is not None
        # Check additive
        for a in range(1, 5):
            for b in range(a, 5):
                c = a + b
                if c <= 4:
                    assert not (w[a] == w[b] == w[c])
        # Check multiplicative
        for a in range(2, 5):
            for b in range(a, 5):
                c = a * b
                if c <= 4:
                    assert not (w[a] == w[b] == w[c])


class TestMixedEquals:
    """Test that mixed numbers equal Schur numbers."""

    def test_mixed_equals_schur_k1(self):
        """Mixed(1) = S(1) + 1 = 2."""
        assert compute_mixed_number(1) == 2

    def test_mixed_equals_schur_k2(self):
        """Mixed(2) = S(2) + 1 = 5."""
        assert compute_mixed_number(2) == 5

    def test_mixed_equals_schur_k3(self):
        """Mixed(3) = S(3) + 1 = 14."""
        assert compute_mixed_number(3, max_N=50) == 14

    def test_additive_dominates(self):
        """For each k, Mixed(k) = Schur(k)+1, showing additive dominates."""
        schur_plus_1 = {1: 2, 2: 5, 3: 14}
        for k, expected in schur_plus_1.items():
            assert compute_mixed_number(k, max_N=50) == expected


# =====================================================================
# Section 6: Cross-cutting properties
# =====================================================================

class TestRadoMonotonicity:
    """Rado numbers are monotone in k and in equation complexity."""

    def test_schur_vs_ap(self):
        """R(AP, k) > R(Schur, k): AP is harder to force."""
        for k in [2, 3]:
            r_schur = find_rado_number(schur_triples, k, hi=200)
            r_ap = find_rado_number(ap_triples, k, hi=200)
            assert r_ap > r_schur

    def test_schur_vs_sum3(self):
        """R(a+b+c=d, k) > R(a+b=c, k): longer equation is harder."""
        for k in [2, 3]:
            r_schur = find_rado_number(schur_triples, k, hi=200)
            r_sum3 = find_rado_number(sum_of_three_quads, k, hi=200)
            assert r_sum3 > r_schur

    def test_multiplicative_vs_additive(self):
        """MS(k) > S(k)+1 for k >= 1: multiplicative is much looser."""
        schur_vals = {1: 2, 2: 5, 3: 14}
        ms_vals = {1: 3, 2: 31, 3: 16383}
        for k in [1, 2, 3]:
            assert ms_vals[k] > schur_vals[k]


class TestRado_1DReduction:
    """The 1D case of the 2D Schur matches the standard Schur number."""

    def test_1d_equivalent_to_schur(self):
        """1xN grid is equivalent to coloring [1..N-1] (excluding origin).
        This should match Schur: 1x5 colorable (4 pts), 1x6 not (5 pts)."""
        assert grid_schur_colorable(1, 5, 2)   # 4 points
        assert not grid_schur_colorable(1, 6, 2)  # 5 points


class TestFindRadoNotFound:
    """Test find_rado_number when the number exceeds the search range."""

    def test_not_found_returns_negative(self):
        """If Rado number exceeds hi and doubling still fails, return -1."""
        # Use a trivially satisfiable equation (no forbidden patterns)
        def no_triples(N):
            return []
        val = find_rado_number(no_triples, 2, lo=1, hi=50)
        assert val == -1


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_triples(self):
        """N=1 with Schur triples: no triples, SAT."""
        assert len(schur_triples(1)) == 0
        sat_solver = RamseySAT(1, 2)
        sat, _ = sat_solver.solve(schur_triples(1))
        assert sat

    def test_mult_schur_large_k_small_N(self):
        """With many colors and few elements, always colorable."""
        assert mult_schur_colorable(10, 10)

    def test_grid_1x1(self):
        """1x1 grid has 0 points, trivially colorable."""
        assert grid_schur_colorable(1, 1, 2)

    def test_modular_z2(self):
        """Z/2Z: only nonzero element is 1. 1+1=0 mod 2, not a nonzero triple.
        So {1} is trivially sum-free."""
        assert modular_schur_colorable(2, 1)

    @pytest.mark.timeout(600)
    def test_schur_s4(self):
        """S(4) = 44, so R(Schur, 4) = 45.
        Verify at the boundary only (full search is slow)."""
        # N=44 should be SAT (S(4)=44)
        sat44 = RamseySAT(44, 4)
        result44, _ = sat44.solve(schur_triples(44))
        assert result44, "S(4) >= 44: [1..44] should be 4-colorable"
        # N=45 should be UNSAT
        sat45 = RamseySAT(45, 4)
        result45, _ = sat45.solve(schur_triples(45))
        assert not result45, "S(4)+1 = 45: [1..45] should force Schur in 4 colors"


# =====================================================================
# Additional coverage tests
# =====================================================================

class TestModularSchurDefaultPrimes:
    """Cover the default primes parameter in compute_modular_schur_table."""

    def test_default_primes(self):
        """When no primes specified, uses [3,5,7,...,31]."""
        table = compute_modular_schur_table(max_k=1)
        primes = {row["p"] for row in table}
        assert 3 in primes
        assert 31 in primes
        assert len(table) == 10  # 10 default primes x 1 k-value


class TestGridLargeSkipped:
    """Cover the grid table skipping logic for large grids."""

    def test_large_grid_skipped(self):
        """Grids with > 100 points are skipped."""
        table = compute_grid_schur_table(max_m=15, max_n=15, k=2)
        for row in table:
            assert row["points"] <= 100


class TestComputeMultSchurEdge:
    """Cover edge cases in compute_mult_schur."""

    def test_compute_ms1_with_large_max(self):
        """compute_mult_schur(1) works with generous max_N."""
        assert compute_mult_schur(1, max_N=100) == 3


class TestMixedNotFound:
    """Cover the -1 return from compute_mixed_number."""

    def test_mixed_not_found_tiny_range(self):
        """With max_N=1 and k=2, mixed is colorable => returns -1."""
        # [1] has no Schur triple, so k=2 can color it.
        val = compute_mixed_number(2, max_N=1)
        assert val == -1


class TestMultSchurWitnessVerification:
    """Additional witness tests for multiplicative Schur."""

    def test_witness_ms1(self):
        """Witness for [2..3] with 1 color."""
        w = mult_schur_witness(3, 1)
        assert w is not None
        assert w[2] == w[3]  # only 1 color
        # No multiplicative triple in [2..3]

    def test_witness_colors_valid(self):
        """All color values in witness are in [0, k-1]."""
        w = mult_schur_witness(20, 2)
        assert w is not None
        for c in w.values():
            assert c in {0, 1}
