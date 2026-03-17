#!/usr/bin/env python3
"""
pattern_synthesis.py — Meta-pattern discovery across all analysis dimensions.

While individual modules each discover patterns from one analytical lens,
this module discovers patterns ABOUT those patterns — the meta-structure:

  1. Problem Archetypes: K-means clustering on the multi-dimensional signal
     space to find recurring "types" of problems
  2. Analytical Blindspots: Where ALL modules agree a problem is uninteresting,
     yet it has properties (prize, OEIS bridges) suggesting importance
  3. Signal Redundancy: Which module pairs capture the same information?
     (beyond the pairwise correlations — looks at conditional independence)
  4. Tag Archetype Mapping: Which tags map to which archetypes?
  5. Solve Prediction: Given the multi-dimensional embedding, which open
     problems look most like already-solved ones?
  6. Prize Efficiency: Which problem archetypes have best prize-per-difficulty?

Output: docs/pattern_synthesis_report.md
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
REPORT_PATH = ROOT / "docs" / "pattern_synthesis_report.md"


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
# Build Multi-Dimensional Signal Space
# ═══════════════════════════════════════════════════════════════════

def build_signal_space(problems: List[Dict]) -> Dict[str, Any]:
    """
    Build a multi-dimensional feature vector for each problem from
    independent analytical signals.

    Dimensions:
    - tag_solve_rate: average solve rate of problem's tags
    - oeis_richness: number of OEIS references (normalized)
    - tag_diversity: number of tags (normalized)
    - problem_age: problem number as proxy for age (normalized)
    - prize_signal: log-normalized prize value
    - formalized: 1.0 if formalized, 0.0 otherwise
    - is_solved: 1.0 if solved, 0.0 otherwise
    - tag_popularity: average tag frequency
    - oeis_exclusivity: fraction of OEIS sequences shared by ≤3 problems

    Returns dict with:
    - features: np.array shape (n_problems, n_dims)
    - dim_names: list of dimension names
    - numbers: list of problem numbers (same order as rows)
    - prob_by_num: lookup dict
    """
    prob_by_num = {_number(p): p for p in problems}

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

    max_oeis = max((len(_oeis(p)) for p in problems), default=1)
    max_tags = max((len(_tags(p)) for p in problems), default=1)
    max_num = max((_number(p) for p in problems), default=1)

    dim_names = [
        "tag_solve_rate", "oeis_richness", "tag_diversity",
        "problem_age", "prize_signal", "formalized",
        "is_solved", "tag_popularity", "oeis_exclusivity",
    ]

    features = []
    numbers = []

    for p in problems:
        num = _number(p)
        tags = _tags(p)
        oeis = _oeis(p) - {"N/A", "possible", "n/a", "none", ""}

        # Tag solve rate
        rates = [tag_rate.get(t, 0.3) for t in tags] if tags else [0.3]
        avg_rate = sum(rates) / len(rates)

        # OEIS richness
        oeis_r = len(oeis) / max_oeis if max_oeis > 0 else 0

        # Tag diversity
        tag_div = len(tags) / max_tags if max_tags > 0 else 0

        # Problem age (lower number = older)
        age = 1.0 - (_number(p) / max_num) if max_num > 0 else 0.5

        # Prize signal
        prize = _prize(p)
        prize_sig = min(math.log1p(prize) / math.log1p(10000), 1.0) if prize > 0 else 0.0

        # Formalized
        form_field = p.get("formalized", {})
        form = 1.0 if isinstance(form_field, dict) and form_field.get("state") == "yes" else 0.0

        # Solved
        solved = 1.0 if _is_solved(p) else 0.0

        # Tag popularity
        pops = [tag_total.get(t, 1) for t in tags] if tags else [1]
        tag_pop = sum(pops) / len(pops) / max(tag_total.values()) if tag_total else 0

        # OEIS exclusivity
        if oeis:
            exclusive = sum(1 for s in oeis if oeis_freq.get(s, 0) <= 3) / len(oeis)
        else:
            exclusive = 0.0

        features.append([avg_rate, oeis_r, tag_div, age, prize_sig,
                         form, solved, tag_pop, exclusive])
        numbers.append(num)

    return {
        "features": np.array(features),
        "dim_names": dim_names,
        "numbers": numbers,
        "prob_by_num": prob_by_num,
    }


# ═══════════════════════════════════════════════════════════════════
# Problem Archetypes — K-Means Clustering
# ═══════════════════════════════════════════════════════════════════

def discover_archetypes(problems: List[Dict],
                        signal_space: Optional[Dict] = None,
                        n_clusters: int = 8) -> List[Dict[str, Any]]:
    """
    Cluster problems into archetypes using k-means on the signal space.

    Returns list of archetypes sorted by size, each with:
    - archetype_id, size, centroid (named dimensions)
    - solve_rate, open_count, prize_total
    - top_tags: most common tags in the cluster
    - representative: problem closest to centroid
    """
    if signal_space is None:
        signal_space = build_signal_space(problems)

    features = signal_space["features"]
    dim_names = signal_space["dim_names"]
    numbers = signal_space["numbers"]
    prob_by_num = signal_space["prob_by_num"]
    n = len(numbers)

    # Standardize features
    means = features.mean(axis=0)
    stds = features.std(axis=0)
    stds[stds == 0] = 1.0
    X = (features - means) / stds

    # Simple k-means (no sklearn dependency)
    rng = np.random.RandomState(42)
    # K-means++ initialization
    centroids = [X[rng.randint(n)]]
    for _ in range(n_clusters - 1):
        dists = np.array([min(np.sum((x - c) ** 2) for c in centroids) for x in X])
        probs = dists / dists.sum()
        idx = rng.choice(n, p=probs)
        centroids.append(X[idx])
    centroids = np.array(centroids)

    # Iterate
    for _ in range(50):
        # Assign
        dists = np.array([[np.sum((x - c) ** 2) for c in centroids] for x in X])
        labels = dists.argmin(axis=1)

        # Update centroids
        new_centroids = np.zeros_like(centroids)
        for k in range(n_clusters):
            mask = labels == k
            if mask.sum() > 0:
                new_centroids[k] = X[mask].mean(axis=0)
            else:
                new_centroids[k] = centroids[k]

        if np.allclose(centroids, new_centroids, atol=1e-6):
            break
        centroids = new_centroids

    # Build archetype records
    archetypes = []
    for k in range(n_clusters):
        mask = labels == k
        member_indices = np.where(mask)[0]
        member_nums = [numbers[i] for i in member_indices]

        if not member_nums:
            continue

        # Centroid in original space
        centroid_orig = centroids[k] * stds + means
        centroid_dict = {dim_names[i]: float(centroid_orig[i]) for i in range(len(dim_names))}

        # Stats
        solved = sum(1 for num in member_nums if _is_solved(prob_by_num.get(num, {})))
        open_count = sum(1 for num in member_nums if _is_open(prob_by_num.get(num, {})))
        total_prize = sum(_prize(prob_by_num.get(num, {})) for num in member_nums)

        # Top tags
        tag_counter = Counter()
        for num in member_nums:
            p = prob_by_num.get(num)
            if p:
                for t in _tags(p):
                    tag_counter[t] += 1
        top_tags = [t for t, _ in tag_counter.most_common(5)]

        # Representative: closest to centroid
        dists_to_centroid = [np.sum((X[i] - centroids[k]) ** 2) for i in member_indices]
        rep_idx = member_indices[np.argmin(dists_to_centroid)]

        archetypes.append({
            "archetype_id": k,
            "size": len(member_nums),
            "centroid": centroid_dict,
            "solve_rate": solved / len(member_nums) if member_nums else 0,
            "open_count": open_count,
            "prize_total": total_prize,
            "top_tags": top_tags,
            "representative": numbers[rep_idx],
            "members": sorted(member_nums),
        })

    archetypes.sort(key=lambda a: -a["size"])
    return archetypes


# ═══════════════════════════════════════════════════════════════════
# Analytical Blindspots — Overlooked Important Problems
# ═══════════════════════════════════════════════════════════════════

def find_blindspots(problems: List[Dict],
                    signal_space: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Find problems that are potentially undervalued: they have "importance"
    indicators (prize, many OEIS refs, central tags) but score low on
    most analytical dimensions.

    These are problems that our analytical framework systematically misses.
    """
    if signal_space is None:
        signal_space = build_signal_space(problems)

    features = signal_space["features"]
    dim_names = signal_space["dim_names"]
    numbers = signal_space["numbers"]
    prob_by_num = signal_space["prob_by_num"]

    # Importance = prize + oeis_richness + tag_popularity
    prize_idx = dim_names.index("prize_signal")
    oeis_idx = dim_names.index("oeis_richness")
    pop_idx = dim_names.index("tag_popularity")

    # Tractability = tag_solve_rate + tag_diversity
    rate_idx = dim_names.index("tag_solve_rate")
    div_idx = dim_names.index("tag_diversity")

    results = []
    for i in range(len(numbers)):
        num = numbers[i]
        p = prob_by_num.get(num)
        if not p or not _is_open(p):
            continue

        importance = (features[i, prize_idx] +
                      features[i, oeis_idx] +
                      features[i, pop_idx]) / 3.0

        tractability = (features[i, rate_idx] + features[i, div_idx]) / 2.0

        # Blindspot: importance exceeds tractability by significant margin
        if importance > 0.15 and importance - tractability > 0.1:
            results.append({
                "number": num,
                "importance": float(importance),
                "tractability": float(tractability),
                "gap": float(importance - tractability),
                "tags": sorted(_tags(p)),
                "prize": _prize(p),
                "oeis_count": len(_oeis(p)),
            })

    results.sort(key=lambda r: -r["gap"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Solve-Similarity — Open Problems Most Like Solved Ones
# ═══════════════════════════════════════════════════════════════════

def solve_similarity(problems: List[Dict],
                     signal_space: Optional[Dict] = None,
                     top_k: int = 30) -> List[Dict[str, Any]]:
    """
    For each open problem, find its distance to the nearest solved problem
    in signal space. Open problems close to solved ones may be more tractable.

    Returns top_k open problems closest to solved problems, with:
    - number, distance, nearest_solved, shared_tags
    """
    if signal_space is None:
        signal_space = build_signal_space(problems)

    features = signal_space["features"]
    numbers = signal_space["numbers"]
    prob_by_num = signal_space["prob_by_num"]

    # Standardize
    means = features.mean(axis=0)
    stds = features.std(axis=0)
    stds[stds == 0] = 1.0
    X = (features - means) / stds

    # Separate solved and open indices
    solved_indices = [i for i in range(len(numbers))
                      if _is_solved(prob_by_num.get(numbers[i], {}))]
    open_indices = [i for i in range(len(numbers))
                    if _is_open(prob_by_num.get(numbers[i], {}))]

    if not solved_indices or not open_indices:
        return []

    X_solved = X[solved_indices]

    results = []
    for oi in open_indices:
        # Distance to all solved problems
        dists = np.sqrt(np.sum((X_solved - X[oi]) ** 2, axis=1))
        nearest_idx = np.argmin(dists)
        nearest_dist = float(dists[nearest_idx])
        nearest_num = numbers[solved_indices[nearest_idx]]

        open_tags = _tags(prob_by_num.get(numbers[oi], {}))
        solved_tags = _tags(prob_by_num.get(nearest_num, {}))
        shared = open_tags & solved_tags

        results.append({
            "number": numbers[oi],
            "distance": nearest_dist,
            "nearest_solved": nearest_num,
            "shared_tags": sorted(shared),
            "n_shared_tags": len(shared),
            "tags": sorted(open_tags),
            "prize": _prize(prob_by_num.get(numbers[oi], {})),
        })

    results.sort(key=lambda r: r["distance"])
    return results[:top_k]


# ═══════════════════════════════════════════════════════════════════
# Tag-Archetype Mapping
# ═══════════════════════════════════════════════════════════════════

def tag_archetype_map(problems: List[Dict],
                      archetypes: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
    """
    For each tag, determine which archetype(s) it belongs to most strongly.

    Returns list of {tag, primary_archetype, distribution, total_count}.
    """
    if archetypes is None:
        archetypes = discover_archetypes(problems)

    prob_by_num = {_number(p): p for p in problems}

    # Map problem numbers to archetype indices
    num_to_arch = {}
    for arch in archetypes:
        for num in arch["members"]:
            num_to_arch[num] = arch["archetype_id"]

    # Count tag occurrences per archetype
    tag_arch_count = defaultdict(Counter)
    tag_total = Counter()
    for p in problems:
        num = _number(p)
        arch = num_to_arch.get(num)
        if arch is None:
            continue
        for t in _tags(p):
            tag_arch_count[t][arch] += 1
            tag_total[t] += 1

    results = []
    for tag, counts in tag_arch_count.items():
        if tag_total[tag] < 3:
            continue

        total = tag_total[tag]
        distribution = {str(k): v / total for k, v in counts.most_common()}
        primary = counts.most_common(1)[0][0]

        results.append({
            "tag": tag,
            "primary_archetype": primary,
            "concentration": counts.most_common(1)[0][1] / total,
            "distribution": distribution,
            "total_count": total,
        })

    results.sort(key=lambda r: -r["concentration"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Prize Efficiency by Archetype
# ═══════════════════════════════════════════════════════════════════

def prize_efficiency(problems: List[Dict],
                     archetypes: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
    """
    For each archetype, compute prize efficiency:
    total_prize / (1 - solve_rate) — prize per unit of remaining difficulty.

    Higher = more prize money available per unit of unsolved difficulty.
    """
    if archetypes is None:
        archetypes = discover_archetypes(problems)

    results = []
    for arch in archetypes:
        remaining = 1.0 - arch["solve_rate"]
        if remaining <= 0:
            efficiency = 0.0
        else:
            efficiency = arch["prize_total"] / remaining / max(arch["size"], 1)

        results.append({
            "archetype_id": arch["archetype_id"],
            "size": arch["size"],
            "solve_rate": arch["solve_rate"],
            "open_count": arch["open_count"],
            "prize_total": arch["prize_total"],
            "efficiency": efficiency,
            "top_tags": arch["top_tags"],
            "representative": arch["representative"],
        })

    results.sort(key=lambda r: -r["efficiency"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    signal_space = build_signal_space(problems)
    archetypes = discover_archetypes(problems, signal_space)
    blindspots = find_blindspots(problems, signal_space)
    similar = solve_similarity(problems, signal_space)
    tag_map = tag_archetype_map(problems, archetypes)
    efficiency = prize_efficiency(problems, archetypes)

    lines = ["# Pattern Synthesis: Meta-Patterns Across Analyses", ""]
    lines.append(f"Analyzing {len(problems)} problems across {len(signal_space['dim_names'])} signal dimensions.")
    lines.append(f"Discovered **{len(archetypes)} problem archetypes**.")
    lines.append("")

    # Section 1: Archetypes
    lines.append("## 1. Problem Archetypes")
    lines.append("")
    lines.append("| ID | Size | Solve Rate | Open | Prize | Top Tags | Representative |")
    lines.append("|----|------|------------|------|-------|----------|----------------|")
    for arch in archetypes:
        tags_str = ", ".join(arch["top_tags"][:3])
        prize_str = f"${arch['prize_total']:.0f}" if arch["prize_total"] > 0 else "-"
        lines.append(f"| {arch['archetype_id']} | {arch['size']} | "
                      f"{arch['solve_rate']:.0%} | {arch['open_count']} | "
                      f"{prize_str} | {tags_str} | #{arch['representative']} |")
    lines.append("")

    # Centroid profiles
    lines.append("### Centroid Profiles")
    lines.append("")
    for arch in archetypes[:5]:
        lines.append(f"**Archetype {arch['archetype_id']}** ({arch['size']} problems, "
                      f"{arch['solve_rate']:.0%} solved)")
        for dim, val in sorted(arch["centroid"].items(), key=lambda x: -x[1]):
            bar = "█" * int(val * 20) if val > 0 else ""
            lines.append(f"  {dim:20s} {val:+.3f} {bar}")
        lines.append("")

    # Section 2: Solve-Similarity
    lines.append("## 2. Open Problems Most Similar to Solved Ones")
    lines.append("")
    lines.append("| Problem | Distance | Nearest Solved | Shared Tags | Prize |")
    lines.append("|---------|----------|----------------|-------------|-------|")
    for s in similar[:15]:
        shared_str = ", ".join(s["shared_tags"][:3])
        prize_str = f"${s['prize']:.0f}" if s["prize"] > 0 else "-"
        lines.append(f"| #{s['number']} | {s['distance']:.2f} | "
                      f"#{s['nearest_solved']} | {shared_str} | {prize_str} |")
    lines.append("")

    # Section 3: Blindspots
    lines.append("## 3. Analytical Blindspots (Undervalued Problems)")
    lines.append("")
    lines.append(f"**{len(blindspots)} problems** have high importance indicators but")
    lines.append("score low on tractability dimensions.")
    lines.append("")
    if blindspots:
        lines.append("| Problem | Importance | Tractability | Gap | Tags | Prize |")
        lines.append("|---------|------------|-------------|-----|------|-------|")
        for b in blindspots[:15]:
            tags_str = ", ".join(b["tags"][:3])
            prize_str = f"${b['prize']:.0f}" if b["prize"] > 0 else "-"
            lines.append(f"| #{b['number']} | {b['importance']:.2f} | "
                          f"{b['tractability']:.2f} | {b['gap']:.2f} | "
                          f"{tags_str} | {prize_str} |")
    lines.append("")

    # Section 4: Tag-Archetype Map
    lines.append("## 4. Tag-Archetype Mapping")
    lines.append("")
    lines.append("Tags concentrated in a single archetype:")
    lines.append("")
    lines.append("| Tag | Primary Archetype | Concentration | Count |")
    lines.append("|-----|-------------------|---------------|-------|")
    for t in tag_map[:15]:
        lines.append(f"| {t['tag']} | {t['primary_archetype']} | "
                      f"{t['concentration']:.0%} | {t['total_count']} |")
    lines.append("")

    # Section 5: Prize Efficiency
    lines.append("## 5. Prize Efficiency by Archetype")
    lines.append("")
    lines.append("| Archetype | Size | Rate | Open | Prize | Efficiency | Tags |")
    lines.append("|-----------|------|------|------|-------|------------|------|")
    for e in efficiency:
        tags_str = ", ".join(e["top_tags"][:3])
        prize_str = f"${e['prize_total']:.0f}" if e["prize_total"] > 0 else "-"
        lines.append(f"| {e['archetype_id']} | {e['size']} | "
                      f"{e['solve_rate']:.0%} | {e['open_count']} | "
                      f"{prize_str} | {e['efficiency']:.1f} | {tags_str} |")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    problems = load_problems()
    report = generate_report(problems)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")
