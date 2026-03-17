#!/usr/bin/env python3
"""
spectral_analysis.py — Graph-theoretic deep analysis of the Erdős problem network.

Uses spectral methods on the conjecture similarity graph to discover:
  1. Community structure via Fiedler vector (spectral bisection)
  2. Bottleneck edges (algebraic connectivity)
  3. Bridge problems connecting otherwise-disconnected research areas
  4. Spectral gap analysis (how well-connected is the network?)
  5. PageRank-like influence scoring

Output: docs/spectral_report.md
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
REPORT_PATH = ROOT / "docs" / "spectral_report.md"


# ═══════════════════════════════════════════════════════════════════
# Data Loading
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


# ═══════════════════════════════════════════════════════════════════
# Graph Construction
# ═══════════════════════════════════════════════════════════════════

def build_problem_graph(problems: List[Dict], max_nodes: int = 400) -> Tuple[
    np.ndarray, List[int], Dict[int, Dict]
]:
    """
    Build weighted adjacency matrix for the problem similarity network.

    Edge weights:
    - OEIS overlap: weight 3 per shared sequence
    - Tag overlap ≥ 2: weight = overlap count
    - Tag overlap ≥ 3: bonus weight +2

    Returns:
        adj_matrix: n×n weighted adjacency matrix
        node_ids: list of problem numbers (maps index to problem)
        node_info: dict mapping problem number to problem metadata
    """
    open_probs = [p for p in problems if _status(p) == "open"][:max_nodes]

    node_ids = [_number(p) for p in open_probs]
    node_info = {_number(p): {
        "tags": sorted(_tags(p)),
        "oeis": _oeis(p),
        "prize": _prize(p),
    } for p in open_probs}

    n = len(open_probs)
    adj = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            p1, p2 = open_probs[i], open_probs[j]
            t1, t2 = _tags(p1), _tags(p2)
            shared_oeis = set(_oeis(p1)) & set(_oeis(p2))
            tag_overlap = len(t1 & t2)

            weight = 0
            weight += len(shared_oeis) * 3
            if tag_overlap >= 2:
                weight += tag_overlap
            if tag_overlap >= 3:
                weight += 2

            if weight > 0:
                adj[i, j] = weight
                adj[j, i] = weight

    return adj, node_ids, node_info


# ═══════════════════════════════════════════════════════════════════
# 1. Laplacian Spectrum
# ═══════════════════════════════════════════════════════════════════

def laplacian_spectrum(adj: np.ndarray) -> Dict[str, Any]:
    """
    Compute the graph Laplacian and its spectrum.

    Key quantities:
    - λ₂ (algebraic connectivity / Fiedler value): measures how connected the graph is
    - Spectral gap: λ₂/λ_max ratio
    - Fiedler vector: eigenvector for λ₂ gives optimal bisection
    """
    n = adj.shape[0]
    degree = adj.sum(axis=1)
    D = np.diag(degree)
    L = D - adj  # Unnormalized Laplacian

    # Compute eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eigh(L)

    # Sort by eigenvalue (should already be sorted, but ensure)
    idx = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Clamp near-zero eigenvalues (floating point artifacts)
    eigenvalues = np.maximum(eigenvalues, 0.0)

    # λ₂ = Fiedler value (algebraic connectivity)
    lambda2 = float(eigenvalues[1]) if n > 1 else 0.0
    lambda_max = float(eigenvalues[-1]) if n > 0 else 0.0

    # Fiedler vector
    fiedler = eigenvectors[:, 1] if n > 1 else np.zeros(n)

    # Spectral gap ratio
    spectral_gap = lambda2 / lambda_max if lambda_max > 0 else 0.0

    return {
        "algebraic_connectivity": round(lambda2, 4),
        "spectral_gap": round(spectral_gap, 6),
        "lambda_max": round(lambda_max, 4),
        "fiedler_vector": fiedler,
        "eigenvalues": eigenvalues[:20].tolist(),  # first 20
        "num_zero_eigenvalues": int(np.sum(eigenvalues < 1e-10)),
    }


# ═══════════════════════════════════════════════════════════════════
# 2. Spectral Bisection (Community Detection)
# ═══════════════════════════════════════════════════════════════════

def spectral_bisection(
    adj: np.ndarray, node_ids: List[int], node_info: Dict
) -> Dict[str, Any]:
    """
    Bisect the graph using the Fiedler vector.

    Nodes with positive Fiedler component go to one side,
    negative to the other. This minimizes the edge cut.
    """
    spectrum = laplacian_spectrum(adj)
    fiedler = spectrum["fiedler_vector"]

    # Partition
    side_a = [node_ids[i] for i in range(len(node_ids)) if fiedler[i] >= 0]
    side_b = [node_ids[i] for i in range(len(node_ids)) if fiedler[i] < 0]

    # Tag profile for each side
    def tag_profile(ids):
        counts = Counter()
        for nid in ids:
            if nid in node_info:
                for t in node_info[nid]["tags"]:
                    counts[t] += 1
        return counts.most_common(5)

    profile_a = tag_profile(side_a)
    profile_b = tag_profile(side_b)

    # Count edges cut
    cut_weight = 0.0
    n = adj.shape[0]
    for i in range(n):
        for j in range(i + 1, n):
            if adj[i, j] > 0:
                if (fiedler[i] >= 0) != (fiedler[j] >= 0):
                    cut_weight += adj[i, j]

    total_weight = adj.sum() / 2

    return {
        "side_a_size": len(side_a),
        "side_b_size": len(side_b),
        "side_a_tags": profile_a,
        "side_b_tags": profile_b,
        "cut_weight": round(cut_weight, 1),
        "total_weight": round(total_weight, 1),
        "cut_ratio": round(cut_weight / max(total_weight, 1), 4),
        "algebraic_connectivity": spectrum["algebraic_connectivity"],
        "spectral_gap": spectrum["spectral_gap"],
    }


# ═══════════════════════════════════════════════════════════════════
# 3. Bridge Problem Detection
# ═══════════════════════════════════════════════════════════════════

def bridge_problems(
    adj: np.ndarray, node_ids: List[int], node_info: Dict
) -> Dict[str, Any]:
    """
    Identify bridge problems — nodes whose removal most increases
    the spectral gap (i.e., most disconnects the network).

    Uses a proxy: nodes with high betweenness-like centrality
    (connected to both sides of the Fiedler bisection).
    """
    spectrum = laplacian_spectrum(adj)
    fiedler = spectrum["fiedler_vector"]
    n = len(node_ids)

    # Bridge score: abs(fiedler[i]) is small AND degree is high
    # (problem sits at the boundary between communities)
    degrees = adj.sum(axis=1)

    bridge_scores = []
    for i in range(n):
        if degrees[i] == 0:
            continue
        # Low |fiedler[i]| = near boundary; high degree = important
        boundary_proximity = 1.0 / (abs(fiedler[i]) + 0.01)
        bridge_score = boundary_proximity * math.log1p(degrees[i])

        # Count neighbors on each side
        neighbors_a = sum(1 for j in range(n) if adj[i, j] > 0 and fiedler[j] >= 0)
        neighbors_b = sum(1 for j in range(n) if adj[i, j] > 0 and fiedler[j] < 0)
        cross_frac = min(neighbors_a, neighbors_b) / max(neighbors_a + neighbors_b, 1)

        bridge_scores.append({
            "number": node_ids[i],
            "bridge_score": round(bridge_score, 2),
            "fiedler_value": round(float(fiedler[i]), 4),
            "degree": int(degrees[i]),
            "cross_fraction": round(cross_frac, 3),
            "tags": node_info.get(node_ids[i], {}).get("tags", []),
            "prize": node_info.get(node_ids[i], {}).get("prize", 0),
        })

    bridge_scores.sort(key=lambda x: -x["bridge_score"])

    return {
        "bridges": bridge_scores[:20],
        "total_scored": len(bridge_scores),
    }


# ═══════════════════════════════════════════════════════════════════
# 4. PageRank-like Influence
# ═══════════════════════════════════════════════════════════════════

def pagerank_influence(
    adj: np.ndarray, node_ids: List[int], node_info: Dict,
    damping: float = 0.85, n_iter: int = 50
) -> Dict[str, Any]:
    """
    Compute PageRank on the problem similarity graph.

    High PageRank = problem is connected to many important problems.
    This is different from raw degree: a problem connected to hubs
    gets higher PageRank than one connected to leaves.
    """
    n = adj.shape[0]
    if n == 0:
        return {"rankings": [], "convergence": True}

    # Normalize adjacency to column-stochastic matrix
    col_sums = adj.sum(axis=0)
    col_sums[col_sums == 0] = 1  # avoid division by zero
    M = adj / col_sums

    # Power iteration
    rank = np.ones(n) / n
    for iteration in range(n_iter):
        new_rank = (1 - damping) / n + damping * (M @ rank)
        if np.linalg.norm(new_rank - rank) < 1e-8:
            rank = new_rank
            break
        rank = new_rank

    # Normalize
    rank /= rank.sum()

    # Build rankings
    rankings = []
    for i in range(n):
        rankings.append({
            "number": node_ids[i],
            "pagerank": round(float(rank[i]), 6),
            "tags": node_info.get(node_ids[i], {}).get("tags", []),
            "prize": node_info.get(node_ids[i], {}).get("prize", 0),
            "degree": int(adj[i].sum()),
        })

    rankings.sort(key=lambda x: -x["pagerank"])

    # Compute correlation between PageRank and degree
    pr_values = rank
    degree_values = adj.sum(axis=1)
    if np.std(pr_values) > 0 and np.std(degree_values) > 0:
        correlation = float(np.corrcoef(pr_values, degree_values)[0, 1])
    else:
        correlation = 0.0

    return {
        "rankings": rankings[:30],
        "pr_degree_correlation": round(correlation, 3),
        "max_pagerank": round(float(rank.max()), 6),
        "min_pagerank": round(float(rank.min()), 6),
        "gini_coefficient": _gini(rank),
    }


def _gini(x: np.ndarray) -> float:
    """Compute Gini coefficient of array."""
    x = np.sort(x)
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    index = np.arange(1, n + 1)
    return float(round(2 * np.sum(index * x) / (n * x.sum()) - (n + 1) / n, 4))


# ═══════════════════════════════════════════════════════════════════
# 5. Multi-Scale Community Detection
# ═══════════════════════════════════════════════════════════════════

def spectral_communities(
    adj: np.ndarray, node_ids: List[int], node_info: Dict,
    n_communities: int = 5
) -> Dict[str, Any]:
    """
    Use the first k eigenvectors of the Laplacian to partition
    problems into k communities (spectral clustering).
    """
    n = adj.shape[0]
    if n <= n_communities:
        return {"communities": [], "n_communities": 0}

    degree = adj.sum(axis=1)
    D = np.diag(degree)
    L = D - adj

    eigenvalues, eigenvectors = np.linalg.eigh(L)
    idx = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Use eigenvectors 1..k for k-means clustering
    k = min(n_communities, n - 1)
    Z = eigenvectors[:, 1:k+1]

    # Normalize rows
    norms = np.linalg.norm(Z, axis=1, keepdims=True)
    norms[norms == 0] = 1
    Z = Z / norms

    # Simple k-means on spectral embedding
    np.random.seed(42)
    centroids_idx = np.random.choice(n, k, replace=False)
    centroids = Z[centroids_idx].copy()
    labels = np.zeros(n, dtype=int)

    for _ in range(30):
        # Assign
        for i in range(n):
            dists = [np.linalg.norm(Z[i] - centroids[c]) for c in range(k)]
            labels[i] = int(np.argmin(dists))
        # Update
        new_centroids = np.zeros_like(centroids)
        for c in range(k):
            members = Z[labels == c]
            if len(members) > 0:
                new_centroids[c] = members.mean(axis=0)
            else:
                new_centroids[c] = centroids[c]
        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids

    # Analyze communities
    communities = []
    for c in range(k):
        member_idx = [i for i in range(n) if labels[i] == c]
        member_ids = [node_ids[i] for i in member_idx]

        tag_counts = Counter()
        total_prize = 0.0
        for nid in member_ids:
            info = node_info.get(nid, {})
            for t in info.get("tags", []):
                tag_counts[t] += 1
            total_prize += info.get("prize", 0)

        # Intra-community edge density
        intra_edges = 0
        possible_edges = len(member_idx) * (len(member_idx) - 1) // 2
        for i in member_idx:
            for j in member_idx:
                if i < j and adj[i, j] > 0:
                    intra_edges += 1

        density = intra_edges / max(possible_edges, 1)

        communities.append({
            "id": c,
            "size": len(member_idx),
            "dominant_tags": tag_counts.most_common(5),
            "total_prize": round(total_prize, 0),
            "density": round(density, 4),
            "sample_problems": member_ids[:5],
        })

    communities.sort(key=lambda c: -c["size"])

    # Compute modularity
    total_edges = adj.sum() / 2
    modularity = 0.0
    if total_edges > 0:
        for c in range(k):
            member_idx = [i for i in range(n) if labels[i] == c]
            for i in member_idx:
                for j in member_idx:
                    if i != j:
                        modularity += adj[i, j] - degree[i] * degree[j] / (2 * total_edges)
        modularity /= (2 * total_edges)

    return {
        "n_communities": k,
        "communities": communities,
        "modularity": round(float(modularity), 4),
        "eigenvalue_gaps": [
            round(float(eigenvalues[i+1] - eigenvalues[i]), 4)
            for i in range(min(10, len(eigenvalues) - 1))
        ],
    }


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(spectrum, bisection, bridges, pagerank, communities) -> str:
    lines = []
    lines.append("# Spectral Analysis of the Erdős Problem Network")
    lines.append("")
    lines.append("Graph-theoretic deep analysis using spectral methods.")
    lines.append("")

    # 1. Spectrum
    lines.append("## 1. Laplacian Spectrum")
    lines.append("")
    lines.append(f"- **Algebraic connectivity (λ₂)**: {spectrum['algebraic_connectivity']}")
    lines.append(f"- **Spectral gap (λ₂/λ_max)**: {spectrum['spectral_gap']}")
    lines.append(f"- **Max eigenvalue**: {spectrum['lambda_max']}")
    lines.append(f"- **Zero eigenvalues (components)**: {spectrum['num_zero_eigenvalues']}")
    lines.append("")
    lines.append("First 10 eigenvalues: " + ", ".join(f"{e:.3f}" for e in spectrum["eigenvalues"][:10]))
    lines.append("")

    # 2. Bisection
    lines.append("## 2. Spectral Bisection")
    lines.append("")
    lines.append(f"- Side A: {bisection['side_a_size']} problems")
    lines.append(f"- Side B: {bisection['side_b_size']} problems")
    lines.append(f"- Cut weight: {bisection['cut_weight']} / {bisection['total_weight']} ({bisection['cut_ratio']:.1%})")
    lines.append("")

    lines.append("### Side A Profile")
    for tag, count in bisection["side_a_tags"]:
        lines.append(f"  - {tag}: {count}")
    lines.append("")

    lines.append("### Side B Profile")
    for tag, count in bisection["side_b_tags"]:
        lines.append(f"  - {tag}: {count}")
    lines.append("")

    # 3. Bridge Problems
    lines.append("## 3. Bridge Problems (Cross-Community Connectors)")
    lines.append("")
    lines.append("Problems that connect otherwise-disconnected research areas.")
    lines.append("")
    lines.append("| Rank | Problem | Bridge Score | Fiedler | Degree | Cross% | Tags |")
    lines.append("|------|---------|-------------|---------|--------|--------|------|")
    for i, b in enumerate(bridges["bridges"][:15]):
        tags = ", ".join(b["tags"][:2])
        prize = f" (${b['prize']:.0f})" if b["prize"] > 0 else ""
        lines.append(
            f"| {i+1} | #{b['number']}{prize} | {b['bridge_score']} | "
            f"{b['fiedler_value']} | {b['degree']} | {b['cross_fraction']:.0%} | {tags} |"
        )
    lines.append("")

    # 4. PageRank
    lines.append("## 4. PageRank Influence")
    lines.append("")
    lines.append(f"- PageRank-degree correlation: {pagerank['pr_degree_correlation']}")
    lines.append(f"- Gini coefficient: {pagerank['gini_coefficient']}")
    lines.append(f"  (0 = uniform influence, 1 = concentrated in few problems)")
    lines.append("")
    lines.append("| Rank | Problem | PageRank | Degree | Tags | Prize |")
    lines.append("|------|---------|----------|--------|------|-------|")
    for i, r in enumerate(pagerank["rankings"][:15]):
        tags = ", ".join(r["tags"][:2])
        prize = f"${r['prize']:.0f}" if r["prize"] > 0 else "-"
        lines.append(
            f"| {i+1} | #{r['number']} | {r['pagerank']:.6f} | "
            f"{r['degree']} | {tags} | {prize} |"
        )
    lines.append("")

    # 5. Communities
    lines.append("## 5. Spectral Communities")
    lines.append("")
    lines.append(f"- Communities found: {communities['n_communities']}")
    lines.append(f"- Modularity: {communities['modularity']}")
    lines.append("")

    if communities.get("eigenvalue_gaps"):
        lines.append("### Eigenvalue Gaps (community count signal)")
        lines.append("")
        lines.append("Large gaps indicate natural community boundaries:")
        for i, gap in enumerate(communities["eigenvalue_gaps"]):
            marker = " ◄" if gap > 1.0 else ""
            lines.append(f"  λ{i+1}→λ{i+2}: gap = {gap:.3f}{marker}")
        lines.append("")

    for comm in communities["communities"]:
        lines.append(f"### Community {comm['id']} ({comm['size']} problems)")
        lines.append(f"- Density: {comm['density']:.3f}")
        if comm["total_prize"] > 0:
            lines.append(f"- Total prize: ${comm['total_prize']:.0f}")
        lines.append(f"- Dominant tags: {', '.join(f'{t}({c})' for t, c in comm['dominant_tags'][:3])}")
        lines.append(f"- Examples: {', '.join(f'#{n}' for n in comm['sample_problems'])}")
        lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("SPECTRAL ANALYSIS")
    print("=" * 70)

    problems = load_problems()
    print(f"Loaded {len(problems)} problems")

    print("\nBuilding problem graph...")
    adj, node_ids, node_info = build_problem_graph(problems)
    print(f"  {len(node_ids)} nodes, {int(np.sum(adj > 0) // 2)} edges")

    print("\n1. Computing Laplacian spectrum...")
    spectrum = laplacian_spectrum(adj)
    print(f"  λ₂ = {spectrum['algebraic_connectivity']}, gap = {spectrum['spectral_gap']}")

    print("\n2. Spectral bisection...")
    bisection = spectral_bisection(adj, node_ids, node_info)
    print(f"  Side A: {bisection['side_a_size']}, Side B: {bisection['side_b_size']}")

    print("\n3. Finding bridge problems...")
    bridges = bridge_problems(adj, node_ids, node_info)
    print(f"  Top bridge: #{bridges['bridges'][0]['number']}" if bridges["bridges"] else "  No bridges")

    print("\n4. Computing PageRank...")
    pr = pagerank_influence(adj, node_ids, node_info)
    print(f"  Top PR: #{pr['rankings'][0]['number']}" if pr["rankings"] else "  No rankings")

    print("\n5. Spectral community detection...")
    comms = spectral_communities(adj, node_ids, node_info)
    print(f"  {comms['n_communities']} communities, modularity = {comms['modularity']}")

    print("\nGenerating report...")
    report = generate_report(spectrum, bisection, bridges, pr, comms)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"Saved to {REPORT_PATH}")

    print("\n" + "=" * 70)
    print("SPECTRAL ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
