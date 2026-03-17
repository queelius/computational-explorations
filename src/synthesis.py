#!/usr/bin/env python3
"""
synthesis.py — Cross-cutting synthesis of all Erdős research workstreams.

Combines insights from:
  - deep_analysis.py     (OEIS clusters, difficulty classifier, tag communities)
  - relationship_discovery.py (technique transfer, tag gaps, structural isomorphism)
  - attack_problems.py   (computational experiments on 15 problems)
  - new_attacks.py        (Sidon, coprime, AP-free, Schur computations)

Produces SECOND-ORDER discoveries:
  1. Technique Transfer Effectiveness: which solved→open transfers have strongest evidence?
  2. Problem Vulnerability Score: multi-signal fusion for "most likely to fall next"
  3. Duality Detection: problem pairs with complementary structure
  4. Conjecture Network: implications and dependencies among open conjectures
  5. Gap-Bridging Proposals: concrete problems at unexplored intersections
  6. Resolution Cascade Predictor: which problem's resolution would unlock others?

Output: docs/synthesis_report.md
"""

import math
import yaml
import numpy as np
from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional
from functools import lru_cache

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "synthesis_report.md"


# ═══════════════════════════════════════════════════════════════════
# Data Loading
# ═══════════════════════════════════════════════════════════════════

def load_problems() -> List[Dict]:
    """Load the full Erdős problems database."""
    with open(DATA_PATH) as f:
        return yaml.safe_load(f)


def problem_status(p: Dict) -> str:
    """Extract status string from a problem dict."""
    return p.get("status", {}).get("state", "unknown")


def problem_tags(p: Dict) -> Set[str]:
    """Extract tags from a problem dict."""
    return set(p.get("tags", []))


def problem_oeis(p: Dict) -> List[str]:
    """Extract OEIS references from a problem dict."""
    return p.get("oeis", [])


def problem_number(p: Dict) -> int:
    """Extract problem number."""
    return p.get("number", 0)


def parse_prize(p: Dict) -> float:
    """Extract prize value in USD."""
    pz = p.get("prize", "no")
    if not pz or pz == "no":
        return 0.0
    import re
    nums = re.findall(r"[\d,]+", str(pz))
    if nums:
        val = float(nums[0].replace(",", ""))
        if "\u00a3" in str(pz):
            val *= 1.27
        return val
    return 0.0


# ═══════════════════════════════════════════════════════════════════
# 1. Problem Vulnerability Score (multi-signal fusion)
# ═══════════════════════════════════════════════════════════════════

def compute_vulnerability_scores(problems: List[Dict]) -> List[Dict]:
    """
    Combine multiple signals into a composite vulnerability score.

    Signals:
      - Tag solvability: what fraction of problems with these tags are solved?
      - OEIS connectivity: problems sharing OEIS with solved ones get bonus
      - Technique density: how many of our techniques apply?
      - Community position: central problems in solved clusters are vulnerable
      - Analog proximity: solved analogs exist?
    """
    open_probs = [p for p in problems if problem_status(p) == "open"]
    solved_probs = [p for p in problems if problem_status(p) in ("proved", "disproved")]

    # Signal 1: Tag solvability rate
    tag_solve_rate = _compute_tag_solve_rates(problems)

    # Signal 2: OEIS bridge to solved problems
    oeis_solved = defaultdict(set)
    for p in solved_probs:
        for seq in problem_oeis(p):
            oeis_solved[seq].add(problem_number(p))

    # Signal 3: Our technique coverage
    technique_map = _technique_coverage()

    # Signal 4: Tag co-occurrence density with solved problems
    solved_tags = Counter()
    for p in solved_probs:
        for t in problem_tags(p):
            solved_tags[t] += 1

    results = []
    for p in open_probs:
        tags = problem_tags(p)
        num = problem_number(p)

        # S1: Average tag solve rate
        rates = [tag_solve_rate.get(t, 0.0) for t in tags]
        s1 = sum(rates) / max(len(rates), 1)

        # S2: OEIS bridges to solved problems
        bridges = set()
        for seq in problem_oeis(p):
            bridges |= oeis_solved.get(seq, set())
        s2 = min(len(bridges) / 5.0, 1.0)  # cap at 5 bridges

        # S3: Technique coverage
        tech_matches = 0
        for tech_name, tech_tags in technique_map.items():
            overlap = tags & tech_tags
            if overlap == tech_tags:
                tech_matches += 2
            elif overlap:
                tech_matches += 1
        s3 = min(tech_matches / 6.0, 1.0)

        # S4: Tag density with solved problems
        solved_density = sum(solved_tags.get(t, 0) for t in tags) / max(len(tags) * 100, 1)
        s4 = min(solved_density, 1.0)

        # S5: Prize as inverse difficulty proxy
        prize = parse_prize(p)
        s5 = 1.0 / (1.0 + prize / 500.0)  # high prize → lower vulnerability

        # Composite score (weighted)
        score = 0.3 * s1 + 0.2 * s2 + 0.25 * s3 + 0.15 * s4 + 0.1 * s5

        results.append({
            "number": num,
            "tags": sorted(tags),
            "vulnerability": round(score, 4),
            "tag_solvability": round(s1, 4),
            "oeis_bridges": len(bridges),
            "technique_match": tech_matches,
            "solved_density": round(s4, 4),
            "prize": prize,
        })

    results.sort(key=lambda x: -x["vulnerability"])
    return results


def _compute_tag_solve_rates(problems: List[Dict]) -> Dict[str, float]:
    """Compute fraction of problems with each tag that are solved."""
    tag_total = Counter()
    tag_solved = Counter()
    for p in problems:
        state = problem_status(p)
        for t in problem_tags(p):
            tag_total[t] += 1
            if state in ("proved", "disproved"):
                tag_solved[t] += 1
    return {t: tag_solved[t] / tag_total[t] for t in tag_total if tag_total[t] > 0}


def _technique_coverage() -> Dict[str, Set[str]]:
    """Map our technique names to the tag sets they require."""
    return {
        "fourier_density": {"number theory", "additive combinatorics"},
        "coprime_cycle": {"graph theory", "cycles"},
        "sidon": {"sidon sets"},
        "prime_mobius": {"primes", "number theory"},
        "ramsey": {"ramsey theory"},
        "chromatic": {"chromatic number"},
        "additive_basis": {"additive basis"},
        "primitive_sets": {"primitive sets"},
        "arithmetic_prog": {"arithmetic progressions"},
        "graph_turan": {"graph theory", "turan number"},
    }


# ═══════════════════════════════════════════════════════════════════
# 2. Duality Detection
# ═══════════════════════════════════════════════════════════════════

def detect_dualities(problems: List[Dict]) -> List[Dict]:
    """
    Find problem pairs with complementary/dual structure:
    - Same tags but one asks for upper bound, other for lower
    - One proved, one open — possible technique transfer
    - Shared OEIS but different tag domains (cross-domain bridge)

    Returns list of duality relationships.
    """
    by_number = {problem_number(p): p for p in problems}
    open_probs = [p for p in problems if problem_status(p) == "open"]
    solved_probs = [p for p in problems if problem_status(p) in ("proved", "disproved")]

    dualities = []

    # Type 1: Same-tag dualities (open pairs)
    for p1, p2 in combinations(open_probs, 2):
        tags1 = problem_tags(p1)
        tags2 = problem_tags(p2)
        if not tags1 or not tags2:
            continue
        jaccard = len(tags1 & tags2) / len(tags1 | tags2)
        if jaccard >= 0.8 and len(tags1 & tags2) >= 2:
            shared_oeis = set(problem_oeis(p1)) & set(problem_oeis(p2))
            if shared_oeis:
                dualities.append({
                    "type": "twin_problems",
                    "problems": (problem_number(p1), problem_number(p2)),
                    "jaccard": round(jaccard, 3),
                    "shared_tags": sorted(tags1 & tags2),
                    "shared_oeis": sorted(shared_oeis),
                })

    # Type 2: Solved-open bridges (technique transfer candidates)
    for sp in solved_probs[:200]:  # limit for performance
        sp_tags = problem_tags(sp)
        if len(sp_tags) < 2:
            continue
        for op in open_probs:
            op_tags = problem_tags(op)
            overlap = sp_tags & op_tags
            if len(overlap) >= 2 and overlap != sp_tags:
                # Partial overlap — technique transfer candidate
                unique_solved = sp_tags - op_tags
                unique_open = op_tags - sp_tags
                if unique_solved and unique_open:
                    dualities.append({
                        "type": "transfer_bridge",
                        "solved": problem_number(sp),
                        "open": problem_number(op),
                        "shared": sorted(overlap),
                        "solved_unique": sorted(unique_solved),
                        "open_unique": sorted(unique_open),
                    })

    # Type 3: Cross-domain OEIS bridges
    oeis_map = defaultdict(list)
    for p in problems:
        for seq in problem_oeis(p):
            oeis_map[seq].append(p)

    for seq, ps in oeis_map.items():
        if len(ps) < 2:
            continue
        all_tags = [problem_tags(p) for p in ps]
        tag_union = set().union(*all_tags)
        # Check if they span different domains
        domains = set()
        for tag_set in all_tags:
            if "number theory" in tag_set:
                domains.add("number_theory")
            if "graph theory" in tag_set:
                domains.add("graph_theory")
            if "geometry" in tag_set:
                domains.add("geometry")
            if "ramsey theory" in tag_set:
                domains.add("ramsey")
            if "additive combinatorics" in tag_set:
                domains.add("additive_comb")
        if len(domains) >= 2:
            dualities.append({
                "type": "cross_domain_oeis",
                "oeis": seq,
                "problems": [problem_number(p) for p in ps],
                "domains": sorted(domains),
                "statuses": [problem_status(p) for p in ps],
            })

    # Deduplicate transfer bridges — keep only top by uniqueness
    transfer_bridges = [d for d in dualities if d["type"] == "transfer_bridge"]
    seen = set()
    deduped_bridges = []
    for b in transfer_bridges:
        key = (b["solved"], b["open"])
        if key not in seen:
            seen.add(key)
            deduped_bridges.append(b)
    # Limit
    deduped_bridges = deduped_bridges[:50]
    dualities = [d for d in dualities if d["type"] != "transfer_bridge"] + deduped_bridges

    return dualities


# ═══════════════════════════════════════════════════════════════════
# 3. Conjecture Network
# ═══════════════════════════════════════════════════════════════════

def build_conjecture_network(problems: List[Dict]) -> Dict[str, Any]:
    """
    Build a dependency/implication network among open conjectures.

    Edges represent:
    - OEIS overlap (same sequence → likely related)
    - Tag overlap ≥ 2 (same domain)
    - Prize inheritance (harder problem implies easier subproblems)

    Returns graph statistics and key structural features.
    """
    open_probs = [p for p in problems if problem_status(p) == "open"]

    # Build adjacency from OEIS overlap
    oeis_edges = []
    oeis_map = defaultdict(set)
    for p in open_probs:
        for seq in problem_oeis(p):
            oeis_map[seq].add(problem_number(p))

    for seq, nums in oeis_map.items():
        if len(nums) >= 2:
            for a, b in combinations(sorted(nums), 2):
                oeis_edges.append((a, b, {"type": "oeis", "seq": seq}))

    # Build adjacency from tag overlap
    tag_edges = []
    for p1, p2 in combinations(open_probs[:300], 2):  # limit
        t1 = problem_tags(p1)
        t2 = problem_tags(p2)
        overlap = t1 & t2
        if len(overlap) >= 3:
            tag_edges.append((problem_number(p1), problem_number(p2),
                            {"type": "tag", "shared": len(overlap)}))

    # Build graph
    all_nodes = {problem_number(p) for p in open_probs}
    edge_set = set()
    for a, b, _ in oeis_edges + tag_edges:
        if (a, b) not in edge_set:
            edge_set.add((a, b))

    # Compute connected components
    adj = defaultdict(set)
    for a, b in edge_set:
        adj[a].add(b)
        adj[b].add(a)

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
                stack.extend(adj[n] - visited)
            components.append(comp)

    components.sort(key=lambda c: -len(c))

    # Degree distribution
    degrees = {n: len(adj[n]) for n in all_nodes}
    high_degree = sorted(degrees.items(), key=lambda x: -x[1])[:20]

    # Hub problems (degree ≥ 5)
    hubs = [(n, d) for n, d in degrees.items() if d >= 5]

    return {
        "num_nodes": len(all_nodes),
        "num_edges": len(edge_set),
        "num_components": len(components),
        "largest_component": len(components[0]) if components else 0,
        "isolated_nodes": sum(1 for c in components if len(c) == 1),
        "hub_problems": sorted(hubs, key=lambda x: -x[1])[:15],
        "high_degree": high_degree,
        "component_sizes": [len(c) for c in components[:10]],
    }


# ═══════════════════════════════════════════════════════════════════
# 4. Resolution Cascade Predictor
# ═══════════════════════════════════════════════════════════════════

def resolution_cascade(problems: List[Dict]) -> List[Dict]:
    """
    Predict which problem's resolution would unlock the most other problems.

    Uses OEIS overlap + tag overlap to measure "influence radius":
    if problem X is solved, how many problems Y become more tractable
    (because X shares structure with Y)?
    """
    open_probs = [p for p in problems if problem_status(p) == "open"]
    by_num = {problem_number(p): p for p in open_probs}

    # Build influence graph: directed edges X → Y where solving X helps Y
    influence = defaultdict(set)
    for p1, p2 in combinations(open_probs[:400], 2):
        n1 = problem_number(p1)
        n2 = problem_number(p2)
        t1 = problem_tags(p1)
        t2 = problem_tags(p2)
        shared_oeis = set(problem_oeis(p1)) & set(problem_oeis(p2))
        tag_overlap = len(t1 & t2)

        # Influence strength
        strength = len(shared_oeis) * 2 + max(0, tag_overlap - 1)
        if strength >= 2:
            influence[n1].add(n2)
            influence[n2].add(n1)

    # Score each problem by influence radius
    cascade_scores = []
    for p in open_probs:
        num = problem_number(p)
        direct = len(influence.get(num, set()))
        # Second-order: problems influenced by those I influence
        indirect = set()
        for n2 in influence.get(num, set()):
            indirect |= influence.get(n2, set())
        indirect -= {num}
        indirect -= influence.get(num, set())

        cascade_scores.append({
            "number": num,
            "tags": sorted(problem_tags(p)),
            "direct_influence": direct,
            "indirect_influence": len(indirect),
            "total_cascade": direct + len(indirect) // 2,
            "prize": parse_prize(p),
        })

    cascade_scores.sort(key=lambda x: -x["total_cascade"])
    return cascade_scores


# ═══════════════════════════════════════════════════════════════════
# 5. Gap-Bridging Proposals
# ═══════════════════════════════════════════════════════════════════

def gap_bridging_proposals(problems: List[Dict]) -> List[Dict]:
    """
    Generate concrete research directions at unexplored intersections.

    Strategy: find pairs of solved problems in different domains whose
    combined tags have NO corresponding open problem.
    """
    solved = [p for p in problems if problem_status(p) in ("proved", "disproved")]
    open_set = [p for p in problems if problem_status(p) == "open"]

    # Build tag-set signatures for open problems
    open_signatures = set()
    for p in open_set:
        tags = frozenset(problem_tags(p))
        if len(tags) >= 2:
            open_signatures.add(tags)

    # Find solved-solved tag merges that are unexplored
    proposals = []
    major_domains = {
        "number theory", "graph theory", "geometry", "ramsey theory",
        "additive combinatorics", "combinatorics", "analysis",
    }

    solved_by_domain = defaultdict(list)
    for p in solved:
        for t in problem_tags(p) & major_domains:
            solved_by_domain[t].append(p)

    domains = sorted(solved_by_domain.keys())
    for d1, d2 in combinations(domains, 2):
        # Check if there are few open problems at this intersection
        intersection_open = [
            p for p in open_set
            if d1 in problem_tags(p) and d2 in problem_tags(p)
        ]
        if len(intersection_open) < 3:
            # Potentially unexplored territory
            example_solved_1 = solved_by_domain[d1][:3]
            example_solved_2 = solved_by_domain[d2][:3]

            # Generate proposal from technique combination
            techniques_1 = set()
            for p in example_solved_1:
                techniques_1 |= problem_tags(p)
            techniques_2 = set()
            for p in example_solved_2:
                techniques_2 |= problem_tags(p)

            proposals.append({
                "domain_pair": (d1, d2),
                "existing_open": len(intersection_open),
                "example_open": [problem_number(p) for p in intersection_open[:3]],
                "techniques_from_d1": sorted(techniques_1 - major_domains)[:5],
                "techniques_from_d2": sorted(techniques_2 - major_domains)[:5],
                "proposal": f"Apply {d1} methods to {d2} problems or vice versa",
            })

    proposals.sort(key=lambda x: x["existing_open"])
    return proposals


# ═══════════════════════════════════════════════════════════════════
# 6. Meta-Pattern: Difficulty Taxonomy
# ═══════════════════════════════════════════════════════════════════

def difficulty_taxonomy(problems: List[Dict]) -> Dict[str, Any]:
    """
    Classify problems into difficulty tiers based on multiple signals.

    Tiers:
    - Tier 1 (Ripe): High tag-solve-rate, multiple technique matches, low prize
    - Tier 2 (Accessible): Moderate signals, some technique match
    - Tier 3 (Hard): Low solve rate, high prize, few technique matches
    - Tier 4 (Fortress): Very low solve rate, $1000+ prize, no technique match
    """
    vuln = compute_vulnerability_scores(problems)
    open_probs = {problem_number(p): p for p in problems if problem_status(p) == "open"}

    tiers = {"ripe": [], "accessible": [], "hard": [], "fortress": []}

    for v in vuln:
        num = v["number"]
        score = v["vulnerability"]
        prize = v["prize"]

        if score >= 0.4 and prize <= 100:
            tier = "ripe"
        elif score >= 0.25 or (score >= 0.2 and prize <= 500):
            tier = "accessible"
        elif prize >= 1000 or score < 0.1:
            tier = "fortress"
        else:
            tier = "hard"

        tiers[tier].append({
            "number": num,
            "tags": v["tags"],
            "vulnerability": score,
            "prize": prize,
        })

    summary = {
        "tier_counts": {t: len(ps) for t, ps in tiers.items()},
        "ripe_top10": tiers["ripe"][:10],
        "fortress_top10": tiers["fortress"][:10],
        "accessible_sample": tiers["accessible"][:10],
    }
    return summary


# ═══════════════════════════════════════════════════════════════════
# 7. Technique Effectiveness Analysis
# ═══════════════════════════════════════════════════════════════════

def technique_effectiveness(problems: List[Dict]) -> List[Dict]:
    """
    For each of our techniques, compute:
    - How many open problems it matches
    - What fraction of matched problems (across all statuses) are solved
    - Estimated "technique power" = solve_rate * coverage
    """
    tech_map = _technique_coverage()
    results = []

    for tech_name, required_tags in tech_map.items():
        matched_open = 0
        matched_solved = 0
        matched_total = 0
        total_prize = 0.0

        for p in problems:
            tags = problem_tags(p)
            overlap = tags & required_tags
            if overlap == required_tags or (len(required_tags) == 1 and overlap):
                matched_total += 1
                state = problem_status(p)
                if state == "open":
                    matched_open += 1
                    total_prize += parse_prize(p)
                elif state in ("proved", "disproved"):
                    matched_solved += 1

        solve_rate = matched_solved / max(matched_total, 1)
        power = solve_rate * matched_open

        results.append({
            "technique": tech_name,
            "required_tags": sorted(required_tags),
            "matched_total": matched_total,
            "matched_open": matched_open,
            "matched_solved": matched_solved,
            "solve_rate": round(solve_rate, 4),
            "power_score": round(power, 2),
            "total_prize_accessible": total_prize,
        })

    results.sort(key=lambda x: -x["power_score"])
    return results


# ═══════════════════════════════════════════════════════════════════
# 8. Problem Similarity Clusters
# ═══════════════════════════════════════════════════════════════════

def problem_similarity_clusters(problems: List[Dict], n_clusters: int = 8) -> Dict[str, Any]:
    """
    Cluster problems by tag+OEIS feature vectors using k-means-like approach.

    Returns cluster assignments and cluster characteristics.
    """
    # Build feature vectors
    all_tags = sorted(set(t for p in problems for t in problem_tags(p)))
    all_oeis = sorted(set(s for p in problems for s in problem_oeis(p)))
    tag_idx = {t: i for i, t in enumerate(all_tags)}
    oeis_idx = {s: i + len(all_tags) for i, s in enumerate(all_oeis[:200])}  # cap OEIS
    dim = len(all_tags) + min(len(all_oeis), 200)

    vectors = []
    prob_nums = []
    for p in problems:
        vec = np.zeros(dim)
        for t in problem_tags(p):
            if t in tag_idx:
                vec[tag_idx[t]] = 1.0
        for s in problem_oeis(p):
            if s in oeis_idx:
                vec[oeis_idx[s]] = 0.5  # lower weight for OEIS
        vectors.append(vec)
        prob_nums.append(problem_number(p))

    X = np.array(vectors)

    # Simple k-means
    np.random.seed(42)
    n = len(X)
    if n < n_clusters:
        n_clusters = max(1, n)

    # Initialize centroids randomly
    indices = np.random.choice(n, n_clusters, replace=False)
    centroids = X[indices].copy()

    labels = np.zeros(n, dtype=int)
    for iteration in range(20):
        # Assign
        for i in range(n):
            dists = [np.linalg.norm(X[i] - centroids[k]) for k in range(n_clusters)]
            labels[i] = int(np.argmin(dists))
        # Update centroids
        new_centroids = np.zeros_like(centroids)
        for k in range(n_clusters):
            members = X[labels == k]
            if len(members) > 0:
                new_centroids[k] = members.mean(axis=0)
            else:
                new_centroids[k] = centroids[k]
        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids

    # Analyze clusters
    clusters = []
    for k in range(n_clusters):
        member_idx = [i for i in range(n) if labels[i] == k]
        member_problems = [problems[i] for i in member_idx]
        member_nums = [prob_nums[i] for i in member_idx]

        # Dominant tags
        tag_counts = Counter()
        for p in member_problems:
            for t in problem_tags(p):
                tag_counts[t] += 1

        # Status distribution
        status_counts = Counter(problem_status(p) for p in member_problems)

        # Average prize
        prizes = [parse_prize(p) for p in member_problems if parse_prize(p) > 0]

        clusters.append({
            "cluster_id": k,
            "size": len(member_idx),
            "dominant_tags": tag_counts.most_common(5),
            "status_dist": dict(status_counts),
            "open_count": status_counts.get("open", 0),
            "solved_count": status_counts.get("proved", 0) + status_counts.get("disproved", 0),
            "avg_prize": round(sum(prizes) / max(len(prizes), 1), 0) if prizes else 0,
            "sample_problems": member_nums[:5],
        })

    clusters.sort(key=lambda c: -c["size"])
    return {"n_clusters": n_clusters, "clusters": clusters}


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(
    vulnerability: List[Dict],
    dualities: List[Dict],
    network: Dict,
    cascade: List[Dict],
    proposals: List[Dict],
    taxonomy: Dict,
    effectiveness: List[Dict],
    clusters: Dict,
) -> str:
    """Generate the synthesis report."""
    lines = []
    lines.append("# Erdos Problems: Cross-Cutting Synthesis Report")
    lines.append("")
    lines.append("This report synthesizes findings from four independent research workstreams")
    lines.append("to discover second-order patterns and identify the most promising attack vectors.")
    lines.append("")

    # ── Section 1: Vulnerability Rankings ──
    lines.append("## 1. Problem Vulnerability Rankings")
    lines.append("")
    lines.append("Multi-signal fusion combining tag solvability, OEIS bridges, technique")
    lines.append("coverage, solved-problem density, and prize calibration.")
    lines.append("")
    lines.append("### Top 20 Most Vulnerable Open Problems")
    lines.append("")
    lines.append("| Rank | Problem | Vulnerability | Tag Solvability | OEIS Bridges | Tech Match | Prize |")
    lines.append("|------|---------|--------------|-----------------|--------------|-----------|-------|")
    for i, v in enumerate(vulnerability[:20]):
        prize = f"${v['prize']:.0f}" if v['prize'] > 0 else "-"
        lines.append(
            f"| {i+1} | #{v['number']} | {v['vulnerability']:.3f} | "
            f"{v['tag_solvability']:.3f} | {v['oeis_bridges']} | "
            f"{v['technique_match']} | {prize} |"
        )
    lines.append("")

    # ── Section 2: Difficulty Taxonomy ──
    lines.append("## 2. Difficulty Taxonomy")
    lines.append("")
    tc = taxonomy["tier_counts"]
    lines.append(f"- **Ripe** (high vulnerability, low prize): {tc.get('ripe', 0)} problems")
    lines.append(f"- **Accessible** (moderate signals): {tc.get('accessible', 0)} problems")
    lines.append(f"- **Hard** (low signals, moderate prize): {tc.get('hard', 0)} problems")
    lines.append(f"- **Fortress** (very hard, high prize): {tc.get('fortress', 0)} problems")
    lines.append("")

    lines.append("### Ripe Problems (Top 10)")
    lines.append("")
    for p in taxonomy.get("ripe_top10", []):
        tags = ", ".join(p["tags"][:3])
        lines.append(f"- **#{p['number']}** (v={p['vulnerability']:.3f}): {tags}")
    lines.append("")

    lines.append("### Fortress Problems (Top 10)")
    lines.append("")
    for p in taxonomy.get("fortress_top10", []):
        tags = ", ".join(p["tags"][:3])
        prize = f"${p['prize']:.0f}" if p['prize'] > 0 else "no prize"
        lines.append(f"- **#{p['number']}** (v={p['vulnerability']:.3f}, {prize}): {tags}")
    lines.append("")

    # ── Section 3: Technique Effectiveness ──
    lines.append("## 3. Technique Effectiveness")
    lines.append("")
    lines.append("| Technique | Matched Open | Matched Solved | Solve Rate | Power Score | Prize Pool |")
    lines.append("|-----------|-------------|----------------|------------|-------------|-----------|")
    for e in effectiveness:
        prize = f"${e['total_prize_accessible']:.0f}" if e['total_prize_accessible'] > 0 else "-"
        lines.append(
            f"| {e['technique']} | {e['matched_open']} | {e['matched_solved']} | "
            f"{e['solve_rate']:.3f} | {e['power_score']:.1f} | {prize} |"
        )
    lines.append("")

    # ── Section 4: Dualities ──
    lines.append("## 4. Problem Dualities")
    lines.append("")

    twin_dualities = [d for d in dualities if d["type"] == "twin_problems"]
    cross_dualities = [d for d in dualities if d["type"] == "cross_domain_oeis"]
    transfer_dualities = [d for d in dualities if d["type"] == "transfer_bridge"]

    lines.append(f"- **Twin problems** (same tags + shared OEIS): {len(twin_dualities)}")
    lines.append(f"- **Cross-domain OEIS bridges**: {len(cross_dualities)}")
    lines.append(f"- **Technique transfer candidates**: {len(transfer_dualities)}")
    lines.append("")

    if twin_dualities:
        lines.append("### Twin Problems (Top 10)")
        lines.append("")
        for d in twin_dualities[:10]:
            n1, n2 = d["problems"]
            tags = ", ".join(d["shared_tags"][:3])
            oeis = ", ".join(d["shared_oeis"][:2])
            lines.append(f"- #{n1} <-> #{n2}: {tags} (OEIS: {oeis})")
        lines.append("")

    if cross_dualities:
        lines.append("### Cross-Domain OEIS Bridges (Top 10)")
        lines.append("")
        for d in cross_dualities[:10]:
            domains = " x ".join(d["domains"])
            nums = ", ".join(f"#{n}" for n in d["problems"][:4])
            lines.append(f"- **{d['oeis']}**: {domains} ({nums})")
        lines.append("")

    # ── Section 5: Conjecture Network ──
    lines.append("## 5. Conjecture Network")
    lines.append("")
    lines.append(f"- Nodes (open problems): {network['num_nodes']}")
    lines.append(f"- Edges (structural similarity): {network['num_edges']}")
    lines.append(f"- Connected components: {network['num_components']}")
    lines.append(f"- Largest component: {network['largest_component']} problems")
    lines.append(f"- Isolated problems: {network['isolated_nodes']}")
    lines.append("")

    if network["hub_problems"]:
        lines.append("### Hub Problems (most connections)")
        lines.append("")
        for num, deg in network["hub_problems"][:10]:
            lines.append(f"- **#{num}**: {deg} connections")
        lines.append("")

    # ── Section 6: Resolution Cascade ──
    lines.append("## 6. Resolution Cascade Analysis")
    lines.append("")
    lines.append("Which problem's resolution would unlock the most others?")
    lines.append("")
    lines.append("| Rank | Problem | Direct Influence | Indirect | Total Cascade | Prize |")
    lines.append("|------|---------|-----------------|----------|---------------|-------|")
    for i, c in enumerate(cascade[:15]):
        prize = f"${c['prize']:.0f}" if c['prize'] > 0 else "-"
        lines.append(
            f"| {i+1} | #{c['number']} | {c['direct_influence']} | "
            f"{c['indirect_influence']} | {c['total_cascade']} | {prize} |"
        )
    lines.append("")

    # ── Section 7: Gap-Bridging Proposals ──
    lines.append("## 7. Gap-Bridging Research Proposals")
    lines.append("")
    for prop in proposals[:10]:
        d1, d2 = prop["domain_pair"]
        lines.append(f"### {d1} x {d2}")
        lines.append(f"- Existing open problems at intersection: {prop['existing_open']}")
        if prop["example_open"]:
            lines.append(f"- Examples: {', '.join(f'#{n}' for n in prop['example_open'])}")
        lines.append(f"- Techniques from {d1}: {', '.join(prop['techniques_from_d1'][:4])}")
        lines.append(f"- Techniques from {d2}: {', '.join(prop['techniques_from_d2'][:4])}")
        lines.append("")

    # ── Section 8: Problem Clusters ──
    lines.append("## 8. Problem Clusters")
    lines.append("")
    lines.append(f"K-means clustering with k={clusters['n_clusters']} produced the following groups:")
    lines.append("")
    for cl in clusters["clusters"]:
        top_tags = ", ".join(f"{t}({c})" for t, c in cl["dominant_tags"][:3])
        solve_rate = cl["solved_count"] / max(cl["size"], 1)
        lines.append(
            f"- **Cluster {cl['cluster_id']}** ({cl['size']} problems): "
            f"{top_tags} | "
            f"{cl['open_count']} open, {cl['solved_count']} solved "
            f"(rate={solve_rate:.2f})"
        )
    lines.append("")

    # ── Section 9: Key Findings ──
    lines.append("## 9. Key Cross-Cutting Findings")
    lines.append("")

    # Compute key findings
    if vulnerability:
        top = vulnerability[0]
        lines.append(
            f"1. **Most vulnerable problem**: #{top['number']} "
            f"(vulnerability={top['vulnerability']:.3f}). "
            f"Tags: {', '.join(top['tags'][:3])}"
        )

    if cascade:
        top_cascade = cascade[0]
        lines.append(
            f"2. **Highest cascade potential**: #{top_cascade['number']} — "
            f"solving it would influence {top_cascade['total_cascade']} other problems"
        )

    if effectiveness:
        best_tech = effectiveness[0]
        lines.append(
            f"3. **Most powerful technique**: {best_tech['technique']} "
            f"(power={best_tech['power_score']:.1f}, "
            f"covers {best_tech['matched_open']} open problems)"
        )

    prize_accessible = sum(
        e["total_prize_accessible"] for e in effectiveness
    )
    lines.append(
        f"4. **Total prize money accessible** by our techniques: "
        f"${prize_accessible:,.0f}"
    )

    lines.append(
        f"5. **Conjecture network density**: "
        f"{network['num_edges'] / max(network['num_nodes'] * (network['num_nodes'] - 1) // 2, 1):.4f}"
    )
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    """Run the full synthesis pipeline."""
    print("=" * 70)
    print("ERDOS PROBLEMS: CROSS-CUTTING SYNTHESIS")
    print("=" * 70)

    problems = load_problems()
    print(f"Loaded {len(problems)} problems")

    print("\n1. Computing vulnerability scores...")
    vuln = compute_vulnerability_scores(problems)
    print(f"   Top 3: {[f'#{v['number']}' for v in vuln[:3]]}")

    print("\n2. Detecting dualities...")
    duals = detect_dualities(problems)
    print(f"   Found {len(duals)} dualities")

    print("\n3. Building conjecture network...")
    network = build_conjecture_network(problems)
    print(f"   {network['num_nodes']} nodes, {network['num_edges']} edges")

    print("\n4. Computing resolution cascades...")
    cascade = resolution_cascade(problems)
    print(f"   Top cascade: #{cascade[0]['number']} ({cascade[0]['total_cascade']} influence)")

    print("\n5. Generating gap-bridging proposals...")
    proposals = gap_bridging_proposals(problems)
    print(f"   {len(proposals)} proposals")

    print("\n6. Building difficulty taxonomy...")
    taxonomy = difficulty_taxonomy(problems)
    print(f"   Tiers: {taxonomy['tier_counts']}")

    print("\n7. Analyzing technique effectiveness...")
    effectiveness = technique_effectiveness(problems)
    print(f"   Most powerful: {effectiveness[0]['technique']}")

    print("\n8. Clustering problems...")
    clusters = problem_similarity_clusters(problems)
    print(f"   {clusters['n_clusters']} clusters")

    print("\n9. Generating report...")
    report = generate_report(
        vuln, duals, network, cascade, proposals, taxonomy, effectiveness, clusters
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"   Report saved to {REPORT_PATH}")

    print("\n" + "=" * 70)
    print("SYNTHESIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
