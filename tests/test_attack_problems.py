"""Tests for attack_problems.py — Systematic problem screening and computational attacks."""
import math
import pytest

from attack_problems import (
    # Primitives
    mobius,
    sieve_primes,
    coprime_pair_count,
    is_sidon,
    difference_set,
    is_sum_free_int,
    fourier_spectrum,
    schur_count_fourier,
    is_primitive,
    coprime_graph_adj,
    is_bipartite,
    greedy_sum_free_coloring,
    # Screening
    load_problems,
    screen_problems,
    TECHNIQUE_MAP,
    # Experiments
    experiment_sidon_43,
    experiment_coprime_density_883,
    experiment_schur_fourier_483,
    experiment_sidon_b2_14,
    experiment_ramsey_coprime_483b,
    experiment_primitive_530,
    experiment_ap_density_3,
    experiment_chromatic_74,
    experiment_sidon_30,
    experiment_turan_146,
    experiment_additive_1,
    experiment_primitive_143,
    experiment_graph_cycles_60,
    experiment_sidon_39,
    experiment_additive_basis_9,
    # Report
    generate_report,
)


# ── Primitive function tests ──────────────────────────────────────


class TestMobius:
    """Test the Mobius function."""

    def test_mobius_1(self):
        assert mobius(1) == 1

    def test_mobius_prime(self):
        assert mobius(2) == -1
        assert mobius(3) == -1
        assert mobius(5) == -1

    def test_mobius_prime_squared(self):
        assert mobius(4) == 0
        assert mobius(9) == 0
        assert mobius(25) == 0

    def test_mobius_product_two_primes(self):
        assert mobius(6) == 1   # 2*3
        assert mobius(10) == 1  # 2*5
        assert mobius(15) == 1  # 3*5

    def test_mobius_product_three_primes(self):
        assert mobius(30) == -1  # 2*3*5


class TestSievePrimes:
    """Test prime sieve."""

    def test_primes_up_to_10(self):
        assert sieve_primes(10) == [2, 3, 5, 7]

    def test_primes_up_to_1(self):
        assert sieve_primes(1) == []

    def test_primes_up_to_2(self):
        assert sieve_primes(2) == [2]

    def test_primes_count_100(self):
        assert len(sieve_primes(100)) == 25


class TestCoprimePairCount:
    """Test coprime pair counting via Mobius inversion."""

    def test_empty(self):
        assert coprime_pair_count(set()) == 0

    def test_singleton(self):
        assert coprime_pair_count({5}) == 0

    def test_coprime_pair(self):
        assert coprime_pair_count({2, 3}) == 1

    def test_non_coprime_pair(self):
        assert coprime_pair_count({4, 6}) == 0

    def test_primes_all_coprime(self):
        """All pairs of distinct primes are coprime."""
        P = {2, 3, 5, 7}
        expected = len(P) * (len(P) - 1) // 2
        assert coprime_pair_count(P) == expected

    def test_known_set(self):
        # {1, 2, 3, 4}: pairs (1,2),(1,3),(1,4),(2,3),(3,4) = 5 coprime pairs
        A = {1, 2, 3, 4}
        # (1,2)=1, (1,3)=1, (1,4)=1, (2,3)=1, (2,4)=2, (3,4)=1
        assert coprime_pair_count(A) == 5


class TestIsSidon:
    """Test Sidon set validation."""

    def test_empty(self):
        assert is_sidon(set())

    def test_singleton(self):
        assert is_sidon({7})

    def test_valid_sidon(self):
        assert is_sidon({0, 1, 3})

    def test_invalid_sidon(self):
        assert not is_sidon({0, 1, 2, 3})

    def test_singer_q2(self):
        assert is_sidon({1, 2, 4})


class TestDifferenceSet:
    """Test difference set computation."""

    def test_singleton(self):
        assert difference_set({5}) == {0}

    def test_pair(self):
        assert difference_set({1, 4}) == {0, 3, -3}


class TestIsSumFreeInt:
    """Test sum-free check over integers."""

    def test_empty(self):
        assert is_sum_free_int(set())

    def test_singleton(self):
        assert is_sum_free_int({5})

    def test_sum_free(self):
        # Odd numbers up to 9: {1,3,5,7,9}. 1+3=4 not in set, etc.
        # Actually 3+5=8 not in set, 1+7=8 not in set. Sum-free.
        assert is_sum_free_int({1, 3, 5, 7, 9})

    def test_not_sum_free(self):
        # {1, 2, 3}: 1+2=3
        assert not is_sum_free_int({1, 2, 3})


class TestFourierSpectrum:
    """Test Fourier spectrum computation."""

    def test_full_set(self):
        """f_hat(0) = |A| for full set."""
        N = 10
        A = set(range(N))
        spec = fourier_spectrum(A, N)
        # DC component should be N
        dc = next(m for r, m in spec if r == 0)
        assert abs(dc - N) < 1e-10

    def test_singleton(self):
        """f_hat(r) = 1 for all r when A = {0}."""
        N = 5
        A = {0}
        spec = fourier_spectrum(A, N)
        for r, m in spec:
            assert abs(m - 1.0) < 1e-10


class TestSchurCountFourier:
    """Test Schur triple counting via Fourier."""

    def test_no_triples(self):
        """Sum-free set should have 0 Schur triples."""
        N = 10
        A = {1, 4}  # sum-free: 1+1=2, 1+4=5, 4+4=8 -- none in A
        count = schur_count_fourier(A, N)
        assert abs(count) < 1.0

    def test_with_triples(self):
        """Set with Schur triples: {1, 2, 3} has 1+2=3."""
        N = 10
        A = {1, 2, 3}
        count = schur_count_fourier(A, N)
        assert count > 0


class TestIsPrimitive:
    """Test primitive set validation."""

    def test_primes(self):
        assert is_primitive({2, 3, 5, 7})

    def test_not_primitive(self):
        assert not is_primitive({2, 4})  # 2 | 4

    def test_top_layer(self):
        T = set(range(6, 11))  # {6,7,8,9,10}
        assert is_primitive(T)


class TestCoprimeGraph:
    """Test coprime graph adjacency and bipartiteness."""

    def test_adj_small(self):
        adj = coprime_graph_adj({2, 3, 4})
        # (2,3) coprime, (3,4) coprime, (2,4) not coprime
        assert 3 in adj[2]
        assert 4 in adj[3]
        assert 4 not in adj.get(2, set())

    def test_bipartite_even_numbers(self):
        """Even numbers form bipartite coprime graph."""
        A = {2, 4, 6, 8, 10}
        adj = coprime_graph_adj(A)
        # No coprime pairs among even numbers > 2
        # (2,4)=2, (2,6)=2, etc. All share factor 2. Actually gcd(4,6)=2.
        # So no edges at all -- trivially bipartite.
        assert is_bipartite(adj, A)


class TestGreedySumFreeColoring:
    """Test greedy sum-free coloring."""

    def test_k1_s1(self):
        """S(1) = 1: can color {1} with 1 color sum-free."""
        coloring = greedy_sum_free_coloring(1, 1)
        assert len(coloring) == 1

    def test_k2_small(self):
        """Greedy 2-coloring of {1,2,3} should be sum-free."""
        coloring = greedy_sum_free_coloring(3, 2)
        colors = [set(), set()]
        for i, c in enumerate(coloring):
            colors[c].add(i + 1)
        # At N=3 with k=2, sum-free coloring exists: {1,2} and {3}, or {1,4} and {2,3}
        for C in colors:
            assert is_sum_free_int(C), f"Color class {C} not sum-free"

    def test_returns_correct_length(self):
        """Coloring should have length N."""
        coloring = greedy_sum_free_coloring(10, 3)
        assert len(coloring) == 10
        for c in coloring:
            assert 0 <= c < 3


# ── Screening tests ──────────────────────────────────────────────


class TestScreening:
    """Test problem screening pipeline."""

    def test_load_problems(self):
        problems = load_problems()
        assert len(problems) > 1000

    def test_screen_returns_sorted(self):
        problems = load_problems()
        scored = screen_problems(problems)
        assert len(scored) > 0
        # Check sorted descending by score
        for i in range(len(scored) - 1):
            assert scored[i]["score"] >= scored[i + 1]["score"]

    def test_technique_map_keys(self):
        for tech_id, tech in TECHNIQUE_MAP.items():
            assert "required" in tech
            assert "name" in tech
            assert "weight" in tech
            assert isinstance(tech["required"], set)

    def test_open_problems_count(self):
        problems = load_problems()
        open_count = sum(
            1 for p in problems if p.get("status", {}).get("state") == "open"
        )
        assert open_count == 636

    def test_sidon_problems_match(self):
        """Problems tagged 'sidon sets' should match our Sidon technique."""
        problems = load_problems()
        scored = screen_problems(problems)
        sidon_scored = [
            s for s in scored
            if "Sidon disjoint framework" in s["matches"]
        ]
        assert len(sidon_scored) > 0


# ── Experiment tests (lightweight) ───────────────────────────────


class TestExperimentSidon43:
    """Test Sidon disjoint differences experiment."""

    def test_runs(self):
        result = experiment_sidon_43(N_values=[5, 6, 7, 8])
        assert result["status"] if "status" in result else True
        assert result["problem"] == 43
        assert len(result["data"]) == 4

    def test_data_structure(self):
        result = experiment_sidon_43(N_values=[5])
        d = result["data"][0]
        assert "N" in d
        assert "f_N" in d
        assert "|A|" in d
        assert "holds" in d

    def test_small_cases_hold(self):
        """Conjecture should hold (with O(1) slack) for very small N."""
        result = experiment_sidon_43(N_values=[5, 6, 7])
        for d in result["data"]:
            assert d["holds"], f"Conjecture failed at N={d['N']}"


class TestExperimentCoprime883:
    """Test coprime cycle forcing experiment."""

    def test_runs(self):
        result = experiment_coprime_density_883()
        assert result["problem"] == 883
        assert len(result["data"]) > 0

    def test_extremal_bipartite(self):
        """Extremal set A* should be bipartite."""
        result = experiment_coprime_density_883()
        for d in result["data"]:
            assert d["bipartite(A*)"] is True


class TestExperimentSchur483:
    """Test Schur number Fourier experiment."""

    def test_runs(self):
        result = experiment_schur_fourier_483()
        assert result["problem"] == 483
        assert "growth_ratios" in result

    def test_known_schur_values(self):
        result = experiment_schur_fourier_483()
        known = {1: 1, 2: 4, 3: 13, 4: 44}
        for d in result["data"]:
            assert d["S(k)"] == known[d["k"]]


class TestExperimentAdditiveBasis9:
    """Test prime + power of 2 experiment."""

    def test_runs(self):
        result = experiment_additive_basis_9()
        assert result["problem"] == 9
        assert len(result["data"]) > 0

    def test_small_all_representable(self):
        """All odd numbers up to 100 should be representable."""
        result = experiment_additive_basis_9()
        d100 = next(d for d in result["data"] if d["N"] == 100)
        assert d100["not_representable_count"] == 0


class TestExperimentPrimitive530:
    """Test primitive set Erdos sum experiment."""

    def test_runs(self):
        result = experiment_primitive_530()
        assert result["problem"] == 530
        assert "max_erdos_sum" in result

    def test_sum_bounded(self):
        """Erdos sum should be bounded (< 2 for all constructions)."""
        result = experiment_primitive_530()
        assert result["max_erdos_sum"] < 2.0


class TestExperimentTuran146:
    """Test Turan number experiment."""

    def test_runs(self):
        result = experiment_turan_146()
        assert result["problem"] == 146

    def test_bipartite_achieves_turan(self):
        """Bipartite graph achieves Turan number for C_5."""
        result = experiment_turan_146()
        for d in result["data"]:
            assert d["ratio_to_turan"] == 1.0


class TestExperimentAP3:
    """Test 3-AP free set experiment."""

    def test_runs(self):
        result = experiment_ap_density_3()
        assert result["problem"] == 3
        assert len(result["data"]) > 0

    def test_density_decreasing(self):
        """r_3(N)/N should decrease on average."""
        result = experiment_ap_density_3()
        data = result["data"]
        first_density = data[0]["r_3/N"]
        last_density = data[-1]["r_3/N"]
        assert last_density < first_density


class TestExperimentAdditive1:
    """Test Erdos-Straus density experiment."""

    def test_runs(self):
        result = experiment_additive_1()
        assert result["problem"] == 1

    def test_sum_grows(self):
        """Sum for full set should grow with N."""
        result = experiment_additive_1()
        sums = []
        for d in result["data"]:
            s = d["constructions"]["full_[N]"]["sum_1/C(a,2)"]
            sums.append(s)
        # Should be increasing
        for i in range(len(sums) - 1):
            assert sums[i + 1] > sums[i]


# ── Report generation test ───────────────────────────────────────


class TestReport:
    """Test report generation."""

    def test_generate_report(self):
        scored = [
            {"number": "1", "tags": ["number theory"], "score": 5.0,
             "raw_score": 5.0, "matches": ["Fourier"], "prize": "no", "oeis": []},
        ]
        results = [
            {"experiment_name": "Test", "status": "completed",
             "problem": 1, "description": "test",
             "data": [{"N": 10, "result": 42}],
             "conclusion": "Test passed."},
        ]
        report = generate_report(scored, results)
        assert "# Erdos Problems Attack Report" in report
        assert "Test passed." in report
        assert "## Part 1" in report
        assert "## Part 2" in report
        assert "## Part 3" in report
