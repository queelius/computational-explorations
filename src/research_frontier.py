#!/usr/bin/env python3
"""
research_frontier.py — Research frontier detection and momentum analysis.

NOTE: Problem numbers are catalogue IDs, not chronological ordering. "Momentum"
and "frontier" scores based on problem number ordering are approximate proxies.
The database lacks true timestamps for when problems were posed or solved, so
all temporal analyses here use problem number as a rough structural proxy.
Results should be interpreted as "patterns across the catalogue" rather than
true temporal trends.

Identifies which mathematical areas appear more or less active based on
structural proxies in the problem catalogue:
  - Problem number window as a rough ordering proxy (NOT chronological)
  - Solution density gradient (solve rate in consecutive number windows)
  - Tag co-solution patterns (tags that co-occur in solved problems)
  - Formalization rate (which areas are attracting formalization)
  - Solve rate anomaly detection (tags with unusually high/low rates)

Analyses:
  1. Tag Momentum: solve rate gradient across problem number windows (not time)
  2. Solution Clusters: runs of consecutive solved problems by tag
  3. Solve Rate Anomalies: tags with z-scores above/below global average
  4. Stagnation Runs: tags with long consecutive unsolved stretches
  5. Emerging Connections: tag pairs more common in later-numbered problems
  6. Frontier Scoring: composite score per tag (exploratory, not predictive)

Output: docs/research_frontier_report.md
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
REPORT_PATH = ROOT / "docs" / "research_frontier_report.md"


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


def _is_formalized(p: Dict) -> bool:
    return p.get("formalized", {}).get("state", "no") == "yes"


# ═══════════════════════════════════════════════════════════════════
# Tag Momentum — Rolling Solve Rate Gradient
# ═══════════════════════════════════════════════════════════════════

def tag_momentum(problems: List[Dict], window: int = 200) -> List[Dict[str, Any]]:
    """
    Compute momentum for each tag: how the solve rate changes across
    problem number windows.

    NOTE: Problem numbers are catalogue IDs, not chronological. "Momentum"
    here means the slope of solve rate across catalogue windows, which is
    an imperfect proxy for temporal trends.

    Positive momentum = higher solve rate in later-numbered windows.
    Negative momentum = lower solve rate in later-numbered windows.

    Returns sorted list (highest momentum first).
    """
    by_number = sorted(problems, key=_number)
    n = len(by_number)

    # Collect per-window tag statistics
    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    tag_windows = {t: [] for t in all_tags}

    for start in range(0, n, window):
        chunk = by_number[start:start + window]
        for tag in all_tags:
            tag_probs = [p for p in chunk if tag in _tags(p)]
            if tag_probs:
                solved = sum(1 for p in tag_probs if _is_solved(p))
                rate = solved / len(tag_probs)
            else:
                rate = None
            tag_windows[tag].append({
                "start": _number(chunk[0]) if chunk else 0,
                "end": _number(chunk[-1]) if chunk else 0,
                "rate": rate,
                "count": len(tag_probs),
            })

    results = []
    for tag in all_tags:
        windows = tag_windows[tag]
        rates = [(i, w["rate"]) for i, w in enumerate(windows) if w["rate"] is not None]
        if len(rates) < 2:
            continue

        # Linear regression on (window_index, solve_rate)
        xs = np.array([r[0] for r in rates])
        ys = np.array([r[1] for r in rates])
        if np.std(xs) == 0 or np.std(ys) == 0:
            slope = 0.0
        else:
            corr = np.corrcoef(xs, ys)[0, 1]
            slope = float(corr * np.std(ys) / np.std(xs)) if not np.isnan(corr) else 0.0

        # Early vs late comparison
        mid = len(rates) // 2
        early_rates = [r[1] for r in rates[:mid]]
        late_rates = [r[1] for r in rates[mid:]]
        early_avg = sum(early_rates) / len(early_rates) if early_rates else 0
        late_avg = sum(late_rates) / len(late_rates) if late_rates else 0

        total_count = sum(w["count"] for w in windows)

        results.append({
            "tag": tag,
            "momentum": slope,
            "early_solve_rate": early_avg,
            "late_solve_rate": late_avg,
            "shift": late_avg - early_avg,
            "total_problems": total_count,
            "n_windows": len(rates),
            "window_rates": [(w["start"], w["rate"]) for w in windows if w["rate"] is not None],
        })

    results.sort(key=lambda x: x["momentum"], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════
# Research Waves — Solution Clustering by Tag
# ═══════════════════════════════════════════════════════════════════

def research_waves(problems: List[Dict]) -> List[Dict[str, Any]]:
    """
    Detect "research waves": clusters of consecutive solved problems
    within the same tag. These suggest technique breakthroughs.

    Returns list of waves sorted by length (longest first).
    """
    by_number = sorted(problems, key=_number)

    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    waves = []

    for tag in all_tags:
        tag_probs = [p for p in by_number if tag in _tags(p)]
        if len(tag_probs) < 3:
            continue

        # Find consecutive solved runs
        current_run = []
        for p in tag_probs:
            if _is_solved(p):
                current_run.append(_number(p))
            else:
                if len(current_run) >= 2:
                    waves.append({
                        "tag": tag,
                        "wave_length": len(current_run),
                        "problems": current_run,
                        "start": current_run[0],
                        "end": current_run[-1],
                        "span": current_run[-1] - current_run[0],
                    })
                current_run = []

        # Handle final run
        if len(current_run) >= 2:
            waves.append({
                "tag": tag,
                "wave_length": len(current_run),
                "problems": current_run,
                "start": current_run[0],
                "end": current_run[-1],
                "span": current_run[-1] - current_run[0],
            })

    waves.sort(key=lambda x: -x["wave_length"])
    return waves


# ═══════════════════════════════════════════════════════════════════
# Breakthrough Detection — Anomalous Solve Rates
# ═══════════════════════════════════════════════════════════════════

def breakthrough_detection(problems: List[Dict]) -> List[Dict[str, Any]]:
    """
    Detect tags where solve rate significantly exceeds the global average,
    suggesting a technique breakthrough in that area.

    Uses z-score of tag solve rate vs global baseline.
    """
    global_solved = sum(1 for p in problems if _is_solved(p))
    global_rate = global_solved / len(problems) if problems else 0

    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    results = []

    for tag in all_tags:
        tag_probs = [p for p in problems if tag in _tags(p)]
        if len(tag_probs) < 5:
            continue

        solved = sum(1 for p in tag_probs if _is_solved(p))
        rate = solved / len(tag_probs)

        # Binomial z-test vs global rate
        n = len(tag_probs)
        expected = global_rate
        std_err = math.sqrt(expected * (1 - expected) / n) if expected > 0 and expected < 1 else 0.01
        z_score = (rate - expected) / std_err if std_err > 0 else 0

        # Also check formalization rate as "attention" proxy
        formalized = sum(1 for p in tag_probs if _is_formalized(p))
        formal_rate = formalized / len(tag_probs)

        results.append({
            "tag": tag,
            "solve_rate": rate,
            "global_rate": global_rate,
            "z_score": z_score,
            "n_problems": len(tag_probs),
            "n_solved": solved,
            "formalization_rate": formal_rate,
            "breakthrough": z_score > 2.0,
            "stagnant": z_score < -2.0,
        })

    results.sort(key=lambda x: x["z_score"], reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════
# Stagnation Analysis — Long Unsolved Runs
# ═══════════════════════════════════════════════════════════════════

def stagnation_analysis(problems: List[Dict]) -> List[Dict[str, Any]]:
    """
    Identify tags with the longest continuous runs of unsolved problems.
    These represent areas where existing techniques have failed.

    Returns list sorted by longest stagnation run.
    """
    by_number = sorted(problems, key=_number)
    all_tags = sorted(set(t for p in problems for t in _tags(p)))

    results = []
    for tag in all_tags:
        tag_probs = [p for p in by_number if tag in _tags(p)]
        if len(tag_probs) < 5:
            continue

        # Find longest consecutive open run
        max_run = 0
        current_run = 0
        current_start = 0
        best_start = 0
        best_end = 0

        for i, p in enumerate(tag_probs):
            if _is_open(p):
                if current_run == 0:
                    current_start = _number(p)
                current_run += 1
                if current_run > max_run:
                    max_run = current_run
                    best_start = current_start
                    best_end = _number(p)
            else:
                current_run = 0

        total_open = sum(1 for p in tag_probs if _is_open(p))
        total = len(tag_probs)

        results.append({
            "tag": tag,
            "longest_stagnation": max_run,
            "stagnation_start": best_start,
            "stagnation_end": best_end,
            "open_fraction": total_open / total if total > 0 else 0,
            "total_problems": total,
        })

    results.sort(key=lambda x: -x["longest_stagnation"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Emerging Connections — New Tag Pairs
# ═══════════════════════════════════════════════════════════════════

def emerging_connections(problems: List[Dict]) -> List[Dict[str, Any]]:
    """
    Find tag pairs that appear more frequently in later problems,
    suggesting emerging research directions.
    """
    by_number = sorted(problems, key=_number)
    n = len(by_number)
    mid = n // 2
    early = by_number[:mid]
    late = by_number[mid:]

    # Count tag pairs in each half
    def count_pairs(probs):
        pairs = Counter()
        for p in probs:
            tags = sorted(_tags(p))
            for i in range(len(tags)):
                for j in range(i + 1, len(tags)):
                    pairs[(tags[i], tags[j])] += 1
        return pairs

    early_pairs = count_pairs(early)
    late_pairs = count_pairs(late)

    # Find pairs that are more common in late problems
    all_pairs = set(early_pairs.keys()) | set(late_pairs.keys())
    results = []

    for pair in all_pairs:
        early_count = early_pairs.get(pair, 0)
        late_count = late_pairs.get(pair, 0)
        total = early_count + late_count

        if total < 3:
            continue

        # Emergence ratio: late / early (higher = more emerging)
        emergence = late_count / max(early_count, 0.5)

        # Also track solve rates
        pair_probs_late = [p for p in late if pair[0] in _tags(p) and pair[1] in _tags(p)]
        late_solved = sum(1 for p in pair_probs_late if _is_solved(p))
        late_rate = late_solved / len(pair_probs_late) if pair_probs_late else 0

        results.append({
            "tag_a": pair[0],
            "tag_b": pair[1],
            "early_count": early_count,
            "late_count": late_count,
            "emergence_ratio": emergence,
            "late_solve_rate": late_rate,
        })

    results.sort(key=lambda x: -x["emergence_ratio"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Frontier Scoring — Composite Research Attractiveness
# ═══════════════════════════════════════════════════════════════════

def frontier_scores(problems: List[Dict]) -> List[Dict[str, Any]]:
    """
    Compute a composite "frontier score" for each tag combining:
    - Momentum (solve rate trend)
    - Breakthrough signal (z-score above global)
    - Stagnation penalty (long unsolved runs)
    - Prize attractiveness (total prize money in tag)
    - Open problem count (more problems = more opportunity)

    Returns sorted list (best frontier first).
    """
    momentum = tag_momentum(problems)
    breakthroughs = breakthrough_detection(problems)
    stagnation = stagnation_analysis(problems)

    # Build lookups
    mom_by_tag = {m["tag"]: m for m in momentum}
    bt_by_tag = {b["tag"]: b for b in breakthroughs}
    stag_by_tag = {s["tag"]: s for s in stagnation}

    # Prize by tag
    tag_prizes = defaultdict(float)
    tag_open = Counter()
    for p in problems:
        if _is_open(p):
            for t in _tags(p):
                tag_prizes[t] += _prize(p)
                tag_open[t] += 1

    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    results = []

    for tag in all_tags:
        m = mom_by_tag.get(tag, {})
        b = bt_by_tag.get(tag, {})
        s = stag_by_tag.get(tag, {})

        if not b:
            continue

        # Normalize components to [0, 1]
        momentum_signal = max(min(m.get("momentum", 0) * 10 + 0.5, 1.0), 0.0)
        z = b.get("z_score", 0)
        breakthrough_signal = max(min((z + 3) / 6, 1.0), 0.0)  # z∈[-3,3] → [0,1]
        stag_penalty = min(s.get("longest_stagnation", 0) / 20.0, 1.0)
        prize_signal = min(math.log1p(tag_prizes.get(tag, 0)) / math.log1p(5000), 1.0)
        open_signal = min(tag_open.get(tag, 0) / 50.0, 1.0)

        # Composite score (weighted)
        score = (0.25 * momentum_signal +
                 0.25 * breakthrough_signal +
                 0.20 * (1.0 - stag_penalty) +  # lower stagnation = better
                 0.15 * prize_signal +
                 0.15 * open_signal)

        results.append({
            "tag": tag,
            "frontier_score": score,
            "momentum": m.get("momentum", 0),
            "z_score": b.get("z_score", 0),
            "solve_rate": b.get("solve_rate", 0),
            "longest_stagnation": s.get("longest_stagnation", 0),
            "prize_total": tag_prizes.get(tag, 0),
            "open_count": tag_open.get(tag, 0),
            "breakthrough": b.get("breakthrough", False),
            "stagnant": b.get("stagnant", False),
        })

    results.sort(key=lambda x: -x["frontier_score"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    mom = tag_momentum(problems)
    waves = research_waves(problems)
    breakthroughs = breakthrough_detection(problems)
    stag = stagnation_analysis(problems)
    emerging = emerging_connections(problems)
    frontier = frontier_scores(problems)

    lines = ["# Research Frontier Analysis", ""]

    # Section 1: Tag Momentum
    lines.append("## 1. Tag Momentum (Rising vs Declining)")
    lines.append("")
    lines.append("### Rising Tags (Positive Momentum)")
    lines.append("")
    lines.append("| Tag | Momentum | Early Rate | Late Rate | Shift | Problems |")
    lines.append("|-----|----------|-----------|----------|-------|----------|")
    for m in mom[:10]:
        if m["momentum"] > 0:
            lines.append(f"| {m['tag']} | {m['momentum']:+.4f} | "
                          f"{m['early_solve_rate']:.1%} | {m['late_solve_rate']:.1%} | "
                          f"{m['shift']:+.1%} | {m['total_problems']} |")
    lines.append("")

    lines.append("### Declining Tags (Negative Momentum)")
    lines.append("")
    lines.append("| Tag | Momentum | Early Rate | Late Rate | Shift | Problems |")
    lines.append("|-----|----------|-----------|----------|-------|----------|")
    for m in reversed(mom[-10:]):
        if m["momentum"] < 0:
            lines.append(f"| {m['tag']} | {m['momentum']:+.4f} | "
                          f"{m['early_solve_rate']:.1%} | {m['late_solve_rate']:.1%} | "
                          f"{m['shift']:+.1%} | {m['total_problems']} |")
    lines.append("")

    # Section 2: Research Waves
    lines.append("## 2. Research Waves (Solution Clusters)")
    lines.append("")
    lines.append("| Tag | Wave Length | Problem Range | Span |")
    lines.append("|-----|-----------|---------------|------|")
    for w in waves[:15]:
        problems_str = f"#{w['start']}–#{w['end']}"
        lines.append(f"| {w['tag']} | {w['wave_length']} | {problems_str} | {w['span']} |")
    lines.append("")

    # Section 3: Breakthroughs
    lines.append("## 3. Breakthrough Detection")
    lines.append("")
    bt_list = [b for b in breakthroughs if b["breakthrough"]]
    stag_list = [b for b in breakthroughs if b["stagnant"]]

    lines.append(f"**Breakthrough tags** (z > 2.0): {len(bt_list)}")
    lines.append(f"**Stagnant tags** (z < -2.0): {len(stag_list)}")
    lines.append("")

    if bt_list:
        lines.append("### Breakthrough Areas")
        lines.append("")
        lines.append("| Tag | Solve Rate | Z-Score | Problems |")
        lines.append("|-----|-----------|---------|----------|")
        for b in bt_list[:10]:
            lines.append(f"| {b['tag']} | {b['solve_rate']:.1%} | {b['z_score']:+.2f} | {b['n_problems']} |")
        lines.append("")

    if stag_list:
        lines.append("### Stagnant Areas")
        lines.append("")
        lines.append("| Tag | Solve Rate | Z-Score | Problems |")
        lines.append("|-----|-----------|---------|----------|")
        for b in stag_list[:10]:
            lines.append(f"| {b['tag']} | {b['solve_rate']:.1%} | {b['z_score']:+.2f} | {b['n_problems']} |")
        lines.append("")

    # Section 4: Stagnation
    lines.append("## 4. Longest Stagnation Runs")
    lines.append("")
    lines.append("| Tag | Run Length | Range | Open % | Total |")
    lines.append("|-----|-----------|-------|--------|-------|")
    for s in stag[:10]:
        lines.append(f"| {s['tag']} | {s['longest_stagnation']} | "
                      f"#{s['stagnation_start']}–#{s['stagnation_end']} | "
                      f"{s['open_fraction']:.1%} | {s['total_problems']} |")
    lines.append("")

    # Section 5: Emerging Connections
    lines.append("## 5. Emerging Tag Connections")
    lines.append("")
    lines.append("| Tag A | Tag B | Early | Late | Emergence | Late Solve Rate |")
    lines.append("|-------|-------|-------|------|-----------|----------------|")
    for e in emerging[:15]:
        lines.append(f"| {e['tag_a']} | {e['tag_b']} | {e['early_count']} | "
                      f"{e['late_count']} | {e['emergence_ratio']:.1f}× | "
                      f"{e['late_solve_rate']:.1%} |")
    lines.append("")

    # Section 6: Frontier Scores
    lines.append("## 6. Research Frontier Scores (Composite)")
    lines.append("")
    lines.append("| Tag | Score | Momentum | Z-Score | Stagnation | Prize | Open |")
    lines.append("|-----|-------|---------|---------|-----------|-------|------|")
    for f in frontier[:20]:
        prize_str = f"${f['prize_total']:,.0f}" if f["prize_total"] > 0 else "-"
        lines.append(f"| {f['tag']} | {f['frontier_score']:.3f} | "
                      f"{f['momentum']:+.4f} | {f['z_score']:+.2f} | "
                      f"{f['longest_stagnation']} | {prize_str} | {f['open_count']} |")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    problems = load_problems()
    report = generate_report(problems)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")
