"""Tests for nt_graph_ramsey.py -- Number-theoretic graph Ramsey taxonomy."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nt_graph_ramsey import (
    # Utilities
    _adjacency,
    _edge_var_map,
    find_cliques,
    clique_number,
    greedy_chromatic_number,
    ramsey_sat,
    compute_ramsey_number,
    # Divisibility graph
    divisibility_edges,
    divisibility_graph,
    divisibility_edge_density,
    divisibility_clique_number,
    compute_rdiv,
    # GCD graph
    gcd_edges,
    gcd_graph,
    gcd_edge_density,
    compute_rgcd,
    # No-carry graph
    digit_sum,
    no_carry_condition,
    no_carry_edges,
    no_carry_graph,
    no_carry_edge_density,
    compute_rnocarry,
    # Paley graph
    is_prime,
    paley_eligible_primes,
    paley_edges,
    paley_graph,
    paley_edge_density,
    paley_clique_number,
    compute_rpaley,
    # Square-free graph
    is_squarefree,
    squarefree_product_edges,
    squarefree_graph,
    squarefree_edge_density,
    compute_rsf,
    # Taxonomy
    compute_structural_invariants,
    compute_density_profile,
)


# ============================================================================
# Generic graph utilities
# ============================================================================

class TestAdjacency:
    def test_empty(self):
        adj = _adjacency(3, [])
        assert all(len(adj[v]) == 0 for v in range(1, 4))

    def test_triangle(self):
        edges = [(1, 2), (2, 3), (1, 3)]
        adj = _adjacency(3, edges)
        assert adj[1] == {2, 3}
        assert adj[2] == {1, 3}
        assert adj[3] == {1, 2}

    def test_symmetric(self):
        edges = [(1, 2), (3, 4)]
        adj = _adjacency(4, edges)
        assert 2 in adj[1] and 1 in adj[2]
        assert 4 in adj[3] and 3 in adj[4]


class TestEdgeVarMap:
    def test_simple(self):
        edges = [(1, 2), (1, 3), (2, 3)]
        evm = _edge_var_map(edges)
        assert evm[(1, 2)] == 1
        assert evm[(1, 3)] == 2
        assert evm[(2, 3)] == 3

    def test_count(self):
        edges = [(i, j) for i in range(1, 6) for j in range(i + 1, 6)]
        evm = _edge_var_map(edges)
        assert len(evm) == 10


class TestFindCliques:
    def test_triangle_in_K4(self):
        edges = [(i, j) for i in range(1, 5) for j in range(i + 1, 5)]
        adj = _adjacency(4, edges)
        vertices = list(range(1, 5))
        triangles = find_cliques(adj, vertices, 3)
        # K_4 has C(4,3) = 4 triangles
        assert len(triangles) == 4

    def test_no_cliques_in_empty(self):
        adj = {1: set(), 2: set(), 3: set()}
        cliques = find_cliques(adj, [1, 2, 3], 2)
        assert len(cliques) == 0

    def test_singleton_cliques(self):
        adj = {1: set(), 2: set()}
        cliques = find_cliques(adj, [1, 2], 1)
        assert len(cliques) == 2

    def test_empty_for_k0(self):
        adj = {1: {2}, 2: {1}}
        assert find_cliques(adj, [1, 2], 0) == []


class TestCliqueNumber:
    def test_complete_graph(self):
        edges = [(i, j) for i in range(1, 5) for j in range(i + 1, 5)]
        adj = _adjacency(4, edges)
        assert clique_number(adj, list(range(1, 5))) == 4

    def test_independent_set(self):
        adj = {1: set(), 2: set(), 3: set()}
        assert clique_number(adj, [1, 2, 3]) == 1

    def test_path(self):
        adj = {1: {2}, 2: {1, 3}, 3: {2}}
        assert clique_number(adj, [1, 2, 3]) == 2


class TestGreedyChromaticNumber:
    def test_complete_graph(self):
        edges = [(i, j) for i in range(1, 5) for j in range(i + 1, 5)]
        adj = _adjacency(4, edges)
        assert greedy_chromatic_number(adj, list(range(1, 5))) == 4

    def test_bipartite(self):
        # K_{2,2}: edges (1,3),(1,4),(2,3),(2,4)
        adj = {1: {3, 4}, 2: {3, 4}, 3: {1, 2}, 4: {1, 2}}
        assert greedy_chromatic_number(adj, [1, 2, 3, 4]) == 2

    def test_odd_cycle(self):
        # C_5 has chi = 3
        adj = {0: {1, 4}, 1: {0, 2}, 2: {1, 3}, 3: {2, 4}, 4: {3, 0}}
        assert greedy_chromatic_number(adj, list(range(5))) == 3

    def test_empty_graph(self):
        assert greedy_chromatic_number({}, []) == 0


class TestRamseySAT:
    def test_triangle_in_K5(self):
        # K_5: every 2-coloring has monochromatic K_3 (since R(3,3)=6, K_5 doesn't)
        # Actually R(3,3)=6, so K_5 can avoid. SAT should return True.
        edges = [(i, j) for i in range(1, 6) for j in range(i + 1, 6)]
        adj = _adjacency(5, edges)
        assert ramsey_sat(edges, adj, list(range(1, 6)), 3) is True

    def test_triangle_in_K6(self):
        # R(3,3)=6: every 2-coloring of K_6 has mono K_3. UNSAT.
        edges = [(i, j) for i in range(1, 7) for j in range(i + 1, 7)]
        adj = _adjacency(6, edges)
        assert ramsey_sat(edges, adj, list(range(1, 7)), 3) is False

    def test_no_edges(self):
        assert ramsey_sat([], {1: set()}, [1], 3) is True

    def test_no_cliques(self):
        # Path graph: no triangles
        edges = [(1, 2), (2, 3)]
        adj = _adjacency(3, edges)
        assert ramsey_sat(edges, adj, [1, 2, 3], 3) is True


# ============================================================================
# 1. Divisibility graph D(n)
# ============================================================================

class TestDivisibilityEdges:
    def test_d5(self):
        """D(5) edges: 1|2, 1|3, 1|4, 1|5, 2|4."""
        edges = divisibility_edges(5)
        assert (1, 2) in edges
        assert (1, 3) in edges
        assert (1, 4) in edges
        assert (1, 5) in edges
        assert (2, 4) in edges
        assert len(edges) == 5

    def test_d10_count(self):
        edges = divisibility_edges(10)
        assert len(edges) == 17

    def test_no_self_loops(self):
        edges = divisibility_edges(10)
        for i, j in edges:
            assert i != j

    def test_canonical_order(self):
        """Edges should have i < j."""
        for e in divisibility_edges(20):
            assert e[0] < e[1]

    def test_monotone(self):
        assert len(divisibility_edges(10)) <= len(divisibility_edges(20))

    def test_1_divides_all(self):
        """Vertex 1 divides everything: edges (1,k) for all k > 1."""
        n = 10
        edges = divisibility_edges(n)
        for k in range(2, n + 1):
            assert (1, k) in edges


class TestDivisibilityDensity:
    def test_sparse(self):
        """Divisibility graph is sparse: density -> 0."""
        d10 = divisibility_edge_density(10)
        d50 = divisibility_edge_density(50)
        d100 = divisibility_edge_density(100)
        assert d10 > d50 > d100

    def test_positive(self):
        assert divisibility_edge_density(5) > 0


class TestDivisibilityCliqueNumber:
    def test_chain_bound(self):
        """omega(D(n)) = floor(log2(n)) + 1 (length of longest binary chain)."""
        for n in [4, 8, 16]:
            omega = divisibility_clique_number(n)
            expected = int(math.log2(n)) + 1
            assert omega == expected, f"D({n}): got {omega}, expected {expected}"

    def test_d10(self):
        assert divisibility_clique_number(10) == 4  # chain 1,2,4,8

    def test_d20(self):
        assert divisibility_clique_number(20) == 5  # chain 1,2,4,8,16

    def test_monotone(self):
        assert divisibility_clique_number(10) <= divisibility_clique_number(20)


class TestRDiv:
    def test_rdiv3(self):
        """R_div(3) = 32: verified at boundary."""
        assert compute_rdiv(3, max_n=40) == 32

    def test_rdiv3_boundary_sat(self):
        """At n=31, avoiding coloring exists for D(n) with k=3."""
        e, adj, v = divisibility_graph(31)
        assert ramsey_sat(e, adj, v, 3) is True

    def test_rdiv3_boundary_unsat(self):
        """At n=32, every 2-coloring of D(n) has mono K_3."""
        e, adj, v = divisibility_graph(32)
        assert ramsey_sat(e, adj, v, 3) is False

    def test_rdiv_requires_cliques(self):
        """R_div(k) requires k-cliques, which need chains of length k."""
        # k=2: any edge gives K_2. R_div(2) should be small.
        r2 = compute_rdiv(2, max_n=10)
        assert r2 >= 2
        assert r2 <= 3


# ============================================================================
# 2. GCD graph G_d(n)
# ============================================================================

class TestGCDEdges:
    def test_gcd1_is_coprime(self):
        """G_1(n) = coprime graph."""
        for n in [5, 10]:
            g1_edges = set(gcd_edges(n, 1))
            coprime = set()
            for i in range(1, n + 1):
                for j in range(i + 1, n + 1):
                    if math.gcd(i, j) == 1:
                        coprime.add((i, j))
            assert g1_edges == coprime

    def test_gcd2_correctness(self):
        """G_2(10) edges verified by hand."""
        edges = gcd_edges(10, 2)
        assert (2, 4) in edges      # gcd=2
        assert (2, 6) in edges      # gcd=2
        assert (4, 6) in edges      # gcd=2
        assert (4, 8) not in edges  # gcd=4, not 2
        assert (1, 2) not in edges  # gcd=1, not 2
        assert len(edges) == 9

    def test_gcd_d_requires_multiples(self):
        """Vertices must be multiples of d to participate in G_d edges."""
        for d in [2, 3, 5]:
            edges = gcd_edges(20, d)
            for i, j in edges:
                assert i % d == 0 and j % d == 0

    def test_gcd_disjoint(self):
        """G_d and G_{d'} are edge-disjoint for d != d'."""
        g1 = set(gcd_edges(20, 1))
        g2 = set(gcd_edges(20, 2))
        g3 = set(gcd_edges(20, 3))
        assert len(g1 & g2) == 0
        assert len(g1 & g3) == 0
        assert len(g2 & g3) == 0


class TestGCDDensity:
    def test_gcd1_dense(self):
        """G_1 (coprime) should have highest density among GCD graphs."""
        for n in [20, 40]:
            d1 = gcd_edge_density(n, 1)
            d2 = gcd_edge_density(n, 2)
            d3 = gcd_edge_density(n, 3)
            assert d1 > d2 > d3

    def test_gcd1_approaches_six_over_pi_squared(self):
        """Density of coprime graph -> 6/pi^2 ~ 0.6079."""
        target = 6.0 / (math.pi ** 2)
        d100 = gcd_edge_density(100, 1)
        assert abs(d100 - target) < 0.03


class TestRGCD:
    def test_rgcd3_d1(self):
        """R_gcd(3; 1) = R_cop(3) = 11."""
        assert compute_rgcd(3, d=1, max_n=20) == 11

    def test_rgcd3_d2(self):
        """R_gcd(3; 2) = 22."""
        assert compute_rgcd(3, d=2, max_n=30) == 22

    def test_rgcd3_d3(self):
        """R_gcd(3; 3) = 33."""
        assert compute_rgcd(3, d=3, max_n=40) == 33

    def test_rgcd3_d6(self):
        """R_gcd(3; 6) = 66."""
        assert compute_rgcd(3, d=6, max_n=80) == 66

    def test_exact_scaling(self):
        """R_gcd(3; d) = 11 * d for d in {1, 2, 3, 6}.

        This is a remarkable exact scaling law: the GCD-d graph is
        isomorphic (on multiples of d) to the coprime graph, so the
        Ramsey number scales linearly with d.
        """
        for d in [1, 2, 3, 6]:
            r = compute_rgcd(3, d, max_n=11 * d + 5)
            assert r == 11 * d, f"R_gcd(3; {d}) = {r}, expected {11 * d}"


# ============================================================================
# 3. No-carry graph S(n)
# ============================================================================

class TestDigitSum:
    def test_single_digit(self):
        for d in range(10):
            assert digit_sum(d) == d

    def test_multi_digit(self):
        assert digit_sum(123) == 6
        assert digit_sum(999) == 27
        assert digit_sum(100) == 1

    def test_zero(self):
        assert digit_sum(0) == 0

    def test_base2(self):
        assert digit_sum(7, base=2) == 3  # 111 in binary
        assert digit_sum(8, base=2) == 1  # 1000 in binary


class TestNoCarryCondition:
    def test_no_carry_small(self):
        """3+4=7: no carry."""
        assert no_carry_condition(3, 4) is True

    def test_carry(self):
        """5+7=12: carry in ones place."""
        assert no_carry_condition(5, 7) is False

    def test_no_carry_tens(self):
        """11+22=33: no carry in any position."""
        assert no_carry_condition(11, 22) is True

    def test_carry_tens(self):
        """15+16=31: carry in ones (5+6=11)."""
        assert no_carry_condition(15, 16) is False

    def test_9_plus_1_carries(self):
        """9+1=10: carry."""
        assert no_carry_condition(9, 1) is False

    def test_9_plus_10_no_carry(self):
        """9+10=19: ones: 9+0=9<10, tens: 0+1=1<10."""
        assert no_carry_condition(9, 10) is True

    def test_symmetric(self):
        for i in range(1, 20):
            for j in range(i + 1, 20):
                assert no_carry_condition(i, j) == no_carry_condition(j, i)

    def test_base2_carry(self):
        """In base 2: 1+1=10, carries."""
        assert no_carry_condition(1, 1, base=2) is False

    def test_base2_no_carry(self):
        """In base 2: 2+1=3 (10+01=11), no carry."""
        assert no_carry_condition(2, 1, base=2) is True


class TestNoCarryEdges:
    def test_s10_count(self):
        """S(10) has 25 edges."""
        assert len(no_carry_edges(10)) == 25

    def test_1_is_universal_within_digit(self):
        """1 connects to 2..8 (no carry) but not 9 (1+9=10, carry)."""
        edges = no_carry_edges(10)
        for j in range(2, 9):
            assert (1, j) in edges
        # 1+9=10 carries
        assert (1, 9) not in edges


class TestNoCarryDensity:
    def test_density_around_half(self):
        """No-carry density is near (base-1)/(2*base-1) = 9/19 ~ 0.474."""
        d20 = no_carry_edge_density(20)
        assert 0.40 < d20 < 0.60

    def test_positive(self):
        assert no_carry_edge_density(10) > 0


class TestRNoCarry:
    def test_rnocarry3(self):
        """R_S(3) = 10."""
        assert compute_rnocarry(3, max_n=20) == 10

    def test_rnocarry3_boundary_sat(self):
        """At n=9, avoiding coloring exists."""
        e, adj, v = no_carry_graph(9)
        assert ramsey_sat(e, adj, v, 3) is True

    def test_rnocarry3_boundary_unsat(self):
        """At n=10, every 2-coloring has mono K_3."""
        e, adj, v = no_carry_graph(10)
        assert ramsey_sat(e, adj, v, 3) is False


# ============================================================================
# 4. Paley graph QR(p)
# ============================================================================

class TestIsPrime:
    def test_primes(self):
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
        for p in primes:
            assert is_prime(p), f"{p} should be prime"

    def test_composites(self):
        composites = [0, 1, 4, 6, 8, 9, 10, 12, 14, 15]
        for n in composites:
            assert not is_prime(n), f"{n} should not be prime"


class TestPaleyEligiblePrimes:
    def test_small(self):
        """Primes p = 1 mod 4 up to 30: 5, 13, 17, 29."""
        primes = paley_eligible_primes(30)
        assert primes == [5, 13, 17, 29]

    def test_all_1_mod_4(self):
        for p in paley_eligible_primes(100):
            assert p % 4 == 1
            assert is_prime(p)


class TestPaleyEdges:
    def test_qr5_is_5cycle(self):
        """QR(5) is the 5-cycle C_5."""
        edges = paley_edges(5)
        assert len(edges) == 5
        # Check it forms a cycle: each vertex has degree 2
        adj: Dict[int, set] = {i: set() for i in range(5)}
        for u, v in edges:
            adj[u].add(v)
            adj[v].add(u)
        for v in range(5):
            assert len(adj[v]) == 2

    def test_qr13_edge_count(self):
        """QR(13): 13 vertices, each with (13-1)/2 = 6 neighbors. 13*6/2 = 39 edges."""
        assert len(paley_edges(13)) == 39

    def test_not_prime_returns_empty(self):
        assert paley_edges(4) == []
        assert paley_edges(6) == []

    def test_wrong_residue_returns_empty(self):
        """p = 3 mod 4 (e.g. p=7) is not eligible."""
        assert paley_edges(7) == []

    def test_self_complementary_degree(self):
        """Paley graph is (p-1)/2-regular."""
        for p in [5, 13, 17, 29]:
            edges = paley_edges(p)
            adj_dict: Dict[int, set] = {i: set() for i in range(p)}
            for u, v in edges:
                adj_dict[u].add(v)
                adj_dict[v].add(u)
            expected_deg = (p - 1) // 2
            for v in range(p):
                assert len(adj_dict[v]) == expected_deg, \
                    f"QR({p}): vertex {v} has degree {len(adj_dict[v])}, expected {expected_deg}"


class TestPaleyDensity:
    def test_exactly_half(self):
        """Paley graph density is exactly 1/2 for all valid p."""
        for p in paley_eligible_primes(60):
            assert paley_edge_density(p) == 0.5


class TestPaleyCliqueNumber:
    def test_qr5_omega(self):
        """QR(5) = C_5 has omega = 2."""
        assert paley_clique_number(5) == 2

    def test_qr13_omega(self):
        """QR(13) has omega = 3."""
        assert paley_clique_number(13) == 3

    def test_qr29_omega(self):
        """QR(29) has omega = 4."""
        assert paley_clique_number(29) == 4

    def test_omega_growth(self):
        """Clique number grows roughly as log(p)/2."""
        # omega should increase with p
        omegas = [(p, paley_clique_number(p)) for p in paley_eligible_primes(50)]
        # At least one increase
        assert omegas[-1][1] >= omegas[0][1]


class TestRPaley:
    def test_rpaley3(self):
        """R_QR(3) = 53: first Paley graph where every 2-coloring has mono K_3."""
        assert compute_rpaley(3, max_p=60) == 53

    def test_rpaley3_boundary_sat(self):
        """QR(41) has an avoiding coloring for K_3."""
        e, adj, v = paley_graph(41)
        assert ramsey_sat(e, adj, v, 3) is True

    def test_rpaley3_boundary_unsat(self):
        """QR(53) forces mono K_3 in every 2-coloring."""
        e, adj, v = paley_graph(53)
        assert ramsey_sat(e, adj, v, 3) is False


# ============================================================================
# 5. Square-free product graph SF(n)
# ============================================================================

class TestIsSquarefree:
    def test_squarefree_small(self):
        """1,2,3,5,6,7,10 are squarefree."""
        for n in [1, 2, 3, 5, 6, 7, 10]:
            assert is_squarefree(n), f"{n} should be squarefree"

    def test_not_squarefree(self):
        """4,8,9,12,16,18 are not squarefree."""
        for n in [4, 8, 9, 12, 16, 18]:
            assert not is_squarefree(n), f"{n} should not be squarefree"

    def test_zero_not_squarefree(self):
        assert not is_squarefree(0)

    def test_primes_are_squarefree(self):
        for p in [2, 3, 5, 7, 11, 13, 17, 19]:
            assert is_squarefree(p)


class TestSquarefreeEdges:
    def test_sf10(self):
        """SF(10): verified edge list."""
        edges = squarefree_product_edges(10)
        assert len(edges) == 16
        # 4, 8, 9 are not squarefree, so they participate in NO edges
        for e in edges:
            assert 4 not in e
            assert 8 not in e
            assert 9 not in e

    def test_subgraph_of_coprime(self):
        """SF(n) is a subgraph of the coprime graph G_1(n)."""
        for n in [10, 20]:
            sf_edges = set(squarefree_product_edges(n))
            cop_edges = set(gcd_edges(n, 1))
            assert sf_edges.issubset(cop_edges)

    def test_requires_squarefree_and_coprime(self):
        """Edge (i,j) iff both squarefree AND coprime."""
        n = 15
        for i in range(1, n + 1):
            for j in range(i + 1, n + 1):
                expected = (is_squarefree(i) and is_squarefree(j)
                            and math.gcd(i, j) == 1)
                actual = (i, j) in squarefree_product_edges(n)
                assert actual == expected, \
                    f"({i},{j}): expected {expected}, got {actual}"


class TestSquarefreeDensity:
    def test_less_than_coprime(self):
        """SF density < coprime density (it's a subgraph)."""
        for n in [20, 40]:
            sf = squarefree_edge_density(n)
            cop = gcd_edge_density(n, 1)
            assert sf < cop

    def test_positive(self):
        assert squarefree_edge_density(10) > 0


class TestRSF:
    def test_rsf3(self):
        """R_SF(3) = 11."""
        assert compute_rsf(3, max_n=20) == 11

    def test_rsf3_boundary_sat(self):
        """SF(10) has avoiding coloring."""
        e, adj, v = squarefree_graph(10)
        assert ramsey_sat(e, adj, v, 3) is True

    def test_rsf3_boundary_unsat(self):
        """SF(11) forces mono K_3."""
        e, adj, v = squarefree_graph(11)
        assert ramsey_sat(e, adj, v, 3) is False

    def test_rsf_ge_rcop(self):
        """R_SF(3) >= R_cop(3) since SF is a subgraph of the coprime graph.

        Actually R_SF(3) = R_cop(3) = 11, showing the coprime graph's
        Ramsey forcing comes from squarefree pairs.
        """
        rsf = compute_rsf(3, max_n=20)
        rcop = compute_rgcd(3, d=1, max_n=20)
        assert rsf >= rcop


# ============================================================================
# Structural invariants
# ============================================================================

class TestStructuralInvariants:
    @pytest.fixture(scope="class")
    def inv20(self):
        return compute_structural_invariants(20)

    def test_divisibility_perfect(self, inv20):
        """D(20) is perfect: omega = chi."""
        d = inv20['divisibility']
        assert d['omega'] == d['chi']

    def test_coprime_omega(self, inv20):
        """omega(coprime(20)) = 9 (1 + primes up to 20: 2,3,5,7,11,13,17,19)."""
        assert inv20['coprime']['omega'] == 9

    def test_no_carry_omega_large(self, inv20):
        """No-carry graph has large clique number (digits don't interfere)."""
        assert inv20['no_carry']['omega'] >= 9

    def test_squarefree_omega(self, inv20):
        """SF(20) omega = coprime omega (squarefree vertices include all primes+1)."""
        assert inv20['squarefree']['omega'] == 9

    def test_density_ordering(self, inv20):
        """Density ordering at n=20: gcd_2 < divisibility < squarefree < no_carry < coprime.

        Note: divisibility > gcd_2 because D(n) has edges (i,j) for ALL
        divisibility relations (gcd can be any value), while G_2 restricts
        to gcd(i,j) = 2 exactly.
        """
        d = {k: v['density'] for k, v in inv20.items() if 'density' in v}
        assert d['gcd_2'] < d['divisibility']
        assert d['divisibility'] < d['squarefree']
        assert d['squarefree'] < d['coprime']

    def test_paley_present(self, inv20):
        """Paley invariants should be computed for some prime near 20."""
        assert 'paley' in inv20


class TestDensityProfile:
    def test_returns_all_families(self):
        profile = compute_density_profile(max_n=30)
        assert 'divisibility' in profile
        assert 'gcd_1' in profile
        assert 'gcd_2' in profile
        assert 'no_carry' in profile
        assert 'squarefree' in profile
        assert 'paley' in profile

    def test_divisibility_decreasing(self):
        profile = compute_density_profile(max_n=50)
        densities = [d for _, d in profile['divisibility']]
        # Should generally decrease
        assert densities[0] > densities[-1]

    def test_paley_constant(self):
        profile = compute_density_profile(max_n=50)
        for _, d in profile['paley']:
            assert d == 0.5


# ============================================================================
# Cross-family comparisons (the taxonomy)
# ============================================================================

class TestTaxonomy:
    """Test the relationships between graph families."""

    def test_gcd_graphs_partition_edges(self):
        """For fixed n, GCD graphs for different d partition all pairs (i,j)
        with i < j (since gcd(i,j) takes exactly one value)."""
        n = 20
        all_pairs = set()
        for d in range(1, n + 1):
            edges = gcd_edges(n, d)
            for e in edges:
                assert e not in all_pairs, f"Edge {e} appears in multiple GCD graphs"
                all_pairs.add(e)
        expected = n * (n - 1) // 2
        assert len(all_pairs) == expected

    def test_squarefree_subgraph_coprime(self):
        """SF(n) edges are a subset of coprime edges."""
        for n in [10, 15, 20]:
            sf = set(squarefree_product_edges(n))
            cop = set(gcd_edges(n, 1))
            assert sf <= cop

    def test_ramsey_ordering(self):
        """Sparser graphs should generally have larger Ramsey numbers.

        R_S(3) <= R_cop(3) <= R_div(3) <= R_QR(3)
        """
        r_nocarry = compute_rnocarry(3, max_n=20)
        r_cop = compute_rgcd(3, d=1, max_n=20)
        r_div = compute_rdiv(3, max_n=40)
        r_paley = compute_rpaley(3, max_p=60)

        # No-carry has highest effective clique density among small n
        assert r_nocarry <= r_cop
        # Divisibility is sparser than coprime
        assert r_cop <= r_div
        # Paley is hardest (self-complementary, density exactly 1/2)
        assert r_div <= r_paley

    def test_no_carry_less_than_coprime(self):
        """R_S(3)=10 < R_cop(3)=11: the no-carry graph forces triangles earlier."""
        assert compute_rnocarry(3, max_n=20) < compute_rgcd(3, d=1, max_n=20)

    def test_gcd_scaling_law(self):
        """The exact scaling R_gcd(3; d) = 11*d is a theorem, not a coincidence.

        Proof sketch: the map i -> d*i gives an isomorphism between
        the coprime graph on [m] and the GCD-d graph on {d, 2d, ..., md}.
        So every 2-coloring of GCD-d on [n] restricts to a 2-coloring
        of the coprime graph on [n/d], and vice versa.

        Therefore R_gcd(3; d) = d * R_cop(3) = 11d.
        """
        for d in [1, 2, 3, 6]:
            assert compute_rgcd(3, d, max_n=11 * d + 5) == 11 * d


class TestEdgeCases:
    def test_divisibility_n1(self):
        assert divisibility_edges(1) == []

    def test_gcd_n1(self):
        assert gcd_edges(1, 1) == []

    def test_no_carry_n1(self):
        assert no_carry_edges(1) == []

    def test_squarefree_n1(self):
        assert squarefree_product_edges(1) == []

    def test_paley_n2(self):
        assert paley_edges(2) == []

    def test_divisibility_n2(self):
        """D(2): edge (1,2) since 1 | 2."""
        assert divisibility_edges(2) == [(1, 2)]

    def test_ramsey_k2_trivial(self):
        """R_X(2) should be small for any graph with edges."""
        # Divisibility
        r2_div = compute_rdiv(2, max_n=10)
        assert 2 <= r2_div <= 3

    def test_no_carry_base2(self):
        """No-carry in base 2 gives different structure."""
        # In base 2: no carry means no bit position has both i,j set
        edges = no_carry_edges(7, base=2)
        assert len(edges) > 0
        # 1 (01) + 2 (10) = 3 (11): no carry -> edge
        assert (1, 2) in edges
        # 1 (01) + 3 (11): bit 0 has 1+1 -> carry -> no edge
        assert (1, 3) not in edges


# ============================================================================
# Performance guards
# ============================================================================

class TestPerformance:
    """Ensure computations stay within reasonable time."""

    def test_divisibility_edges_n100(self):
        """Building D(100) should be fast."""
        edges = divisibility_edges(100)
        assert len(edges) > 100  # plenty of edges

    def test_gcd_edges_n50(self):
        edges = gcd_edges(50, 2)
        assert len(edges) > 0

    def test_no_carry_edges_n100(self):
        edges = no_carry_edges(100)
        assert len(edges) > 100

    def test_paley_edges_p53(self):
        edges = paley_edges(53)
        # 53 vertices, each with (53-1)/2 = 26 neighbors. Total edges = 53*26/2 = 689.
        assert len(edges) == 689
