#!/usr/bin/env python3
"""
resolution_predictor.py — Predict which open problems will be resolved next.

Uses a leave-one-out cross-validated k-nearest-neighbor approach on the
multi-dimensional signal space to estimate "resolution probability" for
each open problem.

Key question: Given a problem's structural features (tag solve rate,
OEIS richness, tag diversity, age, prize, formalization, tag popularity,
OEIS exclusivity), how similar is it to already-solved problems?

This is fundamentally different from the predictive_model.py module which
uses logistic regression. KNN captures nonlinear boundaries and local
structure in the signal space.

Analyses:
  1. Resolution probability: KNN probability estimate for each open problem
  2. Feature importance: which dimensions most discriminate solved from open
  3. Calibration: how well do the predicted probabilities match actual rates
  4. Surprise problems: solved problems that "shouldn't have been" (low predicted prob)
  5. Stuck problems: high-probability open problems that haven't been solved
  6. Tag resolution forecast: expected solve rates per tag in next "wave"

Output: docs/resolution_predictor_report.md
"""

import math
import yaml
import numpy as np
from collections import defaultdict, Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "resolution_predictor_report.md"


def load_problems() -> List[Dict]:
    with open(DATA_PATH) as f:
        return yaml.safe_load(f)


def _status(p: Dict) -> str:
    return p.get("status", {}).get("state", "unknown")


def _tags(p: Dict) -> Set[str]:
    return set(p.get("tags", []))


def _number(p: Dict) -> int:
    n = p.get("number", 0)
    return int(n) if isinstance(n, (int, str)) and str(n).isdigit() else 0


def _oeis(p: Dict) -> Set[str]:
    refs = p.get("oeis", [])
    return set(refs) if isinstance(refs, list) else set()


def _is_solved(p: Dict) -> bool:
    return _status(p) in ("proved", "disproved", "solved",
                           "proved (Lean)", "disproved (Lean)", "solved (Lean)")


def _is_open(p: Dict) -> bool:
    return _status(p) == "open"


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


# ═══════════════════════════════════════════════════════════════════
# Build Feature Matrix
# ═══════════════════════════════════════════════════════════════════

def build_features(problems: List[Dict]) -> Dict[str, Any]:
    """
    Build feature matrix for resolution prediction.
    Excludes 'is_solved' (that's the target) and 'formalized' (leaks info).

    Features (7 dims):
    - tag_solve_rate, oeis_richness, tag_diversity, problem_age,
      prize_signal, tag_popularity, oeis_exclusivity
    """
    # Precompute tag stats
    tag_solved = Counter()
    tag_total = Counter()
    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _is_solved(p):
                tag_solved[t] += 1
    tag_rate = {t: tag_solved[t] / tag_total[t] for t in tag_total if tag_total[t] > 0}

    # OEIS frequency
    oeis_freq = Counter()
    for p in problems:
        for seq in _oeis(p):
            if seq not in ("N/A", "possible", "n/a", "none", ""):
                oeis_freq[seq] += 1

    max_oeis = max((len(_oeis(p) - {"N/A", "possible"}) for p in problems), default=1)
    max_tags = max((len(_tags(p)) for p in problems), default=1)
    max_num = max((_number(p) for p in problems), default=1)
    max_pop = max(tag_total.values()) if tag_total else 1

    dim_names = [
        "tag_solve_rate", "oeis_richness", "tag_diversity",
        "problem_age", "prize_signal", "tag_popularity", "oeis_exclusivity",
    ]

    features = []
    numbers = []
    labels = []  # 1=solved, 0=open

    for p in problems:
        tags = _tags(p)
        oeis = _oeis(p) - {"N/A", "possible", "n/a", "none", ""}

        rates = [tag_rate.get(t, 0.3) for t in tags] if tags else [0.3]
        avg_rate = sum(rates) / len(rates)

        oeis_r = len(oeis) / max_oeis if max_oeis > 0 else 0
        tag_div = len(tags) / max_tags if max_tags > 0 else 0
        age = 1.0 - (_number(p) / max_num) if max_num > 0 else 0.5

        prize = _prize(p)
        prize_sig = min(math.log1p(prize) / math.log1p(10000), 1.0) if prize > 0 else 0.0

        pops = [tag_total.get(t, 1) for t in tags] if tags else [1]
        tag_pop = sum(pops) / len(pops) / max_pop

        if oeis:
            exclusive = sum(1 for s in oeis if oeis_freq.get(s, 0) <= 3) / len(oeis)
        else:
            exclusive = 0.0

        features.append([avg_rate, oeis_r, tag_div, age, prize_sig, tag_pop, exclusive])
        numbers.append(_number(p))

        if _is_solved(p):
            labels.append(1)
        elif _is_open(p):
            labels.append(0)
        else:
            labels.append(-1)  # Unknown/other status

    return {
        "features": np.array(features),
        "dim_names": dim_names,
        "numbers": numbers,
        "labels": np.array(labels),
        "prob_by_num": {_number(p): p for p in problems},
    }


# ═══════════════════════════════════════════════════════════════════
# KNN Resolution Probability
# ═══════════════════════════════════════════════════════════════════

def predict_resolution(problems: List[Dict],
                       feature_data: Optional[Dict] = None,
                       k: int = 15) -> List[Dict[str, Any]]:
    """
    For each open problem, estimate resolution probability using KNN
    on the standardized feature space.

    probability = (# of k nearest neighbors that are solved) / k

    Returns list sorted by probability descending, with:
    - number, probability, tags, prize, nearest_solved_problems
    """
    if feature_data is None:
        feature_data = build_features(problems)

    F = feature_data["features"]
    numbers = feature_data["numbers"]
    labels = feature_data["labels"]
    prob_by_num = feature_data["prob_by_num"]

    # Standardize
    means = F.mean(axis=0)
    stds = F.std(axis=0)
    stds[stds == 0] = 1.0
    X = (F - means) / stds

    # Find solved and open indices
    solved_or_open = np.where(labels >= 0)[0]  # exclude unknown
    open_indices = np.where(labels == 0)[0]

    results = []
    for oi in open_indices:
        # Distance to all solved-or-open problems (excluding self)
        others = solved_or_open[solved_or_open != oi]
        dists = np.sqrt(np.sum((X[others] - X[oi]) ** 2, axis=1))

        # K nearest neighbors
        k_actual = min(k, len(others))
        nearest_idx = np.argsort(dists)[:k_actual]
        nearest_labels = labels[others[nearest_idx]]

        # Probability = fraction of neighbors that are solved
        prob = float(np.mean(nearest_labels == 1))

        # Find nearest solved for reference
        solved_mask = nearest_labels == 1
        nearest_solved = [int(numbers[others[nearest_idx[j]]])
                          for j in range(k_actual) if nearest_labels[j] == 1][:3]

        p = prob_by_num.get(numbers[oi], {})
        results.append({
            "number": numbers[oi],
            "probability": prob,
            "tags": sorted(_tags(p)),
            "prize": _prize(p),
            "nearest_solved": nearest_solved,
        })

    results.sort(key=lambda r: -r["probability"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Leave-One-Out Cross-Validation
# ═══════════════════════════════════════════════════════════════════

def cross_validate(problems: List[Dict],
                   feature_data: Optional[Dict] = None,
                   k: int = 15) -> Dict[str, Any]:
    """
    Leave-one-out cross-validation: for each solved/open problem, predict
    its label using KNN on the remaining problems.

    Returns accuracy, precision, recall, and calibration data.
    """
    if feature_data is None:
        feature_data = build_features(problems)

    F = feature_data["features"]
    labels = feature_data["labels"]
    numbers = feature_data["numbers"]

    means = F.mean(axis=0)
    stds = F.std(axis=0)
    stds[stds == 0] = 1.0
    X = (F - means) / stds

    valid = np.where(labels >= 0)[0]
    predictions = []
    actuals = []

    for vi in valid:
        others = valid[valid != vi]
        dists = np.sqrt(np.sum((X[others] - X[vi]) ** 2, axis=1))
        k_actual = min(k, len(others))
        nearest_idx = np.argsort(dists)[:k_actual]
        nearest_labels = labels[others[nearest_idx]]
        prob = float(np.mean(nearest_labels == 1))
        predictions.append(prob)
        actuals.append(labels[vi])

    predictions = np.array(predictions)
    actuals = np.array(actuals)

    # Metrics
    pred_labels = (predictions >= 0.5).astype(int)
    accuracy = float(np.mean(pred_labels == actuals))

    tp = int(np.sum((pred_labels == 1) & (actuals == 1)))
    fp = int(np.sum((pred_labels == 1) & (actuals == 0)))
    fn = int(np.sum((pred_labels == 0) & (actuals == 1)))
    tn = int(np.sum((pred_labels == 0) & (actuals == 0)))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    # Calibration: bin predictions into deciles
    bins = np.linspace(0, 1, 11)
    calibration = []
    for i in range(10):
        mask = (predictions >= bins[i]) & (predictions < bins[i + 1])
        if mask.sum() > 0:
            predicted_avg = float(predictions[mask].mean())
            actual_avg = float(actuals[mask].mean())
            calibration.append({
                "bin": f"{bins[i]:.1f}-{bins[i+1]:.1f}",
                "predicted": predicted_avg,
                "actual": actual_avg,
                "count": int(mask.sum()),
            })

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "n_valid": len(valid),
        "calibration": calibration,
    }


# ═══════════════════════════════════════════════════════════════════
# Feature Importance — Permutation-Based
# ═══════════════════════════════════════════════════════════════════

def feature_importance(problems: List[Dict],
                       feature_data: Optional[Dict] = None,
                       k: int = 15) -> List[Dict[str, Any]]:
    """
    Compute feature importance by measuring accuracy drop when each
    feature is randomly permuted.

    Higher importance = more discriminative for solved vs open.
    """
    if feature_data is None:
        feature_data = build_features(problems)

    F = feature_data["features"].copy()
    labels = feature_data["labels"]
    dim_names = feature_data["dim_names"]

    means = F.mean(axis=0)
    stds = F.std(axis=0)
    stds[stds == 0] = 1.0

    valid = np.where(labels >= 0)[0]

    # Baseline accuracy (subsample for speed)
    rng = np.random.RandomState(42)
    sample = rng.choice(valid, size=min(200, len(valid)), replace=False)

    def compute_accuracy(X_input):
        correct = 0
        for vi in sample:
            others = valid[valid != vi]
            dists = np.sqrt(np.sum((X_input[others] - X_input[vi]) ** 2, axis=1))
            k_actual = min(k, len(others))
            nearest_idx = np.argsort(dists)[:k_actual]
            nearest_labels = labels[others[nearest_idx]]
            pred = 1 if np.mean(nearest_labels == 1) >= 0.5 else 0
            if pred == labels[vi]:
                correct += 1
        return correct / len(sample)

    X_base = (F - means) / stds
    baseline = compute_accuracy(X_base)

    results = []
    for d in range(len(dim_names)):
        X_perm = X_base.copy()
        rng.shuffle(X_perm[:, d])
        perm_acc = compute_accuracy(X_perm)
        drop = baseline - perm_acc

        results.append({
            "feature": dim_names[d],
            "importance": max(drop, 0.0),
            "baseline_accuracy": baseline,
            "permuted_accuracy": perm_acc,
        })

    results.sort(key=lambda r: -r["importance"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Surprise and Stuck Problems
# ═══════════════════════════════════════════════════════════════════

def surprise_problems(problems: List[Dict],
                      feature_data: Optional[Dict] = None,
                      k: int = 15) -> Dict[str, List[Dict]]:
    """
    Find:
    - Surprises: SOLVED problems with low predicted probability (≤ 0.3)
      These were "unexpectedly" solved — techniques from outside the usual.
    - Stuck: OPEN problems with high predicted probability (≥ 0.7)
      These "should have been" solved by now — something is blocking them.
    """
    if feature_data is None:
        feature_data = build_features(problems)

    F = feature_data["features"]
    labels = feature_data["labels"]
    numbers = feature_data["numbers"]
    prob_by_num = feature_data["prob_by_num"]

    means = F.mean(axis=0)
    stds = F.std(axis=0)
    stds[stds == 0] = 1.0
    X = (F - means) / stds

    valid = np.where(labels >= 0)[0]

    surprises = []
    stuck = []

    for vi in valid:
        others = valid[valid != vi]
        dists = np.sqrt(np.sum((X[others] - X[vi]) ** 2, axis=1))
        k_actual = min(k, len(others))
        nearest_idx = np.argsort(dists)[:k_actual]
        nearest_labels = labels[others[nearest_idx]]
        prob = float(np.mean(nearest_labels == 1))

        p = prob_by_num.get(numbers[vi], {})
        entry = {
            "number": numbers[vi],
            "predicted_prob": prob,
            "actual": "solved" if labels[vi] == 1 else "open",
            "tags": sorted(_tags(p)),
            "prize": _prize(p),
        }

        if labels[vi] == 1 and prob <= 0.3:
            surprises.append(entry)
        elif labels[vi] == 0 and prob >= 0.7:
            stuck.append(entry)

    surprises.sort(key=lambda s: s["predicted_prob"])
    stuck.sort(key=lambda s: -s["predicted_prob"])

    return {"surprises": surprises, "stuck": stuck}


# ═══════════════════════════════════════════════════════════════════
# Tag Resolution Forecast
# ═══════════════════════════════════════════════════════════════════

def tag_forecast(problems: List[Dict],
                 predictions: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
    """
    Aggregate resolution probabilities by tag to forecast which
    mathematical areas will see the most progress.

    Returns list sorted by expected_resolutions descending.
    """
    if predictions is None:
        predictions = predict_resolution(problems)

    pred_by_num = {p["number"]: p["probability"] for p in predictions}
    prob_by_num = {_number(p): p for p in problems}

    tag_probs = defaultdict(list)
    tag_open = Counter()
    tag_total = Counter()

    for p in problems:
        num = _number(p)
        for t in _tags(p):
            tag_total[t] += 1
            if _is_open(p):
                tag_open[t] += 1
                if num in pred_by_num:
                    tag_probs[t].append(pred_by_num[num])

    results = []
    for tag in tag_probs:
        probs = tag_probs[tag]
        if not probs:
            continue

        expected = sum(probs)
        avg_prob = sum(probs) / len(probs)

        results.append({
            "tag": tag,
            "expected_resolutions": expected,
            "avg_probability": avg_prob,
            "open_count": tag_open[tag],
            "total_count": tag_total[tag],
            "current_solve_rate": 1.0 - tag_open[tag] / tag_total[tag] if tag_total[tag] > 0 else 0,
        })

    results.sort(key=lambda r: -r["expected_resolutions"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    feature_data = build_features(problems)
    predictions = predict_resolution(problems, feature_data)
    cv = cross_validate(problems, feature_data)
    importance = feature_importance(problems, feature_data)
    sp = surprise_problems(problems, feature_data)
    forecast = tag_forecast(problems, predictions)

    lines = ["# Resolution Predictor: Which Problems Get Solved Next?", ""]
    lines.append(f"KNN-based resolution prediction for {len(predictions)} open problems.")
    lines.append("")

    # Section 1: Model Performance
    lines.append("## 1. Model Performance (Leave-One-Out CV)")
    lines.append("")
    lines.append(f"- **Accuracy**: {cv['accuracy']:.1%}")
    lines.append(f"- **Precision**: {cv['precision']:.1%}")
    lines.append(f"- **Recall**: {cv['recall']:.1%}")
    lines.append(f"- TP={cv['tp']}, FP={cv['fp']}, FN={cv['fn']}, TN={cv['tn']}")
    lines.append("")

    # Calibration
    lines.append("### Calibration")
    lines.append("| Predicted Range | Actual Rate | Count |")
    lines.append("|-----------------|-------------|-------|")
    for c in cv["calibration"]:
        lines.append(f"| {c['bin']} | {c['actual']:.1%} | {c['count']} |")
    lines.append("")

    # Section 2: Feature Importance
    lines.append("## 2. Feature Importance")
    lines.append("")
    lines.append(f"Baseline accuracy: {importance[0]['baseline_accuracy']:.1%}")
    lines.append("")
    lines.append("| Feature | Importance | Permuted Accuracy |")
    lines.append("|---------|------------|-------------------|")
    for fi in importance:
        bar = "█" * int(fi["importance"] * 100) if fi["importance"] > 0 else ""
        lines.append(f"| {fi['feature']} | {fi['importance']:.3f} {bar} | {fi['permuted_accuracy']:.1%} |")
    lines.append("")

    # Section 3: Top Predictions
    lines.append("## 3. Most Likely to Be Solved (Open Problems)")
    lines.append("")
    lines.append("| Rank | Problem | Probability | Tags | Prize | Nearest Solved |")
    lines.append("|------|---------|-------------|------|-------|----------------|")
    for i, pred in enumerate(predictions[:20]):
        tags_str = ", ".join(pred["tags"][:3])
        prize_str = f"${pred['prize']:.0f}" if pred["prize"] > 0 else "-"
        nearest_str = ", ".join(f"#{n}" for n in pred["nearest_solved"][:3])
        lines.append(f"| {i+1} | #{pred['number']} | {pred['probability']:.0%} | "
                      f"{tags_str} | {prize_str} | {nearest_str} |")
    lines.append("")

    # Section 4: Surprise and Stuck
    lines.append("## 4. Surprise Resolutions")
    lines.append("")
    lines.append(f"**{len(sp['surprises'])} solved problems** with predicted probability ≤ 30%")
    lines.append("(they were solved despite looking like they shouldn't have been).")
    lines.append("")
    if sp["surprises"]:
        lines.append("| Problem | Predicted | Tags | Prize |")
        lines.append("|---------|-----------|------|-------|")
        for s in sp["surprises"][:10]:
            tags_str = ", ".join(s["tags"][:3])
            prize_str = f"${s['prize']:.0f}" if s["prize"] > 0 else "-"
            lines.append(f"| #{s['number']} | {s['predicted_prob']:.0%} | {tags_str} | {prize_str} |")
    lines.append("")

    lines.append(f"### Stuck Problems")
    lines.append(f"**{len(sp['stuck'])} open problems** with predicted probability ≥ 70%")
    lines.append("(they should have been solved by now — something is blocking them).")
    lines.append("")
    if sp["stuck"]:
        lines.append("| Problem | Predicted | Tags | Prize |")
        lines.append("|---------|-----------|------|-------|")
        for s in sp["stuck"][:10]:
            tags_str = ", ".join(s["tags"][:3])
            prize_str = f"${s['prize']:.0f}" if s["prize"] > 0 else "-"
            lines.append(f"| #{s['number']} | {s['predicted_prob']:.0%} | {tags_str} | {prize_str} |")
    lines.append("")

    # Section 5: Tag Forecast
    lines.append("## 5. Tag Resolution Forecast")
    lines.append("")
    lines.append("| Tag | Expected Resolutions | Avg Prob | Open | Current Rate |")
    lines.append("|-----|---------------------|----------|------|--------------|")
    for f in forecast[:15]:
        lines.append(f"| {f['tag']} | {f['expected_resolutions']:.1f} | "
                      f"{f['avg_probability']:.0%} | {f['open_count']} | "
                      f"{f['current_solve_rate']:.0%} |")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    problems = load_problems()
    report = generate_report(problems)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")
