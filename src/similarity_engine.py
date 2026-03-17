#!/usr/bin/env python3
"""
similarity_engine.py — Problem similarity and clustering analysis.

Computes multi-dimensional similarity between Erdős problems to discover:
  1. Hidden Twins: problem pairs that look different but share deep structure
  2. Problem Families: natural clusters beyond tag-based grouping
  3. Isomorphism Classes: problems that are structurally identical under renaming
  4. Isolation Index: problems that are uniquely unlike anything else
  5. Transfer Candidates: solved-open pairs with highest similarity

Output: docs/similarity_report.md
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
REPORT_PATH = ROOT / "docs" / "similarity_report.md"


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
# Feature Extraction — Problem DNA Vectors
# ═══════════════════════════════════════════════════════════════════

def compute_feature_vectors(problems: List[Dict]) -> Tuple[np.ndarray, List[int], List[str]]:
    """
    Encode each problem as a feature vector for similarity computation.

    Features:
    - Tag one-hot encoding (40 features)
    - OEIS count (1 feature)
    - Prize bucket (4 features: none, low, medium, high)
    - Formalized flag (1 feature)
    - Status category (5 features: open, proved, disproved, other solved, other)
    - Tag count (1 feature, normalized)
    - OEIS overlap signature (shared OEIS sequences → 1 feature per top-20 sequence)

    Returns: (feature_matrix, problem_numbers, feature_names)
    """
    # Collect all tags
    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    tag_idx = {t: i for i, t in enumerate(all_tags)}

    # Collect top OEIS sequences (most shared)
    oeis_count = Counter()
    for p in problems:
        for seq in _oeis(p):
            if seq and seq != "A000000" and not seq.startswith("A00000"):
                oeis_count[seq] += 1
    top_oeis = [seq for seq, cnt in oeis_count.most_common(20) if cnt > 1]
    oeis_idx = {s: i for i, s in enumerate(top_oeis)}

    n_tags = len(all_tags)
    n_oeis_feat = len(top_oeis)
    n_features = n_tags + 1 + 4 + 1 + 5 + 1 + n_oeis_feat

    feature_names = (
        [f"tag_{t}" for t in all_tags] +
        ["oeis_count"] +
        ["prize_none", "prize_low", "prize_medium", "prize_high"] +
        ["formalized"] +
        ["status_open", "status_proved", "status_disproved", "status_other_solved", "status_other"] +
        ["tag_count_norm"] +
        [f"oeis_{s}" for s in top_oeis]
    )

    X = np.zeros((len(problems), n_features), dtype=float)
    numbers = []

    for i, p in enumerate(problems):
        num = _number(p)
        numbers.append(num)

        # Tag features
        for t in _tags(p):
            if t in tag_idx:
                X[i, tag_idx[t]] = 1.0

        # OEIS count
        oeis_list = _oeis(p)
        real_oeis = [s for s in oeis_list if s and s != "A000000" and not s.startswith("A00000")]
        X[i, n_tags] = len(real_oeis) / 9.0  # normalize by max

        # Prize bucket
        prize = _prize(p)
        offset = n_tags + 1
        if prize == 0:
            X[i, offset] = 1
        elif prize <= 100:
            X[i, offset + 1] = 1
        elif prize <= 1000:
            X[i, offset + 2] = 1
        else:
            X[i, offset + 3] = 1

        # Formalized
        offset += 4
        X[i, offset] = 1.0 if _is_formalized(p) else 0.0

        # Status
        offset += 1
        s = _status(p)
        if s == "open":
            X[i, offset] = 1
        elif s in ("proved", "proved (Lean)"):
            X[i, offset + 1] = 1
        elif s in ("disproved", "disproved (Lean)"):
            X[i, offset + 2] = 1
        elif s in ("solved", "solved (Lean)"):
            X[i, offset + 3] = 1
        else:
            X[i, offset + 4] = 1

        # Tag count normalized
        offset += 5
        X[i, offset] = len(_tags(p)) / 5.0

        # OEIS sequence features
        offset += 1
        for seq in real_oeis:
            if seq in oeis_idx:
                X[i, offset + oeis_idx[seq]] = 1.0

    return X, numbers, feature_names


# ═══════════════════════════════════════════════════════════════════
# Similarity Computation
# ═══════════════════════════════════════════════════════════════════

def compute_similarity_matrix(X: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity matrix between all problem pairs.

    Uses efficient vectorized computation.
    """
    # Normalize rows
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    X_norm = X / norms

    # Cosine similarity
    sim = X_norm @ X_norm.T

    # Zero out diagonal
    np.fill_diagonal(sim, 0.0)

    return sim


def compute_tag_jaccard(problems: List[Dict]) -> Dict[Tuple[int, int], float]:
    """
    Compute Jaccard similarity between all problem pairs based on tags.

    Jaccard = |A ∩ B| / |A ∪ B|
    """
    jaccard = {}
    for i in range(len(problems)):
        tags_i = _tags(problems[i])
        if not tags_i:
            continue
        for j in range(i + 1, len(problems)):
            tags_j = _tags(problems[j])
            if not tags_j:
                continue
            intersection = len(tags_i & tags_j)
            union = len(tags_i | tags_j)
            if union > 0 and intersection > 0:
                ni, nj = _number(problems[i]), _number(problems[j])
                jaccard[(ni, nj)] = intersection / union
    return jaccard


# ═══════════════════════════════════════════════════════════════════
# 1. Hidden Twins — problems with high cosine but different tags
# ═══════════════════════════════════════════════════════════════════

def hidden_twins(problems: List[Dict], X: np.ndarray, numbers: List[int],
                 top_k: int = 30) -> List[Dict]:
    """
    Find problem pairs with high overall similarity but low tag overlap.

    These are "hidden twins" — structurally similar problems that appear
    to be in different areas of mathematics but share deep features.
    """
    sim = compute_similarity_matrix(X)

    # Get top-k most similar pairs
    n = sim.shape[0]
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            if sim[i, j] > 0.5:  # only consider moderately similar
                tags_i = _tags(problems[i])
                tags_j = _tags(problems[j])
                tag_overlap = len(tags_i & tags_j) / len(tags_i | tags_j) if (tags_i | tags_j) else 0

                # Hidden twin = high cosine similarity but low tag overlap
                if tag_overlap < 0.5:
                    surprise = sim[i, j] * (1 - tag_overlap)
                    pairs.append({
                        "problem_a": numbers[i],
                        "problem_b": numbers[j],
                        "cosine_similarity": round(float(sim[i, j]), 3),
                        "tag_overlap": round(tag_overlap, 3),
                        "surprise_score": round(float(surprise), 3),
                        "tags_a": sorted(tags_i),
                        "tags_b": sorted(tags_j),
                        "status_a": _status(problems[i]),
                        "status_b": _status(problems[j]),
                    })

    pairs.sort(key=lambda x: -x["surprise_score"])
    return pairs[:top_k]


# ═══════════════════════════════════════════════════════════════════
# 2. Problem Families — natural clustering beyond tags
# ═══════════════════════════════════════════════════════════════════

def problem_families(problems: List[Dict], X: np.ndarray, numbers: List[int],
                     n_families: int = 8) -> List[Dict]:
    """
    Cluster problems into natural families using k-means on feature vectors.

    Pure numpy implementation (no sklearn dependency).
    """
    n, d = X.shape
    if n < n_families:
        return []

    # Normalize features
    means = X.mean(axis=0)
    stds = X.std(axis=0)
    stds[stds == 0] = 1.0
    X_norm = (X - means) / stds

    # K-means clustering
    rng = np.random.RandomState(42)
    centroids = X_norm[rng.choice(n, n_families, replace=False)]

    for _ in range(50):  # max iterations
        # Assign
        dists = np.linalg.norm(X_norm[:, None, :] - centroids[None, :, :], axis=2)
        labels = np.argmin(dists, axis=1)

        # Update
        new_centroids = np.zeros_like(centroids)
        for k in range(n_families):
            mask = labels == k
            if mask.sum() > 0:
                new_centroids[k] = X_norm[mask].mean(axis=0)
            else:
                new_centroids[k] = X_norm[rng.randint(n)]

        if np.allclose(centroids, new_centroids, atol=1e-6):
            break
        centroids = new_centroids

    # Analyze each family
    families = []
    for k in range(n_families):
        mask = labels == k
        family_indices = np.where(mask)[0]
        if len(family_indices) == 0:
            continue

        family_problems = [problems[i] for i in family_indices]
        family_numbers = [numbers[i] for i in family_indices]

        # Tag profile
        tag_counts = Counter(t for p in family_problems for t in _tags(p))
        total_tags = sum(tag_counts.values())

        # Solve rate
        n_solved = sum(1 for p in family_problems if _is_solved(p))
        n_open = sum(1 for p in family_problems if _is_open(p))

        # Prize info
        prizes = [_prize(p) for p in family_problems if _prize(p) > 0]

        families.append({
            "family_id": k,
            "size": len(family_indices),
            "solve_rate": round(n_solved / len(family_indices), 3),
            "open_count": n_open,
            "top_tags": [(t, round(c / total_tags, 2))
                         for t, c in tag_counts.most_common(5)] if total_tags > 0 else [],
            "prize_total": sum(prizes),
            "example_problems": sorted(family_numbers)[:8],
        })

    families.sort(key=lambda x: -x["size"])
    return families


# ═══════════════════════════════════════════════════════════════════
# 3. Isolation Index — uniquely unlike everything
# ═══════════════════════════════════════════════════════════════════

def isolation_index(problems: List[Dict], X: np.ndarray,
                    numbers: List[int]) -> List[Dict]:
    """
    Compute how "isolated" each problem is from all others.

    The most isolated problems are the most unique — they don't fit
    neatly into any cluster and may represent genuinely novel directions.
    """
    sim = compute_similarity_matrix(X)

    isolation = []
    for i in range(len(problems)):
        # Average similarity to all other problems
        avg_sim = sim[i].mean()
        max_sim = sim[i].max()
        # Isolation = 1 - max similarity to any other problem
        iso_score = 1.0 - max_sim

        isolation.append({
            "number": numbers[i],
            "isolation": round(float(iso_score), 3),
            "avg_similarity": round(float(avg_sim), 3),
            "max_similarity": round(float(max_sim), 3),
            "tags": sorted(_tags(problems[i])),
            "status": _status(problems[i]),
        })

    isolation.sort(key=lambda x: -x["isolation"])
    return isolation


# ═══════════════════════════════════════════════════════════════════
# 4. Transfer Candidates — best solved→open matches
# ═══════════════════════════════════════════════════════════════════

def transfer_candidates(problems: List[Dict], X: np.ndarray,
                        numbers: List[int], top_k: int = 30) -> List[Dict]:
    """
    Find the most similar solved-open problem pairs.

    These are the strongest candidates for technique transfer:
    if problem A was solved, and problem B looks just like A but is open,
    the techniques that solved A might work for B.
    """
    sim = compute_similarity_matrix(X)

    solved_indices = [i for i, p in enumerate(problems) if _is_solved(p)]
    open_indices = [i for i, p in enumerate(problems) if _is_open(p)]

    transfers = []
    for si in solved_indices:
        for oi in open_indices:
            s = sim[si, oi]
            if s > 0.4:  # minimum threshold
                transfers.append({
                    "solved_problem": numbers[si],
                    "open_problem": numbers[oi],
                    "similarity": round(float(s), 3),
                    "solved_tags": sorted(_tags(problems[si])),
                    "open_tags": sorted(_tags(problems[oi])),
                    "solved_status": _status(problems[si]),
                    "open_prize": _prize(problems[oi]),
                })

    transfers.sort(key=lambda x: -x["similarity"])
    return transfers[:top_k]


# ═══════════════════════════════════════════════════════════════════
# 5. Structural Isomorphism
# ═══════════════════════════════════════════════════════════════════

def structural_isomorphism(problems: List[Dict], X: np.ndarray,
                           numbers: List[int], threshold: float = 0.95) -> List[Dict]:
    """
    Find groups of problems that are structurally identical (or nearly so).

    These are problems that have the same tag set, same OEIS profile,
    same prize status, etc. — they differ only in their specific statement.
    """
    sim = compute_similarity_matrix(X)
    n = len(problems)

    # Union-Find for grouping
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(n):
        for j in range(i + 1, n):
            if sim[i, j] >= threshold:
                union(i, j)

    # Group by component
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    iso_classes = []
    for root, members in groups.items():
        if len(members) < 2:
            continue

        member_problems = [problems[m] for m in members]
        member_numbers = [numbers[m] for m in members]

        # Characterize the class
        tag_counts = Counter(t for p in member_problems for t in _tags(p))
        n_solved = sum(1 for p in member_problems if _is_solved(p))
        n_open = sum(1 for p in member_problems if _is_open(p))

        iso_classes.append({
            "size": len(members),
            "problems": sorted(member_numbers),
            "tags": [t for t, _ in tag_counts.most_common(4)],
            "solve_rate": round(n_solved / len(members), 3),
            "n_open": n_open,
            "n_solved": n_solved,
        })

    iso_classes.sort(key=lambda x: -x["size"])
    return iso_classes


# ═══════════════════════════════════════════════════════════════════
# 6. Tag Embedding — Low-Dimensional Tag Space
# ═══════════════════════════════════════════════════════════════════

def tag_embedding(problems: List[Dict]) -> Dict[str, Any]:
    """
    Build a co-occurrence matrix for tags and compute a low-dimensional
    embedding via SVD.

    This reveals which tags are "close" in mathematical space even if
    they don't directly co-occur on the same problems.
    """
    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    tag_idx = {t: i for i, t in enumerate(all_tags)}
    n_tags = len(all_tags)

    # Co-occurrence matrix
    cooccur = np.zeros((n_tags, n_tags), dtype=float)
    for p in problems:
        tags = sorted(_tags(p))
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                ti, tj = tag_idx[tags[i]], tag_idx[tags[j]]
                cooccur[ti, tj] += 1
                cooccur[tj, ti] += 1

    # Add self-counts (total occurrences)
    for p in problems:
        for t in _tags(p):
            cooccur[tag_idx[t], tag_idx[t]] += 1

    # SVD for embedding
    k = min(10, n_tags - 1)
    if k < 2:
        return {"embedding": {}, "closest_pairs": [], "dim": 0}

    U, S, Vt = np.linalg.svd(cooccur, full_matrices=False)
    embedding = U[:, :k] * S[:k]  # weight by singular values

    # Find closest tag pairs in embedding space
    tag_dists = []
    for i in range(n_tags):
        for j in range(i + 1, n_tags):
            d = np.linalg.norm(embedding[i] - embedding[j])
            tag_dists.append((all_tags[i], all_tags[j], round(float(d), 3)))

    tag_dists.sort(key=lambda x: x[2])

    # Find most distant pairs
    distant = sorted(tag_dists, key=lambda x: -x[2])

    return {
        "embedding_dim": k,
        "closest_pairs": tag_dists[:15],
        "most_distant": distant[:10],
        "variance_explained": [round(float(s**2 / (S**2).sum()), 3) for s in S[:k]],
    }


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(twins, families, isolated, transfers,
                    iso_classes, embedding) -> str:
    lines = []
    lines.append("# Problem Similarity Analysis")
    lines.append("")
    lines.append("Multi-dimensional similarity computation revealing hidden")
    lines.append("relationships, natural clusters, and technique transfer candidates.")
    lines.append("")

    # 1. Hidden Twins
    lines.append("## 1. Hidden Twins (high structural similarity, different tags)")
    lines.append("")
    lines.append("| Problem A | Problem B | Cosine | Tag Overlap | Surprise | Tags A | Tags B |")
    lines.append("|-----------|-----------|--------|-------------|----------|--------|--------|")
    for t in twins[:15]:
        tags_a = ", ".join(t["tags_a"][:2])
        tags_b = ", ".join(t["tags_b"][:2])
        lines.append(
            f"| #{t['problem_a']} | #{t['problem_b']} | {t['cosine_similarity']:.3f} | "
            f"{t['tag_overlap']:.3f} | {t['surprise_score']:.3f} | {tags_a} | {tags_b} |"
        )
    lines.append("")

    # 2. Problem Families
    lines.append("## 2. Natural Problem Families (k-means clustering)")
    lines.append("")
    for f in families:
        top_tag_str = ", ".join(f"{t} ({frac:.0%})" for t, frac in f["top_tags"][:3])
        lines.append(f"### Family {f['family_id']} ({f['size']} problems)")
        lines.append(f"- Solve rate: {f['solve_rate']:.1%}")
        lines.append(f"- Tags: {top_tag_str}")
        lines.append(f"- Examples: {', '.join(f'#{n}' for n in f['example_problems'][:6])}")
        if f["prize_total"] > 0:
            lines.append(f"- Total prizes: ${f['prize_total']:.0f}")
        lines.append("")

    # 3. Most Isolated
    lines.append("## 3. Most Isolated Problems (unique structure)")
    lines.append("")
    lines.append("| Problem | Isolation | Max Sim | Tags | Status |")
    lines.append("|---------|-----------|---------|------|--------|")
    for iso in isolated[:15]:
        tags = ", ".join(iso["tags"][:2])
        lines.append(
            f"| #{iso['number']} | {iso['isolation']:.3f} | "
            f"{iso['max_similarity']:.3f} | {tags} | {iso['status']} |"
        )
    lines.append("")

    # 4. Transfer Candidates
    lines.append("## 4. Best Transfer Candidates (solved → open)")
    lines.append("")
    lines.append("| Solved | Open | Similarity | Open Prize | Solved Tags | Open Tags |")
    lines.append("|--------|------|-----------|-----------|-------------|-----------|")
    for t in transfers[:15]:
        prize = f"${t['open_prize']:.0f}" if t["open_prize"] > 0 else "-"
        st = ", ".join(t["solved_tags"][:2])
        ot = ", ".join(t["open_tags"][:2])
        lines.append(
            f"| #{t['solved_problem']} | #{t['open_problem']} | "
            f"{t['similarity']:.3f} | {prize} | {st} | {ot} |"
        )
    lines.append("")

    # 5. Isomorphism Classes
    lines.append("## 5. Structural Isomorphism Classes")
    lines.append("")
    for ic in iso_classes[:10]:
        probs = ", ".join(f"#{n}" for n in ic["problems"][:10])
        more = f" +{ic['size'] - 10} more" if ic["size"] > 10 else ""
        lines.append(f"- **{ic['size']} problems** ({', '.join(ic['tags'][:3])}): {probs}{more}")
        lines.append(f"  Solve rate: {ic['solve_rate']:.1%} ({ic['n_solved']} solved, {ic['n_open']} open)")
    lines.append("")

    # 6. Tag Embedding
    lines.append("## 6. Tag Embedding (SVD on co-occurrence)")
    lines.append("")
    lines.append("### Closest Tag Pairs (mathematical neighbors)")
    for t1, t2, d in embedding["closest_pairs"][:10]:
        lines.append(f"- {t1} ↔ {t2}: distance {d}")
    lines.append("")
    lines.append("### Most Distant Tag Pairs")
    for t1, t2, d in embedding["most_distant"][:5]:
        lines.append(f"- {t1} ↔ {t2}: distance {d}")
    lines.append("")

    if embedding["variance_explained"]:
        top3 = sum(embedding["variance_explained"][:3])
        lines.append(f"First 3 components explain {top3:.1%} of variance.")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("PROBLEM SIMILARITY ENGINE")
    print("=" * 70)

    problems = load_problems()
    print(f"Loaded {len(problems)} problems")

    print("\nComputing feature vectors...")
    X, numbers, feature_names = compute_feature_vectors(problems)
    print(f"   {X.shape[0]} problems × {X.shape[1]} features")

    print("\n1. Finding hidden twins...")
    twins = hidden_twins(problems, X, numbers)
    print(f"   {len(twins)} hidden twin pairs found")

    print("\n2. Clustering into families...")
    families = problem_families(problems, X, numbers)
    print(f"   {len(families)} families identified")

    print("\n3. Computing isolation index...")
    isolated = isolation_index(problems, X, numbers)
    print(f"   Most isolated: #{isolated[0]['number']} (isolation={isolated[0]['isolation']:.3f})")

    print("\n4. Finding transfer candidates...")
    transfers = transfer_candidates(problems, X, numbers)
    print(f"   {len(transfers)} solved→open transfer candidates")

    print("\n5. Detecting structural isomorphism...")
    iso_classes = structural_isomorphism(problems, X, numbers)
    print(f"   {len(iso_classes)} isomorphism classes (≥2 members)")

    print("\n6. Computing tag embedding...")
    embedding = tag_embedding(problems)
    print(f"   {embedding['embedding_dim']}-dimensional embedding")

    print("\nGenerating report...")
    report = generate_report(twins, families, isolated, transfers,
                             iso_classes, embedding)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"Saved to {REPORT_PATH}")

    print("\n" + "=" * 70)
    print("SIMILARITY ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
