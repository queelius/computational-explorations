"""Tests for coprime_perfectness_proof.py — Weak perfectness of integer coprime graphs."""

import math
import pytest

from coprime_perfectness_proof import (
    sieve_primes,
    sieve_smallest_prime_factor,
    is_prime,
    coprime_graph_adj,
    maximum_clique,
    verify_is_clique,
    clique_number,
    verify_clique_is_maximum,
    smallest_prime_factor_coloring,
    verify_proper_coloring,
    chromatic_number_upper_bound,
    count_colors_used,
    verify_weak_perfectness,
    find_odd_hole,
    find_odd_antihole,
    check_induced_subgraph_perfectness,
    check_random_induced_subgraphs,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def spf_100():
    """Precomputed smallest-prime-factor table up to 100."""
    return sieve_smallest_prime_factor(100)


# ---------------------------------------------------------------------------
# Sieve utilities
# ---------------------------------------------------------------------------

class TestSievePrimes:
    def test_below_2(self):
        assert sieve_primes(0) == []
        assert sieve_primes(1) == []

    def test_small(self):
        assert sieve_primes(10) == [2, 3, 5, 7]

    def test_pi_30(self):
        """pi(30) = 10."""
        assert len(sieve_primes(30)) == 10

    def test_pi_100(self):
        """pi(100) = 25."""
        assert len(sieve_primes(100)) == 25

    def test_all_prime(self):
        for p in sieve_primes(50):
            assert all(p % d != 0 for d in range(2, p))


class TestSieveSmallestPrimeFactor:
    def test_spf_1(self):
        spf = sieve_smallest_prime_factor(10)
        assert spf[1] == 1

    def test_spf_primes(self):
        spf = sieve_smallest_prime_factor(20)
        for p in [2, 3, 5, 7, 11, 13, 17, 19]:
            assert spf[p] == p, f"spf({p}) should be {p}"

    def test_spf_composites(self):
        spf = sieve_smallest_prime_factor(30)
        assert spf[4] == 2
        assert spf[6] == 2
        assert spf[9] == 3
        assert spf[15] == 3
        assert spf[25] == 5

    def test_spf_divides(self):
        """spf(m) always divides m."""
        spf = sieve_smallest_prime_factor(100)
        for m in range(2, 101):
            assert m % spf[m] == 0


class TestIsPrime:
    def test_primes(self, spf_100):
        for p in [2, 3, 5, 7, 97]:
            assert is_prime(p, spf_100), f"{p} should be prime"

    def test_composites(self, spf_100):
        for c in [4, 6, 9, 15, 100]:
            assert not is_prime(c, spf_100), f"{c} should not be prime"

    def test_one_not_prime(self, spf_100):
        assert not is_prime(1, spf_100)


# ---------------------------------------------------------------------------
# Coprime graph construction
# ---------------------------------------------------------------------------

class TestCoprimeGraphAdj:
    def test_n3_complete(self):
        """G(3) is complete: 1-2, 1-3, 2-3 all coprime."""
        adj = coprime_graph_adj(3)
        assert adj[1] == {2, 3}
        assert adj[2] == {1, 3}
        assert adj[3] == {1, 2}

    def test_n4_missing_edge(self):
        """G(4) is missing the edge 2-4 (gcd = 2)."""
        adj = coprime_graph_adj(4)
        assert 4 not in adj[2]
        assert 2 not in adj[4]

    def test_vertex_1_universal(self):
        """Vertex 1 is adjacent to every other vertex."""
        for n in [5, 10, 20]:
            adj = coprime_graph_adj(n)
            assert adj[1] == set(range(2, n + 1))

    def test_symmetry(self):
        adj = coprime_graph_adj(10)
        for a in range(1, 11):
            for b in adj[a]:
                assert a in adj[b], f"Adjacency not symmetric: {a}-{b}"


# ---------------------------------------------------------------------------
# Clique number: omega(G(n)) = 1 + pi(n)
# ---------------------------------------------------------------------------

class TestMaximumClique:
    def test_clique_structure(self):
        """Maximum clique is {1} union primes."""
        assert maximum_clique(5) == [1, 2, 3, 5]
        assert maximum_clique(10) == [1, 2, 3, 5, 7]

    def test_clique_size(self):
        for n in [5, 10, 20, 50]:
            clique = maximum_clique(n)
            assert len(clique) == 1 + len(sieve_primes(n))


class TestVerifyIsClique:
    def test_primes_coprime(self):
        """All primes are pairwise coprime."""
        assert verify_is_clique([2, 3, 5, 7, 11, 13])

    def test_with_1(self):
        assert verify_is_clique([1, 2, 3, 5, 7])

    def test_non_clique(self):
        """4 and 6 share factor 2."""
        assert not verify_is_clique([4, 6, 7])

    def test_singleton(self):
        assert verify_is_clique([42])

    def test_empty(self):
        assert verify_is_clique([])


class TestCliqueNumber:
    @pytest.mark.parametrize("n,expected_pi", [
        (1, 0), (2, 1), (3, 2), (5, 3), (10, 4), (20, 8), (30, 10), (100, 25),
    ])
    def test_clique_number_values(self, n, expected_pi):
        assert clique_number(n) == 1 + expected_pi


class TestVerifyCliqueIsMaximum:
    @pytest.mark.parametrize("n", [5, 10, 20, 50, 100])
    def test_clique_maximality(self, n):
        """No composite can extend the canonical clique."""
        assert verify_clique_is_maximum(n)


# ---------------------------------------------------------------------------
# Explicit coloring: chi(G(n)) <= 1 + pi(n)
# ---------------------------------------------------------------------------

class TestSmallestPrimeFactorColoring:
    def test_vertex_1_color_0(self):
        coloring = smallest_prime_factor_coloring(10)
        assert coloring[1] == 0

    def test_primes_unique_colors(self):
        coloring = smallest_prime_factor_coloring(20)
        primes = sieve_primes(20)
        prime_colors = [coloring[p] for p in primes]
        assert len(set(prime_colors)) == len(primes), "Primes must get distinct colors"

    def test_composite_inherits_spf_color(self):
        """Each composite gets the color of its smallest prime factor."""
        n = 30
        coloring = smallest_prime_factor_coloring(n)
        spf = sieve_smallest_prime_factor(n)
        for m in range(4, n + 1):
            if spf[m] != m:  # composite
                assert coloring[m] == coloring[spf[m]], (
                    f"Composite {m} with spf={spf[m]} should have "
                    f"color {coloring[spf[m]]}, got {coloring[m]}"
                )

    def test_color_range(self):
        """All colors are in {0, 1, ..., pi(n)}."""
        for n in [10, 30, 50]:
            coloring = smallest_prime_factor_coloring(n)
            pi_n = len(sieve_primes(n))
            for v, c in coloring.items():
                assert 0 <= c <= pi_n, f"Color {c} out of range for vertex {v}"


class TestVerifyProperColoring:
    @pytest.mark.parametrize("n", [5, 10, 20, 50, 100])
    def test_proper_for_spf_coloring(self, n):
        """The spf coloring is proper for all tested n."""
        coloring = smallest_prime_factor_coloring(n)
        is_proper, witness = verify_proper_coloring(n, coloring)
        assert is_proper, f"Improper at n={n}: vertices {witness}"

    def test_detects_improper(self):
        """Giving everything color 0 is NOT proper (e.g. 2,3 coprime)."""
        bad_coloring = {v: 0 for v in range(1, 6)}
        is_proper, witness = verify_proper_coloring(5, bad_coloring)
        assert not is_proper
        a, b = witness
        assert math.gcd(a, b) == 1, "Witness should be a coprime pair"


class TestCountColorsUsed:
    @pytest.mark.parametrize("n", [5, 10, 20, 50, 100])
    def test_colors_equal_1_plus_pi(self, n):
        """Number of distinct colors equals 1 + pi(n)."""
        coloring = smallest_prime_factor_coloring(n)
        expected = 1 + len(sieve_primes(n))
        assert count_colors_used(coloring) == expected


class TestChromaticNumberUpperBound:
    def test_equals_clique_number(self):
        for n in [5, 10, 20, 50, 100]:
            assert chromatic_number_upper_bound(n) == clique_number(n)


# ---------------------------------------------------------------------------
# Full verification: chi = omega
# ---------------------------------------------------------------------------

class TestVerifyWeakPerfectness:
    @pytest.mark.parametrize("n", [5, 10, 20, 50, 100])
    def test_chi_equals_omega(self, n):
        """chi(G(n)) = omega(G(n)) = 1 + pi(n) for specific n values."""
        result = verify_weak_perfectness(n)
        assert result["chi_equals_omega"], (
            f"Weak perfectness FAILED at n={n}: {result}"
        )

    @pytest.mark.parametrize("n", [1, 2, 3, 4])
    def test_small_n(self, n):
        """Works correctly even for very small n."""
        result = verify_weak_perfectness(n)
        assert result["chi_equals_omega"]
        assert result["omega"] == 1 + len(sieve_primes(n))

    def test_result_structure(self):
        result = verify_weak_perfectness(10)
        expected_keys = {
            "n", "pi_n", "omega", "clique", "clique_valid",
            "clique_size", "clique_is_maximum", "coloring_proper",
            "improper_witness", "colors_used", "chi_upper_bound",
            "chi_equals_omega",
        }
        assert set(result.keys()) == expected_keys

    def test_all_n_up_to_30(self):
        """Exhaustive check matching the computational verification."""
        for n in range(1, 31):
            result = verify_weak_perfectness(n)
            assert result["chi_equals_omega"], f"Failed at n={n}"


# ---------------------------------------------------------------------------
# Strong perfectness investigation
# ---------------------------------------------------------------------------

class TestFindOddHole:
    @pytest.mark.parametrize("n", [10, 15, 20])
    def test_no_odd_hole(self, n):
        """No odd hole of length 5..11 found in G(n)."""
        hole = find_odd_hole(n, max_length=min(n, 11))
        assert hole is None, f"Odd hole found in G({n}): {hole}"

    def test_valid_hole_if_found(self):
        """If a hole is returned, verify it is indeed a chordless odd cycle."""
        hole = find_odd_hole(20, max_length=11)
        if hole is not None:
            k = len(hole)
            assert k % 2 == 1 and k >= 5
            # Check cycle edges exist and chords don't
            for i in range(k):
                j = (i + 1) % k
                assert math.gcd(hole[i], hole[j]) == 1, "Cycle edge missing"
            for i in range(k):
                for j in range(i + 2, k):
                    if j == (i - 1) % k:
                        continue
                    assert math.gcd(hole[i], hole[j]) != 1, "Chord exists"


class TestFindOddAntihole:
    @pytest.mark.parametrize("n", [10, 15, 20])
    def test_no_odd_antihole(self, n):
        """No odd antihole of length 5..11 found in complement of G(n)."""
        antihole = find_odd_antihole(n, max_length=min(n, 11))
        assert antihole is None, f"Odd antihole in G({n}): {antihole}"


class TestInducedSubgraphPerfectness:
    def test_primes_subset(self):
        """Induced subgraph on primes is a complete graph (trivially perfect)."""
        primes_10 = set(sieve_primes(10))  # {2,3,5,7}
        result = check_induced_subgraph_perfectness(10, primes_10)
        # All primes are pairwise coprime, so it's K_4: omega = chi = 4
        assert result["omega"] == 4
        assert result["weakly_perfect"]

    def test_even_numbers(self):
        """Induced subgraph on {2,4,6,8,10}: only 2 is coprime to odds,
        but within evens, consecutive edges are sparse."""
        evens = {2, 4, 6, 8, 10}
        result = check_induced_subgraph_perfectness(10, evens)
        assert result["weakly_perfect"]

    def test_full_graph(self):
        """Induced subgraph on all of [n] should be weakly perfect."""
        for n in [5, 8, 10]:
            result = check_induced_subgraph_perfectness(n, set(range(1, n + 1)))
            assert result["weakly_perfect"], f"G({n}) itself not weakly perfect"

    def test_singleton(self):
        result = check_induced_subgraph_perfectness(5, {3})
        assert result["omega"] == 1
        assert result["weakly_perfect"]

    def test_coprime_pair(self):
        result = check_induced_subgraph_perfectness(10, {4, 9})
        # gcd(4,9) = 1, so edge exists: K_2, omega = chi = 2
        assert result["omega"] == 2
        assert result["weakly_perfect"]

    def test_non_coprime_pair(self):
        result = check_induced_subgraph_perfectness(10, {4, 6})
        # gcd(4,6) = 2 > 1, no edge: two independent vertices, omega = chi = 1
        assert result["omega"] == 1
        assert result["weakly_perfect"]


class TestRandomInducedSubgraphs:
    @pytest.mark.parametrize("n", [10, 15, 20])
    def test_random_subgraphs_perfect(self, n):
        """Random induced subgraphs are all weakly perfect."""
        result = check_random_induced_subgraphs(
            n, num_trials=200, max_size=min(n, 12), seed=42
        )
        assert result["all_perfect"], (
            f"Found {result['num_failures']} non-perfect subgraphs of G({n}): "
            f"{result['failures'][:3]}"
        )


# ---------------------------------------------------------------------------
# Proof correctness: the four cases of the coloring argument
# ---------------------------------------------------------------------------

class TestColoringProofCases:
    """Directly verify each case in the proof that spf coloring is proper."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.n = 50
        self.coloring = smallest_prime_factor_coloring(self.n)
        self.spf = sieve_smallest_prime_factor(self.n)
        self.primes = set(sieve_primes(self.n))

    def test_case1_vertex_1(self):
        """Case 1: If a=1 and gcd(1,b)=1, then c(1)=0 != c(b) >= 1."""
        assert self.coloring[1] == 0
        for b in range(2, self.n + 1):
            assert self.coloring[b] >= 1, f"c({b}) should be >= 1"

    def test_case2_both_prime(self):
        """Case 2: Distinct primes get distinct colors."""
        prime_list = sorted(self.primes)
        for i in range(len(prime_list)):
            for j in range(i + 1, len(prime_list)):
                assert self.coloring[prime_list[i]] != self.coloring[prime_list[j]], (
                    f"Primes {prime_list[i]} and {prime_list[j]} have same color"
                )

    def test_case3_prime_composite(self):
        """Case 3: If prime p and composite b are coprime, c(p) != c(b)."""
        for p in sorted(self.primes):
            for b in range(4, self.n + 1):
                if b in self.primes:
                    continue
                if math.gcd(p, b) == 1:
                    assert self.coloring[p] != self.coloring[b], (
                        f"Prime {p} and composite {b} are coprime "
                        f"but have same color {self.coloring[p]}"
                    )

    def test_case3_mechanism(self):
        """The *reason* Case 3 works: gcd(p,b)=1 implies spf(b) != p."""
        for p in sorted(self.primes):
            for b in range(4, self.n + 1):
                if b in self.primes:
                    continue
                if math.gcd(p, b) == 1:
                    assert self.spf[b] != p, (
                        f"spf({b})={self.spf[b]} equals prime {p} "
                        f"but gcd({p},{b})=1"
                    )

    def test_case4_both_composite(self):
        """Case 4: If composites a,b are coprime, c(a) != c(b)."""
        composites = [m for m in range(4, self.n + 1) if m not in self.primes]
        for i in range(len(composites)):
            for j in range(i + 1, len(composites)):
                a, b = composites[i], composites[j]
                if math.gcd(a, b) == 1:
                    assert self.coloring[a] != self.coloring[b], (
                        f"Composites {a} and {b} are coprime "
                        f"but have same color {self.coloring[a]}"
                    )

    def test_case4_mechanism(self):
        """The *reason* Case 4 works: gcd(a,b)=1 implies spf(a) != spf(b)."""
        composites = [m for m in range(4, self.n + 1) if m not in self.primes]
        for i in range(len(composites)):
            for j in range(i + 1, len(composites)):
                a, b = composites[i], composites[j]
                if math.gcd(a, b) == 1:
                    assert self.spf[a] != self.spf[b], (
                        f"spf({a})={self.spf[a]}, spf({b})={self.spf[b]} "
                        f"are equal but gcd({a},{b})=1"
                    )
