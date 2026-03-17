#!/usr/bin/env python3
"""
Difficulty Evolution — How Problem Hardness Evolves Across the Corpus

Since explicit year-of-solution data is unavailable, we use problem number
as a temporal proxy (Erdős assigned numbers roughly chronologically).

Key analyses:
1. Resolution density: solve rate as a function of problem number (era)
2. Difficulty acceleration: whether later problems are harder
3. Breakthrough cascades: clusters of solved problems suggesting technique diffusion
4. Survival analysis: expected "lifetime" of an open problem based on features
5. Era analysis: characteristic difficulty of each problem-number epoch
"""

import math
import yaml
import re
import numpy as np
from collections import defaultdict, Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "difficulty_evolution_report.md"


def load_problems() -> List[Dict]:
    with open(DATA_PATH) as f:
        return yaml.safe_load(f)


def _number(p: Dict) -> int:
    n = p.get("number", 0)
    try:
        return int(n)
    except (TypeError, ValueError):
        return 0


def _tags(p: Dict) -> Set[str]:
    return set(p.get("tags", []))


def _status(p: Dict) -> str:
    return p.get("status", {}).get("state", "unknown")


def _is_solved(p: Dict) -> bool:
    return _status(p) in ("proved", "disproved", "solved",
                          "proved (Lean)", "disproved (Lean)", "solved (Lean)")


def _has_prize(p: Dict) -> bool:
    prize = p.get("prize")
    if not prize:
        return False
    try:
        return float(str(prize).replace("$", "").replace(",", "")) > 0
    except (ValueError, TypeError):
        return False


def _prize_value(p: Dict) -> float:
    prize = p.get("prize")
    if not prize:
        return 0.0
    try:
        return float(str(prize).replace("$", "").replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


# ══════════════════════════════════════════════════════════════════════
# Resolution Density by Era
# ══════════════════════════════════════════════════════════════════════

def resolution_density(problems: List[Dict],
                       window_size: int = 50) -> Dict[str, Any]:
    """
    Compute solve rate in sliding windows of problem numbers.

    This reveals how difficulty evolves across the corpus.
    """
    by_num = {}
    for p in problems:
        num = _number(p)
        if num > 0:
            by_num[num] = p

    numbers = sorted(by_num.keys())
    if not numbers:
        return {"windows": [], "trend": "unknown"}

    windows = []
    for start in range(0, len(numbers), window_size // 2):
        chunk = numbers[start:start + window_size]
        if len(chunk) < window_size // 4:
            break

        n_solved = sum(1 for num in chunk if _is_solved(by_num[num]))
        n_open = sum(1 for num in chunk if _status(by_num[num]) == "open")
        total = n_solved + n_open

        windows.append({
            "start_num": chunk[0],
            "end_num": chunk[-1],
            "n_problems": len(chunk),
            "n_solved": n_solved,
            "n_open": n_open,
            "solve_rate": round(n_solved / total, 3) if total > 0 else 0,
        })

    # Trend: linear regression of solve_rate vs window index
    if len(windows) >= 3:
        x = np.arange(len(windows))
        y = np.array([w["solve_rate"] for w in windows])
        slope = float(np.polyfit(x, y, 1)[0])
        trend = "decreasing" if slope < -0.005 else "increasing" if slope > 0.005 else "stable"
    else:
        slope = 0
        trend = "insufficient_data"

    return {
        "windows": windows,
        "n_windows": len(windows),
        "trend": trend,
        "trend_slope": round(slope, 4),
        "overall_solve_rate": round(
            sum(w["n_solved"] for w in windows) /
            max(sum(w["n_solved"] + w["n_open"] for w in windows), 1), 3),
    }


# ══════════════════════════════════════════════════════════════════════
# Era Analysis
# ══════════════════════════════════════════════════════════════════════

def era_analysis(problems: List[Dict]) -> Dict[str, Any]:
    """
    Partition problems into eras by number range and analyze each era.

    Eras: [1-100], [101-300], [301-500], [501-700], [701-900], [901-1135]
    """
    ERA_BOUNDARIES = [
        (1, 100, "Early"),
        (101, 300, "Classical"),
        (301, 500, "Middle"),
        (501, 700, "Late-Middle"),
        (701, 900, "Late"),
        (901, 1200, "Modern"),
    ]

    prob_map = {}
    for p in problems:
        num = _number(p)
        if num > 0:
            prob_map[num] = p

    eras = []
    for lo, hi, name in ERA_BOUNDARIES:
        era_probs = [prob_map[n] for n in prob_map if lo <= n <= hi]
        if not era_probs:
            continue

        n_solved = sum(1 for p in era_probs if _is_solved(p))
        n_open = sum(1 for p in era_probs if _status(p) == "open")
        n_prize = sum(1 for p in era_probs if _has_prize(p))
        n_formalized = sum(1 for p in era_probs
                          if p.get("formalized") not in (None, False, "No", "no"))
        total = n_solved + n_open

        # Tag diversity
        all_tags = set()
        for p in era_probs:
            all_tags.update(_tags(p))

        # Dominant tags
        tag_counts = Counter()
        for p in era_probs:
            for t in _tags(p):
                tag_counts[t] += 1

        eras.append({
            "era": name,
            "range": f"{lo}-{hi}",
            "n_problems": len(era_probs),
            "solve_rate": round(n_solved / total, 3) if total > 0 else 0,
            "n_solved": n_solved,
            "n_open": n_open,
            "prize_fraction": round(n_prize / len(era_probs), 3),
            "formalized_fraction": round(n_formalized / len(era_probs), 3),
            "tag_diversity": len(all_tags),
            "dominant_tags": [t for t, _ in tag_counts.most_common(3)],
        })

    # Is difficulty monotonically increasing?
    solve_rates = [e["solve_rate"] for e in eras]
    monotone_decreasing = all(
        solve_rates[i] >= solve_rates[i+1] - 0.05
        for i in range(len(solve_rates) - 1)
    )

    return {
        "eras": eras,
        "n_eras": len(eras),
        "difficulty_monotone": monotone_decreasing,
        "easiest_era": min(eras, key=lambda e: e["solve_rate"])["era"] if eras else None,
        "hardest_era": max(eras, key=lambda e: e["solve_rate"])["era"] if eras else None,
    }


# ══════════════════════════════════════════════════════════════════════
# Breakthrough Cascades
# ══════════════════════════════════════════════════════════════════════

def breakthrough_cascades(problems: List[Dict],
                         cluster_gap: int = 5) -> Dict[str, Any]:
    """
    Detect clusters of solved problems in number space.

    A "cascade" is a run of ≥3 solved problems within `cluster_gap` numbers
    of each other. These suggest that a breakthrough technique solved
    multiple related problems.
    """
    prob_map = {}
    for p in problems:
        num = _number(p)
        if num > 0:
            prob_map[num] = p

    solved_nums = sorted(num for num, p in prob_map.items() if _is_solved(p))

    if len(solved_nums) < 3:
        return {"cascades": [], "n_cascades": 0}

    # Find clusters
    cascades = []
    current_cluster = [solved_nums[0]]

    for i in range(1, len(solved_nums)):
        if solved_nums[i] - solved_nums[i-1] <= cluster_gap:
            current_cluster.append(solved_nums[i])
        else:
            if len(current_cluster) >= 3:
                # Analyze this cascade
                cluster_tags = Counter()
                for num in current_cluster:
                    for t in _tags(prob_map[num]):
                        cluster_tags[t] += 1

                cascades.append({
                    "start": current_cluster[0],
                    "end": current_cluster[-1],
                    "size": len(current_cluster),
                    "problems": current_cluster,
                    "span": current_cluster[-1] - current_cluster[0],
                    "dominant_tags": [t for t, _ in cluster_tags.most_common(3)],
                })
            current_cluster = [solved_nums[i]]

    # Don't forget the last cluster
    if len(current_cluster) >= 3:
        cluster_tags = Counter()
        for num in current_cluster:
            for t in _tags(prob_map[num]):
                cluster_tags[t] += 1
        cascades.append({
            "start": current_cluster[0],
            "end": current_cluster[-1],
            "size": len(current_cluster),
            "problems": current_cluster,
            "span": current_cluster[-1] - current_cluster[0],
            "dominant_tags": [t for t, _ in cluster_tags.most_common(3)],
        })

    cascades.sort(key=lambda c: -c["size"])

    return {
        "cascades": cascades,
        "n_cascades": len(cascades),
        "largest_cascade": cascades[0]["size"] if cascades else 0,
        "total_in_cascades": sum(c["size"] for c in cascades),
        "cascade_fraction": round(
            sum(c["size"] for c in cascades) / max(len(solved_nums), 1), 3),
    }


# ══════════════════════════════════════════════════════════════════════
# Difficulty Features
# ══════════════════════════════════════════════════════════════════════

def difficulty_features(problems: List[Dict]) -> Dict[str, Any]:
    """
    Analyze which features predict whether a problem is solved or open.

    Uses simple feature comparison between solved and open populations.
    """
    solved_features = {"n_tags": [], "has_prize": [], "prize_value": [],
                       "n_oeis": [], "formalized": [], "number": []}
    open_features = {"n_tags": [], "has_prize": [], "prize_value": [],
                     "n_oeis": [], "formalized": [], "number": []}

    for p in problems:
        num = _number(p)
        if num <= 0:
            continue

        oeis = p.get("oeis", []) or []
        n_oeis = len([s for s in oeis if s and s not in ("N/A", "possible")])
        formalized = 1 if p.get("formalized") not in (None, False, "No", "no") else 0

        features = {
            "n_tags": len(_tags(p)),
            "has_prize": 1 if _has_prize(p) else 0,
            "prize_value": _prize_value(p),
            "n_oeis": n_oeis,
            "formalized": formalized,
            "number": num,
        }

        target = solved_features if _is_solved(p) else open_features if _status(p) == "open" else None
        if target is not None:
            for k, v in features.items():
                target[k].append(v)

    comparisons = {}
    for feat in solved_features:
        s_vals = np.array(solved_features[feat])
        o_vals = np.array(open_features[feat])
        if len(s_vals) > 0 and len(o_vals) > 0:
            comparisons[feat] = {
                "solved_mean": round(float(np.mean(s_vals)), 3),
                "open_mean": round(float(np.mean(o_vals)), 3),
                "difference": round(float(np.mean(o_vals) - np.mean(s_vals)), 3),
                "effect_size": round(
                    float((np.mean(o_vals) - np.mean(s_vals)) /
                          max(np.std(np.concatenate([s_vals, o_vals])), 0.001)), 3),
            }

    return {
        "n_solved": len(solved_features["number"]),
        "n_open": len(open_features["number"]),
        "comparisons": comparisons,
    }


# ══════════════════════════════════════════════════════════════════════
# Survival Analysis (Simplified)
# ══════════════════════════════════════════════════════════════════════

def survival_analysis(problems: List[Dict]) -> Dict[str, Any]:
    """
    Simplified survival analysis: model the probability a problem remains
    open as a function of its "age" (max_number - number) and features.

    Uses a Kaplan-Meier-like estimator on problem number.
    """
    prob_map = {}
    for p in problems:
        num = _number(p)
        if num > 0:
            prob_map[num] = p

    max_num = max(prob_map.keys())

    # "Age" = max_num - number (higher = older)
    ages_solved = []
    ages_open = []  # censored observations

    for num, p in prob_map.items():
        age = max_num - num
        if _is_solved(p):
            ages_solved.append(age)
        elif _status(p) == "open":
            ages_open.append(age)

    if not ages_solved:
        return {"survival_curve": [], "median_survival": None}

    # Kaplan-Meier: at each age, compute survival probability
    # Event = "solved" (failure), censored = "still open"
    all_ages = sorted(set(ages_solved + ages_open))

    # Group by age buckets (every 50 numbers)
    bucket_size = 50
    n_buckets = (max_num // bucket_size) + 1

    buckets = []
    at_risk = len(ages_solved) + len(ages_open)
    cumulative_survival = 1.0

    for b in range(n_buckets):
        age_lo = b * bucket_size
        age_hi = (b + 1) * bucket_size

        events = sum(1 for a in ages_solved if age_lo <= a < age_hi)
        censored = sum(1 for a in ages_open if age_lo <= a < age_hi)

        if at_risk > 0 and events > 0:
            hazard = events / at_risk
            cumulative_survival *= (1 - hazard)

        buckets.append({
            "age_range": f"{age_lo}-{age_hi}",
            "number_range": f"{max_num - age_hi}-{max_num - age_lo}",
            "at_risk": at_risk,
            "events": events,
            "censored": censored,
            "survival_prob": round(cumulative_survival, 3),
        })

        at_risk -= (events + censored)
        if at_risk <= 0:
            break

    # Median survival age
    median_age = None
    for bucket in buckets:
        if bucket["survival_prob"] <= 0.5:
            median_age = bucket["age_range"]
            break

    return {
        "survival_curve": buckets,
        "median_survival_age": median_age,
        "n_events": len(ages_solved),
        "n_censored": len(ages_open),
        "oldest_solved_age": max(ages_solved) if ages_solved else 0,
        "youngest_open_age": min(ages_open) if ages_open else 0,
    }


# ══════════════════════════════════════════════════════════════════════
# Tag Difficulty Ranking
# ══════════════════════════════════════════════════════════════════════

def tag_difficulty_ranking(problems: List[Dict],
                          min_count: int = 10) -> Dict[str, Any]:
    """
    Rank mathematical tags by difficulty (solve rate).
    """
    tag_stats = defaultdict(lambda: {"solved": 0, "open": 0})

    for p in problems:
        num = _number(p)
        if num <= 0:
            continue

        state = "solved" if _is_solved(p) else "open" if _status(p) == "open" else None
        if state:
            for t in _tags(p):
                tag_stats[t][state] += 1

    rankings = []
    for tag, stats in tag_stats.items():
        total = stats["solved"] + stats["open"]
        if total >= min_count:
            rankings.append({
                "tag": tag,
                "total": total,
                "solve_rate": round(stats["solved"] / total, 3),
                "n_open": stats["open"],
            })

    rankings.sort(key=lambda x: x["solve_rate"])

    return {
        "rankings": rankings,
        "n_ranked": len(rankings),
        "hardest_tag": rankings[0]["tag"] if rankings else None,
        "easiest_tag": rankings[-1]["tag"] if rankings else None,
    }


# ══════════════════════════════════════════════════════════════════════
# Difficulty Concentration
# ══════════════════════════════════════════════════════════════════════

def difficulty_concentration(problems: List[Dict]) -> Dict[str, Any]:
    """
    Measure whether difficulty is concentrated in specific regions
    or distributed uniformly.

    Uses Gini coefficient on solve rates across sliding windows.
    """
    density = resolution_density(problems, window_size=50)
    rates = [w["solve_rate"] for w in density["windows"] if w["n_problems"] >= 10]

    if len(rates) < 3:
        return {"gini": 0, "variance": 0, "distribution": "insufficient_data"}

    # Gini coefficient
    rates_arr = np.array(sorted(rates))
    n = len(rates_arr)
    index = np.arange(1, n + 1)
    gini = float((2 * np.sum(index * rates_arr) - (n + 1) * np.sum(rates_arr)) /
                 (n * np.sum(rates_arr))) if np.sum(rates_arr) > 0 else 0

    variance = float(np.var(rates))
    cv = float(np.std(rates) / np.mean(rates)) if np.mean(rates) > 0 else 0

    if gini > 0.3:
        distribution = "concentrated"
    elif gini > 0.15:
        distribution = "moderately_spread"
    else:
        distribution = "uniform"

    return {
        "gini": round(gini, 3),
        "variance": round(variance, 4),
        "coefficient_of_variation": round(cv, 3),
        "distribution": distribution,
        "min_rate": round(min(rates), 3),
        "max_rate": round(max(rates), 3),
        "range": round(max(rates) - min(rates), 3),
    }


# ══════════════════════════════════════════════════════════════════════
# Report
# ══════════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    lines = [
        "# Difficulty Evolution: How Problem Hardness Evolves",
        "",
    ]

    # Resolution density
    lines.append("## Resolution Density")
    rd = resolution_density(problems)
    lines.append(f"**Trend**: {rd['trend']} (slope={rd['trend_slope']})")
    lines.append(f"**Overall solve rate**: {rd['overall_solve_rate']}")
    lines.append("")
    for w in rd["windows"]:
        lines.append(f"  #{w['start_num']}-{w['end_num']}: "
                     f"{w['solve_rate']:.1%} ({w['n_solved']}/{w['n_solved']+w['n_open']})")
    lines.append("")

    # Era analysis
    lines.append("## Era Analysis")
    ea = era_analysis(problems)
    lines.append(f"**Difficulty monotone**: {ea['difficulty_monotone']}")
    for e in ea["eras"]:
        lines.append(f"- **{e['era']}** ({e['range']}): {e['solve_rate']:.1%} solved, "
                     f"prize={e['prize_fraction']:.1%}, "
                     f"tags: {', '.join(e['dominant_tags'][:3])}")
    lines.append("")

    # Breakthrough cascades
    lines.append("## Breakthrough Cascades")
    bc = breakthrough_cascades(problems)
    lines.append(f"**Cascades found**: {bc['n_cascades']}")
    lines.append(f"**Largest**: {bc['largest_cascade']} problems")
    lines.append(f"**In cascades**: {bc['cascade_fraction']:.1%} of solved")
    for c in bc["cascades"][:8]:
        lines.append(f"  #{c['start']}-#{c['end']}: {c['size']} problems, "
                     f"tags: {', '.join(c['dominant_tags'][:2])}")
    lines.append("")

    # Difficulty features
    lines.append("## Difficulty Feature Comparison (Open vs Solved)")
    df = difficulty_features(problems)
    for feat, comp in df["comparisons"].items():
        lines.append(f"- **{feat}**: solved={comp['solved_mean']}, "
                     f"open={comp['open_mean']}, "
                     f"effect={comp['effect_size']}")
    lines.append("")

    # Survival analysis
    lines.append("## Survival Analysis")
    sa = survival_analysis(problems)
    lines.append(f"**Median survival age**: {sa['median_survival_age']}")
    lines.append(f"**Events/Censored**: {sa['n_events']}/{sa['n_censored']}")
    for b in sa["survival_curve"][:10]:
        lines.append(f"  Age {b['age_range']} (#{b['number_range']}): "
                     f"survival={b['survival_prob']:.1%}")
    lines.append("")

    # Tag difficulty
    lines.append("## Tag Difficulty Ranking")
    tdr = tag_difficulty_ranking(problems)
    for r in tdr["rankings"]:
        lines.append(f"- **{r['tag']}**: {r['solve_rate']:.1%} ({r['n_open']} open)")
    lines.append("")

    # Concentration
    lines.append("## Difficulty Concentration")
    dc = difficulty_concentration(problems)
    lines.append(f"**Gini**: {dc['gini']}")
    lines.append(f"**Distribution**: {dc['distribution']}")
    lines.append(f"**Range**: {dc['min_rate']:.1%} - {dc['max_rate']:.1%}")
    lines.append("")

    return "\n".join(lines)


def main():
    problems = load_problems()
    report = generate_report(problems)
    print(report)
    REPORT_PATH.write_text(report)
    print(f"\nReport written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
