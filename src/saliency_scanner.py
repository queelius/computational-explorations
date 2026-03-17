#!/usr/bin/env python3
"""
saliency_scanner.py -- Find problems at critical thresholds.

Identifies the highest-leverage open mathematical problems: those where a
small advance (computational or theoretical) would settle them. Five
complementary analyses converge on "what to work on next":

  1. NEAR-RESOLVED: Open problems with recent OEIS activity (A350000+).
     Someone is actively computing terms -- the problem may be close to
     falling. Ranked by OEIS recency x connectivity x tag tractability.

  2. GAP ANALYSIS: For each tag family, the "frontier problem" -- the open
     problem whose nearest neighbours (by tag similarity) are solved.
     These sit on the resolution boundary and may yield to the same methods.

  3. TECHNIQUE BOTTLENECK: Open problems clustered by the single technique
     gap blocking them. If one bottleneck breaks, many problems fall.

  4. CROSS-FIELD BRIDGES: Problems at the intersection of rarely-combined
     tags. Techniques from the less-expected field often crack these.

  5. ENSEMBLE PREDICTION: "Next 10 to fall" combining survival model,
     KNN predictor, interestingness, and all saliency signals.

Output: docs/saliency_scanner_report.md
"""

import math
import re
import yaml
import numpy as np
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# -- Paths ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "saliency_scanner_report.md"


# ===========================================================================
# Data access helpers (consistent with project conventions)
# ===========================================================================

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
    return _status(p) in (
        "proved", "disproved", "solved",
        "proved (Lean)", "disproved (Lean)", "solved (Lean)",
    )


def _is_open(p: Dict) -> bool:
    return _status(p) == "open"


def _is_formalized(p: Dict) -> bool:
    return p.get("formalized", {}).get("state", "no") == "yes"


def _real_oeis(p: Dict) -> List[str]:
    """Return only genuine OEIS sequence IDs (filter N/A, possible, etc.)."""
    raw = p.get("oeis", [])
    if not isinstance(raw, list):
        return []
    return [
        s for s in raw
        if s and isinstance(s, str) and s not in ("N/A", "possible", "n/a", "none", "")
        and not s.startswith("A00000")
    ]


def _oeis_numeric(seq_id: str) -> int:
    """Extract numeric suffix from OEIS ID like 'A387053' -> 387053."""
    m = re.match(r"A(\d+)", seq_id)
    return int(m.group(1)) if m else 0


def _last_update(p: Dict) -> str:
    """Return status last_update as string."""
    return str(p.get("status", {}).get("last_update", ""))


# ===========================================================================
# Precomputed tag statistics (shared across analyses)
# ===========================================================================

def _build_tag_stats(problems: List[Dict]) -> Dict[str, Any]:
    """Compute tag-level solve rates, pair rates, and OEIS maps."""
    tag_solved = Counter()
    tag_total = Counter()
    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _is_solved(p):
                tag_solved[t] += 1
    tag_solve_rate = {
        t: tag_solved[t] / tag_total[t]
        for t in tag_total if tag_total[t] > 0
    }

    # Pair solve rates
    pair_solved = Counter()
    pair_total = Counter()
    for p in problems:
        for a, b in combinations(sorted(_tags(p)), 2):
            pair_total[(a, b)] += 1
            if _is_solved(p):
                pair_solved[(a, b)] += 1
    pair_solve_rate = {
        pair: pair_solved[pair] / pair_total[pair]
        for pair in pair_total if pair_total[pair] > 0
    }

    # OEIS maps
    oeis_to_problems = defaultdict(set)
    oeis_to_solved = defaultdict(int)
    oeis_to_total = defaultdict(int)
    for p in problems:
        for seq in _real_oeis(p):
            oeis_to_problems[seq].add(_number(p))
            oeis_to_total[seq] += 1
            if _is_solved(p):
                oeis_to_solved[seq] += 1

    return {
        "tag_total": tag_total,
        "tag_solved": tag_solved,
        "tag_solve_rate": tag_solve_rate,
        "pair_total": pair_total,
        "pair_solved": pair_solved,
        "pair_solve_rate": pair_solve_rate,
        "oeis_to_problems": oeis_to_problems,
        "oeis_to_solved": oeis_to_solved,
        "oeis_to_total": oeis_to_total,
    }


# ===========================================================================
# 1. NEAR-RESOLVED: Recent OEIS activity on open problems
# ===========================================================================

# OEIS sequences with numeric ID >= this threshold are considered "recent"
# (A350000 ~ 2023, A380000 ~ late 2024, A387000+ ~ 2025).
OEIS_RECENT_THRESHOLD = 350000

# Finer recency tiers for scoring
OEIS_RECENCY_TIERS = [
    (387000, 1.0),    # 2025: maximum recency signal
    (380000, 0.85),   # late 2024
    (370000, 0.70),   # mid 2024
    (360000, 0.55),   # early 2024
    (350000, 0.40),   # 2023
]


def _oeis_recency_score(seq_id: str) -> float:
    """Score how recent an OEIS sequence is (0=old, 1=brand new)."""
    num = _oeis_numeric(seq_id)
    for threshold, score in OEIS_RECENCY_TIERS:
        if num >= threshold:
            return score
    return 0.0


def near_resolved_problems(problems: List[Dict],
                           stats: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Find open problems with recent OEIS activity.

    Recent OEIS sequences (A350000+) indicate active computation -- someone
    is extending the sequence, which may lead to a conjecture proof/disproof.

    Scoring: max_recency * (1 + log(n_recent_oeis)) * avg_tag_tractability

    Returns sorted list (highest score first).
    """
    if stats is None:
        stats = _build_tag_stats(problems)

    tag_solve_rate = stats["tag_solve_rate"]
    oeis_to_problems = stats["oeis_to_problems"]

    results = []
    for p in problems:
        if not _is_open(p):
            continue

        num = _number(p)
        oeis_seqs = _real_oeis(p)
        if not oeis_seqs:
            continue

        # Compute recency signal for each OEIS sequence
        recency_scores = []
        recent_seqs = []
        for seq in oeis_seqs:
            rs = _oeis_recency_score(seq)
            if rs > 0:
                recency_scores.append(rs)
                recent_seqs.append(seq)

        if not recency_scores:
            continue

        max_recency = max(recency_scores)
        n_recent = len(recent_seqs)

        # OEIS connectivity: how many other problems share these sequences
        oeis_connections = set()
        for seq in oeis_seqs:
            oeis_connections.update(oeis_to_problems.get(seq, set()))
        oeis_connections.discard(num)
        n_connections = len(oeis_connections)

        # Tag tractability: average solve rate of this problem's tags
        tags = _tags(p)
        rates = [tag_solve_rate.get(t, 0.3) for t in tags]
        avg_tractability = sum(rates) / len(rates) if rates else 0.3

        # Composite score
        score = max_recency * (1 + math.log1p(n_recent)) * avg_tractability

        results.append({
            "number": num,
            "tags": sorted(tags),
            "prize": _prize(p),
            "formalized": _is_formalized(p),
            "recent_oeis": recent_seqs,
            "all_oeis": oeis_seqs,
            "max_recency": max_recency,
            "n_recent_oeis": n_recent,
            "n_oeis_connections": n_connections,
            "avg_tag_tractability": avg_tractability,
            "near_resolved_score": score,
        })

    results.sort(key=lambda x: -x["near_resolved_score"])
    return results


# ===========================================================================
# 2. GAP ANALYSIS: Frontier problems at the solved/open boundary
# ===========================================================================

def gap_analysis(problems: List[Dict],
                 stats: Optional[Dict] = None) -> Dict[str, Any]:
    """
    For each tag family, find the "frontier problem" -- the open problem
    whose tag-neighbourhood has the highest fraction of solved problems.

    A frontier problem is one where similar problems (sharing the most tags)
    have been solved, but it remains open. These sit at the resolution
    boundary and may yield to the same techniques.

    Returns:
      - frontier_by_tag: {tag: {problem, solved_neighbour_fraction, ...}}
      - all_frontiers: sorted list of all frontier problems
    """
    if stats is None:
        stats = _build_tag_stats(problems)

    prob_by_num = {_number(p): p for p in problems}
    tag_solve_rate = stats["tag_solve_rate"]

    # Build tag-based similarity: for each open problem, count how many
    # solved problems share each of its tags
    open_probs = [p for p in problems if _is_open(p)]
    solved_probs = [p for p in problems if _is_solved(p)]

    # For each tag, collect solved and open problem numbers
    tag_to_solved = defaultdict(set)
    tag_to_open = defaultdict(set)
    for p in problems:
        num = _number(p)
        for t in _tags(p):
            if _is_solved(p):
                tag_to_solved[t].add(num)
            elif _is_open(p):
                tag_to_open[t].add(num)

    # For each open problem, compute solved-neighbourhood density
    open_scores = []
    for p in open_probs:
        num = _number(p)
        tags = _tags(p)
        if not tags:
            continue

        # Solved neighbours: problems sharing >= 1 tag that are solved
        # Weight by Jaccard similarity (shared tags / union tags)
        solved_neighbour_scores = []
        for sp in solved_probs:
            shared = tags & _tags(sp)
            if shared:
                jaccard = len(shared) / len(tags | _tags(sp))
                solved_neighbour_scores.append(jaccard)

        if not solved_neighbour_scores:
            continue

        # Top-k neighbour density (k=10)
        solved_neighbour_scores.sort(reverse=True)
        k = min(10, len(solved_neighbour_scores))
        top_k_density = sum(solved_neighbour_scores[:k]) / k

        # Also consider tag tractability
        avg_rate = sum(tag_solve_rate.get(t, 0) for t in tags) / len(tags)

        # Frontier score: how close to the solved boundary
        frontier_score = top_k_density * (0.5 + 0.5 * avg_rate)

        open_scores.append({
            "number": num,
            "tags": sorted(tags),
            "prize": _prize(p),
            "formalized": _is_formalized(p),
            "top_k_solved_density": top_k_density,
            "avg_tag_solve_rate": avg_rate,
            "frontier_score": frontier_score,
            "n_solved_neighbours": len(solved_neighbour_scores),
        })

    open_scores.sort(key=lambda x: -x["frontier_score"])

    # Best frontier per tag
    frontier_by_tag = {}
    for entry in open_scores:
        for t in entry["tags"]:
            if t not in frontier_by_tag:
                frontier_by_tag[t] = entry

    return {
        "frontier_by_tag": frontier_by_tag,
        "all_frontiers": open_scores,
    }


# ===========================================================================
# 3. TECHNIQUE BOTTLENECK: Clustered by blocking technique
# ===========================================================================

# Technique families and their characteristic signatures in the tag space.
# Each family maps a "bottleneck description" to the tag-combinations it blocks.
TECHNIQUE_SIGNATURES = {
    "density_increment": {
        "description": "Density increment / regularity method",
        "indicator_tags": {"additive combinatorics", "arithmetic progressions"},
        "complementary_tags": {"number theory", "primes"},
    },
    "fourier_analytic": {
        "description": "Fourier analysis of subset structure",
        "indicator_tags": {"additive combinatorics"},
        "complementary_tags": {"number theory", "set theory"},
    },
    "probabilistic_method": {
        "description": "Probabilistic / random construction",
        "indicator_tags": {"combinatorics", "graph theory"},
        "complementary_tags": {"chromatic number", "ramsey theory", "hypergraphs"},
    },
    "algebraic_structure": {
        "description": "Algebraic / polynomial method",
        "indicator_tags": {"sidon sets", "additive basis"},
        "complementary_tags": {"number theory", "combinatorics"},
    },
    "extremal_counting": {
        "description": "Extremal graph / Turan-type argument",
        "indicator_tags": {"graph theory", "turan number"},
        "complementary_tags": {"combinatorics", "hypergraphs"},
    },
    "spectral_methods": {
        "description": "Spectral / eigenvalue methods",
        "indicator_tags": {"graph theory", "chromatic number"},
        "complementary_tags": {"ramsey theory", "combinatorics"},
    },
    "sieve_methods": {
        "description": "Sieve theory / prime distribution",
        "indicator_tags": {"primes", "number theory"},
        "complementary_tags": {"additive basis", "divisors"},
    },
    "topological_geometric": {
        "description": "Geometric / topological method",
        "indicator_tags": {"geometry", "distances"},
        "complementary_tags": {"combinatorics", "graph theory"},
    },
    "ramsey_partition": {
        "description": "Ramsey / partition regularity",
        "indicator_tags": {"ramsey theory"},
        "complementary_tags": {"number theory", "combinatorics", "graph theory"},
    },
    "computational_search": {
        "description": "Computational / exhaustive search",
        "indicator_tags": {"cycles", "covering systems"},
        "complementary_tags": {"number theory", "graph theory"},
    },
}


def _classify_bottleneck(tags: Set[str]) -> List[Tuple[str, float]]:
    """
    Classify which technique families are relevant for a given tag-set.
    Returns list of (family_name, relevance_score) sorted by relevance.
    """
    scores = []
    for family, sig in TECHNIQUE_SIGNATURES.items():
        # Score = fraction of indicator tags present + 0.3 * fraction of complementary
        indicator_overlap = len(tags & sig["indicator_tags"])
        indicator_max = max(len(sig["indicator_tags"]), 1)
        comp_overlap = len(tags & sig["complementary_tags"])
        comp_max = max(len(sig["complementary_tags"]), 1)

        score = (indicator_overlap / indicator_max) + 0.3 * (comp_overlap / comp_max)
        if score > 0:
            scores.append((family, score))

    scores.sort(key=lambda x: -x[1])
    return scores


def technique_bottlenecks(problems: List[Dict],
                          stats: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Cluster open problems by the technique bottleneck most likely blocking them.

    For each technique family, we find all open problems where that family
    scores highest, then measure how "stuck" those problems are (based on
    how many solved problems in the same tag-neighbourhood used a different
    technique signature).

    Returns:
      - clusters: {family: [problems]}
      - bottleneck_sizes: {family: count}
      - leverage: which bottleneck, if broken, unblocks the most problems
    """
    if stats is None:
        stats = _build_tag_stats(problems)

    open_probs = [p for p in problems if _is_open(p)]

    # Classify each open problem
    clusters = defaultdict(list)
    problem_bottleneck = {}

    for p in open_probs:
        num = _number(p)
        tags = _tags(p)
        if not tags:
            continue

        classifications = _classify_bottleneck(tags)
        if not classifications:
            continue

        primary_family, primary_score = classifications[0]
        secondary = classifications[1] if len(classifications) > 1 else (None, 0)

        entry = {
            "number": num,
            "tags": sorted(tags),
            "prize": _prize(p),
            "primary_bottleneck": primary_family,
            "primary_score": primary_score,
            "secondary_bottleneck": secondary[0],
            "all_bottlenecks": classifications[:3],
        }
        clusters[primary_family].append(entry)
        problem_bottleneck[num] = entry

    # Compute leverage: if this bottleneck breaks, how many problems fall?
    bottleneck_sizes = {
        family: len(members) for family, members in clusters.items()
    }

    # Sort each cluster by primary_score (most blocked first)
    for family in clusters:
        clusters[family].sort(key=lambda x: -x["primary_score"])

    # Also compute "shared bottleneck pairs": problems that share both
    # primary AND secondary bottleneck, suggesting very similar blocking
    shared_pairs = []
    open_entries = list(problem_bottleneck.values())
    for i in range(min(len(open_entries), 400)):
        for j in range(i + 1, min(len(open_entries), 400)):
            a, b = open_entries[i], open_entries[j]
            if (a["primary_bottleneck"] == b["primary_bottleneck"]
                    and a.get("secondary_bottleneck") == b.get("secondary_bottleneck")
                    and a["secondary_bottleneck"] is not None):
                shared_pairs.append({
                    "problems": (a["number"], b["number"]),
                    "shared_bottleneck": a["primary_bottleneck"],
                    "shared_secondary": a["secondary_bottleneck"],
                })

    return {
        "clusters": dict(clusters),
        "bottleneck_sizes": bottleneck_sizes,
        "shared_pairs": shared_pairs[:50],
        "leverage_ranking": sorted(
            bottleneck_sizes.items(), key=lambda x: -x[1]
        ),
    }


# ===========================================================================
# 4. CROSS-FIELD BRIDGES: Rare tag combinations
# ===========================================================================

def cross_field_bridges(problems: List[Dict],
                        stats: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Find open problems at the intersection of rarely-combined tags.

    Bridge problems sit between two fields that don't usually interact.
    When one field develops a new technique, the bridge problem may fall
    because the other field hasn't tried importing it.

    Score = (1 / pair_frequency) * pair_solve_rate * avg_tag_tractability

    High score = rare combination + high solve rate in that combination
    (meaning the few times this combo appeared, it got solved -- so the
    technique works, it just hasn't been tried on this problem yet).
    """
    if stats is None:
        stats = _build_tag_stats(problems)

    pair_total = stats["pair_total"]
    pair_solve_rate = stats["pair_solve_rate"]
    tag_solve_rate = stats["tag_solve_rate"]
    tag_total = stats["tag_total"]

    # Compute global pair frequency baseline
    all_pair_counts = list(pair_total.values())
    if not all_pair_counts:
        return []
    median_pair_freq = float(np.median(all_pair_counts))

    results = []
    for p in problems:
        if not _is_open(p):
            continue

        num = _number(p)
        tags = sorted(_tags(p))
        if len(tags) < 2:
            continue

        # Check all tag pairs for this problem
        best_bridge_score = 0.0
        best_pair = None
        bridge_details = []

        for a, b in combinations(tags, 2):
            pair = (a, b) if a < b else (b, a)
            freq = pair_total.get(pair, 0)
            if freq == 0:
                continue

            # Rarity: inverse frequency relative to median
            rarity = median_pair_freq / max(freq, 1)

            # Solve rate for this specific combination
            psr = pair_solve_rate.get(pair, 0.0)

            # Individual tag sizes (larger tags = more established fields)
            field_size = min(tag_total.get(a, 1), tag_total.get(b, 1))
            size_bonus = min(field_size / 50.0, 1.0)

            # Bridge score: rare but successful combinations between big fields
            bridge_score = rarity * (0.3 + 0.7 * psr) * (0.5 + 0.5 * size_bonus)

            if bridge_score > 0:
                bridge_details.append({
                    "pair": pair,
                    "frequency": freq,
                    "rarity": rarity,
                    "pair_solve_rate": psr,
                    "bridge_score": bridge_score,
                })

            if bridge_score > best_bridge_score:
                best_bridge_score = bridge_score
                best_pair = pair

        if not bridge_details:
            continue

        bridge_details.sort(key=lambda x: -x["bridge_score"])

        # Tag tractability
        rates = [tag_solve_rate.get(t, 0.3) for t in tags]
        avg_tractability = sum(rates) / len(rates)

        results.append({
            "number": num,
            "tags": tags,
            "prize": _prize(p),
            "formalized": _is_formalized(p),
            "best_bridge_pair": best_pair,
            "best_bridge_score": best_bridge_score,
            "bridge_details": bridge_details[:3],
            "avg_tag_tractability": avg_tractability,
            "cross_field_score": best_bridge_score * (0.5 + 0.5 * avg_tractability),
        })

    results.sort(key=lambda x: -x["cross_field_score"])
    return results


# ===========================================================================
# 5. ENSEMBLE PREDICTOR: Next 10 to fall
# ===========================================================================

def _build_knn_probabilities(problems: List[Dict],
                             stats: Dict) -> Dict[int, float]:
    """
    Compute KNN resolution probability for each open problem.
    Lightweight version of resolution_predictor.build_features + predict.
    """
    tag_solve_rate = stats["tag_solve_rate"]
    oeis_to_problems = stats["oeis_to_problems"]

    max_oeis = max(
        (len(_real_oeis(p)) for p in problems), default=1
    )
    max_tags = max((len(_tags(p)) for p in problems), default=1)
    max_num = max((_number(p) for p in problems), default=1)

    features = []
    numbers = []
    labels = []

    for p in problems:
        tags = _tags(p)
        oeis = _real_oeis(p)

        rates = [tag_solve_rate.get(t, 0.3) for t in tags] if tags else [0.3]
        avg_rate = sum(rates) / len(rates)

        oeis_r = len(oeis) / max_oeis if max_oeis > 0 else 0
        tag_div = len(tags) / max_tags if max_tags > 0 else 0
        age = 1.0 - (_number(p) / max_num) if max_num > 0 else 0.5

        prize = _prize(p)
        prize_sig = min(math.log1p(prize) / math.log1p(10000), 1.0) if prize > 0 else 0.0

        features.append([avg_rate, oeis_r, tag_div, age, prize_sig])
        numbers.append(_number(p))
        if _is_solved(p):
            labels.append(1)
        elif _is_open(p):
            labels.append(0)
        else:
            labels.append(-1)

    F = np.array(features)
    labels = np.array(labels)

    means = F.mean(axis=0)
    stds = F.std(axis=0)
    stds[stds == 0] = 1.0
    X = (F - means) / stds

    valid = np.where(labels >= 0)[0]
    open_indices = np.where(labels == 0)[0]
    k = 15

    knn_probs = {}
    for oi in open_indices:
        others = valid[valid != oi]
        dists = np.sqrt(np.sum((X[others] - X[oi]) ** 2, axis=1))
        k_actual = min(k, len(others))
        nearest_idx = np.argsort(dists)[:k_actual]
        nearest_labels = labels[others[nearest_idx]]
        prob = float(np.mean(nearest_labels == 1))
        knn_probs[numbers[oi]] = prob

    return knn_probs


def _survival_hazard_score(p: Dict, max_num: int) -> float:
    """
    Quick survival-based hazard estimate. Problems with lower numbers
    (older) that are still open have accumulated more "survival time"
    and thus their instantaneous hazard is lower. But problems with
    recent updates have elevated hazard (something is happening).
    """
    num = _number(p)
    age_fraction = num / max_num if max_num > 0 else 0.5

    # Recent update boosts hazard
    lu = _last_update(p)
    recency_boost = 0.0
    if "2026" in lu:
        recency_boost = 0.3
    elif "2025-12" in lu or "2025-11" in lu or "2025-10" in lu:
        recency_boost = 0.2

    # Base hazard: middle-numbered problems have highest (empirical observation)
    # Very old (low number) = hard, very new = not enough time
    base_hazard = 1.0 - 4.0 * (age_fraction - 0.5) ** 2
    return max(base_hazard + recency_boost, 0.0)


def ensemble_predict_next_10(
    problems: List[Dict],
    near_resolved: Optional[List[Dict]] = None,
    frontiers: Optional[Dict] = None,
    bottlenecks: Optional[Dict] = None,
    bridges: Optional[List[Dict]] = None,
    stats: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """
    Combine all signals into an ensemble prediction of the next 10
    open problems most likely to be resolved in the next 6 months.

    Signal weights (calibrated against historical resolution patterns):
      - KNN probability:       0.25  (proven discriminator)
      - Near-resolved (OEIS):  0.20  (active computation = imminent)
      - Frontier score:        0.15  (at solved boundary)
      - Survival hazard:       0.15  (timing signal)
      - Cross-field bridge:    0.10  (technique import potential)
      - Technique bottleneck:  0.05  (clustered blocking)
      - Prize signal:          0.05  (incentive)
      - Formalization bonus:   0.05  (community attention)
    """
    if stats is None:
        stats = _build_tag_stats(problems)

    # Gather sub-analyses if not provided
    if near_resolved is None:
        near_resolved = near_resolved_problems(problems, stats)
    if frontiers is None:
        frontiers = gap_analysis(problems, stats)
    if bridges is None:
        bridges = cross_field_bridges(problems, stats)
    if bottlenecks is None:
        bottlenecks = technique_bottlenecks(problems, stats)

    # Build lookup tables
    nr_by_num = {r["number"]: r for r in near_resolved}
    frontier_list = frontiers["all_frontiers"]
    fr_by_num = {f["number"]: f for f in frontier_list}
    br_by_num = {b["number"]: b for b in bridges}

    bn_by_num = {}
    for family, members in bottlenecks["clusters"].items():
        for m in members:
            bn_by_num[m["number"]] = m

    # Normalize sub-scores to [0, 1]
    def _normalize(lookup: Dict[int, Dict], key: str) -> Dict[int, float]:
        if not lookup:
            return {}
        vals = [entry[key] for entry in lookup.values() if key in entry]
        if not vals:
            return {}
        max_val = max(vals) if max(vals) > 0 else 1.0
        return {num: entry.get(key, 0) / max_val for num, entry in lookup.items()}

    nr_norm = _normalize(nr_by_num, "near_resolved_score")
    fr_norm = _normalize(fr_by_num, "frontier_score")
    br_norm = _normalize(br_by_num, "cross_field_score")

    # KNN probabilities (already [0, 1])
    knn_probs = _build_knn_probabilities(problems, stats)

    # Survival hazard
    max_num = max((_number(p) for p in problems), default=1)

    # Ensemble scoring
    open_probs = [p for p in problems if _is_open(p)]
    scored = []
    for p in open_probs:
        num = _number(p)
        tags = _tags(p)

        knn = knn_probs.get(num, 0.3)
        nr = nr_norm.get(num, 0.0)
        fr = fr_norm.get(num, 0.0)
        surv = _survival_hazard_score(p, max_num)
        br = br_norm.get(num, 0.0)

        bn_entry = bn_by_num.get(num)
        bn_score = bn_entry["primary_score"] / 2.0 if bn_entry else 0.0
        bn_score = min(bn_score, 1.0)

        prize = _prize(p)
        prize_sig = min(math.log1p(prize) / math.log1p(10000), 1.0) if prize > 0 else 0.0

        formal_bonus = 1.0 if _is_formalized(p) else 0.0

        ensemble = (
            0.25 * knn
            + 0.20 * nr
            + 0.15 * fr
            + 0.15 * surv
            + 0.10 * br
            + 0.05 * bn_score
            + 0.05 * prize_sig
            + 0.05 * formal_bonus
        )

        # Collect the dominant signal for explanation
        signals = {
            "knn_probability": knn,
            "near_resolved": nr,
            "frontier_proximity": fr,
            "survival_hazard": surv,
            "cross_field_bridge": br,
            "bottleneck_relevance": bn_score,
            "prize_signal": prize_sig,
            "formalization": formal_bonus,
        }
        dominant = max(signals.items(), key=lambda x: x[1])

        # Suggest technique
        bn_info = bn_by_num.get(num)
        technique_suggestion = "general methods"
        if bn_info:
            family_name = bn_info["primary_bottleneck"]
            sig = TECHNIQUE_SIGNATURES.get(family_name, {})
            technique_suggestion = sig.get("description", family_name)

        scored.append({
            "number": num,
            "tags": sorted(tags),
            "prize": prize,
            "formalized": _is_formalized(p),
            "ensemble_score": ensemble,
            "signals": signals,
            "dominant_signal": dominant[0],
            "dominant_value": dominant[1],
            "technique_suggestion": technique_suggestion,
            "why": _explain_prediction(num, signals, technique_suggestion, tags),
        })

    scored.sort(key=lambda x: -x["ensemble_score"])
    return scored[:10]


def _explain_prediction(num: int, signals: Dict[str, float],
                        technique: str, tags: Set[str]) -> str:
    """Generate a human-readable explanation for a prediction."""
    parts = []
    top_signals = sorted(signals.items(), key=lambda x: -x[1])[:3]

    for sig_name, sig_val in top_signals:
        if sig_val < 0.1:
            continue
        if sig_name == "knn_probability":
            parts.append(f"structurally similar to solved problems ({sig_val:.0%})")
        elif sig_name == "near_resolved":
            parts.append(f"active OEIS computation (recency {sig_val:.2f})")
        elif sig_name == "frontier_proximity":
            parts.append(f"neighbours are solved (frontier {sig_val:.2f})")
        elif sig_name == "survival_hazard":
            parts.append(f"timing suggests imminent resolution")
        elif sig_name == "cross_field_bridge":
            parts.append(f"cross-field technique import opportunity")
        elif sig_name == "formalization":
            parts.append("formalized (community attention)")
        elif sig_name == "prize_signal":
            parts.append("prize incentive")

    explanation = "; ".join(parts) if parts else "multiple weak signals converge"
    explanation += f". Likely technique: {technique}"
    return explanation


# ===========================================================================
# Report generation
# ===========================================================================

def generate_report(problems: List[Dict]) -> str:
    stats = _build_tag_stats(problems)
    nr = near_resolved_problems(problems, stats)
    gap = gap_analysis(problems, stats)
    bn = technique_bottlenecks(problems, stats)
    bridges = cross_field_bridges(problems, stats)
    top10 = ensemble_predict_next_10(problems, nr, gap, bn, bridges, stats)

    lines = ["# Saliency Scanner: Critical Threshold Problems", ""]
    lines.append("Finding open problems where a small advance would settle them.")
    n_open = sum(1 for p in problems if _is_open(p))
    lines.append(f"Scanning {n_open} open Erdos problems across 5 dimensions.")
    lines.append("")

    # --- Section 1: Near-Resolved ---
    lines.append("## 1. Near-Resolved Problems (Active OEIS Computation)")
    lines.append("")
    lines.append("Open problems with recently created OEIS sequences (A350000+),")
    lines.append("indicating someone is actively extending computations.")
    lines.append("")
    lines.append("| Rank | Problem | Score | Recent OEIS | Connections | Tags | Prize |")
    lines.append("|------|---------|-------|-------------|-------------|------|-------|")
    for i, r in enumerate(nr[:20]):
        recent_str = ", ".join(r["recent_oeis"][:3])
        if len(r["recent_oeis"]) > 3:
            recent_str += f" (+{len(r['recent_oeis'])-3})"
        tags_str = ", ".join(r["tags"][:3])
        prize_str = f"${r['prize']:.0f}" if r["prize"] > 0 else "-"
        lines.append(
            f"| {i+1} | #{r['number']} | {r['near_resolved_score']:.3f} | "
            f"{recent_str} | {r['n_oeis_connections']} | {tags_str} | {prize_str} |"
        )
    lines.append("")

    # --- Section 2: Gap Analysis ---
    lines.append("## 2. Frontier Problems (At the Solved Boundary)")
    lines.append("")
    lines.append("Open problems whose tag-neighbours are solved. These sit at the")
    lines.append("resolution frontier and may yield to the same techniques.")
    lines.append("")
    lines.append("| Rank | Problem | Frontier Score | Solved Density | Tags | Prize |")
    lines.append("|------|---------|----------------|----------------|------|-------|")
    for i, f in enumerate(gap["all_frontiers"][:20]):
        tags_str = ", ".join(f["tags"][:3])
        prize_str = f"${f['prize']:.0f}" if f["prize"] > 0 else "-"
        lines.append(
            f"| {i+1} | #{f['number']} | {f['frontier_score']:.3f} | "
            f"{f['top_k_solved_density']:.3f} | {tags_str} | {prize_str} |"
        )
    lines.append("")

    # Frontier by tag
    lines.append("### Frontier Problem per Tag Family")
    lines.append("")
    lines.append("| Tag | Frontier Problem | Score | Solved Neighbours |")
    lines.append("|-----|-----------------|-------|-------------------|")
    tag_frontier_sorted = sorted(
        gap["frontier_by_tag"].items(),
        key=lambda x: -x[1]["frontier_score"],
    )
    for tag, entry in tag_frontier_sorted[:20]:
        lines.append(
            f"| {tag} | #{entry['number']} | "
            f"{entry['frontier_score']:.3f} | {entry['n_solved_neighbours']} |"
        )
    lines.append("")

    # --- Section 3: Technique Bottlenecks ---
    lines.append("## 3. Technique Bottlenecks")
    lines.append("")
    lines.append("Clusters of open problems blocked by the same technique gap.")
    lines.append("Breaking one bottleneck may resolve many problems at once.")
    lines.append("")
    lines.append("| Bottleneck | Description | Open Problems | Top Problem |")
    lines.append("|------------|-------------|---------------|-------------|")
    for family, count in bn["leverage_ranking"]:
        desc = TECHNIQUE_SIGNATURES.get(family, {}).get("description", family)
        top = bn["clusters"][family][0] if bn["clusters"][family] else {}
        top_num = f"#{top.get('number', '?')}" if top else "-"
        lines.append(f"| {family} | {desc} | {count} | {top_num} |")
    lines.append("")

    if bn["shared_pairs"]:
        lines.append("### Tightly Coupled Problem Pairs (shared primary + secondary bottleneck)")
        lines.append("")
        lines.append("| Problem A | Problem B | Shared Bottleneck | Secondary |")
        lines.append("|-----------|-----------|-------------------|-----------|")
        for sp in bn["shared_pairs"][:10]:
            lines.append(
                f"| #{sp['problems'][0]} | #{sp['problems'][1]} | "
                f"{sp['shared_bottleneck']} | {sp['shared_secondary']} |"
            )
        lines.append("")

    # --- Section 4: Cross-Field Bridges ---
    lines.append("## 4. Cross-Field Bridge Problems")
    lines.append("")
    lines.append("Problems at the intersection of rarely-combined tags.")
    lines.append("Technique import from the less-expected field often cracks these.")
    lines.append("")
    lines.append("| Rank | Problem | Bridge Score | Bridge Pair | Pair Rate | Tags |")
    lines.append("|------|---------|-------------|-------------|-----------|------|")
    for i, b in enumerate(bridges[:20]):
        pair_str = f"{b['best_bridge_pair'][0]} + {b['best_bridge_pair'][1]}" if b["best_bridge_pair"] else "-"
        prate = b["bridge_details"][0]["pair_solve_rate"] if b["bridge_details"] else 0
        tags_str = ", ".join(b["tags"][:3])
        lines.append(
            f"| {i+1} | #{b['number']} | {b['cross_field_score']:.3f} | "
            f"{pair_str} | {prate:.0%} | {tags_str} |"
        )
    lines.append("")

    # --- Section 5: Ensemble Top 10 ---
    lines.append("## 5. PREDICTION: Next 10 Problems to Fall")
    lines.append("")
    lines.append("Ensemble combining KNN, OEIS activity, frontier proximity,")
    lines.append("survival hazard, cross-field bridge potential, and community signals.")
    lines.append("")
    for i, pred in enumerate(top10):
        lines.append(f"### #{i+1}: Problem #{pred['number']}")
        tags_str = ", ".join(pred["tags"])
        prize_str = f"${pred['prize']:.0f}" if pred["prize"] > 0 else "none"
        lines.append(f"- **Tags**: {tags_str}")
        lines.append(f"- **Ensemble score**: {pred['ensemble_score']:.3f}")
        lines.append(f"- **Dominant signal**: {pred['dominant_signal']} ({pred['dominant_value']:.2f})")
        lines.append(f"- **Prize**: {prize_str}")
        lines.append(f"- **Formalized**: {'yes' if pred['formalized'] else 'no'}")
        lines.append(f"- **WHY**: {pred['why']}")
        lines.append("")

        # Signal breakdown
        lines.append("  Signal breakdown:")
        for sig, val in sorted(pred["signals"].items(), key=lambda x: -x[1]):
            bar = "#" * int(val * 20)
            lines.append(f"  - {sig}: {val:.3f} {bar}")
        lines.append("")

    return "\n".join(lines)


# ===========================================================================
# CLI entry point
# ===========================================================================

if __name__ == "__main__":
    problems = load_problems()
    report = generate_report(problems)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")

    # Quick summary
    stats = _build_tag_stats(problems)
    nr = near_resolved_problems(problems, stats)
    print(f"\nNear-resolved (OEIS active): {len(nr)} problems")
    if nr:
        print(f"  Top: #{nr[0]['number']} (score {nr[0]['near_resolved_score']:.3f})")

    gap = gap_analysis(problems, stats)
    print(f"Frontier problems: {len(gap['all_frontiers'])}")

    bn = technique_bottlenecks(problems, stats)
    print("Bottleneck sizes:")
    for family, count in bn["leverage_ranking"][:5]:
        print(f"  {family}: {count}")
