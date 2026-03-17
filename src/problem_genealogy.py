#!/usr/bin/env python3
"""
Problem Genealogy — Intellectual Lineage Among Erdős Problems

Builds a directed "inspired-by" graph based on:
1. Shared OEIS sequences (weighted by specificity)
2. Tag containment (one problem's tags are a subset of another's)
3. Number proximity (nearby problem numbers suggest temporal relationship)
4. Textual similarity of problem statements (Jaccard on word n-grams)

Key outputs:
- Ancestral problems (most "descendants")
- Terminal problems (no offspring)
- Intellectual distance between any two problems
- Hidden connections between distant families
- Genealogical depth (longest ancestor chain)
"""

import math
import yaml
import re
import numpy as np
from collections import defaultdict, Counter, deque
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "problem_genealogy_report.md"


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


def _oeis(p: Dict) -> List[str]:
    raw = p.get("oeis", [])
    if not raw:
        return []
    return [s for s in raw if s and s not in ("N/A", "possible")]


def _status(p: Dict) -> str:
    return p.get("status", {}).get("state", "unknown")


def _is_solved(p: Dict) -> bool:
    return _status(p) in ("proved", "disproved", "solved",
                          "proved (Lean)", "disproved (Lean)", "solved (Lean)")


def _statement_words(p: Dict) -> Set[str]:
    """Extract normalized word set from problem statement."""
    stmt = p.get("statement", "") or ""
    if isinstance(stmt, dict):
        stmt = stmt.get("text", "") or ""
    words = re.findall(r'[a-z]+', stmt.lower())
    # Filter stopwords
    stops = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
             "have", "has", "had", "do", "does", "did", "will", "would",
             "could", "should", "may", "might", "shall", "can", "must",
             "of", "in", "to", "for", "with", "on", "at", "from", "by",
             "about", "as", "into", "through", "during", "before", "after",
             "and", "but", "or", "nor", "not", "no", "so", "yet", "both",
             "either", "neither", "each", "every", "all", "any", "few",
             "more", "most", "other", "some", "such", "than", "too",
             "very", "just", "only", "own", "same", "that", "this",
             "these", "those", "it", "its", "if", "then", "else",
             "when", "where", "which", "who", "whom", "what", "how",
             "there", "here", "let", "show", "prove", "find", "determine"}
    return {w for w in words if w not in stops and len(w) > 2}


def _bigrams(words: Set[str]) -> Set[Tuple[str, str]]:
    """Generate bigrams from a word set (sorted for consistency)."""
    word_list = sorted(words)
    return {(word_list[i], word_list[j])
            for i in range(len(word_list))
            for j in range(i + 1, min(i + 4, len(word_list)))}


# ══════════════════════════════════════════════════════════════════════
# Build Genealogy Graph
# ══════════════════════════════════════════════════════════════════════

def build_genealogy(problems: List[Dict],
                    oeis_weight: float = 2.0,
                    tag_weight: float = 1.5,
                    text_weight: float = 2.0,
                    proximity_weight: float = 0.8,
                    min_edge_weight: float = 1.0) -> Dict[str, Any]:
    """
    Build directed genealogy graph.

    Direction: older problem (lower number) → younger problem.
    Edge weight = sum of similarity signals.
    """
    prob_by_num = {}
    for p in problems:
        num = _number(p)
        if num > 0:
            prob_by_num[num] = p

    numbers = sorted(prob_by_num.keys())
    n = len(numbers)

    # Precompute features
    tags_map = {num: _tags(prob_by_num[num]) for num in numbers}
    oeis_map = {num: set(_oeis(prob_by_num[num])) for num in numbers}
    words_map = {num: _statement_words(prob_by_num[num]) for num in numbers}

    # OEIS frequency (for IDF weighting)
    oeis_freq = Counter()
    for seqs in oeis_map.values():
        for s in seqs:
            oeis_freq[s] += 1

    # Build edges
    edges = defaultdict(float)  # (ancestor, descendant) -> weight
    edge_reasons = defaultdict(list)  # (ancestor, descendant) -> [reasons]

    for i in range(n):
        for j in range(i + 1, n):
            u, v = numbers[i], numbers[j]
            weight = 0.0
            reasons = []

            # 1. Shared OEIS (IDF-weighted)
            shared_oeis = oeis_map[u] & oeis_map[v]
            if shared_oeis:
                oeis_score = sum(math.log(n / oeis_freq[s])
                                for s in shared_oeis
                                if oeis_freq[s] < n / 2)
                if oeis_score > 0:
                    weight += oeis_weight * min(oeis_score / 3.0, 2.0)
                    reasons.append(f"oeis:{len(shared_oeis)}")

            # 2. Tag relationship
            tags_u = tags_map[u]
            tags_v = tags_map[v]
            if tags_u and tags_v:
                shared = len(tags_u & tags_v)
                jaccard = shared / len(tags_u | tags_v)
                if shared >= 2 and jaccard >= 0.3:
                    weight += tag_weight * jaccard
                    reasons.append(f"tags:{jaccard:.2f}")

            # 3. Textual similarity
            words_u = words_map[u]
            words_v = words_map[v]
            if len(words_u) >= 3 and len(words_v) >= 3:
                word_jaccard = len(words_u & words_v) / len(words_u | words_v)
                if word_jaccard >= 0.08:
                    weight += text_weight * word_jaccard
                    reasons.append(f"text:{word_jaccard:.2f}")

            # 4. Number proximity (closer = more likely related)
            gap = v - u
            if gap <= 20:
                prox_score = proximity_weight * (1.0 - gap / 20.0)
                if prox_score > 0.05:
                    weight += prox_score
                    reasons.append(f"prox:{gap}")

            if weight >= min_edge_weight:
                edges[(u, v)] = weight
                edge_reasons[(u, v)] = reasons

    return {
        "edges": dict(edges),
        "edge_reasons": dict(edge_reasons),
        "numbers": numbers,
        "n_edges": len(edges),
        "n_nodes": n,
    }


# ══════════════════════════════════════════════════════════════════════
# Ancestry Analysis
# ══════════════════════════════════════════════════════════════════════

def find_ancestors(genealogy: Dict) -> List[Dict]:
    """
    Find ancestral problems — those with the most descendants.

    A "descendant" is any problem reachable via directed edges.
    """
    edges = genealogy["edges"]
    numbers = genealogy["numbers"]

    # Build adjacency list
    children = defaultdict(set)
    parents = defaultdict(set)
    for (u, v) in edges:
        children[u].add(v)
        parents[v].add(u)

    # Direct descendant count
    direct_count = {num: len(children.get(num, set())) for num in numbers}

    # BFS reachability for top candidates
    top_direct = sorted(numbers, key=lambda n: -direct_count[n])[:50]

    ancestors = []
    for num in top_direct:
        # BFS from num
        visited = set()
        queue = deque([num])
        visited.add(num)
        while queue:
            curr = queue.popleft()
            for child in children.get(curr, set()):
                if child not in visited:
                    visited.add(child)
                    queue.append(child)

        reachable = len(visited) - 1  # exclude self
        ancestors.append({
            "number": num,
            "direct_descendants": direct_count[num],
            "total_reachable": reachable,
            "tags": list(_tags(genealogy.get("_prob_map", {}).get(num, {}))),
        })

    ancestors.sort(key=lambda x: -x["total_reachable"])
    return ancestors


def find_terminals(genealogy: Dict) -> List[Dict]:
    """
    Find terminal problems — those with no descendants (leaves of the tree).
    """
    edges = genealogy["edges"]
    numbers = set(genealogy["numbers"])

    has_child = set()
    has_parent = set()
    for (u, v) in edges:
        has_child.add(u)
        has_parent.add(v)

    terminals = []
    for num in sorted(numbers):
        if num not in has_child and num in has_parent:
            n_parents = sum(1 for (u, v) in edges if v == num)
            terminals.append({
                "number": num,
                "n_parents": n_parents,
            })

    terminals.sort(key=lambda x: -x["n_parents"])
    return terminals


def find_orphans(genealogy: Dict) -> List[int]:
    """Find problems with no connections at all."""
    edges = genealogy["edges"]
    connected = set()
    for (u, v) in edges:
        connected.add(u)
        connected.add(v)

    all_nums = set(genealogy["numbers"])
    return sorted(all_nums - connected)


# ══════════════════════════════════════════════════════════════════════
# Intellectual Distance
# ══════════════════════════════════════════════════════════════════════

def intellectual_distance(genealogy: Dict,
                         source: int, target: int) -> Dict[str, Any]:
    """
    Compute shortest path between two problems in the undirected genealogy.
    """
    edges = genealogy["edges"]

    # Build undirected adjacency
    adj = defaultdict(set)
    weights = {}
    for (u, v), w in edges.items():
        adj[u].add(v)
        adj[v].add(u)
        weights[(u, v)] = w
        weights[(v, u)] = w

    if source not in adj and target not in adj:
        return {"distance": -1, "path": [], "connected": False}

    # BFS for shortest path
    visited = {source: None}
    queue = deque([source])

    while queue:
        curr = queue.popleft()
        if curr == target:
            # Reconstruct path
            path = []
            node = target
            while node is not None:
                path.append(node)
                node = visited[node]
            path.reverse()
            return {
                "distance": len(path) - 1,
                "path": path,
                "connected": True,
            }
        for neighbor in adj[curr]:
            if neighbor not in visited:
                visited[neighbor] = curr
                queue.append(neighbor)

    return {"distance": -1, "path": [], "connected": False}


def diameter_sample(genealogy: Dict, n_samples: int = 100) -> Dict[str, Any]:
    """
    Estimate graph diameter by sampling random pairs.
    """
    import random
    random.seed(42)

    edges = genealogy["edges"]
    numbers = genealogy["numbers"]

    # Build undirected adjacency
    adj = defaultdict(set)
    for (u, v) in edges:
        adj[u].add(v)
        adj[v].add(u)

    connected_nodes = [n for n in numbers if n in adj]
    if len(connected_nodes) < 2:
        return {"max_distance": 0, "avg_distance": 0, "n_sampled": 0}

    distances = []
    max_dist = 0
    max_pair = None

    for _ in range(n_samples):
        s, t = random.sample(connected_nodes, 2)
        result = intellectual_distance(genealogy, s, t)
        if result["connected"]:
            distances.append(result["distance"])
            if result["distance"] > max_dist:
                max_dist = result["distance"]
                max_pair = (s, t)

    return {
        "max_distance": max_dist,
        "avg_distance": round(np.mean(distances), 2) if distances else 0,
        "median_distance": int(np.median(distances)) if distances else 0,
        "n_sampled": len(distances),
        "n_disconnected": n_samples - len(distances),
        "farthest_pair": max_pair,
    }


# ══════════════════════════════════════════════════════════════════════
# Cross-Family Bridges
# ══════════════════════════════════════════════════════════════════════

def cross_family_bridges(genealogy: Dict, problems: List[Dict]) -> List[Dict]:
    """
    Find edges that connect problems from different tag families.

    Strategy: identify edges whose *primary* signal is not tags —
    these are connections through OEIS, text, or proximity that link
    problems with different subject matter. Also includes tag-driven
    edges that bridge distinct broad families (e.g., combinatorics ↔ number theory).
    """
    BROAD_FAMILIES = {
        "number theory": "NT", "combinatorics": "COMB", "graph theory": "GT",
        "probability": "PROB", "geometry": "GEOM", "algebra": "ALG",
        "analysis": "ANA", "topology": "TOP", "set theory": "SET",
    }

    def _broad_family(tags: Set[str]) -> Set[str]:
        families = set()
        for tag in tags:
            for keyword, family in BROAD_FAMILIES.items():
                if keyword in tag.lower():
                    families.add(family)
        return families if families else {"OTHER"}

    edges = genealogy["edges"]
    edge_reasons = genealogy["edge_reasons"]

    prob_map = {}
    for p in problems:
        num = _number(p)
        if num > 0:
            prob_map[num] = p

    bridges = []
    for (u, v), weight in edges.items():
        tags_u = _tags(prob_map.get(u, {}))
        tags_v = _tags(prob_map.get(v, {}))
        reasons = edge_reasons.get((u, v), [])

        # Two criteria for "bridge":
        # 1. Non-tag-driven edge (text/OEIS/proximity only)
        has_tag_reason = any(r.startswith("tags:") for r in reasons)
        # 2. Different broad families
        families_u = _broad_family(tags_u)
        families_v = _broad_family(tags_v)
        different_families = not (families_u & families_v)

        if (not has_tag_reason) or different_families:
            tag_jaccard = (len(tags_u & tags_v) / len(tags_u | tags_v)
                          if tags_u and tags_v else 0.0)
            bridges.append({
                "from": u,
                "to": v,
                "weight": round(weight, 2),
                "reasons": reasons,
                "from_tags": sorted(tags_u),
                "to_tags": sorted(tags_v),
                "tag_overlap": round(tag_jaccard, 3),
                "cross_family": different_families,
            })

    bridges.sort(key=lambda x: (-x["cross_family"], -x["weight"]))
    return bridges


# ══════════════════════════════════════════════════════════════════════
# Genealogical Depth
# ══════════════════════════════════════════════════════════════════════

def genealogical_depth(genealogy: Dict) -> Dict[str, Any]:
    """
    Compute the longest directed path in the genealogy (genealogical depth).

    Uses dynamic programming on topological order (since graph is DAG
    by construction — edges go from lower to higher numbers).
    """
    edges = genealogy["edges"]
    numbers = genealogy["numbers"]

    # Children adjacency
    children = defaultdict(set)
    for (u, v) in edges:
        children[u].add(v)

    # DP: longest path from each node
    memo = {}

    def longest_from(node):
        if node in memo:
            return memo[node]
        if not children.get(node):
            memo[node] = (0, [node])
            return memo[node]

        best_len = 0
        best_path = [node]
        for child in children[node]:
            child_len, child_path = longest_from(child)
            if child_len + 1 > best_len:
                best_len = child_len + 1
                best_path = [node] + child_path

        memo[node] = (best_len, best_path)
        return memo[node]

    max_depth = 0
    longest_path = []
    deepest_root = None

    for num in numbers:
        depth, path = longest_from(num)
        if depth > max_depth:
            max_depth = depth
            longest_path = path
            deepest_root = num

    # Distribution of depths
    depths = [longest_from(num)[0] for num in numbers]
    depth_dist = Counter(depths)

    return {
        "max_depth": max_depth,
        "longest_chain": longest_path,
        "deepest_root": deepest_root,
        "avg_depth": round(float(np.mean(depths)), 2),
        "depth_distribution": dict(sorted(depth_dist.items())),
    }


# ══════════════════════════════════════════════════════════════════════
# Generation Analysis
# ══════════════════════════════════════════════════════════════════════

def generation_analysis(genealogy: Dict, problems: List[Dict]) -> Dict[str, Any]:
    """
    Partition problems into "generations" based on their earliest ancestor.

    Generation 0: problems with no parents (founders)
    Generation k: problems whose earliest parent is in generation k-1
    """
    edges = genealogy["edges"]
    numbers = genealogy["numbers"]

    # Parents adjacency
    parents = defaultdict(set)
    for (u, v) in edges:
        parents[v].add(u)

    # Assign generations via BFS from founders
    generation = {}
    founders = [n for n in numbers if n not in parents]
    for f in founders:
        generation[f] = 0

    # BFS by number order (ensures older problems processed first)
    children = defaultdict(set)
    for (u, v) in edges:
        children[u].add(v)

    changed = True
    while changed:
        changed = False
        for num in numbers:
            if num in generation:
                for child in children.get(num, set()):
                    new_gen = generation[num] + 1
                    if child not in generation or new_gen < generation[child]:
                        generation[child] = new_gen
                        changed = True

    # Unconnected problems are generation -1
    for num in numbers:
        if num not in generation:
            generation[num] = -1

    # Statistics per generation
    prob_map = {_number(p): p for p in problems if _number(p) > 0}
    gen_stats = defaultdict(lambda: {"count": 0, "solved": 0, "open": 0})

    for num in numbers:
        gen = generation.get(num, -1)
        gen_stats[gen]["count"] += 1
        p = prob_map.get(num, {})
        if _is_solved(p):
            gen_stats[gen]["solved"] += 1
        elif _status(p) == "open":
            gen_stats[gen]["open"] += 1

    gen_results = []
    for gen in sorted(gen_stats.keys()):
        s = gen_stats[gen]
        total = s["solved"] + s["open"]
        solve_rate = s["solved"] / total if total > 0 else 0
        gen_results.append({
            "generation": gen,
            "count": s["count"],
            "solve_rate": round(solve_rate, 3),
        })

    return {
        "n_founders": len(founders),
        "n_generations": max(generation.values()) + 1 if generation else 0,
        "generation_stats": gen_results,
        "founders_sample": sorted(founders)[:20],
    }


# ══════════════════════════════════════════════════════════════════════
# Report
# ══════════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    lines = [
        "# Problem Genealogy: Intellectual Lineage Among Erdős Problems",
        "",
    ]

    genealogy = build_genealogy(problems)
    # Attach problem map for ancestor analysis
    prob_map = {_number(p): p for p in problems if _number(p) > 0}
    genealogy["_prob_map"] = prob_map

    lines.append(f"**Graph**: {genealogy['n_nodes']} problems, "
                 f"{genealogy['n_edges']} directed edges")
    lines.append("")

    # Ancestors
    lines.append("## Ancestral Problems (Most Descendants)")
    ancestors = find_ancestors(genealogy)
    for a in ancestors[:15]:
        lines.append(f"- **#{a['number']}**: {a['direct_descendants']} direct, "
                     f"{a['total_reachable']} total reachable")
    lines.append("")

    # Terminals
    lines.append("## Terminal Problems (No Offspring)")
    terminals = find_terminals(genealogy)
    lines.append(f"**Count**: {len(terminals)}")
    for t in terminals[:10]:
        lines.append(f"- #{t['number']}: {t['n_parents']} parents")
    lines.append("")

    # Orphans
    orphans = find_orphans(genealogy)
    lines.append(f"## Orphaned Problems (No Connections): {len(orphans)}")
    lines.append("")

    # Depth
    lines.append("## Genealogical Depth")
    depth = genealogical_depth(genealogy)
    lines.append(f"**Max depth**: {depth['max_depth']}")
    lines.append(f"**Longest chain**: {' → '.join(f'#{n}' for n in depth['longest_chain'][:10])}")
    lines.append(f"**Avg depth**: {depth['avg_depth']}")
    lines.append("")

    # Diameter
    lines.append("## Intellectual Distance (Diameter)")
    diam = diameter_sample(genealogy)
    lines.append(f"**Estimated diameter**: {diam['max_distance']}")
    lines.append(f"**Avg distance**: {diam['avg_distance']}")
    lines.append(f"**Disconnected pairs**: {diam['n_disconnected']}/{diam['n_sampled'] + diam['n_disconnected']}")
    lines.append("")

    # Cross-family bridges
    lines.append("## Cross-Family Bridges (Surprising Connections)")
    bridges = cross_family_bridges(genealogy, problems)
    for b in bridges[:10]:
        lines.append(f"- #{b['from']} ({', '.join(b['from_tags'][:2])}) → "
                     f"#{b['to']} ({', '.join(b['to_tags'][:2])}): "
                     f"weight={b['weight']}, reasons={b['reasons']}")
    lines.append("")

    # Generations
    lines.append("## Generation Analysis")
    gens = generation_analysis(genealogy, problems)
    lines.append(f"**Founders**: {gens['n_founders']}")
    lines.append(f"**Generations**: {gens['n_generations']}")
    for g in gens["generation_stats"]:
        if g["generation"] >= 0:
            lines.append(f"  - Gen {g['generation']}: {g['count']} problems, "
                         f"solve rate={g['solve_rate']}")
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
