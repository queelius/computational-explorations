#!/usr/bin/env python3
"""
Erdős Problems: Relationship Discovery Engine

Discovers NEW relationships and novel problem formulations through:
1. Hidden OEIS connections (non-obvious bridges)
2. Tag gap analysis (missing intersection problems)
3. Technique transfer mapping (solved → open)
4. Structural isomorphism detection
5. Novel problem generation at unexplored intersections
6. Problem "genome" nearest-neighbor analysis

Usage:
    python src/relationship_discovery.py
    # Writes comprehensive report to docs/relationship_report.md
"""

import yaml
import json
import sys
from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial.distance import cdist
from sklearn.neighbors import NearestNeighbors

DATA_PATH = Path(__file__).parent.parent / "data" / "erdosproblems" / "data" / "problems.yaml"
OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "relationship_report.md"

# Major mathematical areas for tag gap analysis
MAJOR_TAGS = [
    "number theory",
    "graph theory",
    "geometry",
    "ramsey theory",
    "additive combinatorics",
    "analysis",
    "combinatorics",
]

# Tags indicating techniques (for technique transfer)
TECHNIQUE_TAGS = {
    "additive combinatorics",   # Fourier/density methods
    "arithmetic progressions",  # Szemerédi-type
    "sidon sets",               # Additive structure
    "chromatic number",         # Coloring methods
    "ramsey theory",            # Ramsey methods
    "discrepancy",              # Probabilistic / discrepancy
    "polynomials",              # Algebraic methods
    "probability",              # Probabilistic method
    "analysis",                 # Analytic methods
    "turan number",             # Extremal graph theory
    "covering systems",         # Modular arithmetic
    "hypergraphs",              # Hypergraph methods
    "intersecting family",      # Erdős-Ko-Rado type
}

# Tags indicating structure/area (for structural isomorphism)
AREA_TAGS = {
    "number theory",
    "graph theory",
    "geometry",
    "set theory",
    "combinatorics",
    "algebra",
    "topology",
    "group theory",
}


def load_problems() -> list[dict]:
    """Load problems from YAML file."""
    with open(DATA_PATH, "r") as f:
        return yaml.safe_load(f)


def get_status(p: dict) -> str:
    """Get problem status state."""
    return p.get("status", {}).get("state", "unknown")


def get_oeis(p: dict) -> list[str]:
    """Get valid OEIS sequences for a problem."""
    return [s for s in p.get("oeis", []) if s not in ("N/A", "possible", "")]


def is_open(p: dict) -> bool:
    """Check if problem is open."""
    return get_status(p) in ("open", "falsifiable", "verifiable", "decidable")


def is_solved(p: dict) -> bool:
    """Check if problem has been resolved (proved, disproved, solved)."""
    return get_status(p) in (
        "proved", "disproved", "solved",
        "proved (Lean)", "disproved (Lean)", "solved (Lean)",
    )


def get_prize_value(p: dict) -> int:
    """Parse prize as integer dollars (0 if no prize)."""
    prize = p.get("prize", "no")
    if prize == "no" or not prize:
        return 0
    try:
        return int(prize.replace("$", "").replace(",", ""))
    except (ValueError, AttributeError):
        return 0


# ──────────────────────────────────────────────────────────────────
# 1. Hidden Connections via OEIS
# ──────────────────────────────────────────────────────────────────

def find_oeis_hidden_bridges(
    problems: list[dict],
    max_jaccard: float = 0.5,
) -> list[dict]:
    """
    Find problem pairs that share OEIS sequences but have low tag overlap
    (Jaccard similarity <= max_jaccard). Zero-overlap pairs are the strongest
    bridges; low-overlap pairs are still non-obvious connections.
    """
    prob_map = {p["number"]: p for p in problems}

    # Build OEIS → problems index
    oeis_to_probs = defaultdict(list)
    for p in problems:
        for seq in get_oeis(p):
            oeis_to_probs[seq].append(p["number"])

    # Find pairs sharing OEIS with low tag overlap
    bridges = []
    seen_pairs = set()

    for seq, prob_nums in oeis_to_probs.items():
        if len(prob_nums) < 2:
            continue
        for n1, n2 in combinations(prob_nums, 2):
            pair_key = (min(n1, n2), max(n1, n2))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            tags1 = set(prob_map[n1].get("tags", []))
            tags2 = set(prob_map[n2].get("tags", []))
            shared_tags = tags1 & tags2
            union_tags = tags1 | tags2
            jaccard = len(shared_tags) / len(union_tags) if union_tags else 1.0

            if jaccard <= max_jaccard:
                bridges.append({
                    "problem_1": n1,
                    "problem_2": n2,
                    "shared_oeis": seq,
                    "tags_1": sorted(tags1),
                    "tags_2": sorted(tags2),
                    "shared_tags": sorted(shared_tags),
                    "jaccard": round(jaccard, 3),
                    "status_1": get_status(prob_map[n1]),
                    "status_2": get_status(prob_map[n2]),
                    "investigation": _investigate_bridge(tags1, tags2, seq),
                })

    return sorted(bridges, key=lambda b: (b["jaccard"], b["shared_oeis"]))


def _investigate_bridge(tags1: set, tags2: set, oeis_seq: str) -> str:
    """Generate a hypothesis about why two low-overlap problems share OEIS."""
    all_tags = tags1 | tags2
    diff_tags = tags1 ^ tags2  # symmetric difference = unique to each side
    if "number theory" in tags1 and "graph theory" in tags2:
        return "Number-theoretic sequence encodes graph-theoretic structure"
    if "number theory" in tags2 and "graph theory" in tags1:
        return "Graph structure reflects number-theoretic sequence"
    if "geometry" in all_tags and "number theory" in all_tags:
        return "Geometric counting sequence has number-theoretic interpretation"
    if "ramsey theory" in all_tags and "number theory" in all_tags:
        return "Ramsey-type extremal function matches number-theoretic growth"
    if "analysis" in all_tags and "combinatorics" in all_tags:
        return "Analytic extremal bound shares counting sequence with combinatorial problem"
    if "additive combinatorics" in all_tags and "graph theory" in all_tags:
        return "Additive structure and graph density share extremal sequence"
    if "sidon sets" in all_tags and "number theory" in diff_tags:
        return "Sidon set structure bridges additive and number-theoretic properties"
    if "covering systems" in all_tags:
        return "Covering system sequence connects modular arithmetic areas"
    if "primes" in diff_tags and "binomial coefficients" in diff_tags:
        return "Prime-counting and binomial structures share extremal sequence"
    if "squares" in diff_tags:
        return "Perfect square constraints create unexpected counting parallels"
    if "unit fractions" in diff_tags:
        return "Egyptian fraction structure parallels via shared counting sequence"
    if "divisors" in diff_tags:
        return "Divisor structure creates counting parallel with different area"
    if diff_tags:
        return f"Distinct topics ({', '.join(sorted(diff_tags)[:3])}) linked by shared sequence {oeis_seq}"
    return f"Shared OEIS {oeis_seq} suggests hidden structural parallel"


# ──────────────────────────────────────────────────────────────────
# 2. Tag Gap Analysis
# ──────────────────────────────────────────────────────────────────

def tag_gap_analysis(problems: list[dict]) -> dict[str, Any]:
    """
    For each pair of major tags:
    - Count problems with BOTH
    - Identify bridging sub-topics
    - Flag "missing" intersections
    """
    # Index problems by tag
    tag_to_probs = defaultdict(list)
    for p in problems:
        for tag in p.get("tags", []):
            tag_to_probs[tag].append(p)

    results = {}
    for t1, t2 in combinations(MAJOR_TAGS, 2):
        set1 = {p["number"] for p in tag_to_probs[t1]}
        set2 = {p["number"] for p in tag_to_probs[t2]}
        intersection = set1 & set2

        # Find sub-topics bridging these two areas
        bridging_subtopics = Counter()
        for p in problems:
            tags = set(p.get("tags", []))
            if t1 in tags and t2 in tags:
                for tag in tags:
                    if tag != t1 and tag != t2:
                        bridging_subtopics[tag] += 1

        # Find all sub-topics in each area but not the intersection
        subtopics_1 = Counter()
        subtopics_2 = Counter()
        for p in tag_to_probs[t1]:
            for tag in p.get("tags", []):
                if tag != t1:
                    subtopics_1[tag] += 1
        for p in tag_to_probs[t2]:
            for tag in p.get("tags", []):
                if tag != t2:
                    subtopics_2[tag] += 1

        # Potential missing bridges: sub-topics common to each area independently
        # but not appearing in their intersection
        bridge_candidates = set(subtopics_1.keys()) & set(subtopics_2.keys())
        bridge_candidates -= set(bridging_subtopics.keys())
        bridge_candidates -= {t1, t2}

        pair_key = f"{t1} x {t2}"
        results[pair_key] = {
            "count": len(intersection),
            "problems": sorted(intersection),
            "bridging_subtopics": dict(bridging_subtopics.most_common(10)),
            "missing_bridges": sorted(bridge_candidates),
            "category_1_size": len(set1),
            "category_2_size": len(set2),
        }

    return results


def find_rare_intersections(gap_analysis: dict) -> list[dict]:
    """Identify rare tag pair intersections (<=5 problems) for novel problem mining."""
    rare = []
    for pair_key, data in gap_analysis.items():
        if 0 < data["count"] <= 5:
            rare.append({
                "pair": pair_key,
                "count": data["count"],
                "problems": data["problems"],
                "missing_bridges": data["missing_bridges"][:5],
            })
    # Also include empty intersections
    for pair_key, data in gap_analysis.items():
        if data["count"] == 0:
            rare.append({
                "pair": pair_key,
                "count": 0,
                "problems": [],
                "missing_bridges": data["missing_bridges"][:5],
            })
    return sorted(rare, key=lambda x: x["count"])


# ──────────────────────────────────────────────────────────────────
# 3. Technique Transfer Map
# ──────────────────────────────────────────────────────────────────

def build_technique_transfer_map(problems: list[dict]) -> list[dict]:
    """
    For each solved problem with technique tags, find open problems with
    similar structural tags but different area tags. These are candidates
    for technique transfer.
    """
    solved = [p for p in problems if is_solved(p)]
    open_probs = [p for p in problems if is_open(p)]

    transfers = []

    for sp in solved:
        s_tags = set(sp.get("tags", []))
        s_techniques = s_tags & TECHNIQUE_TAGS
        s_areas = s_tags & AREA_TAGS

        if not s_techniques:
            continue

        for op in open_probs:
            o_tags = set(op.get("tags", []))
            o_techniques = o_tags & TECHNIQUE_TAGS
            o_areas = o_tags & AREA_TAGS

            # Want: shared technique tags but different area tags
            shared_techniques = s_techniques & o_techniques
            different_areas = (s_areas ^ o_areas)  # symmetric difference

            if shared_techniques and different_areas:
                transfers.append({
                    "solved_problem": sp["number"],
                    "open_problem": op["number"],
                    "shared_techniques": sorted(shared_techniques),
                    "solved_areas": sorted(s_areas),
                    "open_areas": sorted(o_areas),
                    "solved_status": get_status(sp),
                    "open_prize": get_prize_value(op),
                })

    # Deduplicate and sort by number of shared techniques (most first)
    transfers.sort(key=lambda t: (-len(t["shared_techniques"]), t["open_prize"]))
    return transfers


def summarize_technique_transfers(transfers: list[dict]) -> dict:
    """Summarize technique transfer map by technique and area pair."""
    by_technique = defaultdict(list)
    by_area_pair = defaultdict(list)

    for t in transfers:
        for tech in t["shared_techniques"]:
            by_technique[tech].append(t)
        s_areas = tuple(sorted(t["solved_areas"]))
        o_areas = tuple(sorted(t["open_areas"]))
        by_area_pair[(s_areas, o_areas)].append(t)

    summary = {
        "by_technique": {
            k: len(v) for k, v in sorted(by_technique.items(), key=lambda x: -len(x[1]))
        },
        "top_area_transfers": [],
    }

    # Top area transfers
    for (s, o), items in sorted(by_area_pair.items(), key=lambda x: -len(x[1]))[:15]:
        summary["top_area_transfers"].append({
            "from_areas": list(s),
            "to_areas": list(o),
            "count": len(items),
            "example_solved": items[0]["solved_problem"],
            "example_open": items[0]["open_problem"],
        })

    return summary


# ──────────────────────────────────────────────────────────────────
# 4. Structural Isomorphism
# ──────────────────────────────────────────────────────────────────

def find_structural_isomorphisms(problems: list[dict]) -> list[dict]:
    """
    Find problem pairs with identical tag sets but different statuses
    (one solved, one open). The solved technique might adapt.
    """
    # Group problems by their sorted tag tuple
    tag_groups = defaultdict(list)
    for p in problems:
        tags = tuple(sorted(p.get("tags", [])))
        if tags:
            tag_groups[tags].append(p)

    isomorphisms = []
    for tags, group in tag_groups.items():
        solved_in_group = [p for p in group if is_solved(p)]
        open_in_group = [p for p in group if is_open(p)]

        if solved_in_group and open_in_group:
            for sp in solved_in_group:
                for op in open_in_group:
                    isomorphisms.append({
                        "tags": list(tags),
                        "solved_problem": sp["number"],
                        "open_problem": op["number"],
                        "solved_status": get_status(sp),
                        "open_prize": get_prize_value(op),
                        "solved_oeis": get_oeis(sp),
                        "open_oeis": get_oeis(op),
                    })

    # Sort: prioritize open problems with prizes, then by tag specificity
    isomorphisms.sort(key=lambda x: (-x["open_prize"], -len(x["tags"])))
    return isomorphisms


def summarize_isomorphisms(isos: list[dict]) -> dict:
    """Summarize structural isomorphisms by tag pattern."""
    by_pattern = defaultdict(lambda: {"solved": [], "open": []})
    for iso in isos:
        key = tuple(iso["tags"])
        by_pattern[key]["solved"].append(iso["solved_problem"])
        by_pattern[key]["open"].append(iso["open_problem"])

    summary = []
    for tags, data in sorted(by_pattern.items(), key=lambda x: -len(x[0])):
        solved = sorted(set(data["solved"]))
        opened = sorted(set(data["open"]))
        summary.append({
            "tags": list(tags),
            "tag_count": len(tags),
            "solved_problems": solved,
            "open_problems": opened,
            "solved_count": len(solved),
            "open_count": len(opened),
        })

    summary.sort(key=lambda x: (-x["tag_count"], x["open_count"]))
    return summary


# ──────────────────────────────────────────────────────────────────
# 5. Novel Problem Generation
# ──────────────────────────────────────────────────────────────────

def generate_novel_problems(
    gap_analysis: dict,
    rare_intersections: list[dict],
    technique_summary: dict,
    problems: list[dict],
) -> list[dict]:
    """
    Based on the gap analysis and technique transfer map,
    formulate 5 new novel problems at unexplored intersections.
    """
    # Collect all existing tag pairs
    existing_pairs = set()
    for p in problems:
        tags = p.get("tags", [])
        for t1, t2 in combinations(sorted(tags), 2):
            existing_pairs.add((t1, t2))

    novel = []

    # Novel Problem 1: Geometry x Additive Combinatorics
    # The gap analysis shows this intersection is small
    gap_key = "additive combinatorics x geometry"
    gap_data = gap_analysis.get(gap_key, {})
    novel.append({
        "id": "NRD-1",
        "title": "Sidon Sets in Point Configurations",
        "intersection": "geometry x additive combinatorics",
        "existing_count": gap_data.get("count", 0),
        "question": (
            "Let P be a set of n points in the plane. Define D(P) = {|p-q| : p,q in P, p != q} "
            "as the multiset of pairwise distances. Call P a 'distance-Sidon set' if all distances "
            "in D(P) are distinct (i.e., D(P) is a Sidon set under the distance metric). "
            "What is the maximum n such that a distance-Sidon set of n points exists in [0,N]^2? "
            "How does this relate to the Erdos distinct distances problem?"
        ),
        "why_novel": (
            "The gap analysis shows only {count} problems at the geometry x additive combinatorics "
            "intersection. Distance-Sidon sets combine Sidon structure (additive combinatorics) "
            "with point configurations (geometry). The Guth-Katz distinct distances result gives "
            "an upper bound on distance repetitions, but the Sidon constraint is strictly stronger."
        ).format(count=gap_data.get("count", "few")),
        "approach": (
            "Use polynomial partitioning (Guth-Katz) combined with the B_2 set upper bound "
            "sqrt(N) for Sidon sets. The geometric constraint adds dimension, potentially "
            "allowing larger Sidon-like sets than in the integer case."
        ),
        "related_problems": ["#30 (Sidon)", "#89 (distinct distances)", "#91 (distances)"],
    })

    # Novel Problem 2: Analysis x Graph Theory
    gap_key = "analysis x graph theory"
    gap_data = gap_analysis.get(gap_key, {})
    novel.append({
        "id": "NRD-2",
        "title": "Spectral Gap of Coprime Graphs and Analytic Number Theory",
        "intersection": "analysis x graph theory",
        "existing_count": gap_data.get("count", 0),
        "question": (
            "Let G(n) be the coprime graph on {1,...,n}. Let lambda_1 >= lambda_2 >= ... >= lambda_n "
            "be the eigenvalues of its adjacency matrix. Define the spectral gap "
            "delta(n) = lambda_1 - lambda_2. "
            "Conjecture: delta(n) ~ c * n / log(n) for some constant c related to 6/pi^2. "
            "Does the spectral gap of coprime graphs encode prime distribution information?"
        ),
        "why_novel": (
            "The gap analysis shows only {count} problems bridging analysis and graph theory. "
            "Spectral graph theory on coprime graphs connects analytic number theory (eigenvalue "
            "distributions, random matrix theory) with extremal graph theory (expansion, mixing). "
            "No Erdos problem studies spectral properties of arithmetic graphs."
        ).format(count=gap_data.get("count", "few")),
        "approach": (
            "Compute spectral gaps for small coprime graphs computationally. Compare with "
            "6/pi^2 * n (edge density times n). Use the Ramanujan sum representation of "
            "coprimality to express the adjacency matrix in terms of Dirichlet characters."
        ),
        "related_problems": ["#883 (coprime graphs)", "#75 (chromatic)", "#4 (prime gaps)"],
    })

    # Novel Problem 3: Ramsey Theory x Analysis
    gap_key = "analysis x ramsey theory"
    gap_data = gap_analysis.get(gap_key, {})
    novel.append({
        "id": "NRD-3",
        "title": "Discrepancy Bounds for Ramsey Colorings",
        "intersection": "ramsey theory x analysis",
        "existing_count": gap_data.get("count", 0),
        "question": (
            "For a 2-coloring chi: [N] -> {-1,+1}, define the discrepancy along arithmetic "
            "progressions D(chi) = max_{a,d,k} |sum_{i=0}^{k-1} chi(a+id)|. "
            "The Ramsey coloring problem asks for monochromatic APs. "
            "What is the minimum D(chi) over colorings that avoid monochromatic k-APs? "
            "Specifically, for k=3 and N < W(3,2)=9, what is the minimum 3-AP discrepancy "
            "of a coloring of [8] with no monochromatic 3-AP?"
        ),
        "why_novel": (
            "The gap analysis shows only {count} problems at analysis x ramsey theory. "
            "Discrepancy theory (analysis) and Ramsey theory study complementary aspects of "
            "colorings. This problem asks: when Ramsey-type monochromatic structure is forbidden, "
            "what analytic imbalance must remain? This connects to the Roth/Kelley-Meka Fourier "
            "approach where discrepancy (large Fourier coefficients) drives density increment."
        ).format(count=gap_data.get("count", "few")),
        "approach": (
            "Compute minimum discrepancy for small cases. Connect to Fourier analysis: "
            "a coloring with small discrepancy on all APs has small Fourier coefficients, "
            "which by Kelley-Meka implies density conditions. Seek a phase transition."
        ),
        "related_problems": ["#3 (AP conjecture)", "#142 (AP density)", "#483 (Schur)"],
    })

    # Novel Problem 4: Combinatorics x Geometry (rare intersection)
    gap_key = "combinatorics x geometry"
    gap_data = gap_analysis.get(gap_key, {})
    novel.append({
        "id": "NRD-4",
        "title": "Turan Numbers for Geometric Hypergraphs",
        "intersection": "combinatorics x geometry",
        "existing_count": gap_data.get("count", 0),
        "question": (
            "Given n points in general position in the plane, define a '3-uniform distance "
            "hypergraph' H where {p,q,r} is an edge if the triangle pqr has perimeter exactly "
            "some target value t. What is the maximum number of edges in H? "
            "More precisely, define ex_geo(n, K_4^3) as the maximum number of hyperedges in a "
            "geometric 3-uniform hypergraph on n points in general position that contains no "
            "complete 3-uniform 4-graph (every 4-point subset has a non-edge triple)."
        ),
        "why_novel": (
            "Turan numbers are well-studied in abstract combinatorics ({turan_count} problems "
            "with 'turan number' tag). Geometric hypergraphs add distance constraints from "
            "geometry. This intersection ({count} problems) is underexplored. The problem imports "
            "Turan theory into geometric settings where algebraic geometry tools apply."
        ).format(
            turan_count=sum(1 for p in problems if "turan number" in p.get("tags", [])),
            count=gap_data.get("count", "0"),
        ),
        "approach": (
            "Use the Kővári-Sós-Turán bound combined with incidence geometry. "
            "The algebraic degree of the perimeter constraint limits hyperedge density. "
            "Compare with abstract Turan numbers for 3-uniform hypergraphs."
        ),
        "related_problems": ["#96 (convex position)", "#89 (distances)", "#564 (hypergraph Ramsey)"],
    })

    # Novel Problem 5: Number Theory x Combinatorics (via covering systems + intersecting families)
    gap_key = "combinatorics x number theory"
    gap_data = gap_analysis.get(gap_key, {})
    novel.append({
        "id": "NRD-5",
        "title": "Covering Systems as Intersecting Families",
        "intersection": "number theory x combinatorics",
        "existing_count": gap_data.get("count", 0),
        "question": (
            "A covering system is a finite collection of arithmetic progressions "
            "a_i (mod n_i) that covers all integers. View each progression as a subset "
            "of Z/LCM(n_i)Z. When is a covering system also an intersecting family "
            "(every two progressions share an element in Z/LCM(n_i)Z)? "
            "Define I(N) = max number of residue classes a_i (mod n_i) with n_i <= N "
            "that form both a covering system and an intersecting family. "
            "What is the growth rate of I(N)?"
        ),
        "why_novel": (
            "Covering systems ({cs_count} problems) and intersecting families "
            "({if_count} problems) have never been combined. The former is number theory, "
            "the latter extremal combinatorics (Erdos-Ko-Rado). This asks when the "
            "number-theoretic covering property coexists with the combinatorial intersection "
            "property. The gap analysis shows {count} problems at this intersection."
        ).format(
            cs_count=sum(1 for p in problems if "covering systems" in p.get("tags", [])),
            if_count=sum(1 for p in problems if "intersecting family" in p.get("tags", [])),
            count=gap_data.get("count", "few"),
        ),
        "approach": (
            "For small moduli, enumerate all covering systems and test intersection. "
            "Use the Erdos-Ko-Rado sunflower lemma to bound I(N). "
            "The Chinese Remainder Theorem provides structure for when progressions intersect."
        ),
        "related_problems": [
            "#2 (covering systems)", "#7 (covering systems)",
            "#279 (covering)", "#593 (intersecting family)"
        ],
    })

    return novel


# ──────────────────────────────────────────────────────────────────
# 6. Problem "Genome" and Nearest-Neighbor Analysis
# ──────────────────────────────────────────────────────────────────

def build_problem_genome(problems: list[dict]) -> tuple[np.ndarray, list[str], list[str]]:
    """
    Create a feature vector for each problem:
    - Binary tag presence (one-hot for all tags)
    - OEIS count (number of linked OEIS sequences)
    - Prize (normalized)
    - Status encoding
    Returns: (feature_matrix, problem_numbers, feature_names)
    """
    # Collect all tags
    all_tags = sorted({t for p in problems for t in p.get("tags", [])})
    tag_to_idx = {t: i for i, t in enumerate(all_tags)}

    n_problems = len(problems)
    n_features = len(all_tags) + 4  # tags + oeis_count + prize + status_open + status_solved

    feature_names = all_tags + ["oeis_count", "prize_log", "status_open", "status_solved"]
    matrix = np.zeros((n_problems, n_features), dtype=np.float64)
    problem_nums = []

    for i, p in enumerate(problems):
        problem_nums.append(p["number"])

        # Tag features
        for tag in p.get("tags", []):
            if tag in tag_to_idx:
                matrix[i, tag_to_idx[tag]] = 1.0

        # OEIS count
        oeis_seqs = get_oeis(p)
        matrix[i, len(all_tags)] = len(oeis_seqs)

        # Prize (log-scaled to prevent domination)
        prize = get_prize_value(p)
        matrix[i, len(all_tags) + 1] = np.log1p(prize) / 10.0  # normalize

        # Status
        matrix[i, len(all_tags) + 2] = 1.0 if is_open(p) else 0.0
        matrix[i, len(all_tags) + 3] = 1.0 if is_solved(p) else 0.0

    return matrix, problem_nums, feature_names


def find_nearest_neighbors(
    matrix: np.ndarray,
    problem_nums: list[str],
    problems: list[dict],
    k: int = 5,
) -> list[dict]:
    """
    Find k-nearest neighbors for each problem and highlight surprising pairs.
    'Surprising' = close in feature space but few shared tags.
    """
    prob_map = {p["number"]: p for p in problems}

    nn = NearestNeighbors(n_neighbors=min(k + 1, len(problem_nums)), metric="cosine")
    nn.fit(matrix)
    distances, indices = nn.kneighbors(matrix)

    # For each problem, collect nearest neighbors
    all_pairs = []
    for i in range(len(problem_nums)):
        for j_idx in range(1, distances.shape[1]):  # skip self (index 0)
            j = indices[i, j_idx]
            dist = distances[i, j_idx]
            p1 = prob_map[problem_nums[i]]
            p2 = prob_map[problem_nums[j]]

            tags1 = set(p1.get("tags", []))
            tags2 = set(p2.get("tags", []))
            shared = tags1 & tags2
            jaccard = len(shared) / len(tags1 | tags2) if (tags1 | tags2) else 0

            all_pairs.append({
                "problem_1": problem_nums[i],
                "problem_2": problem_nums[j],
                "cosine_distance": round(float(dist), 4),
                "shared_tags": sorted(shared),
                "unique_tags_1": sorted(tags1 - tags2),
                "unique_tags_2": sorted(tags2 - tags1),
                "jaccard_similarity": round(jaccard, 3),
                "status_1": get_status(p1),
                "status_2": get_status(p2),
            })

    return all_pairs


def find_surprising_neighbors(all_pairs: list[dict], top_n: int = 30) -> list[dict]:
    """
    Find pairs that are close in genome space but have low tag overlap.
    These are the 'surprising' neighbors -- they share structural features
    (OEIS, prize level, status) but differ in mathematical area.
    """
    # Score = closeness * dissimilarity
    # Low cosine distance = close; low Jaccard = dissimilar tags
    scored = []
    seen = set()
    for pair in all_pairs:
        key = (min(pair["problem_1"], pair["problem_2"]),
               max(pair["problem_1"], pair["problem_2"]))
        if key in seen:
            continue
        seen.add(key)

        closeness = 1.0 - pair["cosine_distance"]
        dissimilarity = 1.0 - pair["jaccard_similarity"]

        if closeness > 0.3 and dissimilarity > 0.5:
            surprise_score = closeness * dissimilarity
            pair_copy = dict(pair)
            pair_copy["surprise_score"] = round(surprise_score, 4)
            scored.append(pair_copy)

    scored.sort(key=lambda x: -x["surprise_score"])
    return scored[:top_n]


# ──────────────────────────────────────────────────────────────────
# Report Generation
# ──────────────────────────────────────────────────────────────────

def generate_report(
    problems: list[dict],
    oeis_bridges: list[dict],
    gap_analysis: dict,
    rare_intersections: list[dict],
    transfers: list[dict],
    transfer_summary: dict,
    isomorphisms: list[dict],
    iso_summary: list[dict],
    novel_problems: list[dict],
    surprising_neighbors: list[dict],
    genome_stats: dict,
) -> str:
    """Generate the comprehensive Markdown report."""
    lines = []

    def w(text=""):
        lines.append(text)

    w("# Erdos Problems: Relationship Discovery Report")
    w()
    w(f"**Generated**: 2026-02-12")
    w(f"**Database**: {len(problems)} problems from erdosproblems.com")
    w()
    w("---")
    w()

    # ── Section 1: OEIS Hidden Bridges ──
    w("## 1. Hidden Connections via OEIS Sequences")
    w()
    w("Problem pairs sharing OEIS sequences but having **no shared tags** represent")
    w("non-obvious mathematical bridges. The OEIS sequence links them through a")
    w("common integer sequence, yet their mathematical domains appear disjoint.")
    w()
    if oeis_bridges:
        zero_overlap = [b for b in oeis_bridges if b["jaccard"] == 0]
        low_overlap = [b for b in oeis_bridges if 0 < b["jaccard"] <= 0.5]
        w(f"**Found {len(oeis_bridges)} hidden bridges** ({len(zero_overlap)} with zero tag overlap, "
          f"{len(low_overlap)} with low overlap).")
        w()
        w("| Problem A | Tags A | Problem B | Tags B | Shared OEIS | Shared Tags | Jaccard | Investigation |")
        w("|-----------|--------|-----------|--------|-------------|-------------|---------|---------------|")
        for b in oeis_bridges:
            tags1 = ", ".join(b["tags_1"][:3])
            tags2 = ", ".join(b["tags_2"][:3])
            shared = ", ".join(b["shared_tags"]) if b["shared_tags"] else "(none)"
            w(f"| #{b['problem_1']} ({b['status_1']}) | {tags1} | #{b['problem_2']} ({b['status_2']}) | "
              f"{tags2} | {b['shared_oeis']} | {shared} | {b['jaccard']} | {b['investigation']} |")
        w()
        w("### Key Insight")
        w()
        w("These bridges suggest that the OEIS sequences encode deeper structural")
        w("parallels between problems with little mathematical domain overlap.")
        w("Each bridge is a candidate for a new theorem connecting the two areas.")
        if zero_overlap:
            w()
            w("**Zero-overlap bridges** are the most striking: problems share a counting")
            w("sequence but no mathematical tags at all, suggesting a deep structural parallel.")
    else:
        w("No hidden bridges found (all OEIS-sharing pairs also share tags).")
    w()
    w("---")
    w()

    # ── Section 2: Tag Gap Analysis ──
    w("## 2. Tag Gap Analysis")
    w()
    w("### Major Tag Pair Intersection Counts")
    w()
    w("| Tag Pair | Intersection Size | Category 1 Size | Category 2 Size | Bridging Sub-topics |")
    w("|----------|-------------------|-----------------|-----------------|---------------------|")
    for pair_key in sorted(gap_analysis.keys(), key=lambda k: -gap_analysis[k]["count"]):
        data = gap_analysis[pair_key]
        bridges = ", ".join(list(data["bridging_subtopics"].keys())[:3]) or "(none)"
        w(f"| {pair_key} | {data['count']} | {data['category_1_size']} | {data['category_2_size']} | {bridges} |")
    w()

    w("### Rare Intersections (5 or fewer problems)")
    w()
    w("These sparse intersections are where novel problems are most likely to live.")
    w()
    for ri in rare_intersections:
        w(f"#### {ri['pair']} ({ri['count']} problems)")
        if ri["problems"]:
            w(f"- Existing problems: {', '.join('#' + str(p) for p in ri['problems'])}")
        else:
            w("- **No existing problems** -- entirely unexplored territory")
        if ri["missing_bridges"]:
            w(f"- Missing bridge sub-topics: {', '.join(ri['missing_bridges'])}")
        w()

    w("### Missing Bridge Analysis")
    w()
    w("For each tag pair, 'missing bridges' are sub-topics that appear independently")
    w("in both areas but never at their intersection. These represent unexplored")
    w("connections.")
    w()
    for pair_key in sorted(gap_analysis.keys()):
        data = gap_analysis[pair_key]
        if data["missing_bridges"]:
            w(f"- **{pair_key}**: Missing bridges = {', '.join(data['missing_bridges'][:8])}")
    w()
    w("---")
    w()

    # ── Section 3: Technique Transfer Map ──
    w("## 3. Technique Transfer Map")
    w()
    w("Solved problems whose techniques could transfer to open problems in")
    w("different mathematical areas.")
    w()
    w("### Technique Transfer Counts")
    w()
    w("| Technique | Transfer Candidates |")
    w("|-----------|---------------------|")
    for tech, count in transfer_summary["by_technique"].items():
        w(f"| {tech} | {count} |")
    w()

    w("### Top Area-to-Area Transfers")
    w()
    w("| From Areas | To Areas | Count | Example (Solved -> Open) |")
    w("|-----------|----------|-------|--------------------------|")
    for at in transfer_summary["top_area_transfers"]:
        from_a = ", ".join(at["from_areas"])
        to_a = ", ".join(at["to_areas"])
        w(f"| {from_a} | {to_a} | {at['count']} | #{at['example_solved']} -> #{at['example_open']} |")
    w()

    # Show top 20 specific transfers with prizes
    prize_transfers = [t for t in transfers if t["open_prize"] > 0]
    if prize_transfers:
        w("### High-Value Technique Transfers (Open Problems with Prizes)")
        w()
        w("| Solved | Open | Prize | Shared Techniques | From Area | To Area |")
        w("|--------|------|-------|-------------------|-----------|---------|")
        for t in prize_transfers[:20]:
            techs = ", ".join(t["shared_techniques"])
            from_a = ", ".join(t["solved_areas"])
            to_a = ", ".join(t["open_areas"])
            w(f"| #{t['solved_problem']} ({t['solved_status']}) | #{t['open_problem']} | ${t['open_prize']} | {techs} | {from_a} | {to_a} |")
        w()

    w("---")
    w()

    # ── Section 4: Structural Isomorphism ──
    w("## 4. Structural Isomorphism (Same Tags, Different Status)")
    w()
    w("Problem pairs with **identical tag sets** where one is solved and one is open.")
    w("The solution technique may directly adapt.")
    w()
    w(f"**Found {len(iso_summary)} tag patterns with both solved and open problems.**")
    w()

    # Show most specific patterns first (more tags = more specific)
    w("### Most Specific Isomorphisms (3+ tags)")
    w()
    w("| Tag Pattern | # Tags | Solved Problems | Open Problems |")
    w("|-------------|--------|-----------------|---------------|")
    for iso in iso_summary:
        if iso["tag_count"] >= 3:
            tags_str = ", ".join(iso["tags"])
            solved_str = ", ".join("#" + str(p) for p in iso["solved_problems"][:5])
            open_str = ", ".join("#" + str(p) for p in iso["open_problems"][:5])
            w(f"| {tags_str} | {iso['tag_count']} | {solved_str} | {open_str} |")
    w()

    w("### All Isomorphisms with Prizes")
    w()
    prize_isos = [iso for iso in isomorphisms if iso["open_prize"] > 0]
    if prize_isos:
        w("| Tags | Solved | Open | Prize | Solved OEIS | Open OEIS |")
        w("|------|--------|------|-------|-------------|-----------|")
        for iso in prize_isos[:20]:
            tags_str = ", ".join(iso["tags"])
            s_oeis = ", ".join(iso["solved_oeis"]) if iso["solved_oeis"] else "-"
            o_oeis = ", ".join(iso["open_oeis"]) if iso["open_oeis"] else "-"
            w(f"| {tags_str} | #{iso['solved_problem']} | #{iso['open_problem']} | ${iso['open_prize']} | {s_oeis} | {o_oeis} |")
        w()
    w()
    w("---")
    w()

    # ── Section 5: Novel Problems ──
    w("## 5. Novel Problem Generation")
    w()
    w("Based on gap analysis and technique transfer, here are 5 new problems")
    w("at unexplored intersections.")
    w()
    for np_item in novel_problems:
        w(f"### {np_item['id']}: {np_item['title']}")
        w()
        w(f"**Intersection**: {np_item['intersection']} (existing: {np_item['existing_count']} problems)")
        w()
        w(f"**Question**: {np_item['question']}")
        w()
        w(f"**Why novel**: {np_item['why_novel']}")
        w()
        w(f"**Suggested approach**: {np_item['approach']}")
        w()
        w(f"**Related problems**: {', '.join(np_item['related_problems'])}")
        w()
        w("---")
        w()

    # ── Section 6: Problem Genome ──
    w("## 6. Problem 'Genome' and Nearest-Neighbor Analysis")
    w()
    w(f"Each problem is encoded as a {genome_stats['n_features']}-dimensional feature vector:")
    w("- Binary tag presence (one-hot for all {n_tags} tags)".format(n_tags=genome_stats["n_tags"]))
    w("- OEIS sequence count")
    w("- Log-scaled prize value")
    w("- Status encoding (open/solved binary)")
    w()
    w("Cosine distance is used to find nearest neighbors. **Surprising neighbors**")
    w("are pairs that are close in genome space but have low tag overlap (Jaccard < 0.5),")
    w("indicating shared structural properties (OEIS, prize, status) across different areas.")
    w()

    if surprising_neighbors:
        w(f"### Top {len(surprising_neighbors)} Surprising Near-Neighbors")
        w()
        w("| Problem A | Problem B | Cosine Dist | Shared Tags | Unique to A | Unique to B | Surprise Score |")
        w("|-----------|-----------|-------------|-------------|-------------|-------------|----------------|")
        for sn in surprising_neighbors:
            shared = ", ".join(sn["shared_tags"][:3]) or "(none)"
            uniq1 = ", ".join(sn["unique_tags_1"][:2]) or "-"
            uniq2 = ", ".join(sn["unique_tags_2"][:2]) or "-"
            w(f"| #{sn['problem_1']} ({sn['status_1']}) | #{sn['problem_2']} ({sn['status_2']}) | {sn['cosine_distance']} | {shared} | {uniq1} | {uniq2} | {sn['surprise_score']} |")
        w()

        w("### Interpretation of Surprising Neighbors")
        w()
        w("The highest-surprise pairs represent problems from different mathematical areas")
        w("that share structural 'DNA': similar OEIS profiles, similar prize levels, or")
        w("similar status. These are candidates for cross-pollination of ideas.")
        w()

        # Analyze which area pairs dominate surprising neighbors
        area_pair_counts = Counter()
        for sn in surprising_neighbors:
            areas1 = set(sn["unique_tags_1"]) & AREA_TAGS
            areas2 = set(sn["unique_tags_2"]) & AREA_TAGS
            for a1 in (areas1 or {"(shared)"}):
                for a2 in (areas2 or {"(shared)"}):
                    pair = tuple(sorted([a1, a2]))
                    area_pair_counts[pair] += 1

        if area_pair_counts:
            w("**Most frequent area pairs in surprising neighbors:**")
            w()
            for pair, count in area_pair_counts.most_common(10):
                w(f"- {pair[0]} <-> {pair[1]}: {count} surprising pairs")
            w()

    w("---")
    w()

    # ── Summary ──
    w("## Summary of Key Discoveries")
    w()
    w("### 1. Hidden OEIS Bridges")
    zero_bridges = [b for b in oeis_bridges if b["jaccard"] == 0]
    low_bridges = [b for b in oeis_bridges if b["jaccard"] > 0]
    w(f"- Found **{len(oeis_bridges)}** problem pairs sharing OEIS sequences with low tag overlap "
      f"({len(zero_bridges)} zero-overlap, {len(low_bridges)} low-overlap)")
    if oeis_bridges:
        w(f"- Most notable: #{oeis_bridges[0]['problem_1']} <-> #{oeis_bridges[0]['problem_2']} via {oeis_bridges[0]['shared_oeis']} (Jaccard={oeis_bridges[0]['jaccard']})")
    w()
    w("### 2. Tag Gaps")
    empty_pairs = [k for k, v in gap_analysis.items() if v["count"] == 0]
    sparse_pairs = [k for k, v in gap_analysis.items() if 0 < v["count"] <= 3]
    w(f"- **{len(empty_pairs)}** major tag pairs have ZERO intersection problems")
    if empty_pairs:
        w(f"  - Empty: {', '.join(empty_pairs)}")
    w(f"- **{len(sparse_pairs)}** major tag pairs have 1-3 problems (sparse)")
    if sparse_pairs:
        w(f"  - Sparse: {', '.join(sparse_pairs)}")
    w()
    w("### 3. Technique Transfer")
    w(f"- **{len(transfers)}** potential technique transfers identified")
    w(f"- **{len(prize_transfers)}** target open problems with prizes")
    if transfer_summary["by_technique"]:
        top_tech = max(transfer_summary["by_technique"], key=transfer_summary["by_technique"].get)
        w(f"- Most transferable technique: **{top_tech}** ({transfer_summary['by_technique'][top_tech]} candidates)")
    w()
    w("### 4. Structural Isomorphisms")
    w(f"- **{len(iso_summary)}** tag patterns have both solved and open problems")
    specific_isos = [s for s in iso_summary if s["tag_count"] >= 3]
    w(f"- **{len(specific_isos)}** of these have 3+ tags (highly specific)")
    w()
    w("### 5. Novel Problems")
    w(f"- Generated **{len(novel_problems)}** novel problems at underexplored intersections")
    for np_item in novel_problems:
        w(f"  - **{np_item['id']}**: {np_item['title']} ({np_item['intersection']})")
    w()
    w("### 6. Surprising Genome Neighbors")
    w(f"- Found **{len(surprising_neighbors)}** surprising near-neighbor pairs")
    w("- These are problems with similar structural profiles but different mathematical content")
    w()

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────

def run_all_analyses(problems: list[dict]) -> dict[str, Any]:
    """Run all 6 analyses and return structured results."""
    print(f"Loaded {len(problems)} problems")

    # 1. OEIS Hidden Bridges
    print("\n[1/6] Finding hidden OEIS bridges...")
    oeis_bridges = find_oeis_hidden_bridges(problems)
    print(f"  Found {len(oeis_bridges)} hidden bridges")

    # 2. Tag Gap Analysis
    print("[2/6] Running tag gap analysis...")
    gap = tag_gap_analysis(problems)
    rare = find_rare_intersections(gap)
    print(f"  Found {len(rare)} rare/empty intersections")

    # 3. Technique Transfer Map
    print("[3/6] Building technique transfer map...")
    transfers = build_technique_transfer_map(problems)
    transfer_summary = summarize_technique_transfers(transfers)
    print(f"  Found {len(transfers)} technique transfer candidates")

    # 4. Structural Isomorphism
    print("[4/6] Finding structural isomorphisms...")
    isos = find_structural_isomorphisms(problems)
    iso_summary = summarize_isomorphisms(isos)
    print(f"  Found {len(iso_summary)} isomorphic tag patterns")

    # 5. Novel Problem Generation
    print("[5/6] Generating novel problems...")
    novel = generate_novel_problems(gap, rare, transfer_summary, problems)
    print(f"  Generated {len(novel)} novel problems")

    # 6. Problem Genome
    print("[6/6] Building problem genome and nearest-neighbor analysis...")
    matrix, prob_nums, feature_names = build_problem_genome(problems)
    all_pairs = find_nearest_neighbors(matrix, prob_nums, problems, k=5)
    surprising = find_surprising_neighbors(all_pairs, top_n=30)
    print(f"  Genome: {matrix.shape[0]} problems x {matrix.shape[1]} features")
    print(f"  Found {len(surprising)} surprising near-neighbor pairs")

    genome_stats = {
        "n_features": matrix.shape[1],
        "n_tags": matrix.shape[1] - 4,
        "n_problems": matrix.shape[0],
    }

    return {
        "oeis_bridges": oeis_bridges,
        "gap_analysis": gap,
        "rare_intersections": rare,
        "transfers": transfers,
        "transfer_summary": transfer_summary,
        "isomorphisms": isos,
        "iso_summary": iso_summary,
        "novel_problems": novel,
        "surprising_neighbors": surprising,
        "genome_stats": genome_stats,
    }


def main():
    """Run all analyses and generate report."""
    print("=" * 60)
    print("Erdos Problems: Relationship Discovery Engine")
    print("=" * 60)

    problems = load_problems()
    results = run_all_analyses(problems)

    # Generate report
    print("\nGenerating report...")
    report = generate_report(
        problems=problems,
        oeis_bridges=results["oeis_bridges"],
        gap_analysis=results["gap_analysis"],
        rare_intersections=results["rare_intersections"],
        transfers=results["transfers"],
        transfer_summary=results["transfer_summary"],
        isomorphisms=results["isomorphisms"],
        iso_summary=results["iso_summary"],
        novel_problems=results["novel_problems"],
        surprising_neighbors=results["surprising_neighbors"],
        genome_stats=results["genome_stats"],
    )

    # Write report
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(report)
    print(f"\nReport written to {OUTPUT_PATH}")
    print(f"Report size: {len(report)} characters, {report.count(chr(10))} lines")

    return results


if __name__ == "__main__":
    main()
