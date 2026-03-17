#!/usr/bin/env python3
"""
problem_network.py — Network science applied to mathematical knowledge.

Treats the 1,183 Erdos problems as a NETWORK and performs rigorous
graph-theoretic analysis. This is a multi-relational network where edges
encode four distinct types of similarity between problems:

  1. Tag co-occurrence (Jaccard similarity of tag sets)
  2. OEIS co-occurrence (shared OEIS sequences)
  3. Numerical proximity (|number_i - number_j| < 10)
  4. Same status (both open, both proved, etc.)

Analyses:
  - Community detection via Louvain algorithm
  - Centrality analysis (PageRank, betweenness, eigenvector)
  - Temporal network evolution (problem number as time proxy)
  - Solved vs. open subgraph comparison
  - Logistic regression for solvability prediction from network position

Output: docs/problem_network_report.md
"""

import math
import yaml
import numpy as np
import networkx as nx
from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

# ── Paths ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "problem_network_report.md"


# ═══════════════════════════════════════════════════════════════════
# Data Loading and Accessors
# ═══════════════════════════════════════════════════════════════════

def load_problems() -> List[Dict]:
    """Load problems from YAML file."""
    with open(DATA_PATH) as f:
        return yaml.safe_load(f)


def _number(p: Dict) -> int:
    """Extract problem number as int, handling str/int type ambiguity."""
    n = p.get("number", 0)
    return int(n) if isinstance(n, (int, str)) and str(n).isdigit() else 0


def _tags(p: Dict) -> Set[str]:
    """Extract tag set."""
    return set(p.get("tags", []))


def _status(p: Dict) -> str:
    """Extract status state string."""
    return p.get("status", {}).get("state", "unknown")


def _oeis(p: Dict) -> Set[str]:
    """Extract valid OEIS sequences, filtering N/A and 'possible' entries."""
    raw = p.get("oeis", [])
    if not isinstance(raw, list):
        return set()
    return {s for s in raw if s and s not in ("N/A", "possible", "n/a", "none", "")}


def _is_solved(p: Dict) -> bool:
    """Whether the problem has been resolved (proved, disproved, solved)."""
    return _status(p) in (
        "proved", "disproved", "solved",
        "proved (Lean)", "disproved (Lean)", "solved (Lean)",
    )


def _is_open(p: Dict) -> bool:
    return _status(p) == "open"


def _coarse_status(p: Dict) -> str:
    """Map fine-grained status into coarse categories for the same-status edge type."""
    s = _status(p)
    if s in ("proved", "proved (Lean)"):
        return "proved"
    if s in ("disproved", "disproved (Lean)"):
        return "disproved"
    if s in ("solved", "solved (Lean)"):
        return "solved"
    if s in ("falsifiable", "verifiable", "decidable"):
        return "partially_resolved"
    if s in ("not provable", "not disprovable", "independent"):
        return "independent"
    return s  # "open", "unknown"


def _prize(p: Dict) -> float:
    """Extract prize value in USD."""
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
# 1. Graph Construction
# ═══════════════════════════════════════════════════════════════════

def _jaccard(a: Set[str], b: Set[str]) -> float:
    """Jaccard similarity between two sets."""
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _tag_idf(tag: str, tag_counts: Dict[str, int], n_problems: int) -> float:
    """Inverse document frequency of a tag. Rarer tags carry more weight."""
    count = tag_counts.get(tag, 1)
    return math.log(n_problems / count)


def build_problem_graph(
    problems: List[Dict],
    *,
    tag_threshold: float = 0.5,
    proximity_window: int = 10,
    include_tag: bool = True,
    include_oeis: bool = True,
    include_proximity: bool = True,
    include_status: bool = True,
) -> nx.Graph:
    """
    Build a weighted undirected graph of Erdos problems.

    Edge types and their weights:
      - tag_cooccurrence: IDF-weighted Jaccard similarity of tag sets.
        Each shared tag contributes its IDF weight (rarer tags matter more),
        normalized by the union IDF mass. This prevents "number theory"
        (freq=556) from generating spurious edges while amplifying specific
        tags like "sidon sets" (freq=28).
      - oeis_cooccurrence: 2.0 per shared OEIS sequence (strong signal).
      - numerical_proximity: exp(-|i-j|/3) for |i-j| < proximity_window.
      - same_status: 0.2 bonus, only applied to pairs that already share
        a structural edge (tag or OEIS), never alone.

    Node attributes: number, tags, status, is_solved, oeis, prize, n_tags.
    Edge attributes: weight, edge_types (dict of type -> component weight).

    Parameters
    ----------
    problems : list of dict
        Raw problem records from YAML.
    tag_threshold : float
        Minimum IDF-weighted Jaccard to create a tag edge (default 0.5).
    proximity_window : int
        Maximum distance in problem number for proximity edges.
    include_tag, include_oeis, include_proximity, include_status : bool
        Toggle individual edge types.

    Returns
    -------
    nx.Graph
        The combined problem network.
    """
    G = nx.Graph()

    # Index by number
    prob_by_num = {}
    for p in problems:
        num = _number(p)
        if num == 0:
            continue
        prob_by_num[num] = p

    n_problems = len(prob_by_num)

    # Global tag frequency for IDF weighting
    tag_counts: Dict[str, int] = Counter()
    for p in prob_by_num.values():
        for t in _tags(p):
            tag_counts[t] += 1

    # Add nodes with attributes
    for num, p in prob_by_num.items():
        G.add_node(
            num,
            tags=sorted(_tags(p)),
            status=_status(p),
            coarse_status=_coarse_status(p),
            is_solved=_is_solved(p),
            is_open=_is_open(p),
            oeis=sorted(_oeis(p)),
            prize=_prize(p),
            n_tags=len(_tags(p)),
        )

    sorted_nums = sorted(prob_by_num.keys())

    # Helper to accumulate multi-type edges
    edge_weights: Dict[Tuple[int, int], Dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )

    # (a) Tag co-occurrence with IDF-weighted Jaccard
    if include_tag:
        # Build tag -> problems index to avoid O(n^2) full scan
        tag_index: Dict[str, List[int]] = defaultdict(list)
        for num, p in prob_by_num.items():
            for t in _tags(p):
                tag_index[t].append(num)

        # Only check pairs that share at least one tag
        candidate_pairs: Set[Tuple[int, int]] = set()
        for nums_with_tag in tag_index.values():
            for i in range(len(nums_with_tag)):
                for j in range(i + 1, len(nums_with_tag)):
                    a, b = nums_with_tag[i], nums_with_tag[j]
                    candidate_pairs.add((min(a, b), max(a, b)))

        for a, b in candidate_pairs:
            tags_a = _tags(prob_by_num[a])
            tags_b = _tags(prob_by_num[b])
            intersection = tags_a & tags_b
            union = tags_a | tags_b
            if not intersection or not union:
                continue
            # IDF-weighted Jaccard: sum(IDF of shared) / sum(IDF of union)
            idf_inter = sum(_tag_idf(t, tag_counts, n_problems) for t in intersection)
            idf_union = sum(_tag_idf(t, tag_counts, n_problems) for t in union)
            j_idf = idf_inter / idf_union if idf_union > 0 else 0.0
            if j_idf > tag_threshold:
                edge_weights[(a, b)]["tag_cooccurrence"] = j_idf

    # (b) OEIS co-occurrence
    if include_oeis:
        oeis_index: Dict[str, List[int]] = defaultdict(list)
        for num, p in prob_by_num.items():
            for seq in _oeis(p):
                oeis_index[seq].append(num)

        for seq, nums in oeis_index.items():
            if len(nums) < 2:
                continue
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    a, b = min(nums[i], nums[j]), max(nums[i], nums[j])
                    edge_weights[(a, b)]["oeis_cooccurrence"] += 2.0

    # (c) Numerical proximity
    if include_proximity:
        for i, a in enumerate(sorted_nums):
            for j in range(i + 1, len(sorted_nums)):
                b = sorted_nums[j]
                dist = b - a
                if dist >= proximity_window:
                    break
                w = math.exp(-dist / 3.0)
                edge_weights[(a, b)]["numerical_proximity"] = w

    # (d) Same status — only as a bonus on existing structural edges
    if include_status:
        for (a, b), types in edge_weights.items():
            if types:  # pair already has structural edge
                if _coarse_status(prob_by_num[a]) == _coarse_status(prob_by_num[b]):
                    types["same_status"] = 0.2

    # Materialize edges
    for (a, b), types in edge_weights.items():
        total_weight = sum(types.values())
        G.add_edge(a, b, weight=total_weight, edge_types=dict(types))

    return G


def graph_summary(G: nx.Graph) -> Dict[str, Any]:
    """Compute basic graph statistics."""
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    degrees = [d for _, d in G.degree()]

    # Edge type breakdown
    type_counts: Counter = Counter()
    type_total_weight: Dict[str, float] = defaultdict(float)
    for _, _, data in G.edges(data=True):
        for etype, w in data.get("edge_types", {}).items():
            type_counts[etype] += 1
            type_total_weight[etype] += w

    # Connected components
    components = list(nx.connected_components(G))
    component_sizes = sorted([len(c) for c in components], reverse=True)

    return {
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "density": nx.density(G),
        "avg_degree": np.mean(degrees) if degrees else 0.0,
        "max_degree": max(degrees) if degrees else 0,
        "median_degree": float(np.median(degrees)) if degrees else 0.0,
        "n_components": len(components),
        "largest_component_size": component_sizes[0] if component_sizes else 0,
        "component_sizes": component_sizes[:10],
        "edge_type_counts": dict(type_counts.most_common()),
        "edge_type_total_weight": dict(type_total_weight),
    }


# ═══════════════════════════════════════════════════════════════════
# 2. Community Detection
# ═══════════════════════════════════════════════════════════════════

def detect_communities(G: nx.Graph, resolution: float = 1.0) -> Dict[str, Any]:
    """
    Community detection using Louvain algorithm.

    Returns
    -------
    dict with:
      - partition: dict mapping node -> community_id
      - n_communities: number of communities
      - modularity: Q value
      - community_sizes: list of (community_id, size), sorted descending
      - community_profiles: for each community, its dominant tags, status mix,
        and fraction of solved problems
    """
    # Use greedy modularity (Louvain-like) from networkx
    communities_generator = nx.community.louvain_communities(
        G, weight="weight", resolution=resolution, seed=42
    )
    communities = list(communities_generator)

    partition = {}
    for cid, members in enumerate(communities):
        for node in members:
            partition[node] = cid

    modularity = nx.community.modularity(G, communities, weight="weight")

    community_sizes = sorted(
        [(cid, len(members)) for cid, members in enumerate(communities)],
        key=lambda x: -x[1],
    )

    # Profile each community
    community_profiles = {}
    for cid, members in enumerate(communities):
        tag_counter = Counter()
        status_counter = Counter()
        n_solved = 0
        n_open = 0
        prizes = []
        for node in members:
            data = G.nodes[node]
            for t in data.get("tags", []):
                tag_counter[t] += 1
            status_counter[data.get("coarse_status", "unknown")] += 1
            if data.get("is_solved"):
                n_solved += 1
            if data.get("is_open"):
                n_open += 1
            if data.get("prize", 0) > 0:
                prizes.append(data["prize"])

        size = len(members)
        community_profiles[cid] = {
            "size": size,
            "members": sorted(members),
            "top_tags": tag_counter.most_common(5),
            "status_mix": dict(status_counter.most_common()),
            "solve_rate": n_solved / size if size > 0 else 0.0,
            "open_rate": n_open / size if size > 0 else 0.0,
            "total_prize": sum(prizes),
            "n_prizes": len(prizes),
        }

    return {
        "partition": partition,
        "n_communities": len(communities),
        "modularity": modularity,
        "community_sizes": community_sizes,
        "community_profiles": community_profiles,
    }


def community_tag_alignment(
    G: nx.Graph, community_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Measure how well communities align with tag categories.

    Computes normalized mutual information (NMI) between community
    assignments and the dominant tag of each problem.
    """
    partition = community_result["partition"]

    # Assign each node its most-specific (least common) tag as "ground truth"
    tag_global_freq = Counter()
    for node in G.nodes():
        for t in G.nodes[node].get("tags", []):
            tag_global_freq[t] += 1

    tag_labels = {}
    for node in G.nodes():
        tags = G.nodes[node].get("tags", [])
        if tags:
            # Most specific = least globally frequent
            most_specific = min(tags, key=lambda t: tag_global_freq.get(t, 0))
            tag_labels[node] = most_specific
        else:
            tag_labels[node] = "__none__"

    # Build contingency matrix
    comm_ids = sorted(set(partition.values()))
    tag_ids = sorted(set(tag_labels.values()))
    comm_to_idx = {c: i for i, c in enumerate(comm_ids)}
    tag_to_idx = {t: i for i, t in enumerate(tag_ids)}

    shared_nodes = [n for n in G.nodes() if n in partition and n in tag_labels]
    contingency = np.zeros((len(comm_ids), len(tag_ids)))
    for node in shared_nodes:
        contingency[comm_to_idx[partition[node]], tag_to_idx[tag_labels[node]]] += 1

    # NMI calculation
    N = contingency.sum()
    if N == 0:
        return {"nmi": 0.0, "dominant_tag_per_community": {}}

    # Row and column sums
    row_sums = contingency.sum(axis=1)
    col_sums = contingency.sum(axis=0)

    # Mutual information
    mi = 0.0
    for i in range(contingency.shape[0]):
        for j in range(contingency.shape[1]):
            if contingency[i, j] > 0:
                mi += (contingency[i, j] / N) * math.log(
                    (N * contingency[i, j]) / (row_sums[i] * col_sums[j])
                )

    # Entropies
    H_comm = -sum(
        (r / N) * math.log(r / N) for r in row_sums if r > 0
    )
    H_tag = -sum(
        (c / N) * math.log(c / N) for c in col_sums if c > 0
    )

    nmi = (2 * mi / (H_comm + H_tag)) if (H_comm + H_tag) > 0 else 0.0

    # Dominant tag per community
    dominant = {}
    for cid in comm_ids:
        idx = comm_to_idx[cid]
        best_tag_idx = int(np.argmax(contingency[idx]))
        dominant[cid] = {
            "tag": tag_ids[best_tag_idx],
            "fraction": float(contingency[idx, best_tag_idx] / row_sums[idx])
            if row_sums[idx] > 0
            else 0.0,
        }

    return {
        "nmi": nmi,
        "dominant_tag_per_community": dominant,
    }


# ═══════════════════════════════════════════════════════════════════
# 3. Centrality Analysis
# ═══════════════════════════════════════════════════════════════════

def compute_centralities(G: nx.Graph) -> Dict[str, Dict[int, float]]:
    """
    Compute three centrality measures on the problem network.

    Returns dict of {measure_name: {node: value}}.
    """
    # Use largest connected component for meaningful betweenness/eigenvector
    if not nx.is_connected(G):
        largest_cc = max(nx.connected_components(G), key=len)
        H = G.subgraph(largest_cc).copy()
    else:
        H = G

    pagerank = nx.pagerank(H, weight="weight", alpha=0.85)
    betweenness = nx.betweenness_centrality(H, weight="weight", normalized=True)
    eigenvector = nx.eigenvector_centrality_numpy(H, weight="weight")

    return {
        "pagerank": pagerank,
        "betweenness": betweenness,
        "eigenvector": eigenvector,
    }


def centrality_vs_solved(
    G: nx.Graph, centralities: Dict[str, Dict[int, float]]
) -> Dict[str, Any]:
    """
    Analyze whether central problems are more or less likely to be solved.

    For each centrality measure, compares mean centrality of solved vs open.
    Computes Mann-Whitney U test statistic (non-parametric).
    """
    results = {}

    for measure, scores in centralities.items():
        solved_scores = []
        open_scores = []
        for node, score in scores.items():
            if G.nodes[node].get("is_solved"):
                solved_scores.append(score)
            elif G.nodes[node].get("is_open"):
                open_scores.append(score)

        if not solved_scores or not open_scores:
            results[measure] = {
                "solved_mean": 0.0,
                "open_mean": 0.0,
                "effect_direction": "insufficient_data",
            }
            continue

        solved_arr = np.array(solved_scores)
        open_arr = np.array(open_scores)

        # Mann-Whitney U statistic (manual, avoid scipy dependency)
        # U = number of pairs where solved > open
        u_stat = 0
        n_s, n_o = len(solved_arr), len(open_arr)
        # Use rank-based approach for efficiency
        combined = np.concatenate([solved_arr, open_arr])
        labels = np.array([1] * n_s + [0] * n_o)
        order = np.argsort(combined)
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.arange(1, len(combined) + 1, dtype=float)
        # Handle ties
        sorted_vals = combined[order]
        i = 0
        while i < len(sorted_vals):
            j = i + 1
            while j < len(sorted_vals) and sorted_vals[j] == sorted_vals[i]:
                j += 1
            if j > i + 1:
                avg_rank = np.mean(np.arange(i + 1, j + 1, dtype=float))
                for k in range(i, j):
                    ranks[order[k]] = avg_rank
            i = j

        rank_sum_solved = float(np.sum(ranks[labels == 1]))
        u_solved = rank_sum_solved - n_s * (n_s + 1) / 2
        u_open = n_s * n_o - u_solved

        # Effect size: rank-biserial correlation r = 1 - 2U/(n_s * n_o)
        r_biserial = 1 - 2 * min(u_solved, u_open) / (n_s * n_o)

        results[measure] = {
            "solved_mean": float(np.mean(solved_arr)),
            "open_mean": float(np.mean(open_arr)),
            "solved_median": float(np.median(solved_arr)),
            "open_median": float(np.median(open_arr)),
            "effect_direction": "solved_higher" if np.mean(solved_arr) > np.mean(open_arr) else "open_higher",
            "mann_whitney_U": float(min(u_solved, u_open)),
            "rank_biserial_r": float(r_biserial),
            "n_solved": n_s,
            "n_open": n_o,
        }

    return results


def top_central_problems(
    centralities: Dict[str, Dict[int, float]], top_k: int = 20
) -> Dict[str, List[Tuple[int, float]]]:
    """Return top-k most central problems for each measure."""
    result = {}
    for measure, scores in centralities.items():
        ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
        result[measure] = ranked
    return result


# ═══════════════════════════════════════════════════════════════════
# 4. Temporal Network Analysis
# ═══════════════════════════════════════════════════════════════════

def temporal_analysis(
    G: nx.Graph, n_windows: int = 10
) -> Dict[str, Any]:
    """
    Analyze how the problem network evolves over time.

    Uses problem number as a time proxy: earlier-numbered problems were
    generally posed earlier. Divides the range into windows and measures
    how network properties change.

    Returns
    -------
    dict with:
      - windows: list of {start, end, n_nodes, n_edges, density,
                          avg_degree, clustering, n_components, solve_rate}
      - cumulative: same metrics as problems accumulate
      - connectivity_trend: does connectivity increase or decrease with time?
    """
    sorted_nodes = sorted(G.nodes())
    if not sorted_nodes:
        return {"windows": [], "cumulative": [], "connectivity_trend": "empty"}

    min_num, max_num = sorted_nodes[0], sorted_nodes[-1]
    window_size = max(1, (max_num - min_num + 1) // n_windows)

    windows = []
    cumulative = []
    cumulative_nodes = set()

    for w in range(n_windows):
        start = min_num + w * window_size
        end = start + window_size if w < n_windows - 1 else max_num + 1

        window_nodes = {n for n in sorted_nodes if start <= n < end}
        if not window_nodes:
            continue

        # Subgraph for this window only
        sub = G.subgraph(window_nodes)
        n_nodes_w = sub.number_of_nodes()
        n_edges_w = sub.number_of_edges()
        degrees_w = [d for _, d in sub.degree()]

        n_solved = sum(1 for n in window_nodes if G.nodes[n].get("is_solved"))
        solve_rate = n_solved / n_nodes_w if n_nodes_w > 0 else 0.0

        cc = nx.average_clustering(sub, weight="weight") if n_nodes_w > 1 else 0.0

        windows.append({
            "start": start,
            "end": end,
            "n_nodes": n_nodes_w,
            "n_edges": n_edges_w,
            "density": nx.density(sub) if n_nodes_w > 1 else 0.0,
            "avg_degree": float(np.mean(degrees_w)) if degrees_w else 0.0,
            "clustering": float(cc),
            "n_components": nx.number_connected_components(sub) if n_nodes_w > 0 else 0,
            "solve_rate": solve_rate,
        })

        # Cumulative: all problems up to this window
        cumulative_nodes |= window_nodes
        cum_sub = G.subgraph(cumulative_nodes)
        cum_degrees = [d for _, d in cum_sub.degree()]
        cum_n = cum_sub.number_of_nodes()

        cumulative.append({
            "up_to": end,
            "n_nodes": cum_n,
            "n_edges": cum_sub.number_of_edges(),
            "density": nx.density(cum_sub) if cum_n > 1 else 0.0,
            "avg_degree": float(np.mean(cum_degrees)) if cum_degrees else 0.0,
        })

    # Trend: compare avg degree of first half vs second half windows
    if len(windows) >= 4:
        half = len(windows) // 2
        early_deg = np.mean([w["avg_degree"] for w in windows[:half]])
        late_deg = np.mean([w["avg_degree"] for w in windows[half:]])
        if late_deg > early_deg * 1.1:
            trend = "increasing"
        elif late_deg < early_deg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    return {
        "windows": windows,
        "cumulative": cumulative,
        "connectivity_trend": trend,
    }


# ═══════════════════════════════════════════════════════════════════
# 5. Solved vs Open Subgraphs
# ═══════════════════════════════════════════════════════════════════

def compare_subgraphs(G: nx.Graph) -> Dict[str, Any]:
    """
    Compare network statistics of the solved vs open subgraphs.

    Tests hypothesis: "solved problems cluster together (are more connected)."

    Returns dict with stats for each subgraph and comparison metrics.
    """
    solved_nodes = {n for n in G.nodes() if G.nodes[n].get("is_solved")}
    open_nodes = {n for n in G.nodes() if G.nodes[n].get("is_open")}

    def _subgraph_stats(nodes: set, label: str) -> Dict[str, Any]:
        if len(nodes) < 2:
            return {"label": label, "n_nodes": len(nodes), "stats": "insufficient"}

        sub = G.subgraph(nodes)
        n = sub.number_of_nodes()
        m = sub.number_of_edges()
        degrees = [d for _, d in sub.degree()]
        cc = nx.average_clustering(sub, weight="weight")
        components = list(nx.connected_components(sub))
        largest_cc = max(components, key=len)
        largest_sub = sub.subgraph(largest_cc)

        # Average shortest path in largest component
        if len(largest_cc) > 1:
            # Sample for large graphs
            if len(largest_cc) > 500:
                sampled = list(largest_cc)[:500]
                path_lengths = []
                for src in sampled[:50]:
                    lengths = nx.single_source_shortest_path_length(largest_sub, src)
                    path_lengths.extend(lengths.values())
                avg_path = float(np.mean(path_lengths)) if path_lengths else 0.0
            else:
                avg_path = nx.average_shortest_path_length(largest_sub)
        else:
            avg_path = 0.0

        # Degree distribution
        degree_counts = Counter(degrees)

        return {
            "label": label,
            "n_nodes": n,
            "n_edges": m,
            "density": nx.density(sub),
            "avg_degree": float(np.mean(degrees)),
            "max_degree": max(degrees) if degrees else 0,
            "median_degree": float(np.median(degrees)),
            "clustering_coefficient": float(cc),
            "n_components": len(components),
            "largest_component_frac": len(largest_cc) / n,
            "avg_shortest_path": avg_path,
            "degree_distribution_top5": degree_counts.most_common(5),
        }

    solved_stats = _subgraph_stats(solved_nodes, "solved")
    open_stats = _subgraph_stats(open_nodes, "open")

    # Cross-edges: edges between solved and open
    cross_edges = 0
    for u, v in G.edges():
        u_solved = u in solved_nodes
        v_solved = v in solved_nodes
        u_open = u in open_nodes
        v_open = v in open_nodes
        if (u_solved and v_open) or (u_open and v_solved):
            cross_edges += 1

    return {
        "solved": solved_stats,
        "open": open_stats,
        "cross_edges": cross_edges,
        "more_clustered": (
            "solved"
            if (isinstance(solved_stats.get("clustering_coefficient"), float)
                and isinstance(open_stats.get("clustering_coefficient"), float)
                and solved_stats["clustering_coefficient"] > open_stats["clustering_coefficient"])
            else "open"
        ),
    }


# ═══════════════════════════════════════════════════════════════════
# 6. Solvability Prediction from Network Position
# ═══════════════════════════════════════════════════════════════════

def predict_solvability(
    G: nx.Graph,
    centralities: Dict[str, Dict[int, float]],
    community_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Logistic regression: P(solved) ~ centrality + degree + community_solve_rate.

    Uses numpy-only implementation (no sklearn dependency).

    Returns
    -------
    dict with:
      - coefficients: {feature_name: coefficient}
      - accuracy: classification accuracy on full data
      - auc_approx: approximate AUC from rank ordering
      - top_predictions: open problems ranked by predicted P(solved)
    """
    partition = community_result["partition"]
    profiles = community_result["community_profiles"]

    # Build feature matrix
    feature_names = [
        "pagerank", "betweenness", "eigenvector",
        "degree", "n_tags", "community_solve_rate",
    ]

    nodes = []
    X_rows = []
    y_list = []

    for node in G.nodes():
        if node not in partition:
            continue
        data = G.nodes[node]
        # Only include solved or open (exclude other statuses for clean signal)
        if not data.get("is_solved") and not data.get("is_open"):
            continue

        cid = partition[node]
        comm_sr = profiles.get(cid, {}).get("solve_rate", 0.0)

        row = [
            centralities.get("pagerank", {}).get(node, 0.0),
            centralities.get("betweenness", {}).get(node, 0.0),
            centralities.get("eigenvector", {}).get(node, 0.0),
            float(G.degree(node)),
            float(data.get("n_tags", 0)),
            comm_sr,
        ]
        X_rows.append(row)
        y_list.append(1.0 if data.get("is_solved") else 0.0)
        nodes.append(node)

    if len(X_rows) < 10:
        return {"error": "insufficient_data"}

    X = np.array(X_rows, dtype=float)
    y = np.array(y_list, dtype=float)

    # Standardize features
    means = X.mean(axis=0)
    stds = X.std(axis=0)
    stds[stds == 0] = 1.0
    X_std = (X - means) / stds

    # Add intercept
    X_aug = np.column_stack([np.ones(len(X_std)), X_std])

    # Logistic regression via gradient descent
    n_features = X_aug.shape[1]
    theta = np.zeros(n_features)
    lr = 0.1
    n_iter = 1000
    reg_lambda = 0.01  # L2 regularization

    for _ in range(n_iter):
        z = X_aug @ theta
        z = np.clip(z, -500, 500)
        h = 1.0 / (1.0 + np.exp(-z))
        gradient = X_aug.T @ (h - y) / len(y)
        # L2 regularization (don't regularize intercept)
        gradient[1:] += reg_lambda * theta[1:]
        theta -= lr * gradient

    # Predictions
    z_final = X_aug @ theta
    z_final = np.clip(z_final, -500, 500)
    probs = 1.0 / (1.0 + np.exp(-z_final))
    predictions = (probs >= 0.5).astype(float)
    accuracy = float(np.mean(predictions == y))

    # Approximate AUC via concordance
    solved_probs = probs[y == 1]
    open_probs = probs[y == 0]
    if len(solved_probs) > 0 and len(open_probs) > 0:
        concordant = 0
        total = 0
        # Sample for efficiency
        max_pairs = 50000
        if len(solved_probs) * len(open_probs) > max_pairs:
            rng = np.random.RandomState(42)
            s_idx = rng.choice(len(solved_probs), min(500, len(solved_probs)), replace=False)
            o_idx = rng.choice(len(open_probs), min(500, len(open_probs)), replace=False)
            for si in s_idx:
                for oi in o_idx:
                    total += 1
                    if solved_probs[si] > open_probs[oi]:
                        concordant += 1
                    elif solved_probs[si] == open_probs[oi]:
                        concordant += 0.5
        else:
            for sp in solved_probs:
                for op in open_probs:
                    total += 1
                    if sp > op:
                        concordant += 1
                    elif sp == op:
                        concordant += 0.5
        auc = concordant / total if total > 0 else 0.5
    else:
        auc = 0.5

    # Extract coefficients
    coefficients = {"intercept": float(theta[0])}
    for i, name in enumerate(feature_names):
        coefficients[name] = float(theta[i + 1])

    # Top predictions for open problems
    open_predictions = []
    for i, node in enumerate(nodes):
        if y[i] == 0:  # open
            open_predictions.append((node, float(probs[i])))
    open_predictions.sort(key=lambda x: -x[1])

    return {
        "coefficients": coefficients,
        "accuracy": accuracy,
        "auc_approx": float(auc),
        "n_samples": len(y),
        "n_solved": int(y.sum()),
        "n_open": int(len(y) - y.sum()),
        "feature_names": feature_names,
        "top_predictions": open_predictions[:30],
    }


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(
    G: nx.Graph,
    summary: Dict[str, Any],
    community_result: Dict[str, Any],
    alignment: Dict[str, Any],
    centralities: Dict[str, Dict[int, float]],
    centrality_solved: Dict[str, Any],
    top_central: Dict[str, List[Tuple[int, float]]],
    temporal: Dict[str, Any],
    subgraph_comparison: Dict[str, Any],
    prediction: Dict[str, Any],
) -> str:
    """Generate comprehensive markdown report."""

    lines = [
        "# Problem Network Analysis",
        "",
        "Network science applied to the Erdos problems corpus.",
        "",
        "## 1. Graph Construction",
        "",
        f"- **Nodes**: {summary['n_nodes']} problems",
        f"- **Edges**: {summary['n_edges']}",
        f"- **Density**: {summary['density']:.4f}",
        f"- **Average degree**: {summary['avg_degree']:.1f}",
        f"- **Max degree**: {summary['max_degree']}",
        f"- **Median degree**: {summary['median_degree']:.0f}",
        f"- **Connected components**: {summary['n_components']}",
        f"- **Largest component**: {summary['largest_component_size']} nodes "
        f"({100*summary['largest_component_size']/summary['n_nodes']:.1f}%)",
        "",
        "### Edge type breakdown",
        "",
        "| Edge type | Count | Total weight |",
        "|-----------|-------|-------------|",
    ]
    for etype, count in summary["edge_type_counts"].items():
        tw = summary["edge_type_total_weight"].get(etype, 0)
        lines.append(f"| {etype} | {count:,} | {tw:,.1f} |")

    # Communities
    lines += [
        "",
        "## 2. Community Detection (Louvain)",
        "",
        f"- **Communities found**: {community_result['n_communities']}",
        f"- **Modularity Q**: {community_result['modularity']:.4f}",
        f"- **NMI with tags**: {alignment['nmi']:.4f} "
        f"(1.0 = perfect alignment; low = communities reveal deeper structure)",
        "",
        "### Community profiles (top 15 by size)",
        "",
        "| # | Size | Dominant tag | Solve % | Top tags |",
        "|---|------|-------------|---------|----------|",
    ]
    for cid, size in community_result["community_sizes"][:15]:
        prof = community_result["community_profiles"][cid]
        dom = alignment["dominant_tag_per_community"].get(cid, {})
        dom_tag = dom.get("tag", "?")
        dom_frac = dom.get("fraction", 0)
        sr = prof["solve_rate"]
        top_tags = ", ".join(t for t, _ in prof["top_tags"][:3])
        lines.append(
            f"| {cid} | {size} | {dom_tag} ({dom_frac:.0%}) | {sr:.0%} | {top_tags} |"
        )

    # Centrality
    lines += [
        "",
        "## 3. Centrality Analysis",
        "",
        "### Central problems are more likely to be solved?",
        "",
        "| Measure | Solved mean | Open mean | Direction | Rank-biserial r |",
        "|---------|------------|-----------|-----------|----------------|",
    ]
    for measure in ["pagerank", "betweenness", "eigenvector"]:
        cs = centrality_solved.get(measure, {})
        if cs.get("effect_direction") == "insufficient_data":
            continue
        lines.append(
            f"| {measure} | {cs['solved_mean']:.6f} | {cs['open_mean']:.6f} | "
            f"{cs['effect_direction']} | {cs.get('rank_biserial_r', 0):.3f} |"
        )

    lines += ["", "### Top 15 by PageRank", "", "| Rank | Problem | PageRank |", "|------|---------|----------|"]
    for rank, (node, score) in enumerate(top_central.get("pagerank", [])[:15], 1):
        status_str = G.nodes[node].get("status", "?")
        lines.append(f"| {rank} | #{node} ({status_str}) | {score:.6f} |")

    lines += ["", "### Top 15 by betweenness", "", "| Rank | Problem | Betweenness |", "|------|---------|-------------|"]
    for rank, (node, score) in enumerate(top_central.get("betweenness", [])[:15], 1):
        status_str = G.nodes[node].get("status", "?")
        lines.append(f"| {rank} | #{node} ({status_str}) | {score:.6f} |")

    # Temporal
    lines += [
        "",
        "## 4. Temporal Network Evolution",
        "",
        f"**Connectivity trend**: {temporal['connectivity_trend']}",
        "",
        "| Window | Problems | Edges | Density | Avg degree | Clustering | Solve % |",
        "|--------|----------|-------|---------|------------|------------|---------|",
    ]
    for w in temporal["windows"]:
        lines.append(
            f"| {w['start']}-{w['end']-1} | {w['n_nodes']} | {w['n_edges']} | "
            f"{w['density']:.4f} | {w['avg_degree']:.1f} | {w['clustering']:.3f} | "
            f"{w['solve_rate']:.0%} |"
        )

    # Subgraph comparison
    lines += [
        "",
        "## 5. Solved vs. Open Subgraphs",
        "",
        f"**Cross-edges** (solved-open): {subgraph_comparison['cross_edges']}",
        f"**More clustered**: {subgraph_comparison['more_clustered']} subgraph",
        "",
        "| Metric | Solved | Open |",
        "|--------|--------|------|",
    ]
    sol = subgraph_comparison["solved"]
    opn = subgraph_comparison["open"]
    if isinstance(sol.get("stats"), str) or isinstance(opn.get("stats"), str):
        lines.append("| (insufficient data for comparison) | | |")
    else:
        for metric in [
            "n_nodes", "n_edges", "density", "avg_degree", "max_degree",
            "clustering_coefficient", "n_components", "largest_component_frac",
            "avg_shortest_path",
        ]:
            sv = sol.get(metric, "N/A")
            ov = opn.get(metric, "N/A")
            if isinstance(sv, float):
                sv = f"{sv:.4f}"
            if isinstance(ov, float):
                ov = f"{ov:.4f}"
            lines.append(f"| {metric} | {sv} | {ov} |")

    # Prediction
    lines += [
        "",
        "## 6. Solvability Prediction from Network Position",
        "",
    ]
    if "error" in prediction:
        lines.append(f"Prediction failed: {prediction['error']}")
    else:
        lines += [
            f"- **Accuracy**: {prediction['accuracy']:.1%}",
            f"- **AUC (approx)**: {prediction['auc_approx']:.3f}",
            f"- **Samples**: {prediction['n_samples']} ({prediction['n_solved']} solved, {prediction['n_open']} open)",
            "",
            "### Feature coefficients (standardized)",
            "",
            "| Feature | Coefficient | Direction |",
            "|---------|------------|-----------|",
        ]
        for feat, coef in prediction["coefficients"].items():
            direction = "+" if coef > 0 else "-"
            lines.append(f"| {feat} | {coef:+.4f} | {direction} |")

        lines += [
            "",
            "### Top 20 open problems predicted most likely to be solved",
            "",
            "| Rank | Problem | P(solved) |",
            "|------|---------|-----------|",
        ]
        for rank, (node, prob) in enumerate(prediction["top_predictions"][:20], 1):
            lines.append(f"| {rank} | #{node} | {prob:.3f} |")

    lines.append("")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def run_full_analysis(problems: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Run the complete network analysis pipeline.

    Returns a dict with all intermediate results for testing.
    """
    if problems is None:
        problems = load_problems()

    print(f"Building problem network from {len(problems)} problems...")
    G = build_problem_graph(problems)
    summary = graph_summary(G)
    print(f"  {summary['n_nodes']} nodes, {summary['n_edges']} edges, "
          f"density={summary['density']:.4f}")

    print("Detecting communities...")
    community_result = detect_communities(G)
    print(f"  Found {community_result['n_communities']} communities, "
          f"Q={community_result['modularity']:.4f}")

    alignment = community_tag_alignment(G, community_result)
    print(f"  NMI with tags: {alignment['nmi']:.4f}")

    print("Computing centralities...")
    centralities = compute_centralities(G)
    centrality_solved = centrality_vs_solved(G, centralities)
    top_central = top_central_problems(centralities)

    for measure in ["pagerank", "betweenness", "eigenvector"]:
        top3 = top_central[measure][:3]
        print(f"  Top {measure}: {', '.join(f'#{n}' for n, _ in top3)}")

    print("Analyzing temporal evolution...")
    temporal = temporal_analysis(G)
    print(f"  Connectivity trend: {temporal['connectivity_trend']}")

    print("Comparing solved vs. open subgraphs...")
    subgraph_comp = compare_subgraphs(G)
    print(f"  More clustered: {subgraph_comp['more_clustered']} subgraph")

    print("Predicting solvability from network position...")
    prediction = predict_solvability(G, centralities, community_result)
    if "error" not in prediction:
        print(f"  Accuracy: {prediction['accuracy']:.1%}, "
              f"AUC: {prediction['auc_approx']:.3f}")
    else:
        print(f"  {prediction['error']}")

    report = generate_report(
        G, summary, community_result, alignment, centralities,
        centrality_solved, top_central, temporal, subgraph_comp, prediction,
    )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report)
    print(f"\nReport written to {REPORT_PATH}")

    return {
        "graph": G,
        "summary": summary,
        "community_result": community_result,
        "alignment": alignment,
        "centralities": centralities,
        "centrality_vs_solved": centrality_solved,
        "top_central": top_central,
        "temporal": temporal,
        "subgraph_comparison": subgraph_comp,
        "prediction": prediction,
    }


if __name__ == "__main__":
    run_full_analysis()
