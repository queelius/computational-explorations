#!/usr/bin/env python3
"""
problem_families.py — Structural family detection across Erdős problems.

Groups problems into families using multiple relationship signals:
  - Shared OEIS sequences (strongest signal — same mathematical object)
  - Tag overlap (problems in same mathematical area)
  - Dependency graph proximity (structural neighbors)

For each family, identifies:
  - The "patriarch" (most connected member)
  - The "entry point" (easiest unsolved member)
  - Family solve rate and momentum
  - Cross-domain bridges within the family

Key insight: When a family has mixed solved/open problems, the solved ones
carry technique information that can transfer to the open ones. Families
with high solve rates but remaining open members are the best targets.

Output: docs/problem_families_report.md
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
REPORT_PATH = ROOT / "docs" / "problem_families_report.md"


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


def _oeis(p: Dict) -> Set[str]:
    refs = p.get("oeis", [])
    if isinstance(refs, list):
        return set(refs)
    return set()


def _is_solved(p: Dict) -> bool:
    return _status(p) in ("proved", "disproved", "solved",
                           "proved (Lean)", "disproved (Lean)", "solved (Lean)")


def _is_open(p: Dict) -> bool:
    return _status(p) == "open"


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
# Build Problem Affinity Graph
# ═══════════════════════════════════════════════════════════════════

def build_affinity_graph(problems: List[Dict]) -> Dict[str, Any]:
    """
    Build an undirected weighted affinity graph between problems.

    Edge weights use IDF-weighted OEIS co-occurrence:
    - Shared OEIS sequence: weight = sum of log(N/freq) for each shared sequence
      (rare sequences weigh much more than common ones)
    - Tag Jaccard overlap > 0.5: additional weight 2
    - Only edges with total weight >= 3.0 are kept (strong affinity only)

    Returns dict with:
    - adjacency: {num: [(neighbor, weight)]}
    - n_edges, n_nodes
    - edge_type_counts
    """
    prob_by_num = {_number(p): p for p in problems}
    nums = sorted(prob_by_num.keys())
    n_problems = len(nums)

    # Index: OEIS sequence -> set of problem numbers
    oeis_index = defaultdict(set)
    for p in problems:
        num = _number(p)
        for seq in _oeis(p):
            oeis_index[seq].add(num)

    # Filter garbage OEIS entries
    noise_seqs = {"N/A", "possible", "n/a", "none", "unknown", ""}
    for ns in list(noise_seqs):
        oeis_index.pop(ns, None)

    # IDF weight for each sequence: rare sequences are more informative
    seq_idf = {}
    for seq, members in oeis_index.items():
        freq = len(members)
        if freq >= 2:
            seq_idf[seq] = math.log(n_problems / freq)

    # Accumulate pairwise OEIS affinity
    pair_weight = defaultdict(float)
    edge_counts = Counter()

    for seq, members in oeis_index.items():
        if seq not in seq_idf:
            continue
        idf = seq_idf[seq]
        # Only consider sequences shared by ≤ 100 problems
        if len(members) > 100:
            continue
        members_list = sorted(members)
        for i in range(len(members_list)):
            for j in range(i + 1, len(members_list)):
                pair = (members_list[i], members_list[j])
                pair_weight[pair] += idf

    # Add tag Jaccard bonus for high-overlap pairs
    for i in range(len(nums)):
        tags_i = _tags(prob_by_num[nums[i]])
        if not tags_i:
            continue
        for j in range(i + 1, len(nums)):
            tags_j = _tags(prob_by_num[nums[j]])
            if not tags_j:
                continue
            intersection = len(tags_i & tags_j)
            union = len(tags_i | tags_j)
            if union == 0:
                continue
            jaccard = intersection / union
            if jaccard >= 0.5:
                pair = (nums[i], nums[j])
                # Scale tag weight by Jaccard strength (0.5→2, 1.0→4)
                pair_weight[pair] += 2.0 + 2.0 * (jaccard - 0.5)

    # Build adjacency with minimum weight threshold
    adjacency = defaultdict(list)
    n_edges = 0
    min_edge_weight = 3.0

    for (a, b), w in pair_weight.items():
        if w >= min_edge_weight:
            adjacency[a].append((b, w))
            adjacency[b].append((a, w))
            n_edges += 1
            if w >= 5.0:
                edge_counts["strong_oeis"] += 1
            elif w >= 3.0:
                edge_counts["moderate_affinity"] += 1

    return {
        "adjacency": dict(adjacency),
        "n_nodes": len(nums),
        "n_edges": n_edges,
        "edge_type_counts": dict(edge_counts),
        "prob_by_num": prob_by_num,
    }


# ═══════════════════════════════════════════════════════════════════
# Detect Families — Connected Components with Weight Threshold
# ═══════════════════════════════════════════════════════════════════

def detect_families(problems: List[Dict],
                    graph: Optional[Dict] = None,
                    min_weight: float = 5.0,
                    min_family_size: int = 3) -> List[Dict[str, Any]]:
    """
    Detect problem families using two complementary strategies:

    1. **OEIS families**: Connected components via shared OEIS sequences
       (weight >= min_weight). These are tight families about the same
       mathematical objects.

    2. **Tag-signature families**: Problems with identical tag sets.
       These are broader topic-based groups.

    Families are merged if they overlap, then sorted by size.

    Returns sorted list of families (largest first), each with:
    - members, size, solve_rate, open_count, tags, oeis_count
    - patriarch (most connected member), family_type
    - prize_total
    """
    if graph is None:
        graph = build_affinity_graph(problems)

    prob_by_num = graph["prob_by_num"]
    adj = graph["adjacency"]

    # Strategy 1: OEIS-connected families (strong edges)
    strong_adj = defaultdict(list)
    for src, edges in adj.items():
        for tgt, w in edges:
            if w >= min_weight:
                strong_adj[src].append(tgt)

    visited = set()
    raw_families = []

    all_nums = set()
    for p in problems:
        all_nums.add(_number(p))

    for start in sorted(all_nums):
        if start in visited:
            continue
        if start not in strong_adj:
            visited.add(start)
            continue

        component = []
        queue = [start]
        visited.add(start)
        while queue:
            node = queue.pop(0)
            component.append(node)
            for nbr in strong_adj.get(node, []):
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)

        if len(component) >= min_family_size:
            raw_families.append((sorted(component), "oeis"))

    # Strategy 2: Tag-signature families (identical tag sets)
    tag_sig_groups = defaultdict(list)
    for p in problems:
        tags = tuple(sorted(_tags(p)))
        if tags:
            tag_sig_groups[tags].append(_number(p))

    for tags, members in tag_sig_groups.items():
        if len(members) >= min_family_size:
            raw_families.append((sorted(members), "tag_signature"))

    # Merge overlapping families
    # Use union-find to merge families that share members
    family_parent = list(range(len(raw_families)))

    def find(x):
        while family_parent[x] != x:
            family_parent[x] = family_parent[family_parent[x]]
            x = family_parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            family_parent[ra] = rb

    # Check for overlaps
    num_to_family = defaultdict(list)
    for i, (members, ftype) in enumerate(raw_families):
        for n in members:
            num_to_family[n].append(i)

    for num, fam_indices in num_to_family.items():
        for i in range(len(fam_indices) - 1):
            union(fam_indices[i], fam_indices[i + 1])

    # Collect merged families
    merged = defaultdict(set)
    merged_types = defaultdict(set)
    for i, (members, ftype) in enumerate(raw_families):
        root = find(i)
        merged[root].update(members)
        merged_types[root].add(ftype)

    # Build family records
    families = []
    for root, members_set in merged.items():
        members = sorted(members_set)
        solved = [n for n in members if n in prob_by_num and _is_solved(prob_by_num[n])]
        open_members = [n for n in members if n in prob_by_num and _is_open(prob_by_num[n])]

        all_tags = set()
        all_oeis = set()
        for n in members:
            if n in prob_by_num:
                all_tags.update(_tags(prob_by_num[n]))
                all_oeis.update(_oeis(prob_by_num[n]))

        # Patriarch: highest degree within family
        degree = Counter()
        member_set = set(members)
        for n in members:
            for nbr, w in adj.get(n, []):
                if nbr in member_set:
                    degree[n] += 1
        patriarch = degree.most_common(1)[0][0] if degree else members[0]

        total_prize = sum(_prize(prob_by_num[n]) for n in members if n in prob_by_num)

        ftypes = sorted(merged_types[root])
        family_type = "+".join(ftypes)

        families.append({
            "members": members,
            "size": len(members),
            "solved_count": len(solved),
            "open_count": len(open_members),
            "solve_rate": len(solved) / len(members) if members else 0,
            "tags": sorted(all_tags),
            "oeis_count": len(all_oeis),
            "patriarch": patriarch,
            "patriarch_degree": degree.get(patriarch, 0),
            "prize_total": total_prize,
            "family_type": family_type,
        })

    families.sort(key=lambda f: -f["size"])
    return families


# ═══════════════════════════════════════════════════════════════════
# Family Entry Points — Easiest Open Member
# ═══════════════════════════════════════════════════════════════════

def family_entry_points(problems: List[Dict],
                        families: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
    """
    For each family with open problems, find the best "entry point" —
    the open problem most likely to yield to attack.

    Entry point score based on:
    - High tag solve rate (problems in solvable areas)
    - Many OEIS sequences (more connections = more attack angles)
    - High family solve rate (technique transfer from solved siblings)
    - Prize money (motivation signal, but also difficulty indicator)

    Returns list sorted by entry_score descending.
    """
    if families is None:
        families = detect_families(problems)

    prob_by_num = {_number(p): p for p in problems}

    # Precompute tag solve rates
    tag_solved = Counter()
    tag_total = Counter()
    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _is_solved(p):
                tag_solved[t] += 1
    tag_rate = {t: tag_solved[t] / tag_total[t] for t in tag_total if tag_total[t] > 0}

    results = []
    for family in families:
        if family["open_count"] == 0:
            continue

        open_members = [n for n in family["members"]
                        if n in prob_by_num and _is_open(prob_by_num[n])]

        # Score each open member
        candidates = []
        for num in open_members:
            p = prob_by_num.get(num)
            if not p:
                continue

            tags = _tags(p)
            oeis = _oeis(p)

            # Tag solvability: average tag solve rate
            rates = [tag_rate.get(t, 0.3) for t in tags] if tags else [0.3]
            avg_tag_rate = sum(rates) / len(rates)

            # OEIS richness: more sequences = more attack angles
            oeis_score = min(len(oeis) / 5.0, 1.0)

            # Family solve rate: high rate means techniques are available
            family_rate = family["solve_rate"]

            # Composite entry score
            entry_score = (
                0.35 * avg_tag_rate +
                0.25 * oeis_score +
                0.25 * family_rate +
                0.15 * (1.0 if _prize(p) > 0 else 0.0)
            )

            candidates.append({
                "number": num,
                "entry_score": entry_score,
                "tags": sorted(tags),
                "oeis_count": len(oeis),
                "tag_solve_rate": avg_tag_rate,
                "family_size": family["size"],
                "family_solve_rate": family_rate,
                "family_tags": family["tags"][:5],
                "prize": _prize(p),
            })

        candidates.sort(key=lambda c: -c["entry_score"])
        if candidates:
            results.append(candidates[0])  # Best entry point per family

    results.sort(key=lambda r: -r["entry_score"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Cross-Family Bridges — Problems Linking Different Families
# ═══════════════════════════════════════════════════════════════════

def cross_family_bridges(problems: List[Dict],
                         families: Optional[List[Dict]] = None,
                         graph: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """
    Find problems that bridge two or more families — they have weak edges
    (weight 1) to members of different families. These are potential
    cross-domain breakthrough points.

    Returns list of bridges sorted by number of families connected.
    """
    if graph is None:
        graph = build_affinity_graph(problems)
    if families is None:
        families = detect_families(problems, graph)

    prob_by_num = graph["prob_by_num"]
    adj = graph["adjacency"]

    # Map each problem to its family index (or -1 if none)
    num_to_family = {}
    for i, fam in enumerate(families):
        for num in fam["members"]:
            num_to_family[num] = i

    bridges = []
    for p in problems:
        num = _number(p)
        if num not in adj:
            continue

        # Find which families this problem's neighbors belong to
        neighbor_families = set()
        for nbr, w in adj[num]:
            if nbr in num_to_family:
                fam_idx = num_to_family[nbr]
                neighbor_families.add(fam_idx)

        # Also include own family
        own_family = num_to_family.get(num, -1)
        # External families = families other than own
        external = neighbor_families - {own_family} if own_family >= 0 else neighbor_families

        if len(external) >= 2:
            family_tags = []
            for fi in external:
                family_tags.extend(families[fi]["tags"][:3])

            bridges.append({
                "number": num,
                "families_connected": len(external),
                "own_family": own_family if own_family >= 0 else None,
                "external_families": sorted(external),
                "tags": sorted(_tags(p)),
                "is_open": _is_open(p),
                "cross_tags": sorted(set(family_tags)),
                "prize": _prize(p),
            })

    bridges.sort(key=lambda b: (-b["families_connected"], -b["prize"]))
    return bridges


# ═══════════════════════════════════════════════════════════════════
# Family Momentum — Which Families Are Making Progress?
# ═══════════════════════════════════════════════════════════════════

def family_momentum(problems: List[Dict],
                    families: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
    """
    For each family, compute a "momentum" score based on:
    - What fraction of recently-numbered problems are solved (later problems = recent)
    - How the solve rate changes from early to late members

    Returns list sorted by momentum descending.
    """
    if families is None:
        families = detect_families(problems)

    prob_by_num = {_number(p): p for p in problems}
    results = []

    for family in families:
        members = family["members"]
        if len(members) < 4:
            results.append({
                "family_patriarch": family["patriarch"],
                "family_size": family["size"],
                "momentum": 0.0,
                "early_rate": family["solve_rate"],
                "late_rate": family["solve_rate"],
                "tags": family["tags"][:5],
                "open_count": family["open_count"],
            })
            continue

        # Split into early and late halves by problem number
        mid = len(members) // 2
        early = members[:mid]
        late = members[mid:]

        early_solved = sum(1 for n in early if n in prob_by_num and _is_solved(prob_by_num[n]))
        late_solved = sum(1 for n in late if n in prob_by_num and _is_solved(prob_by_num[n]))

        early_rate = early_solved / len(early) if early else 0
        late_rate = late_solved / len(late) if late else 0

        momentum = late_rate - early_rate

        results.append({
            "family_patriarch": family["patriarch"],
            "family_size": family["size"],
            "momentum": momentum,
            "early_rate": early_rate,
            "late_rate": late_rate,
            "tags": family["tags"][:5],
            "open_count": family["open_count"],
        })

    results.sort(key=lambda r: -r["momentum"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Family Taxonomy — Classify Families by Structure
# ═══════════════════════════════════════════════════════════════════

def family_taxonomy(problems: List[Dict],
                    families: Optional[List[Dict]] = None) -> Dict[str, List[Dict]]:
    """
    Classify families into structural types:
    - "nearly_solved": solve_rate > 0.7 (close to complete)
    - "active": 0.3 < solve_rate <= 0.7 (mix of solved and open)
    - "stalled": solve_rate <= 0.3 and size > 5 (large but unsolved)
    - "emerging": size <= 5 (small, recently forming)
    """
    if families is None:
        families = detect_families(problems)

    taxonomy = {
        "nearly_solved": [],
        "active": [],
        "stalled": [],
        "emerging": [],
    }

    for family in families:
        rate = family["solve_rate"]
        size = family["size"]

        entry = {
            "patriarch": family["patriarch"],
            "size": size,
            "solve_rate": rate,
            "open_count": family["open_count"],
            "tags": family["tags"][:5],
            "prize_total": family["prize_total"],
        }

        if size <= 5:
            taxonomy["emerging"].append(entry)
        elif rate > 0.7:
            taxonomy["nearly_solved"].append(entry)
        elif rate > 0.3:
            taxonomy["active"].append(entry)
        else:
            taxonomy["stalled"].append(entry)

    # Sort each category
    for cat in taxonomy:
        taxonomy[cat].sort(key=lambda x: -x["solve_rate"])

    return taxonomy


# ═══════════════════════════════════════════════════════════════════
# OEIS Family Clusters — Families Connected by Shared Sequences
# ═══════════════════════════════════════════════════════════════════

def oeis_family_clusters(problems: List[Dict]) -> List[Dict[str, Any]]:
    """
    Find clusters of problems connected by shared OEIS sequences.
    These represent problems about the SAME mathematical objects,
    making technique transfer most direct.

    Returns clusters sorted by size, each with the connecting sequences.
    """
    # Build OEIS co-occurrence graph
    oeis_index = defaultdict(set)
    prob_by_num = {_number(p): p for p in problems}

    for p in problems:
        num = _number(p)
        for seq in _oeis(p):
            oeis_index[seq].add(num)

    # Only keep sequences shared by 2+ problems
    shared_seqs = {seq: nums for seq, nums in oeis_index.items() if len(nums) >= 2}

    # Union-find for clustering
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Connect problems sharing sequences
    for seq, nums in shared_seqs.items():
        nums_list = sorted(nums)
        for i in range(len(nums_list) - 1):
            union(nums_list[i], nums_list[i + 1])

    # Collect clusters
    clusters_map = defaultdict(set)
    for seq, nums in shared_seqs.items():
        for n in nums:
            clusters_map[find(n)].add(n)

    # Build result
    results = []
    for root, members in clusters_map.items():
        members_list = sorted(members)
        # Find which sequences connect this cluster
        connecting_seqs = set()
        for seq, nums in shared_seqs.items():
            if nums & members:
                connecting_seqs.add(seq)

        solved = [n for n in members_list if n in prob_by_num and _is_solved(prob_by_num[n])]
        open_members = [n for n in members_list if n in prob_by_num and _is_open(prob_by_num[n])]

        all_tags = set()
        for n in members_list:
            if n in prob_by_num:
                all_tags.update(_tags(prob_by_num[n]))

        results.append({
            "members": members_list,
            "size": len(members_list),
            "connecting_sequences": sorted(connecting_seqs),
            "n_sequences": len(connecting_seqs),
            "solved_count": len(solved),
            "open_count": len(open_members),
            "solve_rate": len(solved) / len(members_list) if members_list else 0,
            "tags": sorted(all_tags),
        })

    results.sort(key=lambda c: -c["size"])
    return results


# ═══════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════

def generate_report(problems: List[Dict]) -> str:
    graph = build_affinity_graph(problems)
    families = detect_families(problems, graph)
    entries = family_entry_points(problems, families)
    bridges = cross_family_bridges(problems, families, graph)
    momentum = family_momentum(problems, families)
    taxonomy = family_taxonomy(problems, families)
    oeis_clusters = oeis_family_clusters(problems)

    lines = ["# Problem Families: Structural Family Detection", ""]
    lines.append(f"Detected **{len(families)} families** from {graph['n_nodes']} problems")
    lines.append(f"using {graph['n_edges']} affinity edges.")
    lines.append("")
    lines.append("Edge types:")
    for etype, count in sorted(graph["edge_type_counts"].items()):
        lines.append(f"- {etype}: {count}")
    lines.append("")

    # Section 1: Largest families
    lines.append("## 1. Largest Problem Families")
    lines.append("")
    lines.append("| Rank | Patriarch | Size | Solved | Open | Rate | Tags | Prize |")
    lines.append("|------|-----------|------|--------|------|------|------|-------|")
    for i, fam in enumerate(families[:15]):
        tags_str = ", ".join(fam["tags"][:3])
        prize_str = f"${fam['prize_total']:.0f}" if fam["prize_total"] > 0 else "-"
        lines.append(f"| {i+1} | #{fam['patriarch']} | {fam['size']} | "
                      f"{fam['solved_count']} | {fam['open_count']} | "
                      f"{fam['solve_rate']:.0%} | {tags_str} | {prize_str} |")
    lines.append("")

    # Section 2: Entry points
    lines.append("## 2. Best Entry Points (Easiest Open Member Per Family)")
    lines.append("")
    lines.append("| Problem | Score | Tag Rate | OEIS | Family Rate | Family Size | Tags |")
    lines.append("|---------|-------|----------|------|-------------|-------------|------|")
    for e in entries[:15]:
        tags_str = ", ".join(e["tags"][:3])
        lines.append(f"| #{e['number']} | {e['entry_score']:.3f} | "
                      f"{e['tag_solve_rate']:.2f} | {e['oeis_count']} | "
                      f"{e['family_solve_rate']:.0%} | {e['family_size']} | {tags_str} |")
    lines.append("")

    # Section 3: Cross-family bridges
    lines.append("## 3. Cross-Family Bridges")
    lines.append("")
    lines.append("Problems connecting multiple families — potential cross-domain breakthroughs.")
    lines.append("")
    lines.append("| Problem | Families | Open? | Tags | Cross Tags |")
    lines.append("|---------|----------|-------|------|------------|")
    for b in bridges[:15]:
        tags_str = ", ".join(b["tags"][:3])
        cross_str = ", ".join(b["cross_tags"][:4])
        open_str = "YES" if b["is_open"] else "no"
        lines.append(f"| #{b['number']} | {b['families_connected']} | "
                      f"{open_str} | {tags_str} | {cross_str} |")
    lines.append("")

    # Section 4: Family momentum
    lines.append("## 4. Family Momentum (Accelerating vs Decelerating)")
    lines.append("")
    accel = [m for m in momentum if m["momentum"] > 0.1]
    decel = [m for m in momentum if m["momentum"] < -0.1]
    lines.append(f"- **Accelerating** (late rate > early rate): {len(accel)} families")
    lines.append(f"- **Decelerating**: {len(decel)} families")
    lines.append("")
    lines.append("### Top Accelerating Families")
    lines.append("| Patriarch | Size | Early Rate | Late Rate | Momentum | Tags |")
    lines.append("|-----------|------|------------|-----------|----------|------|")
    for m in momentum[:10]:
        if m["momentum"] > 0:
            tags_str = ", ".join(m["tags"][:3])
            lines.append(f"| #{m['family_patriarch']} | {m['family_size']} | "
                          f"{m['early_rate']:.0%} | {m['late_rate']:.0%} | "
                          f"{m['momentum']:+.2f} | {tags_str} |")
    lines.append("")

    # Section 5: OEIS clusters
    lines.append("## 5. OEIS-Based Clusters (Same Mathematical Object)")
    lines.append("")
    lines.append(f"**{len(oeis_clusters)} clusters** connected by shared OEIS sequences.")
    lines.append("")
    lines.append("| Rank | Size | Sequences | Solved | Open | Rate | Tags |")
    lines.append("|------|------|-----------|--------|------|------|------|")
    for i, c in enumerate(oeis_clusters[:10]):
        tags_str = ", ".join(c["tags"][:3])
        lines.append(f"| {i+1} | {c['size']} | {c['n_sequences']} | "
                      f"{c['solved_count']} | {c['open_count']} | "
                      f"{c['solve_rate']:.0%} | {tags_str} |")
    lines.append("")

    # Section 6: Taxonomy
    lines.append("## 6. Family Taxonomy")
    lines.append("")
    for cat, label, desc in [
        ("nearly_solved", "Nearly Solved (>70% solved)", "Close to complete — final push needed"),
        ("active", "Active (30-70% solved)", "Good technique availability from solved siblings"),
        ("stalled", "Stalled (≤30% solved, large)", "Need new techniques"),
        ("emerging", "Emerging (≤5 members)", "Newly forming research areas"),
    ]:
        items = taxonomy[cat]
        lines.append(f"### {label}")
        lines.append(f"**{len(items)} families** — {desc}")
        lines.append("")
        if items:
            lines.append("| Patriarch | Size | Rate | Open | Tags | Prize |")
            lines.append("|-----------|------|------|------|------|-------|")
            for item in items[:5]:
                tags_str = ", ".join(item["tags"][:3])
                prize_str = f"${item['prize_total']:.0f}" if item["prize_total"] > 0 else "-"
                lines.append(f"| #{item['patriarch']} | {item['size']} | "
                              f"{item['solve_rate']:.0%} | {item['open_count']} | "
                              f"{tags_str} | {prize_str} |")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    problems = load_problems()
    report = generate_report(problems)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")
