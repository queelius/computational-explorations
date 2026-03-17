#!/usr/bin/env python3
"""
Technique Transfer — Matching Solved Proof Techniques to Open Problems

Strategy: extract "technique signatures" from solved problems based on
their tags, OEIS sequences, and statement keywords, then find open problems
with similar structural signatures that haven't been attacked with the
most promising technique family.

Key outputs:
- Technique family classification for solved problems
- Transfer recommendations: (open problem, recommended technique, evidence)
- Technique coverage gaps: areas where known methods haven't been tried
- Cross-pollination opportunities between mathematical subfields
"""

import math
import yaml
import re
import numpy as np
from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "technique_transfer_report.md"


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


def _statement_text(p: Dict) -> str:
    stmt = p.get("statement", "") or ""
    if isinstance(stmt, dict):
        stmt = stmt.get("text", "") or ""
    return stmt.lower()


def _statement_words(p: Dict) -> Set[str]:
    text = _statement_text(p)
    words = re.findall(r'[a-z]+', text)
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


# ══════════════════════════════════════════════════════════════════════
# Technique Family Classification
# ══════════════════════════════════════════════════════════════════════

# Technique families and their keyword signatures
TECHNIQUE_FAMILIES = {
    "probabilistic": {
        "keywords": {"random", "probability", "expected", "expectation",
                     "almost", "surely", "random graph", "probabilistic"},
        "tags": {"probability", "random graphs"},
    },
    "algebraic": {
        "keywords": {"polynomial", "ring", "field", "algebraic", "group",
                     "module", "ideal", "galois", "characteristic"},
        "tags": {"algebra", "polynomials"},
    },
    "analytic": {
        "keywords": {"asymptotic", "limit", "density", "logarithm",
                     "integral", "zeta", "sum", "series", "convergence",
                     "divergence", "exponential"},
        "tags": {"analysis", "number theory"},
    },
    "combinatorial": {
        "keywords": {"counting", "bijection", "pigeonhole", "inclusion",
                     "exclusion", "partition", "coloring", "matching",
                     "extremal", "turán", "ramsey"},
        "tags": {"combinatorics", "extremal graph theory", "Ramsey theory"},
    },
    "spectral": {
        "keywords": {"eigenvalue", "spectral", "matrix", "adjacency",
                     "laplacian", "characteristic polynomial"},
        "tags": set(),
    },
    "topological": {
        "keywords": {"topological", "homotopy", "homology", "borsuk",
                     "continuous", "connected", "planarity"},
        "tags": {"topology"},
    },
    "fourier": {
        "keywords": {"fourier", "transform", "frequency", "convolution",
                     "character", "exponential sum"},
        "tags": set(),
    },
    "geometric": {
        "keywords": {"convex", "distance", "point", "line", "plane",
                     "circle", "triangle", "dimension", "lattice",
                     "incidence"},
        "tags": {"geometry", "combinatorial geometry", "convex geometry",
                 "discrete geometry"},
    },
    "sieve": {
        "keywords": {"sieve", "prime", "divisor", "multiplicative",
                     "coprime", "gcd", "euler", "phi", "mobius",
                     "arithmetic function"},
        "tags": {"primes", "number theory"},
    },
    "additive": {
        "keywords": {"sumset", "sum-free", "arithmetic progression",
                     "additive", "sidon", "difference set", "density",
                     "schur"},
        "tags": {"additive combinatorics", "arithmetic progressions",
                 "sidon sets"},
    },
}


def classify_technique(p: Dict) -> Dict[str, float]:
    """
    Score a problem against each technique family.

    Returns dict mapping technique family -> affinity score [0, 1].
    """
    words = _statement_words(p)
    tags = _tags(p)
    text = _statement_text(p)

    scores = {}
    for family, signature in TECHNIQUE_FAMILIES.items():
        kw_score = 0
        for kw in signature["keywords"]:
            if " " in kw:
                # Multi-word keyword: check in full text
                if kw in text:
                    kw_score += 2
            elif kw in words:
                kw_score += 1

        tag_score = len(tags & signature["tags"]) * 3

        raw = kw_score + tag_score
        # Normalize to [0, 1] with soft cap
        scores[family] = 1 - math.exp(-raw / 4.0) if raw > 0 else 0.0

    return scores


def technique_profile(problems: List[Dict]) -> Dict[str, Any]:
    """
    Compute technique family profiles for all solved and open problems.

    Returns summary statistics about technique distribution.
    """
    solved_profiles = {}
    open_profiles = {}

    for p in problems:
        num = _number(p)
        if num <= 0:
            continue
        profile = classify_technique(p)
        if _is_solved(p):
            solved_profiles[num] = profile
        elif _status(p) == "open":
            open_profiles[num] = profile

    # Dominant technique per solved problem
    solved_dominants = Counter()
    for num, profile in solved_profiles.items():
        if max(profile.values()) > 0:
            dominant = max(profile, key=profile.get)
            solved_dominants[dominant] += 1

    open_dominants = Counter()
    for num, profile in open_profiles.items():
        if max(profile.values()) > 0:
            dominant = max(profile, key=profile.get)
            open_dominants[dominant] += 1

    # Technique effectiveness: solve rate per dominant technique
    effectiveness = {}
    for family in TECHNIQUE_FAMILIES:
        n_solved = solved_dominants.get(family, 0)
        n_open = open_dominants.get(family, 0)
        total = n_solved + n_open
        if total > 0:
            effectiveness[family] = {
                "n_solved": n_solved,
                "n_open": n_open,
                "total": total,
                "solve_rate": round(n_solved / total, 3),
            }

    return {
        "n_solved": len(solved_profiles),
        "n_open": len(open_profiles),
        "solved_dominant_techniques": dict(solved_dominants.most_common()),
        "open_dominant_techniques": dict(open_dominants.most_common()),
        "technique_effectiveness": effectiveness,
    }


# ══════════════════════════════════════════════════════════════════════
# Structure Similarity
# ══════════════════════════════════════════════════════════════════════

def _structure_vector(p: Dict) -> np.ndarray:
    """
    Create a fixed-length structure vector for a problem.

    Combines technique scores + tag features + OEIS count.
    """
    profile = classify_technique(p)
    families = sorted(TECHNIQUE_FAMILIES.keys())
    tech_vec = [profile.get(f, 0) for f in families]

    n_tags = len(_tags(p))
    n_oeis = len(_oeis(p))
    has_prize = 1 if p.get("prize") else 0

    return np.array(tech_vec + [n_tags / 5.0, n_oeis / 3.0, has_prize])


def structure_similarity(p1: Dict, p2: Dict) -> float:
    """Cosine similarity between structure vectors."""
    v1 = _structure_vector(p1)
    v2 = _structure_vector(p2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 < 1e-10 or norm2 < 1e-10:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))


# ══════════════════════════════════════════════════════════════════════
# Transfer Recommendations
# ══════════════════════════════════════════════════════════════════════

def transfer_recommendations(problems: List[Dict],
                            top_k: int = 20,
                            min_technique_count: int = 5) -> List[Dict]:
    """
    For each open problem, find solved problems with similar structure
    and recommend the technique that solved the similar problem.

    Score = structure_similarity * technique_confidence * technique_effectiveness

    Requires min_technique_count solved problems per technique family to
    avoid small-sample bias (e.g., topological with n=1).
    """
    prob_map = {_number(p): p for p in problems if _number(p) > 0}

    solved = [(num, p) for num, p in prob_map.items() if _is_solved(p)]
    open_probs = [(num, p) for num, p in prob_map.items() if _status(p) == "open"]

    if not solved or not open_probs:
        return []

    # Precompute structure vectors
    solved_vecs = {num: _structure_vector(p) for num, p in solved}
    open_vecs = {num: _structure_vector(p) for num, p in open_probs}

    # Technique effectiveness for weighting (filter by min count)
    profile = technique_profile(problems)
    effectiveness = {
        fam: stats for fam, stats in profile["technique_effectiveness"].items()
        if stats["total"] >= min_technique_count
    }

    recommendations = []
    seen_evidence = Counter()  # Prevent one evidence problem dominating

    for o_num, o_prob in open_probs:
        o_vec = open_vecs[o_num]
        o_norm = np.linalg.norm(o_vec)
        if o_norm < 1e-10:
            continue

        # Collect top candidates from different techniques
        candidates = []

        for s_num, s_prob in solved:
            s_vec = solved_vecs[s_num]
            s_norm = np.linalg.norm(s_vec)
            if s_norm < 1e-10:
                continue

            sim = float(np.dot(o_vec, s_vec) / (o_norm * s_norm))
            if sim < 0.5:
                continue

            s_profile = classify_technique(s_prob)
            if max(s_profile.values()) == 0:
                continue

            dominant = max(s_profile, key=s_profile.get)
            if dominant not in effectiveness:
                continue

            tech_conf = s_profile[dominant]
            eff = effectiveness[dominant]["solve_rate"]
            score = sim * tech_conf * eff

            candidates.append((score, s_num, dominant, sim))

        if not candidates:
            continue

        # Pick best candidate, preferring diverse evidence
        candidates.sort(key=lambda x: -x[0])
        score, s_num, technique, sim = candidates[0]

        if score > 0.05:
            recommendations.append({
                "open_problem": o_num,
                "recommended_technique": technique,
                "evidence_problem": s_num,
                "similarity": round(sim, 3),
                "score": round(score, 3),
                "open_tags": sorted(_tags(o_prob)),
                "evidence_tags": sorted(_tags(prob_map[s_num])),
            })
            seen_evidence[s_num] += 1

    recommendations.sort(key=lambda x: -x["score"])

    # Diversify: limit any single evidence problem to 3 appearances
    diversified = []
    ev_count = Counter()
    for r in recommendations:
        if ev_count[r["evidence_problem"]] < 3:
            diversified.append(r)
            ev_count[r["evidence_problem"]] += 1
        if len(diversified) >= top_k:
            break

    return diversified


# ══════════════════════════════════════════════════════════════════════
# Technique Coverage Gaps
# ══════════════════════════════════════════════════════════════════════

def technique_gaps(problems: List[Dict]) -> Dict[str, Any]:
    """
    Identify technique coverage gaps: tag-technique combinations where
    solved problems use a technique but open problems with the same tag
    don't have that technique applied.
    """
    solved_tag_tech = defaultdict(set)  # tag -> set of techniques used
    open_tag_tech = defaultdict(set)    # tag -> set of techniques with affinity

    for p in problems:
        num = _number(p)
        if num <= 0:
            continue

        tags = _tags(p)
        profile = classify_technique(p)
        dominant_techs = {f for f, s in profile.items() if s > 0.3}

        if _is_solved(p):
            for tag in tags:
                solved_tag_tech[tag].update(dominant_techs)
        elif _status(p) == "open":
            for tag in tags:
                open_tag_tech[tag].update(dominant_techs)

    gaps = []
    for tag in sorted(set(solved_tag_tech) & set(open_tag_tech)):
        missing = solved_tag_tech[tag] - open_tag_tech[tag]
        if missing:
            gaps.append({
                "tag": tag,
                "techniques_used_in_solved": sorted(solved_tag_tech[tag]),
                "missing_in_open": sorted(missing),
                "n_open_with_tag": sum(
                    1 for p in problems
                    if _status(p) == "open" and tag in _tags(p)
                ),
            })

    gaps.sort(key=lambda x: -x["n_open_with_tag"])
    return {
        "n_gaps": len(gaps),
        "gaps": gaps,
    }


# ══════════════════════════════════════════════════════════════════════
# Cross-Pollination Opportunities
# ══════════════════════════════════════════════════════════════════════

def cross_pollination(problems: List[Dict]) -> Dict[str, Any]:
    """
    Identify cross-pollination opportunities: techniques that have been
    highly effective in one tag family but barely tried in another.
    """
    tag_technique_matrix = defaultdict(lambda: defaultdict(lambda: {"solved": 0, "open": 0}))

    for p in problems:
        num = _number(p)
        if num <= 0:
            continue

        tags = _tags(p)
        profile = classify_technique(p)
        if max(profile.values()) == 0:
            continue
        dominant = max(profile, key=profile.get)

        status = "solved" if _is_solved(p) else "open" if _status(p) == "open" else None
        if status:
            for tag in tags:
                tag_technique_matrix[tag][dominant][status] += 1

    # Find tags with ≥5 problems
    large_tags = [tag for tag in tag_technique_matrix
                  if sum(v["solved"] + v["open"]
                         for v in tag_technique_matrix[tag].values()) >= 5]

    opportunities = []
    for t1 in large_tags:
        for t2 in large_tags:
            if t1 >= t2:
                continue

            # Find techniques that work well in t1 but barely appear in t2
            for tech in TECHNIQUE_FAMILIES:
                s1 = tag_technique_matrix[t1][tech]["solved"]
                o1 = tag_technique_matrix[t1][tech]["open"]
                tot1 = s1 + o1
                s2 = tag_technique_matrix[t2][tech]["solved"]
                o2 = tag_technique_matrix[t2][tech]["open"]
                tot2 = s2 + o2

                if tot1 >= 3 and s1 / tot1 > 0.5 and tot2 <= 1:
                    opportunities.append({
                        "technique": tech,
                        "strong_in": t1,
                        "strong_solve_rate": round(s1 / tot1, 2),
                        "weak_in": t2,
                        "weak_count": tot2,
                        "potential_targets": o2 + sum(
                            1 for p in problems
                            if _status(p) == "open" and t2 in _tags(p)
                            and classify_technique(p).get(tech, 0) < 0.2
                        ),
                    })

    opportunities.sort(key=lambda x: (-x["strong_solve_rate"], -x["potential_targets"]))
    return {
        "n_opportunities": len(opportunities),
        "opportunities": opportunities[:30],
    }


# ══════════════════════════════════════════════════════════════════════
# Technique Co-occurrence
# ══════════════════════════════════════════════════════════════════════

def technique_cooccurrence(problems: List[Dict]) -> Dict[str, Any]:
    """
    Analyze which technique families co-occur in solved problems.

    Problems often require combining techniques (e.g., probabilistic + algebraic).
    """
    pair_counts = Counter()  # (tech1, tech2) -> count in solved
    single_counts = Counter()

    for p in problems:
        if not _is_solved(p) or _number(p) <= 0:
            continue

        profile = classify_technique(p)
        active = sorted(f for f, s in profile.items() if s > 0.3)

        for f in active:
            single_counts[f] += 1
        for i in range(len(active)):
            for j in range(i + 1, len(active)):
                pair_counts[(active[i], active[j])] += 1

    n_solved = sum(1 for p in problems if _is_solved(p) and _number(p) > 0)

    # Compute lift: observed co-occurrence / expected under independence
    pairs = []
    for (t1, t2), count in pair_counts.most_common():
        expected = (single_counts[t1] * single_counts[t2]) / n_solved
        lift = count / expected if expected > 0 else 0
        pairs.append({
            "technique_1": t1,
            "technique_2": t2,
            "co_occurrences": count,
            "expected": round(expected, 1),
            "lift": round(lift, 2),
        })

    # Sort by lift (surprisingness)
    pairs.sort(key=lambda x: -x["lift"])

    return {
        "n_solved_classified": n_solved,
        "technique_counts": dict(single_counts.most_common()),
        "top_pairs_by_lift": pairs[:15],
        "top_pairs_by_count": sorted(pairs, key=lambda x: -x["co_occurrences"])[:15],
    }


# ══════════════════════════════════════════════════════════════════════
# Report
# ══════════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    lines = [
        "# Technique Transfer: Matching Proof Methods to Open Problems",
        "",
    ]

    # Technique profile
    profile = technique_profile(problems)
    lines.append(f"**Solved**: {profile['n_solved']}, **Open**: {profile['n_open']}")
    lines.append("")
    lines.append("## Technique Effectiveness")
    for family, stats in sorted(profile["technique_effectiveness"].items(),
                                 key=lambda x: -x[1]["solve_rate"]):
        lines.append(f"- **{family}**: {stats['solve_rate']:.0%} solve rate "
                     f"({stats['n_solved']} solved / {stats['total']} total)")
    lines.append("")

    # Transfer recommendations
    lines.append("## Transfer Recommendations")
    recs = transfer_recommendations(problems)
    for r in recs[:15]:
        lines.append(f"- **#{r['open_problem']}** ← {r['recommended_technique']} "
                     f"(evidence: #{r['evidence_problem']}, "
                     f"similarity={r['similarity']}, score={r['score']})")
    lines.append("")

    # Gaps
    lines.append("## Technique Coverage Gaps")
    gap_result = technique_gaps(problems)
    lines.append(f"**Total gaps**: {gap_result['n_gaps']}")
    for g in gap_result["gaps"][:10]:
        lines.append(f"- **{g['tag']}**: missing {g['missing_in_open']} "
                     f"({g['n_open_with_tag']} open problems)")
    lines.append("")

    # Cross-pollination
    lines.append("## Cross-Pollination Opportunities")
    cp = cross_pollination(problems)
    for o in cp["opportunities"][:10]:
        lines.append(f"- **{o['technique']}**: {o['strong_solve_rate']:.0%} in "
                     f"'{o['strong_in']}', untried in '{o['weak_in']}' "
                     f"({o['potential_targets']} targets)")
    lines.append("")

    # Co-occurrence
    lines.append("## Technique Co-occurrence (Lift)")
    cooc = technique_cooccurrence(problems)
    for pair in cooc["top_pairs_by_lift"][:10]:
        lines.append(f"- {pair['technique_1']} + {pair['technique_2']}: "
                     f"lift={pair['lift']}, count={pair['co_occurrences']}")
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
