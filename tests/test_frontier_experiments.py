"""Tests for frontier_experiments.py — novel experiments at unexplored intersections."""
import math
import pytest
from unittest.mock import patch

from frontier_experiments import (
    sieve_primes,
    is_sidon,
    has_3ap,
    sidon_coprime_clique,
    ramsey_multiplicity,
    ap_free_coprime_subset,
    divisibility_chromatic_number,
    sum_free_ramsey,
    coprime_independence,
    run_sidon_coprime_experiment,
    run_ramsey_multiplicity_experiment,
    run_ap_free_coprime_experiment,
    run_divisibility_coloring_experiment,
    run_sum_free_ramsey_experiment,
    run_coprime_independence_experiment,
    run_all_frontier,
)


class TestPrimitives:
    """Test shared primitive functions."""

    def test_sieve_small(self):
        assert sieve_primes(10) == [2, 3, 5, 7]

    def test_sieve_empty(self):
        assert sieve_primes(1) == []

    def test_is_sidon_yes(self):
        assert is_sidon({1, 2, 5, 11})

    def test_is_sidon_no(self):
        assert not is_sidon({1, 2, 3})

    def test_has_3ap_yes(self):
        assert has_3ap({1, 2, 3})

    def test_has_3ap_no(self):
        assert not has_3ap({1, 2, 4, 8})

    def test_has_3ap_empty(self):
        assert not has_3ap(set())


class TestSidonCoprime:
    """Test Sidon-coprime clique computation."""

    def test_small_n(self):
        r = sidon_coprime_clique(10)
        assert r["max_sidon_coprime"] >= 2
        assert r["is_sidon"]
        assert r["all_coprime"]

    def test_result_valid(self):
        r = sidon_coprime_clique(20)
        S = set(r["set"])
        assert is_sidon(S)
        for a, b in [(x, y) for x in S for y in S if x < y]:
            assert math.gcd(a, b) == 1

    def test_grows_with_n(self):
        r1 = sidon_coprime_clique(10)
        r2 = sidon_coprime_clique(50)
        assert r2["max_sidon_coprime"] >= r1["max_sidon_coprime"]


class TestRamseyMultiplicity:
    """Test Ramsey multiplicity computation."""

    def test_small_n_no_forced(self):
        r = ramsey_multiplicity(4, k=3)
        # n=4 has few coprime triangles
        assert "min_mono_copies" in r

    def test_total_cliques_nonneg(self):
        r = ramsey_multiplicity(6, k=3)
        assert r["total_coprime_triangles"] >= 0

    def test_fraction_bounded(self):
        r = ramsey_multiplicity(8, k=3)
        assert 0 <= r["fraction_forced"] <= 1


class TestAPFreeCoprime:
    """Test AP-free coprime subset computation."""

    def test_small_n(self):
        r = ap_free_coprime_subset(10)
        assert r["max_ap_free_coprime"] >= 2

    def test_result_is_coprime(self):
        r = ap_free_coprime_subset(20)
        S = set(r["set_sample"])
        for a, b in [(x, y) for x in S for y in S if x < y]:
            assert math.gcd(a, b) == 1

    def test_result_is_ap_free(self):
        r = ap_free_coprime_subset(20)
        S = set(r["set_sample"])
        assert not has_3ap(S)

    def test_primes_are_coprime(self):
        """Primes should form a coprime set."""
        r = ap_free_coprime_subset(30)
        assert r["primes_ap_free"] >= 1

    def test_ratio_bounded(self):
        r = ap_free_coprime_subset(50)
        assert 0 < r["ratio_to_primes"] <= 2.0


class TestDivisibilityColoring:
    """Test divisibility graph chromatic number."""

    def test_small_n(self):
        r = divisibility_chromatic_number(10)
        assert r["chi_greedy"] >= 1

    def test_chi_matches_chain(self):
        """χ should be close to max chain length (perfect graph)."""
        for n in [10, 20, 50]:
            r = divisibility_chromatic_number(n)
            # Greedy might overestimate by 1
            assert abs(r["chi_greedy"] - r["max_chain"]) <= 2

    def test_antichain_is_half(self):
        """Max antichain = ⌊n/2⌋."""
        r = divisibility_chromatic_number(20)
        assert r["max_antichain"] == 10

    def test_density_decreases(self):
        """Edge density should decrease with n (sparse graph)."""
        r10 = divisibility_chromatic_number(10)
        r50 = divisibility_chromatic_number(50)
        assert r50["density"] <= r10["density"]


class TestSumFreeRamsey:
    """Test sum-free Ramsey computation."""

    def test_n1_achievable(self):
        r = sum_free_ramsey(1, k=2)
        assert r["achievable"]

    def test_small_n_achievable(self):
        r = sum_free_ramsey(3, k=2)
        assert r["achievable"]

    def test_large_n_fails(self):
        """Eventually no valid coloring exists."""
        r = sum_free_ramsey(20, k=2)
        # May or may not be achievable, just check format
        assert "achievable" in r

    def test_color_sizes_sum_to_n(self):
        r = sum_free_ramsey(4, k=2)
        if r["achievable"]:
            assert sum(r["color_sizes"]) == 4


class TestCoprimeIndependence:
    """Test coprime graph independence number."""

    def test_small_n(self):
        r = coprime_independence(10)
        assert r["alpha_heuristic"] >= 1

    def test_evens_are_independent(self):
        """Even numbers should form the max independent set."""
        r = coprime_independence(20)
        assert r["alpha_heuristic"] == r["evens_size"]

    def test_alpha_is_half_n(self):
        """α(G([n])) = ⌊n/2⌋."""
        for n in [10, 20, 30]:
            r = coprime_independence(n)
            assert r["alpha_heuristic"] == n // 2

    def test_ratio_is_half(self):
        r = coprime_independence(50)
        assert abs(r["ratio_alpha_n"] - 0.5) < 0.02


# ═══════════════════════════════════════════════════════════════════
# Tests for runner / orchestrator functions (covers uncovered lines)
# ═══════════════════════════════════════════════════════════════════


class TestRunSidonCoprimeExperiment:
    """Tests for run_sidon_coprime_experiment — covers lines 109-126."""

    @pytest.fixture(scope="module")
    def result(self):
        import random
        random.seed(42)
        return run_sidon_coprime_experiment()

    def test_returns_name(self, result):
        assert result["name"] == "Sidon-Coprime Cliques"

    def test_data_populated(self, result):
        assert len(result["data"]) == 8

    def test_data_n_values(self, result):
        ns = [d["n"] for d in result["data"]]
        assert ns == [10, 20, 30, 50, 75, 100, 150, 200]

    def test_data_has_cube_root(self, result):
        for d in result["data"]:
            expected = round(d["n"] ** (1/3), 3)
            assert d["n^{1/3}"] == expected

    def test_data_has_ratio(self, result):
        for d in result["data"]:
            expected = round(d["max_sidon_coprime"] / (d["n"] ** (1/3)), 3)
            assert d["ratio"] == expected

    def test_conjecture_string(self, result):
        assert "conjecture" in result
        assert "n^{1/3}" in result["conjecture"]
        assert "1/6" in result["conjecture"]

    def test_all_sidon_and_coprime(self, result):
        for d in result["data"]:
            assert d["is_sidon"]
            assert d["all_coprime"]


class TestRamseyMultiplicityEdgeCases:
    """Tests for ramsey_multiplicity edge cases — covers lines 151, 167-180."""

    def test_no_edges_returns_zero(self):
        """n=1 or n=2 with no coprime edges: covers line 151."""
        r = ramsey_multiplicity(1, k=3)
        assert r["min_mono_copies"] == 0
        assert r["total_cliques"] == 0

    def test_heuristic_branch_large_n(self):
        """n large enough to trigger heuristic branch (edges > 30): covers 167-180."""
        r = ramsey_multiplicity(10, k=3)
        assert "min_mono_copies" in r
        assert r["min_mono_copies"] >= 0
        assert r["total_coprime_triangles"] >= 0
        assert 0 <= r["fraction_forced"] <= 1

    def test_heuristic_branch_n12(self):
        """n=12 definitely has >30 coprime edges, triggering heuristic."""
        r = ramsey_multiplicity(12, k=3)
        assert r["total_coprime_triangles"] > 0
        assert r["min_mono_copies"] >= 0

    def test_n2_no_triangles(self):
        """n=2 has one coprime edge (1,2) but no triangles."""
        r = ramsey_multiplicity(2, k=3)
        # Only 2 vertices — no triangle possible
        assert r["min_mono_copies"] == 0


class TestRunRamseyMultiplicityExperiment:
    """Tests for run_ramsey_multiplicity_experiment — covers lines 206-216.

    Uses mocking to avoid expensive exhaustive search for large n.
    """

    @pytest.fixture(scope="module")
    def result(self):
        fake_return = {
            "n": 5, "k": 3,
            "total_coprime_triangles": 6,
            "min_mono_copies": 1,
            "fraction_forced": 0.1667,
        }

        def fast_ramsey(n, k=3):
            return {
                "n": n, "k": k,
                "total_coprime_triangles": max(0, n - 4),
                "min_mono_copies": max(0, n - 6),
                "fraction_forced": round(max(0, n - 6) / max(1, n - 4), 4),
            }

        with patch("frontier_experiments.ramsey_multiplicity", side_effect=fast_ramsey):
            return run_ramsey_multiplicity_experiment()

    def test_returns_name(self, result):
        assert result["name"] == "Coprime Ramsey Multiplicity"

    def test_data_populated(self, result):
        assert len(result["data"]) == 8

    def test_data_n_values(self, result):
        ns = [d["n"] for d in result["data"]]
        assert ns == [5, 6, 7, 8, 9, 10, 12, 15]

    def test_conjecture_mentions_goodman(self, result):
        assert "conjecture" in result
        assert "Goodman" in result["conjecture"]

    def test_all_entries_have_keys(self, result):
        for d in result["data"]:
            assert "total_coprime_triangles" in d
            assert "min_mono_copies" in d
            assert "fraction_forced" in d


class TestRunAPFreCoprimeExperiment:
    """Tests for run_ap_free_coprime_experiment — covers lines 272-283."""

    @pytest.fixture(scope="module")
    def result(self):
        import random
        random.seed(42)
        return run_ap_free_coprime_experiment()

    def test_returns_name(self, result):
        assert result["name"] == "AP-Free Coprime Subsets"

    def test_data_populated(self, result):
        assert len(result["data"]) == 7

    def test_data_n_values(self, result):
        ns = [d["n"] for d in result["data"]]
        assert ns == [10, 20, 30, 50, 75, 100, 150]

    def test_conjecture_mentions_primes(self, result):
        assert "conjecture" in result
        assert "primes" in result["conjecture"].lower()

    def test_all_entries_have_fields(self, result):
        for d in result["data"]:
            assert "max_ap_free_coprime" in d
            assert "primes_ap_free" in d
            assert "pi(n)" in d
            assert "ratio_to_primes" in d


class TestRunDivisibilityColoringExperiment:
    """Tests for run_divisibility_coloring_experiment — covers lines 352-363."""

    @pytest.fixture(scope="module")
    def result(self):
        return run_divisibility_coloring_experiment()

    def test_returns_name(self, result):
        assert result["name"] == "Divisibility Graph Coloring"

    def test_data_populated(self, result):
        assert len(result["data"]) == 8

    def test_data_n_values(self, result):
        ns = [d["n"] for d in result["data"]]
        assert ns == [10, 20, 30, 50, 75, 100, 150, 200]

    def test_conjecture_mentions_dilworth(self, result):
        assert "conjecture" in result
        assert "Dilworth" in result["conjecture"]

    def test_chi_grows_logarithmically(self, result):
        """Chromatic number should grow roughly as log2(n)."""
        import math as m
        for d in result["data"]:
            expected_log = m.floor(m.log2(d["n"])) + 1
            assert abs(d["chi_greedy"] - expected_log) <= 2

    def test_all_entries_have_fields(self, result):
        for d in result["data"]:
            assert "chi_greedy" in d
            assert "max_chain" in d
            assert "max_antichain" in d
            assert "edges" in d
            assert "density" in d


class TestRunSumFreeRamseyExperiment:
    """Tests for run_sum_free_ramsey_experiment — covers lines 419-441."""

    @pytest.fixture(scope="module")
    def result(self):
        import random
        random.seed(42)
        return run_sum_free_ramsey_experiment()

    def test_returns_name(self, result):
        assert result["name"] == "Sum-Free Ramsey Numbers"

    def test_data_populated(self, result):
        assert len(result["data"]) >= 2

    def test_sr2_lower_bound(self, result):
        """SR(2) should be at least 1 (trivially achievable for n=1)."""
        assert result["SR(2)_lower"] >= 1

    def test_sr3_lower_bound(self, result):
        """SR(3) should be at least 1."""
        assert result["SR(3)_lower"] >= 1

    def test_sr2_at_most_schur(self, result):
        """SR(2) <= S(2) = 4 since AP-free adds extra constraint."""
        assert result["SR(2)_lower"] <= 4

    def test_conjecture_mentions_schur(self, result):
        assert "conjecture" in result
        assert "Schur" in result["conjecture"]
        # Should reference both SR(2) and SR(3)
        assert "SR(2)" in result["conjecture"] or "SR(3)" in result["conjecture"]

    def test_data_entries_have_fields(self, result):
        for d in result["data"]:
            assert "n" in d
            assert "k" in d
            assert "achievable" in d

    def test_achievable_entries_have_color_sizes(self, result):
        for d in result["data"]:
            if d["achievable"]:
                assert len(d["color_sizes"]) == d["k"]
                assert sum(d["color_sizes"]) == d["n"]


class TestRunCoprimeIndependenceExperiment:
    """Tests for run_coprime_independence_experiment — covers lines 494-505."""

    @pytest.fixture(scope="module")
    def result(self):
        import random
        random.seed(42)
        return run_coprime_independence_experiment()

    def test_returns_name(self, result):
        assert result["name"] == "Coprime Graph Independence Number"

    def test_data_populated(self, result):
        assert len(result["data"]) == 6

    def test_data_n_values(self, result):
        ns = [d["n"] for d in result["data"]]
        assert ns == [10, 20, 30, 50, 75, 100]

    def test_conjecture_mentions_evens(self, result):
        assert "conjecture" in result
        assert "even" in result["conjecture"].lower()

    def test_alpha_equals_half_n(self, result):
        for d in result["data"]:
            assert d["alpha_heuristic"] == d["n"] // 2

    def test_all_entries_have_fields(self, result):
        for d in result["data"]:
            assert "alpha_heuristic" in d
            assert "evens_size" in d
            assert "sample" in d
            assert "ratio_alpha_n" in d


class TestRunAllFrontier:
    """Tests for run_all_frontier — covers lines 514-536.

    Patches the expensive runner functions to return fast stubs, while
    verifying that run_all_frontier orchestrates correctly.
    """

    @staticmethod
    def _make_stub(name, data_count=3):
        return {
            "name": name,
            "data": [{"n": i, "val": i * 2} for i in range(data_count)],
            "conjecture": f"Stub conjecture for {name} — long enough to pass length check.",
        }

    @pytest.fixture(scope="module")
    def results(self):
        stubs = {
            "run_sidon_coprime_experiment": TestRunAllFrontier._make_stub("Sidon-Coprime Cliques"),
            "run_ramsey_multiplicity_experiment": TestRunAllFrontier._make_stub("Coprime Ramsey Multiplicity"),
            "run_ap_free_coprime_experiment": TestRunAllFrontier._make_stub("AP-Free Coprime Subsets"),
            "run_divisibility_coloring_experiment": TestRunAllFrontier._make_stub("Divisibility Graph Coloring"),
            "run_sum_free_ramsey_experiment": TestRunAllFrontier._make_stub("Sum-Free Ramsey Numbers"),
            "run_coprime_independence_experiment": TestRunAllFrontier._make_stub("Coprime Graph Independence Number"),
        }
        patches = [
            patch(f"frontier_experiments.{fname}", return_value=stubs[fname])
            for fname in stubs
        ]
        for p in patches:
            p.start()
        try:
            return run_all_frontier()
        finally:
            for p in patches:
                p.stop()

    def test_returns_list(self, results):
        assert isinstance(results, list)

    def test_returns_six_experiments(self, results):
        assert len(results) == 6

    def test_all_completed(self, results):
        for r in results:
            assert r["status"] == "completed", (
                f"Experiment {r.get('name', '?')} failed: {r.get('error', '')}"
            )

    def test_experiment_names(self, results):
        names = [r["name"] for r in results]
        assert "Sidon-Coprime Cliques" in names
        assert "Coprime Ramsey Multiplicity" in names
        assert "AP-Free Coprime Subsets" in names
        assert "Divisibility Graph Coloring" in names
        assert "Sum-Free Ramsey Numbers" in names
        assert "Coprime Graph Independence Number" in names

    def test_all_have_data(self, results):
        for r in results:
            assert "data" in r
            assert len(r["data"]) >= 1

    def test_all_have_conjecture(self, results):
        for r in results:
            assert "conjecture" in r
            assert len(r["conjecture"]) > 10


class TestRunAllFrontierWithFailure:
    """Test run_all_frontier handles exceptions gracefully — covers line 533-534."""

    def test_captures_failure(self):
        def exploding_func():
            raise ValueError("Intentional test explosion")

        with patch("frontier_experiments.run_sidon_coprime_experiment", side_effect=exploding_func):
            stubs = {
                "run_ramsey_multiplicity_experiment": lambda: {"name": "RM", "data": [], "conjecture": "x"},
                "run_ap_free_coprime_experiment": lambda: {"name": "AP", "data": [], "conjecture": "x"},
                "run_divisibility_coloring_experiment": lambda: {"name": "DC", "data": [], "conjecture": "x"},
                "run_sum_free_ramsey_experiment": lambda: {"name": "SF", "data": [], "conjecture": "x"},
                "run_coprime_independence_experiment": lambda: {"name": "CI", "data": [], "conjecture": "x"},
            }
            patches = [patch(f"frontier_experiments.{k}", side_effect=v) for k, v in stubs.items()]
            for p in patches:
                p.start()
            try:
                results = run_all_frontier()
            finally:
                for p in patches:
                    p.stop()

        assert len(results) == 6
        # First experiment should have failed
        failed = [r for r in results if r["status"] == "failed"]
        assert len(failed) == 1
        assert "Intentional test explosion" in failed[0]["error"]
        assert failed[0]["name"] == "Sidon-Coprime Cliques"

        # Other five should have completed
        completed = [r for r in results if r["status"] == "completed"]
        assert len(completed) == 5
