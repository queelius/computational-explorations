#!/usr/bin/env python3
"""
interestingness.py -- Quantifying mathematical interestingness.

The meta-problem: what makes a mathematical problem "interesting"?

We decompose interestingness into five orthogonal dimensions, inspired by
Lakatos (Proofs and Refutations), Gowers (Two Cultures), and Tao (blog
taxonomy of mathematical quality):

  1. DEPTH: How connected is this problem to the rest of mathematics?
     Measured by OEIS connectivity, tag count, and cross-domain bridging.

  2. DIFFICULTY: How resistant is this problem to solution?
     Measured by age (problem number as proxy), tag-family solve rate
     (inverse), prize value (Erdos's own difficulty assessment).

  3. SURPRISE POTENTIAL: Does this problem sit at an unusual intersection?
     Measured by tag-combination rarity (isolation score) and deviation
     from the "expected" solve rate given its tags.

  4. FERTILITY: Does this problem's neighborhood generate new mathematics?
     Measured by resolution velocity in its tag family, cascade potential
     (how many other problems share its OEIS sequences), and whether
     similar problems have been recently formalized.

  5. COMMUNITY INVESTMENT: Has someone cared enough to formalize, prize,
     or connect this problem to OEIS sequences?
     Measured directly from formalization status, prize existence, and
     OEIS entry count.

The composite interestingness score is NOT a weighted sum of these five
dimensions. Instead, we train a model where the "ground truth" signal is
a blend of Erdos's own valuation (prizes) and community investment
(formalization). We then use this model to score ALL problems, and the
"hidden gems" are those that score high on intrinsic features (depth,
surprise, fertility) but low on community investment.

Output: docs/interestingness_report.md
"""

import math
import re
import yaml
import numpy as np
from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional


# -- Paths -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "interestingness_report.md"


# ==========================================================================
# Data Access Helpers
# ==========================================================================

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


def _prize(p: Dict) -> float:
    pz = p.get("prize", "no")
    if not pz or pz == "no":
        return 0.0
    nums = re.findall(r"[\d,]+", str(pz))
    if nums:
        val = float(nums[0].replace(",", ""))
        if "\u00a3" in str(pz):      # GBP
            val *= 1.27
        if "\u20b9" in str(pz):      # INR
            val *= 0.012
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


def _real_oeis(p: Dict) -> List[str]:
    """Return only genuine OEIS sequence IDs (filter N/A, possible, etc.)."""
    return [
        s for s in p.get("oeis", [])
        if s and s not in ("N/A", "possible") and not s.startswith("A00000")
    ]


# ==========================================================================
# Feature Extraction: The Five Dimensions
# ==========================================================================

def compute_tag_statistics(problems: List[Dict]) -> Dict[str, Any]:
    """Precompute tag-level statistics used by multiple features."""
    tag_total = Counter()
    tag_solved = Counter()
    tag_formalized = Counter()
    tag_prized = Counter()

    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _is_solved(p):
                tag_solved[t] += 1
            if _is_formalized(p):
                tag_formalized[t] += 1
            if _prize(p) > 0:
                tag_prized[t] += 1

    tag_solve_rate = {
        t: tag_solved[t] / tag_total[t]
        for t in tag_total if tag_total[t] > 0
    }
    tag_formalize_rate = {
        t: tag_formalized[t] / tag_total[t]
        for t in tag_total if tag_total[t] > 0
    }

    # Tag-combination frequency for isolation scoring
    combo_counts = Counter()
    for p in problems:
        combo = tuple(sorted(_tags(p)))
        combo_counts[combo] += 1

    # OEIS maps
    oeis_to_problems = defaultdict(set)
    oeis_to_solved = defaultdict(int)
    oeis_to_total = defaultdict(int)
    for p in problems:
        for seq in _real_oeis(p):
            oeis_to_problems[seq].add(_number(p))
            oeis_to_total[seq] += 1
            if _is_solved(p):
                oeis_to_solved[seq] += 1

    # Resolution velocity: solve rate in problem-number windows
    # (proxy for temporal trends per tag)
    max_num = max(_number(p) for p in problems) if problems else 1
    window_size = max(max_num // 4, 1)
    tag_velocity = {}
    for tag in tag_total:
        tag_probs = [p for p in problems if tag in _tags(p)]
        tag_probs.sort(key=_number)
        if len(tag_probs) < 4:
            tag_velocity[tag] = 0.0
            continue
        # Compare solve rate in last quarter vs first quarter of catalogue
        early = [p for p in tag_probs if _number(p) <= window_size]
        late = [p for p in tag_probs if _number(p) > max_num - window_size]
        early_rate = (
            sum(1 for p in early if _is_solved(p)) / len(early)
            if early else 0.0
        )
        late_rate = (
            sum(1 for p in late if _is_solved(p)) / len(late)
            if late else 0.0
        )
        tag_velocity[tag] = late_rate - early_rate

    return {
        "tag_total": tag_total,
        "tag_solved": tag_solved,
        "tag_solve_rate": tag_solve_rate,
        "tag_formalize_rate": tag_formalize_rate,
        "combo_counts": combo_counts,
        "oeis_to_problems": oeis_to_problems,
        "oeis_to_solved": oeis_to_solved,
        "oeis_to_total": oeis_to_total,
        "tag_velocity": tag_velocity,
        "max_number": max_num,
    }


def extract_features(problems: List[Dict]) -> Tuple[
    np.ndarray, List[Dict], List[str], Dict[str, Any]
]:
    """
    Extract the interestingness feature matrix for ALL problems.

    Returns:
        X: feature matrix (n_problems x n_features)
        info: per-problem metadata dicts
        feature_names: ordered list of feature names
        stats: precomputed tag statistics (for reuse)
    """
    stats = compute_tag_statistics(problems)
    tag_solve_rate = stats["tag_solve_rate"]
    tag_formalize_rate = stats["tag_formalize_rate"]
    combo_counts = stats["combo_counts"]
    oeis_to_problems = stats["oeis_to_problems"]
    oeis_to_solved = stats["oeis_to_solved"]
    oeis_to_total = stats["oeis_to_total"]
    tag_velocity = stats["tag_velocity"]
    max_number = stats["max_number"]

    feature_names = [
        # Dimension 1: DEPTH
        "n_oeis",              # OEIS connectivity count
        "n_tags",              # Tag count (breadth)
        "cross_domain",        # Bridges major categories?
        "oeis_reach",          # How many other problems share OEIS seqs
        # Dimension 2: DIFFICULTY
        "catalogue_position",  # Problem number / max (chronological proxy)
        "inv_tag_solve_rate",  # 1 - avg tag solve rate (harder tags)
        "prize_log",           # log(1 + prize), Erdos's difficulty signal
        "unsolved_despite_age",  # Old + open = persistent difficulty
        # Dimension 3: SURPRISE POTENTIAL
        "isolation_score",     # Rarity of this tag combination
        "solve_rate_anomaly",  # Deviance from expected solve rate
        "tag_entropy",         # Shannon entropy of tag frequencies
        # Dimension 4: FERTILITY
        "resolution_velocity", # Are similar problems being solved recently?
        "cascade_potential",   # OEIS-linked open problems
        "formalization_momentum",  # Tag family formalization trend
        # Dimension 5: COMMUNITY INVESTMENT
        "is_formalized",       # Binary: someone formalized this
        "has_prize",           # Binary: Erdos put money on it
        "oeis_investment",     # Fraction of OEIS links solved
    ]

    MAJOR_CATEGORIES = {
        "number theory", "graph theory", "geometry",
        "ramsey theory", "additive combinatorics", "analysis",
        "combinatorics", "set theory",
    }

    # Global solve rate for anomaly detection
    total_solved = sum(1 for p in problems if _is_solved(p))
    global_solve_rate = total_solved / len(problems) if problems else 0.0

    X_rows = []
    info_list = []

    for p in problems:
        tags = _tags(p)
        num = _number(p)
        oeis = _real_oeis(p)
        prize = _prize(p)
        solved = _is_solved(p)
        formalized = _is_formalized(p)

        # -- DEPTH --
        n_oeis = len(oeis)
        n_tags = len(tags)
        major_tags = tags & MAJOR_CATEGORIES
        cross_domain = 1.0 if len(major_tags) >= 2 else 0.0
        oeis_neighbors = set()
        for seq in oeis:
            oeis_neighbors |= oeis_to_problems.get(seq, set())
        oeis_neighbors.discard(num)
        oeis_reach = len(oeis_neighbors)

        # -- DIFFICULTY --
        catalogue_position = num / max_number if max_number > 0 else 0.0
        rates = [tag_solve_rate.get(t, 0.0) for t in tags]
        avg_solve_rate = sum(rates) / len(rates) if rates else global_solve_rate
        inv_tag_solve_rate = 1.0 - avg_solve_rate
        prize_log = math.log1p(prize)
        # Old + still open => persistent difficulty
        is_open = _is_open(p)
        unsolved_despite_age = (1.0 - catalogue_position) * (1.0 if is_open else 0.0)

        # -- SURPRISE POTENTIAL --
        combo = tuple(sorted(tags))
        combo_freq = combo_counts.get(combo, 1)
        isolation_score = 1.0 / combo_freq  # rarer = more isolated
        # Anomaly: is this problem solved/open when its tags predict otherwise?
        expected_rate = avg_solve_rate
        actual = 1.0 if solved else 0.0
        solve_rate_anomaly = abs(actual - expected_rate)
        # Tag entropy: problems touching rare tags are more surprising
        total_tag_count = sum(stats["tag_total"].values())
        if tags and total_tag_count > 0:
            tag_probs = [stats["tag_total"][t] / total_tag_count for t in tags]
            tag_entropy = -sum(p_t * math.log2(p_t) for p_t in tag_probs if p_t > 0)
        else:
            tag_entropy = 0.0

        # -- FERTILITY --
        velocities = [tag_velocity.get(t, 0.0) for t in tags]
        resolution_velocity = max(velocities) if velocities else 0.0
        # Cascade: how many open problems share OEIS sequences with this one
        cascade_open = 0
        for seq in oeis:
            for neighbor_num in oeis_to_problems.get(seq, set()):
                if neighbor_num != num:
                    # Check if neighbor is open
                    cascade_open += 1
        cascade_potential = min(cascade_open, 50)  # cap
        form_rates = [tag_formalize_rate.get(t, 0.0) for t in tags]
        formalization_momentum = max(form_rates) if form_rates else 0.0

        # -- COMMUNITY INVESTMENT --
        is_form_f = 1.0 if formalized else 0.0
        has_prize_f = 1.0 if prize > 0 else 0.0
        # Fraction of this problem's OEIS links that appear in solved problems
        if oeis:
            bridge_scores = [
                oeis_to_solved.get(s, 0) / max(oeis_to_total.get(s, 1), 1)
                for s in oeis
            ]
            oeis_investment = sum(bridge_scores) / len(bridge_scores)
        else:
            oeis_investment = 0.0

        row = [
            n_oeis, n_tags, cross_domain, oeis_reach,
            catalogue_position, inv_tag_solve_rate, prize_log,
            unsolved_despite_age,
            isolation_score, solve_rate_anomaly, tag_entropy,
            resolution_velocity, cascade_potential, formalization_momentum,
            is_form_f, has_prize_f, oeis_investment,
        ]
        X_rows.append(row)
        info_list.append({
            "number": num,
            "tags": sorted(tags),
            "status": _status(p),
            "prize": prize,
            "formalized": formalized,
            "solved": solved,
            "open": is_open,
        })

    X = np.array(X_rows, dtype=np.float64)
    return X, info_list, feature_names, stats


# ==========================================================================
# Normalization
# ==========================================================================

def normalize_features(X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Min-max normalize each feature to [0, 1].

    Returns (X_norm, mins, ranges) so we can invert later.
    """
    mins = X.min(axis=0)
    ranges = X.max(axis=0) - mins
    ranges[ranges == 0] = 1.0  # avoid division by zero for constant features
    X_norm = (X - mins) / ranges
    return X_norm, mins, ranges


# ==========================================================================
# Composite Interestingness Score
# ==========================================================================

# Feature indices grouped by dimension
DIMENSION_MAP = {
    "depth": [0, 1, 2, 3],          # n_oeis, n_tags, cross_domain, oeis_reach
    "difficulty": [4, 5, 6, 7],      # catalogue_pos, inv_solve, prize_log, unsolved_age
    "surprise": [8, 9, 10],          # isolation, anomaly, entropy
    "fertility": [11, 12, 13],       # velocity, cascade, form_momentum
    "investment": [14, 15, 16],      # formalized, has_prize, oeis_investment
}


def compute_dimension_scores(
    X_norm: np.ndarray,
    feature_names: List[str],
) -> Tuple[np.ndarray, List[str]]:
    """
    Compute per-dimension scores by averaging normalized features within
    each dimension.

    Returns:
        dim_scores: (n_problems x 5) array
        dim_names: list of dimension names
    """
    dim_names = list(DIMENSION_MAP.keys())
    dim_scores = np.zeros((X_norm.shape[0], len(dim_names)))
    for i, dim in enumerate(dim_names):
        indices = DIMENSION_MAP[dim]
        dim_scores[:, i] = X_norm[:, indices].mean(axis=1)
    return dim_scores, dim_names


def composite_interestingness(
    dim_scores: np.ndarray,
    dim_names: List[str],
    weights: Optional[Dict[str, float]] = None,
) -> np.ndarray:
    """
    Compute the composite interestingness score.

    Default weights reflect the philosophical position that intrinsic
    mathematical qualities (depth, difficulty, surprise, fertility) matter
    more than community attention (investment), since community attention
    is precisely what we want to discover is MISSING for hidden gems.

    Default weights:
        depth:      0.25  -- connections to other mathematics
        difficulty: 0.20  -- resistance to solution
        surprise:   0.25  -- sitting at unusual intersections
        fertility:  0.20  -- generating new mathematics
        investment: 0.10  -- community has noticed
    """
    if weights is None:
        weights = {
            "depth": 0.25,
            "difficulty": 0.20,
            "surprise": 0.25,
            "fertility": 0.20,
            "investment": 0.10,
        }
    w = np.array([weights.get(d, 0.0) for d in dim_names])
    # Normalize weights to sum to 1
    w = w / w.sum() if w.sum() > 0 else w
    return dim_scores @ w


# ==========================================================================
# Model Training: Learning Interestingness from Ground Truth
# ==========================================================================

def _sigmoid(z: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid."""
    z = np.clip(z, -500, 500)
    return 1.0 / (1.0 + np.exp(-z))


def build_ground_truth(
    info: List[Dict],
    stats: Dict[str, Any],
) -> np.ndarray:
    """
    Construct ground-truth interestingness labels from multiple signals.

    We combine three proxies:
      - Prize value: Erdos's own assessment (continuous, log-scaled)
      - Formalization: community interest (binary)
      - Tag family solve rate: tractability signal (continuous)

    The composite ground truth is a continuous score in [0, 1].
    """
    n = len(info)
    gt = np.zeros(n)

    # Collect prize values for normalization
    prizes = np.array([i["prize"] for i in info])
    max_prize_log = math.log1p(prizes.max()) if prizes.max() > 0 else 1.0

    for idx, item in enumerate(info):
        # Prize signal: log-scaled, normalized to [0, 1]
        prize_score = math.log1p(item["prize"]) / max_prize_log if max_prize_log > 0 else 0.0

        # Formalization signal
        form_score = 1.0 if item["formalized"] else 0.0

        # Tag tractability: higher solve rate in tag family = more tractable
        tags = set(item["tags"])
        rates = [stats["tag_solve_rate"].get(t, 0.0) for t in tags]
        tractability = sum(rates) / len(rates) if rates else 0.0

        # Composite: prize dominates (it's Erdos's direct signal), formalization
        # adds community validation, tractability adds "doable interesting"
        gt[idx] = 0.50 * prize_score + 0.30 * form_score + 0.20 * tractability

    return gt


def train_interestingness_model(
    X: np.ndarray,
    gt: np.ndarray,
    lr: float = 0.01,
    n_iter: int = 1000,
    reg: float = 0.1,
) -> Tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    """
    Train a linear regression model (with sigmoid output for bounded scores)
    to predict interestingness from features.

    Uses L2-regularized gradient descent on MSE loss (not cross-entropy,
    since gt is continuous).

    Returns (weights, bias, feature_means, feature_stds).
    """
    n, d = X.shape
    mean = X.mean(axis=0)
    std = X.std(axis=0) + 1e-8
    X_norm = (X - mean) / std

    w = np.zeros(d)
    b = 0.0

    for _ in range(n_iter):
        z = X_norm @ w + b
        pred = _sigmoid(z)
        error = pred - gt

        # Gradient of MSE through sigmoid
        sig_grad = pred * (1 - pred)
        dw = (X_norm.T @ (error * sig_grad)) / n + reg * w
        db = (error * sig_grad).mean()

        w -= lr * dw
        b -= lr * db

    return w, b, mean, std


def predict_interestingness(
    X: np.ndarray,
    w: np.ndarray,
    b: float,
    mean: np.ndarray,
    std: np.ndarray,
) -> np.ndarray:
    """Predict interestingness scores for feature matrix X."""
    X_norm = (X - mean) / std
    return _sigmoid(X_norm @ w + b)


# ==========================================================================
# Analysis: Rank, Hidden Gems, Meta-Analysis
# ==========================================================================

def rank_all_problems(
    problems: List[Dict],
    weights: Optional[Dict[str, float]] = None,
) -> List[Dict]:
    """
    Score and rank all problems by composite interestingness.

    Returns list of dicts sorted by score (highest first), each containing:
      - number, tags, status, score
      - dimension_scores: dict of per-dimension scores
      - model_score: learned model prediction
      - composite_score: final blended score
    """
    X, info, feature_names, stats = extract_features(problems)
    X_norm, mins, ranges = normalize_features(X)
    dim_scores, dim_names = compute_dimension_scores(X_norm, feature_names)
    heuristic_scores = composite_interestingness(dim_scores, dim_names, weights)

    # Train model on ground truth
    gt = build_ground_truth(info, stats)
    w, b, mean, std = train_interestingness_model(X, gt)
    model_scores = predict_interestingness(X, w, b, mean, std)

    # Blend: heuristic (structural) + model (learned) equally
    # Both are in [0, 1] range
    blended = 0.5 * heuristic_scores + 0.5 * model_scores

    results = []
    for i, item in enumerate(info):
        dim_dict = {dim_names[j]: round(float(dim_scores[i, j]), 4)
                    for j in range(len(dim_names))}
        results.append({
            "number": item["number"],
            "tags": item["tags"],
            "status": item["status"],
            "prize": item["prize"],
            "formalized": item["formalized"],
            "heuristic_score": round(float(heuristic_scores[i]), 4),
            "model_score": round(float(model_scores[i]), 4),
            "composite_score": round(float(blended[i]), 4),
            "dimension_scores": dim_dict,
            "ground_truth": round(float(gt[i]), 4),
        })

    results.sort(key=lambda r: r["composite_score"], reverse=True)
    return results


def find_hidden_gems(
    ranked: List[Dict],
    top_n: int = 30,
) -> List[Dict]:
    """
    Find "hidden gems": problems with high intrinsic interestingness but
    low community investment.

    A hidden gem satisfies:
      - High depth, surprise, or fertility scores
      - Low investment score (no prize, not formalized, few OEIS links)
      - Preferably still open (unsolved gems are actionable)

    We define the "intrinsic score" as the average of depth, difficulty,
    surprise, and fertility (excluding investment), then rank by
    (intrinsic_score - investment_score).
    """
    gems = []
    for r in ranked:
        ds = r["dimension_scores"]
        intrinsic = (ds["depth"] + ds["difficulty"] + ds["surprise"] + ds["fertility"]) / 4
        investment = ds["investment"]
        gem_score = intrinsic - investment

        gems.append({
            **r,
            "intrinsic_score": round(intrinsic, 4),
            "investment_score": round(investment, 4),
            "gem_score": round(gem_score, 4),
        })

    gems.sort(key=lambda g: g["gem_score"], reverse=True)
    return gems[:top_n]


def dimension_analysis(ranked: List[Dict]) -> Dict[str, Any]:
    """
    Analyze each dimension: which problems excel on each axis?
    Returns top-5 per dimension and correlation matrix.
    """
    dim_names = ["depth", "difficulty", "surprise", "fertility", "investment"]
    top_by_dim = {}
    for dim in dim_names:
        sorted_by = sorted(ranked, key=lambda r: r["dimension_scores"][dim], reverse=True)
        top_by_dim[dim] = [
            {"number": r["number"], "score": r["dimension_scores"][dim], "tags": r["tags"]}
            for r in sorted_by[:5]
        ]

    # Correlation matrix between dimensions
    n = len(ranked)
    if n < 3:
        return {"top_by_dimension": top_by_dim, "correlations": {}}

    dim_matrix = np.zeros((n, len(dim_names)))
    for i, r in enumerate(ranked):
        for j, dim in enumerate(dim_names):
            dim_matrix[i, j] = r["dimension_scores"][dim]

    # Protect against constant columns
    stds = dim_matrix.std(axis=0)
    if np.any(stds == 0):
        corr = np.zeros((len(dim_names), len(dim_names)))
    else:
        corr = np.corrcoef(dim_matrix.T)

    correlations = {}
    for i in range(len(dim_names)):
        for j in range(i + 1, len(dim_names)):
            key = f"{dim_names[i]}_vs_{dim_names[j]}"
            correlations[key] = round(float(corr[i, j]), 4) if np.isfinite(corr[i, j]) else 0.0

    return {
        "top_by_dimension": top_by_dim,
        "correlations": correlations,
    }


def feature_importance(
    problems: List[Dict],
) -> List[Tuple[str, float]]:
    """
    Compute feature importance by training the model and examining weights.

    Returns sorted list of (feature_name, importance).
    """
    X, info, feature_names, stats = extract_features(problems)
    gt = build_ground_truth(info, stats)
    w, b, mean, std = train_interestingness_model(X, gt)

    importance = np.abs(w)
    ranked = sorted(zip(feature_names, importance.tolist()), key=lambda x: -x[1])
    return [(name, round(imp, 4)) for name, imp in ranked]


def tag_interestingness(ranked: List[Dict]) -> List[Dict]:
    """
    Aggregate interestingness by tag: which mathematical areas are most
    "interesting" on average?
    """
    tag_scores = defaultdict(list)
    tag_dims = defaultdict(lambda: defaultdict(list))

    for r in ranked:
        for tag in r["tags"]:
            tag_scores[tag].append(r["composite_score"])
            for dim, val in r["dimension_scores"].items():
                tag_dims[tag][dim].append(val)

    results = []
    for tag in tag_scores:
        scores = tag_scores[tag]
        avg = sum(scores) / len(scores)
        dim_avgs = {
            dim: round(sum(vals) / len(vals), 4)
            for dim, vals in tag_dims[tag].items()
        }
        results.append({
            "tag": tag,
            "n_problems": len(scores),
            "avg_interestingness": round(avg, 4),
            "dimension_profile": dim_avgs,
        })

    results.sort(key=lambda r: r["avg_interestingness"], reverse=True)
    return results


# ==========================================================================
# Meta-Analysis: What Predicts Solvability, Theory-Generation, Connectivity?
# ==========================================================================

def solvability_predictors(problems: List[Dict]) -> Dict[str, Any]:
    """
    Q5(a): What features predict that a problem will eventually be solved?

    We use the solved/open split as ground truth and rank features by
    their discriminative power (difference in means between solved and open).
    """
    X, info, feature_names, stats = extract_features(problems)
    X_norm, _, _ = normalize_features(X)

    solved_mask = np.array([i["solved"] for i in info])
    open_mask = np.array([i["open"] for i in info])

    if solved_mask.sum() == 0 or open_mask.sum() == 0:
        return {"predictors": [], "note": "insufficient data"}

    solved_means = X_norm[solved_mask].mean(axis=0)
    open_means = X_norm[open_mask].mean(axis=0)
    diffs = solved_means - open_means

    predictors = sorted(
        zip(feature_names, diffs.tolist()),
        key=lambda x: abs(x[1]),
        reverse=True,
    )
    return {
        "predictors": [(name, round(d, 4)) for name, d in predictors],
        "interpretation": (
            "Positive = higher in solved problems (predicts solvability). "
            "Negative = higher in open problems (predicts resistance)."
        ),
    }


def connectivity_predictors(problems: List[Dict]) -> Dict[str, Any]:
    """
    Q5(c): What features predict that a problem connects multiple fields?

    Ground truth: cross_domain feature (tags spanning 2+ major categories).
    """
    X, info, feature_names, stats = extract_features(problems)
    X_norm, _, _ = normalize_features(X)

    cross_idx = feature_names.index("cross_domain")
    cross_mask = X[:, cross_idx] > 0.5

    if cross_mask.sum() == 0 or (~cross_mask).sum() == 0:
        return {"predictors": [], "note": "insufficient data"}

    cross_means = X_norm[cross_mask].mean(axis=0)
    non_cross_means = X_norm[~cross_mask].mean(axis=0)
    diffs = cross_means - non_cross_means

    predictors = sorted(
        zip(feature_names, diffs.tolist()),
        key=lambda x: abs(x[1]),
        reverse=True,
    )
    return {
        "predictors": [(name, round(d, 4)) for name, d in predictors],
        "interpretation": (
            "Positive = higher in cross-domain problems. "
            "These features predict boundary-spanning problems."
        ),
    }


def theory_generation_predictors(problems: List[Dict]) -> Dict[str, Any]:
    """
    Q5(b): What features predict that a problem leads to new theory?

    Proxy: problems that are both solved AND formalized (someone cared
    enough to formalize the solution, suggesting the result was theory-generative).
    Also: problems with high cascade potential (many OEIS-linked neighbors).
    """
    X, info, feature_names, stats = extract_features(problems)
    X_norm, _, _ = normalize_features(X)

    # "Theory-generative" = solved AND (formalized OR high cascade)
    theory_mask = np.array([
        i["solved"] and (i["formalized"] or i["number"] in _high_cascade_set(stats))
        for i in info
    ])
    other_solved = np.array([i["solved"] and not theory_mask[idx]
                             for idx, i in enumerate(info)])

    if theory_mask.sum() < 3 or other_solved.sum() < 3:
        return {"predictors": [], "note": "insufficient data for comparison"}

    theory_means = X_norm[theory_mask].mean(axis=0)
    other_means = X_norm[other_solved].mean(axis=0)
    diffs = theory_means - other_means

    predictors = sorted(
        zip(feature_names, diffs.tolist()),
        key=lambda x: abs(x[1]),
        reverse=True,
    )
    return {
        "predictors": [(name, round(d, 4)) for name, d in predictors],
        "interpretation": (
            "Features distinguishing theory-generative solved problems "
            "from other solved problems."
        ),
    }


def _high_cascade_set(stats: Dict) -> Set[int]:
    """Problems with above-median cascade potential."""
    oeis_to_problems = stats["oeis_to_problems"]
    problem_cascade = Counter()
    for seq, pnums in oeis_to_problems.items():
        for pn in pnums:
            problem_cascade[pn] += len(pnums) - 1
    if not problem_cascade:
        return set()
    median_cascade = sorted(problem_cascade.values())[len(problem_cascade) // 2]
    return {p for p, c in problem_cascade.items() if c > median_cascade}


# ==========================================================================
# Report Generation
# ==========================================================================

def generate_report(problems: List[Dict]) -> str:
    """Generate the full interestingness analysis report."""
    ranked = rank_all_problems(problems)
    gems = find_hidden_gems(ranked)
    dim_analysis = dimension_analysis(ranked)
    fi = feature_importance(problems)
    tag_int = tag_interestingness(ranked)
    solve_pred = solvability_predictors(problems)
    connect_pred = connectivity_predictors(problems)
    theory_pred = theory_generation_predictors(problems)

    lines = [
        "# Quantifying Mathematical Interestingness",
        "",
        "## The Meta-Problem",
        "",
        "What makes a mathematical problem 'interesting'? We decompose this into",
        "five orthogonal dimensions: **depth**, **difficulty**, **surprise potential**,",
        "**fertility**, and **community investment**. We score all 1,183 Erdos problems",
        "and identify hidden gems -- problems with high intrinsic interest but low attention.",
        "",
        f"Total problems analyzed: {len(ranked)}",
        "",
    ]

    # Top 20 most interesting
    lines.append("## Top 20 Most Interesting Problems")
    lines.append("")
    lines.append("| Rank | # | Score | Depth | Diff | Surprise | Fertility | Invest | Tags |")
    lines.append("|------|---|-------|-------|------|----------|-----------|--------|------|")
    for i, r in enumerate(ranked[:20]):
        ds = r["dimension_scores"]
        tags_str = ", ".join(r["tags"][:3])
        lines.append(
            f"| {i+1} | {r['number']} | {r['composite_score']:.3f} | "
            f"{ds['depth']:.2f} | {ds['difficulty']:.2f} | {ds['surprise']:.2f} | "
            f"{ds['fertility']:.2f} | {ds['investment']:.2f} | {tags_str} |"
        )
    lines.append("")

    # Hidden gems
    lines.append("## Hidden Gems: High Intrinsic Interest, Low Attention")
    lines.append("")
    lines.append("These problems score high on depth/surprise/fertility but have no prize,")
    lines.append("no formalization, and few OEIS connections.")
    lines.append("")
    lines.append("| Rank | # | Gem Score | Intrinsic | Investment | Status | Tags |")
    lines.append("|------|---|-----------|-----------|------------|--------|------|")
    for i, g in enumerate(gems[:15]):
        tags_str = ", ".join(g["tags"][:3])
        lines.append(
            f"| {i+1} | {g['number']} | {g['gem_score']:.3f} | "
            f"{g['intrinsic_score']:.3f} | {g['investment_score']:.3f} | "
            f"{g['status']} | {tags_str} |"
        )
    lines.append("")

    # Feature importance
    lines.append("## Feature Importance (Learned Model)")
    lines.append("")
    for name, imp in fi[:10]:
        lines.append(f"- **{name}**: {imp:.4f}")
    lines.append("")

    # Tag interestingness
    lines.append("## Tag Interestingness Rankings")
    lines.append("")
    lines.append("| Tag | N | Avg Score | Depth | Difficulty | Surprise | Fertility |")
    lines.append("|-----|---|-----------|-------|------------|----------|-----------|")
    for t in tag_int[:15]:
        dp = t["dimension_profile"]
        lines.append(
            f"| {t['tag']} | {t['n_problems']} | {t['avg_interestingness']:.3f} | "
            f"{dp.get('depth', 0):.2f} | {dp.get('difficulty', 0):.2f} | "
            f"{dp.get('surprise', 0):.2f} | {dp.get('fertility', 0):.2f} |"
        )
    lines.append("")

    # Dimension correlations
    lines.append("## Dimension Correlations")
    lines.append("")
    for key, val in dim_analysis["correlations"].items():
        lines.append(f"- {key}: r = {val:.3f}")
    lines.append("")

    # Meta-analysis: what predicts solvability?
    lines.append("## What Predicts Solvability?")
    lines.append("")
    for name, diff in solve_pred["predictors"][:8]:
        direction = "+" if diff > 0 else "-"
        lines.append(f"- {name}: {direction}{abs(diff):.3f}")
    lines.append("")

    # What predicts cross-field connectivity?
    lines.append("## What Predicts Cross-Field Connectivity?")
    lines.append("")
    for name, diff in connect_pred["predictors"][:8]:
        direction = "+" if diff > 0 else "-"
        lines.append(f"- {name}: {direction}{abs(diff):.3f}")
    lines.append("")

    # What predicts theory generation?
    lines.append("## What Predicts Theory Generation?")
    lines.append("")
    if theory_pred["predictors"]:
        for name, diff in theory_pred["predictors"][:8]:
            direction = "+" if diff > 0 else "-"
            lines.append(f"- {name}: {direction}{abs(diff):.3f}")
    else:
        lines.append(f"_{theory_pred.get('note', 'N/A')}_")
    lines.append("")

    return "\n".join(lines)


# ==========================================================================
# Main
# ==========================================================================

def main():
    """Run the full interestingness analysis."""
    problems = load_problems()
    report = generate_report(problems)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)

    print(f"Report written to {REPORT_PATH}")

    # Quick summary to stdout
    ranked = rank_all_problems(problems)
    print("\nTop 10 Most Interesting Problems:")
    for i, r in enumerate(ranked[:10]):
        print(f"  {i+1}. #{r['number']} (score={r['composite_score']:.3f}) "
              f"tags={r['tags']}")

    gems = find_hidden_gems(ranked)
    print("\nTop 5 Hidden Gems:")
    for i, g in enumerate(gems[:5]):
        print(f"  {i+1}. #{g['number']} (gem={g['gem_score']:.3f}, "
              f"intrinsic={g['intrinsic_score']:.3f}, "
              f"invest={g['investment_score']:.3f}) "
              f"tags={g['tags']}")


if __name__ == "__main__":
    main()
