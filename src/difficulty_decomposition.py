#!/usr/bin/env python3
"""
difficulty_decomposition.py — Factor analysis of what makes Erdős problems hard.

Decomposes the multi-dimensional problem space into independent difficulty
dimensions via PCA. Each principal component represents an orthogonal axis
of variation that contributes to problem difficulty in a distinct way.

Discovers:
  1. Principal Components: independent axes of variation in problem structure
  2. Factor Loadings: which features define each difficulty dimension
  3. Factor Names: human-interpretable labels for each dimension
  4. Difficulty Spectrum: how each problem scores on each dimension
  5. Dimension-Status Correlation: which dimensions predict solvability
  6. Difficulty Outliers: problems extreme on specific dimensions
  7. Difficulty Clusters: grouping by difficulty profile (not just topic)
  8. Tag Difficulty Profiles: how each tag loads on difficulty dimensions

Output: docs/difficulty_decomposition_report.md
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
REPORT_PATH = ROOT / "docs" / "difficulty_decomposition_report.md"


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


def _oeis(p: Dict) -> List[str]:
    return p.get("oeis", [])


def _is_formalized(p: Dict) -> bool:
    return p.get("formalized", {}).get("state", "no") == "yes"


# ═══════════════════════════════════════════════════════════════════
# Extended Feature Extraction
# ═══════════════════════════════════════════════════════════════════

def build_difficulty_features(problems: List[Dict]) -> Tuple[np.ndarray, List[int], List[str]]:
    """
    Build an enriched feature matrix optimized for difficulty analysis.

    Goes beyond the 72-dim DNA vectors by adding:
    - Tag solve rates (continuous, not just one-hot)
    - OEIS bridge counts (how many solved problems share sequences)
    - Problem number quartile (proxy for chronological age)
    - Prize amount (log-scaled)
    - Cross-tag features (number of tags, tag diversity)
    - Named problem flag

    Returns: (feature_matrix, problem_numbers, feature_names)
    """
    # Pre-compute tag statistics
    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    tag_idx = {t: i for i, t in enumerate(all_tags)}
    n_tags_total = len(all_tags)

    # Tag solve rates
    tag_solved = Counter()
    tag_total = Counter()
    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _is_solved(p):
                tag_solved[t] += 1
    tag_solve_rate = {t: tag_solved[t] / tag_total[t] if tag_total[t] > 0 else 0.5
                      for t in all_tags}

    # OEIS connectivity
    oeis_to_problems = defaultdict(list)
    for p in problems:
        for seq in _oeis(p):
            if seq and seq != "A000000" and not seq.startswith("A00000"):
                oeis_to_problems[seq].append(p)

    # Problem number range for quartile computation
    numbers = sorted(_number(p) for p in problems if _number(p) > 0)
    if numbers:
        q1 = numbers[len(numbers) // 4]
        q2 = numbers[len(numbers) // 2]
        q3 = numbers[3 * len(numbers) // 4]
    else:
        q1, q2, q3 = 250, 500, 750

    # Build feature matrix
    feature_names = (
        [f"tag:{t}" for t in all_tags] +           # tag one-hot
        ["avg_tag_solve_rate"] +                    # average solve rate of problem's tags
        ["min_tag_solve_rate"] +                    # minimum tag solve rate (hardest tag)
        ["max_tag_solve_rate"] +                    # maximum tag solve rate (easiest tag)
        ["tag_count"] +                             # number of tags (complexity proxy)
        ["oeis_count"] +                            # OEIS sequence count
        ["oeis_solved_bridges"] +                   # OEIS connections to solved problems
        ["prize_log"] +                             # log(1 + prize)
        ["formalized"] +                            # binary formalization flag
        ["problem_number_norm"] +                   # normalized problem number [0,1]
        ["number_quartile"] +                       # quartile (1-4) normalized
        ["is_named"] +                              # has a named conjecture
        ["tag_diversity"] +                         # entropy of tag solve rates
        ["isolation_proxy"]                          # 1 / (1 + oeis_connections)
    )
    n_features = len(feature_names)

    X = np.zeros((len(problems), n_features), dtype=float)
    prob_numbers = []
    max_num = max(numbers) if numbers else 1

    for i, p in enumerate(problems):
        num = _number(p)
        prob_numbers.append(num)
        tags = _tags(p)

        # Tag one-hot
        for t in tags:
            if t in tag_idx:
                X[i, tag_idx[t]] = 1.0

        offset = n_tags_total

        # Tag solve rate features
        if tags:
            rates = [tag_solve_rate[t] for t in tags if t in tag_solve_rate]
            if rates:
                X[i, offset] = sum(rates) / len(rates)     # avg
                X[i, offset + 1] = min(rates)              # min
                X[i, offset + 2] = max(rates)              # max
            else:
                X[i, offset] = X[i, offset + 1] = X[i, offset + 2] = 0.5
        else:
            X[i, offset] = X[i, offset + 1] = X[i, offset + 2] = 0.5

        offset += 3

        # Tag count
        X[i, offset] = len(tags) / 5.0  # normalize by approx max
        offset += 1

        # OEIS count
        real_oeis = [s for s in _oeis(p) if s and s != "A000000" and not s.startswith("A00000")]
        X[i, offset] = len(real_oeis) / 9.0  # normalize
        offset += 1

        # OEIS solved bridges
        solved_bridges = 0
        for seq in real_oeis:
            for linked in oeis_to_problems.get(seq, []):
                if _is_solved(linked) and _number(linked) != num:
                    solved_bridges += 1
        X[i, offset] = min(solved_bridges / 10.0, 1.0)
        offset += 1

        # Prize (log)
        prize = _prize(p)
        X[i, offset] = math.log1p(prize) / math.log1p(10000)  # normalize
        offset += 1

        # Formalized
        X[i, offset] = 1.0 if _is_formalized(p) else 0.0
        offset += 1

        # Problem number normalized
        X[i, offset] = num / max_num if max_num > 0 else 0.5
        offset += 1

        # Quartile
        if num <= q1:
            X[i, offset] = 0.25
        elif num <= q2:
            X[i, offset] = 0.50
        elif num <= q3:
            X[i, offset] = 0.75
        else:
            X[i, offset] = 1.00
        offset += 1

        # Named problem
        status_info = p.get("status", {})
        name = status_info.get("name", "")
        X[i, offset] = 1.0 if name and name.strip() else 0.0
        offset += 1

        # Tag diversity (entropy of tag solve rates)
        if tags and len(tags) > 1:
            rates = [tag_solve_rate.get(t, 0.5) for t in tags]
            total = sum(rates) if sum(rates) > 0 else 1.0
            div_entropy = 0.0
            for r in rates:
                p_r = r / total
                if p_r > 0:
                    div_entropy -= p_r * math.log2(p_r)
            X[i, offset] = div_entropy / math.log2(max(len(tags), 2))  # normalize
        else:
            X[i, offset] = 0.0
        offset += 1

        # Isolation proxy
        total_connections = sum(len(oeis_to_problems.get(s, [])) - 1
                                for s in real_oeis)
        X[i, offset] = 1.0 / (1.0 + total_connections)
        offset += 1

    return X, prob_numbers, feature_names


# ═══════════════════════════════════════════════════════════════════
# PCA — Principal Component Analysis
# ═══════════════════════════════════════════════════════════════════

def pca_decomposition(problems: List[Dict],
                      n_components: int = 10) -> Dict[str, Any]:
    """
    Perform PCA on the difficulty feature space.

    Returns dict with:
    - components: principal component vectors (n_components × n_features)
    - explained_variance: fraction of variance each component explains
    - cumulative_variance: cumulative explained variance
    - loadings: feature loadings on each component (named)
    - scores: each problem's projection onto principal components
    - problem_numbers: problem number for each row
    - feature_names: names of all features
    """
    X, numbers, feature_names = build_difficulty_features(problems)

    # Center and scale (standardize)
    means = X.mean(axis=0)
    stds = X.std(axis=0)
    stds[stds == 0] = 1.0  # avoid division by zero for constant features
    X_std = (X - means) / stds

    # Compute covariance matrix and eigendecomposition
    cov = np.dot(X_std.T, X_std) / (X_std.shape[0] - 1)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    # Sort by descending eigenvalue
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Take top n_components
    n_components = min(n_components, len(eigenvalues))
    total_var = eigenvalues.sum()
    explained = eigenvalues[:n_components] / total_var if total_var > 0 else np.zeros(n_components)
    cumulative = np.cumsum(explained)

    components = eigenvectors[:, :n_components].T  # n_components × n_features
    scores = X_std @ eigenvectors[:, :n_components]  # n_problems × n_components

    # Named loadings for each component
    loadings = []
    for c in range(n_components):
        comp_loadings = []
        for j, fname in enumerate(feature_names):
            comp_loadings.append({
                "feature": fname,
                "loading": float(components[c, j]),
                "abs_loading": abs(float(components[c, j])),
            })
        comp_loadings.sort(key=lambda x: x["abs_loading"], reverse=True)
        loadings.append(comp_loadings)

    return {
        "components": components,
        "explained_variance": [float(v) for v in explained],
        "cumulative_variance": [float(v) for v in cumulative],
        "loadings": loadings,
        "scores": scores,
        "problem_numbers": numbers,
        "feature_names": feature_names,
        "n_components": n_components,
    }


# ═══════════════════════════════════════════════════════════════════
# Factor Interpretation — Name the Dimensions
# ═══════════════════════════════════════════════════════════════════

def name_components(pca_result: Dict[str, Any],
                    n_top: int = 5) -> List[Dict[str, Any]]:
    """
    Assign human-interpretable names to principal components based on
    their top loading features.

    Returns list of dicts with:
    - component: index
    - name: human-readable name
    - explained_variance: fraction of variance explained
    - top_positive: features with highest positive loadings
    - top_negative: features with highest negative loadings
    - interpretation: brief description
    """
    results = []
    loadings = pca_result["loadings"]
    explained = pca_result["explained_variance"]

    for c in range(pca_result["n_components"]):
        comp_loadings = loadings[c]

        # Top positive and negative
        positive = [l for l in comp_loadings if l["loading"] > 0.05][:n_top]
        negative = [l for l in comp_loadings if l["loading"] < -0.05]
        negative = sorted(negative, key=lambda x: x["loading"])[:n_top]

        # Auto-name based on top features
        top_feats = [l["feature"] for l in comp_loadings[:3]]
        name = _auto_name(c, top_feats, positive, negative)

        results.append({
            "component": c,
            "name": name,
            "explained_variance": explained[c],
            "top_positive": positive,
            "top_negative": negative,
        })

    return results


def _auto_name(idx: int, top_feats: List[str],
               positive: List, negative: List) -> str:
    """Generate a descriptive name for a component based on its loadings."""
    # Use the TOP 3 features by absolute loading (not just positive/negative)
    all_sorted = sorted(positive + negative, key=lambda x: x["abs_loading"], reverse=True)
    top3 = [l["feature"] for l in all_sorted[:3]]
    top5 = [l["feature"] for l in all_sorted[:5]]

    # Detect feature categories in top features
    def has(pattern, feats=top5):
        return any(pattern in f for f in feats)

    def has_top(pattern, feats=top3):
        return any(pattern in f for f in feats)

    # Priority 1: solve rate dominates
    if has_top("solve_rate"):
        if has("tag_count") or has("diversity"):
            return "Structural Complexity"
        if has("geometry") or has("distances"):
            return "Geometry-Age-Solvability"
        return "Tag Solvability Gradient"

    # Priority 2: structural complexity dominates
    if has_top("tag_count") or has_top("diversity"):
        if has("solve_rate"):
            return "Structural Complexity"
        return "Multi-Tag Complexity"

    # Priority 3: domain opposition (geometry/graph/NT dominate)
    if has_top("geometry") or has_top("distances"):
        if has("graph"):
            return "Geometry vs Graph Theory"
        if has("number_norm") or has("quartile"):
            return "Geometric-Chronological"
        return "Geometric Specialization"

    if has_top("graph") and has("number theory"):
        return "Graph Theory vs Number Theory"

    # Priority 4: chronological
    if has_top("number_norm") or has_top("quartile"):
        if has("analysis") or has("polynomial"):
            return "Late-Era Analytical"
        return "Chronological Position"

    # Priority 5: specific single-feature patterns
    if has_top("formalized"):
        return "Formalization-Difficulty Axis"
    if has_top("prize"):
        return "Prize-Weighted Hardness"
    if has_top("oeis"):
        return "OEIS Connectivity"
    if has_top("isolation"):
        return "Problem Isolation"
    if has_top("named"):
        return "Fame-Difficulty Axis"

    # Fallback: descriptive
    clean = [f.replace("tag:", "").replace("_", " ") for f in top3[:2]]
    return f"PC{idx + 1}: {' / '.join(clean)}"


# ═══════════════════════════════════════════════════════════════════
# Dimension-Status Correlation
# ═══════════════════════════════════════════════════════════════════

def dimension_solvability(problems: List[Dict],
                          pca_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    For each principal component, compute how strongly it correlates with
    problem solvability (binary: solved=1, open=0).

    Returns list of dicts with:
    - component: index
    - correlation: Pearson r with solvability
    - solved_mean: mean score for solved problems
    - open_mean: mean score for open problems
    - separation: |solved_mean - open_mean| / pooled_std
    """
    scores = pca_result["scores"]
    numbers = pca_result["problem_numbers"]

    # Build number → problem lookup
    prob_by_num = {}
    for p in problems:
        prob_by_num[_number(p)] = p

    # Build solvability vector
    y = np.zeros(len(numbers))
    for i, num in enumerate(numbers):
        p = prob_by_num.get(num)
        if p and _is_solved(p):
            y[i] = 1.0

    results = []
    for c in range(pca_result["n_components"]):
        pc_scores = scores[:, c]

        # Pearson correlation
        if np.std(pc_scores) > 0 and np.std(y) > 0:
            r = float(np.corrcoef(pc_scores, y)[0, 1])
        else:
            r = 0.0

        # Group means
        solved_mask = y == 1
        open_mask = y == 0
        solved_mean = float(pc_scores[solved_mask].mean()) if solved_mask.any() else 0.0
        open_mean = float(pc_scores[open_mask].mean()) if open_mask.any() else 0.0

        # Separation (Cohen's d)
        pooled_var = (np.var(pc_scores[solved_mask]) * solved_mask.sum() +
                      np.var(pc_scores[open_mask]) * open_mask.sum())
        n_total = solved_mask.sum() + open_mask.sum()
        pooled_std = math.sqrt(pooled_var / n_total) if n_total > 0 else 1.0
        separation = abs(solved_mean - open_mean) / pooled_std if pooled_std > 0 else 0.0

        results.append({
            "component": c,
            "correlation": r,
            "solved_mean": solved_mean,
            "open_mean": open_mean,
            "separation": separation,
        })

    results.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════
# Difficulty Outliers
# ═══════════════════════════════════════════════════════════════════

def difficulty_outliers(problems: List[Dict],
                        pca_result: Dict[str, Any],
                        n_outliers: int = 10) -> List[Dict[str, Any]]:
    """
    Find problems that are extreme on specific difficulty dimensions.
    These are problems that are "surprisingly hard/easy" along particular axes.

    Returns list of dicts with:
    - number: problem number
    - component: which dimension they're extreme on
    - score: their score on that dimension
    - direction: "high" or "low"
    - status: problem status
    - tags: problem tags
    """
    scores = pca_result["scores"]
    numbers = pca_result["problem_numbers"]

    prob_by_num = {}
    for p in problems:
        prob_by_num[_number(p)] = p

    outliers = []
    n_comps = min(pca_result["n_components"], 5)  # top 5 components

    for c in range(n_comps):
        pc_scores = scores[:, c]
        mean_sc = pc_scores.mean()
        std_sc = pc_scores.std()
        if std_sc == 0:
            continue

        # Z-scores
        z_scores = (pc_scores - mean_sc) / std_sc

        # Top extreme on both sides
        high_idx = np.argsort(z_scores)[-n_outliers:][::-1]
        low_idx = np.argsort(z_scores)[:n_outliers]

        for idx in high_idx:
            num = numbers[idx]
            p = prob_by_num.get(num)
            if p:
                outliers.append({
                    "number": num,
                    "component": c,
                    "score": float(z_scores[idx]),
                    "direction": "high",
                    "status": _status(p),
                    "tags": sorted(_tags(p)),
                })

        for idx in low_idx:
            num = numbers[idx]
            p = prob_by_num.get(num)
            if p:
                outliers.append({
                    "number": num,
                    "component": c,
                    "score": float(z_scores[idx]),
                    "direction": "low",
                    "status": _status(p),
                    "tags": sorted(_tags(p)),
                })

    return outliers


# ═══════════════════════════════════════════════════════════════════
# Difficulty Clusters — Grouping by Difficulty Profile
# ═══════════════════════════════════════════════════════════════════

def difficulty_clusters(problems: List[Dict],
                        pca_result: Dict[str, Any],
                        k: int = 6) -> Dict[str, Any]:
    """
    K-means clustering in PCA space to find groups of problems that share
    a similar difficulty PROFILE (not just similar topics).

    Returns dict with:
    - clusters: list of cluster dicts (members, centroid, stats)
    - silhouette: average silhouette score
    """
    scores = pca_result["scores"][:, :5]  # use top 5 components
    numbers = pca_result["problem_numbers"]

    prob_by_num = {}
    for p in problems:
        prob_by_num[_number(p)] = p

    n = scores.shape[0]
    k = min(k, n)

    # K-means with random seed
    rng = np.random.RandomState(42)
    centroids = scores[rng.choice(n, k, replace=False)]

    for _ in range(50):  # max iterations
        # Assign
        dists = np.zeros((n, k))
        for c in range(k):
            dists[:, c] = np.sum((scores - centroids[c]) ** 2, axis=1)
        labels = np.argmin(dists, axis=1)

        # Update centroids
        new_centroids = np.zeros_like(centroids)
        for c in range(k):
            mask = labels == c
            if mask.any():
                new_centroids[c] = scores[mask].mean(axis=0)
            else:
                new_centroids[c] = centroids[c]

        if np.allclose(centroids, new_centroids, atol=1e-6):
            break
        centroids = new_centroids

    # Build cluster descriptions
    clusters = []
    for c in range(k):
        mask = labels == c
        member_nums = [numbers[i] for i in range(n) if mask[i]]
        if not member_nums:
            continue

        member_problems = [prob_by_num[num] for num in member_nums if num in prob_by_num]
        n_solved = sum(1 for p in member_problems if _is_solved(p))
        n_open = sum(1 for p in member_problems if _is_open(p))
        n_total = len(member_problems)

        # Dominant tags
        tag_counts = Counter()
        for p in member_problems:
            for t in _tags(p):
                tag_counts[t] += 1
        top_tags = tag_counts.most_common(3)

        # Prize stats
        prizes = [_prize(p) for p in member_problems]
        avg_prize = sum(prizes) / len(prizes) if prizes else 0

        clusters.append({
            "cluster": c,
            "size": n_total,
            "solve_rate": n_solved / n_total if n_total > 0 else 0.0,
            "n_solved": n_solved,
            "n_open": n_open,
            "top_tags": [(t, cnt) for t, cnt in top_tags],
            "avg_prize": avg_prize,
            "centroid": [float(v) for v in centroids[c]],
            "member_numbers": sorted(member_nums)[:20],  # sample
        })

    clusters.sort(key=lambda x: x["solve_rate"])

    # Silhouette score (simplified)
    silhouette_vals = []
    for i in range(n):
        own_cluster = labels[i]
        own_dists = np.sqrt(np.sum((scores[labels == own_cluster] - scores[i]) ** 2, axis=1))
        a = own_dists.mean() if len(own_dists) > 1 else 0.0

        min_other = float("inf")
        for c in range(k):
            if c != own_cluster:
                other_mask = labels == c
                if other_mask.any():
                    other_dists = np.sqrt(np.sum((scores[other_mask] - scores[i]) ** 2, axis=1))
                    min_other = min(min_other, other_dists.mean())

        if min_other == float("inf"):
            min_other = 0.0

        s = (min_other - a) / max(a, min_other) if max(a, min_other) > 0 else 0.0
        silhouette_vals.append(s)

    return {
        "clusters": clusters,
        "silhouette": float(np.mean(silhouette_vals)),
        "n_clusters": len(clusters),
    }


# ═══════════════════════════════════════════════════════════════════
# Tag Difficulty Profiles
# ═══════════════════════════════════════════════════════════════════

def tag_difficulty_profiles(problems: List[Dict],
                            pca_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    For each tag, compute its average score on each PCA dimension.
    This reveals HOW tags are difficult, not just WHETHER they are.

    Returns list of dicts with:
    - tag: tag name
    - profile: list of mean scores on each PC dimension
    - dominant_dimension: which PC dimension the tag loads most strongly on
    - solve_rate: tag solve rate for context
    - count: number of problems with this tag
    """
    scores = pca_result["scores"]
    numbers = pca_result["problem_numbers"]
    n_comps = min(pca_result["n_components"], 5)

    # Build number → index lookup
    num_to_idx = {num: i for i, num in enumerate(numbers)}

    # Collect tag statistics
    tag_scores = defaultdict(list)
    tag_solved = Counter()
    tag_total = Counter()

    for p in problems:
        num = _number(p)
        idx = num_to_idx.get(num)
        if idx is None:
            continue
        for t in _tags(p):
            tag_scores[t].append(scores[idx, :n_comps])
            tag_total[t] += 1
            if _is_solved(p):
                tag_solved[t] += 1

    results = []
    for tag, score_list in tag_scores.items():
        if len(score_list) < 3:  # skip rare tags
            continue
        mean_profile = np.mean(score_list, axis=0)
        dominant = int(np.argmax(np.abs(mean_profile)))

        results.append({
            "tag": tag,
            "profile": [float(v) for v in mean_profile],
            "dominant_dimension": dominant,
            "dominant_strength": float(np.abs(mean_profile[dominant])),
            "solve_rate": tag_solved[tag] / tag_total[tag] if tag_total[tag] > 0 else 0.0,
            "count": tag_total[tag],
        })

    results.sort(key=lambda x: x["dominant_strength"], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════
# Difficulty Spectrum — Per-Problem Scores
# ═══════════════════════════════════════════════════════════════════

def difficulty_spectrum(problems: List[Dict],
                        pca_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compute a comprehensive difficulty score for each open problem.

    The score combines:
    - PC dimensions weighted by their solvability correlation
    - Higher score = more structurally difficult

    Returns sorted list (hardest first) with:
    - number, difficulty_score, pc_scores, tags, prize
    """
    scores = pca_result["scores"]
    numbers = pca_result["problem_numbers"]
    n_comps = pca_result["n_components"]

    # Get solvability correlations for weighting
    dim_solv = dimension_solvability(problems, pca_result)
    # Sort by component index for alignment
    dim_solv_by_comp = {d["component"]: d for d in dim_solv}

    # Weight: negative correlation = harder when score is high
    weights = np.zeros(n_comps)
    for c in range(n_comps):
        d = dim_solv_by_comp.get(c, {})
        # Use negative correlation: high score on negatively-correlated PC = hard
        weights[c] = -d.get("correlation", 0.0) * pca_result["explained_variance"][c]

    # Normalize weights
    w_norm = np.abs(weights).sum()
    if w_norm > 0:
        weights = weights / w_norm

    # Compute difficulty for open problems
    prob_by_num = {_number(p): p for p in problems}
    results = []

    for i, num in enumerate(numbers):
        p = prob_by_num.get(num)
        if not p or not _is_open(p):
            continue

        difficulty = float(np.dot(scores[i, :n_comps], weights))

        results.append({
            "number": num,
            "difficulty_score": difficulty,
            "pc_scores": [float(scores[i, c]) for c in range(min(n_comps, 5))],
            "tags": sorted(_tags(p)),
            "prize": _prize(p),
        })

    results.sort(key=lambda x: x["difficulty_score"], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    pca = pca_decomposition(problems)
    named = name_components(pca)
    dim_solv = dimension_solvability(problems, pca)
    outliers = difficulty_outliers(problems, pca)
    clusters_result = difficulty_clusters(problems, pca)
    tag_profiles = tag_difficulty_profiles(problems, pca)
    spectrum = difficulty_spectrum(problems, pca)

    lines = ["# Difficulty Decomposition Analysis", ""]
    lines.append("Decomposing the multi-dimensional Erdős problem space into")
    lines.append("independent difficulty dimensions via PCA.")
    lines.append("")

    # Section 1: Explained Variance
    lines.append("## 1. Principal Components (Variance Explained)")
    lines.append("")
    lines.append("| PC | Name | Variance | Cumulative |")
    lines.append("|-----|------|----------|------------|")
    for comp in named:
        c = comp["component"]
        var = pca["explained_variance"][c]
        cum = pca["cumulative_variance"][c]
        lines.append(f"| PC{c + 1} | {comp['name']} | {var:.1%} | {cum:.1%} |")
    lines.append("")

    # Section 2: Factor Loadings (top 3 components)
    lines.append("## 2. Factor Loadings (Top 3 Components)")
    lines.append("")
    for comp in named[:3]:
        c = comp["component"]
        lines.append(f"### PC{c + 1}: {comp['name']} ({pca['explained_variance'][c]:.1%})")
        lines.append("")
        lines.append("**Positive loadings** (high score = more of this):")
        for l in comp["top_positive"][:5]:
            lines.append(f"- {l['feature']}: {l['loading']:+.3f}")
        lines.append("")
        lines.append("**Negative loadings** (high score = less of this):")
        for l in comp["top_negative"][:5]:
            lines.append(f"- {l['feature']}: {l['loading']:+.3f}")
        lines.append("")

    # Section 3: Solvability Correlation
    lines.append("## 3. Dimension-Solvability Correlation")
    lines.append("")
    lines.append("| PC | Correlation | Solved Mean | Open Mean | Separation |")
    lines.append("|----|-------------|------------|-----------|-----------|")
    for d in dim_solv:
        c = d["component"]
        comp_name = named[c]["name"] if c < len(named) else f"PC{c + 1}"
        lines.append(f"| PC{c + 1} ({comp_name}) | {d['correlation']:+.3f} | "
                      f"{d['solved_mean']:+.2f} | {d['open_mean']:+.2f} | "
                      f"{d['separation']:.3f} |")
    lines.append("")

    # Section 4: Difficulty Clusters
    lines.append("## 4. Difficulty Clusters")
    lines.append("")
    lines.append(f"Silhouette score: {clusters_result['silhouette']:.3f}")
    lines.append("")
    lines.append("| Cluster | Size | Solve Rate | Top Tags | Avg Prize |")
    lines.append("|---------|------|-----------|----------|-----------|")
    for cl in clusters_result["clusters"]:
        tags_str = ", ".join(t for t, _ in cl["top_tags"])
        lines.append(f"| {cl['cluster']} | {cl['size']} | {cl['solve_rate']:.1%} | "
                      f"{tags_str} | ${cl['avg_prize']:.0f} |")
    lines.append("")

    # Section 5: Tag Difficulty Profiles
    lines.append("## 5. Tag Difficulty Profiles")
    lines.append("")
    lines.append("| Tag | Dominant PC | Strength | Solve Rate | Count |")
    lines.append("|-----|-----------|----------|-----------|-------|")
    for tp in tag_profiles[:20]:
        pc_name = named[tp["dominant_dimension"]]["name"] if tp["dominant_dimension"] < len(named) else "?"
        lines.append(f"| {tp['tag']} | PC{tp['dominant_dimension'] + 1} ({pc_name}) | "
                      f"{tp['dominant_strength']:.3f} | {tp['solve_rate']:.1%} | {tp['count']} |")
    lines.append("")

    # Section 6: Hardest Open Problems
    lines.append("## 6. Hardest Open Problems (by Difficulty Score)")
    lines.append("")
    lines.append("| Problem | Score | Tags | Prize |")
    lines.append("|---------|-------|------|-------|")
    for s in spectrum[:15]:
        tags_str = ", ".join(s["tags"][:3])
        prize_str = f"${s['prize']:.0f}" if s["prize"] > 0 else "-"
        lines.append(f"| #{s['number']} | {s['difficulty_score']:.3f} | {tags_str} | {prize_str} |")
    lines.append("")

    # Section 7: Easiest Open Problems (low-hanging fruit)
    lines.append("## 7. Easiest Open Problems (Low-Hanging Fruit)")
    lines.append("")
    lines.append("| Problem | Score | Tags | Prize |")
    lines.append("|---------|-------|------|-------|")
    for s in spectrum[-15:]:
        tags_str = ", ".join(s["tags"][:3])
        prize_str = f"${s['prize']:.0f}" if s["prize"] > 0 else "-"
        lines.append(f"| #{s['number']} | {s['difficulty_score']:.3f} | {tags_str} | {prize_str} |")
    lines.append("")

    # Section 8: Difficulty Outliers
    lines.append("## 8. Difficulty Outliers")
    lines.append("")
    outlier_by_comp = defaultdict(list)
    for o in outliers:
        outlier_by_comp[o["component"]].append(o)
    for c in sorted(outlier_by_comp.keys())[:3]:
        comp_name = named[c]["name"] if c < len(named) else f"PC{c + 1}"
        lines.append(f"### PC{c + 1}: {comp_name}")
        lines.append("")
        high = [o for o in outlier_by_comp[c] if o["direction"] == "high"][:5]
        low = [o for o in outlier_by_comp[c] if o["direction"] == "low"][:5]
        lines.append("**Extreme high:**")
        for o in high:
            tags_str = ", ".join(o["tags"][:3])
            lines.append(f"- #{o['number']} (z={o['score']:.2f}, {o['status']}): {tags_str}")
        lines.append("")
        lines.append("**Extreme low:**")
        for o in low:
            tags_str = ", ".join(o["tags"][:3])
            lines.append(f"- #{o['number']} (z={o['score']:.2f}, {o['status']}): {tags_str}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    problems = load_problems()
    report = generate_report(problems)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")
    print(f"Analyzed {len(problems)} problems")
