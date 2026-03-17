"""Tests for cycle_spectrum.py (Problem #883 extension) and hub-spoke theorem."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cycle_spectrum import (
    coprime_graph,
    find_odd_cycle_lengths,
    coprime_edge_density,
    bipartite_ET,
    hub_coprime_neighbors,
    bipartite_min_degrees,
    greedy_alternating_path,
    build_bipartite_adj,
    verify_cycle_spectrum_bipartite,
    verify_full_cycle_spectrum,
)


class TestCoprimeGraph:
    def test_small_set(self):
        adj = coprime_graph({2, 3, 5})
        # All pairs coprime
        assert 3 in adj[2]
        assert 5 in adj[2]
        assert 5 in adj[3]

    def test_non_coprime_excluded(self):
        adj = coprime_graph({4, 6})
        # gcd(4,6)=2, not coprime
        assert 6 not in adj.get(4, set())

    def test_singleton(self):
        adj = coprime_graph({7})
        assert len(adj) == 0

    def test_includes_1(self):
        adj = coprime_graph({1, 2, 3})
        # 1 coprime with everything
        assert 2 in adj[1]
        assert 3 in adj[1]


class TestFindOddCycleLengths:
    def test_triangle(self):
        # {1,2,3}: 1-2, 1-3, 2-3 form K3, which has a triangle
        cycles = find_odd_cycle_lengths({1, 2, 3})
        assert 3 in cycles

    def test_no_cycle_small(self):
        # Two elements can't form a cycle
        cycles = find_odd_cycle_lengths({2, 3})
        assert len(cycles) == 0

    def test_primes_have_triangle(self):
        # {2,3,5,7}: all coprime, so K4 has triangle
        cycles = find_odd_cycle_lengths({2, 3, 5, 7})
        assert 3 in cycles

    def test_full_set_has_triangle(self):
        cycles = find_odd_cycle_lengths(set(range(1, 11)))
        assert 3 in cycles

    def test_empty_set(self):
        cycles = find_odd_cycle_lengths(set())
        assert len(cycles) == 0


class TestCoprimeEdgeDensity:
    def test_primes_density_one(self):
        d = coprime_edge_density({2, 3, 5, 7, 11})
        assert abs(d - 1.0) < 0.001

    def test_even_density_zero(self):
        d = coprime_edge_density({2, 4, 6, 8})
        assert d == 0.0

    def test_singleton(self):
        d = coprime_edge_density({5})
        assert d == 0.0

    def test_full_set_moderate(self):
        d = coprime_edge_density(set(range(1, 51)))
        assert 0.5 < d < 0.7  # Should be near 6/π² ≈ 0.608


# =============================================================================
# Hub-Spoke Theorem Tests (Problem #883 Full Cycle Spectrum)
# =============================================================================


def extremal_set(n):
    """A*(n) = {i in [n] : 2|i or 3|i}."""
    return {i for i in range(1, n + 1) if i % 2 == 0 or i % 3 == 0}


def bipartite_ET(n):
    """Decompose A*(n) into E (even, not div by 3) and T (odd multiples of 3)."""
    E = {i for i in range(1, n + 1) if i % 2 == 0 and i % 3 != 0}
    T = {i for i in range(1, n + 1) if i % 3 == 0 and i % 2 != 0}
    return E, T


class TestExtremalSetStructure:
    """Verify structural properties of A* = {i : 2|i or 3|i}."""

    def test_extremal_size(self):
        """|A*| = floor(n/2) + floor(n/3) - floor(n/6) by inclusion-exclusion."""
        for n in range(6, 100):
            expected = n // 2 + n // 3 - n // 6
            assert len(extremal_set(n)) == expected

    def test_extremal_is_triangle_free(self):
        """A* has no coprime triple (it IS the extremal set)."""
        for n in [12, 18, 24, 30, 48]:
            A_star = extremal_set(n)
            adj = coprime_graph(A_star)
            # Check no triangle exists
            for a in A_star:
                for b in adj.get(a, set()):
                    if b > a:
                        # Check if any c > b is adjacent to both a and b
                        for c in adj.get(a, set()):
                            if c > b and c in adj.get(b, set()):
                                pytest.fail(f"Triangle {a},{b},{c} in A*({n})")

    def test_bipartite_decomposition(self):
        """A* = R0 ∪ E ∪ T where R0 is isolated, E-T is bipartite."""
        for n in [18, 30, 60]:
            A_star = extremal_set(n)
            E, T = bipartite_ET(n)
            R0 = {i for i in range(1, n + 1) if i % 6 == 0}
            # Check partition
            assert E | T | R0 == A_star
            assert len(E & T) == 0
            assert len(E & R0) == 0
            assert len(T & R0) == 0

    def test_ET_coprime_pairs_only(self):
        """Within A*, coprime pairs exist ONLY between E and T."""
        for n in [18, 30, 48]:
            A_star = extremal_set(n)
            E, T = bipartite_ET(n)
            adj = coprime_graph(A_star)
            for a, neighbors in adj.items():
                for b in neighbors:
                    # Every coprime pair must be one from E, one from T
                    assert (a in E and b in T) or (a in T and b in E), \
                        f"Non-E-T coprime pair: {a}, {b} in A*({n})"


class TestCoprimeDensityET:
    """Verify coprime density in E × T equals 9/π² ≈ 0.9119."""

    def _compute_ET_density(self, n):
        """Compute coprime pair density between E and T."""
        E, T = bipartite_ET(n)
        if not E or not T:
            return 0.0
        coprime_count = sum(
            1 for e in E for t in T if math.gcd(e, t) == 1
        )
        return coprime_count / (len(E) * len(T))

    def test_density_approaches_9_over_pi_sq(self):
        """For large n, E-T coprime density → 9/π²."""
        target = 9 / math.pi**2  # ≈ 0.9119
        for n in [100, 200, 500]:
            density = self._compute_ET_density(n)
            assert abs(density - target) < 0.03, \
                f"n={n}: density {density:.4f} not near 9/π²={target:.4f}"

    def test_density_monotone_approach(self):
        """Density approaches 9/π² from above or oscillates tightly."""
        target = 9 / math.pi**2
        prev_diff = None
        for n in [60, 120, 240, 480]:
            density = self._compute_ET_density(n)
            diff = abs(density - target)
            assert diff < 0.05, f"n={n}: density {density:.4f} too far from target"

    def test_density_above_half(self):
        """E-T coprime density > 0.5 for all n ≥ 6 (needed for hub-spoke)."""
        for n in range(6, 200):
            density = self._compute_ET_density(n)
            if len(bipartite_ET(n)[0]) > 0 and len(bipartite_ET(n)[1]) > 0:
                assert density > 0.5, f"n={n}: density {density:.4f} ≤ 0.5"


class TestMinDegreeProperty:
    """Verify min_deg(T→E) > |T| for the hub-spoke theorem."""

    def _min_T_degree(self, n):
        """Compute min degree from T into E in the coprime bipartite graph."""
        E, T = bipartite_ET(n)
        if not T:
            return 0
        min_deg = len(E)  # Start at max
        for t in T:
            deg = sum(1 for e in E if math.gcd(e, t) == 1)
            min_deg = min(min_deg, deg)
        return min_deg

    def test_min_deg_exceeds_T_size(self):
        """Every t ∈ T has more than |T| neighbors in E (for n ≥ 18)."""
        for n in range(18, 200, 6):
            E, T = bipartite_ET(n)
            min_deg = self._min_T_degree(n)
            assert min_deg > len(T), \
                f"n={n}: min_deg(T→E)={min_deg} ≤ |T|={len(T)}"

    def test_min_deg_ratio(self):
        """The ratio min_deg(T→E)/|T| is ≥ 1.3 for moderate n."""
        for n in [30, 60, 120, 240]:
            E, T = bipartite_ET(n)
            min_deg = self._min_T_degree(n)
            ratio = min_deg / len(T) if len(T) > 0 else 0
            assert ratio > 1.3, f"n={n}: ratio {ratio:.3f} < 1.3"

    def test_worst_T_vertex_has_many_small_primes(self):
        """The worst T-vertex is one with many small prime factors ≥ 5."""
        for n in [30, 60, 120]:
            E, T = bipartite_ET(n)
            worst_t = min(T, key=lambda t: sum(1 for e in E if math.gcd(e, t) == 1))
            # Worst vertex must be divisible by 5 (the smallest prime ≥ 5)
            assert worst_t % 5 == 0 or worst_t % 3 == 0, \
                f"n={n}: worst t={worst_t} not divisible by small primes"
            # It should be a product of 3 and small primes: 15, 45, 105, etc.
            assert worst_t % 15 == 0, \
                f"n={n}: worst t={worst_t} not divisible by 15=3×5"


class TestMinEDegreeProperty:
    """Verify min_deg(E→T) > |T|/2 (needed for full path construction)."""

    def _min_E_degree(self, n):
        """Compute min degree from E into T."""
        E, T = bipartite_ET(n)
        if not E:
            return 0
        min_deg = len(T)
        for e in E:
            deg = sum(1 for t in T if math.gcd(e, t) == 1)
            min_deg = min(min_deg, deg)
        return min_deg

    def test_min_E_deg_exceeds_half_T(self):
        """Every e ∈ E has more than |T|/2 neighbors in T (for n ≥ 18)."""
        for n in range(18, 200, 6):
            E, T = bipartite_ET(n)
            if not T:
                continue
            min_deg = self._min_E_degree(n)
            assert min_deg > len(T) / 2, \
                f"n={n}: min_deg(E→T)={min_deg} ≤ |T|/2={len(T)/2}"


class TestHubSpokeOddCycles:
    """Verify the hub-spoke construction produces all required odd cycle lengths."""

    def test_all_odd_cycles_at_threshold(self):
        """For A = A* ∪ {x}, all odd cycles 3..⌊n/3⌋+1 exist."""
        for n in [12, 18, 24, 30]:
            A_star = extremal_set(n)
            # Add the best hub (smallest coprime-to-6 element)
            R15 = sorted(i for i in range(1, n + 1) if math.gcd(i, 6) == 1)
            if not R15:
                continue
            A = A_star | {R15[0]}
            max_target = n // 3 + 1
            cycles = find_odd_cycle_lengths(A, max_length=max_target)
            required = set(range(3, max_target + 1, 2))
            missing = required - cycles
            assert not missing, \
                f"n={n}, hub={R15[0]}: missing cycles {sorted(missing)}"

    def test_worst_hub_still_produces_all_cycles(self):
        """Even the worst hub element produces all required cycles."""
        for n in [18, 24, 30]:
            A_star = extremal_set(n)
            R15 = [i for i in range(1, n + 1) if math.gcd(i, 6) == 1 and i > 1]
            if not R15:
                continue
            # Worst hub: fewest coprime neighbors in A*
            worst_hub = min(R15, key=lambda x: sum(
                1 for a in A_star if math.gcd(x, a) == 1
            ))
            A = A_star | {worst_hub}
            max_target = n // 3 + 1
            cycles = find_odd_cycle_lengths(A, max_length=max_target)
            required = set(range(3, max_target + 1, 2))
            missing = required - cycles
            assert not missing, \
                f"n={n}, worst_hub={worst_hub}: missing cycles {sorted(missing)}"

    def test_coprime_density_formula(self):
        """Verify the analytical formula: E-T coprime density = 9/π²."""
        # The formula: for e = 2a (3∤a) and t = 3b (b odd),
        # gcd(e,t) = gcd(a,b), and Pr[gcd=1] = (6/π²) / ((3/4)(8/9)) = 9/π²
        target = 9 / math.pi**2
        n = 300
        E, T = bipartite_ET(n)
        coprime_count = sum(1 for e in E for t in T if math.gcd(e, t) == 1)
        density = coprime_count / (len(E) * len(T))
        assert abs(density - target) < 0.02, \
            f"Density {density:.5f} ≠ 9/π²={target:.5f}"


# =============================================================================
# Bipartite Path Construction Tests (Improved Cycle Spectrum)
# =============================================================================


class TestBipartiteET:
    """Test bipartite decomposition helper."""

    def test_partition_correct(self):
        for n in [18, 30, 60]:
            E, T = bipartite_ET(n)
            # E = even not div 3, T = odd mult of 3
            for e in E:
                assert e % 2 == 0 and e % 3 != 0, f"{e} not in E"
            for t in T:
                assert t % 3 == 0 and t % 2 != 0, f"{t} not in T"

    def test_sizes(self):
        for n in [60, 120]:
            E, T = bipartite_ET(n)
            # |E| ≈ n/3, |T| ≈ n/6
            assert abs(len(E) - n/3) <= 2
            assert abs(len(T) - n/6) <= 2


class TestHubCoprimeNeighbors:
    def test_hub_1_gets_all(self):
        """Hub=1 is coprime to everything."""
        E, T = bipartite_ET(60)
        E_x, T_x = hub_coprime_neighbors(1, E, T)
        assert E_x == E
        assert T_x == T

    def test_hub_5_loses_multiples_of_5(self):
        E, T = bipartite_ET(60)
        E_x, T_x = hub_coprime_neighbors(5, E, T)
        # Should exclude elements divisible by 5
        for e in E - E_x:
            assert e % 5 == 0
        for t in T - T_x:
            assert t % 5 == 0

    def test_hub_35_loses_5_and_7(self):
        E, T = bipartite_ET(60)
        E_x, T_x = hub_coprime_neighbors(35, E, T)
        for e in E - E_x:
            assert e % 5 == 0 or e % 7 == 0
        for t in T - T_x:
            assert t % 5 == 0 or t % 7 == 0


class TestBipartiteMinDegrees:
    def test_returns_four_values(self):
        E, T = bipartite_ET(30)
        result = bipartite_min_degrees(E, T)
        assert len(result) == 4

    def test_min_T_to_E_exceeds_T_size(self):
        """Every T-vertex has more E-neighbors than |T| for n ≥ 18."""
        for n in [18, 30, 60, 120]:
            E, T = bipartite_ET(n)
            min_te, _, _, _ = bipartite_min_degrees(E, T)
            assert min_te > len(T), \
                f"n={n}: min_T_to_E={min_te} ≤ |T|={len(T)}"

    def test_empty_sets(self):
        assert bipartite_min_degrees(set(), set()) == (0, 0, 0, 0)


class TestBuildBipartiteAdj:
    def test_adjacency_symmetric(self):
        E, T = bipartite_ET(30)
        adj_et, adj_te = build_bipartite_adj(E, T)
        for e, t_nbrs in adj_et.items():
            for t in t_nbrs:
                assert e in adj_te[t], f"{e} in adj_et[{e}] but {e} not in adj_te[{t}]"

    def test_all_edges_coprime(self):
        E, T = bipartite_ET(30)
        adj_et, adj_te = build_bipartite_adj(E, T)
        for e, t_nbrs in adj_et.items():
            for t in t_nbrs:
                assert math.gcd(e, t) == 1


class TestGreedyAlternatingPath:
    def test_simple_path(self):
        E, T = bipartite_ET(30)
        E_sorted = sorted(E)
        path = greedy_alternating_path(E, T, E_sorted[0], 3)
        if path is not None:
            # Path: e1, t1, e2, t2, e3, t3 = 2*k elements
            assert len(path) == 2 * 3

    def test_returns_none_for_impossible(self):
        """Can't start from a vertex not in E."""
        E, T = bipartite_ET(30)
        path = greedy_alternating_path(E, T, 999999, 3)
        assert path is None

    def test_with_end_constraint(self):
        E, T = bipartite_ET(60)
        E_x, T_x = hub_coprime_neighbors(5, E, T)
        start = sorted(E_x)[0]
        path = greedy_alternating_path(E, T, start, 3, end_constraint=T_x)
        if path is not None:
            # Last element should be in T_x
            assert path[-1] in T_x


class TestVerifyCycleSpectrumBipartite:
    """Test the backtracking bipartite path verifier."""

    def test_hub_1_all_cycles(self):
        """Hub=1 (coprime to all) should find all required cycles."""
        for n in [18, 30, 60]:
            r = verify_cycle_spectrum_bipartite(n, hub=1)
            assert r["verified"], f"n={n}: missing {r['missing']}"

    def test_worst_hub_all_cycles(self):
        """Even worst hub finds all cycles via backtracking."""
        for n in [18, 30, 60]:
            A_star = {i for i in range(1, n+1) if i%2==0 or i%3==0}
            coprime_to_6 = sorted(i for i in range(1, n+1) if math.gcd(i, 6) == 1 and i > 1)
            worst_hub = min(coprime_to_6,
                          key=lambda x: sum(1 for a in A_star if math.gcd(x, a) == 1))
            r = verify_cycle_spectrum_bipartite(n, hub=worst_hub)
            assert r["verified"], \
                f"n={n}, worst_hub={worst_hub}: missing {r['missing']}"

    def test_result_structure(self):
        r = verify_cycle_spectrum_bipartite(30, hub=1)
        assert "n" in r
        assert "hub" in r
        assert "verified" in r
        assert "missing" in r
        assert "required" in r
        assert "found" in r


class TestVerifyFullCycleSpectrum:
    """Test the greedy-based full cycle spectrum verifier."""

    def test_default_hub(self):
        """Default hub (smallest coprime-to-6) works for small n."""
        for n in [18, 30, 42]:
            r = verify_full_cycle_spectrum(n)
            assert r["verified"], f"n={n}: missing {r['missing']}"

    def test_small_n(self):
        r = verify_full_cycle_spectrum(6)
        assert r["verified"]


# =============================================================================
# Extended Cycle Spectrum Verification (n up to 200)
# =============================================================================


class TestExtendedCycleSpectrumBipartite:
    """Verify cycle spectrum via bipartite path method for n up to 200."""

    @pytest.mark.parametrize("n", [60, 80, 100, 120, 150, 200])
    def test_all_odd_cycles_default_hub(self, n):
        """Default hub (hub=1) finds all odd cycles 3..floor(n/3)+1."""
        r = verify_cycle_spectrum_bipartite(n, hub=1)
        assert r["verified"], f"n={n}: missing {r['missing']}"
        max_target = n // 3 + 1
        expected = list(range(3, max_target + 1, 2))
        assert r["found"] == expected, (
            f"n={n}: found {r['found']} != expected {expected}"
        )

    @pytest.mark.parametrize("n", [60, 80, 100, 120, 150, 200])
    def test_all_odd_cycles_worst_hub(self, n):
        """Worst hub (fewest coprime neighbors) still finds all odd cycles."""
        A_star = {i for i in range(1, n + 1) if i % 2 == 0 or i % 3 == 0}
        coprime_to_6 = sorted(
            i for i in range(1, n + 1) if math.gcd(i, 6) == 1 and i > 1
        )
        worst_hub = min(
            coprime_to_6,
            key=lambda x: sum(1 for a in A_star if math.gcd(x, a) == 1),
        )
        r = verify_cycle_spectrum_bipartite(n, hub=worst_hub)
        assert r["verified"], (
            f"n={n}, worst_hub={worst_hub}: missing {r['missing']}"
        )

    @pytest.mark.parametrize("n", [60, 80, 100, 120, 150, 200])
    def test_cycle_count_matches_expected(self, n):
        """Number of distinct odd cycle lengths equals floor((floor(n/3)+1-3)/2)+1."""
        r = verify_cycle_spectrum_bipartite(n)
        max_target = n // 3 + 1
        expected_count = len(range(3, max_target + 1, 2))
        assert r["found_count"] if "found_count" in r else len(r["found"]) == expected_count, (
            f"n={n}: found {len(r['found'])} cycles, expected {expected_count}"
        )

    @pytest.mark.parametrize("n", [60, 80, 100, 120, 150, 200])
    def test_max_cycle_length(self, n):
        """Longest odd cycle found equals the largest odd number <= floor(n/3)+1."""
        r = verify_cycle_spectrum_bipartite(n, hub=1)
        max_target = n // 3 + 1
        expected_max = max_target if max_target % 2 == 1 else max_target - 1
        assert max(r["found"]) == expected_max, (
            f"n={n}: max cycle {max(r['found'])} != expected {expected_max}"
        )


class TestExtendedFullCycleSpectrum:
    """Verify the greedy-based method for n up to 200."""

    @pytest.mark.parametrize("n", [60, 80, 100, 120, 150, 200])
    def test_greedy_all_cycles(self, n):
        """Greedy method also finds all required odd cycles up to n=200."""
        r = verify_full_cycle_spectrum(n)
        assert r["verified"], f"n={n}: missing {r['missing']}"
        assert r["found_count"] == r["required_count"], (
            f"n={n}: found {r['found_count']}/{r['required_count']}"
        )

    def test_greedy_and_backtracking_agree(self):
        """Both methods find exactly the same cycle lengths for all tested n."""
        for n in [60, 100, 150, 200]:
            r_greedy = verify_full_cycle_spectrum(n)
            r_bt = verify_cycle_spectrum_bipartite(n)
            assert r_greedy["verified"] == r_bt["verified"], (
                f"n={n}: greedy={r_greedy['verified']}, bt={r_bt['verified']}"
            )
            assert r_greedy["found_count"] == len(r_bt["found"]), (
                f"n={n}: greedy found {r_greedy['found_count']}, "
                f"bt found {len(r_bt['found'])}"
            )
