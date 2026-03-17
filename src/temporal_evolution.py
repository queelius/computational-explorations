#!/usr/bin/env python3
"""
temporal_evolution.py — Structural evolution analysis of the Erdős problem database.

Since the database lacks true resolution timestamps (all last_update = 2025-08-31),
this module analyzes how problem STRUCTURE evolves across problem number space,
which correlates with chronological ordering (earlier numbers = earlier problems).

Discovers:
  1. Problem Number Epochs: how problem character changes over time
  2. Tag Emergence Curves: when tags first appear, peak, and fade
  3. Difficulty Gradient: how solvability changes across problem number
  4. Prize Decay: how prize distribution evolves
  5. Formalization Frontier: which problem regions have been formalized
  6. Complexity Drift: how structural complexity changes with problem number
  7. Status Landscape: how problem status distributes across number space

Output: docs/temporal_evolution_report.md
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
REPORT_PATH = ROOT / "docs" / "temporal_evolution_report.md"


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


def _oeis_count(p: Dict) -> int:
    oeis = p.get("oeis", [])
    # Filter out placeholder sequences (A000000 or similar)
    real = [s for s in oeis if s and s != "A000000" and not s.startswith("A00000")]
    return len(real)


def _is_formalized(p: Dict) -> bool:
    return p.get("formalized", {}).get("state", "no") == "yes"


# ═══════════════════════════════════════════════════════════════════
# 1. Problem Number Epochs
# ═══════════════════════════════════════════════════════════════════

def problem_epochs(problems: List[Dict], epoch_size: int = 100) -> List[Dict]:
    """
    Divide problems into epochs by number and characterize each.

    Each epoch gets: solve rate, tag distribution, prize density,
    formalization rate, OEIS connectivity, and dominant theme.
    """
    by_number = sorted(problems, key=_number)

    epochs = []
    for start in range(0, len(by_number), epoch_size):
        chunk = by_number[start:start + epoch_size]
        if not chunk:
            break

        numbers = [_number(p) for p in chunk]
        n_solved = sum(1 for p in chunk if _is_solved(p))
        n_open = sum(1 for p in chunk if _is_open(p))
        n_formalized = sum(1 for p in chunk if _is_formalized(p))
        prizes = [_prize(p) for p in chunk if _prize(p) > 0]
        oeis_total = sum(_oeis_count(p) for p in chunk)

        # Tag distribution
        tag_counts = Counter(t for p in chunk for t in _tags(p))
        tag_diversity = len(tag_counts)
        dominant_tag = tag_counts.most_common(1)[0] if tag_counts else ("none", 0)

        # Average tags per problem
        avg_tags = np.mean([len(_tags(p)) for p in chunk])

        epochs.append({
            "epoch_start": min(numbers),
            "epoch_end": max(numbers),
            "size": len(chunk),
            "solve_rate": round(n_solved / len(chunk), 3) if chunk else 0,
            "open_rate": round(n_open / len(chunk), 3) if chunk else 0,
            "formalization_rate": round(n_formalized / len(chunk), 3) if chunk else 0,
            "prize_count": len(prizes),
            "total_prize": sum(prizes),
            "avg_prize": round(np.mean(prizes), 0) if prizes else 0,
            "oeis_per_problem": round(oeis_total / len(chunk), 2) if chunk else 0,
            "tag_diversity": tag_diversity,
            "dominant_tag": dominant_tag[0],
            "dominant_tag_fraction": round(dominant_tag[1] / len(chunk), 2) if chunk else 0,
            "avg_tags": round(float(avg_tags), 2),
        })

    return epochs


# ═══════════════════════════════════════════════════════════════════
# 2. Tag Emergence Curves
# ═══════════════════════════════════════════════════════════════════

def tag_emergence(problems: List[Dict]) -> Dict[str, Any]:
    """
    For each tag, track when it first appears, peaks, and fades.

    Returns: tag lifecycle profiles showing birth, peak, and current
    activity levels across problem number space.
    """
    by_number = sorted(problems, key=_number)
    all_tags = set(t for p in problems for t in _tags(p))

    tag_profiles = {}
    for tag in all_tags:
        numbers = [_number(p) for p in by_number if tag in _tags(p)]
        if not numbers:
            continue

        # Solve rate for this tag
        tag_problems = [p for p in problems if tag in _tags(p)]
        n_solved = sum(1 for p in tag_problems if _is_solved(p))
        solve_rate = n_solved / len(tag_problems) if tag_problems else 0

        # Density curve: fraction of problems with this tag in sliding windows
        window = 100
        density_curve = []
        for start in range(0, len(by_number), window // 2):
            chunk = by_number[start:start + window]
            if not chunk:
                break
            frac = sum(1 for p in chunk if tag in _tags(p)) / len(chunk)
            mid = _number(chunk[len(chunk) // 2])
            density_curve.append((mid, round(frac, 3)))

        # Find peak density
        if density_curve:
            peak_idx = max(range(len(density_curve)), key=lambda i: density_curve[i][1])
            peak_number = density_curve[peak_idx][0]
            peak_density = density_curve[peak_idx][1]
        else:
            peak_number = numbers[0]
            peak_density = 0

        tag_profiles[tag] = {
            "first_appearance": min(numbers),
            "last_appearance": max(numbers),
            "count": len(numbers),
            "solve_rate": round(solve_rate, 3),
            "peak_number": peak_number,
            "peak_density": peak_density,
            "span": max(numbers) - min(numbers),
            "density_curve": density_curve,
        }

    # Classify tags by lifecycle phase
    emerging = []  # late first appearance, rising density
    established = []  # wide span, stable density
    declining = []  # density peak in early numbers

    max_number = max(_number(p) for p in problems)
    for tag, prof in tag_profiles.items():
        if prof["count"] < 5:
            continue
        relative_peak = prof["peak_number"] / max_number if max_number > 0 else 0
        relative_first = prof["first_appearance"] / max_number if max_number > 0 else 0

        if relative_first > 0.5:
            emerging.append((tag, prof))
        elif relative_peak < 0.3:
            declining.append((tag, prof))
        else:
            established.append((tag, prof))

    emerging.sort(key=lambda x: x[1]["first_appearance"], reverse=True)
    declining.sort(key=lambda x: x[1]["peak_number"])
    established.sort(key=lambda x: -x[1]["count"])

    return {
        "tag_profiles": tag_profiles,
        "emerging": [(t, p["first_appearance"], p["count"]) for t, p in emerging],
        "established": [(t, p["count"], p["solve_rate"]) for t, p in established],
        "declining": [(t, p["peak_number"], p["count"]) for t, p in declining],
    }


# ═══════════════════════════════════════════════════════════════════
# 3. Difficulty Gradient
# ═══════════════════════════════════════════════════════════════════

def difficulty_gradient(problems: List[Dict], window: int = 50) -> Dict[str, Any]:
    """
    Analyze how problem difficulty changes across number space.

    Uses solve rate as primary difficulty proxy, supplemented by
    formalization rate and prize amounts.
    """
    by_number = sorted(problems, key=_number)
    n = len(by_number)

    gradient_points = []
    for start in range(0, n, window // 2):
        chunk = by_number[start:start + window]
        if len(chunk) < window // 4:
            break

        mid = _number(chunk[len(chunk) // 2])
        solve_rate = sum(1 for p in chunk if _is_solved(p)) / len(chunk)
        open_rate = sum(1 for p in chunk if _is_open(p)) / len(chunk)
        form_rate = sum(1 for p in chunk if _is_formalized(p)) / len(chunk)
        avg_prize = np.mean([_prize(p) for p in chunk if _prize(p) > 0]) if any(_prize(p) > 0 for p in chunk) else 0

        gradient_points.append({
            "center_number": mid,
            "solve_rate": round(solve_rate, 3),
            "open_rate": round(open_rate, 3),
            "formalization_rate": round(form_rate, 3),
            "avg_prize": round(float(avg_prize), 0),
            "window_size": len(chunk),
        })

    # Compute overall trend (linear regression of solve rate vs number)
    if len(gradient_points) >= 3:
        x = np.array([g["center_number"] for g in gradient_points], dtype=float)
        y = np.array([g["solve_rate"] for g in gradient_points], dtype=float)
        x_mean, y_mean = x.mean(), y.mean()
        denom = np.sum((x - x_mean) ** 2)
        slope = np.sum((x - x_mean) * (y - y_mean)) / denom if denom > 0 else 0
        intercept = y_mean - slope * x_mean
        trend = "getting easier" if slope > 0.0001 else ("getting harder" if slope < -0.0001 else "stable")
    else:
        slope, intercept, trend = 0, 0, "insufficient data"

    # Find the "difficulty cliff" — largest drop in solve rate
    max_drop = 0
    cliff_at = None
    for i in range(1, len(gradient_points)):
        drop = gradient_points[i - 1]["solve_rate"] - gradient_points[i]["solve_rate"]
        if drop > max_drop:
            max_drop = drop
            cliff_at = gradient_points[i]["center_number"]

    return {
        "gradient_points": gradient_points,
        "trend_slope": round(slope, 6),
        "trend_direction": trend,
        "difficulty_cliff": cliff_at,
        "cliff_magnitude": round(max_drop, 3),
        "easiest_region": min(gradient_points, key=lambda g: -g["solve_rate"])["center_number"] if gradient_points else None,
        "hardest_region": min(gradient_points, key=lambda g: g["solve_rate"])["center_number"] if gradient_points else None,
    }


# ═══════════════════════════════════════════════════════════════════
# 4. Status Landscape
# ═══════════════════════════════════════════════════════════════════

def status_landscape(problems: List[Dict], window: int = 100) -> Dict[str, Any]:
    """
    Map the distribution of problem statuses across number space.

    Shows how the "landscape" of open/proved/disproved/etc changes,
    revealing regions of concentrated activity or stagnation.
    """
    by_number = sorted(problems, key=_number)
    n = len(by_number)

    # Define status categories
    def categorize(p):
        s = _status(p)
        if s in ("proved", "proved (Lean)"):
            return "proved"
        elif s in ("disproved", "disproved (Lean)"):
            return "disproved"
        elif s in ("solved", "solved (Lean)"):
            return "solved"
        elif s == "open":
            return "open"
        elif s in ("falsifiable", "verifiable", "decidable"):
            return "tractable"
        else:
            return "other"

    landscape_points = []
    for start in range(0, n, window // 2):
        chunk = by_number[start:start + window]
        if len(chunk) < window // 4:
            break

        mid = _number(chunk[len(chunk) // 2])
        cats = Counter(categorize(p) for p in chunk)
        total = len(chunk)

        landscape_points.append({
            "center": mid,
            "proved": round(cats.get("proved", 0) / total, 3),
            "disproved": round(cats.get("disproved", 0) / total, 3),
            "solved": round(cats.get("solved", 0) / total, 3),
            "open": round(cats.get("open", 0) / total, 3),
            "tractable": round(cats.get("tractable", 0) / total, 3),
        })

    # Find "dead zones" — regions with >90% open problems
    dead_zones = [lp for lp in landscape_points if lp["open"] > 0.85]

    # Find "golden zones" — regions with >50% solved
    golden_zones = [lp for lp in landscape_points
                    if (lp["proved"] + lp["disproved"] + lp["solved"]) > 0.50]

    # Disproof clusters — where are disproved problems concentrated?
    disproof_hotspots = sorted(landscape_points, key=lambda x: -x["disproved"])[:5]

    return {
        "landscape": landscape_points,
        "dead_zones": [(dz["center"], dz["open"]) for dz in dead_zones],
        "golden_zones": [(gz["center"], gz["proved"] + gz["disproved"] + gz["solved"]) for gz in golden_zones],
        "disproof_hotspots": [(dh["center"], dh["disproved"]) for dh in disproof_hotspots],
    }


# ═══════════════════════════════════════════════════════════════════
# 5. Tag Succession Patterns
# ═══════════════════════════════════════════════════════════════════

def tag_succession(problems: List[Dict]) -> Dict[str, Any]:
    """
    Analyze which tags "follow" which in problem number ordering.

    If problems about X tend to be followed by problems about Y,
    this reveals thematic succession patterns in Erdős's thinking.
    """
    by_number = sorted(problems, key=_number)

    # Build transition matrix: P(tag_j at position i+1 | tag_i at position i)
    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    tag_idx = {t: i for i, t in enumerate(all_tags)}
    n_tags = len(all_tags)

    transitions = np.zeros((n_tags, n_tags), dtype=float)
    for i in range(len(by_number) - 1):
        tags_current = _tags(by_number[i])
        tags_next = _tags(by_number[i + 1])
        for t1 in tags_current:
            for t2 in tags_next:
                transitions[tag_idx[t1], tag_idx[t2]] += 1

    # Normalize rows
    row_sums = transitions.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    trans_probs = transitions / row_sums

    # Find strongest successor relationships (excluding self-transition)
    successors = []
    for i in range(n_tags):
        for j in range(n_tags):
            if i != j and transitions[i, j] > 5:  # minimum count threshold
                successors.append({
                    "from_tag": all_tags[i],
                    "to_tag": all_tags[j],
                    "probability": round(float(trans_probs[i, j]), 3),
                    "count": int(transitions[i, j]),
                })

    successors.sort(key=lambda x: -x["probability"])

    # Find self-reinforcing tags (high self-transition = clustered)
    self_reinforcing = []
    for i in range(n_tags):
        if transitions[i, i] > 3:
            self_reinforcing.append({
                "tag": all_tags[i],
                "self_prob": round(float(trans_probs[i, i]), 3),
                "count": int(transitions[i, i]),
            })
    self_reinforcing.sort(key=lambda x: -x["self_prob"])

    # Compute tag "momentum" — how many consecutive problems share a tag
    tag_runs = defaultdict(list)
    for tag in all_tags:
        run = 0
        for p in by_number:
            if tag in _tags(p):
                run += 1
            elif run > 0:
                tag_runs[tag].append(run)
                run = 0
        if run > 0:
            tag_runs[tag].append(run)

    tag_momentum = {}
    for tag in all_tags:
        runs = tag_runs.get(tag, [])
        if runs:
            tag_momentum[tag] = {
                "max_run": max(runs),
                "avg_run": round(np.mean(runs), 2),
                "num_runs": len(runs),
            }

    return {
        "strongest_successors": successors[:20],
        "self_reinforcing": self_reinforcing[:15],
        "tag_momentum": tag_momentum,
        "transition_matrix_shape": (n_tags, n_tags),
    }


# ═══════════════════════════════════════════════════════════════════
# 6. Complexity Drift
# ═══════════════════════════════════════════════════════════════════

def complexity_drift(problems: List[Dict], window: int = 50) -> Dict[str, Any]:
    """
    Track how problem complexity evolves across number space.

    Complexity proxies:
    - Tag count per problem (more tags = more concepts involved)
    - OEIS connectivity (more sequences = richer structure)
    - Prize amount (harder problems get bigger prizes)
    - Statement length (longer = more complex constraints)
    """
    by_number = sorted(problems, key=_number)
    n = len(by_number)

    drift_points = []
    for start in range(0, n, window // 2):
        chunk = by_number[start:start + window]
        if len(chunk) < window // 4:
            break

        mid = _number(chunk[len(chunk) // 2])
        tag_counts = [len(_tags(p)) for p in chunk]
        oeis_counts = [_oeis_count(p) for p in chunk]
        prizes = [_prize(p) for p in chunk]
        stmt_lengths = [len(str(p.get("statement", ""))) for p in chunk]

        drift_points.append({
            "center_number": mid,
            "avg_tags": round(float(np.mean(tag_counts)), 2),
            "max_tags": max(tag_counts),
            "avg_oeis": round(float(np.mean(oeis_counts)), 2),
            "total_prize": sum(prizes),
            "avg_stmt_length": round(float(np.mean(stmt_lengths)), 0),
            "tag_entropy": round(float(_entropy(Counter(t for p in chunk for t in _tags(p)))), 3),
        })

    # Trend: are problems getting more complex?
    if len(drift_points) >= 3:
        x = np.array([d["center_number"] for d in drift_points], dtype=float)
        y = np.array([d["avg_tags"] for d in drift_points], dtype=float)
        x_mean, y_mean = x.mean(), y.mean()
        denom = np.sum((x - x_mean) ** 2)
        tag_slope = np.sum((x - x_mean) * (y - y_mean)) / denom if denom > 0 else 0
    else:
        tag_slope = 0

    # Find complexity peaks and valleys
    if drift_points:
        most_complex = max(drift_points, key=lambda d: d["avg_tags"])
        least_complex = min(drift_points, key=lambda d: d["avg_tags"])
    else:
        most_complex = least_complex = {}

    return {
        "drift_points": drift_points,
        "tag_complexity_trend": round(tag_slope, 6),
        "complexity_increasing": tag_slope > 0.0001,
        "most_complex_region": most_complex.get("center_number"),
        "least_complex_region": least_complex.get("center_number"),
    }


def _entropy(counter: Counter) -> float:
    """Shannon entropy of a frequency distribution."""
    total = sum(counter.values())
    if total == 0:
        return 0.0
    probs = [c / total for c in counter.values()]
    return -sum(p * math.log2(p) for p in probs if p > 0)


# ═══════════════════════════════════════════════════════════════════
# 7. Named Problem Analysis
# ═══════════════════════════════════════════════════════════════════

def named_problem_analysis(problems: List[Dict]) -> Dict[str, Any]:
    """
    Analyze the 61 named problems (those with 'comments' field).

    Named problems are famous — do they have different characteristics
    than unnamed problems?
    """
    named = [p for p in problems if p.get("comments")]
    unnamed = [p for p in problems if not p.get("comments")]

    def stats(group, label):
        n = len(group)
        if n == 0:
            return {"label": label, "count": 0}
        n_solved = sum(1 for p in group if _is_solved(p))
        n_open = sum(1 for p in group if _is_open(p))
        n_form = sum(1 for p in group if _is_formalized(p))
        prizes = [_prize(p) for p in group if _prize(p) > 0]
        tag_counts = [len(_tags(p)) for p in group]
        return {
            "label": label,
            "count": n,
            "solve_rate": round(n_solved / n, 3),
            "open_rate": round(n_open / n, 3),
            "formalization_rate": round(n_form / n, 3),
            "avg_tags": round(float(np.mean(tag_counts)), 2),
            "prize_problems": len(prizes),
            "total_prize": sum(prizes),
        }

    named_stats = stats(named, "named")
    unnamed_stats = stats(unnamed, "unnamed")

    # Named problems by status
    named_by_status = Counter(_status(p) for p in named)

    # Named problems list
    named_list = []
    for p in sorted(named, key=_number):
        named_list.append({
            "number": _number(p),
            "name": p.get("comments", ""),
            "status": _status(p),
            "tags": sorted(_tags(p)),
            "prize": _prize(p),
        })

    return {
        "named_stats": named_stats,
        "unnamed_stats": unnamed_stats,
        "named_by_status": dict(named_by_status),
        "named_problems": named_list,
    }


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(epochs, emergence, gradient, landscape, succession,
                    drift, named) -> str:
    lines = []
    lines.append("# Temporal Evolution Analysis")
    lines.append("")
    lines.append("How the character of Erdős problems changes across")
    lines.append("problem number space (proxy for chronological ordering).")
    lines.append("")

    # 1. Epochs
    lines.append("## 1. Problem Epochs")
    lines.append("")
    lines.append("| Epoch | Solve Rate | Open Rate | Formalized | Prize $ | Tags/Prob | Dominant Tag |")
    lines.append("|-------|-----------|-----------|-----------|---------|----------|--------------|")
    for e in epochs:
        lines.append(
            f"| {e['epoch_start']}-{e['epoch_end']} | {e['solve_rate']:.1%} | "
            f"{e['open_rate']:.1%} | {e['formalization_rate']:.1%} | "
            f"${e['total_prize']:.0f} | {e['avg_tags']:.1f} | {e['dominant_tag']} |"
        )
    lines.append("")

    # 2. Tag Emergence
    lines.append("## 2. Tag Lifecycle Phases")
    lines.append("")
    if emergence["emerging"]:
        lines.append("### Emerging Tags (late appearance)")
        for tag, first, count in emergence["emerging"][:5]:
            lines.append(f"- **{tag}**: first at #{first} ({count} problems)")
        lines.append("")

    if emergence["declining"]:
        lines.append("### Declining Tags (peak in early problems)")
        for tag, peak, count in emergence["declining"][:5]:
            lines.append(f"- **{tag}**: peaked at #{peak} ({count} problems)")
        lines.append("")

    if emergence["established"]:
        lines.append("### Established Tags (persistent)")
        for tag, count, rate in emergence["established"][:10]:
            lines.append(f"- **{tag}**: {count} problems, solve rate {rate:.1%}")
        lines.append("")

    # 3. Difficulty Gradient
    lines.append("## 3. Difficulty Gradient")
    lines.append("")
    lines.append(f"- Trend: **{gradient['trend_direction']}** (slope={gradient['trend_slope']:.6f})")
    if gradient["difficulty_cliff"]:
        lines.append(f"- Difficulty cliff at problem #{gradient['difficulty_cliff']} (drop={gradient['cliff_magnitude']:.3f})")
    if gradient["easiest_region"]:
        lines.append(f"- Easiest region: around #{gradient['easiest_region']}")
    if gradient["hardest_region"]:
        lines.append(f"- Hardest region: around #{gradient['hardest_region']}")
    lines.append("")

    # 4. Status Landscape
    lines.append("## 4. Status Landscape")
    lines.append("")
    if landscape["dead_zones"]:
        lines.append("### Dead Zones (>85% open)")
        for center, rate in landscape["dead_zones"][:5]:
            lines.append(f"- Around #{center}: {rate:.1%} open")
        lines.append("")
    if landscape["golden_zones"]:
        lines.append("### Golden Zones (>50% resolved)")
        for center, rate in landscape["golden_zones"][:5]:
            lines.append(f"- Around #{center}: {rate:.1%} resolved")
        lines.append("")
    if landscape["disproof_hotspots"]:
        lines.append("### Disproof Hotspots")
        for center, rate in landscape["disproof_hotspots"][:3]:
            lines.append(f"- Around #{center}: {rate:.1%} disproved")
        lines.append("")

    # 5. Tag Succession
    lines.append("## 5. Tag Succession Patterns")
    lines.append("")
    lines.append("### Strongest Successors (tag A → tag B)")
    lines.append("")
    for s in succession["strongest_successors"][:10]:
        lines.append(f"- {s['from_tag']} → **{s['to_tag']}** (p={s['probability']:.3f}, n={s['count']})")
    lines.append("")
    if succession["self_reinforcing"]:
        lines.append("### Most Clustered Tags (self-reinforcing)")
        for sr in succession["self_reinforcing"][:8]:
            lines.append(f"- **{sr['tag']}**: self-probability {sr['self_prob']:.3f}")
        lines.append("")

    # 6. Complexity Drift
    lines.append("## 6. Complexity Drift")
    lines.append("")
    lines.append(f"- Tag complexity trend: {'increasing' if drift['complexity_increasing'] else 'stable or decreasing'}")
    if drift["most_complex_region"]:
        lines.append(f"- Most complex region: around #{drift['most_complex_region']}")
    if drift["least_complex_region"]:
        lines.append(f"- Least complex region: around #{drift['least_complex_region']}")
    lines.append("")

    # 7. Named Problems
    lines.append("## 7. Named Problems")
    lines.append("")
    ns = named["named_stats"]
    us = named["unnamed_stats"]
    lines.append(f"- Named: {ns['count']} problems, solve rate {ns.get('solve_rate', 0):.1%}")
    lines.append(f"- Unnamed: {us['count']} problems, solve rate {us.get('solve_rate', 0):.1%}")
    lines.append(f"- Named formalization: {ns.get('formalization_rate', 0):.1%} vs unnamed {us.get('formalization_rate', 0):.1%}")
    lines.append("")

    lines.append("### Famous Problems")
    lines.append("")
    lines.append("| # | Name | Status | Tags | Prize |")
    lines.append("|---|------|--------|------|-------|")
    for np_ in named["named_problems"][:20]:
        tags = ", ".join(np_["tags"][:2])
        prize = f"${np_['prize']:.0f}" if np_["prize"] > 0 else "-"
        lines.append(f"| #{np_['number']} | {np_['name']} | {np_['status']} | {tags} | {prize} |")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("TEMPORAL EVOLUTION ANALYSIS")
    print("=" * 70)

    problems = load_problems()
    print(f"Loaded {len(problems)} problems")

    print("\n1. Computing problem epochs...")
    epochs = problem_epochs(problems)
    print(f"   {len(epochs)} epochs identified")

    print("\n2. Analyzing tag emergence...")
    emergence = tag_emergence(problems)
    print(f"   {len(emergence['emerging'])} emerging, {len(emergence['declining'])} declining tags")

    print("\n3. Computing difficulty gradient...")
    gradient = difficulty_gradient(problems)
    print(f"   Trend: {gradient['trend_direction']}")

    print("\n4. Mapping status landscape...")
    landscape = status_landscape(problems)
    print(f"   {len(landscape['dead_zones'])} dead zones, {len(landscape['golden_zones'])} golden zones")

    print("\n5. Analyzing tag succession...")
    succession = tag_succession(problems)
    print(f"   {len(succession['strongest_successors'])} successor relationships")

    print("\n6. Tracking complexity drift...")
    drift = complexity_drift(problems)
    print(f"   Complexity {'increasing' if drift['complexity_increasing'] else 'stable'}")

    print("\n7. Analyzing named problems...")
    named = named_problem_analysis(problems)
    print(f"   {named['named_stats']['count']} named problems")

    print("\nGenerating report...")
    report = generate_report(epochs, emergence, gradient, landscape,
                             succession, drift, named)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"Saved to {REPORT_PATH}")

    print("\n" + "=" * 70)
    print("TEMPORAL EVOLUTION ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
