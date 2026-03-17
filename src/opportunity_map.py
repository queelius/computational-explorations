#!/usr/bin/env python3
"""
opportunity_map.py — Exploratory opportunity scoring for Erdős open problems.

NOTE: This is an EXPLORATORY scoring system, not a predictive model. The
composite scores have not been validated against out-of-sample outcomes
(e.g., which problems actually got solved after scoring). The weights are
hand-chosen heuristics, not learned from data. High-scoring problems are
plausible research targets, but the scores should not be interpreted as
calibrated probabilities of resolution.

Combines multiple analysis signals into a composite ranking of research
opportunities. Each open problem receives a heuristic score reflecting
metadata-derived features along several dimensions.

Signal sources:
  - Vulnerability score (from synthesis.py) -- tag/OEIS-based heuristic
  - Cascade potential -- OEIS co-occurrence count, not causal cascades
  - Near-miss status (from attack_surface.py)
  - OEIS bridge ratio (fraction of shared sequences with solved problems)
  - Tag solvability (average solve rate of the problem's tags)
  - Tag pair effectiveness (best pairwise tag solve rate)
  - Prize signal (log-scaled prize amount)
  - OEIS count and formalization status

Output: docs/opportunity_map_report.md
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
REPORT_PATH = ROOT / "docs" / "opportunity_map_report.md"


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
# Signal Collection — Gather All Signals Per Problem
# ═══════════════════════════════════════════════════════════════════

def collect_signals(problems: List[Dict]) -> List[Dict[str, Any]]:
    """
    Collect all available signals for each open problem from multiple modules.

    Each signal is normalized to [0, 1] where higher = better opportunity.
    """
    open_problems = [p for p in problems if _is_open(p)]
    if not open_problems:
        return []

    prob_by_num = {_number(p): p for p in problems}

    # ── Signal 1: Vulnerability (from synthesis) ─────────────
    from synthesis import compute_vulnerability_scores
    vuln_scores = compute_vulnerability_scores(problems)
    vuln_by_num = {}
    for v in vuln_scores:
        vuln_by_num[v["number"]] = v
        if isinstance(v["number"], str) and v["number"].isdigit():
            vuln_by_num[int(v["number"])] = v
        vuln_by_num[str(v["number"])] = v

    # ── Signal 2: Tag solve rates ─────────────────────────────
    tag_solved = Counter()
    tag_total = Counter()
    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _is_solved(p):
                tag_solved[t] += 1
    tag_solve_rate = {t: tag_solved[t] / tag_total[t] if tag_total[t] > 0 else 0.0
                      for t in tag_total}

    # ── Signal 3: OEIS bridges to solved problems ─────────────
    oeis_to_solved = defaultdict(int)
    oeis_to_total = defaultdict(int)
    for p in problems:
        for seq in _oeis(p):
            if seq and seq != "A000000" and not seq.startswith("A00000"):
                oeis_to_total[seq] += 1
                if _is_solved(p):
                    oeis_to_solved[seq] += 1

    # ── Signal 4: Cascade potential (OEIS chain length) ───────
    oeis_to_problems = defaultdict(list)
    for p in problems:
        for seq in _oeis(p):
            if seq and seq != "A000000" and not seq.startswith("A00000"):
                oeis_to_problems[seq].append(_number(p))

    # ── Signal 5: Technique pair effectiveness ────────────────
    pair_solve_rate = {}
    for p in problems:
        tags = sorted(_tags(p))
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                pair = (tags[i], tags[j])
                if pair not in pair_solve_rate:
                    pair_probs = [q for q in problems
                                  if tags[i] in _tags(q) and tags[j] in _tags(q)]
                    if len(pair_probs) >= 2:
                        solved = sum(1 for q in pair_probs if _is_solved(q))
                        pair_solve_rate[pair] = solved / len(pair_probs)

    # ── Signal 6: Near-miss detection ─────────────────────────
    near_miss_nums = set()
    for p in problems:
        status = _status(p)
        if status in ("falsifiable", "verifiable", "decidable"):
            near_miss_nums.add(_number(p))

    # ── Aggregate per-problem signals ─────────────────────────
    results = []
    for p in open_problems:
        num = _number(p)
        tags = _tags(p)
        prize = _prize(p)

        # Vulnerability
        v_info = vuln_by_num.get(num) or vuln_by_num.get(str(num), {})
        vulnerability = v_info.get("vulnerability", 0.0)

        # Tag solvability (average)
        rates = [tag_solve_rate.get(t, 0.0) for t in tags]
        avg_tag_rate = sum(rates) / len(rates) if rates else 0.0
        max_tag_rate = max(rates) if rates else 0.0

        # OEIS bridge strength
        real_oeis = [s for s in _oeis(p) if s and s != "A000000" and not s.startswith("A00000")]
        oeis_bridge_ratio = 0.0
        if real_oeis:
            bridge_scores = [oeis_to_solved.get(s, 0) / max(oeis_to_total.get(s, 1), 1)
                             for s in real_oeis]
            oeis_bridge_ratio = max(bridge_scores) if bridge_scores else 0.0

        # Cascade potential
        cascade_count = 0
        for seq in real_oeis:
            connected = [n for n in oeis_to_problems.get(seq, []) if n != num]
            open_connected = [n for n in connected if prob_by_num.get(n) and _is_open(prob_by_num[n])]
            cascade_count += len(open_connected)

        # Best technique pair
        best_pair_rate = 0.0
        sorted_tags = sorted(tags)
        for i in range(len(sorted_tags)):
            for j in range(i + 1, len(sorted_tags)):
                pair = (sorted_tags[i], sorted_tags[j])
                rate = pair_solve_rate.get(pair, 0.0)
                best_pair_rate = max(best_pair_rate, rate)

        # Near-miss bonus
        is_near_miss = num in near_miss_nums

        # Prize attractiveness (log-scaled, normalized)
        prize_signal = math.log1p(prize) / math.log1p(10000) if prize > 0 else 0.0

        results.append({
            "number": num,
            "tags": sorted(tags),
            "prize": prize,
            "formalized": _is_formalized(p),
            "signals": {
                "vulnerability": vulnerability,
                "avg_tag_solve_rate": avg_tag_rate,
                "max_tag_solve_rate": max_tag_rate,
                "oeis_bridge_ratio": oeis_bridge_ratio,
                "cascade_potential": min(cascade_count / 50.0, 1.0),
                "best_pair_rate": best_pair_rate,
                "near_miss": 1.0 if is_near_miss else 0.0,
                "prize_signal": prize_signal,
                "oeis_count": min(len(real_oeis) / 5.0, 1.0),
                "not_formalized": 0.0 if _is_formalized(p) else 1.0,
            },
        })

    return results


# ═══════════════════════════════════════════════════════════════════
# Composite Scoring
# ═══════════════════════════════════════════════════════════════════

def compute_opportunity_scores(problems: List[Dict],
                               weights: Optional[Dict[str, float]] = None) -> List[Dict]:
    """
    Compute composite opportunity scores for all open problems.

    NOTE: These are heuristic scores with hand-chosen weights, not
    validated predictions. The weights have not been optimized against
    actual resolution outcomes. "Vulnerability" (weight 0.25) is itself
    a composite of tag/OEIS signals, so this score double-counts some
    of the same underlying data as other signals (tag_solve_rate,
    oeis_bridge_ratio).

    Default weights:
    - vulnerability: 0.25
    - avg_tag_solve_rate: 0.15
    - oeis_bridge_ratio: 0.12
    - best_pair_rate: 0.10
    - cascade_potential: 0.10
    - prize_signal: 0.08
    - near_miss: 0.08
    - max_tag_solve_rate: 0.05
    - not_formalized: 0.04
    - oeis_count: 0.03

    Returns sorted list (highest score first).
    """
    if weights is None:
        weights = {
            "vulnerability": 0.25,
            "avg_tag_solve_rate": 0.15,
            "oeis_bridge_ratio": 0.12,
            "best_pair_rate": 0.10,
            "cascade_potential": 0.10,
            "prize_signal": 0.08,
            "near_miss": 0.08,
            "max_tag_solve_rate": 0.05,
            "not_formalized": 0.04,
            "oeis_count": 0.03,
        }

    signals = collect_signals(problems)

    for item in signals:
        score = 0.0
        for signal_name, weight in weights.items():
            val = item["signals"].get(signal_name, 0.0)
            score += weight * val
        item["opportunity_score"] = score

    signals.sort(key=lambda x: -x["opportunity_score"])
    return signals


# ═══════════════════════════════════════════════════════════════════
# Opportunity Tiers
# ═══════════════════════════════════════════════════════════════════

def opportunity_tiers(scored: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Classify scored problems into tiers based on opportunity score distribution.

    Returns dict with:
    - platinum: top 5% (exceptional opportunities)
    - gold: top 15%
    - silver: top 30%
    - bronze: rest
    """
    n = len(scored)
    if n == 0:
        return {"platinum": [], "gold": [], "silver": [], "bronze": []}

    p5 = int(n * 0.05) or 1
    p15 = int(n * 0.15) or 1
    p30 = int(n * 0.30) or 1

    return {
        "platinum": scored[:p5],
        "gold": scored[p5:p15],
        "silver": scored[p15:p30],
        "bronze": scored[p30:],
    }


# ═══════════════════════════════════════════════════════════════════
# Tag Opportunity Analysis
# ═══════════════════════════════════════════════════════════════════

def tag_opportunities(scored: List[Dict]) -> List[Dict]:
    """
    Aggregate opportunity scores by tag to find the most promising research areas.

    Returns list of tags sorted by average opportunity score of their open problems.
    """
    tag_scores = defaultdict(list)
    tag_prizes = defaultdict(float)

    for item in scored:
        for t in item["tags"]:
            tag_scores[t].append(item["opportunity_score"])
            tag_prizes[t] += item["prize"]

    results = []
    for tag, scores in tag_scores.items():
        if len(scores) < 3:  # skip rare tags
            continue
        results.append({
            "tag": tag,
            "avg_opportunity": sum(scores) / len(scores),
            "max_opportunity": max(scores),
            "open_count": len(scores),
            "total_prize": tag_prizes[tag],
            "top_problem": None,
        })

    results.sort(key=lambda x: -x["avg_opportunity"])

    # Add top problem for each tag
    for r in results:
        for item in scored:
            if r["tag"] in item["tags"]:
                r["top_problem"] = item["number"]
                break

    return results


# ═══════════════════════════════════════════════════════════════════
# Signal Contribution Analysis
# ═══════════════════════════════════════════════════════════════════

def signal_contributions(scored: List[Dict]) -> Dict[str, Any]:
    """
    Analyze how much each signal contributes to the final rankings.

    Returns dict with:
    - signal_stats: mean, std, correlation with final score for each signal
    - dominant_signals: for each tier, which signals drive the ranking
    """
    if not scored:
        return {"signal_stats": [], "dominant_signals": {}}

    signal_names = list(scored[0]["signals"].keys())
    n = len(scored)
    final_scores = np.array([s["opportunity_score"] for s in scored])

    stats = []
    for sig_name in signal_names:
        vals = np.array([s["signals"][sig_name] for s in scored])
        mean_val = float(vals.mean())
        std_val = float(vals.std())

        # Correlation with final score
        if std_val > 0 and np.std(final_scores) > 0:
            corr = float(np.corrcoef(vals, final_scores)[0, 1])
        else:
            corr = 0.0

        stats.append({
            "signal": sig_name,
            "mean": mean_val,
            "std": std_val,
            "correlation": corr,
        })

    stats.sort(key=lambda x: abs(x["correlation"]), reverse=True)

    # Dominant signals in top tier
    tiers = opportunity_tiers(scored)
    dominant = {}
    for tier_name, tier_items in tiers.items():
        if not tier_items:
            continue
        tier_means = {}
        for sig_name in signal_names:
            tier_vals = [s["signals"][sig_name] for s in tier_items]
            all_vals = [s["signals"][sig_name] for s in scored]
            tier_mean = sum(tier_vals) / len(tier_vals) if tier_vals else 0
            all_mean = sum(all_vals) / len(all_vals) if all_vals else 0
            tier_means[sig_name] = tier_mean - all_mean  # enrichment
        # Sort by enrichment
        top_signals = sorted(tier_means.items(), key=lambda x: -x[1])[:3]
        dominant[tier_name] = top_signals

    return {"signal_stats": stats, "dominant_signals": dominant}


# ═══════════════════════════════════════════════════════════════════
# Prize-Weighted Opportunity
# ═══════════════════════════════════════════════════════════════════

def prize_weighted_ranking(scored: List[Dict]) -> List[Dict]:
    """
    Rank problems by expected prize value: prize × opportunity_score.
    Only includes problems with prizes.

    Returns sorted list with prize_ev field.
    """
    results = []
    for item in scored:
        if item["prize"] > 0:
            ev = item["prize"] * item["opportunity_score"]
            results.append({
                "number": item["number"],
                "tags": item["tags"],
                "prize": item["prize"],
                "opportunity_score": item["opportunity_score"],
                "prize_ev": ev,
            })

    results.sort(key=lambda x: -x["prize_ev"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Research Portfolio Optimization
# ═══════════════════════════════════════════════════════════════════

def research_portfolio(scored: List[Dict], budget: int = 10) -> Dict[str, Any]:
    """
    Select an optimal research portfolio that maximizes total opportunity
    while maintaining topic diversity.

    Uses greedy selection with tag-diversity penalty.

    Returns dict with:
    - portfolio: selected problems
    - total_score: sum of opportunity scores
    - topic_coverage: set of tags covered
    - total_prize: potential prize money
    """
    available = list(scored)
    portfolio = []
    covered_tags = set()

    for _ in range(budget):
        if not available:
            break

        # Score each candidate with diversity bonus
        best = None
        best_score = -float("inf")
        for item in available:
            base = item["opportunity_score"]
            # Diversity bonus: new tags are worth more
            new_tags = set(item["tags"]) - covered_tags
            diversity_bonus = 0.1 * len(new_tags) / max(len(item["tags"]), 1)
            adjusted = base + diversity_bonus
            if adjusted > best_score:
                best_score = adjusted
                best = item

        if best:
            portfolio.append(best)
            covered_tags.update(best["tags"])
            available.remove(best)

    total_score = sum(p["opportunity_score"] for p in portfolio)
    total_prize = sum(p["prize"] for p in portfolio)

    return {
        "portfolio": portfolio,
        "total_score": total_score,
        "topic_coverage": sorted(covered_tags),
        "n_topics": len(covered_tags),
        "total_prize": total_prize,
    }


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    scored = compute_opportunity_scores(problems)
    tiers = opportunity_tiers(scored)
    tag_opps = tag_opportunities(scored)
    sig_contrib = signal_contributions(scored)
    prize_rank = prize_weighted_ranking(scored)
    portfolio = research_portfolio(scored)

    lines = ["# Unified Opportunity Map", ""]
    lines.append("Combining all analysis signals into a single actionable ranking")
    lines.append(f"of {len(scored)} open Erdős problems.")
    lines.append("")

    # Section 1: Top Opportunities
    lines.append("## 1. Top 20 Research Opportunities")
    lines.append("")
    lines.append("| Rank | Problem | Score | Tags | Prize | Key Signal |")
    lines.append("|------|---------|-------|------|-------|-----------|")
    for i, item in enumerate(scored[:20]):
        tags_str = ", ".join(item["tags"][:3])
        prize_str = f"${item['prize']:.0f}" if item["prize"] > 0 else "-"
        # Find dominant signal
        sigs = item["signals"]
        best_sig = max(sigs.items(), key=lambda x: x[1])
        lines.append(f"| {i + 1} | #{item['number']} | {item['opportunity_score']:.3f} | "
                      f"{tags_str} | {prize_str} | {best_sig[0]}={best_sig[1]:.2f} |")
    lines.append("")

    # Section 2: Tier Distribution
    lines.append("## 2. Opportunity Tiers")
    lines.append("")
    for tier_name in ["platinum", "gold", "silver", "bronze"]:
        tier = tiers[tier_name]
        if not tier:
            continue
        avg_score = sum(t["opportunity_score"] for t in tier) / len(tier)
        total_prize = sum(t["prize"] for t in tier)
        lines.append(f"### {tier_name.title()} ({len(tier)} problems)")
        lines.append(f"- Average score: {avg_score:.3f}")
        lines.append(f"- Total prize money: ${total_prize:,.0f}")
        if tier_name in ("platinum", "gold"):
            nums = [f"#{t['number']}" for t in tier[:10]]
            lines.append(f"- Problems: {', '.join(nums)}")
        lines.append("")

    # Section 3: Tag Opportunities
    lines.append("## 3. Most Promising Research Areas (by Tag)")
    lines.append("")
    lines.append("| Tag | Avg Score | Open Problems | Total Prize | Top Problem |")
    lines.append("|-----|-----------|---------------|-------------|-------------|")
    for t in tag_opps[:15]:
        top = f"#{t['top_problem']}" if t['top_problem'] else "-"
        lines.append(f"| {t['tag']} | {t['avg_opportunity']:.3f} | "
                      f"{t['open_count']} | ${t['total_prize']:,.0f} | {top} |")
    lines.append("")

    # Section 4: Signal Analysis
    lines.append("## 4. Signal Contribution Analysis")
    lines.append("")
    lines.append("| Signal | Mean | Std | Correlation |")
    lines.append("|--------|------|-----|-------------|")
    for s in sig_contrib["signal_stats"]:
        lines.append(f"| {s['signal']} | {s['mean']:.3f} | {s['std']:.3f} | "
                      f"{s['correlation']:+.3f} |")
    lines.append("")

    if sig_contrib["dominant_signals"]:
        lines.append("### Dominant Signals by Tier")
        lines.append("")
        for tier_name, sigs in sig_contrib["dominant_signals"].items():
            sig_str = ", ".join(f"{s[0]} (+{s[1]:.3f})" for s in sigs)
            lines.append(f"- **{tier_name.title()}**: {sig_str}")
        lines.append("")

    # Section 5: Prize-Weighted Ranking
    lines.append("## 5. Prize-Weighted Opportunities")
    lines.append("")
    lines.append("| Problem | Prize | Score | Expected Value | Tags |")
    lines.append("|---------|-------|-------|---------------|------|")
    for p in prize_rank[:15]:
        tags_str = ", ".join(p["tags"][:3])
        lines.append(f"| #{p['number']} | ${p['prize']:,.0f} | "
                      f"{p['opportunity_score']:.3f} | ${p['prize_ev']:,.0f} | {tags_str} |")
    lines.append("")

    # Section 6: Optimal Research Portfolio
    lines.append("## 6. Optimal Research Portfolio (10 problems)")
    lines.append("")
    lines.append(f"Total opportunity score: {portfolio['total_score']:.3f}")
    lines.append(f"Topic coverage: {portfolio['n_topics']} tags")
    lines.append(f"Total prize potential: ${portfolio['total_prize']:,.0f}")
    lines.append("")
    lines.append("| # | Problem | Score | Tags | Prize |")
    lines.append("|---|---------|-------|------|-------|")
    for i, p in enumerate(portfolio["portfolio"]):
        tags_str = ", ".join(p["tags"][:3])
        prize_str = f"${p['prize']:.0f}" if p["prize"] > 0 else "-"
        lines.append(f"| {i + 1} | #{p['number']} | {p['opportunity_score']:.3f} | "
                      f"{tags_str} | {prize_str} |")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    problems = load_problems()
    report = generate_report(problems)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")
    print(f"Scored {sum(1 for p in problems if _is_open(p))} open problems")
