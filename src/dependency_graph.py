#!/usr/bin/env python3
"""
dependency_graph.py — Tag-based proximity graph between Erdős problems.

NOTE: Despite the name, this module constructs a TAG PROXIMITY GRAPH, not a
causal dependency graph. Edges represent shared tags or OEIS sequences, not
mathematical implications. "A -> B" means "A and B are related by metadata
overlap," not "solving A logically enables solving B." The large SCCs and
long chains are artifacts of dense tag co-occurrence, not evidence of deep
mathematical dependency.

Constructs DIRECTED relationships based on metadata heuristics:
  1. Shared OEIS sequences (solved→open, used as a proxy for technique relevance)
  2. Tag containment (subset tags suggest topical overlap, not logical dependency)
  3. Problem number ordering (catalogue IDs, not chronological — see note below)

Analyses (interpret with the above caveats):
  1. Strongly Connected Components: clusters of mutually related problems by tag/OEIS overlap
  2. Topological Layers: ordering induced by the proximity heuristics (not a true dependency order)
  3. High-Reach Problems: problems with the most downstream connections in the proximity graph
     (often driven by broad tags like "number theory," not mathematical centrality)
  4. Longest Chains: longest paths in the proximity graph (reflect tag transitivity, not bottleneck sequences)
  5. Graph Depth: how far "downstream" each problem is in the proximity graph
  6. Reachability Simulation: BFS reachability through the proximity graph
  7. Isolated Problems: problems with no incoming edges in this graph

Output: docs/dependency_graph_report.md
"""

import math
import yaml
import numpy as np
from collections import defaultdict, Counter, deque
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "dependency_graph_report.md"


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


# ═══════════════════════════════════════════════════════════════════
# Graph Construction
# ═══════════════════════════════════════════════════════════════════

def build_dependency_graph(problems: List[Dict]) -> Dict[str, Any]:
    """
    Build directed proximity graph where edge A->B means
    "A and B share metadata (tags or OEIS sequences)."

    This is NOT a causal dependency graph. Edges reflect metadata overlap,
    not mathematical implication. The direction is imposed by heuristics
    (solved->open, lower number->higher number), not by logical structure.

    Edge types and weights:
    - OEIS bridge (weight 3): A and B share OEIS sequence, A is solved
    - Tag containment (weight 2): A's tags are a strict subset of B's tags
    - OEIS co-occurrence (weight 1): A and B share OEIS, both open
    (No sequential reference edges are actually created despite earlier docs.)

    Returns dict with:
    - adjacency: {source: [(target, weight, edge_type), ...]}
    - nodes: set of all problem numbers
    - n_edges: total edge count
    - edge_type_counts: count by type
    """
    prob_by_num = {_number(p): p for p in problems}

    # OEIS index
    oeis_to_problems = defaultdict(list)
    for p in problems:
        num = _number(p)
        for seq in _oeis(p):
            if seq and seq != "A000000" and not seq.startswith("A00000"):
                oeis_to_problems[seq].append(num)

    adjacency = defaultdict(list)
    nodes = set()
    edge_counts = Counter()

    for p in problems:
        nodes.add(_number(p))

    # Type 1: OEIS bridge (solved → open via shared sequence)
    for seq, nums in oeis_to_problems.items():
        solved_nums = [n for n in nums if prob_by_num.get(n) and _is_solved(prob_by_num[n])]
        open_nums = [n for n in nums if prob_by_num.get(n) and _is_open(prob_by_num[n])]
        for s in solved_nums:
            for o in open_nums:
                adjacency[s].append((o, 3, "oeis_bridge"))
                edge_counts["oeis_bridge"] += 1

    # Type 2: OEIS co-occurrence (both open, lower number → higher)
    for seq, nums in oeis_to_problems.items():
        open_nums = sorted(n for n in nums if prob_by_num.get(n) and _is_open(prob_by_num[n]))
        for i in range(len(open_nums)):
            for j in range(i + 1, min(i + 5, len(open_nums))):  # limit fan-out
                adjacency[open_nums[i]].append((open_nums[j], 1, "oeis_cooccurrence"))
                edge_counts["oeis_cooccurrence"] += 1

    # Type 3: Tag containment (A's tags ⊂ B's tags)
    open_problems = [(p, _number(p), _tags(p)) for p in problems if _is_open(p)]
    for i, (pi, ni, ti) in enumerate(open_problems):
        if not ti:
            continue
        for j, (pj, nj, tj) in enumerate(open_problems):
            if i == j or not tj:
                continue
            if ti < tj:  # strict subset
                adjacency[ni].append((nj, 2, "tag_containment"))
                edge_counts["tag_containment"] += 1

    return {
        "adjacency": dict(adjacency),
        "nodes": nodes,
        "n_edges": sum(edge_counts.values()),
        "edge_type_counts": dict(edge_counts),
    }


# ═══════════════════════════════════════════════════════════════════
# Strongly Connected Components (Tarjan's Algorithm)
# NOTE: Large SCCs here reflect dense tag overlap (e.g., many problems
# share "number theory"), not genuine mutual mathematical dependency.
# ═══════════════════════════════════════════════════════════════════

def strongly_connected_components(graph: Dict[str, Any]) -> List[List[int]]:
    """
    Find SCCs using Tarjan's algorithm.
    Returns list of components (each a list of problem numbers), sorted by size.
    """
    adj = graph["adjacency"]
    nodes = graph["nodes"]

    index_counter = [0]
    stack = []
    lowlink = {}
    index = {}
    on_stack = set()
    result = []

    def strongconnect(v):
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack.add(v)

        for w, _, _ in adj.get(v, []):
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            component = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                component.append(w)
                if w == v:
                    break
            result.append(sorted(component))

    # Use iterative approach to avoid recursion limit
    # (Simplified: just process each node)
    import sys
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_limit, len(nodes) + 100))
    try:
        for v in sorted(nodes):
            if v not in index:
                strongconnect(v)
    finally:
        sys.setrecursionlimit(old_limit)

    result.sort(key=len, reverse=True)
    return result


# ═══════════════════════════════════════════════════════════════════
# Topological Layers (BFS layering of the proximity graph)
# NOTE: These layers reflect the structure of tag/OEIS overlap, not
# a true mathematical dependency ordering.
# ═══════════════════════════════════════════════════════════════════

def topological_layers(graph: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute topological layers of the proximity graph.
    Layer 0 = source nodes (no incoming edges in the proximity graph).
    Layer k = nodes whose incoming proximity edges are all from layers < k.

    These layers reflect tag/OEIS overlap structure, not true mathematical
    dependency ordering.

    Returns dict with:
    - layers: list of lists (problems in each layer)
    - depth: dict mapping problem number -> layer depth
    - max_depth: deepest layer
    """
    adj = graph["adjacency"]
    nodes = graph["nodes"]

    # Compute in-degree
    in_degree = defaultdict(int)
    for src, edges in adj.items():
        for tgt, _, _ in edges:
            in_degree[tgt] += 1

    # BFS from sources
    queue = deque()
    depth = {}
    for n in nodes:
        if in_degree[n] == 0:
            queue.append(n)
            depth[n] = 0

    while queue:
        v = queue.popleft()
        for w, _, _ in adj.get(v, []):
            if w not in depth:
                depth[w] = depth[v] + 1
                queue.append(w)
            else:
                depth[w] = max(depth[w], depth[v] + 1)

    # Assign depth 0 to unreachable nodes
    for n in nodes:
        if n not in depth:
            depth[n] = 0

    # Group by layer
    layers = defaultdict(list)
    for n, d in depth.items():
        layers[d].append(n)

    max_depth = max(depth.values()) if depth else 0

    return {
        "layers": [sorted(layers.get(d, [])) for d in range(max_depth + 1)],
        "depth": depth,
        "max_depth": max_depth,
    }


# ═══════════════════════════════════════════════════════════════════
# High-Reach Problems — Maximum Downstream Reachability in Proximity Graph
# NOTE: "Keystone" is a misnomer. High reachability here is driven by
# broad tags (e.g., "number theory" connects to many problems). These
# are not necessarily mathematically central problems.
# ═══════════════════════════════════════════════════════════════════

def keystone_problems(problems: List[Dict],
                      graph: Dict[str, Any],
                      top_k: int = 20) -> List[Dict[str, Any]]:
    """
    Identify problems with the highest BFS reachability in the proximity graph.

    NOTE: Despite the function name, these are not true "keystones." High
    reachability is largely an artifact of broad tag overlap (e.g., "number
    theory" problems reach many others because the tag is common). This
    does not mean solving these problems would mathematically unblock others.

    Uses BFS reachability from each node to count downstream problems.
    """
    adj = graph["adjacency"]
    prob_by_num = {_number(p): p for p in problems}

    # Only consider open problems as potential keystones
    open_nums = {_number(p) for p in problems if _is_open(p)}

    results = []
    for num in sorted(open_nums):
        # BFS to find all reachable nodes
        visited = set()
        queue = deque([num])
        while queue:
            v = queue.popleft()
            for w, _, _ in adj.get(v, []):
                if w not in visited and w != num:
                    visited.add(w)
                    queue.append(w)

        # Count open downstream
        open_downstream = sum(1 for v in visited if v in open_nums and v != num)

        if open_downstream > 0:
            p = prob_by_num.get(num)
            results.append({
                "number": num,
                "downstream_open": open_downstream,
                "downstream_total": len(visited),
                "tags": sorted(_tags(p)) if p else [],
                "prize": _prize(p) if p else 0.0,
                "status": _status(p) if p else "unknown",
            })

    results.sort(key=lambda x: -x["downstream_open"])
    return results[:top_k]


# ═══════════════════════════════════════════════════════════════════
# Longest Paths — Longest Chains in Proximity Graph
# NOTE: These are NOT bottleneck dependency chains. They reflect
# transitive tag overlap, not sequential mathematical prerequisites.
# ═══════════════════════════════════════════════════════════════════

def critical_paths(problems: List[Dict],
                   graph: Dict[str, Any],
                   top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Find the longest chains in the proximity graph.

    NOTE: These are not true dependency chains. A "chain" here means a
    sequence of problems connected by tag/OEIS overlap, not a sequence
    where each problem mathematically depends on the previous one.
    """
    adj = graph["adjacency"]
    prob_by_num = {_number(p): p for p in problems}
    open_nums = {_number(p) for p in problems if _is_open(p)}

    # Compute longest path from each node using memoized DFS
    memo = {}

    def longest_from(v, visited=None):
        if v in memo:
            return memo[v]
        if visited is None:
            visited = set()
        if v in visited:
            return [v]  # cycle detected, stop
        visited.add(v)

        best_path = [v]
        for w, _, _ in adj.get(v, []):
            if w in open_nums and w not in visited:
                sub = longest_from(w, visited.copy())
                if len(sub) + 1 > len(best_path):
                    best_path = [v] + sub

        memo[v] = best_path
        return best_path

    # Find longest paths from each open node
    all_paths = []
    for num in sorted(open_nums):
        path = longest_from(num)
        if len(path) >= 3:
            all_paths.append(path)

    # Deduplicate (keep unique starting points) and sort by length
    seen_starts = set()
    unique_paths = []
    all_paths.sort(key=len, reverse=True)
    for path in all_paths:
        if path[0] not in seen_starts:
            seen_starts.add(path[0])
            tags = set()
            for num in path:
                p = prob_by_num.get(num)
                if p:
                    tags.update(_tags(p))
            unique_paths.append({
                "path": path,
                "length": len(path),
                "tags": sorted(tags),
                "total_prize": sum(_prize(prob_by_num[n]) for n in path if n in prob_by_num),
            })

    return unique_paths[:top_k]


# ═══════════════════════════════════════════════════════════════════
# Isolated Problems — No Incoming Edges in Proximity Graph
# ═══════════════════════════════════════════════════════════════════

def orphan_problems(problems: List[Dict],
                    graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find open problems that have no incoming edges in the proximity graph.

    NOTE: "Orphan" is a misnomer. Having no incoming proximity edges means
    these problems don't share tags/OEIS with problems that point to them
    in this heuristic graph. It does NOT mean they are mathematically
    independent or must be attacked without help from other results.
    """
    adj = graph["adjacency"]
    prob_by_num = {_number(p): p for p in problems}

    # Compute in-degree for open problems
    in_degree = defaultdict(int)
    for src, edges in adj.items():
        for tgt, _, _ in edges:
            in_degree[tgt] += 1

    open_nums = {_number(p) for p in problems if _is_open(p)}
    orphans = []
    for num in sorted(open_nums):
        if in_degree[num] == 0:
            p = prob_by_num.get(num)
            if p:
                out_degree = len(adj.get(num, []))
                orphans.append({
                    "number": num,
                    "tags": sorted(_tags(p)),
                    "prize": _prize(p),
                    "out_degree": out_degree,
                })

    orphans.sort(key=lambda x: -x["out_degree"])
    return orphans


# ═══════════════════════════════════════════════════════════════════
# Reachability Simulation — BFS Through Proximity Graph
# NOTE: This simulates BFS reachability through tag/OEIS overlap, not
# actual technique transfer or mathematical cascades.
# ═══════════════════════════════════════════════════════════════════

def influence_flow(problems: List[Dict],
                   graph: Dict[str, Any],
                   seed_problems: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Simulate BFS reachability from a set of "seed" problems through the
    proximity graph.

    NOTE: This does NOT model actual technique transfer or mathematical
    cascades. It measures how many problems are reachable via tag/OEIS
    overlap edges. The "waves" reflect graph distance in the proximity
    graph, not a realistic model of how solving one problem helps with others.

    Returns dict with:
    - waves: list of (wave_number, newly_reached_problems)
    - total_influenced: count of problems reached
    - influence_tags: tags of reached problems
    """
    adj = graph["adjacency"]
    prob_by_num = {_number(p): p for p in problems}
    open_nums = {_number(p) for p in problems if _is_open(p)}

    if seed_problems is None:
        # Default: simulate solving the top keystone
        keystones = keystone_problems(problems, graph, top_k=1)
        seed_problems = [keystones[0]["number"]] if keystones else []

    if not seed_problems:
        return {"waves": [], "total_influenced": 0, "influence_tags": []}

    # BFS waves
    visited = set(seed_problems)
    waves = []
    current_wave = set(seed_problems)

    for wave_num in range(10):  # max 10 waves
        next_wave = set()
        for v in current_wave:
            for w, weight, _ in adj.get(v, []):
                if w not in visited and w in open_nums:
                    next_wave.add(w)
                    visited.add(w)

        if not next_wave:
            break
        waves.append({
            "wave": wave_num + 1,
            "count": len(next_wave),
            "problems": sorted(next_wave)[:20],  # sample
        })
        current_wave = next_wave

    # Collect tags of all influenced problems
    influenced_tags = Counter()
    for n in visited:
        p = prob_by_num.get(n)
        if p:
            for t in _tags(p):
                influenced_tags[t] += 1

    return {
        "seed_problems": seed_problems,
        "waves": waves,
        "total_influenced": len(visited) - len(seed_problems),
        "influence_tags": influenced_tags.most_common(10),
    }


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    graph = build_dependency_graph(problems)
    sccs = strongly_connected_components(graph)
    layers = topological_layers(graph)
    keystones = keystone_problems(problems, graph)
    paths = critical_paths(problems, graph)
    orphans = orphan_problems(problems, graph)
    flow = influence_flow(problems, graph)

    lines = ["# Tag Proximity Graph Analysis", ""]
    lines.append("NOTE: This is a tag/OEIS proximity graph, not a causal dependency graph.")
    lines.append("Edges represent shared metadata, not mathematical implications.")
    lines.append("")
    lines.append(f"Directed proximity graph: {len(graph['nodes'])} nodes, "
                 f"{graph['n_edges']} edges")
    lines.append("")

    # Edge type distribution
    lines.append("## 1. Graph Structure")
    lines.append("")
    lines.append("| Edge Type | Count | Weight |")
    lines.append("|-----------|-------|--------|")
    for etype, count in sorted(graph["edge_type_counts"].items(), key=lambda x: -x[1]):
        w = {"oeis_bridge": 3, "tag_containment": 2, "oeis_cooccurrence": 1}.get(etype, 1)
        lines.append(f"| {etype} | {count} | {w} |")
    lines.append("")

    # SCCs
    lines.append("## 2. Strongly Connected Components")
    lines.append("")
    large_sccs = [s for s in sccs if len(s) > 1]
    lines.append(f"Total SCCs: {len(sccs)} ({len(large_sccs)} with >1 member)")
    lines.append("")
    if large_sccs:
        lines.append("| SCC | Size | Sample Members |")
        lines.append("|-----|------|----------------|")
        for i, scc in enumerate(large_sccs[:10]):
            members = ", ".join(f"#{n}" for n in scc[:5])
            if len(scc) > 5:
                members += f" (+{len(scc) - 5} more)"
            lines.append(f"| {i + 1} | {len(scc)} | {members} |")
        lines.append("")

    # Topological layers
    lines.append("## 3. Topological Layers")
    lines.append("")
    lines.append(f"Maximum depth: {layers['max_depth']}")
    lines.append("")
    lines.append("| Layer | Problems | Description |")
    lines.append("|-------|----------|-------------|")
    for d in range(min(layers["max_depth"] + 1, 10)):
        layer_probs = layers["layers"][d] if d < len(layers["layers"]) else []
        desc = "Source (no dependencies)" if d == 0 else f"Depth {d}"
        lines.append(f"| {d} | {len(layer_probs)} | {desc} |")
    lines.append("")

    # High-reachability problems (see caveats in module docstring)
    lines.append("## 4. High-Reachability Problems (Proximity Graph)")
    lines.append("")
    lines.append("| Problem | Downstream | Tags | Prize |")
    lines.append("|---------|-----------|------|-------|")
    for k in keystones[:15]:
        tags_str = ", ".join(k["tags"][:3])
        prize_str = f"${k['prize']:.0f}" if k["prize"] > 0 else "-"
        lines.append(f"| #{k['number']} | {k['downstream_open']} open | {tags_str} | {prize_str} |")
    lines.append("")

    # Critical paths
    lines.append("## 5. Longest Paths (Tag/OEIS Proximity Chains)")
    lines.append("")
    for i, path in enumerate(paths[:5]):
        path_str = " → ".join(f"#{n}" for n in path["path"][:8])
        if len(path["path"]) > 8:
            path_str += " → ..."
        lines.append(f"### Chain {i + 1} (length {path['length']})")
        lines.append(f"- Path: {path_str}")
        lines.append(f"- Tags: {', '.join(path['tags'][:5])}")
        if path["total_prize"] > 0:
            lines.append(f"- Total prize: ${path['total_prize']:.0f}")
        lines.append("")

    # Orphans
    lines.append("## 6. Isolated Problems (No Incoming Proximity Edges)")
    lines.append("")
    lines.append(f"Total orphans: {len(orphans)} (must be attacked directly)")
    lines.append("")
    if orphans:
        lines.append("| Problem | Tags | Prize | Out-Degree |")
        lines.append("|---------|------|-------|-----------|")
        for o in orphans[:15]:
            tags_str = ", ".join(o["tags"][:3])
            prize_str = f"${o['prize']:.0f}" if o["prize"] > 0 else "-"
            lines.append(f"| #{o['number']} | {tags_str} | {prize_str} | {o['out_degree']} |")
        lines.append("")

    # Influence flow
    lines.append("## 7. Reachability Simulation (BFS Through Proximity Graph)")
    lines.append("")
    if flow["seed_problems"]:
        seeds = ", ".join(f"#{n}" for n in flow["seed_problems"])
        lines.append(f"Seed problems: {seeds}")
        lines.append(f"Total influenced: {flow['total_influenced']} problems")
        lines.append("")
        if flow["waves"]:
            lines.append("| Wave | New Problems | Sample |")
            lines.append("|------|-------------|--------|")
            for w in flow["waves"]:
                sample = ", ".join(f"#{n}" for n in w["problems"][:5])
                lines.append(f"| {w['wave']} | {w['count']} | {sample} |")
            lines.append("")
        if flow["influence_tags"]:
            lines.append("### Influenced Tags")
            for tag, count in flow["influence_tags"]:
                lines.append(f"- **{tag}**: {count} problems")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    problems = load_problems()
    report = generate_report(problems)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")
