#!/usr/bin/env python3
"""
Meta-Conjectures Engine — Structural Laws About Problem Ensembles

Goes beyond individual problem analysis to formulate precise mathematical
statements about the STRUCTURE of the Erdős problem corpus itself.

Key questions:
1. Is the formalization paradox a genuine causal effect or pure selection bias?
2. Can the hard-center phenomenon be stated as a theorem about random graphs?
3. Is there a universal scaling law for problem solvability?
4. Do prize amounts encode a consistent difficulty measure?
5. Is there a "phase transition" in solvability as a function of structural features?

These are META-Erdős problems: conjectures about conjectures.
"""

import math
import yaml
import numpy as np
from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "meta_conjectures_report.md"


def load_problems() -> List[Dict]:
    with open(DATA_PATH) as f:
        return yaml.safe_load(f)


def _status(p: Dict) -> str:
    return p.get("status", {}).get("state", "unknown")


def _tags(p: Dict) -> Set[str]:
    return set(p.get("tags", []))


def _number(p: Dict) -> int:
    n = p.get("number", 0)
    try:
        return int(n)
    except (TypeError, ValueError):
        return 0


def _prize(p: Dict) -> float:
    import re
    pz = p.get("prize", "no")
    if not pz or pz == "no":
        return 0.0
    nums = re.findall(r"[\d,]+", str(pz))
    if nums:
        val = float(nums[0].replace(",", ""))
        if "\u00a3" in str(pz):
            val *= 1.27
        return val
    return 0.0


def _is_solved(p: Dict) -> bool:
    return _status(p) in ("proved", "disproved", "solved",
                          "proved (Lean)", "disproved (Lean)", "solved (Lean)")


def _is_open(p: Dict) -> bool:
    return _status(p) == "open"


def _is_formalized(p: Dict) -> bool:
    form = p.get("formalized")
    if isinstance(form, dict):
        return form.get("state") == "yes"
    return False


def _oeis(p: Dict) -> List[str]:
    return p.get("oeis", [])


# ══════════════════════════════════════════════════════════════════════
# Meta-Conjecture 1: Formalization Paradox with Causal Analysis
# ══════════════════════════════════════════════════════════════════════

def formalization_causal_analysis(problems: List[Dict]) -> Dict[str, Any]:
    """
    Disentangle selection bias from causal effect in formalization paradox.

    Method: stratified analysis. For each tag, compute P(solved | formalized)
    and P(solved | not formalized). If the paradox is purely selection bias
    (hard problems attract formalization), then within each tag stratum the
    effect should vanish.
    """
    # Overall rates
    formalized = [p for p in problems if _is_formalized(p)]
    not_formalized = [p for p in problems if not _is_formalized(p)]

    overall_form_rate = sum(1 for p in formalized if _is_solved(p)) / max(len(formalized), 1)
    overall_noform_rate = sum(1 for p in not_formalized if _is_solved(p)) / max(len(not_formalized), 1)

    # Per-tag stratified analysis
    tag_strata = defaultdict(lambda: {"form_solved": 0, "form_total": 0,
                                       "noform_solved": 0, "noform_total": 0})
    for p in problems:
        for tag in _tags(p):
            if _is_formalized(p):
                tag_strata[tag]["form_total"] += 1
                if _is_solved(p):
                    tag_strata[tag]["form_solved"] += 1
            elif _is_open(p) or _is_solved(p):
                tag_strata[tag]["noform_total"] += 1
                if _is_solved(p):
                    tag_strata[tag]["noform_solved"] += 1

    # Compute per-tag odds ratios
    strata_results = []
    paradox_holds_in_stratum = 0
    paradox_reverses = 0
    for tag, data in sorted(tag_strata.items()):
        if data["form_total"] >= 3 and data["noform_total"] >= 3:
            form_rate = data["form_solved"] / data["form_total"]
            noform_rate = data["noform_solved"] / data["noform_total"]
            gap = noform_rate - form_rate
            strata_results.append({
                "tag": tag,
                "form_rate": round(form_rate, 3),
                "noform_rate": round(noform_rate, 3),
                "gap": round(gap, 3),
                "form_n": data["form_total"],
                "noform_n": data["noform_total"],
            })
            if gap > 0.05:
                paradox_holds_in_stratum += 1
            elif gap < -0.05:
                paradox_reverses += 1

    # Mantel-Haenszel adjusted odds ratio (simplified)
    mh_num = 0.0
    mh_den = 0.0
    for tag, data in tag_strata.items():
        n_total = data["form_total"] + data["noform_total"]
        if n_total < 6:
            continue
        a = data["form_solved"]
        b = data["form_total"] - a
        c = data["noform_solved"]
        d = data["noform_total"] - c
        if n_total > 0:
            mh_num += a * d / n_total
            mh_den += b * c / n_total

    mh_or = mh_num / mh_den if mh_den > 0 else float('inf')

    return {
        "overall_formalized_solve_rate": round(overall_form_rate, 3),
        "overall_unformalized_solve_rate": round(overall_noform_rate, 3),
        "overall_gap": round(overall_noform_rate - overall_form_rate, 3),
        "n_formalized": len(formalized),
        "n_not_formalized": len(not_formalized),
        "strata_analyzed": len(strata_results),
        "paradox_holds_in_strata": paradox_holds_in_stratum,
        "paradox_reverses_in_strata": paradox_reverses,
        "strata_details": sorted(strata_results, key=lambda x: -abs(x["gap"])),
        "mantel_haenszel_or": round(mh_or, 3),
        "mh_interpretation": "selection_bias" if 0.5 < mh_or < 2.0 else "genuine_effect",
    }


# ══════════════════════════════════════════════════════════════════════
# Meta-Conjecture 2: Universal Solvability Scaling Law
# ══════════════════════════════════════════════════════════════════════

def solvability_scaling(problems: List[Dict]) -> Dict[str, Any]:
    """
    Test whether solvability follows a universal scaling law as a function
    of structural complexity.

    Hypothesis: P(solved) = f(complexity) where complexity combines
    problem number (age proxy), tag count, OEIS count, and prize.

    Test: logistic regression P(solved) = σ(β₀ + β₁·age + β₂·tags + ...)
    """
    # Build feature vectors
    features = []
    labels = []

    for p in problems:
        if not (_is_solved(p) or _is_open(p)):
            continue

        num = _number(p)
        try:
            num = int(num)
        except (TypeError, ValueError):
            continue
        if num <= 0:
            continue

        n_tags = len(_tags(p))
        n_oeis = len(_oeis(p))
        prize = _prize(p)
        formalized = 1.0 if _is_formalized(p) else 0.0

        # Normalize features
        features.append([
            num / 1200.0,       # age proxy (normalized)
            n_tags / 10.0,      # tag count (normalized)
            n_oeis / 20.0,      # OEIS count (normalized)
            min(prize, 5000) / 5000.0,  # prize (normalized)
            formalized,
        ])
        labels.append(1.0 if _is_solved(p) else 0.0)

    X = np.array(features)
    y = np.array(labels)
    n_samples = len(y)

    # Simple logistic regression via gradient descent
    n_features = X.shape[1]
    beta = np.zeros(n_features + 1)  # +1 for intercept
    X_aug = np.column_stack([np.ones(n_samples), X])  # add intercept

    lr = 0.1
    for _ in range(1000):
        z = X_aug @ beta
        z = np.clip(z, -20, 20)
        pred = 1.0 / (1.0 + np.exp(-z))
        grad = X_aug.T @ (pred - y) / n_samples
        beta -= lr * grad

    # Predictions and accuracy
    z = X_aug @ beta
    z = np.clip(z, -20, 20)
    pred_prob = 1.0 / (1.0 + np.exp(-z))
    pred_label = (pred_prob >= 0.5).astype(float)
    accuracy = np.mean(pred_label == y)

    # Feature names
    feature_names = ["intercept", "age_proxy", "tag_count", "oeis_count",
                     "prize", "formalized"]

    coefficients = {name: round(float(b), 4)
                    for name, b in zip(feature_names, beta)}

    # Bin predicted probabilities for calibration
    bins = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
    calibration = []
    for lo, hi in bins:
        mask = (pred_prob >= lo) & (pred_prob < hi)
        if mask.sum() > 0:
            actual = y[mask].mean()
            predicted = pred_prob[mask].mean()
            calibration.append({
                "bin": f"{lo:.1f}-{hi:.1f}",
                "count": int(mask.sum()),
                "predicted": round(float(predicted), 3),
                "actual": round(float(actual), 3),
            })

    return {
        "n_problems": n_samples,
        "accuracy": round(float(accuracy), 3),
        "base_rate": round(float(y.mean()), 3),
        "coefficients": coefficients,
        "calibration": calibration,
        "scaling_law": _interpret_scaling(coefficients),
    }


def _interpret_scaling(coefficients: Dict[str, float]) -> str:
    """Interpret the logistic regression coefficients."""
    effects = []
    if abs(coefficients.get("age_proxy", 0)) > 0.3:
        sign = "older → harder" if coefficients["age_proxy"] < 0 else "older → easier"
        effects.append(sign)
    if abs(coefficients.get("prize", 0)) > 0.3:
        sign = "prize → harder" if coefficients["prize"] < 0 else "prize → easier"
        effects.append(sign)
    if abs(coefficients.get("formalized", 0)) > 0.3:
        sign = "formalized → harder" if coefficients["formalized"] < 0 else "formalized → easier"
        effects.append(sign)
    return "; ".join(effects) if effects else "no strong scaling effects detected"


# ══════════════════════════════════════════════════════════════════════
# Meta-Conjecture 3: Hard-Center Theorem
# ══════════════════════════════════════════════════════════════════════

def hard_center_analysis(problems: List[Dict]) -> Dict[str, Any]:
    """
    The Hard-Center Conjecture: In any sufficiently rich problem corpus,
    the most impactful problems are the least tractable.

    Formalize as: for random problem graph G with n nodes, if we define
    - tractability(v) = features correlated with solvability
    - impact(v) = degree centrality in the dependency graph
    then Cor(tractability, impact) < 0 for large n.

    Test with multiple centrality/tractability measures.
    """
    # Build problem metadata
    tag_solve_rates = defaultdict(list)
    for p in problems:
        solved = _is_solved(p)
        for tag in _tags(p):
            tag_solve_rates[tag].append(1.0 if solved else 0.0)

    tag_avg_solve = {tag: np.mean(vals)
                     for tag, vals in tag_solve_rates.items()
                     if len(vals) >= 5}

    # Build dependency-like graph via shared OEIS sequences
    oeis_to_problems = defaultdict(set)
    for p in problems:
        num = _number(p)
        for seq in _oeis(p):
            if seq and seq not in ("N/A", "possible"):
                oeis_to_problems[seq].add(num)

    # Degree centrality (OEIS connections)
    degree = defaultdict(int)
    for seq, pnums in oeis_to_problems.items():
        if 2 <= len(pnums) <= 50:
            for pnum in pnums:
                degree[pnum] += len(pnums) - 1

    # Tractability score: tag solve rate + age bonus
    open_problems = [p for p in problems if _is_open(p)]
    tractability = {}
    impact = {}

    for p in open_problems:
        num = _number(p)
        tags = _tags(p)
        if not tags:
            continue

        # Tractability: average solve rate of tags
        tag_rates = [tag_avg_solve.get(t, 0.5) for t in tags]
        tract = np.mean(tag_rates)

        # Age bonus: higher number = newer = slightly more tractable
        age_bonus = num / 1200.0 * 0.1
        tract = min(tract + age_bonus, 1.0)

        tractability[num] = tract
        impact[num] = degree.get(num, 0)

    # Compute correlations
    common = set(tractability.keys()) & set(impact.keys())
    common = [n for n in common if impact[n] > 0]  # only connected problems

    if len(common) < 10:
        return {"error": "insufficient connected open problems"}

    tract_vals = np.array([tractability[n] for n in common])
    impact_vals = np.array([impact[n] for n in common])

    # Spearman rank correlation
    tract_ranks = np.argsort(np.argsort(tract_vals)).astype(float)
    impact_ranks = np.argsort(np.argsort(impact_vals)).astype(float)
    n = len(common)
    d_sq = np.sum((tract_ranks - impact_ranks) ** 2)
    spearman = 1 - 6 * d_sq / (n * (n * n - 1))

    # Pearson correlation
    pearson = float(np.corrcoef(tract_vals, impact_vals)[0, 1])

    # Identify the "hard center": high impact, low tractability
    hard_center = []
    impact_threshold = np.percentile(impact_vals, 75)
    tract_threshold = np.percentile(tract_vals, 25)

    for num in common:
        if impact[num] >= impact_threshold and tractability[num] <= tract_threshold:
            hard_center.append({
                "number": num,
                "tractability": round(tractability[num], 3),
                "impact": impact[num],
            })
    hard_center.sort(key=lambda x: -x["impact"])

    # "Easy wins": high tractability, high impact
    easy_wins = []
    tract_high = np.percentile(tract_vals, 75)
    for num in common:
        if impact[num] >= impact_threshold and tractability[num] >= tract_high:
            easy_wins.append({
                "number": num,
                "tractability": round(tractability[num], 3),
                "impact": impact[num],
            })
    easy_wins.sort(key=lambda x: -x["impact"])

    return {
        "n_connected_open": len(common),
        "spearman_correlation": round(spearman, 3),
        "pearson_correlation": round(pearson, 3),
        "hard_center_count": len(hard_center),
        "easy_win_count": len(easy_wins),
        "hard_center_top10": hard_center[:10],
        "easy_wins_top10": easy_wins[:10],
        "conjecture_holds": spearman < -0.1,
        "effect_size": "strong" if spearman < -0.3 else "moderate" if spearman < -0.1 else "weak",
    }


# ══════════════════════════════════════════════════════════════════════
# Meta-Conjecture 4: Prize Monotonicity Theorem
# ══════════════════════════════════════════════════════════════════════

def prize_monotonicity(problems: List[Dict]) -> Dict[str, Any]:
    """
    Test: Erdős's prize assignments are monotonically correlated with
    problem difficulty.

    Formalize: For prize brackets P₁ < P₂ < ... < Pₖ,
    P(open | prize ∈ Pᵢ) is non-decreasing in i.

    Also test: do prizes predict WHICH specific structural features
    make a problem hard?
    """
    # Prize brackets
    brackets = [
        (0, 0, "No prize"),
        (1, 100, "$1-$100"),
        (101, 500, "$101-$500"),
        (501, 1000, "$501-$1000"),
        (1001, 100000, "$1000+"),
    ]

    bracket_data = []
    for lo, hi, label in brackets:
        in_bracket = [p for p in problems
                      if lo <= _prize(p) <= hi and (_is_solved(p) or _is_open(p))]
        if not in_bracket:
            continue
        n_open = sum(1 for p in in_bracket if _is_open(p))
        n_total = len(in_bracket)
        open_rate = n_open / n_total

        # Average structural features for this bracket
        avg_tags = np.mean([len(_tags(p)) for p in in_bracket])
        avg_oeis = np.mean([len(_oeis(p)) for p in in_bracket])
        avg_number = np.mean([_number(p) for p in in_bracket])

        bracket_data.append({
            "bracket": label,
            "n_total": n_total,
            "n_open": n_open,
            "open_rate": round(open_rate, 3),
            "avg_tags": round(float(avg_tags), 1),
            "avg_oeis": round(float(avg_oeis), 1),
            "avg_number": round(float(avg_number), 0),
        })

    # Check monotonicity
    rates = [b["open_rate"] for b in bracket_data if b["n_total"] >= 5]
    monotone_violations = 0
    for i in range(len(rates) - 1):
        if rates[i] > rates[i + 1] + 0.01:
            monotone_violations += 1

    # Kendall's tau between bracket index and open rate
    n_brackets = len(rates)
    concordant = 0
    discordant = 0
    for i in range(n_brackets):
        for j in range(i + 1, n_brackets):
            if rates[j] > rates[i]:
                concordant += 1
            elif rates[j] < rates[i]:
                discordant += 1

    tau = (concordant - discordant) / max(concordant + discordant, 1)

    return {
        "brackets": bracket_data,
        "monotone_violations": monotone_violations,
        "is_monotone": monotone_violations == 0,
        "kendall_tau": round(tau, 3),
        "conjecture_holds": tau > 0.5,
    }


# ══════════════════════════════════════════════════════════════════════
# Meta-Conjecture 5: Phase Transition in Solvability
# ══════════════════════════════════════════════════════════════════════

def solvability_phase_transition(problems: List[Dict]) -> Dict[str, Any]:
    """
    Test: Is there a sharp phase transition in solvability as a function
    of some structural parameter?

    In random graph theory, many properties exhibit sharp thresholds.
    We test whether the Erdős corpus has a similar phenomenon:
    - Below some threshold in "complexity", almost all problems are solved
    - Above it, almost all are open
    - The transition region is narrow

    Use tag_solve_rate as the complexity proxy.
    """
    # Compute per-problem "solvability signal"
    tag_solve_rates = defaultdict(list)
    for p in problems:
        solved = _is_solved(p)
        for tag in _tags(p):
            tag_solve_rates[tag].append(1.0 if solved else 0.0)

    tag_avg = {tag: np.mean(vals)
               for tag, vals in tag_solve_rates.items()
               if len(vals) >= 3}

    signal_label = []
    for p in problems:
        if not (_is_solved(p) or _is_open(p)):
            continue
        tags = _tags(p)
        if not tags:
            continue
        avg_rate = np.mean([tag_avg.get(t, 0.5) for t in tags])
        signal_label.append((avg_rate, 1.0 if _is_solved(p) else 0.0))

    signal_label.sort(key=lambda x: x[0])
    signals = np.array([s for s, l in signal_label])
    labels = np.array([l for s, l in signal_label])
    n = len(signals)

    # Sliding window analysis
    window = max(n // 20, 10)
    curve = []
    for i in range(0, n - window, window // 2):
        chunk = labels[i:i + window]
        mid_signal = float(np.median(signals[i:i + window]))
        solve_rate = float(chunk.mean())
        curve.append({
            "signal_midpoint": round(mid_signal, 3),
            "solve_rate": round(solve_rate, 3),
            "count": len(chunk),
        })

    # Find steepest drop
    max_gradient = 0
    transition_point = None
    for i in range(len(curve) - 1):
        gradient = abs(curve[i + 1]["solve_rate"] - curve[i]["solve_rate"])
        if gradient > max_gradient:
            max_gradient = gradient
            transition_point = (curve[i]["signal_midpoint"] + curve[i + 1]["signal_midpoint"]) / 2

    # Phase transition width: range over which solve rate goes from 0.8 to 0.2
    high_idx = None
    low_idx = None
    for c in curve:
        if c["solve_rate"] >= 0.7 and high_idx is None:
            high_idx = c["signal_midpoint"]
        if c["solve_rate"] <= 0.3:
            low_idx = c["signal_midpoint"]
            break

    transition_width = None
    if high_idx is not None and low_idx is not None:
        transition_width = round(low_idx - high_idx, 3)

    return {
        "n_problems": n,
        "curve": curve,
        "max_gradient": round(max_gradient, 3),
        "transition_point": round(transition_point, 3) if transition_point else None,
        "transition_width": transition_width,
        "has_sharp_transition": max_gradient > 0.3,
        "has_phase_transition": transition_width is not None and transition_width < 0.15,
    }


# ══════════════════════════════════════════════════════════════════════
# Meta-Conjecture 6: Tag Ecosystem Dynamics
# ══════════════════════════════════════════════════════════════════════

def tag_ecosystem(problems: List[Dict]) -> Dict[str, Any]:
    """
    Model the tag space as an ecosystem where tags compete, cooperate,
    and evolve.

    Key metrics:
    - Tag "fitness": solve rate (solved tags are fitter)
    - Tag "niche overlap": Jaccard similarity of problem sets
    - Tag "predation": does solving in tag A reduce open problems in tag B?
    - Tag "mutualism": do tags co-occur more in solved problems?
    """
    tag_problems = defaultdict(set)
    tag_solved = defaultdict(set)
    tag_open = defaultdict(set)

    for p in problems:
        num = _number(p)
        for tag in _tags(p):
            tag_problems[tag].add(num)
            if _is_solved(p):
                tag_solved[tag].add(num)
            elif _is_open(p):
                tag_open[tag].add(num)

    # Filter to tags with enough problems
    min_count = 10
    active_tags = [t for t in tag_problems if len(tag_problems[t]) >= min_count]

    # Tag fitness (solve rate)
    fitness = {}
    for tag in active_tags:
        total = len(tag_solved[tag]) + len(tag_open[tag])
        if total > 0:
            fitness[tag] = len(tag_solved[tag]) / total

    # Tag niche overlap matrix
    niche_overlap = {}
    for t1, t2 in combinations(active_tags, 2):
        intersection = len(tag_problems[t1] & tag_problems[t2])
        union = len(tag_problems[t1] | tag_problems[t2])
        if union > 0:
            jaccard = intersection / union
            if jaccard > 0.1:  # significant overlap
                niche_overlap[(t1, t2)] = round(jaccard, 3)

    # Mutualism: tags that co-occur disproportionately in solved problems
    mutualism = []
    for (t1, t2), overlap in sorted(niche_overlap.items(), key=lambda x: -x[1])[:30]:
        both_problems = tag_problems[t1] & tag_problems[t2]
        both_solved = tag_solved[t1] & tag_solved[t2]
        if len(both_problems) >= 5:
            joint_rate = len(both_solved) / len(both_problems)
            expected = fitness.get(t1, 0.5) * fitness.get(t2, 0.5)
            mutualism.append({
                "tags": (t1, t2),
                "joint_solve_rate": round(joint_rate, 3),
                "expected_independent": round(expected, 3),
                "synergy": round(joint_rate - expected, 3),
                "n_shared": len(both_problems),
            })

    mutualism.sort(key=lambda x: -x["synergy"])

    # Dominant tags: high fitness + large niche
    dominance = []
    for tag in active_tags:
        if tag in fitness:
            dominance.append({
                "tag": tag,
                "fitness": round(fitness[tag], 3),
                "niche_size": len(tag_problems[tag]),
                "dominance_score": round(fitness[tag] * math.log2(len(tag_problems[tag]) + 1), 3),
            })
    dominance.sort(key=lambda x: -x["dominance_score"])

    return {
        "n_active_tags": len(active_tags),
        "avg_fitness": round(float(np.mean(list(fitness.values()))), 3),
        "fitness_std": round(float(np.std(list(fitness.values()))), 3),
        "n_significant_overlaps": len(niche_overlap),
        "top_mutualistic_pairs": mutualism[:10],
        "dominant_tags": dominance[:15],
        "ecosystem_diversity": round(float(-sum(
            (len(tag_problems[t]) / sum(len(tag_problems[t2]) for t2 in active_tags)) *
            math.log2(len(tag_problems[t]) / sum(len(tag_problems[t2]) for t2 in active_tags) + 1e-10)
            for t in active_tags
        )), 3),
    }


# ══════════════════════════════════════════════════════════════════════
# Meta-Conjecture 7: Problem Complexity Classes
# ══════════════════════════════════════════════════════════════════════

def complexity_classes(problems: List[Dict]) -> Dict[str, Any]:
    """
    Can Erdős problems be classified into "complexity classes" analogous
    to P, NP, etc., based on structural features?

    Define:
    - E (Easy): tag_solve_rate > 0.6, no prize, n_tags < 3
    - M (Medium): 0.3 < tag_solve_rate < 0.6, or small prize
    - H (Hard): tag_solve_rate < 0.3, or prize > $500
    - U (Ultra): formalized + open + prize + old

    Test: do these classes predict solvability better than random?
    """
    tag_solve_rates = defaultdict(list)
    for p in problems:
        solved = _is_solved(p)
        for tag in _tags(p):
            tag_solve_rates[tag].append(1.0 if solved else 0.0)

    tag_avg = {tag: np.mean(vals)
               for tag, vals in tag_solve_rates.items()
               if len(vals) >= 3}

    classes = {"E": [], "M": [], "H": [], "U": []}
    for p in problems:
        if not (_is_solved(p) or _is_open(p)):
            continue

        tags = _tags(p)
        if not tags:
            continue

        avg_rate = np.mean([tag_avg.get(t, 0.5) for t in tags])
        prize = _prize(p)
        num = _number(p)
        formalized = _is_formalized(p)

        # Classification
        if formalized and _is_open(p) and prize > 0 and num < 200:
            cls = "U"
        elif avg_rate < 0.3 or prize > 500:
            cls = "H"
        elif avg_rate > 0.6 and prize == 0 and len(tags) < 3:
            cls = "E"
        else:
            cls = "M"

        classes[cls].append({
            "number": num,
            "solved": _is_solved(p),
            "avg_tag_rate": round(avg_rate, 3),
            "prize": prize,
        })

    # Solve rates by class
    class_stats = {}
    for cls, members in classes.items():
        if not members:
            continue
        n_solved = sum(1 for m in members if m["solved"])
        n_total = len(members)
        class_stats[cls] = {
            "count": n_total,
            "solve_rate": round(n_solved / n_total, 3),
            "avg_prize": round(float(np.mean([m["prize"] for m in members])), 1),
        }

    # Check monotonicity: E > M > H > U in solve rate
    order = ["E", "M", "H", "U"]
    rates = [class_stats[c]["solve_rate"] for c in order if c in class_stats]
    is_monotone = all(rates[i] >= rates[i + 1] - 0.01 for i in range(len(rates) - 1))

    return {
        "class_stats": class_stats,
        "is_monotone": is_monotone,
        "total_classified": sum(s["count"] for s in class_stats.values()),
        "separation_quality": _separation_quality(class_stats),
    }


def _separation_quality(stats: Dict) -> str:
    """How well do complexity classes separate solved from open?"""
    if not stats:
        return "insufficient_data"
    rates = [s["solve_rate"] for s in stats.values()]
    if max(rates) - min(rates) > 0.5:
        return "excellent"
    elif max(rates) - min(rates) > 0.3:
        return "good"
    elif max(rates) - min(rates) > 0.15:
        return "moderate"
    else:
        return "poor"


# ══════════════════════════════════════════════════════════════════════
# Report Generation
# ══════════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    """Generate comprehensive meta-conjectures report."""
    lines = [
        "# Meta-Conjectures: Structural Laws About Problem Ensembles",
        "",
        "These are conjectures *about* the Erdős problem corpus itself —",
        "patterns about patterns, laws about mathematical difficulty.",
        "",
    ]

    # 1. Formalization paradox
    lines.append("## 1. The Formalization Paradox — Causal Analysis")
    form = formalization_causal_analysis(problems)
    lines.append(f"**Overall**: formalized solve rate = {form['overall_formalized_solve_rate']}, "
                 f"unformalized = {form['overall_unformalized_solve_rate']}")
    lines.append(f"**Gap**: {form['overall_gap']} (non-formalized solve MORE)")
    lines.append(f"**Mantel-Haenszel OR**: {form['mantel_haenszel_or']} "
                 f"({form['mh_interpretation']})")
    lines.append(f"**Strata where paradox holds**: {form['paradox_holds_in_strata']}/{form['strata_analyzed']}")
    lines.append(f"**Strata where paradox reverses**: {form['paradox_reverses_in_strata']}/{form['strata_analyzed']}")
    lines.append("")
    lines.append("### Per-Tag Stratification (top by gap magnitude)")
    for s in form["strata_details"][:10]:
        lines.append(f"- **{s['tag']}**: form={s['form_rate']}, no-form={s['noform_rate']}, "
                     f"gap={s['gap']} (n_form={s['form_n']}, n_noform={s['noform_n']})")
    lines.append("")

    # 2. Scaling law
    lines.append("## 2. Universal Solvability Scaling Law")
    scaling = solvability_scaling(problems)
    lines.append(f"**Logistic regression accuracy**: {scaling['accuracy']} "
                 f"(base rate: {scaling['base_rate']})")
    lines.append(f"**Scaling interpretation**: {scaling['scaling_law']}")
    lines.append("**Coefficients**:")
    for name, coeff in scaling["coefficients"].items():
        lines.append(f"  - {name}: {coeff}")
    lines.append("**Calibration**:")
    for c in scaling["calibration"]:
        lines.append(f"  - {c['bin']}: predicted={c['predicted']}, "
                     f"actual={c['actual']} (n={c['count']})")
    lines.append("")

    # 3. Hard center
    lines.append("## 3. The Hard-Center Conjecture")
    hc = hard_center_analysis(problems)
    lines.append(f"**Spearman(tractability, impact)**: {hc['spearman_correlation']}")
    lines.append(f"**Pearson**: {hc['pearson_correlation']}")
    lines.append(f"**Hard center**: {hc['hard_center_count']} problems")
    lines.append(f"**Easy wins**: {hc['easy_win_count']} problems")
    lines.append(f"**Effect size**: {hc['effect_size']}")
    if hc.get("hard_center_top10"):
        lines.append("**Top hard-center problems**:")
        for p in hc["hard_center_top10"]:
            lines.append(f"  - #{p['number']}: tract={p['tractability']}, impact={p['impact']}")
    lines.append("")

    # 4. Prize monotonicity
    lines.append("## 4. Prize Monotonicity Theorem")
    pm = prize_monotonicity(problems)
    lines.append(f"**Is monotone**: {pm['is_monotone']}")
    lines.append(f"**Kendall's tau**: {pm['kendall_tau']}")
    for b in pm["brackets"]:
        lines.append(f"  - {b['bracket']}: {b['open_rate']*100:.0f}% open "
                     f"(n={b['n_total']}, avg_tags={b['avg_tags']})")
    lines.append("")

    # 5. Phase transition
    lines.append("## 5. Solvability Phase Transition")
    pt = solvability_phase_transition(problems)
    lines.append(f"**Has sharp transition**: {pt['has_sharp_transition']}")
    lines.append(f"**Transition point**: {pt['transition_point']}")
    lines.append(f"**Transition width**: {pt['transition_width']}")
    lines.append(f"**Max gradient**: {pt['max_gradient']}")
    lines.append("**Solvability curve**:")
    for c in pt["curve"]:
        bar = "#" * int(c["solve_rate"] * 20)
        lines.append(f"  signal={c['signal_midpoint']:.3f}: {bar} ({c['solve_rate']:.2f}, n={c['count']})")
    lines.append("")

    # 6. Tag ecosystem
    lines.append("## 6. Tag Ecosystem Dynamics")
    eco = tag_ecosystem(problems)
    lines.append(f"**Active tags**: {eco['n_active_tags']}")
    lines.append(f"**Average fitness**: {eco['avg_fitness']} (std={eco['fitness_std']})")
    lines.append(f"**Ecosystem diversity (bits)**: {eco['ecosystem_diversity']}")
    lines.append("**Dominant tags**:")
    for d in eco["dominant_tags"][:10]:
        lines.append(f"  - **{d['tag']}**: fitness={d['fitness']}, "
                     f"niche={d['niche_size']}, dominance={d['dominance_score']}")
    if eco["top_mutualistic_pairs"]:
        lines.append("**Mutualistic pairs** (synergy in joint solve rate):")
        for m in eco["top_mutualistic_pairs"][:5]:
            lines.append(f"  - {m['tags']}: joint={m['joint_solve_rate']}, "
                         f"expected={m['expected_independent']}, synergy={m['synergy']}")
    lines.append("")

    # 7. Complexity classes
    lines.append("## 7. Problem Complexity Classes")
    cc = complexity_classes(problems)
    lines.append(f"**Separation quality**: {cc['separation_quality']}")
    lines.append(f"**Monotone (E > M > H > U)**: {cc['is_monotone']}")
    for cls in ["E", "M", "H", "U"]:
        if cls in cc["class_stats"]:
            s = cc["class_stats"][cls]
            lines.append(f"  - **Class {cls}**: {s['count']} problems, "
                         f"solve rate={s['solve_rate']}, avg_prize=${s['avg_prize']}")
    lines.append("")

    return "\n".join(lines)


def main():
    problems = load_problems()

    print("=" * 70)
    print("META-CONJECTURES ENGINE")
    print(f"Analyzing {len(problems)} Erdős problems for structural laws")
    print("=" * 70)
    print()

    report = generate_report(problems)
    print(report)

    REPORT_PATH.write_text(report)
    print(f"\nReport written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
