#!/usr/bin/env python3
"""
attack_surface.py — Concrete attack strategy analysis for Erdős problems.

Combines all analysis modules to produce actionable attack plans:
  1. Technique Arsenal: which mathematical techniques have solved similar problems
  2. Prerequisite Chain: what must be solved/proved first
  3. Partial Progress Map: what's already known about each target
  4. Approach Ranking: which attack angles are most promising
  5. Prize-Weighted Portfolio: optimal research investment allocation
  6. Breakthrough Cascade Simulator: what happens if we solve problem X

Output: docs/attack_surface_report.md
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
REPORT_PATH = ROOT / "docs" / "attack_surface_report.md"


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
# 1. Technique Arsenal
# ═══════════════════════════════════════════════════════════════════

def technique_arsenal(problems: List[Dict]) -> Dict[str, Any]:
    """
    For each tag combination, analyze what "techniques" have worked
    (proxied by which tag-combos have high solve rates).

    Returns: a mapping from tag-set → solve effectiveness.
    """
    # Compute solve rates by tag pair
    pair_stats = defaultdict(lambda: {"solved": 0, "total": 0, "examples": []})

    for p in problems:
        tags = sorted(_tags(p))
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                pair = (tags[i], tags[j])
                pair_stats[pair]["total"] += 1
                if _is_solved(p):
                    pair_stats[pair]["solved"] += 1
                    pair_stats[pair]["examples"].append(_number(p))

    # Rank by effectiveness (solve rate for pairs with enough data)
    effective_pairs = []
    for pair, stats in pair_stats.items():
        if stats["total"] >= 3:
            rate = stats["solved"] / stats["total"]
            effective_pairs.append({
                "technique": f"{pair[0]} + {pair[1]}",
                "solve_rate": round(rate, 3),
                "solved_count": stats["solved"],
                "total_count": stats["total"],
                "examples": stats["examples"][:5],
            })

    effective_pairs.sort(key=lambda x: (-x["solve_rate"], -x["total_count"]))

    # Single tag effectiveness
    tag_stats = defaultdict(lambda: {"solved": 0, "total": 0})
    for p in problems:
        for t in _tags(p):
            tag_stats[t]["total"] += 1
            if _is_solved(p):
                tag_stats[t]["solved"] += 1

    tag_effectiveness = []
    for tag, stats in tag_stats.items():
        if stats["total"] >= 5:
            tag_effectiveness.append({
                "tag": tag,
                "solve_rate": round(stats["solved"] / stats["total"], 3),
                "total": stats["total"],
            })
    tag_effectiveness.sort(key=lambda x: -x["solve_rate"])

    return {
        "effective_pairs": effective_pairs[:20],
        "tag_effectiveness": tag_effectiveness,
        "total_techniques": len(effective_pairs),
    }


# ═══════════════════════════════════════════════════════════════════
# 2. Prerequisite Chain
# ═══════════════════════════════════════════════════════════════════

def prerequisite_chains(problems: List[Dict]) -> List[Dict]:
    """
    Identify problems that share OEIS sequences, creating implicit
    prerequisite/dependency relationships.

    If problem A (solved) and problem B (open) share an OEIS sequence,
    A's solution may provide tools/insights for B.
    """
    # Build OEIS → problem mapping
    oeis_to_problems = defaultdict(list)
    for p in problems:
        for seq in _oeis(p):
            if seq and seq != "A000000" and not seq.startswith("A00000"):
                oeis_to_problems[seq].append(p)

    chains = []
    for seq, seq_problems in oeis_to_problems.items():
        if len(seq_problems) < 2:
            continue

        solved = [p for p in seq_problems if _is_solved(p)]
        open_probs = [p for p in seq_problems if _is_open(p)]

        if solved and open_probs:
            for op in open_probs:
                # Each solved problem is a potential prerequisite
                prereqs = [{
                    "number": _number(s),
                    "status": _status(s),
                    "tags": sorted(_tags(s)),
                } for s in solved]

                chains.append({
                    "target": _number(op),
                    "target_tags": sorted(_tags(op)),
                    "target_prize": _prize(op),
                    "shared_sequence": seq,
                    "prerequisites": prereqs,
                    "chain_strength": len(solved),
                })

    # Deduplicate by target (keep strongest chain)
    by_target = {}
    for c in chains:
        t = c["target"]
        if t not in by_target or c["chain_strength"] > by_target[t]["chain_strength"]:
            by_target[t] = c

    result = sorted(by_target.values(), key=lambda x: -x["chain_strength"])
    return result[:30]


# ═══════════════════════════════════════════════════════════════════
# 3. Status Proximity Analysis
# ═══════════════════════════════════════════════════════════════════

def status_proximity(problems: List[Dict]) -> Dict[str, Any]:
    """
    Analyze "near-miss" statuses — problems that are close to being solved.

    Categories:
    - Falsifiable: can be tested computationally → close to disproof
    - Verifiable: can be checked → close to proof
    - Decidable: known to be decidable → guaranteed solvable
    - Partially solved: proved in special cases (from comments)
    """
    near_miss = {
        "falsifiable": [],
        "verifiable": [],
        "decidable": [],
    }

    for p in problems:
        s = _status(p)
        info = {
            "number": _number(p),
            "tags": sorted(_tags(p)),
            "prize": _prize(p),
            "status": s,
            "comment": p.get("comments", ""),
        }

        if s == "falsifiable":
            near_miss["falsifiable"].append(info)
        elif s == "verifiable":
            near_miss["verifiable"].append(info)
        elif s == "decidable":
            near_miss["decidable"].append(info)

    # Lean-verified problems: a pool of techniques we KNOW are correct
    lean_proved = [p for p in problems if _status(p) in ("proved (Lean)", "disproved (Lean)", "solved (Lean)")]
    lean_tags = Counter(t for p in lean_proved for t in _tags(p))

    return {
        "near_miss": near_miss,
        "lean_proved_count": len(lean_proved),
        "lean_tag_coverage": dict(lean_tags.most_common(10)),
        "total_near_miss": sum(len(v) for v in near_miss.values()),
    }


# ═══════════════════════════════════════════════════════════════════
# 4. Prize-Weighted Portfolio
# ═══════════════════════════════════════════════════════════════════

def prize_portfolio(problems: List[Dict]) -> Dict[str, Any]:
    """
    Compute an optimal research portfolio that maximizes expected value.

    Expected value = Prize × P(solving) × (1/effort_proxy)

    The effort proxy is inversely related to the number of solved problems
    with similar structure.
    """
    from synthesis import compute_vulnerability_scores

    vuln = compute_vulnerability_scores(problems)
    vuln_by_num = {v["number"]: v["vulnerability"] for v in vuln}

    # Only look at open problems with prizes
    prize_problems = [p for p in problems if _is_open(p) and _prize(p) > 0]

    # Compute solve rate for each problem's tag set
    tag_solve_rates = {}
    for p in problems:
        for t in _tags(p):
            if t not in tag_solve_rates:
                tag_probs = [q for q in problems if t in _tags(q)]
                solved = sum(1 for q in tag_probs if _is_solved(q))
                tag_solve_rates[t] = solved / len(tag_probs) if tag_probs else 0

    portfolio = []
    for p in prize_problems:
        num = _number(p)
        prize = _prize(p)
        tags = _tags(p)

        # Solvability estimate
        tag_rate = np.mean([tag_solve_rates.get(t, 0) for t in tags]) if tags else 0
        vuln_score = vuln_by_num.get(num, 0.3)
        p_solve = 0.5 * tag_rate + 0.5 * vuln_score

        # Effort proxy: 1 / (similar solved count + 1)
        similar_solved = sum(1 for q in problems
                            if _is_solved(q) and len(_tags(q) & tags) > 0)
        effort_factor = 1.0 / (similar_solved + 1)

        # Expected value
        ev = prize * p_solve * (1 - effort_factor)  # higher similar solved = less effort

        portfolio.append({
            "number": num,
            "tags": sorted(tags),
            "prize": prize,
            "p_solve": round(p_solve, 3),
            "similar_solved": similar_solved,
            "expected_value": round(ev, 1),
            "comment": p.get("comments", ""),
        })

    portfolio.sort(key=lambda x: -x["expected_value"])

    total_ev = sum(p["expected_value"] for p in portfolio)
    total_prize = sum(p["prize"] for p in portfolio)

    return {
        "portfolio": portfolio,
        "total_expected_value": round(total_ev, 0),
        "total_available_prize": total_prize,
        "best_ev_per_dollar": portfolio[0] if portfolio else None,
    }


# ═══════════════════════════════════════════════════════════════════
# 5. Breakthrough Cascade Simulator
# ═══════════════════════════════════════════════════════════════════

def cascade_simulator(problems: List[Dict], target_numbers: List[int] = None) -> List[Dict]:
    """
    Simulate what happens to the problem landscape if specific problems
    are solved. For each target, compute:
    - How many OEIS-related problems become "closer" to solution
    - How tag solve rates change
    - Which additional problems move from "hard" to "tractable"
    """
    if target_numbers is None:
        # Default: top-10 open prize problems
        open_prize = [(p, _prize(p)) for p in problems if _is_open(p) and _prize(p) > 0]
        open_prize.sort(key=lambda x: -x[1])
        target_numbers = [_number(p) for p, _ in open_prize[:10]]

    by_number = {_number(p): p for p in problems}

    # Current tag solve rates
    tag_counts = defaultdict(lambda: {"total": 0, "solved": 0})
    for p in problems:
        for t in _tags(p):
            tag_counts[t]["total"] += 1
            if _is_solved(p):
                tag_counts[t]["solved"] += 1

    # OEIS connections
    oeis_to_problems = defaultdict(set)
    for p in problems:
        for seq in _oeis(p):
            if seq and seq != "A000000" and not seq.startswith("A00000"):
                oeis_to_problems[seq].add(_number(p))

    cascades = []
    for num in target_numbers:
        p = by_number.get(num)
        if not p:
            continue

        tags = _tags(p)
        prize = _prize(p)

        # What tags would gain a solved example?
        tag_boosts = {}
        for t in tags:
            old_rate = tag_counts[t]["solved"] / tag_counts[t]["total"] if tag_counts[t]["total"] > 0 else 0
            new_rate = (tag_counts[t]["solved"] + 1) / tag_counts[t]["total"] if tag_counts[t]["total"] > 0 else 0
            tag_boosts[t] = round(new_rate - old_rate, 4)

        # What problems share OEIS sequences?
        connected = set()
        for seq in _oeis(p):
            if seq in oeis_to_problems:
                connected |= oeis_to_problems[seq]
        connected.discard(num)

        # Of connected problems, which are open?
        unlocked = [n for n in connected if by_number.get(n) and _is_open(by_number[n])]

        cascades.append({
            "number": num,
            "tags": sorted(tags),
            "prize": prize,
            "tag_boosts": tag_boosts,
            "oeis_connected": len(connected),
            "problems_unlocked": len(unlocked),
            "unlocked_list": sorted(unlocked)[:10],
            "comment": p.get("comments", ""),
        })

    cascades.sort(key=lambda x: -x["problems_unlocked"])
    return cascades


# ═══════════════════════════════════════════════════════════════════
# 6. Comprehensive Attack Plans for Top Targets
# ═══════════════════════════════════════════════════════════════════

def attack_plans(problems: List[Dict], target_numbers: List[int] = None) -> List[Dict]:
    """
    Generate comprehensive attack plans for specific problems.

    Each plan includes:
    - Problem profile
    - Available techniques (from solved similar problems)
    - Potential approaches (based on tag effectiveness)
    - Related solved problems to study
    - Risk assessment
    """
    from synthesis import compute_vulnerability_scores

    vuln = compute_vulnerability_scores(problems)
    # Build lookup keyed by both int and str forms
    vuln_by_num = {}
    for v in vuln:
        vuln_by_num[v["number"]] = v
        vuln_by_num[str(v["number"])] = v
        if isinstance(v["number"], str) and v["number"].isdigit():
            vuln_by_num[int(v["number"])] = v

    if target_numbers is None:
        # Top 10 by vulnerability among open problems
        open_numbers = set()
        for p in problems:
            if _is_open(p):
                open_numbers.add(_number(p))
                open_numbers.add(str(p.get("number", "")))

        open_vuln = sorted(
            [v for v in vuln if v["number"] in open_numbers],
            key=lambda x: -x["vulnerability"]
        )
        target_numbers = [_number({"number": v["number"]}) for v in open_vuln[:10]]

    by_number = {}
    for p in problems:
        n = _number(p)
        by_number[n] = p
        by_number[str(p.get("number", ""))] = p

    # Tag solve rates
    tag_rates = {}
    for p in problems:
        for t in _tags(p):
            if t not in tag_rates:
                tag_probs = [q for q in problems if t in _tags(q)]
                solved = sum(1 for q in tag_probs if _is_solved(q))
                tag_rates[t] = round(solved / len(tag_probs), 3) if tag_probs else 0

    plans = []
    for num in target_numbers:
        p = by_number.get(num)
        if not p:
            continue

        tags = _tags(p)
        prize = _prize(p)
        v_info = vuln_by_num.get(num, {})

        # Find solved problems with overlapping tags
        solved_similar = []
        for q in problems:
            if _is_solved(q) and len(_tags(q) & tags) > 0:
                overlap = len(_tags(q) & tags) / len(_tags(q) | tags) if (_tags(q) | tags) else 0
                solved_similar.append({
                    "number": _number(q),
                    "status": _status(q),
                    "overlap": round(overlap, 2),
                    "shared_tags": sorted(_tags(q) & tags),
                })

        solved_similar.sort(key=lambda x: -x["overlap"])

        # Best approach angles
        approach_angles = []
        for t in sorted(tags):
            rate = tag_rates.get(t, 0)
            approach_angles.append({
                "tag": t,
                "historical_success": rate,
                "recommendation": "strong" if rate > 0.45 else ("moderate" if rate > 0.30 else "weak"),
            })
        approach_angles.sort(key=lambda x: -x["historical_success"])

        # Risk assessment
        vulnerability = v_info.get("vulnerability", 0)
        if vulnerability > 0.6:
            risk = "low"
        elif vulnerability > 0.4:
            risk = "moderate"
        else:
            risk = "high"

        plans.append({
            "number": num,
            "tags": sorted(tags),
            "prize": prize,
            "vulnerability": vulnerability,
            "risk": risk,
            "comment": p.get("comments", ""),
            "formalized": _is_formalized(p),
            "approach_angles": approach_angles,
            "solved_similar": solved_similar[:8],
            "oeis_count": len([s for s in _oeis(p)
                              if s and s != "A000000" and not s.startswith("A00000")]),
        })

    plans.sort(key=lambda x: -x["vulnerability"])
    return plans


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(arsenal, chains, proximity, portfolio, cascades, plans) -> str:
    lines = []
    lines.append("# Attack Surface Analysis")
    lines.append("")
    lines.append("Concrete mathematical attack strategies for open Erdős problems.")
    lines.append("")

    # 1. Technique Arsenal
    lines.append("## 1. Most Effective Technique Combinations")
    lines.append("")
    lines.append("| Technique | Solve Rate | Solved/Total | Examples |")
    lines.append("|-----------|-----------|-------------|----------|")
    for t in arsenal["effective_pairs"][:15]:
        examples = ", ".join(f"#{e}" for e in t["examples"][:3])
        lines.append(
            f"| {t['technique']} | {t['solve_rate']:.1%} | "
            f"{t['solved_count']}/{t['total_count']} | {examples} |"
        )
    lines.append("")

    lines.append("### Single Tag Effectiveness (top 15)")
    lines.append("")
    for t in arsenal["tag_effectiveness"][:15]:
        lines.append(f"- **{t['tag']}**: {t['solve_rate']:.1%} ({t['total']} problems)")
    lines.append("")

    # 2. Prerequisite Chains
    lines.append("## 2. Prerequisite Chains (OEIS-linked)")
    lines.append("")
    for c in chains[:10]:
        prereq_nums = ", ".join(f"#{p['number']}" for p in c["prerequisites"][:3])
        prize = f" (${c['target_prize']:.0f})" if c["target_prize"] > 0 else ""
        lines.append(f"- **#{c['target']}**{prize}: depends on [{prereq_nums}] via {c['shared_sequence']}")
    lines.append("")

    # 3. Near-Miss Status
    lines.append("## 3. Near-Miss Problems")
    lines.append("")
    for category, probs in proximity["near_miss"].items():
        if probs:
            lines.append(f"### {category.title()} ({len(probs)} problems)")
            for p in probs[:8]:
                prize = f" ${p['prize']:.0f}" if p["prize"] > 0 else ""
                comment = f" — {p['comment']}" if p["comment"] else ""
                lines.append(f"- #{p['number']}{prize}: {', '.join(p['tags'][:3])}{comment}")
            lines.append("")
    lines.append(f"Lean-verified techniques cover: {', '.join(list(proximity['lean_tag_coverage'].keys())[:8])}")
    lines.append("")

    # 4. Prize Portfolio
    lines.append("## 4. Prize Portfolio (Optimal Research Investment)")
    lines.append("")
    lines.append(f"Total available prize money: **${portfolio['total_available_prize']:.0f}**")
    lines.append(f"Total expected value: **${portfolio['total_expected_value']:.0f}**")
    lines.append("")
    lines.append("| Problem | Prize | P(solve) | Similar Solved | Expected Value |")
    lines.append("|---------|-------|----------|---------------|----------------|")
    for p in portfolio["portfolio"][:15]:
        comment = f" ({p['comment']})" if p["comment"] else ""
        lines.append(
            f"| #{p['number']}{comment} | ${p['prize']:.0f} | {p['p_solve']:.1%} | "
            f"{p['similar_solved']} | ${p['expected_value']:.0f} |"
        )
    lines.append("")

    # 5. Cascade Simulations
    lines.append("## 5. Breakthrough Cascade Simulations")
    lines.append("")
    lines.append("What happens if we solve these problems?")
    lines.append("")
    for c in cascades[:8]:
        prize = f" (${c['prize']:.0f})" if c["prize"] > 0 else ""
        comment = f" [{c['comment']}]" if c["comment"] else ""
        unlocked = ", ".join(f"#{n}" for n in c["unlocked_list"][:5])
        lines.append(f"### #{c['number']}{prize}{comment}")
        lines.append(f"- Tags: {', '.join(c['tags'])}")
        lines.append(f"- OEIS connections: {c['oeis_connected']}")
        lines.append(f"- Problems potentially unlocked: **{c['problems_unlocked']}**")
        if unlocked:
            lines.append(f"- Unlocked: {unlocked}")
        if c["tag_boosts"]:
            top_boost = max(c["tag_boosts"].items(), key=lambda x: x[1])
            lines.append(f"- Biggest tag boost: {top_boost[0]} +{top_boost[1]:.3f}")
        lines.append("")

    # 6. Attack Plans
    lines.append("## 6. Detailed Attack Plans")
    lines.append("")
    for plan in plans[:8]:
        prize = f" — ${plan['prize']:.0f}" if plan["prize"] > 0 else ""
        comment = f" [{plan['comment']}]" if plan["comment"] else ""
        lines.append(f"### #{plan['number']}{prize}{comment}")
        lines.append(f"- **Risk**: {plan['risk']} (vulnerability={plan['vulnerability']:.3f})")
        lines.append(f"- **Tags**: {', '.join(plan['tags'])}")
        lines.append(f"- **Formalized**: {'yes' if plan['formalized'] else 'no'}")
        lines.append(f"- **OEIS sequences**: {plan['oeis_count']}")
        lines.append("")

        lines.append("  **Approach angles:**")
        for a in plan["approach_angles"]:
            lines.append(f"  - {a['tag']}: {a['recommendation']} ({a['historical_success']:.1%} success)")
        lines.append("")

        if plan["solved_similar"]:
            lines.append("  **Study these solved problems:**")
            for s in plan["solved_similar"][:5]:
                lines.append(f"  - #{s['number']} ({s['status']}, overlap={s['overlap']:.0%}, shared: {', '.join(s['shared_tags'])})")
            lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("ATTACK SURFACE ANALYSIS")
    print("=" * 70)

    problems = load_problems()
    print(f"Loaded {len(problems)} problems")

    print("\n1. Building technique arsenal...")
    arsenal = technique_arsenal(problems)
    print(f"   {arsenal['total_techniques']} technique combinations analyzed")

    print("\n2. Tracing prerequisite chains...")
    chains = prerequisite_chains(problems)
    print(f"   {len(chains)} prerequisite chains found")

    print("\n3. Analyzing status proximity...")
    proximity = status_proximity(problems)
    print(f"   {proximity['total_near_miss']} near-miss problems")

    print("\n4. Computing prize portfolio...")
    portfolio = prize_portfolio(problems)
    print(f"   Expected value: ${portfolio['total_expected_value']:.0f}")

    print("\n5. Simulating cascades...")
    cascades = cascade_simulator(problems)
    print(f"   Top cascade: #{cascades[0]['number']} → {cascades[0]['problems_unlocked']} unlocked")

    print("\n6. Generating attack plans...")
    plans = attack_plans(problems)
    print(f"   {len(plans)} detailed plans generated")

    print("\nGenerating report...")
    report = generate_report(arsenal, chains, proximity, portfolio, cascades, plans)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"Saved to {REPORT_PATH}")

    print("\n" + "=" * 70)
    print("ATTACK SURFACE ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
