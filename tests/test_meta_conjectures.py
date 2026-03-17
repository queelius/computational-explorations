"""Tests for meta_conjectures.py — structural laws about problem ensembles."""
import math
import numpy as np
import pytest

from meta_conjectures import (
    load_problems,
    formalization_causal_analysis,
    solvability_scaling,
    hard_center_analysis,
    prize_monotonicity,
    solvability_phase_transition,
    tag_ecosystem,
    complexity_classes,
)


@pytest.fixture(scope="module")
def problems():
    return load_problems()


@pytest.fixture(scope="module")
def form_analysis(problems):
    return formalization_causal_analysis(problems)


@pytest.fixture(scope="module")
def scaling(problems):
    return solvability_scaling(problems)


@pytest.fixture(scope="module")
def hard_center(problems):
    return hard_center_analysis(problems)


@pytest.fixture(scope="module")
def prize_mono(problems):
    return prize_monotonicity(problems)


@pytest.fixture(scope="module")
def phase_trans(problems):
    return solvability_phase_transition(problems)


@pytest.fixture(scope="module")
def ecosystem(problems):
    return tag_ecosystem(problems)


@pytest.fixture(scope="module")
def complexity(problems):
    return complexity_classes(problems)


# ── formalization_causal_analysis ─────────────────────────────────────

class TestFormalizationCausal:
    """Test formalization causal analysis."""

    def test_returns_dict(self, form_analysis):
        assert isinstance(form_analysis, dict)

    def test_has_rates(self, form_analysis):
        assert "overall_formalized_solve_rate" in form_analysis
        assert "overall_unformalized_solve_rate" in form_analysis

    def test_rates_bounded(self, form_analysis):
        assert 0.0 <= form_analysis["overall_formalized_solve_rate"] <= 1.0
        assert 0.0 <= form_analysis["overall_unformalized_solve_rate"] <= 1.0

    def test_paradox_exists(self, form_analysis):
        # Non-formalized should solve more
        assert form_analysis["overall_gap"] > 0

    def test_has_strata(self, form_analysis):
        assert form_analysis["strata_analyzed"] > 10

    def test_strata_details_nonempty(self, form_analysis):
        assert len(form_analysis["strata_details"]) > 0

    def test_mh_or_positive(self, form_analysis):
        assert form_analysis["mantel_haenszel_or"] > 0

    def test_paradox_pervasive(self, form_analysis):
        # Paradox should hold in most strata
        assert form_analysis["paradox_holds_in_strata"] > form_analysis["paradox_reverses_in_strata"]


# ── solvability_scaling ──────────────────────────────────────────────

class TestSolvabilityScaling:
    """Test logistic regression solvability scaling."""

    def test_returns_dict(self, scaling):
        assert isinstance(scaling, dict)

    def test_accuracy_above_baseline(self, scaling):
        assert scaling["accuracy"] > scaling["base_rate"]

    def test_has_coefficients(self, scaling):
        assert "intercept" in scaling["coefficients"]
        assert "age_proxy" in scaling["coefficients"]
        assert "formalized" in scaling["coefficients"]

    def test_formalized_negative(self, scaling):
        # Formalization should predict lower solvability
        assert scaling["coefficients"]["formalized"] < 0

    def test_calibration_present(self, scaling):
        assert len(scaling["calibration"]) > 0

    def test_calibration_counts_positive(self, scaling):
        for c in scaling["calibration"]:
            assert c["count"] > 0

    def test_n_problems_large(self, scaling):
        assert scaling["n_problems"] > 500


# ── hard_center_analysis ─────────────────────────────────────────────

class TestHardCenter:
    """Test hard-center phenomenon analysis."""

    def test_returns_dict(self, hard_center):
        assert isinstance(hard_center, dict)

    def test_has_correlation(self, hard_center):
        assert "spearman_correlation" in hard_center

    def test_correlation_bounded(self, hard_center):
        assert -1.0 <= hard_center["spearman_correlation"] <= 1.0

    def test_has_hard_center(self, hard_center):
        assert "hard_center_count" in hard_center
        assert hard_center["hard_center_count"] >= 0

    def test_has_easy_wins(self, hard_center):
        assert "easy_win_count" in hard_center

    def test_connected_problems(self, hard_center):
        assert hard_center["n_connected_open"] > 50


# ── prize_monotonicity ───────────────────────────────────────────────

class TestPrizeMonotonicity:
    """Test prize-difficulty relationship."""

    def test_returns_dict(self, prize_mono):
        assert isinstance(prize_mono, dict)

    def test_has_brackets(self, prize_mono):
        assert len(prize_mono["brackets"]) >= 3

    def test_open_rates_bounded(self, prize_mono):
        for b in prize_mono["brackets"]:
            assert 0.0 <= b["open_rate"] <= 1.0

    def test_kendall_tau_bounded(self, prize_mono):
        assert -1.0 <= prize_mono["kendall_tau"] <= 1.0

    def test_high_prize_harder(self, prize_mono):
        # $1000+ should have higher open rate than $1-$100
        brackets = {b["bracket"]: b for b in prize_mono["brackets"]}
        if "$1000+" in brackets and "$1-$100" in brackets:
            assert brackets["$1000+"]["open_rate"] >= brackets["$1-$100"]["open_rate"]

    def test_no_prize_bracket_largest(self, prize_mono):
        # No-prize bracket should have most problems
        sizes = [(b["bracket"], b["n_total"]) for b in prize_mono["brackets"]]
        assert sizes[0][0] == "No prize"
        assert sizes[0][1] > 500


# ── solvability_phase_transition ─────────────────────────────────────

class TestPhaseTransition:
    """Test solvability phase transition analysis."""

    def test_returns_dict(self, phase_trans):
        assert isinstance(phase_trans, dict)

    def test_has_curve(self, phase_trans):
        assert len(phase_trans["curve"]) > 5

    def test_curve_signal_increasing(self, phase_trans):
        signals = [c["signal_midpoint"] for c in phase_trans["curve"]]
        # Should be roughly increasing
        assert signals[-1] >= signals[0]

    def test_max_gradient_positive(self, phase_trans):
        assert phase_trans["max_gradient"] > 0

    def test_n_problems_large(self, phase_trans):
        assert phase_trans["n_problems"] > 500


# ── tag_ecosystem ────────────────────────────────────────────────────

class TestTagEcosystem:
    """Test tag ecosystem dynamics."""

    def test_returns_dict(self, ecosystem):
        assert isinstance(ecosystem, dict)

    def test_has_active_tags(self, ecosystem):
        assert ecosystem["n_active_tags"] > 10

    def test_avg_fitness_bounded(self, ecosystem):
        assert 0.0 <= ecosystem["avg_fitness"] <= 1.0

    def test_dominant_tags_nonempty(self, ecosystem):
        assert len(ecosystem["dominant_tags"]) > 5

    def test_dominant_tag_fields(self, ecosystem):
        for d in ecosystem["dominant_tags"]:
            assert "tag" in d
            assert "fitness" in d
            assert "niche_size" in d
            assert "dominance_score" in d

    def test_diversity_positive(self, ecosystem):
        assert ecosystem["ecosystem_diversity"] > 0

    def test_number_theory_large_niche(self, ecosystem):
        nt = [d for d in ecosystem["dominant_tags"] if d["tag"] == "number theory"]
        assert len(nt) == 1
        assert nt[0]["niche_size"] > 200


# ── complexity_classes ───────────────────────────────────────────────

class TestComplexityClasses:
    """Test problem complexity class assignment."""

    def test_returns_dict(self, complexity):
        assert isinstance(complexity, dict)

    def test_has_stats(self, complexity):
        assert len(complexity["class_stats"]) >= 3

    def test_solve_rates_bounded(self, complexity):
        for cls, stats in complexity["class_stats"].items():
            assert 0.0 <= stats["solve_rate"] <= 1.0

    def test_ultra_hard_lowest(self, complexity):
        stats = complexity["class_stats"]
        if "U" in stats and "M" in stats:
            assert stats["U"]["solve_rate"] <= stats["M"]["solve_rate"]

    def test_total_classified(self, complexity):
        assert complexity["total_classified"] > 500

    def test_separation_not_poor(self, complexity):
        assert complexity["separation_quality"] in ("excellent", "good", "moderate")
