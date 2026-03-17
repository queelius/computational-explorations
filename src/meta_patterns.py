#!/usr/bin/env python3
"""
meta_patterns.py — Higher-order pattern mining across the Erdős database.

Discovers PATTERNS OF PATTERNS:
  1. Resolution Waves: temporal clustering of solutions (do solutions come in bursts?)
  2. Tag Co-Evolution: which tag pairs get solved together (hidden technique sharing)
  3. Difficulty Decay Curves: how solvability changes with problem age/structure
  4. Network Motifs: triangles, stars, bridges in the conjecture network
  5. Problem DNA: structural fingerprints that classify problem behavior
  6. Anomaly Detection: problems whose structure doesn't match their outcome

Output: docs/meta_patterns_report.md
"""

import math
import yaml
import numpy as np
from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "meta_patterns_report.md"


# ═══════════════════════════════════════════════════════════════════
# Data Loading (reuse synthesis patterns)
# ═══════════════════════════════════════════════════════════════════

def load_problems() -> List[Dict]:
    with open(DATA_PATH) as f:
        return yaml.safe_load(f)


def _status(p: Dict) -> str:
    return p.get("status", {}).get("state", "unknown")


def _tags(p: Dict) -> Set[str]:
    return set(p.get("tags", []))


def _oeis(p: Dict) -> List[str]:
    return p.get("oeis", [])


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


def _year_solved(p: Dict) -> Optional[int]:
    """Extract year the problem was solved, if available.

    Tries multiple fields: status.date, date, references with years.
    """
    # Try status date
    status = p.get("status", {})
    for field in ["date", "last_update"]:
        date = status.get(field, "")
        if date:
            parts = str(date).split("-")
            if parts and parts[0].isdigit():
                y = int(parts[0])
                if 1900 <= y <= 2030:
                    return y
    # Try top-level date
    date = p.get("date", "")
    if date:
        parts = str(date).split("-")
        if parts and parts[0].isdigit():
            y = int(parts[0])
            if 1900 <= y <= 2030:
                return y
    # Try extracting year from references
    refs = p.get("references", [])
    if isinstance(refs, list):
        import re
        for ref in refs:
            years = re.findall(r'\b(19[5-9]\d|20[0-2]\d)\b', str(ref))
            if years:
                return int(max(years))
    return None


def _year_posed(p: Dict) -> Optional[int]:
    """Extract year the problem was posed, if available."""
    date = p.get("date", "")
    if date:
        parts = str(date).split("-")
        if parts and parts[0].isdigit():
            y = int(parts[0])
            if 1900 <= y <= 2030:
                return y
    return None


# ═══════════════════════════════════════════════════════════════════
# 1. Resolution Waves — temporal clustering of solutions
# ═══════════════════════════════════════════════════════════════════

def resolution_waves(problems: List[Dict], bin_width: int = 5) -> Dict[str, Any]:
    """
    Analyze temporal patterns in problem resolution.

    Groups solved problems by year and identifies:
    - Peak resolution periods
    - Burst detection (years with > 2σ solutions above mean)
    - Inter-solution gaps
    - Whether solutions cluster by tag/domain
    """
    solved = []
    for p in problems:
        year = _year_solved(p)
        if year and _status(p) in ("proved", "disproved"):
            solved.append({"number": _number(p), "year": year,
                          "tags": sorted(_tags(p)), "status": _status(p)})

    if not solved:
        return {"wave_count": 0, "solved_with_dates": 0}

    # Bin by year
    year_counts = Counter(s["year"] for s in solved)
    min_year = min(year_counts)
    max_year = max(year_counts)

    # Build year histogram
    years = list(range(min_year, max_year + 1))
    counts = [year_counts.get(y, 0) for y in years]

    # Detect bursts: years with count > mean + 2*std
    mean_rate = np.mean(counts) if counts else 0
    std_rate = np.std(counts) if counts else 0
    burst_threshold = mean_rate + 2 * std_rate if std_rate > 0 else mean_rate + 1

    bursts = [(y, year_counts.get(y, 0)) for y in years
              if year_counts.get(y, 0) > burst_threshold]

    # Bin by wider periods
    binned = defaultdict(list)
    for s in solved:
        decade_bin = (s["year"] // bin_width) * bin_width
        binned[decade_bin].append(s)

    period_summary = []
    for period in sorted(binned):
        ps = binned[period]
        tag_counts = Counter(t for s in ps for t in s["tags"])
        period_summary.append({
            "period": f"{period}-{period + bin_width - 1}",
            "count": len(ps),
            "dominant_tags": tag_counts.most_common(3),
        })

    # Tag-specific waves: for each major tag, when were problems solved?
    tag_waves = {}
    major_tags = Counter(t for s in solved for t in s["tags"]).most_common(10)
    for tag, total_count in major_tags:
        tag_years = Counter(s["year"] for s in solved if tag in s["tags"])
        if tag_years:
            peak_year = max(tag_years, key=tag_years.get)
            tag_waves[tag] = {
                "total_solved": total_count,
                "peak_year": peak_year,
                "peak_count": tag_years[peak_year],
                "span": max(tag_years) - min(tag_years),
            }

    return {
        "solved_with_dates": len(solved),
        "year_range": (min_year, max_year),
        "mean_per_year": round(mean_rate, 2),
        "std_per_year": round(std_rate, 2),
        "burst_threshold": round(burst_threshold, 2),
        "burst_years": bursts,
        "wave_count": len(bursts),
        "period_summary": period_summary,
        "tag_waves": tag_waves,
        "peak_year": max(year_counts, key=year_counts.get) if year_counts else None,
        "peak_count": max(year_counts.values()) if year_counts else 0,
    }


# ═══════════════════════════════════════════════════════════════════
# 2. Tag Co-Evolution — which tags get solved together?
# ═══════════════════════════════════════════════════════════════════

def tag_coevolution(problems: List[Dict]) -> Dict[str, Any]:
    """
    Analyze which tag pairs co-occur in solved vs open problems.

    A tag pair with HIGH solve rate suggests an effective technique combination.
    A tag pair with LOW solve rate suggests a genuine difficulty barrier.
    """
    solved = [p for p in problems if _status(p) in ("proved", "disproved")]
    open_probs = [p for p in problems if _status(p) == "open"]

    # Count tag pairs in solved and open
    pair_solved = Counter()
    pair_open = Counter()
    pair_total = Counter()

    for p in solved:
        tags = sorted(_tags(p))
        for i, j in combinations(tags, 2):
            pair_solved[(i, j)] += 1
            pair_total[(i, j)] += 1

    for p in open_probs:
        tags = sorted(_tags(p))
        for i, j in combinations(tags, 2):
            pair_open[(i, j)] += 1
            pair_total[(i, j)] += 1

    # Compute solve rates for pairs (minimum 3 occurrences)
    pair_rates = {}
    for pair in pair_total:
        if pair_total[pair] >= 3:
            rate = pair_solved.get(pair, 0) / pair_total[pair]
            pair_rates[pair] = {
                "solve_rate": round(rate, 3),
                "total": pair_total[pair],
                "solved": pair_solved.get(pair, 0),
                "open": pair_open.get(pair, 0),
            }

    # Sort by solve rate
    easy_pairs = sorted(pair_rates.items(), key=lambda x: -x[1]["solve_rate"])
    hard_pairs = sorted(pair_rates.items(), key=lambda x: x[1]["solve_rate"])

    # "Synergy" detection: pairs whose joint solve rate differs from individual tag averages.
    # NOTE: This is a raw difference of averages, not a statistically validated synergy
    # metric. No p-values or multiple-testing correction. The "expected" rate is just the
    # mean of the two individual tag solve rates, which is not a principled null model
    # (it ignores base rate, sample size, and confounders). Treat these as exploratory
    # observations, not confirmed synergies or anti-synergies.
    tag_individual_rates = {}
    tag_total = Counter()
    tag_solved_count = Counter()
    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _status(p) in ("proved", "disproved"):
                tag_solved_count[t] += 1
    for t in tag_total:
        tag_individual_rates[t] = tag_solved_count.get(t, 0) / tag_total[t]

    synergies = []
    for pair, info in pair_rates.items():
        t1, t2 = pair
        if t1 in tag_individual_rates and t2 in tag_individual_rates:
            # NOTE: This "expected" rate is just the average of individual tag rates,
            # not a proper statistical expectation. The difference (actual - expected)
            # is reported as "synergy" but has no confidence interval or significance test.
            expected = (tag_individual_rates[t1] + tag_individual_rates[t2]) / 2
            actual = info["solve_rate"]
            if info["total"] >= 5:
                synergies.append({
                    "pair": pair,
                    "actual_rate": actual,
                    "expected_rate": round(expected, 3),
                    "synergy": round(actual - expected, 3),
                    "count": info["total"],
                })

    synergies.sort(key=lambda x: -x["synergy"])

    return {
        "num_pairs_analyzed": len(pair_rates),
        "easiest_pairs": [(p, info) for p, info in easy_pairs[:10]],
        "hardest_pairs": [(p, info) for p, info in hard_pairs[:10]],
        "strongest_synergies": synergies[:10],
        "strongest_anti_synergies": sorted(synergies, key=lambda x: x["synergy"])[:10],
    }


# ═══════════════════════════════════════════════════════════════════
# 3. Difficulty Decay — how does solvability change with structure?
# ═══════════════════════════════════════════════════════════════════

def difficulty_decay(problems: List[Dict]) -> Dict[str, Any]:
    """
    Analyze how problem characteristics correlate with difficulty.

    Features:
    - Tag count vs solve rate
    - OEIS count vs solve rate
    - Problem number (proxy for age) vs solve rate
    - Prize amount vs solve duration
    """
    # Tag count vs solve rate
    tag_count_groups = defaultdict(lambda: {"solved": 0, "total": 0})
    for p in problems:
        n_tags = len(_tags(p))
        bucket = min(n_tags, 5)  # cap at 5+
        tag_count_groups[bucket]["total"] += 1
        if _status(p) in ("proved", "disproved"):
            tag_count_groups[bucket]["solved"] += 1

    tag_count_rates = {}
    for bucket in sorted(tag_count_groups):
        g = tag_count_groups[bucket]
        tag_count_rates[bucket] = round(g["solved"] / max(g["total"], 1), 3)

    # OEIS count vs solve rate
    oeis_count_groups = defaultdict(lambda: {"solved": 0, "total": 0})
    for p in problems:
        n_oeis = len(_oeis(p))
        bucket = min(n_oeis, 5)
        oeis_count_groups[bucket]["total"] += 1
        if _status(p) in ("proved", "disproved"):
            oeis_count_groups[bucket]["solved"] += 1

    oeis_count_rates = {}
    for bucket in sorted(oeis_count_groups):
        g = oeis_count_groups[bucket]
        oeis_count_rates[bucket] = round(g["solved"] / max(g["total"], 1), 3)

    # Problem number quartiles vs solve rate
    all_nums = [_number(p) for p in problems]
    int_nums = sorted(int(n) for n in all_nums if str(n).isdigit())
    if int_nums:
        q25 = int_nums[len(int_nums) // 4]
        q50 = int_nums[len(int_nums) // 2]
        q75 = int_nums[3 * len(int_nums) // 4]
    else:
        q25, q50, q75 = 0, 0, 0

    quartile_groups = defaultdict(lambda: {"solved": 0, "total": 0})
    for p in problems:
        num = _number(p)
        try:
            n = int(num)
        except (ValueError, TypeError):
            continue
        if n <= q25:
            q = "Q1 (earliest)"
        elif n <= q50:
            q = "Q2"
        elif n <= q75:
            q = "Q3"
        else:
            q = "Q4 (latest)"
        quartile_groups[q]["total"] += 1
        if _status(p) in ("proved", "disproved"):
            quartile_groups[q]["solved"] += 1

    quartile_rates = {}
    for q in sorted(quartile_groups):
        g = quartile_groups[q]
        quartile_rates[q] = {
            "rate": round(g["solved"] / max(g["total"], 1), 3),
            "total": g["total"],
            "solved": g["solved"],
        }

    # Formalization paradox: formalized vs non-formalized solve rates
    formalized_groups = defaultdict(lambda: {"solved": 0, "total": 0})
    for p in problems:
        is_formalized = bool(p.get("formalized", {}).get("lean", False) or
                           p.get("formalized", {}).get("isabelle", False))
        key = "formalized" if is_formalized else "not_formalized"
        formalized_groups[key]["total"] += 1
        if _status(p) in ("proved", "disproved"):
            formalized_groups[key]["solved"] += 1

    formalization_rates = {}
    for key in formalized_groups:
        g = formalized_groups[key]
        formalization_rates[key] = {
            "rate": round(g["solved"] / max(g["total"], 1), 3),
            "total": g["total"],
            "solved": g["solved"],
        }

    return {
        "tag_count_vs_solve_rate": tag_count_rates,
        "oeis_count_vs_solve_rate": oeis_count_rates,
        "quartile_solve_rates": quartile_rates,
        "formalization_paradox": formalization_rates,
        "quartile_boundaries": {"Q1": q25, "Q2": q50, "Q3": q75},
    }


# ═══════════════════════════════════════════════════════════════════
# 4. Network Motifs — structural patterns in the conjecture graph
# ═══════════════════════════════════════════════════════════════════

def network_motifs(problems: List[Dict]) -> Dict[str, Any]:
    """
    Count structural motifs in the problem similarity network.

    Motifs:
    - Triangles: three mutually related problems (potential theory)
    - Stars: one hub connected to many leaves (central problem)
    - Bridges: edges whose removal disconnects components (critical links)
    - Isolated components: disconnected problem groups
    """
    open_probs = [p for p in problems if _status(p) == "open"]

    # Build adjacency from tag overlap ≥ 2 and OEIS overlap
    adj = defaultdict(set)
    for p1, p2 in combinations(open_probs[:400], 2):
        n1, n2 = _number(p1), _number(p2)
        t1, t2 = _tags(p1), _tags(p2)
        shared_oeis = set(_oeis(p1)) & set(_oeis(p2))
        tag_overlap = len(t1 & t2)

        if len(shared_oeis) >= 1 or tag_overlap >= 3:
            adj[n1].add(n2)
            adj[n2].add(n1)

    all_nodes = set()
    for n in adj:
        all_nodes.add(n)
        all_nodes |= adj[n]

    # Count triangles
    triangle_count = 0
    triangle_examples = []
    nodes_list = sorted(all_nodes)[:300]  # limit for performance

    for i, u in enumerate(nodes_list):
        for v in sorted(adj.get(u, set())):
            if v <= u:
                continue
            common = adj.get(u, set()) & adj.get(v, set())
            for w in common:
                if w > v:
                    triangle_count += 1
                    if len(triangle_examples) < 5:
                        triangle_examples.append((u, v, w))

    # Stars: nodes with degree ≥ 10
    degrees = {n: len(adj.get(n, set())) for n in all_nodes}
    stars = [(n, d) for n, d in degrees.items() if d >= 10]
    stars.sort(key=lambda x: -x[1])

    # Bridges (simplified): edges whose endpoints have few other connections
    bridge_candidates = []
    for u in list(adj.keys())[:200]:
        for v in adj[u]:
            if v > u:
                # If removing this edge would disconnect u or v
                u_other = len(adj[u]) - 1
                v_other = len(adj[v]) - 1
                if u_other <= 1 or v_other <= 1:
                    bridge_candidates.append({
                        "edge": (u, v),
                        "u_degree": len(adj[u]),
                        "v_degree": len(adj[v]),
                    })

    # Component analysis
    visited = set()
    components = []
    for node in all_nodes:
        if node not in visited:
            comp = set()
            stack = [node]
            while stack:
                n = stack.pop()
                if n in visited:
                    continue
                visited.add(n)
                comp.add(n)
                stack.extend(adj.get(n, set()) - visited)
            components.append(comp)

    components.sort(key=lambda c: -len(c))

    # Degree distribution statistics
    degree_values = sorted(degrees.values(), reverse=True) if degrees else [0]
    max_degree = degree_values[0]
    median_degree = degree_values[len(degree_values) // 2]
    mean_degree = sum(degree_values) / max(len(degree_values), 1)

    return {
        "num_nodes": len(all_nodes),
        "num_edges": sum(len(v) for v in adj.values()) // 2,
        "triangle_count": triangle_count,
        "triangle_examples": triangle_examples[:5],
        "star_nodes": stars[:10],
        "bridge_count": len(bridge_candidates),
        "bridge_examples": bridge_candidates[:5],
        "num_components": len(components),
        "largest_component": len(components[0]) if components else 0,
        "component_sizes": [len(c) for c in components[:10]],
        "degree_stats": {
            "max": max_degree,
            "median": median_degree,
            "mean": round(mean_degree, 1),
        },
    }


# ═══════════════════════════════════════════════════════════════════
# 5. Problem DNA — structural fingerprinting
# ═══════════════════════════════════════════════════════════════════

def problem_dna(problems: List[Dict]) -> Dict[str, Any]:
    """
    Encode each problem as a structural fingerprint ("DNA") and discover
    which fingerprint patterns predict solvability.

    DNA components:
    - Tag signature (binary vector)
    - OEIS connectivity (number of sequences)
    - Prize signal (log scale)
    - Community membership
    - Formalization status
    """
    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    tag_idx = {t: i for i, t in enumerate(all_tags)}

    solved_dna = []
    open_dna = []

    for p in problems:
        tags = _tags(p)
        dna = {
            "number": _number(p),
            "n_tags": len(tags),
            "n_oeis": len(_oeis(p)),
            "prize_log": math.log1p(_prize(p)),
            "formalized": bool(p.get("formalized", {}).get("lean", False) or
                             p.get("formalized", {}).get("isabelle", False)),
            "tag_vector": [1 if t in tags else 0 for t in all_tags],
        }

        if _status(p) in ("proved", "disproved"):
            solved_dna.append(dna)
        elif _status(p) == "open":
            open_dna.append(dna)

    # Compute average DNA profiles for solved vs open
    def avg_profile(dna_list):
        if not dna_list:
            return {}
        return {
            "avg_tags": round(np.mean([d["n_tags"] for d in dna_list]), 2),
            "avg_oeis": round(np.mean([d["n_oeis"] for d in dna_list]), 2),
            "avg_prize_log": round(np.mean([d["prize_log"] for d in dna_list]), 2),
            "formalized_pct": round(np.mean([d["formalized"] for d in dna_list]) * 100, 1),
            "count": len(dna_list),
        }

    solved_profile = avg_profile(solved_dna)
    open_profile = avg_profile(open_dna)

    # Tag importance: which tags appear more in solved vs open?
    tag_enrichment = {}
    for i, tag in enumerate(all_tags):
        solved_frac = np.mean([d["tag_vector"][i] for d in solved_dna]) if solved_dna else 0
        open_frac = np.mean([d["tag_vector"][i] for d in open_dna]) if open_dna else 0
        if open_frac > 0:
            enrichment = solved_frac / open_frac
        elif solved_frac > 0:
            enrichment = float("inf")
        else:
            enrichment = 1.0
        tag_enrichment[tag] = {
            "solved_frac": round(solved_frac, 3),
            "open_frac": round(open_frac, 3),
            "enrichment": round(enrichment, 3) if enrichment != float("inf") else 999.0,
        }

    # Sort by enrichment
    solvability_tags = sorted(tag_enrichment.items(), key=lambda x: -x[1]["enrichment"])
    difficulty_tags = sorted(tag_enrichment.items(), key=lambda x: x[1]["enrichment"])

    return {
        "solved_profile": solved_profile,
        "open_profile": open_profile,
        "solvability_indicators": solvability_tags[:10],
        "difficulty_indicators": difficulty_tags[:10],
        "total_tags": len(all_tags),
    }


# ═══════════════════════════════════════════════════════════════════
# 6. Anomaly Detection — surprising outcomes
# ═══════════════════════════════════════════════════════════════════

def anomaly_detection(problems: List[Dict]) -> Dict[str, Any]:
    """
    Find problems whose outcome doesn't match their structural prediction.

    - "Should be solved" (high vulnerability, still open): missed opportunities
    - "Surprisingly solved" (low connectivity, yet resolved): hidden insight
    - "Prize orphans" (prize but no technique match): unclaimed rewards
    """
    from synthesis import compute_vulnerability_scores

    vuln_scores = compute_vulnerability_scores(problems)
    vuln_by_num = {v["number"]: v for v in vuln_scores}

    # Build solved problem set
    solved_nums = {_number(p) for p in problems if _status(p) in ("proved", "disproved")}

    # "Should be solved": top vulnerability but still open
    should_be_solved = [v for v in vuln_scores[:50] if v["number"] not in solved_nums][:10]

    # "Surprisingly solved": solved problems that have low-solvability tags
    tag_solve_rates = {}
    tag_counts = Counter()
    tag_solved_counts = Counter()
    for p in problems:
        for t in _tags(p):
            tag_counts[t] += 1
            if _status(p) in ("proved", "disproved"):
                tag_solved_counts[t] += 1
    for t in tag_counts:
        tag_solve_rates[t] = tag_solved_counts.get(t, 0) / tag_counts[t]

    surprising_solved = []
    for p in problems:
        if _status(p) not in ("proved", "disproved"):
            continue
        tags = _tags(p)
        if not tags:
            continue
        avg_rate = np.mean([tag_solve_rates.get(t, 0) for t in tags])
        if avg_rate < 0.25:  # tags with < 25% solve rate
            surprising_solved.append({
                "number": _number(p),
                "tags": sorted(tags),
                "avg_tag_solve_rate": round(avg_rate, 3),
            })

    surprising_solved.sort(key=lambda x: x["avg_tag_solve_rate"])

    # "Prize orphans": open problems with prize but low technique match
    prize_orphans = []
    for v in vuln_scores:
        if v["prize"] > 0 and v["technique_match"] == 0:
            prize_orphans.append({
                "number": v["number"],
                "prize": v["prize"],
                "tags": v["tags"],
                "vulnerability": v["vulnerability"],
            })

    prize_orphans.sort(key=lambda x: -x["prize"])

    return {
        "should_be_solved": should_be_solved[:10],
        "surprisingly_solved": surprising_solved[:10],
        "prize_orphans": prize_orphans[:10],
        "total_anomalies": len(should_be_solved) + len(surprising_solved) + len(prize_orphans),
    }


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(waves, coevol, decay, motifs, dna, anomalies) -> str:
    lines = []
    lines.append("# Meta-Patterns in Erdős Problems")
    lines.append("")
    lines.append("Higher-order patterns discovered by analyzing patterns of patterns.")
    lines.append("")

    # Section 1: Resolution Waves
    lines.append("## 1. Resolution Waves")
    lines.append("")
    lines.append(f"- Problems with resolution dates: {waves['solved_with_dates']}")
    if waves.get("year_range"):
        lines.append(f"- Year range: {waves['year_range'][0]}–{waves['year_range'][1]}")
    lines.append(f"- Mean solutions per year: {waves.get('mean_per_year', 'N/A')}")
    if waves.get("peak_year"):
        lines.append(f"- Peak year: {waves['peak_year']} ({waves['peak_count']} solutions)")
    lines.append("")

    if waves.get("burst_years"):
        lines.append("### Burst Years (>2σ above mean)")
        lines.append("")
        for year, count in waves["burst_years"]:
            lines.append(f"- **{year}**: {count} solutions")
        lines.append("")

    if waves.get("tag_waves"):
        lines.append("### Tag-Specific Resolution Peaks")
        lines.append("")
        lines.append("| Tag | Total Solved | Peak Year | Peak Count | Span |")
        lines.append("|-----|-------------|-----------|------------|------|")
        for tag, info in sorted(waves["tag_waves"].items(), key=lambda x: -x[1]["total_solved"]):
            lines.append(f"| {tag} | {info['total_solved']} | {info['peak_year']} | {info['peak_count']} | {info['span']}y |")
        lines.append("")

    # Section 2: Tag Co-Evolution
    lines.append("## 2. Tag Co-Evolution")
    lines.append("")
    lines.append(f"Analyzed {coevol['num_pairs_analyzed']} tag pairs (≥3 occurrences)")
    lines.append("")

    lines.append("### Easiest Tag Pairs (highest solve rate)")
    lines.append("")
    lines.append("| Tags | Solve Rate | Solved/Total |")
    lines.append("|------|-----------|-------------|")
    for pair, info in coevol["easiest_pairs"][:8]:
        lines.append(f"| {pair[0]} + {pair[1]} | {info['solve_rate']:.1%} | {info['solved']}/{info['total']} |")
    lines.append("")

    lines.append("### Hardest Tag Pairs (lowest solve rate)")
    lines.append("")
    lines.append("| Tags | Solve Rate | Solved/Total |")
    lines.append("|------|-----------|-------------|")
    for pair, info in coevol["hardest_pairs"][:8]:
        lines.append(f"| {pair[0]} + {pair[1]} | {info['solve_rate']:.1%} | {info['solved']}/{info['total']} |")
    lines.append("")

    if coevol.get("strongest_synergies"):
        lines.append("### Tag Pairs with Higher-Than-Average Solve Rates")
        lines.append("")
        lines.append("NOTE: 'Synergy' is the raw difference between joint solve rate and")
        lines.append("average of individual tag rates. No statistical testing applied.")
        lines.append("")
        lines.append("| Tags | Actual Rate | Avg Individual | Difference |")
        lines.append("|------|-----------|----------------|------------|")
        for s in coevol["strongest_synergies"][:8]:
            lines.append(f"| {s['pair'][0]} + {s['pair'][1]} | {s['actual_rate']:.1%} | {s['expected_rate']:.1%} | {s['synergy']:+.3f} |")
        lines.append("")

    # Section 3: Difficulty Decay
    lines.append("## 3. Difficulty Structure")
    lines.append("")

    lines.append("### Tag Count vs Solve Rate")
    lines.append("")
    lines.append("| Tags | Solve Rate |")
    lines.append("|------|-----------|")
    for n_tags, rate in sorted(decay["tag_count_vs_solve_rate"].items()):
        label = f"{n_tags}+" if n_tags == 5 else str(n_tags)
        lines.append(f"| {label} | {rate:.1%} |")
    lines.append("")

    lines.append("### Problem Age vs Solve Rate")
    lines.append("")
    lines.append("| Quartile | Solve Rate | Total | Solved |")
    lines.append("|----------|-----------|-------|--------|")
    for q, info in sorted(decay["quartile_solve_rates"].items()):
        lines.append(f"| {q} | {info['rate']:.1%} | {info['total']} | {info['solved']} |")
    lines.append("")

    lines.append("### Formalization Paradox")
    lines.append("")
    for key, info in decay["formalization_paradox"].items():
        label = "Formalized" if key == "formalized" else "Not formalized"
        lines.append(f"- **{label}**: {info['rate']:.1%} solved ({info['solved']}/{info['total']})")
    lines.append("")

    # Section 4: Network Motifs
    lines.append("## 4. Network Structure")
    lines.append("")
    lines.append(f"- Nodes: {motifs['num_nodes']}")
    lines.append(f"- Edges: {motifs['num_edges']}")
    lines.append(f"- Triangles: {motifs['triangle_count']}")
    lines.append(f"- Star nodes (degree ≥ 10): {len(motifs['star_nodes'])}")
    lines.append(f"- Bridge edges: {motifs['bridge_count']}")
    lines.append(f"- Components: {motifs['num_components']}")
    lines.append(f"- Largest component: {motifs['largest_component']}")
    lines.append("")

    stats = motifs["degree_stats"]
    lines.append(f"Degree distribution: max={stats['max']}, median={stats['median']}, mean={stats['mean']}")
    lines.append("")

    if motifs["star_nodes"]:
        lines.append("### Hub Nodes")
        lines.append("")
        for num, deg in motifs["star_nodes"][:5]:
            lines.append(f"- **#{num}**: degree {deg}")
        lines.append("")

    # Section 5: Problem DNA
    lines.append("## 5. Problem DNA Profiles")
    lines.append("")
    lines.append("### Solved vs Open Averages")
    lines.append("")
    lines.append("| Feature | Solved | Open |")
    lines.append("|---------|--------|------|")
    sp, op = dna["solved_profile"], dna["open_profile"]
    if sp and op:
        lines.append(f"| Avg tags | {sp['avg_tags']} | {op['avg_tags']} |")
        lines.append(f"| Avg OEIS | {sp['avg_oeis']} | {op['avg_oeis']} |")
        lines.append(f"| Avg prize (log) | {sp['avg_prize_log']} | {op['avg_prize_log']} |")
        lines.append(f"| Formalized % | {sp['formalized_pct']}% | {op['formalized_pct']}% |")
    lines.append("")

    if dna.get("solvability_indicators"):
        lines.append("### Tags Most Enriched in Solved Problems")
        lines.append("")
        for tag, info in dna["solvability_indicators"][:8]:
            if info["enrichment"] < 100:
                lines.append(f"- **{tag}**: {info['enrichment']:.1f}× enriched (solved: {info['solved_frac']:.1%}, open: {info['open_frac']:.1%})")
        lines.append("")

    if dna.get("difficulty_indicators"):
        lines.append("### Tags Most Enriched in Open Problems")
        lines.append("")
        for tag, info in dna["difficulty_indicators"][:8]:
            if info["enrichment"] < 100 and info["open_frac"] > 0:
                lines.append(f"- **{tag}**: {info['enrichment']:.2f}× (solved: {info['solved_frac']:.1%}, open: {info['open_frac']:.1%})")
        lines.append("")

    # Section 6: Anomalies
    lines.append("## 6. Anomalies")
    lines.append("")

    if anomalies.get("should_be_solved"):
        lines.append("### Should Be Solved (high vulnerability, still open)")
        lines.append("")
        for a in anomalies["should_be_solved"][:5]:
            lines.append(f"- **#{a['number']}** (v={a['vulnerability']:.3f}): {', '.join(a['tags'][:3])}")
        lines.append("")

    if anomalies.get("surprisingly_solved"):
        lines.append("### Surprisingly Solved (low-solvability tags)")
        lines.append("")
        for a in anomalies["surprisingly_solved"][:5]:
            lines.append(f"- **#{a['number']}**: avg tag rate = {a['avg_tag_solve_rate']:.1%}")
        lines.append("")

    if anomalies.get("prize_orphans"):
        lines.append("### Prize Orphans (has prize, no technique match)")
        lines.append("")
        for a in anomalies["prize_orphans"][:5]:
            lines.append(f"- **#{a['number']}** (${a['prize']:.0f}): {', '.join(a['tags'][:3])}")
        lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("META-PATTERN MINING")
    print("=" * 70)

    problems = load_problems()
    print(f"Loaded {len(problems)} problems")

    print("\n1. Analyzing resolution waves...")
    waves = resolution_waves(problems)
    print(f"   {waves['solved_with_dates']} dated solutions, {waves['wave_count']} burst years")

    print("\n2. Computing tag co-evolution...")
    coevol = tag_coevolution(problems)
    print(f"   {coevol['num_pairs_analyzed']} tag pairs analyzed")

    print("\n3. Computing difficulty decay curves...")
    decay = difficulty_decay(problems)
    print(f"   Tag count rates: {decay['tag_count_vs_solve_rate']}")

    print("\n4. Counting network motifs...")
    motifs = network_motifs(problems)
    print(f"   {motifs['triangle_count']} triangles, {len(motifs['star_nodes'])} stars")

    print("\n5. Building problem DNA profiles...")
    dna = problem_dna(problems)
    print(f"   {dna['total_tags']} tags in vocabulary")

    print("\n6. Detecting anomalies...")
    anomalies = anomaly_detection(problems)
    print(f"   {anomalies['total_anomalies']} anomalies found")

    print("\n7. Generating report...")
    report = generate_report(waves, coevol, decay, motifs, dna, anomalies)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"   Saved to {REPORT_PATH}")

    print("\n" + "=" * 70)
    print("META-PATTERN MINING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
