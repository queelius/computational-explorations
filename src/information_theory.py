#!/usr/bin/env python3
"""
information_theory.py — Information-theoretic analysis of the Erdős database.

Applies foundational information theory to discover:
  1. Mutual Information: which features carry information about solvability
  2. Conditional Entropy: how much uncertainty remains after observing each feature
  3. Information Gain: optimal feature ordering for classification trees
  4. Tag Channel Capacity: maximum information flow through each tag
  5. Minimum Description Length: simplest model of problem structure
  6. Redundancy Analysis: which features are redundant vs complementary
  7. Surprise Scoring: which problem outcomes are most information-theoretically surprising

Output: docs/information_theory_report.md
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
REPORT_PATH = ROOT / "docs" / "information_theory_report.md"


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


def _is_formalized(p: Dict) -> bool:
    return p.get("formalized", {}).get("state", "no") == "yes"


# ═══════════════════════════════════════════════════════════════════
# Core Information-Theoretic Functions
# ═══════════════════════════════════════════════════════════════════

def entropy(labels: List) -> float:
    """Shannon entropy H(X) in bits."""
    n = len(labels)
    if n == 0:
        return 0.0
    counts = Counter(labels)
    return -sum((c / n) * math.log2(c / n) for c in counts.values() if c > 0)


def conditional_entropy(labels: List, conditions: List) -> float:
    """Conditional entropy H(Y|X) in bits."""
    n = len(labels)
    if n == 0:
        return 0.0

    # Group labels by condition
    groups = defaultdict(list)
    for label, cond in zip(labels, conditions):
        groups[cond].append(label)

    # H(Y|X) = sum P(x) H(Y|X=x)
    h = 0.0
    for cond, group_labels in groups.items():
        p_x = len(group_labels) / n
        h += p_x * entropy(group_labels)
    return h


def mutual_information(x: List, y: List) -> float:
    """Mutual information I(X;Y) = H(Y) - H(Y|X) in bits."""
    return entropy(y) - conditional_entropy(y, x)


def normalized_mutual_information(x: List, y: List) -> float:
    """NMI = I(X;Y) / sqrt(H(X) * H(Y)), bounded in [0, 1]."""
    mi = mutual_information(x, y)
    hx, hy = entropy(x), entropy(y)
    if hx == 0 or hy == 0:
        return 0.0
    return mi / math.sqrt(hx * hy)


def information_gain(labels: List, feature_values: List) -> float:
    """Information gain = H(Y) - H(Y|X). Same as MI but named for decision trees."""
    return mutual_information(feature_values, labels)


def kl_divergence(p_dist: Dict, q_dist: Dict) -> float:
    """KL divergence D_KL(P || Q) in bits."""
    d = 0.0
    for key in p_dist:
        p = p_dist[key]
        q = q_dist.get(key, 1e-10)
        if p > 0:
            d += p * math.log2(p / q)
    return d


# ═══════════════════════════════════════════════════════════════════
# 1. Feature Mutual Information with Solvability
# ═══════════════════════════════════════════════════════════════════

def feature_mutual_information(problems: List[Dict]) -> Dict[str, Any]:
    """
    Compute mutual information between each feature and solvability.

    This tells us how many bits of information each feature provides
    about whether a problem is solved or open.
    """
    solved_labels = ["solved" if _is_solved(p) else "open" for p in problems]

    # Features to test
    features = {}

    # 1. Each tag (binary)
    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    for tag in all_tags:
        features[f"tag:{tag}"] = [1 if tag in _tags(p) else 0 for p in problems]

    # 2. Formalization
    features["formalized"] = [1 if _is_formalized(p) else 0 for p in problems]

    # 3. Has prize
    features["has_prize"] = [1 if _prize(p) > 0 else 0 for p in problems]

    # 4. Prize bucket
    features["prize_bucket"] = [
        "high" if _prize(p) > 1000 else ("medium" if _prize(p) > 100 else ("low" if _prize(p) > 0 else "none"))
        for p in problems
    ]

    # 5. Tag count
    features["tag_count"] = [len(_tags(p)) for p in problems]

    # 6. OEIS count
    features["oeis_count"] = [
        len([s for s in p.get("oeis", []) if s and s != "A000000" and not s.startswith("A00000")])
        for p in problems
    ]

    # 7. Problem number quartile
    numbers = [_number(p) for p in problems]
    sorted_nums = sorted(numbers)
    q1 = sorted_nums[len(sorted_nums) // 4]
    q2 = sorted_nums[len(sorted_nums) // 2]
    q3 = sorted_nums[3 * len(sorted_nums) // 4]
    features["number_quartile"] = [
        "Q1" if _number(p) <= q1 else ("Q2" if _number(p) <= q2 else ("Q3" if _number(p) <= q3 else "Q4"))
        for p in problems
    ]

    # Compute MI for each
    base_entropy = entropy(solved_labels)
    results = []
    for name, values in features.items():
        mi = mutual_information(values, solved_labels)
        nmi = normalized_mutual_information(values, solved_labels)
        ig = information_gain(solved_labels, values)
        h_cond = conditional_entropy(solved_labels, values)

        results.append({
            "feature": name,
            "mutual_information": round(mi, 6),
            "normalized_mi": round(nmi, 4),
            "information_gain": round(ig, 6),
            "conditional_entropy": round(h_cond, 6),
            "entropy_reduction": round(1 - h_cond / base_entropy, 4) if base_entropy > 0 else 0,
        })

    results.sort(key=lambda x: -x["mutual_information"])

    return {
        "base_entropy": round(base_entropy, 6),
        "features": results,
        "total_features": len(results),
    }


# ═══════════════════════════════════════════════════════════════════
# 2. Tag-Tag Mutual Information
# ═══════════════════════════════════════════════════════════════════

def tag_mutual_information(problems: List[Dict]) -> Dict[str, Any]:
    """
    Compute pairwise mutual information between all tag pairs.

    High MI = tags that co-occur more (or less) than expected.
    This reveals hidden dependencies in the tag system.
    """
    all_tags = sorted(set(t for p in problems for t in _tags(p)))

    tag_vectors = {}
    for tag in all_tags:
        tag_vectors[tag] = [1 if tag in _tags(p) else 0 for p in problems]

    results = []
    for i, t1 in enumerate(all_tags):
        for j, t2 in enumerate(all_tags):
            if i >= j:
                continue
            mi = mutual_information(tag_vectors[t1], tag_vectors[t2])
            nmi = normalized_mutual_information(tag_vectors[t1], tag_vectors[t2])
            if mi > 0.001:  # filter noise
                results.append({
                    "tag_a": t1,
                    "tag_b": t2,
                    "mutual_information": round(mi, 6),
                    "normalized_mi": round(nmi, 4),
                })

    results.sort(key=lambda x: -x["mutual_information"])

    return {
        "tag_pairs": results,
        "total_pairs": len(results),
    }


# ═══════════════════════════════════════════════════════════════════
# 3. Surprise Scoring
# ═══════════════════════════════════════════════════════════════════

def surprise_scores(problems: List[Dict]) -> List[Dict]:
    """
    Score each problem by how "surprising" its outcome is.

    Surprise = -log2(P(outcome | features))

    High surprise = the problem's status is unexpected given its features.
    These are the most interesting problems to investigate.
    """
    all_tags = sorted(set(t for p in problems for t in _tags(p)))

    # Compute conditional probabilities
    # P(solved | tag) for each tag
    tag_solve_prob = {}
    for tag in all_tags:
        tag_problems = [p for p in problems if tag in _tags(p)]
        if not tag_problems:
            tag_solve_prob[tag] = 0.5
            continue
        solved = sum(1 for p in tag_problems if _is_solved(p))
        tag_solve_prob[tag] = solved / len(tag_problems)

    # P(solved | formalized)
    formalized_probs = [p for p in problems if _is_formalized(p)]
    unformalized_probs = [p for p in problems if not _is_formalized(p)]
    p_solved_formalized = sum(1 for p in formalized_probs if _is_solved(p)) / len(formalized_probs) if formalized_probs else 0.5
    p_solved_unformalized = sum(1 for p in unformalized_probs if _is_solved(p)) / len(unformalized_probs) if unformalized_probs else 0.5

    results = []
    for p in problems:
        tags = _tags(p)
        is_solved = _is_solved(p)

        # Estimate P(status | features) using naive Bayes-like approach
        # Average tag-based probability
        if tags:
            tag_prob = np.mean([tag_solve_prob.get(t, 0.5) for t in tags])
        else:
            tag_prob = 0.5

        # Formalization adjustment
        form_prob = p_solved_formalized if _is_formalized(p) else p_solved_unformalized

        # Combined estimate
        p_solved = 0.6 * tag_prob + 0.4 * form_prob
        p_solved = max(0.01, min(0.99, p_solved))  # clamp

        # Surprise
        if is_solved:
            surprise = -math.log2(p_solved)
        else:
            surprise = -math.log2(1 - p_solved)

        results.append({
            "number": _number(p),
            "status": _status(p),
            "tags": sorted(tags),
            "p_estimated": round(p_solved, 3),
            "surprise": round(surprise, 3),
            "direction": "solved_surprisingly" if (is_solved and p_solved < 0.3) else
                         ("open_surprisingly" if (not is_solved and p_solved > 0.7) else "expected"),
        })

    results.sort(key=lambda x: -x["surprise"])
    return results


# ═══════════════════════════════════════════════════════════════════
# 4. Redundancy Analysis
# ═══════════════════════════════════════════════════════════════════

def redundancy_analysis(problems: List[Dict]) -> Dict[str, Any]:
    """
    Identify which features are redundant (carry the same information)
    and which are complementary (carry independent information).

    Uses the data processing inequality: features that are highly
    correlated with each other provide redundant information.
    """
    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    solved_labels = ["solved" if _is_solved(p) else "open" for p in problems]

    # Build feature vectors
    features = {}
    for tag in all_tags:
        features[tag] = [1 if tag in _tags(p) else 0 for p in problems]
    features["formalized"] = [1 if _is_formalized(p) else 0 for p in problems]
    features["has_prize"] = [1 if _prize(p) > 0 else 0 for p in problems]

    # Compute MI with solved for each
    mi_with_solved = {}
    for name, values in features.items():
        mi_with_solved[name] = mutual_information(values, solved_labels)

    # Find redundant pairs (high MI between features, both have MI with solved)
    redundant = []
    feature_names = list(features.keys())
    for i in range(len(feature_names)):
        for j in range(i + 1, len(feature_names)):
            fi, fj = feature_names[i], feature_names[j]
            mi_ij = mutual_information(features[fi], features[fj])
            if mi_ij > 0.01:
                # Redundancy ratio: how much of the weaker signal is already in the stronger?
                min_mi = min(mi_with_solved.get(fi, 0), mi_with_solved.get(fj, 0))
                if min_mi > 0:
                    redundancy_ratio = mi_ij / min_mi
                    redundant.append({
                        "feature_a": fi,
                        "feature_b": fj,
                        "mi_between": round(mi_ij, 6),
                        "redundancy_ratio": round(redundancy_ratio, 3),
                    })

    redundant.sort(key=lambda x: -x["redundancy_ratio"])

    # Find most complementary features
    # Complementary = low MI between features but both have MI with solved
    complementary = []
    for i in range(len(feature_names)):
        for j in range(i + 1, len(feature_names)):
            fi, fj = feature_names[i], feature_names[j]
            mi_ij = mutual_information(features[fi], features[fj])
            mi_fi = mi_with_solved.get(fi, 0)
            mi_fj = mi_with_solved.get(fj, 0)

            if mi_fi > 0.002 and mi_fj > 0.002 and mi_ij < 0.005:
                complementary.append({
                    "feature_a": fi,
                    "feature_b": fj,
                    "mi_a_with_solved": round(mi_fi, 6),
                    "mi_b_with_solved": round(mi_fj, 6),
                    "mi_between": round(mi_ij, 6),
                    "joint_info": round(mi_fi + mi_fj - mi_ij, 6),
                })

    complementary.sort(key=lambda x: -x["joint_info"])

    return {
        "redundant_pairs": redundant[:15],
        "complementary_pairs": complementary[:15],
    }


# ═══════════════════════════════════════════════════════════════════
# 5. Channel Capacity Analysis
# ═══════════════════════════════════════════════════════════════════

def channel_capacity(problems: List[Dict]) -> Dict[str, Any]:
    """
    Treat each tag as a "channel" from problem features to solvability.

    Channel capacity = max MI achievable through this tag's problems.
    Tags with high channel capacity are the most informative for prediction.
    """
    all_tags = sorted(set(t for p in problems for t in _tags(p)))
    solved_labels = ["solved" if _is_solved(p) else "open" for p in problems]

    tag_capacity = []
    for tag in all_tags:
        tag_problems = [p for p in problems if tag in _tags(p)]
        if len(tag_problems) < 5:
            continue

        # Channel: formalization → solvability for this tag's problems
        form_values = [1 if _is_formalized(p) else 0 for p in tag_problems]
        solve_values = ["solved" if _is_solved(p) else "open" for p in tag_problems]

        mi = mutual_information(form_values, solve_values)
        h_solve = entropy(solve_values)

        tag_capacity.append({
            "tag": tag,
            "n_problems": len(tag_problems),
            "channel_mi": round(mi, 6),
            "solve_entropy": round(h_solve, 4),
            "capacity_ratio": round(mi / h_solve, 4) if h_solve > 0 else 0,
        })

    tag_capacity.sort(key=lambda x: -x["channel_mi"])

    return {
        "tag_channels": tag_capacity,
    }


# ═══════════════════════════════════════════════════════════════════
# 6. Optimal Classification Tree (Greedy Information Gain)
# ═══════════════════════════════════════════════════════════════════

def optimal_split_tree(problems: List[Dict], max_depth: int = 4) -> Dict[str, Any]:
    """
    Build a classification tree for solvability using greedy information gain.

    This reveals the optimal sequence of questions to ask about a problem
    to predict whether it's solved.
    """
    all_tags = sorted(set(t for p in problems for t in _tags(p)))

    def build_tree(probs, depth, used_features):
        solved = sum(1 for p in probs if _is_solved(p))
        total = len(probs)
        base_rate = solved / total if total > 0 else 0

        if depth >= max_depth or total < 10:
            return {
                "type": "leaf",
                "n": total,
                "solved_rate": round(base_rate, 3),
                "label": "solved" if base_rate > 0.5 else "open",
            }

        # Find best split
        labels = ["solved" if _is_solved(p) else "open" for p in probs]
        h_base = entropy(labels)
        if h_base < 0.01:
            return {
                "type": "leaf",
                "n": total,
                "solved_rate": round(base_rate, 3),
                "label": "solved" if base_rate > 0.5 else "open",
            }

        best_ig = 0
        best_feature = None
        best_split = None

        # Try each tag as split
        for tag in all_tags:
            feat_name = f"tag:{tag}"
            if feat_name in used_features:
                continue
            values = [1 if tag in _tags(p) else 0 for p in probs]
            ig = information_gain(labels, values)
            if ig > best_ig:
                best_ig = ig
                best_feature = feat_name
                best_split = lambda p, t=tag: t in _tags(p)

        # Try formalization
        if "formalized" not in used_features:
            values = [1 if _is_formalized(p) else 0 for p in probs]
            ig = information_gain(labels, values)
            if ig > best_ig:
                best_ig = ig
                best_feature = "formalized"
                best_split = _is_formalized

        # Try has_prize
        if "has_prize" not in used_features:
            values = [1 if _prize(p) > 0 else 0 for p in probs]
            ig = information_gain(labels, values)
            if ig > best_ig:
                best_ig = ig
                best_feature = "has_prize"
                best_split = lambda p: _prize(p) > 0

        if best_ig < 0.001 or best_feature is None:
            return {
                "type": "leaf",
                "n": total,
                "solved_rate": round(base_rate, 3),
                "label": "solved" if base_rate > 0.5 else "open",
            }

        # Split
        yes_probs = [p for p in probs if best_split(p)]
        no_probs = [p for p in probs if not best_split(p)]

        new_used = used_features | {best_feature}

        return {
            "type": "split",
            "feature": best_feature,
            "info_gain": round(best_ig, 6),
            "n": total,
            "yes": build_tree(yes_probs, depth + 1, new_used),
            "no": build_tree(no_probs, depth + 1, new_used),
        }

    tree = build_tree(problems, 0, set())
    return {"tree": tree}


# ═══════════════════════════════════════════════════════════════════
# 7. Status Distribution Entropy by Tag
# ═══════════════════════════════════════════════════════════════════

def status_entropy_by_tag(problems: List[Dict]) -> List[Dict]:
    """
    For each tag, compute the entropy of status distribution.

    Low entropy = the tag strongly predicts a single outcome (good predictor).
    High entropy = the tag is associated with many different outcomes (poor predictor).
    """
    all_tags = sorted(set(t for p in problems for t in _tags(p)))

    results = []
    for tag in all_tags:
        tag_problems = [p for p in problems if tag in _tags(p)]
        if len(tag_problems) < 3:
            continue

        statuses = [_status(p) for p in tag_problems]
        h = entropy(statuses)
        n_states = len(set(statuses))

        # Max possible entropy for this number of states
        h_max = math.log2(n_states) if n_states > 1 else 0

        results.append({
            "tag": tag,
            "n_problems": len(tag_problems),
            "status_entropy": round(h, 4),
            "n_distinct_statuses": n_states,
            "normalized_entropy": round(h / h_max, 4) if h_max > 0 else 0,
            "most_common_status": Counter(statuses).most_common(1)[0],
        })

    results.sort(key=lambda x: x["status_entropy"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(feature_mi, tag_mi, surprises, redundancy,
                    capacity, tree, status_ent) -> str:
    lines = []
    lines.append("# Information-Theoretic Analysis")
    lines.append("")
    lines.append("Applying information theory to discover which features carry")
    lines.append("the most information about problem solvability.")
    lines.append("")

    # 1. Feature MI
    lines.append("## 1. Feature Mutual Information with Solvability")
    lines.append("")
    lines.append(f"Base entropy of solvability: **{feature_mi['base_entropy']:.4f} bits**")
    lines.append("")
    lines.append("| Feature | MI (bits) | NMI | Entropy Reduction |")
    lines.append("|---------|-----------|-----|-------------------|")
    for f in feature_mi["features"][:20]:
        lines.append(
            f"| {f['feature']} | {f['mutual_information']:.6f} | "
            f"{f['normalized_mi']:.4f} | {f['entropy_reduction']:.1%} |"
        )
    lines.append("")

    # 2. Tag-Tag MI
    lines.append("## 2. Tag-Tag Mutual Information (Strongest Associations)")
    lines.append("")
    lines.append("| Tag A | Tag B | MI (bits) | NMI |")
    lines.append("|-------|-------|-----------|-----|")
    for t in tag_mi["tag_pairs"][:15]:
        lines.append(
            f"| {t['tag_a']} | {t['tag_b']} | "
            f"{t['mutual_information']:.6f} | {t['normalized_mi']:.4f} |"
        )
    lines.append("")

    # 3. Surprise Scoring
    lines.append("## 3. Most Surprising Problem Outcomes")
    lines.append("")
    lines.append("### Surprisingly Solved (solved despite prediction of open)")
    lines.append("")
    solved_surprises = [s for s in surprises if s["direction"] == "solved_surprisingly"][:10]
    for s in solved_surprises:
        lines.append(f"- **#{s['number']}** (surprise={s['surprise']:.2f} bits, P(solved)={s['p_estimated']:.2f}): {', '.join(s['tags'][:3])}")
    lines.append("")

    lines.append("### Surprisingly Open (open despite prediction of solved)")
    lines.append("")
    open_surprises = [s for s in surprises if s["direction"] == "open_surprisingly"][:10]
    for s in open_surprises:
        lines.append(f"- **#{s['number']}** (surprise={s['surprise']:.2f} bits, P(solved)={s['p_estimated']:.2f}): {', '.join(s['tags'][:3])}")
    lines.append("")

    # 4. Redundancy
    lines.append("## 4. Redundancy Analysis")
    lines.append("")
    if redundancy["redundant_pairs"]:
        lines.append("### Most Redundant Feature Pairs")
        for r in redundancy["redundant_pairs"][:10]:
            lines.append(f"- {r['feature_a']} ↔ {r['feature_b']}: MI={r['mi_between']:.4f}, redundancy={r['redundancy_ratio']:.1f}×")
        lines.append("")

    if redundancy["complementary_pairs"]:
        lines.append("### Most Complementary Feature Pairs")
        for c in redundancy["complementary_pairs"][:10]:
            lines.append(f"- {c['feature_a']} + {c['feature_b']}: joint info={c['joint_info']:.4f} bits")
        lines.append("")

    # 5. Channel Capacity
    lines.append("## 5. Tag Channel Capacity")
    lines.append("")
    lines.append("| Tag | MI (bits) | Solve Entropy | Capacity Ratio | Problems |")
    lines.append("|-----|-----------|--------------|----------------|----------|")
    for tc in capacity["tag_channels"][:15]:
        lines.append(
            f"| {tc['tag']} | {tc['channel_mi']:.6f} | "
            f"{tc['solve_entropy']:.4f} | {tc['capacity_ratio']:.2%} | {tc['n_problems']} |"
        )
    lines.append("")

    # 6. Classification Tree
    lines.append("## 6. Optimal Classification Tree")
    lines.append("")
    lines.append("Greedy tree built by maximizing information gain at each split:")
    lines.append("")

    def render_tree(node, indent=0):
        prefix = "  " * indent
        if node["type"] == "leaf":
            lines.append(f"{prefix}→ **{node['label']}** (n={node['n']}, solve rate={node['solved_rate']:.1%})")
        else:
            lines.append(f"{prefix}**Split on {node['feature']}** (IG={node['info_gain']:.4f}, n={node['n']})")
            lines.append(f"{prefix}  YES:")
            render_tree(node["yes"], indent + 2)
            lines.append(f"{prefix}  NO:")
            render_tree(node["no"], indent + 2)

    render_tree(tree["tree"])
    lines.append("")

    # 7. Status Entropy by Tag
    lines.append("## 7. Tag Predictiveness (Status Entropy)")
    lines.append("")
    lines.append("### Most Predictive Tags (lowest entropy)")
    for se in status_ent[:10]:
        mc_status, mc_count = se["most_common_status"]
        lines.append(f"- **{se['tag']}** (H={se['status_entropy']:.3f}): {mc_status} ({mc_count}/{se['n_problems']})")
    lines.append("")

    lines.append("### Least Predictive Tags (highest entropy)")
    for se in status_ent[-5:]:
        mc_status, mc_count = se["most_common_status"]
        lines.append(f"- **{se['tag']}** (H={se['status_entropy']:.3f}): {se['n_distinct_statuses']} distinct statuses")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("INFORMATION-THEORETIC ANALYSIS")
    print("=" * 70)

    problems = load_problems()
    print(f"Loaded {len(problems)} problems")

    print("\n1. Computing feature mutual information...")
    feature_mi = feature_mutual_information(problems)
    top = feature_mi["features"][0]
    print(f"   Most informative: {top['feature']} ({top['mutual_information']:.6f} bits)")

    print("\n2. Computing tag-tag mutual information...")
    tag_mi = tag_mutual_information(problems)
    print(f"   {tag_mi['total_pairs']} tag pairs with MI > 0.001")

    print("\n3. Computing surprise scores...")
    surprises = surprise_scores(problems)
    most_surprised = surprises[0]
    print(f"   Most surprising: #{most_surprised['number']} ({most_surprised['surprise']:.2f} bits)")

    print("\n4. Analyzing redundancy...")
    redundancy = redundancy_analysis(problems)
    print(f"   {len(redundancy['redundant_pairs'])} redundant, {len(redundancy['complementary_pairs'])} complementary pairs")

    print("\n5. Computing channel capacity...")
    capacity = channel_capacity(problems)
    print(f"   {len(capacity['tag_channels'])} tag channels analyzed")

    print("\n6. Building classification tree...")
    tree = optimal_split_tree(problems)
    print(f"   Tree root: {tree['tree'].get('feature', 'leaf')}")

    print("\n7. Computing status entropy by tag...")
    status_ent = status_entropy_by_tag(problems)
    print(f"   {len(status_ent)} tags analyzed")

    print("\nGenerating report...")
    report = generate_report(feature_mi, tag_mi, surprises, redundancy,
                             capacity, tree, status_ent)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"Saved to {REPORT_PATH}")

    print("\n" + "=" * 70)
    print("INFORMATION-THEORETIC ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
