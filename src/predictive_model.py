#!/usr/bin/env python3
"""
predictive_model.py — Problem resolution forecasting.

Builds a logistic regression model trained on solved problems to predict
which open problems are most likely to be resolved next.

Features used:
  1. Tag solvability rates (continuous)
  2. OEIS connectivity (count)
  3. Technique match count
  4. Network degree centrality
  5. Prize amount (log scale)
  6. Tag count (complexity proxy)
  7. Formalization status
  8. Community membership (one-hot)

Output: docs/prediction_report.md
"""

import math
import yaml
import numpy as np
from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "prediction_report.md"


# ═══════════════════════════════════════════════════════════════════
# Data Loading
# ═══════════════════════════════════════════════════════════════════

def load_problems() -> List[Dict]:
    with open(DATA_PATH) as f:
        return yaml.safe_load(f)


def _status(p: Dict) -> str:
    return p.get("status", {}).get("state", "unknown")


def _tags(p: Dict) -> Set[str]:
    return set(p.get("tags", []))


def _oeis(p: Dict) -> List[str]:
    return p.get("oeis", [])


def _number(p: Dict) -> int:
    n = p.get("number", 0)
    return int(n) if isinstance(n, (int, str)) and str(n).isdigit() else 0


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
# Feature Engineering
# ═══════════════════════════════════════════════════════════════════

def compute_features(problems: List[Dict]) -> Tuple[np.ndarray, np.ndarray, List[Dict], List[str]]:
    """
    Compute feature matrix for all problems.

    Returns:
        X: feature matrix (n_problems × n_features)
        y: labels (1 = solved, 0 = open)
        problem_info: list of dicts with number/tags/status
        feature_names: list of feature name strings
    """
    # Precompute tag solve rates
    tag_total = Counter()
    tag_solved = Counter()
    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _status(p) in ("proved", "disproved"):
                tag_solved[t] += 1
    tag_rates = {t: tag_solved[t] / tag_total[t] for t in tag_total if tag_total[t] > 0}

    # Precompute OEIS solved counts
    oeis_solved_count = Counter()
    for p in problems:
        if _status(p) in ("proved", "disproved"):
            for seq in _oeis(p):
                oeis_solved_count[seq] += 1

    # Technique map
    tech_map = {
        "fourier_density": {"number theory", "additive combinatorics"},
        "coprime_cycle": {"graph theory", "cycles"},
        "sidon": {"sidon sets"},
        "prime_mobius": {"primes", "number theory"},
        "ramsey": {"ramsey theory"},
        "chromatic": {"chromatic number"},
        "additive_basis": {"additive basis"},
        "primitive_sets": {"primitive sets"},
        "arithmetic_prog": {"arithmetic progressions"},
        "graph_turan": {"graph theory", "turan number"},
    }

    # Major tag set for one-hot
    major_tags = [t for t, c in tag_total.most_common(15)]

    feature_names = [
        "avg_tag_solve_rate",
        "max_tag_solve_rate",
        "min_tag_solve_rate",
        "n_tags",
        "n_oeis",
        "oeis_solved_bridges",
        "technique_match_count",
        "prize_log",
        "formalized",
    ] + [f"tag_{t.replace(' ', '_')}" for t in major_tags]

    X_rows = []
    y_vec = []
    info = []

    for p in problems:
        status = _status(p)
        if status not in ("open", "proved", "disproved"):
            continue

        tags = _tags(p)
        oeis = _oeis(p)

        # Tag solvability features
        rates = [tag_rates.get(t, 0.0) for t in tags] or [0.0]
        avg_rate = np.mean(rates)
        max_rate = max(rates)
        min_rate = min(rates)

        # OEIS bridge count
        oeis_bridges = sum(oeis_solved_count.get(s, 0) for s in oeis)

        # Technique matches
        tech_matches = 0
        for tech_name, tech_tags in tech_map.items():
            overlap = tags & tech_tags
            if overlap == tech_tags:
                tech_matches += 2
            elif overlap:
                tech_matches += 1

        # Other features
        prize = _prize(p)
        is_formalized = float(bool(p.get("formalized", {}).get("lean", False) or
                                  p.get("formalized", {}).get("isabelle", False)))

        # Major tag one-hot
        tag_features = [1.0 if t in tags else 0.0 for t in major_tags]

        row = [
            avg_rate,
            max_rate,
            min_rate,
            len(tags),
            len(oeis),
            min(oeis_bridges, 20),  # cap
            tech_matches,
            math.log1p(prize),
            is_formalized,
        ] + tag_features

        X_rows.append(row)
        y_vec.append(1 if status in ("proved", "disproved") else 0)
        info.append({
            "number": _number(p),
            "tags": sorted(tags),
            "status": status,
            "prize": prize,
        })

    return np.array(X_rows), np.array(y_vec), info, feature_names


# ═══════════════════════════════════════════════════════════════════
# Logistic Regression Model (numpy-only, no sklearn dependency)
# ═══════════════════════════════════════════════════════════════════

def _sigmoid(z):
    """Numerically stable sigmoid."""
    z = np.clip(z, -500, 500)
    return 1.0 / (1.0 + np.exp(-z))


def train_logistic_regression(
    X: np.ndarray, y: np.ndarray,
    lr: float = 0.01, n_iter: int = 500, reg: float = 0.1
) -> Tuple[np.ndarray, float]:
    """
    Train L2-regularized logistic regression via gradient descent.

    Returns (weights, bias).
    """
    n, d = X.shape
    # Standardize features
    mean = X.mean(axis=0)
    std = X.std(axis=0) + 1e-8
    X_norm = (X - mean) / std

    w = np.zeros(d)
    b = 0.0

    for iteration in range(n_iter):
        z = X_norm @ w + b
        pred = _sigmoid(z)
        error = pred - y

        # Gradients with L2 regularization
        dw = (X_norm.T @ error) / n + reg * w
        db = error.mean()

        w -= lr * dw
        b -= lr * db

    return w, b, mean, std


def predict_probabilities(
    X: np.ndarray, w: np.ndarray, b: float,
    mean: np.ndarray, std: np.ndarray
) -> np.ndarray:
    """Predict probability of being solved."""
    X_norm = (X - mean) / std
    return _sigmoid(X_norm @ w + b)


# ═══════════════════════════════════════════════════════════════════
# Cross-Validation & Feature Importance
# ═══════════════════════════════════════════════════════════════════

def cross_validate(X: np.ndarray, y: np.ndarray, n_folds: int = 5) -> Dict[str, Any]:
    """
    k-fold cross-validation for the logistic regression model.

    Returns accuracy, precision, recall for each fold.
    """
    n = len(y)
    indices = np.arange(n)
    np.random.seed(42)
    np.random.shuffle(indices)

    fold_size = n // n_folds
    fold_results = []

    for fold in range(n_folds):
        test_idx = indices[fold * fold_size:(fold + 1) * fold_size]
        train_idx = np.concatenate([indices[:fold * fold_size],
                                    indices[(fold + 1) * fold_size:]])

        X_train, y_train = X[train_idx], y[train_idx]
        X_test, y_test = X[test_idx], y[test_idx]

        w, b, mean, std = train_logistic_regression(X_train, y_train)
        probs = predict_probabilities(X_test, w, b, mean, std)
        preds = (probs >= 0.5).astype(int)

        accuracy = np.mean(preds == y_test)
        # Precision/recall for class 1 (solved)
        tp = np.sum((preds == 1) & (y_test == 1))
        fp = np.sum((preds == 1) & (y_test == 0))
        fn = np.sum((preds == 0) & (y_test == 1))

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)

        fold_results.append({
            "accuracy": round(accuracy, 3),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
        })

    avg_acc = np.mean([f["accuracy"] for f in fold_results])
    avg_prec = np.mean([f["precision"] for f in fold_results])
    avg_rec = np.mean([f["recall"] for f in fold_results])

    return {
        "folds": fold_results,
        "avg_accuracy": round(avg_acc, 3),
        "avg_precision": round(avg_prec, 3),
        "avg_recall": round(avg_rec, 3),
    }


def feature_importance(
    w: np.ndarray, std: np.ndarray, feature_names: List[str]
) -> List[Tuple[str, float]]:
    """
    Compute feature importance as |w_i / std_i| (standardized weights).
    """
    importance = np.abs(w)
    ranked = sorted(zip(feature_names, importance), key=lambda x: -x[1])
    return [(name, round(float(imp), 4)) for name, imp in ranked]


# ═══════════════════════════════════════════════════════════════════
# Prediction Pipeline
# ═══════════════════════════════════════════════════════════════════

def predict_next_solved(problems: List[Dict], top_k: int = 30) -> Dict[str, Any]:
    """
    Full prediction pipeline: train model, predict on open problems,
    return ranked predictions.
    """
    X, y, info, feature_names = compute_features(problems)

    # Cross-validation
    cv_results = cross_validate(X, y)

    # Train on full data
    w, b, mean, std = train_logistic_regression(X, y)

    # Feature importance
    importance = feature_importance(w, std, feature_names)

    # Predict on open problems
    open_mask = np.array([i["status"] == "open" for i in info])
    X_open = X[open_mask]
    info_open = [i for i, m in zip(info, open_mask) if m]

    probs = predict_probabilities(X_open, w, b, mean, std)

    # Rank predictions
    predictions = []
    for i, prob in enumerate(probs):
        predictions.append({
            "number": info_open[i]["number"],
            "tags": info_open[i]["tags"],
            "prize": info_open[i]["prize"],
            "predicted_solvability": round(float(prob), 4),
        })

    predictions.sort(key=lambda x: -x["predicted_solvability"])

    # Calibration check: solved problems should have higher scores
    solved_mask = np.array([i["status"] in ("proved", "disproved") for i in info])
    solved_probs = predict_probabilities(X[solved_mask], w, b, mean, std)
    open_probs_scores = probs

    return {
        "cv_results": cv_results,
        "feature_importance": importance,
        "top_predictions": predictions[:top_k],
        "model_stats": {
            "n_features": len(feature_names),
            "n_train": int(np.sum(~open_mask)),
            "n_predict": int(np.sum(open_mask)),
            "solved_mean_score": round(float(np.mean(solved_probs)), 3),
            "open_mean_score": round(float(np.mean(open_probs_scores)), 3),
            "score_separation": round(float(np.mean(solved_probs) - np.mean(open_probs_scores)), 3),
        },
    }


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(results: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Erdős Problem Resolution Predictions")
    lines.append("")
    lines.append("Logistic regression model trained on solved/disproved problems")
    lines.append("to predict which open problems are most likely to be resolved next.")
    lines.append("")

    # Model Performance
    lines.append("## 1. Model Performance")
    lines.append("")
    cv = results["cv_results"]
    lines.append(f"- **5-fold CV accuracy**: {cv['avg_accuracy']:.1%}")
    lines.append(f"- **Precision** (solved class): {cv['avg_precision']:.1%}")
    lines.append(f"- **Recall** (solved class): {cv['avg_recall']:.1%}")
    lines.append("")

    lines.append("### Per-Fold Results")
    lines.append("")
    lines.append("| Fold | Accuracy | Precision | Recall |")
    lines.append("|------|----------|-----------|--------|")
    for i, f in enumerate(cv["folds"]):
        lines.append(f"| {i+1} | {f['accuracy']:.1%} | {f['precision']:.1%} | {f['recall']:.1%} |")
    lines.append("")

    # Model Statistics
    stats = results["model_stats"]
    lines.append("## 2. Model Statistics")
    lines.append("")
    lines.append(f"- Features: {stats['n_features']}")
    lines.append(f"- Training set (solved): {stats['n_train']}")
    lines.append(f"- Prediction set (open): {stats['n_predict']}")
    lines.append(f"- Mean score (solved): {stats['solved_mean_score']:.3f}")
    lines.append(f"- Mean score (open): {stats['open_mean_score']:.3f}")
    lines.append(f"- Score separation: {stats['score_separation']:.3f}")
    lines.append("")

    # Feature Importance
    lines.append("## 3. Feature Importance")
    lines.append("")
    lines.append("| Rank | Feature | Importance |")
    lines.append("|------|---------|-----------|")
    for i, (name, imp) in enumerate(results["feature_importance"][:15]):
        lines.append(f"| {i+1} | {name} | {imp:.4f} |")
    lines.append("")

    # Top Predictions
    lines.append("## 4. Top Predictions — Most Likely to Fall")
    lines.append("")
    lines.append("| Rank | Problem | Predicted Solvability | Tags | Prize |")
    lines.append("|------|---------|---------------------|------|-------|")
    for i, pred in enumerate(results["top_predictions"][:25]):
        tags = ", ".join(pred["tags"][:3])
        prize = f"${pred['prize']:.0f}" if pred["prize"] > 0 else "-"
        lines.append(f"| {i+1} | #{pred['number']} | {pred['predicted_solvability']:.3f} | {tags} | {prize} |")
    lines.append("")

    # High-Value Targets (prize × solvability)
    lines.append("## 5. High-Value Targets (Prize × Solvability)")
    lines.append("")
    valued = [p for p in results["top_predictions"] if p["prize"] > 0]
    valued.sort(key=lambda x: -x["predicted_solvability"] * x["prize"])
    lines.append("| Problem | Predicted Solvability | Prize | Expected Value |")
    lines.append("|---------|---------------------|-------|---------------|")
    for p in valued[:10]:
        ev = p["predicted_solvability"] * p["prize"]
        lines.append(f"| #{p['number']} | {p['predicted_solvability']:.3f} | ${p['prize']:.0f} | ${ev:.0f} |")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("PROBLEM RESOLUTION PREDICTOR")
    print("=" * 70)

    problems = load_problems()
    print(f"Loaded {len(problems)} problems")

    print("\nTraining predictive model...")
    results = predict_next_solved(problems)

    cv = results["cv_results"]
    print(f"\nModel Performance:")
    print(f"  Accuracy: {cv['avg_accuracy']:.1%}")
    print(f"  Precision: {cv['avg_precision']:.1%}")
    print(f"  Recall: {cv['avg_recall']:.1%}")

    print(f"\nTop 5 predictions:")
    for i, pred in enumerate(results["top_predictions"][:5]):
        print(f"  {i+1}. #{pred['number']} (p={pred['predicted_solvability']:.3f}): {', '.join(pred['tags'][:3])}")

    print("\nGenerating report...")
    report = generate_report(results)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"Saved to {REPORT_PATH}")

    print("\n" + "=" * 70)
    print("PREDICTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
