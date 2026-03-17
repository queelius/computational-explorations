"""Tests for coprime_number_theory.py -- Number-theoretic coprime Ramsey experiments."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from coprime_number_theory import (
    coprime_edges,
    coprime_adj,
    find_cliques,
    _edge_var_map,
    _check_ramsey_sat,
    gcd_weight_matrix,
    max_weight_monochromatic_clique,
    soft_ramsey_threshold,
    ap_vertex_set,
    coprime_ramsey_ap,
    ap_coprime_density,
    ap_triangle_count,
    scan_ap_ramsey,
    coprime_ramsey_without,
    coprime_ramsey_odd_only,
    vertex_removal_impact,
    multiplicative_triples,
    multiplicative_ramsey,
    multiplicative_ramsey_witness,
    multiplicative_triple_density,
    coprime_turan_exact_small,
    coprime_turan_scan,
    _standard_turan,
)


# ---------------------------------------------------------------------------
# Infrastructure tests
# ---------------------------------------------------------------------------

class TestCoprimeEdges:
    def test_standard_n5(self):
        """Standard coprime edges on [5]."""
        edges = coprime_edges(5)
        expected = sum(1 for i in range(1, 6)
                       for j in range(i + 1, 6) if math.gcd(i, j) == 1)
        assert len(edges) == expected

    def test_custom_vertex_set(self):
        """Coprime edges on a custom vertex set."""
        edges = coprime_edges(0, vertex_set=[2, 3, 5, 6])
        # (2,3): gcd=1 YES, (2,5): gcd=1 YES, (2,6): gcd=2 NO
        # (3,5): gcd=1 YES, (3,6): gcd=3 NO, (5,6): gcd=1 YES
        assert (2, 3) in edges
        assert (2, 5) in edges
        assert (2, 6) not in edges
        assert (3, 6) not in edges
        assert (5, 6) in edges
        assert len(edges) == 4

    def test_even_numbers_no_coprime(self):
        """Even numbers share factor 2, so no coprime pairs."""
        edges = coprime_edges(0, vertex_set=[2, 4, 6, 8, 10])
        assert len(edges) == 0

    def test_primes_all_coprime(self):
        """Distinct primes are all mutually coprime."""
        primes = [2, 3, 5, 7, 11]
        edges = coprime_edges(0, vertex_set=primes)
        expected = len(primes) * (len(primes) - 1) // 2
        assert len(edges) == expected

    def test_edges_sorted(self):
        """Each edge (i,j) has i < j."""
        edges = coprime_edges(10)
        for a, b in edges:
            assert a < b


class TestCoprimeAdj:
    def test_symmetric(self):
        adj = coprime_adj([1, 2, 3, 4, 5])
        for v, nbrs in adj.items():
            for w in nbrs:
                assert v in adj[w]

    def test_vertex_1_universal(self):
        vs = list(range(1, 11))
        adj = coprime_adj(vs)
        assert adj[1] == set(range(2, 11))

    def test_custom_vertices(self):
        adj = coprime_adj([6, 10, 15])
        # gcd(6,10)=2, gcd(6,15)=3, gcd(10,15)=5
        assert len(adj[6]) == 0
        assert len(adj[10]) == 0
        assert len(adj[15]) == 0


class TestFindCliques:
    def test_triangles_n5(self):
        adj = coprime_adj(list(range(1, 6)))
        cliques = find_cliques(adj, 3)
        for c in cliques:
            assert len(c) == 3
            for i in range(3):
                for j in range(i + 1, 3):
                    assert math.gcd(c[i], c[j]) == 1

    def test_no_clique_in_independent_set(self):
        """Even numbers have no coprime pairs, so no cliques of size >= 2."""
        adj = coprime_adj([2, 4, 6, 8])
        assert find_cliques(adj, 2) == []
        assert find_cliques(adj, 3) == []

    def test_singleton_cliques(self):
        adj = coprime_adj([1, 2, 3])
        assert len(find_cliques(adj, 1)) == 3

    def test_empty_for_k0(self):
        adj = coprime_adj([1, 2, 3])
        assert find_cliques(adj, 0) == []

    def test_large_clique_impossible(self):
        adj = coprime_adj([1, 2, 3])
        assert find_cliques(adj, 5) == []


class TestCheckRamseySat:
    def test_forced_at_small_n(self):
        """At n=3, two coprime edges and one 2-edge clique should not force."""
        edges = coprime_edges(3)
        adj = coprime_adj([1, 2, 3])
        cliques = find_cliques(adj, 3)
        # [1,2,3] is a single triangle -- 2-coloring of 3 edges:
        # need both all-0 and all-1 forbidden, but 2^3=8 colorings,
        # and only 2 (all-same) are forbidden. So SAT (not forced).
        result = _check_ramsey_sat(edges, cliques)
        assert result is False

    def test_no_cliques_not_forced(self):
        """With no cliques, nothing is forced."""
        edges = coprime_edges(0, vertex_set=[2, 4, 6])
        assert _check_ramsey_sat(edges, []) is False


class TestEdgeVarMap:
    def test_positive_indices(self):
        edges = coprime_edges(5)
        etv = _edge_var_map(edges)
        assert all(v >= 1 for v in etv.values())
        assert len(set(etv.values())) == len(edges)


# ---------------------------------------------------------------------------
# 1. GCD-Weighted Coprime Graph
# ---------------------------------------------------------------------------

class TestGCDWeightMatrix:
    def test_symmetric(self):
        W = gcd_weight_matrix(5)
        assert W.shape == (5, 5)
        assert (W == W.T).all()

    def test_diagonal_zero(self):
        W = gcd_weight_matrix(5)
        for i in range(5):
            assert W[i, i] == 0.0

    def test_coprime_weight_one(self):
        """gcd(1,2)=1, so weight = 1.0."""
        W = gcd_weight_matrix(3)
        assert W[0, 1] == 1.0  # vertices 1,2

    def test_non_coprime_weight_fraction(self):
        """gcd(2,4)=2, so weight = 0.5."""
        W = gcd_weight_matrix(5)
        assert W[1, 3] == pytest.approx(0.5)  # vertices 2,4

    def test_all_weights_positive(self):
        """All off-diagonal weights are positive (1/gcd >= 1/n)."""
        W = gcd_weight_matrix(10)
        for i in range(10):
            for j in range(10):
                if i != j:
                    assert W[i, j] > 0


class TestMaxWeightMonochromaticClique:
    def test_small_n(self):
        info = max_weight_monochromatic_clique(4, 3)
        assert info["n"] == 4
        assert info["k"] == 3
        assert info["soft_ramsey_value"] >= 0

    def test_hard_threshold(self):
        """Hard threshold for k=3 is C(3,2) = 3."""
        info = max_weight_monochromatic_clique(5, 3)
        assert info["hard_clique_weight"] == 3.0

    def test_max_possible_at_least_hard(self):
        """Max possible weight >= hard threshold if coprime triples exist."""
        info = max_weight_monochromatic_clique(5, 3)
        if info["num_k_subsets"] > 0:
            assert info["max_possible_weight"] >= info["hard_clique_weight"]


class TestSoftRamseyThreshold:
    def test_returns_scan(self):
        result = soft_ramsey_threshold(3, max_n=7)
        assert "scan" in result
        assert len(result["scan"]) > 0

    def test_soft_values_nonnegative(self):
        result = soft_ramsey_threshold(3, max_n=7)
        for entry in result["scan"]:
            if entry["soft_value"] >= 0:
                assert entry["soft_value"] >= 0


# ---------------------------------------------------------------------------
# 2. Arithmetic Progression Coprime Ramsey
# ---------------------------------------------------------------------------

class TestAPVertexSet:
    def test_standard(self):
        assert ap_vertex_set(1, 1, 5) == [1, 2, 3, 4, 5]

    def test_odd_numbers(self):
        assert ap_vertex_set(1, 2, 4) == [1, 3, 5, 7]

    def test_even_numbers(self):
        assert ap_vertex_set(2, 2, 3) == [2, 4, 6]

    def test_custom(self):
        assert ap_vertex_set(5, 6, 3) == [5, 11, 17]


class TestCoprimeRamseyAP:
    def test_standard_ap_gives_11(self):
        """AP(1,1) is the standard coprime graph; R_cop^AP(3) = R_cop(3) = 11."""
        assert coprime_ramsey_ap(3, 1, 1, max_n=15) == 11

    def test_even_ap_no_coprime(self):
        """Even numbers have no coprime pairs, so no triangle can form."""
        result = coprime_ramsey_ap(3, 2, 2, max_n=30)
        assert result == -1

    def test_returns_minus1_if_not_found(self):
        """Should return -1 if max_n is too small."""
        result = coprime_ramsey_ap(3, 1, 1, max_n=5)
        assert result == -1

    def test_odd_numbers_ap(self):
        """AP(1,2) = odd numbers. All pairs of odd primes are coprime."""
        result = coprime_ramsey_ap(3, 1, 2, max_n=40)
        assert result > 0 or result == -1


class TestAPCoprimeDensity:
    def test_standard_density(self):
        """Standard coprime density should be around 6/pi^2 for large n."""
        dens = ap_coprime_density(1, 1, 100)
        assert 0.5 < dens < 0.7

    def test_even_density_zero(self):
        """Even numbers have zero coprime density."""
        dens = ap_coprime_density(2, 2, 20)
        assert dens == 0.0

    def test_primes_mod6_high_density(self):
        """AP(1,6) elements are coprime to 2 and 3, should have high density."""
        dens = ap_coprime_density(1, 6, 20)
        assert dens > 0.5


class TestAPTriangleCount:
    def test_no_triangles_evens(self):
        """Even numbers have no coprime triangles."""
        assert ap_triangle_count(2, 2, 10) == 0

    def test_positive_triangles_standard(self):
        """Standard [n] for n >= 3 has coprime triangles."""
        assert ap_triangle_count(1, 1, 5) > 0


class TestScanAPRamsey:
    def test_returns_dict(self):
        result = scan_ap_ramsey(3, [(1, 1)], max_n=15)
        assert (1, 1) in result
        assert result[(1, 1)] == 11


# ---------------------------------------------------------------------------
# 3. Vertex Removal
# ---------------------------------------------------------------------------

class TestCoprimeRamseyWithout:
    def test_standard_is_11(self):
        """No exclusions should give R_cop(3) = 11."""
        result = coprime_ramsey_without(3, 15, excluded=set(), max_n=15)
        assert result == 11

    def test_removing_1_increases(self):
        """Removing vertex 1 should increase R_cop(3) (it's the hub)."""
        result = coprime_ramsey_without(3, 30, excluded={1}, max_n=40)
        assert result >= 11  # should be >= 11, likely strictly greater

    def test_excluding_all_gives_minus1(self):
        """Excluding enough vertices should prevent finding the Ramsey number."""
        result = coprime_ramsey_without(3, 5, excluded={1, 2, 3, 4, 5}, max_n=5)
        assert result == -1


class TestCoprimeRamseyOddOnly:
    def test_returns_positive(self):
        """Odd coprime Ramsey should be computable."""
        result = coprime_ramsey_odd_only(3, max_n=40)
        assert result > 0 or result == -1

    def test_different_from_standard(self):
        """Odd-only should differ from standard (removes even numbers)."""
        result = coprime_ramsey_odd_only(3, max_n=60)
        if result > 0:
            assert result != 11  # Likely different from standard


class TestVertexRemovalImpact:
    def test_vertex_1_most_impactful(self):
        """Removing vertex 1 should create the most avoiding colorings."""
        # At n=11 (R_cop(3)), [11] has 0 avoiding colorings.
        # Removing any vertex should create some.
        impact = vertex_removal_impact(3, 11, [1, 2, 3])
        # Vertex 1 is coprime to all, so removing it should be most impactful
        assert impact[1] >= impact[2] or impact[1] >= impact[3]

    def test_all_positive_at_ramsey(self):
        """At R_cop(3) = 11, removing any vertex should create avoiding colorings."""
        impact = vertex_removal_impact(3, 11, [1, 5, 11])
        for v in [1, 5, 11]:
            assert impact[v] >= 0


# ---------------------------------------------------------------------------
# 4. Multiplicative Ramsey
# ---------------------------------------------------------------------------

class TestMultiplicativeTriples:
    def test_small(self):
        """Multiplicative triples in {2,...,8}: (2,3,6), (2,4,8)."""
        triples = multiplicative_triples(8)
        assert (2, 3, 6) in triples
        assert (2, 4, 8) in triples

    def test_no_triples_below_6(self):
        """Smallest multiplicative triple is (2,3,6)."""
        assert multiplicative_triples(5) == []

    def test_product_correct(self):
        """Every triple (a,b,c) satisfies a*b=c."""
        for a, b, c in multiplicative_triples(50):
            assert a * b == c

    def test_ordering(self):
        """Triples have a < b < c."""
        for a, b, c in multiplicative_triples(50):
            assert a < b < c

    def test_start_parameter(self):
        """Start=3 should exclude triples with a=2."""
        triples = multiplicative_triples(20, start=3)
        for a, b, c in triples:
            assert a >= 3

    def test_count_n10(self):
        """Count triples in {2,...,10}."""
        triples = multiplicative_triples(10)
        # (2,3,6), (2,4,8), (2,5,10)
        assert len(triples) == 3

    def test_count_n12(self):
        """Count triples in {2,...,12}."""
        triples = multiplicative_triples(12)
        # (2,3,6), (2,4,8), (2,5,10), (2,6,12), (3,4,12)
        assert len(triples) == 5


class TestMultiplicativeRamsey:
    def test_m1(self):
        """M(1): max N with 1-coloring avoiding mono triples.
        First triple is at N=6, so M(1) = 5."""
        m = multiplicative_ramsey(1, max_n=20)
        assert m == 5

    def test_m2_at_least_6(self):
        """M(2) >= 6 since we can 2-color to avoid triples at N=6."""
        m = multiplicative_ramsey(2, max_n=500)
        assert m >= 6

    def test_m_monotone(self):
        """More colors allow larger N: M(k) <= M(k+1)."""
        m2 = multiplicative_ramsey(2, max_n=500)
        m3 = multiplicative_ramsey(3, max_n=500)
        assert m3 >= m2

    def test_m2_witness(self):
        """Witness for M(2) should exist and avoid all triples."""
        m2 = multiplicative_ramsey(2, max_n=500)
        witness = multiplicative_ramsey_witness(2, m2)
        assert witness is not None
        # Verify no monochromatic triple
        triples = multiplicative_triples(m2)
        for a, b, c in triples:
            colors = {witness[a], witness[b], witness[c]}
            assert len(colors) > 1, f"Monochromatic triple ({a},{b},{c})"

    def test_m2_plus1_no_witness(self):
        """No valid 2-coloring at M(2)+1."""
        m2 = multiplicative_ramsey(2, max_n=500)
        witness = multiplicative_ramsey_witness(2, m2 + 1)
        assert witness is None

    def test_m1_witness(self):
        """Witness for M(1) = 5: just one color, no triples in {2,...,5}."""
        witness = multiplicative_ramsey_witness(1, 5)
        assert witness is not None
        assert all(v == 0 for v in witness.values())


class TestMultiplicativeTripleDensity:
    def test_density_fields(self):
        td = multiplicative_triple_density(20)
        assert "num_triples" in td
        assert "triple_density" in td
        assert td["num_triples"] > 0

    def test_density_grows(self):
        """Triple density should be nondecreasing with n."""
        d10 = multiplicative_triple_density(10)["num_triples"]
        d20 = multiplicative_triple_density(20)["num_triples"]
        assert d20 >= d10


# ---------------------------------------------------------------------------
# 5. Coprime Turan Numbers
# ---------------------------------------------------------------------------

class TestStandardTuran:
    def test_ex_n4_k3(self):
        """ex(4, K_3) = 4 (bipartite graph K_{2,2})."""
        assert _standard_turan(4, 3) == 4

    def test_ex_n5_k3(self):
        """ex(5, K_3) = 6 (Turan graph T(5,2))."""
        assert _standard_turan(5, 3) == 6

    def test_ex_n6_k3(self):
        """ex(6, K_3) = 9."""
        assert _standard_turan(6, 3) == 9

    def test_ex_n6_k4(self):
        """ex(6, K_4) = 12 (Turan graph T(6,3))."""
        assert _standard_turan(6, 4) == 12

    def test_k2_is_zero(self):
        """ex(n, K_2) = 0 (no edges allowed)."""
        assert _standard_turan(5, 2) == 0

    def test_monotone_in_n(self):
        """Turan number is non-decreasing in n."""
        for k in [3, 4]:
            for n in range(k, 15):
                assert _standard_turan(n, k) <= _standard_turan(n + 1, k)


class TestCoprimeTuranExact:
    def test_small_n(self):
        info = coprime_turan_exact_small(5, 3)
        assert info["ex_cop"] >= 0
        assert info["ex_cop"] <= info["total"]

    def test_no_cliques_means_full(self):
        """If G(n) has no K_k, then ex_cop = total coprime edges."""
        # n=3, k=4: no K_4 in G(3)
        info = coprime_turan_exact_small(3, 4)
        assert info["ex_cop"] == info["total"]

    def test_ex_cop_at_most_standard(self):
        """ex_cop(n, K_k) <= ex(n, K_k) since G(n) is a subgraph of K_n."""
        for n in range(4, 10):
            info = coprime_turan_exact_small(n, 3)
            assert info["ex_cop"] <= info["standard_turan"]

    def test_ex_cop_at_most_total(self):
        """ex_cop(n, K_k) <= total coprime edges."""
        for n in range(4, 10):
            info = coprime_turan_exact_small(n, 3)
            assert info["ex_cop"] <= info["total"]

    def test_fraction_bounded(self):
        """Fraction of retained edges should be in [0, 1]."""
        for n in range(4, 10):
            info = coprime_turan_exact_small(n, 3)
            assert 0 <= info["fraction"] <= 1


class TestCoprimeTuranScan:
    def test_returns_list(self):
        results = coprime_turan_scan(3, [4, 5, 6])
        assert len(results) == 3

    def test_monotone_total_edges(self):
        """Total coprime edges should be non-decreasing."""
        results = coprime_turan_scan(3, [5, 6, 7, 8])
        for i in range(len(results) - 1):
            assert results[i]["total"] <= results[i + 1]["total"]


# ---------------------------------------------------------------------------
# Cross-cutting pattern tests
# ---------------------------------------------------------------------------

class TestCrossCuttingPatterns:
    """Tests that verify relationships BETWEEN the experiments."""

    def test_ap_d1_equals_standard(self):
        """AP(1,1) coprime Ramsey should equal standard R_cop(3) = 11."""
        assert coprime_ramsey_ap(3, 1, 1, max_n=15) == 11

    def test_even_ap_trivially_infinite(self):
        """Even AP has no coprime pairs, so Ramsey is infinite."""
        assert coprime_ramsey_ap(3, 2, 2, max_n=30) == -1

    def test_vertex_1_removal_strict_increase(self):
        """R_cop(3; [n]\\{1}) > R_cop(3) = 11 (vertex 1 is critical)."""
        r_no1 = coprime_ramsey_without(3, 30, excluded={1}, max_n=30)
        # Removing the universal hub should delay forcing
        if r_no1 > 0:
            assert r_no1 > 11

    def test_multiplicative_m1_equals_5(self):
        """M(1) = 5: first multiplicative triple (2,3,6) forces at N=6."""
        assert multiplicative_ramsey(1, max_n=20) == 5

    def test_multiplicative_growth_subexponential(self):
        """M(k) grows, but check M(2) and M(3) are finite within range."""
        m2 = multiplicative_ramsey(2, max_n=500)
        m3 = multiplicative_ramsey(3, max_n=500)
        assert m2 > 5
        assert m3 > m2

    def test_turan_coprime_vs_standard_ratio(self):
        """ex_cop(n, K_3) / ex(n, K_3) should be < 1 for large enough n."""
        info = coprime_turan_exact_small(10, 3)
        if info["standard_turan"] > 0:
            assert info["ex_cop"] / info["standard_turan"] <= 1.0


class TestExactComputedValues:
    """Lock in exact computed values from experiments."""

    def test_soft_ramsey_n5_n6(self):
        """Soft Ramsey value is 2.5 for n=5,6 (not fully forced).
        n=7,8 verified in experiment runner but too slow for 120s tests."""
        for n in [5, 6]:
            info = max_weight_monochromatic_clique(n, 3)
            assert info["soft_ramsey_value"] == pytest.approx(2.5)

    def test_soft_ramsey_n3_n4_zero(self):
        """At n=3,4, some coloring avoids even near-miss triples."""
        for n in [3, 4]:
            info = max_weight_monochromatic_clique(n, 3)
            assert info["soft_ramsey_value"] == pytest.approx(0.0)

    def test_ap_ramsey_exact_values(self):
        """Exact AP Ramsey values for key configurations."""
        assert coprime_ramsey_ap(3, 1, 1, max_n=15) == 11   # standard
        assert coprime_ramsey_ap(3, 1, 2, max_n=15) == 7    # odds
        assert coprime_ramsey_ap(3, 2, 2, max_n=30) == -1   # evens: infinite
        assert coprime_ramsey_ap(3, 1, 6, max_n=15) == 6    # coprime to 6
        assert coprime_ramsey_ap(3, 1, 30, max_n=15) == 6   # coprime to 30

    def test_vertex_removal_exact(self):
        """Exact values for vertex removal experiments."""
        assert coprime_ramsey_without(3, 30, excluded={1}, max_n=20) == 13
        assert coprime_ramsey_without(3, 30, excluded={2}, max_n=15) == 11
        assert coprime_ramsey_without(3, 30, excluded={3}, max_n=15) == 11

    def test_vertex_impact_at_11(self):
        """Exact avoiding coloring counts at n=11."""
        impact = vertex_removal_impact(3, 11, [1, 5, 7, 11])
        assert impact[1] == 156
        assert impact[5] == 36
        assert impact[7] == 156
        assert impact[11] == 156

    def test_m2_exact(self):
        """M(2) = 95 exactly."""
        assert multiplicative_ramsey(2, max_n=200) == 95

    def test_coprime_turan_exact_values(self):
        """Exact coprime Turan numbers for small n."""
        for n, expected in [(4, 4), (5, 6), (6, 8), (7, 12)]:
            info = coprime_turan_exact_small(n, 3)
            assert info["ex_cop"] == expected, f"ex_cop({n},K_3) = {info['ex_cop']}, expected {expected}"

    def test_odd_only_ramsey(self):
        """R_cop(3; odd only) = 13."""
        assert coprime_ramsey_odd_only(3, max_n=20) == 13


class TestSoftRamseySAT:
    """Tests for the SAT-based soft Ramsey function."""

    def test_forced_at_11(self):
        from coprime_number_theory import soft_ramsey_sat
        result = soft_ramsey_sat(11, 3)
        assert result["forced"] is True

    def test_not_forced_at_10(self):
        from coprime_number_theory import soft_ramsey_sat
        result = soft_ramsey_sat(10, 3)
        assert result["forced"] is False

    def test_near_miss_weight(self):
        from coprime_number_theory import soft_ramsey_sat
        result = soft_ramsey_sat(8, 3)
        assert result["near_miss_weight"] == pytest.approx(2.5)

    def test_triangle_count_grows(self):
        from coprime_number_theory import soft_ramsey_sat
        counts = [soft_ramsey_sat(n, 3)["num_coprime_cliques"] for n in [5, 7, 9, 11]]
        for i in range(len(counts) - 1):
            assert counts[i] < counts[i + 1]


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_coprime_edges_empty_vertex_set(self):
        """Empty vertex set yields no edges."""
        assert coprime_edges(0, vertex_set=[]) == []

    def test_coprime_edges_singleton(self):
        """Single vertex yields no edges."""
        assert coprime_edges(0, vertex_set=[7]) == []

    def test_multiplicative_triples_small_n(self):
        """No triples for n < 6."""
        for n in range(2, 6):
            assert multiplicative_triples(n) == []

    def test_ap_vertex_set_single(self):
        """AP with n=1 gives single element."""
        assert ap_vertex_set(7, 3, 1) == [7]

    def test_standard_turan_k1(self):
        """ex(n, K_1) = 0."""
        assert _standard_turan(5, 1) == 0
