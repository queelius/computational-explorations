#!/usr/bin/env python3
"""
cross_analysis.py — Third-order synthesis across all analysis modules.

Combines insights from:
  - synthesis.py         (vulnerability scores, cascade, technique effectiveness)
  - meta_patterns.py     (tag synergy, anomalies, DNA profiles)
  - predictive_model.py  (logistic regression predictions)
  - spectral_analysis.py (PageRank, bridge problems, communities)

Produces THIRD-ORDER discoveries:
  1. Unified Opportunity Score (multi-model consensus)
  2. Ranking Disagreements (where models disagree = interesting problems)
  3. Strategic Roadmap (optimal attack sequence)
  4. Problem Genome (comprehensive per-problem analysis)
  5. Hidden Structure Detection (patterns visible only from multiple angles)

Output: docs/cross_analysis_report.md
"""

import math
import yaml
import numpy as np
from collections import defaultdict, Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "cross_analysis_report.md"


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


# ═══════════════════════════════════════════════════════════════════
# 1. Unified Opportunity Score
# ═══════════════════════════════════════════════════════════════════

def unified_opportunity_score(problems: List[Dict]) -> List[Dict]:
    """
    Combine ALL scoring systems into a single unified opportunity score.

    Components:
    - Vulnerability (synthesis.py): structural solvability signal
    - Predicted solvability (predictive_model.py): ML-based signal
    - PageRank influence (spectral_analysis.py): network importance
    - Cascade potential (synthesis.py): downstream impact
    - Prize value: economic incentive

    The unified score is a weighted combination designed to maximize
    expected value of research effort.
    """
    from synthesis import compute_vulnerability_scores, resolution_cascade
    from predictive_model import compute_features, train_logistic_regression, predict_probabilities
    from spectral_analysis import build_problem_graph, pagerank_influence

    # Signal 1: Vulnerability scores
    vuln = compute_vulnerability_scores(problems)
    vuln_by_num = {v["number"]: v["vulnerability"] for v in vuln}

    # Signal 2: Prediction model
    X, y, info, feature_names = compute_features(problems)
    w, b, mean, std = train_logistic_regression(X, y)
    probs = predict_probabilities(X, w, b, mean, std)
    pred_by_num = {}
    for i, inf in enumerate(info):
        if inf["status"] == "open":
            pred_by_num[inf["number"]] = float(probs[i])

    # Signal 3: PageRank
    adj, node_ids, node_info = build_problem_graph(problems)
    pr = pagerank_influence(adj, node_ids, node_info)
    pr_by_num = {r["number"]: r["pagerank"] for r in pr["rankings"]}
    pr_max = max(pr_by_num.values()) if pr_by_num else 1.0

    # Signal 4: Cascade potential
    cascade = resolution_cascade(problems)
    cascade_by_num = {c["number"]: c["total_cascade"] for c in cascade}
    cascade_max = max(cascade_by_num.values()) if cascade_by_num else 1

    # Combine into unified score
    open_probs = [p for p in problems if _status(p) == "open"]
    results = []

    for p in open_probs:
        num = _number(p)
        prize = _prize(p)

        # Normalize each signal to [0, 1]
        s_vuln = vuln_by_num.get(num, 0.0)
        s_pred = pred_by_num.get(num, 0.3)
        s_pr = pr_by_num.get(num, 0.0) / pr_max if pr_max > 0 else 0
        s_cascade = cascade_by_num.get(num, 0) / cascade_max if cascade_max > 0 else 0
        s_prize = math.log1p(prize) / math.log1p(5000)  # normalize to $5000

        # Unified score: weighted blend
        unified = (
            0.25 * s_vuln +       # structural tractability
            0.25 * s_pred +       # ML prediction
            0.15 * s_pr +         # network importance
            0.20 * s_cascade +    # downstream impact
            0.15 * s_prize        # economic incentive
        )

        results.append({
            "number": num,
            "tags": sorted(_tags(p)),
            "unified_score": round(unified, 4),
            "vulnerability": round(s_vuln, 4),
            "predicted_solvability": round(s_pred, 4),
            "pagerank_norm": round(s_pr, 4),
            "cascade_norm": round(s_cascade, 4),
            "prize": prize,
        })

    results.sort(key=lambda x: -x["unified_score"])
    return results


# ═══════════════════════════════════════════════════════════════════
# 2. Ranking Disagreements
# ═══════════════════════════════════════════════════════════════════

def ranking_disagreements(unified_scores: List[Dict], top_k: int = 50) -> List[Dict]:
    """
    Find problems where different scoring systems disagree.

    High disagreement = the problem has unusual structure that different
    models capture differently. These are the MOST INTERESTING problems
    to investigate further.
    """
    disagreements = []

    for u in unified_scores[:top_k]:
        # Compute variance across normalized signals
        signals = [
            u["vulnerability"],
            u["predicted_solvability"],
            u["pagerank_norm"],
            u["cascade_norm"],
        ]
        mean_signal = np.mean(signals)
        variance = np.var(signals)

        # High variance = high disagreement
        disagreements.append({
            "number": u["number"],
            "tags": u["tags"],
            "unified_score": u["unified_score"],
            "disagreement": round(float(variance), 4),
            "signals": {
                "vulnerability": u["vulnerability"],
                "prediction": u["predicted_solvability"],
                "pagerank": u["pagerank_norm"],
                "cascade": u["cascade_norm"],
            },
            "prize": u["prize"],
        })

    disagreements.sort(key=lambda x: -x["disagreement"])
    return disagreements


# ═══════════════════════════════════════════════════════════════════
# 3. Strategic Roadmap
# ═══════════════════════════════════════════════════════════════════

def strategic_roadmap(unified_scores: List[Dict]) -> Dict[str, Any]:
    """
    Organize problems into a strategic attack sequence.

    Categories:
    - Quick Wins: high solvability, low complexity, any prize
    - Strategic Targets: medium solvability, high cascade/influence
    - Prize Hunts: has prize money, reasonable solvability
    - Moonshots: low solvability but massive cascade or prize
    """
    quick_wins = []
    strategic = []
    prize_hunts = []
    moonshots = []

    for u in unified_scores:
        is_solvable = u["predicted_solvability"] > 0.45
        is_influential = u["cascade_norm"] > 0.5
        has_prize = u["prize"] > 0
        is_high_value = u["unified_score"] > 0.3

        if is_solvable and not has_prize:
            quick_wins.append(u)
        elif is_influential and is_high_value:
            strategic.append(u)
        elif has_prize and u["predicted_solvability"] > 0.3:
            prize_hunts.append(u)
        elif (u["cascade_norm"] > 0.7 or u["prize"] > 500):
            moonshots.append(u)

    # Sort each category
    quick_wins.sort(key=lambda x: -x["predicted_solvability"])
    strategic.sort(key=lambda x: -x["unified_score"])
    prize_hunts.sort(key=lambda x: -x["prize"] * x["predicted_solvability"])
    moonshots.sort(key=lambda x: -x["cascade_norm"])

    return {
        "quick_wins": quick_wins[:15],
        "strategic_targets": strategic[:15],
        "prize_hunts": prize_hunts[:10],
        "moonshots": moonshots[:10],
        "total_classified": len(quick_wins) + len(strategic) + len(prize_hunts) + len(moonshots),
    }


# ═══════════════════════════════════════════════════════════════════
# 4. Problem Genome (comprehensive per-problem analysis)
# ═══════════════════════════════════════════════════════════════════

def problem_genome(problems: List[Dict], target_numbers: List[int] = None) -> List[Dict]:
    """
    Generate a comprehensive "genome" for selected problems.

    Each genome includes ALL signals from ALL modules.
    Default targets: top 10 from unified score.
    """
    from synthesis import compute_vulnerability_scores
    from meta_patterns import tag_coevolution

    if target_numbers is None:
        unified = unified_opportunity_score(problems)
        target_numbers = [u["number"] for u in unified[:10]]

    vuln = compute_vulnerability_scores(problems)
    vuln_by_num = {v["number"]: v for v in vuln}

    coevol = tag_coevolution(problems)
    synergy_map = {}
    for s in coevol.get("strongest_synergies", []):
        synergy_map[s["pair"]] = s["synergy"]

    # Build lookup by both int and string forms of number
    by_number = {}
    for p in problems:
        n = _number(p)
        by_number[n] = p
        by_number[str(n)] = p

    genomes = []
    for num in target_numbers:
        p = by_number.get(num) or by_number.get(str(num))
        if not p:
            continue

        tags = sorted(_tags(p))
        v = vuln_by_num.get(num, {})

        # Compute tag synergies for this problem
        tag_synergies = []
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                pair = tuple(sorted([tags[i], tags[j]]))
                if pair in synergy_map:
                    tag_synergies.append({
                        "pair": pair,
                        "synergy": synergy_map[pair],
                    })

        genomes.append({
            "number": num,
            "tags": tags,
            "prize": _prize(p),
            "vulnerability": v.get("vulnerability", 0),
            "tag_solvability": v.get("tag_solvability", 0),
            "oeis_bridges": v.get("oeis_bridges", 0),
            "technique_match": v.get("technique_match", 0),
            "tag_synergies": tag_synergies,
        })

    return genomes


# ═══════════════════════════════════════════════════════════════════
# 5. Hidden Structure Detection
# ═══════════════════════════════════════════════════════════════════

def hidden_structures(problems: List[Dict]) -> Dict[str, Any]:
    """
    Detect patterns only visible from combining multiple analyses.

    Analyses:
    - "Dark horse" problems: low vulnerability but high prediction score
    - "False positives": high vulnerability but low prediction score
    - "Influence orphans": high PageRank but low solvability
    - "Tag paradoxes": problems whose tags predict solvability but
      whose other features predict difficulty
    """
    unified = unified_opportunity_score(problems)
    unified_by_num = {u["number"]: u for u in unified}

    dark_horses = []
    false_positives = []
    influence_orphans = []

    for u in unified:
        vuln = u["vulnerability"]
        pred = u["predicted_solvability"]
        pr = u["pagerank_norm"]
        cascade = u["cascade_norm"]

        # Dark horse: ML says solvable, but vulnerability says no
        if pred > 0.5 and vuln < 0.3:
            dark_horses.append(u)

        # False positive: vulnerability says yes, ML says no
        if vuln > 0.5 and pred < 0.35:
            false_positives.append(u)

        # Influence orphan: important but not solvable
        if pr > 0.5 and pred < 0.4:
            influence_orphans.append(u)

    dark_horses.sort(key=lambda x: x["predicted_solvability"] - x["vulnerability"], reverse=True)
    false_positives.sort(key=lambda x: x["vulnerability"] - x["predicted_solvability"], reverse=True)
    influence_orphans.sort(key=lambda x: -x["pagerank_norm"])

    # Tag paradoxes: problems with high-solvability tags but overall low score
    from synthesis import _compute_tag_solve_rates
    tag_rates = _compute_tag_solve_rates(problems)

    tag_paradoxes = []
    for u in unified:
        tags = u["tags"]
        tag_rate_avg = np.mean([tag_rates.get(t, 0) for t in tags]) if tags else 0
        if tag_rate_avg > 0.4 and u["unified_score"] < 0.25:
            tag_paradoxes.append({
                **u,
                "avg_tag_rate": round(float(tag_rate_avg), 3),
            })

    tag_paradoxes.sort(key=lambda x: -x["avg_tag_rate"])

    return {
        "dark_horses": dark_horses[:10],
        "false_positives": false_positives[:10],
        "influence_orphans": influence_orphans[:10],
        "tag_paradoxes": tag_paradoxes[:10],
    }


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(unified, disagreements, roadmap, genomes, hidden) -> str:
    lines = []
    lines.append("# Cross-Analysis: Third-Order Synthesis")
    lines.append("")
    lines.append("Combining all analysis modules to discover patterns visible only")
    lines.append("from multiple perspectives simultaneously.")
    lines.append("")

    # 1. Unified Opportunity Score
    lines.append("## 1. Unified Opportunity Score (Top 20)")
    lines.append("")
    lines.append("| Rank | Problem | Unified | Vuln | Predicted | PageRank | Cascade | Prize |")
    lines.append("|------|---------|---------|------|-----------|----------|---------|-------|")
    for i, u in enumerate(unified[:20]):
        prize = f"${u['prize']:.0f}" if u["prize"] > 0 else "-"
        lines.append(
            f"| {i+1} | #{u['number']} | {u['unified_score']:.3f} | "
            f"{u['vulnerability']:.3f} | {u['predicted_solvability']:.3f} | "
            f"{u['pagerank_norm']:.3f} | {u['cascade_norm']:.3f} | {prize} |"
        )
    lines.append("")

    # 2. Ranking Disagreements
    lines.append("## 2. Most Interesting Problems (High Model Disagreement)")
    lines.append("")
    lines.append("Problems where different scoring systems strongly disagree —")
    lines.append("these are the most structurally unusual and worth investigating.")
    lines.append("")
    lines.append("| Problem | Disagreement | Vuln | Pred | PR | Cascade | Tags |")
    lines.append("|---------|-------------|------|------|-----|---------|------|")
    for d in disagreements[:15]:
        tags = ", ".join(d["tags"][:2])
        lines.append(
            f"| #{d['number']} | {d['disagreement']:.4f} | "
            f"{d['signals']['vulnerability']:.3f} | {d['signals']['prediction']:.3f} | "
            f"{d['signals']['pagerank']:.3f} | {d['signals']['cascade']:.3f} | {tags} |"
        )
    lines.append("")

    # 3. Strategic Roadmap
    lines.append("## 3. Strategic Research Roadmap")
    lines.append("")

    lines.append("### Quick Wins (high solvability, low barrier)")
    lines.append("")
    for u in roadmap["quick_wins"][:8]:
        lines.append(f"- **#{u['number']}** (pred={u['predicted_solvability']:.3f}): {', '.join(u['tags'][:3])}")
    lines.append("")

    lines.append("### Strategic Targets (influential + solvable)")
    lines.append("")
    for u in roadmap["strategic_targets"][:8]:
        lines.append(f"- **#{u['number']}** (unified={u['unified_score']:.3f}, cascade={u['cascade_norm']:.3f}): {', '.join(u['tags'][:3])}")
    lines.append("")

    lines.append("### Prize Hunts")
    lines.append("")
    for u in roadmap["prize_hunts"][:8]:
        lines.append(f"- **#{u['number']}** (${u['prize']:.0f}, pred={u['predicted_solvability']:.3f}): {', '.join(u['tags'][:3])}")
    lines.append("")

    lines.append("### Moonshots (high impact, difficult)")
    lines.append("")
    for u in roadmap["moonshots"][:5]:
        prize_str = f"${u['prize']:.0f}" if u["prize"] > 0 else "no prize"
        lines.append(f"- **#{u['number']}** ({prize_str}, cascade={u['cascade_norm']:.3f}): {', '.join(u['tags'][:3])}")
    lines.append("")

    # 4. Problem Genomes
    lines.append("## 4. Problem Genomes (Top 10)")
    lines.append("")
    for g in genomes:
        lines.append(f"### #{g['number']}")
        lines.append(f"- Tags: {', '.join(g['tags'])}")
        if g['prize'] > 0:
            lines.append(f"- Prize: ${g['prize']:.0f}")
        lines.append(f"- Vulnerability: {g['vulnerability']:.3f}")
        lines.append(f"- OEIS bridges: {g['oeis_bridges']}")
        lines.append(f"- Technique matches: {g['technique_match']}")
        if g["tag_synergies"]:
            for ts in g["tag_synergies"]:
                lines.append(f"- Tag synergy: {ts['pair'][0]} × {ts['pair'][1]} = {ts['synergy']:+.3f}")
        lines.append("")

    # 5. Hidden Structures
    lines.append("## 5. Hidden Structures")
    lines.append("")

    if hidden["dark_horses"]:
        lines.append("### Dark Horses (ML predicts solvable, structure says hard)")
        lines.append("")
        for d in hidden["dark_horses"][:5]:
            lines.append(f"- **#{d['number']}**: pred={d['predicted_solvability']:.3f} vs vuln={d['vulnerability']:.3f}")
        lines.append("")

    if hidden["false_positives"]:
        lines.append("### False Positives (structure says easy, ML says hard)")
        lines.append("")
        for f in hidden["false_positives"][:5]:
            lines.append(f"- **#{f['number']}**: vuln={f['vulnerability']:.3f} vs pred={f['predicted_solvability']:.3f}")
        lines.append("")

    if hidden["influence_orphans"]:
        lines.append("### Influence Orphans (important but unsolvable)")
        lines.append("")
        for io in hidden["influence_orphans"][:5]:
            lines.append(f"- **#{io['number']}**: PageRank={io['pagerank_norm']:.3f}, pred={io['predicted_solvability']:.3f}")
        lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("CROSS-ANALYSIS: THIRD-ORDER SYNTHESIS")
    print("=" * 70)

    problems = load_problems()
    print(f"Loaded {len(problems)} problems")

    print("\n1. Computing unified opportunity scores...")
    unified = unified_opportunity_score(problems)
    print(f"   Top: #{unified[0]['number']} (score={unified[0]['unified_score']:.3f})")

    print("\n2. Finding ranking disagreements...")
    disagreements = ranking_disagreements(unified)
    print(f"   Most controversial: #{disagreements[0]['number']}")

    print("\n3. Building strategic roadmap...")
    roadmap = strategic_roadmap(unified)
    print(f"   {len(roadmap['quick_wins'])} quick wins, {len(roadmap['prize_hunts'])} prize hunts")

    print("\n4. Generating problem genomes...")
    genomes = problem_genome(problems)
    print(f"   {len(genomes)} genomes generated")

    print("\n5. Detecting hidden structures...")
    hidden = hidden_structures(problems)
    print(f"   {len(hidden['dark_horses'])} dark horses, {len(hidden['false_positives'])} false positives")

    print("\nGenerating report...")
    report = generate_report(unified, disagreements, roadmap, genomes, hidden)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"Saved to {REPORT_PATH}")

    print("\n" + "=" * 70)
    print("CROSS-ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
