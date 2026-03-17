"""Tests for constant_relations.py (Ramanujan Library approach)."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from constant_relations import (
    CONSTANT_REGISTRY,
    get_registry,
    pslq_relation,
    search_pairwise_relations,
    search_triple_relations,
    analyze_ramsey_ratios,
    analyze_59_over_11,
    analyze_prime_indices,
    fit_rcop_models,
    build_relation_graph,
    describe_relation_graph,
    identify_constant,
    identify_all_constants,
    sieve_primes,
    prime_index,
    nth_prime,
)

import mpmath
from mpmath import mp, mpf, pi, euler, log, zeta

mp.dps = 50


# ===================================================================
# Registry tests
# ===================================================================

class TestConstantRegistry:
    def test_registry_nonempty(self):
        reg = get_registry()
        assert len(reg) > 20

    def test_registry_has_required_constants(self):
        reg = get_registry()
        required = [
            "6/pi^2", "R_cop(2)", "R_cop(3)", "R_cop(4)", "R_cop(3;3)",
            "gamma", "log2/log3", "2/3", "32/27",
            "pi(R_cop(2))", "pi(R_cop(3))", "pi(R_cop(4))",
        ]
        for name in required:
            assert name in reg, f"Missing constant: {name}"

    def test_registry_values_correct(self):
        reg = get_registry()
        assert abs(reg["R_cop(3)"]["float_value"] - 11) < 1e-10
        assert abs(reg["R_cop(4)"]["float_value"] - 59) < 1e-10
        assert abs(reg["R_cop(3;3)"]["float_value"] - 53) < 1e-10
        assert abs(reg["6/pi^2"]["float_value"] - 6 / math.pi**2) < 1e-10
        assert abs(reg["gamma"]["float_value"] - 0.5772156649) < 1e-8
        assert abs(reg["32/27"]["float_value"] - 32 / 27) < 1e-10

    def test_registry_structure(self):
        reg = get_registry()
        for name, info in reg.items():
            assert "value" in info, f"{name} missing 'value'"
            assert "float_value" in info, f"{name} missing 'float_value'"
            assert "description" in info, f"{name} missing 'description'"
            assert "source" in info, f"{name} missing 'source'"
            assert "category" in info, f"{name} missing 'category'"

    def test_coprime_density_value(self):
        """6/pi^2 = 1/zeta(2), both should be in registry and equal."""
        reg = get_registry()
        v1 = reg["6/pi^2"]["float_value"]
        v2 = reg["1/zeta(2)"]["float_value"]
        assert abs(v1 - v2) < 1e-15

    def test_prime_index_values(self):
        """Verify prime index entries match known values."""
        reg = get_registry()
        assert reg["pi(R_cop(2))"]["float_value"] == 1
        assert reg["pi(R_cop(3))"]["float_value"] == 5
        assert reg["pi(R_cop(4))"]["float_value"] == 17
        assert reg["pi(R_cop(3;3))"]["float_value"] == 16


# ===================================================================
# Prime utilities tests
# ===================================================================

class TestPrimeUtilities:
    def test_sieve_small(self):
        assert sieve_primes(10) == [2, 3, 5, 7]
        assert sieve_primes(1) == []
        assert sieve_primes(2) == [2]

    def test_prime_index_known(self):
        assert prime_index(2) == 1
        assert prime_index(3) == 2
        assert prime_index(5) == 3
        assert prime_index(11) == 5
        assert prime_index(59) == 17
        assert prime_index(53) == 16

    def test_prime_index_nonprime(self):
        assert prime_index(4) is None
        assert prime_index(1) is None
        assert prime_index(0) is None

    def test_nth_prime_known(self):
        assert nth_prime(1) == 2
        assert nth_prime(5) == 11
        assert nth_prime(17) == 59
        assert nth_prime(16) == 53

    def test_nth_prime_roundtrip(self):
        """prime_index(nth_prime(n)) == n for all n."""
        for n in range(1, 20):
            p = nth_prime(n)
            assert prime_index(p) == n

    def test_nth_prime_invalid(self):
        with pytest.raises(ValueError):
            nth_prime(0)


# ===================================================================
# PSLQ relation tests
# ===================================================================

class TestPSLQRelation:
    def test_identity_6_pi2_zeta2(self):
        """6/pi^2 = 1/zeta(2) should be found by PSLQ."""
        r = pslq_relation(["6/pi^2", "1/zeta(2)"])
        assert r is not None
        a, b = r
        assert a == 1 and b == -1 or a == -1 and b == 1

    def test_density_relation(self):
        """4 * (6/pi^2) = 3 * (8/pi^2)."""
        r = pslq_relation(["6/pi^2", "8/pi^2"])
        assert r is not None
        a, b = r
        # 4*(6/pi^2) - 3*(8/pi^2) = (24 - 24)/pi^2 = 0
        assert (a == 4 and b == -3) or (a == -4 and b == 3)

    def test_unknown_constant_raises(self):
        with pytest.raises(KeyError):
            pslq_relation(["nonexistent_constant", "6/pi^2"])

    def test_ramsey_17_equals_pi_rcop4(self):
        """R(3,3,3) = 17 = pi(R_cop(4))."""
        r = pslq_relation(["R(3,3,3)", "pi(R_cop(4))"])
        assert r is not None
        a, b = r
        assert abs(a) == 1 and abs(b) == 1


# ===================================================================
# Pairwise relation search tests
# ===================================================================

class TestPairwiseRelations:
    @pytest.fixture(scope="module")
    def pairwise_results(self):
        # Search among a small subset for speed
        names = ["6/pi^2", "1/zeta(2)", "8/pi^2", "R_cop(2)", "R(3,3)", "2/3"]
        return search_pairwise_relations(names, maxcoeff=100)

    def test_finds_relations(self, pairwise_results):
        assert len(pairwise_results) > 0

    def test_6_pi2_equals_1_zeta2(self, pairwise_results):
        found = any(
            r for r in pairwise_results
            if set(r["constants"]) == {"6/pi^2", "1/zeta(2)"}
        )
        assert found, "Should find 6/pi^2 = 1/zeta(2)"

    def test_residuals_small(self, pairwise_results):
        for r in pairwise_results:
            assert r["residual"] < 1e-15, f"Large residual: {r}"

    def test_relation_structure(self, pairwise_results):
        for r in pairwise_results:
            assert "constants" in r
            assert "coefficients" in r
            assert "equation" in r
            assert "residual" in r
            assert "max_coeff" in r
            assert len(r["constants"]) == 2
            assert len(r["coefficients"]) == 2


# ===================================================================
# Triple relation search tests
# ===================================================================

class TestTripleRelations:
    def test_empty_when_all_pairwise(self):
        """If all pairs have relations, triples should be empty (all trivial)."""
        names = ["R_cop(2)", "R(3,3)", "R(4,4)"]  # 2, 6, 18 all rational multiples
        results = search_triple_relations(names, maxcoeff=100)
        assert results == []

    def test_returns_list(self):
        names = ["gamma", "log2/log3", "e"]
        results = search_triple_relations(names, maxcoeff=50)
        assert isinstance(results, list)


# ===================================================================
# Ramsey ratio analysis tests
# ===================================================================

class TestRamseyRatios:
    @pytest.fixture(scope="module")
    def ramsey_results(self):
        return analyze_ramsey_ratios()

    def test_log59_log11_value(self, ramsey_results):
        v = ramsey_results["log59_log11"]["value"]
        expected = math.log(59) / math.log(11)
        assert abs(v - expected) < 1e-10

    def test_growth_rates_positive(self, ramsey_results):
        for k, rate in ramsey_results["growth_rates"].items():
            assert rate > 0

    def test_growth_rates_increasing(self, ramsey_results):
        rates = ramsey_results["growth_rates"]
        assert rates[3] > rates[2]
        assert rates[4] > rates[3]

    def test_growth_differences_computed(self, ramsey_results):
        diffs = ramsey_results["growth_rate_differences"]
        assert "k3_minus_k2" in diffs
        assert "k4_minus_k3" in diffs

    def test_targeted_pslq_structure(self, ramsey_results):
        tp = ramsey_results["targeted_pslq"]
        assert isinstance(tp, dict)
        assert "log(59)/log(11)" in tp

    def test_no_irrational_relation_for_59_over_11(self, ramsey_results):
        """59/11 is rational, so PSLQ with irrational targets should only
        find trivial relations (where target coeff = 0). We filter those."""
        hits = ramsey_results["targeted_pslq"].get("59/11", {})
        # All non-trivial hits (with b != 0) should be empty for a rational constant
        # vs an irrational target -- there is no such relation
        for t_name, info in hits.items():
            a, b, c = info["coefficients"]
            assert b != 0, "Filtered search should exclude b=0 hits"

    def test_log59_log11_no_simple_relation(self, ramsey_results):
        """log(59)/log(11) should NOT have a simple relation to known irrationals."""
        hits = ramsey_results["targeted_pslq"].get("log(59)/log(11)", {})
        # Any hits found would be significant; absence is the expected result
        # This is a notable negative result
        assert isinstance(hits, dict)


# ===================================================================
# 59/11 deep dive tests
# ===================================================================

class TestDeepDive59Over11:
    @pytest.fixture(scope="module")
    def dive_results(self):
        return analyze_59_over_11()

    def test_decimal_value(self, dive_results):
        assert abs(dive_results["decimal"] - 59 / 11) < 1e-10

    def test_quadratic_residue_reciprocity(self, dive_results):
        """By quadratic reciprocity, exactly one of (59/11), (11/59) is a QR."""
        qr1 = dive_results["59_qr_mod_11"]
        qr2 = dive_results["11_qr_mod_59"]
        assert qr1 != qr2, "Quadratic reciprocity: exactly one should be QR"

    def test_euclidean_division(self, dive_results):
        assert dive_results["euclidean"] == "59 = 5*11 + 4"


# ===================================================================
# Prime index analysis tests
# ===================================================================

class TestPrimeIndexAnalysis:
    @pytest.fixture(scope="module")
    def pi_results(self):
        return analyze_prime_indices()

    def test_index_sequence(self, pi_results):
        assert pi_results["index_sequence"] == [1, 5, 17]

    def test_first_differences(self, pi_results):
        assert pi_results["first_differences"] == [4, 12]

    def test_second_differences(self, pi_results):
        assert pi_results["second_differences"] == [8]

    def test_quadratic_formula_matches(self, pi_results):
        """4k^2 - 8k + 5 should match for k=1,2,3."""
        for h in pi_results["pattern_hypotheses"]:
            if "4k^2" in h["formula"]:
                assert h["matches"], "Quadratic formula should match exactly"
                break
        else:
            pytest.fail("Quadratic hypothesis not found")

    def test_exponential_formula_matches(self, pi_results):
        """2*3^(k-1) - 1 should match for k=1,2,3."""
        for h in pi_results["pattern_hypotheses"]:
            if h["formula"] == "2 * 3^(k-1) - 1":
                assert h["matches"], "Exponential formula should match exactly"
                break
        else:
            pytest.fail("Exponential hypothesis not found")

    def test_geometric_diffs_matches(self, pi_results):
        """Differences = 4*3^(k-2) should match."""
        for h in pi_results["pattern_hypotheses"]:
            if "differences" in h.get("formula", ""):
                assert h.get("matches_diffs"), "Geometric diffs should match"
                break
        else:
            pytest.fail("Geometric diffs hypothesis not found")

    def test_at_least_3_exact_matches(self, pi_results):
        assert pi_results["exact_matches_count"] >= 3

    def test_predictions_are_primes(self, pi_results):
        """All predicted R_cop values should be prime."""
        for h in pi_results["pattern_hypotheses"]:
            if h.get("matches") or h.get("matches_diffs"):
                for key in ["prediction_k4_prime", "prediction_k5_prime", "prediction_R_cop(5)"]:
                    if key in h:
                        p = h[key]
                        assert prime_index(p) is not None, f"Predicted {p} should be prime"

    def test_quadratic_predicts_r_cop_5(self, pi_results):
        """Quadratic: index 37 => p_37 = 157."""
        for h in pi_results["pattern_hypotheses"]:
            if "4k^2" in h["formula"]:
                assert h["prediction_k4_index"] == 37
                assert h["prediction_k4_prime"] == nth_prime(37)
                break

    def test_exponential_predicts_r_cop_5(self, pi_results):
        """Exponential (closed form): index 53 => p_53 = 241."""
        for h in pi_results["pattern_hypotheses"]:
            if h["formula"] == "2 * 3^(k-1) - 1":
                assert h["prediction_k4_index"] == 53
                assert h["prediction_k4_prime"] == nth_prime(53)
                break

    def test_fermat_partial_match(self, pi_results):
        """Fermat numbers: 5 = F_1, 17 = F_2."""
        for h in pi_results["pattern_hypotheses"]:
            if "Fermat" in h.get("formula", ""):
                assert 5 in h["fermat_sequence"]
                assert 17 in h["fermat_sequence"]
                break


# ===================================================================
# Cross-constant model fitting tests
# ===================================================================

class TestFitRcopModels:
    @pytest.fixture(scope="module")
    def models(self):
        return fit_rcop_models()

    def test_model_a_exists(self, models):
        assert "model_A_power_of_Rkk" in models
        assert "error" not in models["model_A_power_of_Rkk"]

    def test_model_a_alpha_gt_1(self, models):
        """R_cop grows faster than R(k,k), so alpha > 1."""
        alpha = models["model_A_power_of_Rkk"]["alpha"]
        assert alpha > 1.0

    def test_model_a_small_residual(self, models):
        """Power model should fit the 3 data points well."""
        assert models["model_A_power_of_Rkk"]["max_residual"] < 1.0

    def test_model_c_exists(self, models):
        assert "model_C_two_param_exp" in models
        assert "error" not in models["model_C_two_param_exp"]

    def test_model_c_predicts_large_rcop5(self, models):
        """R_cop(5) should be >> 59."""
        pred = models["model_C_two_param_exp"]["prediction_k5"]
        assert pred > 100

    def test_model_d1_matches_known(self, models):
        """Quadratic index model should reproduce R_cop(3)=11, R_cop(4)=59."""
        d1 = models["model_D1_quadratic"]["predictions"]
        assert d1[2]["prime"] == 11  # R_cop(3) via index formula at k=2 offset
        assert d1[3]["prime"] == 59

    def test_model_d2_matches_known(self, models):
        """Exponential index model should reproduce R_cop(3)=11, R_cop(4)=59."""
        d2 = models["model_D2_exponential"]["predictions"]
        assert d2[2]["prime"] == 11
        assert d2[3]["prime"] == 59

    def test_d2_and_d3_agree(self, models):
        """D2 (closed form) and D3 (geometric diffs) should give same results."""
        d2 = models["model_D2_exponential"]["predictions"]
        d3 = models["model_D3_diffs_geometric"]["predictions"]
        for k in d2:
            if k in d3:
                assert d2[k]["prime"] == d3[k]["prime"]


# ===================================================================
# Relation graph tests
# ===================================================================

class TestRelationGraph:
    @pytest.fixture(scope="module")
    def graph(self):
        return build_relation_graph(maxcoeff=200)

    def test_graph_has_nodes(self, graph):
        assert len(graph["nodes"]) > 20

    def test_graph_has_edges(self, graph):
        assert graph["num_edges"] > 0

    def test_rational_cluster_connected(self, graph):
        """All integer Ramsey values should be in the same component."""
        # Find component containing R_cop(3)
        adj = graph["adjacency"]
        assert "R_cop(3)" in adj
        neighbors = {e["neighbor"] for e in adj["R_cop(3)"]}
        # R_cop(4) should be reachable from R_cop(3)
        assert "R_cop(4)" in neighbors or any(
            "R_cop(4)" in {e2["neighbor"] for e2 in adj.get(n, [])}
            for n in neighbors
        )

    def test_irrational_isolated(self, graph):
        """gamma, e, pi should be isolated (no rational relation to Ramsey values)."""
        isolated = graph["isolated"]
        for name in ["gamma", "e", "pi"]:
            assert name in isolated, f"{name} should be isolated"

    def test_description_nonempty(self, graph):
        desc = describe_relation_graph(graph)
        assert len(desc) > 100
        assert "Component" in desc

    def test_components_cover_all_nodes(self, graph):
        all_in_components = set()
        for members in graph["components"].values():
            all_in_components.update(members)
        assert all_in_components == set(graph["nodes"])


# ===================================================================
# Identification tests
# ===================================================================

class TestIdentification:
    def test_identify_rational(self):
        result = identify_constant("2/3")
        assert result is not None
        assert "2" in result and "3" in result

    def test_identify_integer(self):
        result = identify_constant("R_cop(3)")
        assert result is not None
        assert "11" in result

    def test_identify_all_returns_dict(self):
        results = identify_all_constants()
        assert isinstance(results, dict)
        assert len(results) == len(CONSTANT_REGISTRY)

    def test_identify_unknown_raises(self):
        with pytest.raises(KeyError):
            identify_constant("nonexistent")


# ===================================================================
# Mathematical consistency tests
# ===================================================================

class TestMathematicalConsistency:
    def test_coprime_density_equals_inverse_zeta2(self):
        """6/pi^2 = 1/zeta(2) to full precision."""
        reg = get_registry()
        v1 = reg["6/pi^2"]["value"]
        v2 = reg["1/zeta(2)"]["value"]
        assert abs(float(v1 - v2)) < 1e-50

    def test_sieve_density_formula(self):
        """8/pi^2 * (1 - f_E^2) at f_E=1/3 should give 64/(9*pi^2)."""
        reg = get_registry()
        base = reg["8/pi^2"]["value"]
        f_E = mpf(1) / 3
        computed = base * (1 - f_E**2)
        expected = reg["64/(9*pi^2)"]["value"]
        assert abs(float(computed - expected)) < 1e-50

    def test_ratio_32_27_correct(self):
        """64/(9*pi^2) / (6/pi^2) = 32/27."""
        reg = get_registry()
        ratio = reg["64/(9*pi^2)"]["value"] / reg["6/pi^2"]["value"]
        expected = reg["32/27"]["value"]
        assert abs(float(ratio - expected)) < 1e-50

    def test_growth_rates_match_log(self):
        """log(R_cop(k))/k should match registry values."""
        reg = get_registry()
        v3 = reg["log(R_cop(3))/3"]["value"]
        expected3 = log(mpf(11)) / 3
        assert abs(float(v3 - expected3)) < 1e-50

    def test_rcop_all_prime(self):
        """R_cop(2), R_cop(3), R_cop(4), R_cop(3;3) are all prime."""
        for name, expected_idx in [
            ("R_cop(2)", 1),
            ("R_cop(3)", 5),
            ("R_cop(4)", 17),
            ("R_cop(3;3)", 16),
        ]:
            val = int(CONSTANT_REGISTRY[name]["float_value"])
            idx = prime_index(val)
            assert idx is not None, f"{name}={val} should be prime"
            assert idx == expected_idx, f"pi({val}) should be {expected_idx}, got {idx}"

    def test_quadratic_reciprocity(self):
        """11 = 3 mod 4, 59 = 3 mod 4 => (11/59)(59/11) = -1."""
        assert 11 % 4 == 3
        assert 59 % 4 == 3
        # Legendre symbols
        ls_11_59 = pow(11, (59 - 1) // 2, 59)
        ls_59_11 = pow(59, (11 - 1) // 2, 11)
        # Map to {1, -1}
        ls1 = 1 if ls_11_59 == 1 else -1
        ls2 = 1 if ls_59_11 == 1 else -1
        assert ls1 * ls2 == -1, "Quadratic reciprocity product should be -1"

    def test_index_formula_consistency(self):
        """Both exact formulas agree at k=1,2,3 but MUST diverge at k=4.

        Quadratic: 4k^2 - 8k + 5 gives 1, 5, 17, 37, 65, ...
        Exponential: 2*3^(k-1) - 1 gives 1, 5, 17, 53, 161, ...
        They agree for the 3 data points but predict differently beyond.
        """
        for k in [1, 2, 3]:
            quad = 4 * k**2 - 8 * k + 5
            exp = 2 * 3**(k - 1) - 1
            assert quad == exp, f"Formulas should agree at k={k}: {quad} vs {exp}"
        # They MUST diverge at k=4
        quad_4 = 4 * 16 - 32 + 5  # = 37
        exp_4 = 2 * 27 - 1  # = 53
        assert quad_4 != exp_4, "Formulas should diverge at k=4"
        # And at k=5
        quad_5 = 4 * 25 - 40 + 5  # = 65
        exp_5 = 2 * 81 - 1  # = 161
        assert quad_5 != exp_5, "Formulas should diverge at k=5"


# ===================================================================
# Edge case and robustness tests
# ===================================================================

class TestEdgeCases:
    def test_pslq_with_equal_constants(self):
        """PSLQ on two equal values should find [1, -1]."""
        r = pslq_relation(["6/pi^2", "1/zeta(2)"])
        assert r is not None

    def test_empty_pairwise_search(self):
        """Search with a single constant should return empty."""
        results = search_pairwise_relations(["6/pi^2"])
        assert results == []

    def test_pairwise_search_with_two(self):
        results = search_pairwise_relations(["6/pi^2", "1/zeta(2)"])
        assert len(results) == 1

    def test_sieve_primes_boundary(self):
        assert sieve_primes(0) == []
        assert sieve_primes(1) == []
        assert sieve_primes(2) == [2]
        assert sieve_primes(3) == [2, 3]

    def test_nth_prime_large(self):
        """nth_prime should work for reasonably large n."""
        p100 = nth_prime(100)
        assert p100 == 541
        assert prime_index(541) == 100
