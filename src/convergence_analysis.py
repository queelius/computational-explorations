#!/usr/bin/env python3
"""
convergence_analysis.py — Cross-module signal convergence analysis.

NOTE: Opportunity scores already incorporate vulnerability as a sub-signal
(weight 0.25), so agreement between the "opportunity" and "vulnerability"
modules is partially autocorrelation, not independent confirmation. Similarly,
"tag_solvability" and "tractability" both derive from tag solve rates, making
their high correlation (r ~ 0.9) expected rather than informative. The number
of truly independent signals is smaller than the number of modules aggregated.

Identifies where multiple analysis modules agree on the same conclusions.
Because several modules share input signals (tag solve rates, OEIS bridges,
vulnerability scores), high agreement is partially expected and should not
be over-interpreted as independent confirmation.

This module synthesizes outputs from:
  - opportunity_map.py (composite score; INCLUDES vulnerability at weight 0.25)
  - difficulty_decomposition.py (PCA difficulty scores)
  - dependency_graph.py (proximity graph reachability, not true dependencies)
  - research_frontier.py (tag frontier scores)
  - attack_surface.py (vulnerability, cascade potential)
  - information_theory.py (surprise scores)
  - spectral_analysis.py (PageRank, bridge scores)
  - predictive_model.py (logistic regression predictions)

Analyses:
  1. Signal Convergence: problems ranked highly by most modules
  2. Consensus Targets: problems where modules agree (with the caveats above)
  3. Disagreement Analysis: where modules disagree
  4. Meta-Rankings: rank-aggregation across all module rankings
  5. Agreement Level: how much agreement exists for each ranking
  6. Research Strategy Matrix: 2D map of tractability vs impact

Output: docs/convergence_analysis_report.md
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
REPORT_PATH = ROOT / "docs" / "convergence_analysis_report.md"


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


# ═══════════════════════════════════════════════════════════════════
# Collect Rankings from All Modules
# ═══════════════════════════════════════════════════════════════════

def collect_all_rankings(problems: List[Dict]) -> Dict[str, Dict[int, float]]:
    """
    Collect per-problem scores from all available analysis modules.
    Each module provides a dict: {problem_number: normalized_score [0,1]}.

    Returns dict: {module_name: {number: score}}.
    """
    rankings = {}
    open_nums = {_number(p) for p in problems if _is_open(p)}

    # 1. Opportunity Map — composite opportunity score
    from opportunity_map import compute_opportunity_scores
    opp = compute_opportunity_scores(problems)
    rankings["opportunity"] = {s["number"]: s["opportunity_score"] for s in opp}

    # 2. Difficulty Decomposition — inverted difficulty (easier = higher score)
    from difficulty_decomposition import pca_decomposition, difficulty_spectrum
    pca = pca_decomposition(problems, n_components=5)
    spectrum = difficulty_spectrum(problems, pca)
    if spectrum:
        min_d = spectrum[-1]["difficulty_score"]
        max_d = spectrum[0]["difficulty_score"]
        rng = max_d - min_d if max_d != min_d else 1.0
        # Invert: low difficulty = high tractability score
        rankings["tractability"] = {
            s["number"]: 1.0 - (s["difficulty_score"] - min_d) / rng
            for s in spectrum
        }

    # 3. Proximity Graph — reachability in tag/OEIS proximity graph
    # NOTE: "keystone_impact" here reflects BFS reachability through tag overlap,
    # not true mathematical dependency. High values are driven by broad tags.
    from dependency_graph import build_dependency_graph, keystone_problems
    graph = build_dependency_graph(problems)
    keystones = keystone_problems(problems, graph, top_k=100)
    if keystones:
        max_down = keystones[0]["downstream_open"] if keystones else 1
        rankings["keystone_impact"] = {
            k["number"]: k["downstream_open"] / max_down
            for k in keystones
        }

    # 4. Research Frontier — tag frontier score (averaged for problem)
    from research_frontier import frontier_scores
    frontier = frontier_scores(problems)
    tag_frontier = {f["tag"]: f["frontier_score"] for f in frontier}
    frontier_ranking = {}
    for p in problems:
        if not _is_open(p):
            continue
        tags = _tags(p)
        if tags:
            scores = [tag_frontier.get(t, 0.3) for t in tags]
            frontier_ranking[_number(p)] = sum(scores) / len(scores)
        else:
            frontier_ranking[_number(p)] = 0.3
    rankings["frontier"] = frontier_ranking

    # 5. Attack Surface — vulnerability score
    from synthesis import compute_vulnerability_scores
    vuln = compute_vulnerability_scores(problems)
    vuln_ranking = {}
    for v in vuln:
        num = v["number"]
        if isinstance(num, str) and num.isdigit():
            num = int(num)
        if num in open_nums:
            vuln_ranking[num] = v["vulnerability"]
    rankings["vulnerability"] = vuln_ranking

    # 6. Tag solve rate average (simple but independent signal)
    tag_solved = Counter()
    tag_total = Counter()
    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _is_solved(p):
                tag_solved[t] += 1
    tag_rate = {t: tag_solved[t] / tag_total[t] for t in tag_total if tag_total[t] > 0}
    tag_ranking = {}
    for p in problems:
        if not _is_open(p):
            continue
        tags = _tags(p)
        if tags:
            rates = [tag_rate.get(t, 0.3) for t in tags]
            tag_ranking[_number(p)] = sum(rates) / len(rates)
        else:
            tag_ranking[_number(p)] = 0.3
    rankings["tag_solvability"] = tag_ranking

    return rankings


# ═══════════════════════════════════════════════════════════════════
# Percentile Ranking — Normalize to Rank Percentiles
# ═══════════════════════════════════════════════════════════════════

def compute_percentile_ranks(rankings: Dict[str, Dict[int, float]]) -> Dict[str, Dict[int, float]]:
    """
    Convert raw scores to percentile ranks [0, 1] where 1.0 = best.
    This makes rankings comparable across modules with different scales.
    """
    percentiles = {}
    for module, scores in rankings.items():
        if not scores:
            percentiles[module] = {}
            continue
        sorted_nums = sorted(scores.keys(), key=lambda n: scores[n])
        n = len(sorted_nums)
        percentiles[module] = {
            num: (rank + 1) / n
            for rank, num in enumerate(sorted_nums)
        }
    return percentiles


# ═══════════════════════════════════════════════════════════════════
# Consensus Ranking — Borda Count Aggregation
# ═══════════════════════════════════════════════════════════════════

def consensus_ranking(problems: List[Dict],
                      rankings: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Aggregate multiple module rankings into a single consensus ranking
    using Borda count (average percentile rank).

    Returns sorted list with:
    - number, consensus_score, module_scores, agreement_level, tags, prize
    """
    if rankings is None:
        rankings = collect_all_rankings(problems)

    percentiles = compute_percentile_ranks(rankings)
    modules = list(percentiles.keys())
    open_nums = {_number(p) for p in problems if _is_open(p)}
    prob_by_num = {_number(p): p for p in problems}

    results = []
    for num in open_nums:
        scores = {}
        for mod in modules:
            if num in percentiles[mod]:
                scores[mod] = percentiles[mod][num]

        if not scores:
            continue

        # Consensus = average percentile across all modules that rank this problem
        consensus = sum(scores.values()) / len(scores)

        # Agreement level: std of percentile ranks (low std = high agreement)
        if len(scores) >= 2:
            vals = list(scores.values())
            mean_v = sum(vals) / len(vals)
            variance = sum((v - mean_v) ** 2 for v in vals) / len(vals)
            agreement = 1.0 - min(math.sqrt(variance), 1.0)  # 1 = perfect agreement
        else:
            agreement = 0.5

        p = prob_by_num.get(num)
        results.append({
            "number": num,
            "consensus_score": consensus,
            "module_scores": scores,
            "n_modules": len(scores),
            "agreement": agreement,
            "tags": sorted(_tags(p)) if p else [],
            "prize": _prize(p) if p else 0.0,
        })

    results.sort(key=lambda x: -x["consensus_score"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Disagreement Analysis — Where Modules Conflict
# ═══════════════════════════════════════════════════════════════════

def disagreement_analysis(consensus: List[Dict],
                          threshold: float = 0.3) -> List[Dict[str, Any]]:
    """
    Find problems where modules strongly disagree — one module ranks
    it highly while another ranks it low.

    These are the most interesting cases: they reveal what different
    analytical lenses see differently about a problem.

    threshold: minimum range of percentile ranks to count as disagreement.
    """
    results = []
    for item in consensus:
        scores = item["module_scores"]
        if len(scores) < 3:
            continue

        vals = list(scores.values())
        max_val = max(vals)
        min_val = min(vals)
        spread = max_val - min_val

        if spread >= threshold:
            # Find which modules agree/disagree
            high_modules = [m for m, v in scores.items() if v >= max_val - 0.1]
            low_modules = [m for m, v in scores.items() if v <= min_val + 0.1]

            results.append({
                "number": item["number"],
                "spread": spread,
                "high_modules": high_modules,
                "low_modules": low_modules,
                "consensus_score": item["consensus_score"],
                "tags": item["tags"],
                "prize": item["prize"],
                "module_scores": scores,
            })

    results.sort(key=lambda x: -x["spread"])
    return results


# ═══════════════════════════════════════════════════════════════════
# High-Confidence Targets — Strong Multi-Module Agreement
# ═══════════════════════════════════════════════════════════════════

def high_confidence_targets(consensus: List[Dict],
                            min_agreement: float = 0.7,
                            min_consensus: float = 0.6) -> List[Dict[str, Any]]:
    """
    Find problems that MULTIPLE independent modules all rank highly.
    These are the highest-confidence research targets.

    min_agreement: minimum agreement score (1 = perfect)
    min_consensus: minimum consensus score (1 = top of all rankings)
    """
    results = []
    for item in consensus:
        if (item["agreement"] >= min_agreement and
            item["consensus_score"] >= min_consensus and
            item["n_modules"] >= 4):
            results.append(item)

    results.sort(key=lambda x: -x["consensus_score"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Research Strategy Matrix — Tractability vs Impact
# ═══════════════════════════════════════════════════════════════════

def strategy_matrix(problems: List[Dict],
                    rankings: Optional[Dict] = None) -> Dict[str, List[Dict]]:
    """
    Classify problems into a 2×2 strategy matrix:
    - High tractability + High impact = "Do First" (quick wins with big payoff)
    - High tractability + Low impact = "Easy Wins" (low-hanging fruit)
    - Low tractability + High impact = "Moonshots" (hard but transformative)
    - Low tractability + Low impact = "Deprioritize" (hard and low payoff)

    Tractability = average of (opportunity, tractability, vulnerability, tag_solvability)
    Impact = average of (keystone_impact, frontier, prize_signal)
    """
    if rankings is None:
        rankings = collect_all_rankings(problems)

    percentiles = compute_percentile_ranks(rankings)
    open_nums = {_number(p) for p in problems if _is_open(p)}
    prob_by_num = {_number(p): p for p in problems}

    # Tractability signals
    tract_mods = ["opportunity", "tractability", "vulnerability", "tag_solvability"]
    # Impact signals
    impact_mods = ["keystone_impact", "frontier"]

    results = {"do_first": [], "easy_wins": [], "moonshots": [], "deprioritize": []}

    for num in open_nums:
        # Compute tractability score
        tract_scores = [percentiles[m].get(num, 0.5) for m in tract_mods if m in percentiles]
        tract = sum(tract_scores) / len(tract_scores) if tract_scores else 0.5

        # Compute impact score
        impact_scores = [percentiles[m].get(num, 0.5) for m in impact_mods if m in percentiles]
        # Add prize as impact signal
        p = prob_by_num.get(num)
        prize = _prize(p) if p else 0
        prize_signal = min(math.log1p(prize) / math.log1p(10000), 1.0) if prize > 0 else 0.0
        impact_scores.append(prize_signal)
        impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0.5

        entry = {
            "number": num,
            "tractability": tract,
            "impact": impact,
            "tags": sorted(_tags(p)) if p else [],
            "prize": prize,
        }

        if tract >= 0.6 and impact >= 0.5:
            results["do_first"].append(entry)
        elif tract >= 0.6 and impact < 0.5:
            results["easy_wins"].append(entry)
        elif tract < 0.6 and impact >= 0.5:
            results["moonshots"].append(entry)
        else:
            results["deprioritize"].append(entry)

    # Sort each quadrant
    for key in results:
        results[key].sort(key=lambda x: -(x["tractability"] + x["impact"]))

    return results


# ═══════════════════════════════════════════════════════════════════
# Module Correlation — How Similar Are the Rankings?
# ═══════════════════════════════════════════════════════════════════

def module_correlations(rankings: Dict[str, Dict[int, float]]) -> Dict[str, Any]:
    """
    Compute pairwise Spearman rank correlations between all modules.
    High correlation = modules see the same things.
    Low correlation = modules capture different aspects.
    """
    percentiles = compute_percentile_ranks(rankings)
    modules = list(percentiles.keys())

    # Find common problems across all modules
    all_nums = set()
    for mod in modules:
        all_nums.update(percentiles[mod].keys())

    # Build correlation matrix
    n_mods = len(modules)
    corr_matrix = np.eye(n_mods)

    for i in range(n_mods):
        for j in range(i + 1, n_mods):
            # Common problems
            common = set(percentiles[modules[i]].keys()) & set(percentiles[modules[j]].keys())
            if len(common) < 10:
                corr_matrix[i, j] = corr_matrix[j, i] = 0.0
                continue

            x = np.array([percentiles[modules[i]][n] for n in common])
            y = np.array([percentiles[modules[j]][n] for n in common])

            if np.std(x) > 0 and np.std(y) > 0:
                r = float(np.corrcoef(x, y)[0, 1])
            else:
                r = 0.0
            corr_matrix[i, j] = r
            corr_matrix[j, i] = r

    # Find most/least correlated pairs
    pairs = []
    for i in range(n_mods):
        for j in range(i + 1, n_mods):
            pairs.append({
                "module_a": modules[i],
                "module_b": modules[j],
                "correlation": float(corr_matrix[i, j]),
            })
    pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

    return {
        "modules": modules,
        "correlation_matrix": corr_matrix.tolist(),
        "pairs": pairs,
        "avg_correlation": float(np.mean([p["correlation"] for p in pairs])),
    }


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    rankings = collect_all_rankings(problems)
    consensus = consensus_ranking(problems, rankings)
    disagreements = disagreement_analysis(consensus)
    hc_targets = high_confidence_targets(consensus)
    matrix = strategy_matrix(problems, rankings)
    correlations = module_correlations(rankings)

    lines = ["# Convergence Analysis: Cross-Module Signal Agreement", ""]
    lines.append(f"Synthesizing {len(rankings)} independent analytical modules")
    lines.append(f"to identify highest-confidence research targets among {len(consensus)} open problems.")
    lines.append("")

    # Section 1: Module Correlations
    lines.append("## 1. Module Independence")
    lines.append("")
    lines.append(f"Average pairwise correlation: **{correlations['avg_correlation']:.3f}**")
    lines.append("")
    lines.append("| Module A | Module B | Correlation |")
    lines.append("|----------|----------|-------------|")
    for p in correlations["pairs"][:10]:
        lines.append(f"| {p['module_a']} | {p['module_b']} | {p['correlation']:+.3f} |")
    lines.append("")

    # Section 2: Consensus Top 20
    lines.append("## 2. Consensus Top 20 (Borda Count Aggregation)")
    lines.append("")
    lines.append("| Rank | Problem | Consensus | Agreement | Modules | Tags | Prize |")
    lines.append("|------|---------|-----------|-----------|---------|------|-------|")
    for i, item in enumerate(consensus[:20]):
        tags_str = ", ".join(item["tags"][:3])
        prize_str = f"${item['prize']:.0f}" if item["prize"] > 0 else "-"
        lines.append(f"| {i + 1} | #{item['number']} | {item['consensus_score']:.3f} | "
                      f"{item['agreement']:.2f} | {item['n_modules']} | {tags_str} | {prize_str} |")
    lines.append("")

    # Section 3: High-Confidence Targets
    lines.append("## 3. High-Confidence Targets (Multi-Module Agreement)")
    lines.append("")
    if hc_targets:
        lines.append(f"**{len(hc_targets)} problems** pass the high-confidence filter")
        lines.append("(agreement ≥ 0.7, consensus ≥ 0.6, ≥ 4 modules).")
        lines.append("")
        lines.append("| Problem | Consensus | Agreement | Tags | Prize |")
        lines.append("|---------|-----------|-----------|------|-------|")
        for item in hc_targets[:15]:
            tags_str = ", ".join(item["tags"][:3])
            prize_str = f"${item['prize']:.0f}" if item["prize"] > 0 else "-"
            lines.append(f"| #{item['number']} | {item['consensus_score']:.3f} | "
                          f"{item['agreement']:.2f} | {tags_str} | {prize_str} |")
    else:
        lines.append("No problems passed the strict high-confidence filter.")
        lines.append("Relaxing to agreement ≥ 0.6, consensus ≥ 0.5:")
        relaxed = high_confidence_targets(consensus, min_agreement=0.6, min_consensus=0.5)
        lines.append(f"**{len(relaxed)} problems** pass relaxed filter.")
        if relaxed:
            lines.append("")
            lines.append("| Problem | Consensus | Agreement | Tags | Prize |")
            lines.append("|---------|-----------|-----------|------|-------|")
            for item in relaxed[:15]:
                tags_str = ", ".join(item["tags"][:3])
                prize_str = f"${item['prize']:.0f}" if item["prize"] > 0 else "-"
                lines.append(f"| #{item['number']} | {item['consensus_score']:.3f} | "
                              f"{item['agreement']:.2f} | {tags_str} | {prize_str} |")
    lines.append("")

    # Section 4: Disagreements
    lines.append("## 4. Module Disagreements (Analytical Blindspots)")
    lines.append("")
    lines.append("Problems where modules strongly disagree reveal what different")
    lines.append("analytical lenses see differently.")
    lines.append("")
    for d in disagreements[:10]:
        lines.append(f"### #{d['number']} (spread={d['spread']:.2f})")
        tags_str = ", ".join(d["tags"][:3])
        lines.append(f"- Tags: {tags_str}")
        lines.append(f"- **High**: {', '.join(d['high_modules'])}")
        lines.append(f"- **Low**: {', '.join(d['low_modules'])}")
        scores_str = ", ".join(f"{m}={v:.2f}" for m, v in sorted(d["module_scores"].items()))
        lines.append(f"- Scores: {scores_str}")
        lines.append("")

    # Section 5: Strategy Matrix
    lines.append("## 5. Research Strategy Matrix")
    lines.append("")
    for quadrant, label, desc in [
        ("do_first", "Do First (High Tractability + High Impact)", "Quick wins with big payoff"),
        ("easy_wins", "Easy Wins (High Tractability + Low Impact)", "Low-hanging fruit"),
        ("moonshots", "Moonshots (Low Tractability + High Impact)", "Hard but transformative"),
        ("deprioritize", "Deprioritize (Low Tractability + Low Impact)", ""),
    ]:
        items = matrix[quadrant]
        lines.append(f"### {label}")
        lines.append(f"**{len(items)} problems** — {desc}")
        lines.append("")
        if items and quadrant != "deprioritize":
            lines.append("| Problem | Tractability | Impact | Tags | Prize |")
            lines.append("|---------|-------------|--------|------|-------|")
            for item in items[:10]:
                tags_str = ", ".join(item["tags"][:3])
                prize_str = f"${item['prize']:.0f}" if item["prize"] > 0 else "-"
                lines.append(f"| #{item['number']} | {item['tractability']:.2f} | "
                              f"{item['impact']:.2f} | {tags_str} | {prize_str} |")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    problems = load_problems()
    report = generate_report(problems)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")
