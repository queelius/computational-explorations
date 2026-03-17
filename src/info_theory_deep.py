#!/usr/bin/env python3
"""
info_theory_deep.py -- Deep information-theoretic analysis of Erdos problems.

Five analysis layers:
  1. Coprime graph entropy: degree-sequence entropy vs random graphs
  2. Mutual information between problem features and solvability
  3. Kolmogorov complexity proxy via compression
  4. Channel capacity of the coprime Ramsey "channel"
  5. Minimum description length for Ramsey witnesses
"""

import math
import zlib
import yaml
import numpy as np
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# -- Paths -----------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"


# =========================================================================
# Shared helpers (problem YAML)
# =========================================================================

def load_problems() -> List[Dict]:
    """Load the Erdos problems YAML."""
    with open(DATA_PATH) as f:
        return yaml.safe_load(f)


def _status(p: Dict) -> str:
    return p.get("status", {}).get("state", "unknown")


def _tags(p: Dict) -> Set[str]:
    return set(p.get("tags", []))


def _number(p: Dict) -> int:
    n = p.get("number", 0)
    return int(n) if isinstance(n, (int, str)) and str(n).isdigit() else 0


def _is_solved(p: Dict) -> bool:
    return _status(p) in (
        "proved", "disproved", "solved",
        "proved (Lean)", "disproved (Lean)", "solved (Lean)",
    )


def _is_formalized(p: Dict) -> bool:
    return p.get("formalized", {}).get("state", "no") == "yes"


def _oeis_sequences(p: Dict) -> List[str]:
    """Return real OEIS sequences, filtering N/A and possible entries."""
    raw = p.get("oeis", [])
    if not raw:
        return []
    return [
        s for s in raw
        if s and isinstance(s, str)
        and s.startswith("A")
        and s not in ("N/A", "possible")
        and not s.startswith("A00000")
    ]


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


# =========================================================================
# Core information-theoretic primitives
# =========================================================================

def shannon_entropy(counts: np.ndarray) -> float:
    """H(X) in bits from a count array.  Ignores zeros."""
    total = counts.sum()
    if total == 0:
        return 0.0
    probs = counts / total
    probs = probs[probs > 0]
    return float(-np.sum(probs * np.log2(probs)))


def entropy_from_labels(labels: List) -> float:
    """Shannon entropy from a label list."""
    n = len(labels)
    if n == 0:
        return 0.0
    counts = np.array(list(Counter(labels).values()), dtype=float)
    return shannon_entropy(counts)


def mutual_information_labels(x: List, y: List) -> float:
    """I(X;Y) = H(Y) - H(Y|X) from two label lists."""
    n = len(x)
    if n == 0:
        return 0.0
    hy = entropy_from_labels(y)
    # H(Y|X) = sum_x P(x) H(Y|X=x)
    groups: Dict[Any, List] = {}
    for xi, yi in zip(x, y):
        groups.setdefault(xi, []).append(yi)
    hy_given_x = sum(
        len(g) / n * entropy_from_labels(g) for g in groups.values()
    )
    return max(hy - hy_given_x, 0.0)  # clamp rounding noise


def normalized_mi(x: List, y: List) -> float:
    """NMI = I(X;Y) / sqrt(H(X)*H(Y)), in [0,1]."""
    mi = mutual_information_labels(x, y)
    hx = entropy_from_labels(x)
    hy = entropy_from_labels(y)
    denom = math.sqrt(hx * hy) if hx > 0 and hy > 0 else 0.0
    return mi / denom if denom > 0 else 0.0


# =========================================================================
# 1. Coprime graph entropy
# =========================================================================

def coprime_graph_edges(n: int) -> List[Tuple[int, int]]:
    """All coprime pairs (i,j) with 1 <= i < j <= n."""
    edges = []
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                edges.append((i, j))
    return edges


def degree_sequence(n: int) -> np.ndarray:
    """Degree of each vertex in the coprime graph G([n])."""
    deg = np.zeros(n + 1, dtype=int)  # 1-indexed
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                deg[i] += 1
                deg[j] += 1
    return deg[1:]  # drop index 0


def graph_entropy(n: int) -> Dict[str, float]:
    """
    Entropy of the coprime graph G([n]):
      H(G) = Shannon entropy of the degree distribution.

    Also returns edge density for comparison with Erdos-Renyi.
    """
    deg = degree_sequence(n)
    counts = np.array(list(Counter(deg).values()), dtype=float)
    h = shannon_entropy(counts)
    max_edges = n * (n - 1) / 2
    num_edges = int(deg.sum() / 2)
    density = num_edges / max_edges if max_edges > 0 else 0.0
    return {
        "n": n,
        "num_edges": num_edges,
        "density": round(density, 6),
        "degree_entropy": round(h, 6),
        "max_degree": int(deg.max()),
        "min_degree": int(deg.min()),
        "mean_degree": round(float(deg.mean()), 3),
    }


def erdos_renyi_degree_entropy(n: int, p: float, trials: int = 50) -> float:
    """
    Expected degree-sequence entropy of G(n,p).

    We sample ``trials`` ER graphs and return the mean entropy.
    """
    rng = np.random.default_rng(seed=42)
    entropies = []
    for _ in range(trials):
        deg = np.zeros(n, dtype=int)
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < p:
                    deg[i] += 1
                    deg[j] += 1
        counts = np.array(list(Counter(deg).values()), dtype=float)
        entropies.append(shannon_entropy(counts))
    return float(np.mean(entropies))


def coprime_vs_random_entropy(ns: Optional[List[int]] = None) -> List[Dict]:
    """
    Compare coprime graph entropy with random graphs of same density.

    For each n, compute H(G(n)) and E[H(ER(n, density(G(n))))].
    """
    if ns is None:
        ns = [5, 10, 20, 50, 100]
    results = []
    for n in ns:
        info = graph_entropy(n)
        p = info["density"]
        er_h = erdos_renyi_degree_entropy(n, p, trials=30)
        results.append({
            "n": n,
            "coprime_entropy": info["degree_entropy"],
            "er_entropy": round(er_h, 6),
            "entropy_ratio": round(info["degree_entropy"] / er_h, 4) if er_h > 0 else float("inf"),
            "density": info["density"],
            "num_edges": info["num_edges"],
            "mean_degree": info["mean_degree"],
        })
    return results


# =========================================================================
# 2. Mutual information between problem features
# =========================================================================

def feature_importance(problems: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Information-theoretic feature importance ranking.

    Computes I(feature; solved) for several feature types and returns
    a sorted ranking of features by mutual information.
    """
    if problems is None:
        problems = load_problems()

    solved_labels = ["solved" if _is_solved(p) else "open" for p in problems]
    h_solved = entropy_from_labels(solved_labels)

    features: Dict[str, List] = {}

    # -- tag features (top-level tag presence) --
    all_tags = sorted({t for p in problems for t in _tags(p)})
    for tag in all_tags:
        features[f"tag:{tag}"] = [
            1 if tag in _tags(p) else 0 for p in problems
        ]

    # -- formalized --
    features["formalized"] = [
        1 if _is_formalized(p) else 0 for p in problems
    ]

    # -- OEIS (has at least one real sequence) --
    features["has_oeis"] = [
        1 if _oeis_sequences(p) else 0 for p in problems
    ]
    features["oeis_count"] = [len(_oeis_sequences(p)) for p in problems]

    # -- prize --
    features["has_prize"] = [1 if _prize(p) > 0 else 0 for p in problems]
    features["prize_bucket"] = [
        "high" if _prize(p) > 1000
        else ("medium" if _prize(p) > 100
              else ("low" if _prize(p) > 0 else "none"))
        for p in problems
    ]

    # -- tag count --
    features["tag_count"] = [len(_tags(p)) for p in problems]

    rows = []
    for name, vals in features.items():
        mi = mutual_information_labels(vals, solved_labels)
        nmi = normalized_mi(vals, solved_labels)
        rows.append({
            "feature": name,
            "mutual_information": round(mi, 6),
            "nmi": round(nmi, 4),
        })

    rows.sort(key=lambda r: -r["mutual_information"])
    return {
        "base_entropy": round(h_solved, 6),
        "features": rows,
        "most_informative": rows[0]["feature"] if rows else None,
    }


# =========================================================================
# 3. Kolmogorov complexity proxy
# =========================================================================

def _problem_descriptor(p: Dict) -> str:
    """Build a canonical descriptor string for a problem."""
    parts = []
    for tag in sorted(_tags(p)):
        parts.append(tag)
    for seq in sorted(_oeis_sequences(p)):
        parts.append(seq)
    return "|".join(parts)


def compressed_size(s: str) -> int:
    """zlib-compressed byte length -- proxy for Kolmogorov complexity."""
    return len(zlib.compress(s.encode("utf-8"), level=9))


def kolmogorov_proxy(problems: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Approximate K(problem) by compression of the tag+oeis descriptor.

    Returns per-problem complexity, plus Pearson correlation with solve
    probability.
    """
    if problems is None:
        problems = load_problems()

    records = []
    for p in problems:
        desc = _problem_descriptor(p)
        raw_len = len(desc.encode("utf-8"))
        clen = compressed_size(desc)
        solved = 1 if _is_solved(p) else 0
        records.append({
            "number": _number(p),
            "raw_length": raw_len,
            "compressed_length": clen,
            "compression_ratio": round(clen / raw_len, 4) if raw_len > 0 else 1.0,
            "solved": solved,
        })

    comp_lengths = np.array([r["compressed_length"] for r in records], dtype=float)
    solved_arr = np.array([r["solved"] for r in records], dtype=float)

    # Pearson correlation between compressed size and solved indicator
    if np.std(comp_lengths) > 0 and np.std(solved_arr) > 0:
        corr = float(np.corrcoef(comp_lengths, solved_arr)[0, 1])
    else:
        corr = 0.0

    # Split into solved/open groups
    solved_sizes = comp_lengths[solved_arr == 1]
    open_sizes = comp_lengths[solved_arr == 0]

    return {
        "records": records,
        "correlation": round(corr, 4),
        "mean_compressed_solved": round(float(solved_sizes.mean()), 2) if len(solved_sizes) > 0 else 0.0,
        "mean_compressed_open": round(float(open_sizes.mean()), 2) if len(open_sizes) > 0 else 0.0,
        "interpretation": (
            "negative correlation means solved problems have shorter descriptors"
            if corr < -0.05
            else (
                "positive correlation means harder problems have more complex descriptors"
                if corr > 0.05
                else "no significant correlation between complexity and solvability"
            )
        ),
    }


# =========================================================================
# 4. Channel capacity of coprime Ramsey "channel"
# =========================================================================

def _has_mono_clique(n: int, k: int, coloring: Dict[Tuple[int, int], int]) -> bool:
    """True if coloring of G([n]) has a monochromatic K_k."""
    for subset in combinations(range(1, n + 1), k):
        # Check all pairs coprime
        all_coprime = True
        for i in range(len(subset)):
            for j in range(i + 1, len(subset)):
                if math.gcd(subset[i], subset[j]) != 1:
                    all_coprime = False
                    break
            if not all_coprime:
                break
        if not all_coprime:
            continue
        # Check monochromatic
        colors = set()
        for i in range(len(subset)):
            for j in range(i + 1, len(subset)):
                e = (min(subset[i], subset[j]), max(subset[i], subset[j]))
                colors.add(coloring.get(e, -1))
        if len(colors) == 1:
            return True
    return False


def count_avoiding_colorings(n: int, k: int) -> Tuple[int, int]:
    """
    Count 2-colorings of G([n]) that avoid monochromatic K_k.

    Uses incremental extension from a base where exhaustive enumeration
    is feasible (edges <= 25).

    Returns (avoiding_count, total_colorings).
    """
    edges = coprime_graph_edges(n)
    m = len(edges)

    if m == 0:
        return (1, 1)  # trivially: empty edge set, one (vacuous) coloring

    # If small enough, enumerate directly
    if m <= 25:
        avoiding = 0
        for bits in range(2 ** m):
            coloring = {e: (bits >> i) & 1 for i, e in enumerate(edges)}
            if not _has_mono_clique(n, k, coloring):
                avoiding += 1
        return (avoiding, 2 ** m)

    # Incremental extension from a base
    # Find largest base_n whose edge count <= 25
    base_n = None
    base_avoiding: List[Dict] = []
    for bn in range(k, n + 1):
        bedges = coprime_graph_edges(bn)
        if len(bedges) <= 25:
            avs = []
            for bits in range(2 ** len(bedges)):
                col = {e: (bits >> i) & 1 for i, e in enumerate(bedges)}
                if not _has_mono_clique(bn, k, col):
                    avs.append(col)
            base_n = bn
            base_avoiding = avs
        else:
            break

    if base_n is None or not base_avoiding:
        return (0, 2 ** m)

    # Extend from base_n+1 to n
    avoiding_set = base_avoiding
    for nn in range(base_n + 1, n + 1):
        new_edges = [
            (min(i, nn), max(i, nn))
            for i in range(1, nn) if math.gcd(i, nn) == 1
        ]
        if not new_edges:
            continue
        next_avoiding = []
        for col in avoiding_set:
            for bits in range(2 ** len(new_edges)):
                new_col = dict(col)
                for idx, e in enumerate(new_edges):
                    new_col[e] = (bits >> idx) & 1
                if not _has_mono_clique(nn, k, new_col):
                    next_avoiding.append(new_col)
        avoiding_set = next_avoiding
        if not avoiding_set:
            break

    return (len(avoiding_set), 2 ** m)


def ramsey_channel_capacity(
    k: int = 3,
    ns: Optional[List[int]] = None,
) -> List[Dict]:
    """
    Channel capacity of the coprime Ramsey "channel" for clique size k.

    Model:
      Input:  edge 2-coloring (2^m possibilities, m = |E(G([n]))|)
      Channel: coprime structure filters out colorings with mono K_k
      Output:  valid avoiding coloring

    Capacity = log2(#avoiding) / m   (bits per edge)

    As n -> R_cop(k), capacity -> 0 (no valid output).
    """
    if ns is None:
        ns = list(range(3, 12))
    results = []
    for n in ns:
        edges = coprime_graph_edges(n)
        m = len(edges)
        if m == 0:
            results.append({
                "n": n,
                "edges": 0,
                "avoiding": 1,
                "total": 1,
                "capacity": 1.0,
                "log2_avoiding": 0.0,
            })
            continue
        av, total = count_avoiding_colorings(n, k)
        log2_av = math.log2(av) if av > 0 else 0.0
        cap = log2_av / m if m > 0 else 0.0
        results.append({
            "n": n,
            "edges": m,
            "avoiding": av,
            "total": total,
            "capacity": round(cap, 6),
            "log2_avoiding": round(log2_av, 4),
        })
    return results


# =========================================================================
# 5. Minimum description length for Ramsey witnesses
# =========================================================================

def _coloring_to_bitstring(coloring: Dict[Tuple[int, int], int],
                           edges: List[Tuple[int, int]]) -> str:
    """Encode coloring as a bit string in canonical edge order."""
    return "".join(str(coloring.get(e, 0)) for e in edges)


def witness_mdl(n: int = 10, k: int = 3) -> Dict[str, Any]:
    """
    Minimum description length analysis for Ramsey witnesses at n, k.

    At n = R_cop(k) - 1, there are some avoiding colorings.  We ask:
      - How compressible are they individually?
      - How much structure do they share (joint compression)?
      - What is the "backbone" -- bits that are the same across all witnesses?

    This connects to the backbone concept in SAT theory: fixed variables
    across all satisfying assignments.
    """
    edges = coprime_graph_edges(n)
    m = len(edges)

    if m == 0:
        return {
            "n": n, "k": k, "edges": 0, "avoiding": 0,
            "individual_mdl": 0.0, "joint_mdl": 0.0,
            "backbone_fraction": 1.0, "backbone_bits": [],
        }

    # Collect all avoiding colorings via incremental extension
    av_count, _ = count_avoiding_colorings(n, k)

    # We need the actual colorings, not just the count.
    # Rebuild them (for moderate n this is feasible).
    base_n = None
    base_avoiding: List[Dict] = []
    for bn in range(k, n + 1):
        bedges = coprime_graph_edges(bn)
        if len(bedges) <= 25:
            avs = []
            for bits in range(2 ** len(bedges)):
                col = {e: (bits >> i) & 1 for i, e in enumerate(bedges)}
                if not _has_mono_clique(bn, k, col):
                    avs.append(col)
            base_n = bn
            base_avoiding = avs
        else:
            break

    if base_n is None or not base_avoiding:
        return {
            "n": n, "k": k, "edges": m, "avoiding": 0,
            "individual_mdl": 0.0, "joint_mdl": 0.0,
            "backbone_fraction": 0.0, "backbone_bits": [],
        }

    avoiding_set = base_avoiding
    for nn in range(base_n + 1, n + 1):
        new_edges = [
            (min(i, nn), max(i, nn))
            for i in range(1, nn) if math.gcd(i, nn) == 1
        ]
        if not new_edges:
            continue
        next_avoiding = []
        for col in avoiding_set:
            for bits in range(2 ** len(new_edges)):
                new_col = dict(col)
                for idx, e in enumerate(new_edges):
                    new_col[e] = (bits >> idx) & 1
                if not _has_mono_clique(nn, k, new_col):
                    next_avoiding.append(new_col)
        avoiding_set = next_avoiding
        if not avoiding_set:
            break

    num_avoiding = len(avoiding_set)
    if num_avoiding == 0:
        return {
            "n": n, "k": k, "edges": m, "avoiding": 0,
            "individual_mdl": 0.0, "joint_mdl": 0.0,
            "backbone_fraction": 0.0, "backbone_bits": [],
        }

    # Encode each coloring as a bit string
    bitstrings = [
        _coloring_to_bitstring(col, edges) for col in avoiding_set
    ]

    # Individual compressed sizes
    individual_sizes = [compressed_size(bs) for bs in bitstrings]
    mean_individual = float(np.mean(individual_sizes))

    # Joint compression: concatenate all bitstrings and compress
    joint_blob = "\n".join(bitstrings)
    joint_compressed = compressed_size(joint_blob)
    per_witness_joint = joint_compressed / num_avoiding if num_avoiding > 0 else 0.0

    # Backbone: for each edge position, check if all witnesses agree
    backbone_bits: List[Dict] = []
    if num_avoiding > 0:
        for idx, e in enumerate(edges):
            vals = {bs[idx] for bs in bitstrings}
            if len(vals) == 1:
                backbone_bits.append({
                    "edge": e,
                    "fixed_color": int(vals.pop()),
                })

    backbone_fraction = len(backbone_bits) / m if m > 0 else 0.0

    # Entropy of each edge position across witnesses
    edge_entropies = []
    for idx, e in enumerate(edges):
        vals = [int(bs[idx]) for bs in bitstrings]
        h = entropy_from_labels(vals)
        edge_entropies.append({
            "edge": e,
            "entropy": round(h, 4),
            "fraction_color_0": round(vals.count(0) / len(vals), 4),
        })

    # Sort by entropy (most constrained first)
    edge_entropies.sort(key=lambda x: x["entropy"])

    return {
        "n": n,
        "k": k,
        "edges": m,
        "avoiding": num_avoiding,
        "raw_bits_per_witness": m,
        "mean_individual_compressed": round(mean_individual, 2),
        "joint_compressed_total": joint_compressed,
        "per_witness_joint": round(per_witness_joint, 2),
        "compression_ratio": round(mean_individual / m, 4) if m > 0 else 0.0,
        "backbone_bits": backbone_bits,
        "backbone_fraction": round(backbone_fraction, 4),
        "edge_entropies": edge_entropies,
        "naively_encoded_bits": m * num_avoiding,
        "joint_compression_savings": round(
            1 - joint_compressed / (m * num_avoiding), 4
        ) if m * num_avoiding > 0 else 0.0,
    }


# =========================================================================
# Main -- run all analyses and print summary
# =========================================================================

def main():
    print("=" * 70)
    print("DEEP INFORMATION-THEORETIC ANALYSIS")
    print("=" * 70)

    # -- 1. Coprime graph entropy --
    print("\n--- 1. Coprime Graph Entropy ---")
    ns = [5, 10, 20, 50, 100]
    entropy_results = coprime_vs_random_entropy(ns)
    for r in entropy_results:
        print(
            f"  n={r['n']:3d}  H(coprime)={r['coprime_entropy']:.4f}  "
            f"H(ER)={r['er_entropy']:.4f}  "
            f"ratio={r['entropy_ratio']:.4f}  "
            f"density={r['density']:.4f}  "
            f"edges={r['num_edges']}"
        )

    # -- 2. Feature importance --
    print("\n--- 2. Feature Mutual Information ---")
    problems = load_problems()
    fi = feature_importance(problems)
    print(f"  Base entropy H(solved): {fi['base_entropy']:.4f} bits")
    print(f"  Most informative feature: {fi['most_informative']}")
    print("  Top 10 features:")
    for r in fi["features"][:10]:
        print(f"    {r['feature']:30s}  I={r['mutual_information']:.6f}  NMI={r['nmi']:.4f}")

    # -- 3. Kolmogorov proxy --
    print("\n--- 3. Kolmogorov Complexity Proxy ---")
    kp = kolmogorov_proxy(problems)
    print(f"  Correlation(compressed_size, solved): {kp['correlation']:.4f}")
    print(f"  Mean compressed (solved):  {kp['mean_compressed_solved']:.1f} bytes")
    print(f"  Mean compressed (open):    {kp['mean_compressed_open']:.1f} bytes")
    print(f"  Interpretation: {kp['interpretation']}")

    # -- 4. Channel capacity --
    print("\n--- 4. Coprime Ramsey Channel Capacity (k=3) ---")
    cap = ramsey_channel_capacity(k=3, ns=list(range(3, 12)))
    for r in cap:
        print(
            f"  n={r['n']:2d}  edges={r['edges']:3d}  "
            f"avoiding={r['avoiding']:6d}  "
            f"cap={r['capacity']:.6f} bits/edge"
        )

    # -- 5. MDL for witnesses --
    print("\n--- 5. Minimum Description Length for Witnesses ---")
    mdl = witness_mdl(n=10, k=3)
    print(f"  n={mdl['n']}, k={mdl['k']}")
    print(f"  Edges: {mdl['edges']}")
    print(f"  Avoiding colorings: {mdl['avoiding']}")
    print(f"  Raw bits/witness: {mdl['raw_bits_per_witness']}")
    print(f"  Mean compressed/witness: {mdl['mean_individual_compressed']:.1f} bytes")
    print(f"  Joint per-witness: {mdl['per_witness_joint']:.1f} bytes")
    print(f"  Backbone fraction: {mdl['backbone_fraction']:.2%}")
    print(f"  Joint savings: {mdl['joint_compression_savings']:.2%}")
    if mdl["backbone_bits"]:
        print(f"  Backbone edges ({len(mdl['backbone_bits'])} fixed):")
        for bb in mdl["backbone_bits"][:10]:
            print(f"    {bb['edge']}  ->  color {bb['fixed_color']}")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
