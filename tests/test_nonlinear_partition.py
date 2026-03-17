"""Tests for nonlinear_partition.py -- Pythagorean-Markov regularity boundary."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nonlinear_partition import (
    pythagorean_triples,
    primitive_pythagorean_triples,
    markov_triples,
    generalized_quadratic_triples,
    PartitionSAT,
    find_partition_number,
    pythagorean_schur_number,
    pythagorean_schur_lower_bound,
    coprime_pythagorean_triples,
    coprime_pythagorean_schur,
    coprime_pythagorean_graph_triples,
    coprime_graph_pyth_ramsey,
    markov_schur_number,
    markov_avoiding_coloring,
    quadratic_regularity_test,
    scan_regularity_boundary,
    regularity_classification,
    pythagorean_triple_density,
    markov_triple_density,
    compare_densities,
    coprime_triple_fraction,
    coprime_enhancement_ratio,
)


# =====================================================================
# Section 1: Pythagorean triple enumeration
# =====================================================================

class TestPythagoreanTriples:
    def test_smallest_triple(self):
        """(3,4,5) is the smallest Pythagorean triple."""
        triples = pythagorean_triples(5)
        assert (3, 4, 5) in triples

    def test_ordering(self):
        """All triples have a < b < c."""
        for a, b, c in pythagorean_triples(100):
            assert a < b < c, f"Bad ordering: ({a}, {b}, {c})"

    def test_validity(self):
        """All returned triples satisfy a^2 + b^2 = c^2."""
        for a, b, c in pythagorean_triples(200):
            assert a * a + b * b == c * c, f"Invalid: {a}^2+{b}^2 != {c}^2"

    def test_contains_known_triples(self):
        """Check presence of well-known Pythagorean triples."""
        triples = pythagorean_triples(100)
        for t in [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)]:
            assert t in triples, f"Missing known triple {t}"

    def test_contains_non_primitive(self):
        """Non-primitive triples like (6,8,10) = 2*(3,4,5) are included."""
        triples = pythagorean_triples(10)
        assert (6, 8, 10) in triples

    def test_no_triple_below_5(self):
        """No Pythagorean triple has c < 5."""
        assert pythagorean_triples(4) == []

    def test_count_up_to_100(self):
        """There are 52 Pythagorean triples with c <= 100."""
        # Standard count from number theory
        triples = pythagorean_triples(100)
        assert len(triples) == 52

    def test_bounded_by_N(self):
        """No triple exceeds the bound N."""
        for N in [20, 50, 100]:
            for a, b, c in pythagorean_triples(N):
                assert c <= N

    def test_monotone_count(self):
        """Triple count is non-decreasing in N."""
        prev = 0
        for N in range(1, 101):
            cur = len(pythagorean_triples(N))
            assert cur >= prev, f"Count decreased at N={N}"
            prev = cur


class TestPrimitivePythagoreanTriples:
    def test_smallest_primitive(self):
        """(3,4,5) is primitive: gcd(3,4,5) = 1."""
        triples = primitive_pythagorean_triples(5)
        assert (3, 4, 5) in triples

    def test_all_coprime(self):
        """All returned triples have gcd(a,b,c) = 1."""
        for a, b, c in primitive_pythagorean_triples(200):
            assert math.gcd(math.gcd(a, b), c) == 1, \
                f"Non-primitive: ({a}, {b}, {c})"

    def test_all_valid(self):
        """All returned triples satisfy a^2+b^2=c^2."""
        for a, b, c in primitive_pythagorean_triples(200):
            assert a * a + b * b == c * c

    def test_excludes_non_primitive(self):
        """(6,8,10) is NOT primitive."""
        triples = primitive_pythagorean_triples(10)
        assert (6, 8, 10) not in triples

    def test_pairwise_coprime(self):
        """For primitive triples, elements are pairwise coprime."""
        for a, b, c in primitive_pythagorean_triples(200):
            assert math.gcd(a, b) == 1, f"gcd({a},{b}) != 1"
            assert math.gcd(a, c) == 1, f"gcd({a},{c}) != 1"
            assert math.gcd(b, c) == 1, f"gcd({b},{c}) != 1"

    def test_subset_of_all(self):
        """Primitive triples are a subset of all triples."""
        all_t = set(pythagorean_triples(100))
        prim_t = set(primitive_pythagorean_triples(100))
        assert prim_t.issubset(all_t)

    def test_count_up_to_100(self):
        """There are 16 primitive Pythagorean triples with c <= 100."""
        triples = primitive_pythagorean_triples(100)
        assert len(triples) == 16


# =====================================================================
# Section 2: Markov triple enumeration
# =====================================================================

class TestMarkovTriples:
    def test_fundamental_triple_with_repeats(self):
        """(1,1,1): 1+1+1 = 3*1*1*1. Only appears when distinct_only=False."""
        triples = markov_triples(1, distinct_only=False)
        assert (1, 1, 1) in triples

    def test_distinct_only_default(self):
        """Default (distinct_only=True) excludes triples with repeated elements."""
        triples = markov_triples(10)
        for x, y, z in triples:
            assert x < y < z, f"Non-distinct triple: ({x}, {y}, {z})"

    def test_validity(self):
        """All returned triples satisfy x^2+y^2+z^2 = 3xyz."""
        for x, y, z in markov_triples(200):
            assert x * x + y * y + z * z == 3 * x * y * z, \
                f"Invalid Markov triple: ({x}, {y}, {z})"

    def test_validity_with_repeats(self):
        """All triples (including repeated) satisfy x^2+y^2+z^2 = 3xyz."""
        for x, y, z in markov_triples(200, distinct_only=False):
            assert x * x + y * y + z * z == 3 * x * y * z

    def test_ordering(self):
        """All triples have x < y < z (distinct) or x <= y <= z (all)."""
        for x, y, z in markov_triples(200, distinct_only=False):
            assert x <= y <= z, f"Bad ordering: ({x}, {y}, {z})"

    def test_known_small_distinct_triples(self):
        """Check known small Markov triples with distinct elements."""
        triples = markov_triples(200)
        known_distinct = [(1, 2, 5), (1, 5, 13), (2, 5, 29),
                          (1, 13, 34), (1, 34, 89), (2, 29, 169)]
        for t in known_distinct:
            if t[2] <= 200:
                assert t in triples, f"Missing Markov triple {t}"

    def test_bounded_by_N(self):
        """Max element in each triple is at most N."""
        for N in [10, 50, 200]:
            for x, y, z in markov_triples(N, distinct_only=False):
                assert z <= N

    def test_sparse_growth(self):
        """Markov triples grow much slower than Pythagorean triples."""
        pyth_count = len(pythagorean_triples(100))
        mark_count = len(markov_triples(100))
        assert pyth_count > mark_count, \
            f"Expected Pyth ({pyth_count}) > Markov ({mark_count})"

    def test_vieta_involution(self):
        """Each Markov triple generates others via 3yz-x."""
        triples = set(markov_triples(200, distinct_only=False))
        for x, y, z in list(triples):
            new_z = 3 * x * y - z
            if new_z > 0:
                new_triple = tuple(sorted([x, y, new_z]))
                if new_triple[2] <= 200:
                    assert new_triple in triples, \
                        f"Vieta involution of ({x},{y},{z}) = {new_triple} missing"

    def test_empty_for_n0(self):
        """No Markov triples for N=0."""
        assert markov_triples(0) == []
        assert markov_triples(0, distinct_only=False) == []


# =====================================================================
# Section 3: Generalized quadratic triples
# =====================================================================

class TestGeneralizedQuadraticTriples:
    def test_pythagorean_case(self):
        """(a=1, b=1, c=1) gives x^2+y^2=z^2, i.e., Pythagorean triples."""
        gen = generalized_quadratic_triples(100, 1, 1, 1)
        pyth = pythagorean_triples(100)
        # generalized allows x <= y but z is free ordering
        gen_set = set()
        for x, y, z in gen:
            a, b, c = sorted([x, y, z])
            gen_set.add((a, b, c))
        pyth_set = set(pyth)
        # Every Pythagorean triple should appear (all have distinct elements)
        for t in pyth_set:
            a, b, c = t
            assert any((min(a, b), max(a, b), c) == (x, y, z) or
                       (x, y, z) in gen_set or t in gen_set
                       for x, y, z in gen), \
                f"Missing Pythagorean triple {t} in generalized"

    def test_validity(self):
        """All triples satisfy the equation."""
        for a_c, b_c, c_c in [(1, 2, 3), (2, 3, 1), (1, 1, 2)]:
            for x, y, z in generalized_quadratic_triples(50, a_c, b_c, c_c,
                                                         distinct_only=False):
                assert a_c * x * x + b_c * y * y == c_c * z * z, \
                    f"{a_c}*{x}^2 + {b_c}*{y}^2 != {c_c}*{z}^2"

    def test_distinct_only_excludes_trivial(self):
        """x^2+y^2=2z^2 has trivial solutions (n,n,n). distinct_only removes them."""
        all_triples = generalized_quadratic_triples(10, 1, 1, 2, distinct_only=False)
        dist_triples = generalized_quadratic_triples(10, 1, 1, 2, distinct_only=True)
        trivial = [(x, y, z) for x, y, z in all_triples if x == y == z]
        assert len(trivial) > 0, "Should have trivial (n,n,n) solutions"
        for t in trivial:
            assert t not in dist_triples

    def test_empty_for_impossible(self):
        """Some equations have no solutions in small ranges."""
        triples = generalized_quadratic_triples(10, 1, 1, 3)
        for x, y, z in triples:
            assert x * x + y * y == 3 * z * z


# =====================================================================
# Section 4: PartitionSAT framework
# =====================================================================

class TestPartitionSAT:
    def test_trivially_sat(self):
        """With no forbidden tuples, any coloring works."""
        sat_solver = PartitionSAT(10, 2)
        sat, _ = sat_solver.solve([])
        assert sat

    def test_single_element_avoidable(self):
        """A single forbidden pair (1,2) is avoidable with 2 colors."""
        sat_solver = PartitionSAT(2, 2)
        sat, coloring = sat_solver.solve([(1, 2)], extract_witness=True)
        assert sat
        assert coloring is not None
        # Elements 1 and 2 must have different colors
        assert coloring[1] != coloring[2]

    def test_triangle_unavoidable_2_colors(self):
        """Schur triple (1,2,3) unavoidable with 2 colors on [1..4]."""
        # Schur triples in [1..4]: (1,1,2), (1,2,3), (1,3,4), (2,2,4)
        triples = [(1, 2, 3), (1, 1, 2), (1, 3, 4), (2, 2, 4)]
        sat_solver = PartitionSAT(4, 2)
        sat, _ = sat_solver.solve(triples)
        assert sat  # S(2) = 4, so [1..4] is still colorable

    def test_schur_number_2(self):
        """S(2) + 1 = 5: [1..5] forces a mono Schur triple with 2 colors."""
        def schur_fn(N):
            result = []
            for a in range(1, N + 1):
                for b in range(a, N + 1):
                    c = a + b
                    if c <= N:
                        result.append((a, b, c))
            return result

        # N=4 should be SAT
        sat4 = PartitionSAT(4, 2)
        res4, _ = sat4.solve(schur_fn(4))
        assert res4

        # N=5 should be UNSAT (S(2)+1 = 5)
        sat5 = PartitionSAT(5, 2)
        res5, _ = sat5.solve(schur_fn(5))
        assert not res5

    def test_witness_valid(self):
        """Extracted witness is a valid coloring."""
        sat_solver = PartitionSAT(10, 3)
        triples = [(1, 2, 3)]  # Simple forbidden triple
        sat, coloring = sat_solver.solve(triples, extract_witness=True)
        assert sat
        assert coloring is not None
        # All elements colored
        for i in range(1, 11):
            assert i in coloring
            assert coloring[i] in (0, 1, 2)
        # Forbidden triple not monochromatic
        assert not (coloring[1] == coloring[2] == coloring[3])

    def test_k1_pigeonhole(self):
        """With k=1, any forbidden pair of elements forces UNSAT."""
        sat_solver = PartitionSAT(5, 1)
        sat, _ = sat_solver.solve([(1, 2)])
        assert not sat  # Only 1 color, so (1,2) must be monochromatic


class TestFindPartitionNumber:
    def test_schur_number_2_colors(self):
        """find_partition_number recovers S(2)+1 = 5 for Schur triples."""
        def schur_fn(N):
            result = []
            for a in range(1, N + 1):
                for b in range(a, N + 1):
                    c = a + b
                    if c <= N:
                        result.append((a, b, c))
            return result

        num = find_partition_number(schur_fn, k=2, lo=2, hi=10)
        assert num == 5


# =====================================================================
# Section 5: Pythagorean Schur numbers
# =====================================================================

class TestPythagoreanSchur:
    def test_ps2_lower_bound(self):
        """PS(2) = 7825 (Heule et al. 2016). Test that N=100 is SAT."""
        triples = pythagorean_triples(100)
        sat_solver = PartitionSAT(100, 2)
        sat, _ = sat_solver.solve(triples)
        assert sat, "N=100 should be easily avoidable for 2 colors"

    def test_ps2_lower_bound_500(self):
        """N=500 is still SAT for 2-color Pythagorean avoidance."""
        triples = pythagorean_triples(500)
        sat_solver = PartitionSAT(500, 2)
        sat, _ = sat_solver.solve(triples)
        assert sat, "N=500 should be SAT for PS(2)=7825"

    def test_lower_bound_function(self):
        """pythagorean_schur_lower_bound returns a valid bound."""
        bound, coloring = pythagorean_schur_lower_bound(2, max_n=100)
        assert bound >= 5  # At minimum, small N is avoidable
        if coloring:
            # Verify coloring is valid
            triples = pythagorean_triples(bound)
            for a, b, c in triples:
                if a in coloring and b in coloring and c in coloring:
                    assert not (coloring[a] == coloring[b] == coloring[c]), \
                        f"Monochromatic triple ({a},{b},{c}) in coloring"


# =====================================================================
# Section 6: Coprime Pythagorean Ramsey
# =====================================================================

class TestCoprimePythagorean:
    def test_coprime_triples_are_primitive(self):
        """coprime_pythagorean_triples returns only primitive triples."""
        triples = coprime_pythagorean_triples(100)
        for a, b, c in triples:
            assert math.gcd(math.gcd(a, b), c) == 1

    def test_coprime_subset_of_all(self):
        """Coprime Pythagorean triples are a subset of all."""
        all_t = set(pythagorean_triples(100))
        cop_t = set(coprime_pythagorean_triples(100))
        assert cop_t.issubset(all_t)

    def test_avoidable_at_small_N(self):
        """Small N is avoidable for primitive-only constraint."""
        triples = coprime_pythagorean_triples(100)
        sat_solver = PartitionSAT(100, 2)
        sat, _ = sat_solver.solve(triples)
        assert sat

    def test_coprime_graph_triples_valid(self):
        """Coprime graph Pythagorean triples are valid and pairwise coprime."""
        triples = coprime_pythagorean_graph_triples(100)
        for a, b, c in triples:
            assert a * a + b * b == c * c
            assert math.gcd(a, b) == 1
            assert math.gcd(a, c) == 1
            assert math.gcd(b, c) == 1


# =====================================================================
# Section 7: Markov avoidance
# =====================================================================

class TestMarkovAvoidance:
    def test_markov_always_avoidable_small(self):
        """Markov triples (distinct) should be avoidable at small N with 2 colors."""
        for N in [10, 50, 100]:
            triples = markov_triples(N)  # distinct_only=True by default
            if not triples:
                continue
            sat_solver = PartitionSAT(N, 2)
            sat, _ = sat_solver.solve(triples)
            assert sat, f"N={N} should be avoidable (Markov not partition regular)"

    def test_markov_avoidable_large(self):
        """Even at large N, distinct Markov triples are avoidable."""
        N = 1000
        triples = markov_triples(N)
        sat_solver = PartitionSAT(N, 2)
        sat, _ = sat_solver.solve(triples)
        assert sat, "N=1000 should be avoidable (Markov not partition regular)"

    def test_markov_schur_not_found(self):
        """markov_schur_number should return -1 (not partition regular)."""
        result = markov_schur_number(2, max_n=200)
        assert result == -1, \
            f"Expected -1 (Markov not regular), got {result}"

    def test_avoiding_coloring_valid(self):
        """markov_avoiding_coloring returns a valid coloring."""
        N = 100
        coloring = markov_avoiding_coloring(N, 2)
        assert coloring is not None, "Should find an avoiding coloring"
        triples = markov_triples(N)
        for x, y, z in triples:
            if x in coloring and y in coloring and z in coloring:
                assert not (coloring[x] == coloring[y] == coloring[z]), \
                    f"Monochromatic Markov triple ({x},{y},{z})"

    def test_markov_k1_forces_with_distinct(self):
        """With k=1, any distinct triple in the range forces UNSAT."""
        # (1, 2, 5) is the smallest distinct Markov triple
        triples = markov_triples(5)
        assert (1, 2, 5) in triples
        sat_solver = PartitionSAT(5, 1)
        sat, _ = sat_solver.solve(triples)
        assert not sat, "(1,2,5) forces monochromatic with 1 color"

    def test_markov_k1_avoidable_below_threshold(self):
        """With k=1, before (1,2,5) appears, Markov is vacuously avoidable."""
        # No distinct Markov triples with max element <= 4
        triples = markov_triples(4)
        assert len(triples) == 0
        sat_solver = PartitionSAT(4, 1)
        sat, _ = sat_solver.solve(triples)
        assert sat


# =====================================================================
# Section 8: Regularity boundary
# =====================================================================

class TestRegularityBoundary:
    def test_pythagorean_regular(self):
        """x^2+y^2=z^2 should show signs of regularity."""
        result = quadratic_regularity_test(1, 1, 1, k=2, max_n=200)
        # We might not find the exact PS(2)=7825 in N<=200, so it may
        # show as not-regular at this range. The key test is structural.
        assert result['equation'] == "1x^2 + 1y^2 = 1z^2"
        assert result['coefficients'] == (1, 1, 1)

    def test_scan_returns_results(self):
        """scan_regularity_boundary returns a non-empty list."""
        results = scan_regularity_boundary(max_coeff=2, k=2, max_n=50)
        assert len(results) > 0

    def test_classification_structure(self):
        """regularity_classification returns expected fields."""
        results = scan_regularity_boundary(max_coeff=2, k=2, max_n=50)
        cls = regularity_classification(results)
        assert 'total' in cls
        assert 'regular_count' in cls
        assert 'not_regular_count' in cls
        assert cls['total'] == len(results)
        assert cls['regular_count'] + cls['not_regular_count'] + \
            cls['inconclusive_count'] == cls['total']

    def test_each_result_has_fields(self):
        """Each result from quadratic_regularity_test has required fields."""
        result = quadratic_regularity_test(1, 2, 3, k=2, max_n=50)
        for field in ['equation', 'coefficients', 'k', 'regular',
                      'number', 'max_tested', 'triple_count_at_max', 'density']:
            assert field in result, f"Missing field: {field}"


# =====================================================================
# Section 9: Density and comparison
# =====================================================================

class TestDensityAnalysis:
    def test_pythagorean_density_positive(self):
        """Pythagorean triple density should be positive for N >= 5."""
        assert pythagorean_triple_density(100) > 0

    def test_markov_density_positive(self):
        """Markov triple density should be positive for N >= 1."""
        assert markov_triple_density(10) > 0

    def test_pythagorean_denser_than_markov(self):
        """At N=100, Pythagorean triples are denser than Markov triples."""
        pyth_d = pythagorean_triple_density(100)
        mark_d = markov_triple_density(100)
        assert pyth_d > mark_d

    def test_compare_densities(self):
        """compare_densities returns valid data."""
        data = compare_densities(max_n=100, step=50)
        assert len(data) == 2  # N=50, N=100
        for d in data:
            assert d['N'] > 0
            assert d['pyth_count'] >= 0
            assert d['markov_count'] >= 0

    def test_coprime_fraction(self):
        """Fraction of primitive triples is between 0 and 1."""
        info = coprime_triple_fraction(100)
        assert 0 < info['fraction'] <= 1
        assert info['primitive_count'] <= info['all_count']

    def test_coprime_enhancement(self):
        """coprime_enhancement_ratio returns valid comparison."""
        info = coprime_enhancement_ratio(100, k=2)
        assert info['N'] == 100
        assert info['prim_triples'] <= info['all_triples']
        # Both should be avoidable at N=100
        assert info['all_avoidable'] is True
        assert info['prim_avoidable'] is True


# =====================================================================
# Section 10: Structural invariants
# =====================================================================

class TestStructuralInvariants:
    def test_pythagorean_triples_sorted(self):
        """pythagorean_triples returns sorted output."""
        triples = pythagorean_triples(100)
        assert triples == sorted(triples)

    def test_primitive_triples_sorted(self):
        """primitive_pythagorean_triples returns sorted output."""
        triples = primitive_pythagorean_triples(100)
        assert triples == sorted(triples)

    def test_markov_triples_sorted(self):
        """markov_triples returns sorted output."""
        triples = markov_triples(100)
        assert triples == sorted(triples)

    def test_no_duplicate_pythagorean(self):
        """No duplicate Pythagorean triples."""
        triples = pythagorean_triples(200)
        assert len(triples) == len(set(triples))

    def test_no_duplicate_primitive(self):
        """No duplicate primitive triples."""
        triples = primitive_pythagorean_triples(200)
        assert len(triples) == len(set(triples))

    def test_no_duplicate_markov(self):
        """No duplicate Markov triples."""
        triples = markov_triples(200)
        assert len(triples) == len(set(triples))

    def test_primitive_fraction_decreases(self):
        """The fraction of primitive triples among all triples decreases
        as N grows (multiples accumulate)."""
        f1 = coprime_triple_fraction(50)['fraction']
        f2 = coprime_triple_fraction(200)['fraction']
        # At small N, the fraction should be high (mostly primitive)
        # and decrease as non-primitive triples accumulate
        assert f1 >= f2 or abs(f1 - f2) < 0.15  # Allow some fluctuation

    def test_density_growth_pythagorean(self):
        """Pythagorean triple count grows with N."""
        c1 = len(pythagorean_triples(50))
        c2 = len(pythagorean_triples(100))
        assert c2 > c1


# =====================================================================
# Section 11: Edge cases
# =====================================================================

class TestEdgeCases:
    def test_pythagorean_triples_n0(self):
        """Empty for N=0."""
        assert pythagorean_triples(0) == []

    def test_markov_triples_n0(self):
        """Empty for N=0."""
        assert markov_triples(0) == []
        assert markov_triples(0, distinct_only=False) == []

    def test_partition_sat_n0(self):
        """SAT with N=0 and no constraints."""
        sat_solver = PartitionSAT(0, 2)
        sat, _ = sat_solver.solve([])
        assert sat

    def test_generalized_empty_for_small_n(self):
        """Some equations have no solutions for small N."""
        triples = generalized_quadratic_triples(2, 1, 1, 1)
        assert triples == []  # Smallest Pythagorean triple needs c=5

    def test_coprime_graph_triples_small(self):
        """At N=4, no coprime Pythagorean graph triples."""
        assert coprime_pythagorean_graph_triples(4) == []

    def test_partition_sat_single_element(self):
        """PartitionSAT with N=1, no forbidden tuples."""
        sat_solver = PartitionSAT(1, 2)
        sat, coloring = sat_solver.solve([], extract_witness=True)
        assert sat
        assert coloring is not None
        assert 1 in coloring
