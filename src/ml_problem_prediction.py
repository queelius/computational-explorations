#!/usr/bin/env python3
"""
ml_problem_prediction.py -- Predictive models for Erdos problem resolution.

Six analysis components built with proper ML methodology:

  1. Feature engineering (YAML-derived, structural, family-derived)
  2. Classification: will this problem be solved? (logistic, RF, GBT)
  3. Regression: when will it be solved? (linear, RF regression)
  4. Clustering: problem archetypes (k-means, silhouette selection)
  5. Anomaly detection: undervalued problems (isolation forest + density)
  6. Transfer learning potential (tag-family transfer coefficients)

Requires: scikit-learn, numpy, scipy, pyyaml.
"""

import math
import re
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import yaml
from scipy import stats as scipy_stats
from sklearn.cluster import KMeans
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    IsolationForest,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    roc_auc_score,
    silhouette_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

# ── Paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"

# Suppress convergence warnings for small-data logistic regression
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")


# =====================================================================
# Data loading and helpers
# =====================================================================

def load_problems() -> List[Dict]:
    """Load the Erdos problems YAML dataset."""
    with open(DATA_PATH) as f:
        return yaml.safe_load(f)


def _status(p: Dict) -> str:
    return p.get("status", {}).get("state", "unknown")


def _tags(p: Dict) -> Set[str]:
    return set(p.get("tags", []))


def _number(p: Dict) -> int:
    n = p.get("number", 0)
    return int(n) if isinstance(n, (int, str)) and str(n).isdigit() else 0


def _oeis(p: Dict) -> List[str]:
    raw = p.get("oeis", [])
    if isinstance(raw, list):
        return [s for s in raw if s not in ("N/A", "possible", "n/a", "none", "")]
    return []


def _prize(p: Dict) -> float:
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
    return _status(p) in (
        "proved", "disproved", "solved",
        "proved (Lean)", "disproved (Lean)", "solved (Lean)",
    )


def _is_open(p: Dict) -> bool:
    return _status(p) == "open"


def _is_formalized(p: Dict) -> bool:
    return p.get("formalized", {}).get("state", "no") == "yes"


# =====================================================================
# 1. Feature Engineering
# =====================================================================

# Major mathematical areas for cross-domain detection
MAJOR_AREAS = {
    "number theory", "graph theory", "ramsey theory", "geometry",
    "additive combinatorics", "analysis", "combinatorics", "set theory",
}


def _tag_entropy(tag_counts: Counter, tags: Set[str]) -> float:
    """Shannon entropy of this problem's tags in the global distribution."""
    total = sum(tag_counts.values())
    if total == 0 or not tags:
        return 0.0
    probs = [tag_counts[t] / total for t in tags if t in tag_counts]
    if not probs:
        return 0.0
    return float(-sum(p * math.log2(p) for p in probs if p > 0))


def _tag_solve_rates(problems: List[Dict]) -> Dict[str, float]:
    """Compute per-tag solve rate across the corpus."""
    tag_total = Counter()
    tag_solved = Counter()
    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _is_solved(p):
                tag_solved[t] += 1
    return {t: tag_solved[t] / tag_total[t] for t in tag_total if tag_total[t] > 0}


def compute_family_features(problems: List[Dict]) -> Dict[int, Dict[str, float]]:
    """
    Compute per-problem family-derived features using problem_families module.

    Returns {problem_number: {family_solve_rate, family_momentum, family_cv}}.
    Falls back to tag-signature families if problem_families is unavailable.
    """
    try:
        from problem_families import (
            build_affinity_graph,
            detect_families,
            family_momentum as compute_momentum,
        )
        graph = build_affinity_graph(problems)
        families = detect_families(problems, graph)
        momentum_data = compute_momentum(problems, families)
    except ImportError:
        families = _fallback_tag_families(problems)
        momentum_data = _fallback_momentum(problems, families)

    # Map each problem number -> its family record
    num_to_family = {}
    for i, fam in enumerate(families):
        for num in fam["members"]:
            num_to_family[num] = i

    # For momentum, index by patriarch
    patriarch_momentum = {}
    for m in momentum_data:
        patriarch_momentum[m.get("family_patriarch", -1)] = m.get("momentum", 0.0)

    result = {}
    for p in problems:
        num = _number(p)
        fam_idx = num_to_family.get(num)
        if fam_idx is not None and fam_idx < len(families):
            fam = families[fam_idx]
            solve_rate = fam["solve_rate"]
            patriarch = fam["patriarch"]
            momentum = patriarch_momentum.get(patriarch, 0.0)
            # coefficient of variation of problem numbers in family
            members = fam["members"]
            if len(members) > 1:
                arr = np.array(members, dtype=float)
                cv = float(np.std(arr) / np.mean(arr)) if np.mean(arr) > 0 else 0.0
            else:
                cv = 0.0
            result[num] = {
                "family_solve_rate": solve_rate,
                "family_momentum": momentum,
                "family_cv": cv,
                "family_size": fam["size"],
            }
        else:
            result[num] = {
                "family_solve_rate": 0.0,
                "family_momentum": 0.0,
                "family_cv": 0.0,
                "family_size": 1,
            }
    return result


def _fallback_tag_families(problems: List[Dict]) -> List[Dict]:
    """Minimal family detection without problem_families module."""
    tag_groups = defaultdict(list)
    prob_by_num = {}
    for p in problems:
        num = _number(p)
        prob_by_num[num] = p
        sig = tuple(sorted(_tags(p)))
        if sig:
            tag_groups[sig].append(num)

    families = []
    for sig, members in tag_groups.items():
        if len(members) >= 3:
            solved = sum(1 for n in members if n in prob_by_num and _is_solved(prob_by_num[n]))
            families.append({
                "members": sorted(members),
                "size": len(members),
                "solve_rate": solved / len(members),
                "patriarch": members[0],
            })
    families.sort(key=lambda f: -f["size"])
    return families


def _fallback_momentum(problems: List[Dict], families: List[Dict]) -> List[Dict]:
    """Minimal momentum computation without problem_families module."""
    prob_by_num = {_number(p): p for p in problems}
    results = []
    for fam in families:
        members = fam["members"]
        if len(members) < 4:
            results.append({"family_patriarch": fam["patriarch"], "momentum": 0.0})
            continue
        mid = len(members) // 2
        early = members[:mid]
        late = members[mid:]
        er = sum(1 for n in early if n in prob_by_num and _is_solved(prob_by_num[n])) / len(early)
        lr = sum(1 for n in late if n in prob_by_num and _is_solved(prob_by_num[n])) / len(late)
        results.append({"family_patriarch": fam["patriarch"], "momentum": lr - er})
    return results


def build_feature_matrix(
    problems: List[Dict],
    family_features: Optional[Dict[int, Dict[str, float]]] = None,
) -> Tuple[np.ndarray, np.ndarray, List[Dict], List[str]]:
    """
    Construct the feature matrix for all classifiable problems.

    Only includes problems with status in {open, proved, disproved, solved,
    proved (Lean), disproved (Lean), solved (Lean)}.

    Returns:
        X: (n_problems, n_features) feature matrix
        y: (n_problems,) binary labels: 1=solved, 0=open
        info: per-problem metadata dicts
        feature_names: ordered list of feature name strings
    """
    tag_rates = _tag_solve_rates(problems)
    tag_counts = Counter()
    for p in problems:
        for t in _tags(p):
            tag_counts[t] += 1

    # Collect all tags by frequency for one-hot encoding
    all_tags_sorted = [t for t, _ in tag_counts.most_common()]

    # Precompute solved-problem feature vectors for Jaccard isolation
    solved_tag_vecs = []
    for p in problems:
        if _is_solved(p):
            vec = tuple(1 if t in _tags(p) else 0 for t in all_tags_sorted)
            solved_tag_vecs.append(vec)

    if family_features is None:
        family_features = compute_family_features(problems)

    # Valid statuses for classification
    valid_statuses = {
        "open", "proved", "disproved", "solved",
        "proved (Lean)", "disproved (Lean)", "solved (Lean)",
    }

    # Build feature names
    feature_names = [
        # YAML-derived
        "problem_number",           # age proxy
        "n_tags",
        "n_oeis",
        "has_prize",
        "prize_log",
        "formalized",
        # Tag solvability
        "avg_tag_solve_rate",
        "max_tag_solve_rate",
        "min_tag_solve_rate",
        # Derived
        "tag_diversity",            # entropy of tag distribution
        "cross_domain",             # has tags from 2+ major areas
        "isolation",                # Jaccard distance to nearest solved problem
        # Family-derived
        "family_solve_rate",
        "family_momentum",
        "family_cv",
        "family_size_log",
    ] + [f"tag_{t.replace(' ', '_')}" for t in all_tags_sorted]

    X_rows = []
    y_vec = []
    info_list = []

    for p in problems:
        status = _status(p)
        if status not in valid_statuses:
            continue

        num = _number(p)
        tags = _tags(p)
        oeis = _oeis(p)
        prize = _prize(p)

        # Tag solvability
        rates = [tag_rates.get(t, 0.0) for t in tags] if tags else [0.0]
        avg_rate = float(np.mean(rates))
        max_rate = float(max(rates))
        min_rate = float(min(rates))

        # Tag diversity (entropy)
        tag_div = _tag_entropy(tag_counts, tags)

        # Cross-domain: has tags from 2+ major areas
        major_count = len(tags & MAJOR_AREAS)
        cross_domain = 1.0 if major_count >= 2 else 0.0

        # Isolation: Jaccard distance to nearest solved problem
        if tags and solved_tag_vecs:
            prob_vec = tuple(1 if t in tags else 0 for t in all_tags_sorted)
            min_dist = 1.0
            for sv in solved_tag_vecs:
                # Jaccard distance = 1 - |intersection| / |union|
                intersection = sum(a and b for a, b in zip(prob_vec, sv))
                union = sum(a or b for a, b in zip(prob_vec, sv))
                if union > 0:
                    dist = 1.0 - intersection / union
                    min_dist = min(min_dist, dist)
            isolation = min_dist
        else:
            isolation = 1.0

        # Family features
        ff = family_features.get(num, {})
        fam_rate = ff.get("family_solve_rate", 0.0)
        fam_mom = ff.get("family_momentum", 0.0)
        fam_cv = ff.get("family_cv", 0.0)
        fam_size = ff.get("family_size", 1)

        # Tag one-hot
        tag_onehot = [1.0 if t in tags else 0.0 for t in all_tags_sorted]

        row = [
            float(num),
            float(len(tags)),
            float(len(oeis)),
            1.0 if prize > 0 else 0.0,
            math.log1p(prize),
            1.0 if _is_formalized(p) else 0.0,
            avg_rate,
            max_rate,
            min_rate,
            tag_div,
            cross_domain,
            isolation,
            fam_rate,
            fam_mom,
            fam_cv,
            math.log1p(fam_size),
        ] + tag_onehot

        X_rows.append(row)
        y_vec.append(1 if _is_solved(p) else 0)
        info_list.append({
            "number": num,
            "tags": sorted(tags),
            "status": status,
            "prize": prize,
            "is_solved": _is_solved(p),
            "is_open": _is_open(p),
        })

    return np.array(X_rows, dtype=np.float64), np.array(y_vec), info_list, feature_names


# =====================================================================
# 2. Classification: Will this problem be solved?
# =====================================================================

def classification_pipeline(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    n_folds: int = 5,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Train logistic regression, random forest, and gradient boosting classifiers.
    Evaluate with stratified k-fold cross-validation.

    Returns per-model: AUC, accuracy, precision@k, feature importances.
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=random_state)

    models = {
        "logistic_regression": LogisticRegression(
            C=1.0, penalty="l2", solver="lbfgs", max_iter=1000,
            random_state=random_state,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_leaf=5,
            random_state=random_state, n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.1,
            min_samples_leaf=5, random_state=random_state,
        ),
    }

    results = {}
    for name, model in models.items():
        # Use scaled features for logistic regression, raw for tree models
        X_use = X_scaled if name == "logistic_regression" else X

        # Cross-validated predictions (out-of-fold)
        y_prob = cross_val_predict(model, X_use, y, cv=cv, method="predict_proba")[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)

        # Metrics
        auc = roc_auc_score(y, y_prob)
        acc = accuracy_score(y, y_pred)
        prec = precision_score(y, y_pred, zero_division=0)
        f1 = f1_score(y, y_pred, zero_division=0)

        # Precision at k (top-k predicted-positive)
        prec_at_k = {}
        for k in [10, 25, 50]:
            if k <= len(y):
                top_k_idx = np.argsort(-y_prob)[:k]
                prec_at_k[k] = float(np.mean(y[top_k_idx]))

        # Fit on full data for feature importance
        model.fit(X_use, y)
        if name == "logistic_regression":
            importances = np.abs(model.coef_[0])
        else:
            importances = model.feature_importances_

        # Rank features
        ranked = sorted(
            zip(feature_names, importances.tolist()),
            key=lambda x: -x[1],
        )

        results[name] = {
            "auc": round(auc, 4),
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "f1": round(f1, 4),
            "precision_at_k": {k: round(v, 4) for k, v in prec_at_k.items()},
            "feature_importances": [(n, round(v, 6)) for n, v in ranked],
            "model": model,
            "scaler": scaler if name == "logistic_regression" else None,
        }

    return results


# =====================================================================
# 3. Regression: When will it be solved?
# =====================================================================

def regression_pipeline(
    X: np.ndarray,
    y: np.ndarray,
    info: List[Dict],
    feature_names: List[str],
    n_folds: int = 5,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    For solved problems, predict the "resolution time" (problem number as age proxy).
    For open problems, predict expected time-to-resolution.

    The target is the problem number (higher = more recent posing).
    We EXCLUDE problem_number from the regression features to avoid trivial
    identity leakage, since it IS the target variable.

    The regression answers: "given this problem's mathematical character
    (tags, OEIS, family, formalization), what problem number would we expect
    it to have?" Open problems that get low predicted numbers are "overdue"
    -- they look like old solved problems but remain open.
    """
    # Exclude problem_number (feature index 0) from regression features
    prob_num_idx = feature_names.index("problem_number") if "problem_number" in feature_names else 0
    reg_feature_mask = np.ones(X.shape[1], dtype=bool)
    reg_feature_mask[prob_num_idx] = False
    X_reg = X[:, reg_feature_mask]
    reg_feature_names = [f for i, f in enumerate(feature_names) if reg_feature_mask[i]]

    # Filter to solved problems only
    solved_mask = np.array([inf["is_solved"] for inf in info])
    open_mask = np.array([inf["is_open"] for inf in info])

    X_solved = X_reg[solved_mask]
    # Target: problem number (age proxy -- higher number = more recent)
    y_target = np.array([inf["number"] for inf in info])[solved_mask]

    if len(X_solved) < 20:
        return {"error": "Too few solved problems for regression",
                "model_results": {}, "open_predictions": []}

    scaler = StandardScaler()
    X_solved_scaled = scaler.fit_transform(X_solved)

    models = {
        "linear_regression": LinearRegression(),
        "random_forest_reg": RandomForestRegressor(
            n_estimators=200, max_depth=10, min_samples_leaf=5,
            random_state=random_state, n_jobs=-1,
        ),
        "gradient_boosting_reg": GradientBoostingRegressor(
            n_estimators=200, max_depth=4, learning_rate=0.1,
            min_samples_leaf=5, random_state=random_state,
        ),
    }

    # Bin the target for stratified CV on a continuous variable
    n_bins = min(n_folds, 5)
    bin_edges = np.percentile(y_target, np.linspace(0, 100, n_bins + 1)[1:-1])
    y_binned = np.digitize(y_target, bin_edges)

    results = {}
    for name, model in models.items():
        X_use = X_solved_scaled if name == "linear_regression" else X_solved

        # Cross-validated predictions
        try:
            cv_splits = list(StratifiedKFold(
                n_splits=n_folds, shuffle=True, random_state=random_state,
            ).split(X_use, y_binned))
            y_pred_cv = cross_val_predict(model, X_use, y_target, cv=cv_splits)
            mae_cv = mean_absolute_error(y_target, y_pred_cv)
            rmse_cv = float(np.sqrt(mean_squared_error(y_target, y_pred_cv)))
            r2_cv = r2_score(y_target, y_pred_cv)
        except Exception:
            mae_cv = None
            rmse_cv = None
            r2_cv = None

        # Fit on full solved data for feature importance + open predictions
        model.fit(X_use, y_target)
        y_pred_full = model.predict(X_use)
        mae_train = mean_absolute_error(y_target, y_pred_full)
        rmse_train = float(np.sqrt(mean_squared_error(y_target, y_pred_full)))
        r2_train = r2_score(y_target, y_pred_full)

        # Feature importance
        if name == "linear_regression":
            importances = np.abs(model.coef_)
        else:
            importances = model.feature_importances_

        ranked = sorted(
            zip(reg_feature_names, importances.tolist()),
            key=lambda x: -x[1],
        )

        results[name] = {
            "mae_train": round(mae_train, 2),
            "rmse_train": round(rmse_train, 2),
            "r2_train": round(r2_train, 4),
            "mae_cv": round(mae_cv, 2) if mae_cv is not None else None,
            "rmse_cv": round(rmse_cv, 2) if rmse_cv is not None else None,
            "r2_cv": round(r2_cv, 4) if r2_cv is not None else None,
            "feature_importances": [(n, round(v, 6)) for n, v in ranked],
            "model": model,
            "scaler": scaler if name == "linear_regression" else None,
        }

    # Select best model by CV MAE (prefer generalization over training fit)
    models_with_cv = {k: v for k, v in results.items() if v.get("mae_cv") is not None}
    if models_with_cv:
        best_name = min(models_with_cv, key=lambda k: models_with_cv[k]["mae_cv"])
    else:
        best_name = min(results, key=lambda k: results[k]["mae_train"])

    best_model = results[best_name]["model"]
    X_open = X_reg[open_mask]

    if best_name == "linear_regression":
        X_open_use = scaler.transform(X_open)
    else:
        X_open_use = X_open

    if len(X_open_use) > 0:
        open_preds = best_model.predict(X_open_use)
    else:
        open_preds = np.array([])

    open_predictions = []
    open_info = [inf for inf, m in zip(info, open_mask) if m]
    for i, inf in enumerate(open_info):
        pred_num = float(open_preds[i]) if i < len(open_preds) else None
        actual_num = inf["number"]
        # "Overdue" score: low predicted number relative to actual = looks like
        # an old solved problem but is still open. Negative residual = overdue.
        overdue = actual_num - pred_num if pred_num is not None else None
        open_predictions.append({
            "number": actual_num,
            "tags": inf["tags"],
            "predicted_resolution_number": round(pred_num, 1) if pred_num is not None else None,
            "overdue_score": round(overdue, 1) if overdue is not None else None,
        })

    # Sort by overdue_score descending (most overdue first)
    open_predictions.sort(key=lambda x: -(x.get("overdue_score") or -1e9))

    return {
        "model_results": results,
        "best_model": best_name,
        "open_predictions": open_predictions,
        "regression_feature_names": reg_feature_names,
    }


# =====================================================================
# 4. Clustering: Problem Archetypes
# =====================================================================

def clustering_pipeline(
    X: np.ndarray,
    y: np.ndarray,
    info: List[Dict],
    feature_names: List[str],
    max_k: int = 15,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    K-means clustering on scaled features. Selects k by silhouette score.

    Returns cluster assignments, per-cluster solve rates, characterization.
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Evaluate k from 2..max_k
    silhouette_scores = {}
    inertias = {}
    for k in range(2, max_k + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=random_state)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels)
        silhouette_scores[k] = round(float(sil), 4)
        inertias[k] = round(float(km.inertia_), 2)

    # Select best k
    best_k = max(silhouette_scores, key=silhouette_scores.get)

    # Fit final model
    km_final = KMeans(n_clusters=best_k, n_init=20, random_state=random_state)
    labels = km_final.fit_predict(X_scaled)

    # Characterize each cluster
    clusters = []
    for c in range(best_k):
        mask = labels == c
        cluster_y = y[mask]
        cluster_info = [inf for inf, m in zip(info, mask) if m]

        # Solve rate
        solve_rate = float(np.mean(cluster_y)) if len(cluster_y) > 0 else 0.0

        # Dominant tags
        tag_counts = Counter()
        for inf in cluster_info:
            for t in inf["tags"]:
                tag_counts[t] += 1
        top_tags = tag_counts.most_common(5)

        # Feature means vs global
        cluster_X = X[mask]
        global_mean = X.mean(axis=0)
        cluster_mean = cluster_X.mean(axis=0)
        diff = cluster_mean - global_mean

        # Find distinguishing features (largest absolute deviation)
        feature_diffs = sorted(
            zip(feature_names, diff.tolist()),
            key=lambda x: -abs(x[1]),
        )

        clusters.append({
            "cluster_id": c,
            "size": int(mask.sum()),
            "solve_rate": round(solve_rate, 4),
            "n_solved": int(cluster_y.sum()),
            "n_open": int((cluster_y == 0).sum()),
            "top_tags": [(t, cnt) for t, cnt in top_tags],
            "distinguishing_features": feature_diffs[:5],
            "members": [inf["number"] for inf in cluster_info],
        })

    # Sort by solve rate for reporting
    clusters_by_rate = sorted(clusters, key=lambda c: -c["solve_rate"])

    return {
        "best_k": best_k,
        "silhouette_scores": silhouette_scores,
        "inertias": inertias,
        "clusters": clusters,
        "clusters_by_solve_rate": clusters_by_rate,
        "highest_solve_cluster": clusters_by_rate[0]["cluster_id"] if clusters_by_rate else None,
        "lowest_solve_cluster": clusters_by_rate[-1]["cluster_id"] if clusters_by_rate else None,
        "labels": labels.tolist(),
    }


# =====================================================================
# 5. Anomaly Detection: Undervalued Problems
# =====================================================================

def anomaly_detection_pipeline(
    X: np.ndarray,
    y: np.ndarray,
    info: List[Dict],
    feature_names: List[str],
    top_n: int = 30,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Train on solved problems, score open problems by proximity to solved distribution.

    Uses two complementary approaches:
      (a) Isolation Forest: anomaly score relative to solved distribution
      (b) K-nearest-neighbor density: how close to solved centroid

    Problems that look like solved problems but are still open are flagged
    as "undervalued" -- most likely to be solved next.
    """
    solved_mask = np.array([inf["is_solved"] for inf in info])
    open_mask = np.array([inf["is_open"] for inf in info])

    X_solved = X[solved_mask]
    X_open = X[open_mask]
    open_info = [inf for inf, m in zip(info, open_mask) if m]

    if len(X_solved) < 10 or len(X_open) < 10:
        return {"error": "Too few solved or open problems"}

    scaler = StandardScaler()
    X_solved_scaled = scaler.fit_transform(X_solved)
    X_open_scaled = scaler.transform(X_open)

    # Method A: Isolation Forest trained on solved problems
    iso = IsolationForest(
        n_estimators=200, contamination=0.1,
        random_state=random_state,
    )
    iso.fit(X_solved_scaled)
    # score_samples: higher = more normal (looks like solved)
    open_iso_scores = iso.score_samples(X_open_scaled)

    # Method B: KNN distance to solved problems
    n_neighbors = min(10, len(X_solved_scaled) - 1)
    knn = NearestNeighbors(n_neighbors=n_neighbors)
    knn.fit(X_solved_scaled)
    distances, _ = knn.kneighbors(X_open_scaled)
    # Average distance to k nearest solved problems (lower = more similar)
    avg_knn_dist = distances.mean(axis=1)

    # Combine: normalize both to [0, 1], then average
    # Isolation forest: higher is more normal -> use directly
    iso_norm = (open_iso_scores - open_iso_scores.min())
    iso_range = open_iso_scores.max() - open_iso_scores.min()
    if iso_range > 0:
        iso_norm = iso_norm / iso_range
    else:
        iso_norm = np.ones_like(iso_norm) * 0.5

    # KNN: lower distance is more similar -> invert
    knn_range = avg_knn_dist.max() - avg_knn_dist.min()
    if knn_range > 0:
        knn_norm = 1.0 - (avg_knn_dist - avg_knn_dist.min()) / knn_range
    else:
        knn_norm = np.ones_like(avg_knn_dist) * 0.5

    # Combined score: weighted average (higher = more like solved)
    combined = 0.5 * iso_norm + 0.5 * knn_norm

    # Build ranked list
    candidates = []
    for i, inf in enumerate(open_info):
        candidates.append({
            "number": inf["number"],
            "tags": inf["tags"],
            "prize": inf["prize"],
            "anomaly_score": round(float(combined[i]), 4),
            "isolation_forest_score": round(float(open_iso_scores[i]), 4),
            "knn_distance": round(float(avg_knn_dist[i]), 4),
        })

    # Sort by combined score descending (most like solved = highest)
    candidates.sort(key=lambda x: -x["anomaly_score"])

    return {
        "top_undervalued": candidates[:top_n],
        "all_scored": candidates,
        "stats": {
            "n_solved_train": int(solved_mask.sum()),
            "n_open_scored": int(open_mask.sum()),
            "iso_score_mean": round(float(open_iso_scores.mean()), 4),
            "iso_score_std": round(float(open_iso_scores.std()), 4),
            "knn_dist_mean": round(float(avg_knn_dist.mean()), 4),
            "knn_dist_std": round(float(avg_knn_dist.std()), 4),
        },
    }


# =====================================================================
# 6. Transfer Learning Potential
# =====================================================================

def transfer_learning_pipeline(
    problems: List[Dict],
) -> Dict[str, Any]:
    """
    For each pair of tag families, compute the transfer coefficient:
    how much does solving problems in family A predict solutions in family B?

    Method: for each tag pair (A, B), compute:
      - P(solved | has tag B and exists solved with tag A)
      - compare to P(solved | has tag B) baseline

    The "transfer coefficient" is the lift ratio.
    """
    # Per-tag solve rates (baseline)
    tag_total = Counter()
    tag_solved = Counter()
    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _is_solved(p):
                tag_solved[t] += 1

    baseline_rate = {t: tag_solved[t] / tag_total[t]
                     for t in tag_total if tag_total[t] >= 5}

    # For each problem, collect which tags' problems are solved
    # "tag A has a solved problem that also has tag B"
    tag_pairs_total = Counter()     # (A, B) -> count of problems with both
    tag_pairs_solved = Counter()    # (A, B) -> count of solved problems with both

    for p in problems:
        tags = _tags(p)
        if len(tags) < 2:
            continue
        for tA in tags:
            for tB in tags:
                if tA != tB:
                    tag_pairs_total[(tA, tB)] += 1
                    if _is_solved(p):
                        tag_pairs_solved[(tA, tB)] += 1

    # Compute transfer coefficients
    # For tag pair (A -> B): among problems that have BOTH tags,
    # the conditional solve rate compared to baseline B rate
    transfers = []
    for (tA, tB), count in tag_pairs_total.items():
        if count < 5:
            continue
        if tB not in baseline_rate:
            continue
        pair_rate = tag_pairs_solved[(tA, tB)] / count
        base = baseline_rate[tB]
        if base > 0:
            lift = pair_rate / base
        else:
            lift = 0.0

        transfers.append({
            "from_tag": tA,
            "to_tag": tB,
            "pair_count": count,
            "pair_solve_rate": round(pair_rate, 4),
            "baseline_rate": round(base, 4),
            "transfer_coefficient": round(lift, 4),
        })

    transfers.sort(key=lambda x: -x["transfer_coefficient"])

    # Build a synergy matrix for major tags
    major_tags = [t for t in sorted(baseline_rate) if tag_total[t] >= 10]
    synergy_matrix = {}
    for tA in major_tags:
        for tB in major_tags:
            if tA == tB:
                continue
            key = (tA, tB)
            count = tag_pairs_total.get(key, 0)
            if count >= 3:
                pair_rate = tag_pairs_solved.get(key, 0) / count
                base = baseline_rate.get(tB, 0.0)
                lift = pair_rate / base if base > 0 else 0.0
                synergy_matrix[(tA, tB)] = round(lift, 4)

    # Find strongest synergies
    strong_synergies = sorted(
        [(k, v) for k, v in synergy_matrix.items() if v > 1.0],
        key=lambda x: -x[1],
    )

    return {
        "all_transfers": transfers,
        "top_transfers": transfers[:30],
        "synergy_matrix": synergy_matrix,
        "strong_synergies": [(f"{a} -> {b}", lift) for (a, b), lift in strong_synergies[:20]],
        "n_tag_pairs": len(transfers),
        "n_strong_synergies": len(strong_synergies),
    }


# =====================================================================
# Full pipeline
# =====================================================================

def run_full_pipeline(
    problems: Optional[List[Dict]] = None,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Run the complete ML analysis pipeline.

    Returns a dict with results from all six components.
    """
    if problems is None:
        problems = load_problems()

    # 1. Feature engineering
    family_features = compute_family_features(problems)
    X, y, info, feature_names = build_feature_matrix(problems, family_features)

    # 2. Classification
    classification_results = classification_pipeline(
        X, y, feature_names, random_state=random_state,
    )

    # 3. Regression
    regression_results = regression_pipeline(
        X, y, info, feature_names, random_state=random_state,
    )

    # 4. Clustering
    clustering_results = clustering_pipeline(
        X, y, info, feature_names, random_state=random_state,
    )

    # 5. Anomaly detection
    anomaly_results = anomaly_detection_pipeline(
        X, y, info, feature_names, random_state=random_state,
    )

    # 6. Transfer learning
    transfer_results = transfer_learning_pipeline(problems)

    # Serialize regression model_results (strip non-serializable model objects)
    reg_serializable = {}
    for k, v in regression_results.items():
        if k == "model_results":
            reg_serializable[k] = {
                name: {rk: rv for rk, rv in res.items() if rk not in ("model", "scaler")}
                for name, res in v.items()
            }
        else:
            reg_serializable[k] = v

    return {
        "feature_matrix": {
            "n_problems": X.shape[0],
            "n_features": X.shape[1],
            "n_solved": int(y.sum()),
            "n_open": int((y == 0).sum()),
            "class_balance": round(float(y.mean()), 4),
            "feature_names": feature_names,
        },
        "classification": {
            name: {k: v for k, v in res.items() if k not in ("model", "scaler")}
            for name, res in classification_results.items()
        },
        "regression": reg_serializable,
        "clustering": clustering_results,
        "anomaly_detection": anomaly_results,
        "transfer_learning": transfer_results,
    }


# =====================================================================
# Main entry point
# =====================================================================

def main():
    print("=" * 70)
    print("ML PROBLEM PREDICTION PIPELINE")
    print("=" * 70)

    problems = load_problems()
    print(f"Loaded {len(problems)} problems")

    print("\n--- Feature Engineering ---")
    family_features = compute_family_features(problems)
    X, y, info, feature_names = build_feature_matrix(problems, family_features)
    print(f"Feature matrix: {X.shape[0]} problems x {X.shape[1]} features")
    print(f"Class balance: {y.mean():.1%} solved, {1-y.mean():.1%} open")

    print("\n--- Classification ---")
    cls_results = classification_pipeline(X, y, feature_names)
    for name, res in cls_results.items():
        print(f"  {name}: AUC={res['auc']:.3f}, acc={res['accuracy']:.3f}, "
              f"prec={res['precision']:.3f}, F1={res['f1']:.3f}")
        top3 = res["feature_importances"][:3]
        print(f"    Top features: {', '.join(f'{n}({v:.4f})' for n, v in top3)}")

    print("\n--- Regression ---")
    reg_results = regression_pipeline(X, y, info, feature_names)
    if "model_results" in reg_results and reg_results["model_results"]:
        for name, res in reg_results["model_results"].items():
            if isinstance(res, dict) and "mae_train" in res:
                cv_str = f", CV-MAE={res['mae_cv']:.1f}" if res.get("mae_cv") else ""
                cv_r2 = f", CV-R2={res['r2_cv']:.3f}" if res.get("r2_cv") else ""
                print(f"  {name}: MAE={res['mae_train']:.1f}, R2={res['r2_train']:.3f}"
                      f"{cv_str}{cv_r2}")
        print(f"  Best model: {reg_results.get('best_model', '?')}")
        if reg_results.get("open_predictions"):
            print(f"  Top 5 most overdue open problems:")
            for p in reg_results["open_predictions"][:5]:
                pred = p.get("predicted_resolution_number")
                overdue = p.get("overdue_score")
                pred_s = f"pred={pred:.0f}" if pred is not None else "N/A"
                overdue_s = f"overdue={overdue:.0f}" if overdue is not None else ""
                print(f"    #{p['number']} ({pred_s}, {overdue_s}): "
                      f"{', '.join(p['tags'][:3])}")

    print("\n--- Clustering ---")
    clust_results = clustering_pipeline(X, y, info, feature_names)
    print(f"  Best k={clust_results['best_k']} "
          f"(silhouette={clust_results['silhouette_scores'][clust_results['best_k']]:.3f})")
    for c in clust_results["clusters_by_solve_rate"]:
        top_t = ", ".join(t for t, _ in c["top_tags"][:3])
        print(f"  Cluster {c['cluster_id']}: n={c['size']}, "
              f"rate={c['solve_rate']:.0%}, tags=[{top_t}]")

    print("\n--- Anomaly Detection ---")
    anom_results = anomaly_detection_pipeline(X, y, info, feature_names)
    if "top_undervalued" in anom_results:
        print(f"  Top 10 undervalued (most like solved but still open):")
        for p in anom_results["top_undervalued"][:10]:
            print(f"    #{p['number']} (score={p['anomaly_score']:.3f}): "
                  f"{', '.join(p['tags'][:3])}")

    print("\n--- Transfer Learning ---")
    xfer_results = transfer_learning_pipeline(problems)
    print(f"  {xfer_results['n_tag_pairs']} tag pairs analyzed")
    print(f"  {xfer_results['n_strong_synergies']} pairs with lift > 1.0")
    if xfer_results["strong_synergies"]:
        print(f"  Top synergies:")
        for pair, lift in xfer_results["strong_synergies"][:5]:
            print(f"    {pair}: lift={lift:.2f}")

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
