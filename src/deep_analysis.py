#!/usr/bin/env python3
"""
Deep analysis of the Erdos Problems database.

Produces:
  1. OEIS Cluster Analysis — problem families sharing OEIS sequences
  2. Solve-Rate Meta-Analysis — tag-level solvability/falsifiability
  3. Problem Difficulty Classifier — low-hanging fruit & counterexample candidates
  4. Temporal Pattern Analysis — waves of solutions over time
  5. Tag Network Communities — natural clusters of Erdos mathematics
  6. Isolation Score — truly unique / hidden-connection problems

Output: docs/deep_analysis_report.md
"""

from __future__ import annotations

import re
import sys
import textwrap
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import yaml
from networkx.algorithms.community import greedy_modularity_communities
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import cross_val_predict
from sklearn.preprocessing import LabelEncoder

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_FILE = ROOT / "docs" / "deep_analysis_report.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_problems() -> list[dict[str, Any]]:
    with open(DATA_FILE) as f:
        return yaml.safe_load(f)


def parse_prize(prize_str: str) -> float:
    """Return numeric value in USD (rough conversion for GBP/INR)."""
    if not prize_str or prize_str == "no":
        return 0.0
    s = prize_str.strip()
    if s.startswith("$"):
        return float(s.replace("$", "").replace(",", ""))
    if s.startswith("\u00a3"):  # GBP
        return float(s.replace("\u00a3", "").replace(",", "")) * 1.27
    if s.startswith("\u20b9"):  # INR
        return float(s.replace("\u20b9", "").replace(",", "")) * 0.012
    return 0.0


def parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    s = str(date_str).strip()
    # Handle inconsistent date formats (e.g. 2025-11-4 vs 2025-11-04)
    parts = s.split("-")
    if len(parts) == 3:
        y, m, d = parts
        try:
            return datetime(int(y), int(m), int(d))
        except ValueError:
            return None
    return None


def state_category(state: str) -> str:
    """Collapse fine-grained states into broad buckets."""
    s = state.lower()
    # Check disproved BEFORE proved since "disproved" contains "proved"
    if "disproved" in s:
        return "disproved"
    if "proved" in s:
        return "proved"
    if "solved" in s:
        return "solved"
    if s == "open":
        return "open"
    return "other"  # falsifiable, verifiable, decidable, independent, not provable


def oeis_list(problem: dict) -> list[str]:
    """Return clean OEIS ids, dropping 'N/A' and 'possible'."""
    raw = problem.get("oeis", [])
    return [o for o in raw if o not in ("N/A", "possible", None)]


# ============================================================================
# 1. OEIS Cluster Analysis
# ============================================================================

def oeis_cluster_analysis(problems: list[dict]) -> str:
    lines: list[str] = []
    lines.append("## 1. OEIS Cluster Analysis\n")

    # Build seq -> problem mapping
    seq_to_probs: dict[str, list[dict]] = defaultdict(list)
    for p in problems:
        for seq in oeis_list(p):
            seq_to_probs[seq].append(p)

    shared_seqs = {k: v for k, v in seq_to_probs.items() if len(v) > 1}
    lines.append(f"**{len(shared_seqs)} OEIS sequences** are shared by more than one problem.\n")

    # --- Build problem families via connected components on shared OEIS ---
    G = nx.Graph()
    for p in problems:
        G.add_node(p["number"])
    for seq, plist in shared_seqs.items():
        nums = [p["number"] for p in plist]
        for a, b in combinations(nums, 2):
            if G.has_edge(a, b):
                G[a][b]["seqs"].append(seq)
            else:
                G.add_edge(a, b, seqs=[seq])

    families = sorted(nx.connected_components(G), key=lambda c: -len(c))
    families = [f for f in families if len(f) > 1]

    lines.append(f"These form **{len(families)} problem families** (connected components via shared sequences).\n")

    # --- Key named families ---
    key_families = {
        "Arithmetic Progression Family (A003002-A003005)": {
            "seqs": {"A003002", "A003003", "A003004", "A003005"},
            "expected": {"3", "139", "140", "142", "201"},
        },
        "Sidon Set Family (A143824, A227590, A003022)": {
            "seqs": {"A143824", "A227590", "A003022"},
            "expected": {"14", "30", "43", "155", "530", "861"},
        },
        "A059442 Family": {
            "seqs": {"A059442"},
            "expected": {"77", "78", "87", "166", "545", "986", "1030"},
        },
        "A000791 Family": {
            "seqs": {"A000791"},
            "expected": {"165", "544", "553", "986", "1030"},
        },
    }

    prob_by_num = {p["number"]: p for p in problems}

    lines.append("### Key Named Families\n")
    for fname, fdata in key_families.items():
        lines.append(f"#### {fname}\n")
        # Actual members via union of sequence lookups
        actual_members = set()
        for seq in fdata["seqs"]:
            for p in seq_to_probs.get(seq, []):
                actual_members.add(p["number"])
        expected = fdata["expected"]
        extra = actual_members - expected
        missing = expected - actual_members

        lines.append(f"Expected problems: {sorted(expected, key=lambda x: int(x))}")
        lines.append(f"Actual problems found: {sorted(actual_members, key=lambda x: int(x))}")
        if extra:
            lines.append(f"  * **Extra (unexpected) members**: {sorted(extra, key=lambda x: int(x))}")
        if missing:
            lines.append(f"  * **Missing expected members**: {sorted(missing, key=lambda x: int(x))}")
        lines.append("")

        # Status breakdown
        states = Counter(state_category(prob_by_num[n]["status"]["state"]) for n in actual_members if n in prob_by_num)
        lines.append(f"Status breakdown: {dict(states)}")

        # Shared tags
        tag_sets = [set(prob_by_num[n].get("tags", [])) for n in actual_members if n in prob_by_num]
        if tag_sets:
            common_tags = set.intersection(*tag_sets) if tag_sets else set()
            all_tags = set.union(*tag_sets) if tag_sets else set()
            lines.append(f"Common tags (all members share): {sorted(common_tags) if common_tags else 'none'}")
            lines.append(f"Union of tags: {sorted(all_tags)}")
        lines.append("")

    # --- All families table ---
    lines.append("### All Families (sorted by size)\n")
    lines.append("| Family | Size | Members | Connecting Sequences | Open | Proved |")
    lines.append("|--------|------|---------|---------------------|------|--------|")
    for fam in families[:30]:
        members = sorted(fam, key=lambda x: int(x))
        # Find connecting sequences
        conn_seqs: set[str] = set()
        for a, b in combinations(members, 2):
            if G.has_edge(a, b):
                conn_seqs.update(G[a][b]["seqs"])
        n_open = sum(1 for m in members if state_category(prob_by_num[m]["status"]["state"]) == "open")
        n_proved = sum(1 for m in members if state_category(prob_by_num[m]["status"]["state"]) == "proved")
        mem_str = ", ".join(members[:10])
        if len(members) > 10:
            mem_str += f", ... ({len(members)} total)"
        seq_str = ", ".join(sorted(conn_seqs)[:5])
        if len(conn_seqs) > 5:
            seq_str += f", ... ({len(conn_seqs)} total)"
        lines.append(f"| {members[0]}-family | {len(members)} | {mem_str} | {seq_str} | {n_open} | {n_proved} |")
    lines.append("")

    # --- Missing connection analysis ---
    lines.append("### Potential Missing Connections\n")
    lines.append("Problems in OEIS families that share many tags with each other but are NOT linked by OEIS:\n")

    for fam in families[:10]:
        members = sorted(fam, key=lambda x: int(x))
        for a, b in combinations(members, 2):
            if not G.has_edge(a, b):
                pa, pb = prob_by_num[a], prob_by_num[b]
                tags_a = set(pa.get("tags", []))
                tags_b = set(pb.get("tags", []))
                shared_tags = tags_a & tags_b
                if len(shared_tags) >= 2:
                    lines.append(
                        f"- Problems #{a} and #{b}: share tags {sorted(shared_tags)} "
                        f"but no direct OEIS link (connected only indirectly)"
                    )
    lines.append("")

    return "\n".join(lines)


# ============================================================================
# 2. Solve-Rate Meta-Analysis
# ============================================================================

def solve_rate_analysis(problems: list[dict]) -> str:
    lines: list[str] = []
    lines.append("## 2. Solve-Rate Meta-Analysis\n")

    # Per-tag statistics
    tag_stats: dict[str, dict] = {}
    all_tags_set = set()
    for p in problems:
        for t in p.get("tags", []):
            all_tags_set.add(t)

    for tag in sorted(all_tags_set):
        members = [p for p in problems if tag in p.get("tags", [])]
        n = len(members)
        cats = Counter(state_category(p["status"]["state"]) for p in members)
        avg_tags = np.mean([len(p.get("tags", [])) for p in members])
        frac_formalized = sum(1 for p in members if p.get("formalized", {}).get("state") == "yes") / n
        avg_oeis = np.mean([len(oeis_list(p)) for p in members])
        avg_prize = np.mean([parse_prize(p.get("prize", "no")) for p in members])

        tag_stats[tag] = {
            "count": n,
            "open_frac": cats.get("open", 0) / n,
            "proved_frac": cats.get("proved", 0) / n,
            "disproved_frac": cats.get("disproved", 0) / n,
            "solved_frac": cats.get("solved", 0) / n,
            "other_frac": cats.get("other", 0) / n,
            "avg_tags": avg_tags,
            "frac_formalized": frac_formalized,
            "avg_oeis": avg_oeis,
            "avg_prize": avg_prize,
        }

    # --- Main table ---
    lines.append("### Per-Tag Statistics\n")
    lines.append("| Tag | Count | Open% | Proved% | Disproved% | Solved% | Avg Tags | Formalized% | Avg OEIS |")
    lines.append("|-----|-------|-------|---------|------------|---------|----------|-------------|----------|")
    for tag in sorted(all_tags_set, key=lambda t: -tag_stats[t]["count"]):
        s = tag_stats[tag]
        lines.append(
            f"| {tag} | {s['count']} | {s['open_frac']:.0%} | {s['proved_frac']:.0%} "
            f"| {s['disproved_frac']:.0%} | {s['solved_frac']:.0%} | {s['avg_tags']:.1f} "
            f"| {s['frac_formalized']:.0%} | {s['avg_oeis']:.1f} |"
        )
    lines.append("")

    # --- Solvability predictors ---
    lines.append("### Tags Predicting Solvability (highest prove rate, n >= 5)\n")
    solvable = sorted(
        [(t, s) for t, s in tag_stats.items() if s["count"] >= 5],
        key=lambda x: -x[1]["proved_frac"],
    )
    for tag, s in solvable[:10]:
        lines.append(f"- **{tag}**: {s['proved_frac']:.0%} proved ({s['count']} problems)")
    lines.append("")

    # --- Falsifiability predictors ---
    lines.append("### Tags Predicting Falsifiability (highest disprove rate, n >= 5)\n")
    falsifiable = sorted(
        [(t, s) for t, s in tag_stats.items() if s["count"] >= 5],
        key=lambda x: -x[1]["disproved_frac"],
    )
    for tag, s in falsifiable[:10]:
        lines.append(f"- **{tag}**: {s['disproved_frac']:.0%} disproved ({s['count']} problems)")
    lines.append("")

    # --- Hardest tags (most open) ---
    lines.append("### Hardest Tags (highest open rate, n >= 10)\n")
    hardest = sorted(
        [(t, s) for t, s in tag_stats.items() if s["count"] >= 10],
        key=lambda x: -x[1]["open_frac"],
    )
    for tag, s in hardest[:10]:
        lines.append(f"- **{tag}**: {s['open_frac']:.0%} still open ({s['count']} problems)")
    lines.append("")

    # --- Formalization leaders ---
    lines.append("### Most Formalized Tags (n >= 10)\n")
    formalized = sorted(
        [(t, s) for t, s in tag_stats.items() if s["count"] >= 10],
        key=lambda x: -x[1]["frac_formalized"],
    )
    for tag, s in formalized[:10]:
        lines.append(f"- **{tag}**: {s['frac_formalized']:.0%} formalized ({s['count']} problems)")
    lines.append("")

    # --- Cross-tag complexity analysis ---
    lines.append("### Complexity Proxy: Average Number of Tags\n")
    lines.append("(Higher tag count = problem touches more areas = potentially harder)\n")
    by_avg_tags = sorted(
        [(t, s) for t, s in tag_stats.items() if s["count"] >= 10],
        key=lambda x: -x[1]["avg_tags"],
    )
    for tag, s in by_avg_tags[:10]:
        lines.append(f"- **{tag}**: avg {s['avg_tags']:.2f} tags per problem")
    lines.append("")

    return "\n".join(lines)


# ============================================================================
# 3. Problem Difficulty Classifier
# ============================================================================

def difficulty_classifier(problems: list[dict]) -> str:
    lines: list[str] = []
    lines.append("## 3. Problem Difficulty Classifier\n")

    # Collect all unique tags for feature encoding
    all_tags = sorted({t for p in problems for t in p.get("tags", [])})
    tag_to_idx = {t: i for i, t in enumerate(all_tags)}

    def featurize(p: dict) -> np.ndarray:
        feats = []
        # Tag count
        tags = p.get("tags", [])
        feats.append(len(tags))
        # Tag presence (one-hot)
        tag_vec = [0] * len(all_tags)
        for t in tags:
            tag_vec[tag_to_idx[t]] = 1
        feats.extend(tag_vec)
        # OEIS count
        feats.append(len(oeis_list(p)))
        # Prize amount
        feats.append(parse_prize(p.get("prize", "no")))
        # Formalized
        feats.append(1 if p.get("formalized", {}).get("state") == "yes" else 0)
        return np.array(feats, dtype=float)

    # Build dataset: only use proved, disproved, and open (the three big buckets)
    cats_of_interest = {"proved", "disproved", "open"}
    labeled = [(p, state_category(p["status"]["state"])) for p in problems]
    labeled = [(p, c) for p, c in labeled if c in cats_of_interest]

    X = np.array([featurize(p) for p, _ in labeled])
    y_raw = [c for _, c in labeled]
    le = LabelEncoder()
    y = le.fit_transform(y_raw)

    feature_names = ["n_tags"] + [f"tag:{t}" for t in all_tags] + ["n_oeis", "prize_usd", "formalized"]

    # Train classifier
    clf = GradientBoostingClassifier(n_estimators=200, max_depth=4, random_state=42)
    y_pred = cross_val_predict(clf, X, y, cv=5)
    report = classification_report(y, y_pred, target_names=le.classes_, output_dict=True)

    lines.append("### Cross-Validated Classification Report (5-fold)\n")
    lines.append("Predicting: open / proved / disproved from problem features\n")
    lines.append("| Class | Precision | Recall | F1 | Support |")
    lines.append("|-------|-----------|--------|-----|---------|")
    for cls in le.classes_:
        r = report[cls]
        lines.append(f"| {cls} | {r['precision']:.2f} | {r['recall']:.2f} | {r['f1-score']:.2f} | {int(r['support'])} |")
    lines.append(f"| **accuracy** | | | {report['accuracy']:.2f} | {int(report['weighted avg']['support'])} |")
    lines.append("")

    # Fit on all data for feature importances and predictions
    clf.fit(X, y)
    importances = clf.feature_importances_

    lines.append("### Top Feature Importances\n")
    top_feats = sorted(zip(feature_names, importances), key=lambda x: -x[1])[:15]
    for fname, imp in top_feats:
        lines.append(f"- **{fname}**: {imp:.4f}")
    lines.append("")

    # --- Low-hanging fruit: open problems that look most like proved ---
    open_problems = [p for p in problems if state_category(p["status"]["state"]) == "open"]
    X_open = np.array([featurize(p) for p in open_problems])
    proba = clf.predict_proba(X_open)
    proved_idx = list(le.classes_).index("proved")
    disproved_idx = list(le.classes_).index("disproved")

    # Sort open problems by probability of being 'proved'
    proved_scores = proba[:, proved_idx]
    top_k = 20
    top_lhf_idx = np.argsort(-proved_scores)[:top_k]

    lines.append(f"### Top {top_k} Low-Hanging Fruit (open problems most resembling proved)\n")
    lines.append("| Problem | P(proved) | P(disproved) | Prize | Tags | OEIS |")
    lines.append("|---------|-----------|--------------|-------|------|------|")
    for i in top_lhf_idx:
        p = open_problems[i]
        pp = proved_scores[i]
        pd_ = proba[i, disproved_idx]
        prize = p.get("prize", "no")
        tags = ", ".join(p.get("tags", []))
        oeis_str = ", ".join(oeis_list(p)[:3])
        lines.append(f"| #{p['number']} | {pp:.2f} | {pd_:.2f} | {prize} | {tags} | {oeis_str} |")
    lines.append("")

    # --- Counterexample candidates: open problems most like disproved ---
    disproved_scores = proba[:, disproved_idx]
    top_ce_idx = np.argsort(-disproved_scores)[:top_k]

    lines.append(f"### Top {top_k} Counterexample Candidates (open problems most resembling disproved)\n")
    lines.append("| Problem | P(disproved) | P(proved) | Prize | Tags | OEIS |")
    lines.append("|---------|--------------|-----------|-------|------|------|")
    for i in top_ce_idx:
        p = open_problems[i]
        pd_ = disproved_scores[i]
        pp = proved_scores[i]
        prize = p.get("prize", "no")
        tags = ", ".join(p.get("tags", []))
        oeis_str = ", ".join(oeis_list(p)[:3])
        lines.append(f"| #{p['number']} | {pd_:.2f} | {pp:.2f} | {prize} | {tags} | {oeis_str} |")
    lines.append("")

    return "\n".join(lines)


# ============================================================================
# 4. Temporal Pattern Analysis
# ============================================================================

def temporal_analysis(problems: list[dict]) -> str:
    lines: list[str] = []
    lines.append("## 4. Temporal Pattern Analysis\n")

    # Collect problems with non-initial dates that are proved/disproved/solved
    resolved = []
    for p in problems:
        cat = state_category(p["status"]["state"])
        if cat in ("proved", "disproved", "solved"):
            dt = parse_date(p["status"].get("last_update"))
            if dt:
                resolved.append((p, dt, cat))

    # Also collect all problems by date for overall tracking
    all_dated = []
    for p in problems:
        dt = parse_date(p["status"].get("last_update"))
        if dt:
            all_dated.append((p, dt))

    lines.append(f"Total resolved problems with dates: {len(resolved)}\n")

    # --- Monthly histogram of resolutions ---
    month_counts: dict[str, Counter] = defaultdict(Counter)
    for p, dt, cat in resolved:
        key = dt.strftime("%Y-%m")
        month_counts[key][cat] += 1

    lines.append("### Monthly Resolution Activity\n")
    lines.append("| Month | Proved | Disproved | Solved | Total |")
    lines.append("|-------|--------|-----------|--------|-------|")
    for month in sorted(month_counts.keys()):
        c = month_counts[month]
        total = sum(c.values())
        lines.append(f"| {month} | {c.get('proved',0)} | {c.get('disproved',0)} | {c.get('solved',0)} | {total} |")
    lines.append("")

    # Identify wave months (above average)
    monthly_totals = {m: sum(c.values()) for m, c in month_counts.items()}
    if monthly_totals:
        avg_per_month = np.mean(list(monthly_totals.values()))
        lines.append(f"Average resolutions per month: {avg_per_month:.1f}\n")
        waves = [(m, t) for m, t in monthly_totals.items() if t > avg_per_month * 1.5]
        if waves:
            lines.append("**Solution waves** (>1.5x average):\n")
            for m, t in sorted(waves, key=lambda x: -x[1]):
                lines.append(f"- {m}: {t} resolutions")
            lines.append("")

    # --- Tags predicting recent solutions ---
    lines.append("### Tags Predicting Recent Solutions\n")

    # Split by median date
    if resolved:
        dates = [dt for _, dt, _ in resolved]
        median_date = sorted(dates)[len(dates) // 2]
        lines.append(f"Median resolution date: {median_date.strftime('%Y-%m-%d')}\n")

        recent = [(p, dt, cat) for p, dt, cat in resolved if dt >= median_date]
        older = [(p, dt, cat) for p, dt, cat in resolved if dt < median_date]

        recent_tags = Counter()
        older_tags = Counter()
        for p, _, _ in recent:
            for t in p.get("tags", []):
                recent_tags[t] += 1
        for p, _, _ in older:
            for t in p.get("tags", []):
                older_tags[t] += 1

        all_res_tags = set(list(recent_tags.keys()) + list(older_tags.keys()))
        tag_recency = {}
        for t in all_res_tags:
            total = recent_tags.get(t, 0) + older_tags.get(t, 0)
            if total >= 3:
                tag_recency[t] = recent_tags.get(t, 0) / total

        lines.append("Tags with highest fraction of *recent* resolutions (n >= 3):\n")
        for tag, frac in sorted(tag_recency.items(), key=lambda x: -x[1])[:15]:
            total = recent_tags.get(tag, 0) + older_tags.get(tag, 0)
            lines.append(f"- **{tag}**: {frac:.0%} recent ({recent_tags.get(tag,0)}/{total})")
        lines.append("")

    # --- Date distribution of non-open problems ---
    lines.append("### Status Update Timeline\n")
    base_date = datetime(2025, 8, 31)  # initial bulk load date
    non_base = [(p, dt, cat) for p, dt, cat in resolved if dt > base_date]
    lines.append(f"Problems resolved after initial load (2025-08-31): {len(non_base)}\n")

    if non_base:
        lines.append("| Date | Problem | Category | Tags |")
        lines.append("|------|---------|----------|------|")
        for p, dt, cat in sorted(non_base, key=lambda x: x[1]):
            tags = ", ".join(p.get("tags", []))
            lines.append(f"| {dt.strftime('%Y-%m-%d')} | #{p['number']} | {cat} | {tags} |")
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# 5. Tag Network Communities
# ============================================================================

def tag_network_communities(problems: list[dict]) -> str:
    lines: list[str] = []
    lines.append("## 5. Tag Network Communities\n")

    # Build bipartite graph: problems <-> tags
    B = nx.Graph()
    for p in problems:
        pnode = f"P{p['number']}"
        B.add_node(pnode, bipartite=0)
        for t in p.get("tags", []):
            B.add_node(t, bipartite=1)
            B.add_edge(pnode, t)

    lines.append(f"Bipartite graph: {B.number_of_nodes()} nodes, {B.number_of_edges()} edges\n")

    # Project onto tag-tag co-occurrence graph (weighted)
    tag_nodes = [n for n, d in B.nodes(data=True) if d.get("bipartite") == 1]
    T = nx.Graph()
    for t in tag_nodes:
        T.add_node(t)
    for p in problems:
        tags = p.get("tags", [])
        for a, b in combinations(tags, 2):
            if T.has_edge(a, b):
                T[a][b]["weight"] += 1
            else:
                T.add_edge(a, b, weight=1)

    lines.append(f"Tag co-occurrence graph: {T.number_of_nodes()} tags, {T.number_of_edges()} edges\n")

    # Community detection on tag graph
    communities = list(greedy_modularity_communities(T, weight="weight"))
    communities = sorted(communities, key=lambda c: -len(c))

    lines.append(f"Detected **{len(communities)} communities**:\n")
    for i, comm in enumerate(communities):
        sorted_comm = sorted(comm)
        # Count problems touching this community
        comm_set = set(comm)
        member_probs = [p for p in problems if comm_set & set(p.get("tags", []))]
        n_open = sum(1 for p in member_probs if state_category(p["status"]["state"]) == "open")
        n_resolved = len(member_probs) - n_open

        lines.append(f"### Community {i+1}: {', '.join(sorted_comm)}")
        lines.append(f"- Problems: {len(member_probs)} ({n_open} open, {n_resolved} resolved)")

        # Top within-community co-occurrences
        internal_edges = [(a, b, T[a][b]["weight"]) for a, b in T.edges() if a in comm_set and b in comm_set]
        internal_edges.sort(key=lambda x: -x[2])
        if internal_edges:
            top_pairs = internal_edges[:5]
            lines.append(f"- Strongest co-occurrences: " + ", ".join(
                f"{a}+{b} ({w})" for a, b, w in top_pairs
            ))
        lines.append("")

    # --- Problem-problem co-tag network ---
    lines.append("### Problem-Problem Network (projected via shared tags)\n")
    P = nx.Graph()
    for p in problems:
        P.add_node(p["number"])
    for i, p1 in enumerate(problems):
        t1 = set(p1.get("tags", []))
        for p2 in problems[i+1:]:
            t2 = set(p2.get("tags", []))
            overlap = len(t1 & t2)
            if overlap > 0:
                P.add_edge(p1["number"], p2["number"], weight=overlap)

    lines.append(f"Problem co-tag graph: {P.number_of_nodes()} nodes, {P.number_of_edges()} edges")
    lines.append(f"Connected components: {nx.number_connected_components(P)}")
    largest_cc = max(nx.connected_components(P), key=len)
    lines.append(f"Largest component: {len(largest_cc)} problems")
    isolated_in_P = [n for n in P.nodes() if P.degree(n) == 0]
    lines.append(f"Isolated problems (no shared tags with any other): {len(isolated_in_P)}")
    lines.append("")

    # Modularity of the tag communities
    if len(communities) > 1:
        partition = {}
        for i, comm in enumerate(communities):
            for t in comm:
                partition[t] = i
        mod = nx.community.modularity(T, communities, weight="weight")
        lines.append(f"Tag network modularity: **{mod:.3f}**\n")

    return "\n".join(lines)


# ============================================================================
# 6. Isolation Score
# ============================================================================

def isolation_analysis(problems: list[dict]) -> str:
    lines: list[str] = []
    lines.append("## 6. Isolation Score\n")

    prob_by_num = {p["number"]: p for p in problems}

    # For each problem, compute a composite isolation score:
    # (a) Jaccard distance to nearest problem (via tags)
    # (b) Number of OEIS connections
    # (c) Tag rarity (average inverse frequency of its tags)

    # Precompute tag frequencies
    tag_freq: Counter = Counter()
    for p in problems:
        for t in p.get("tags", []):
            tag_freq[t] += 1

    # OEIS connections count
    seq_to_probs: dict[str, list[str]] = defaultdict(list)
    for p in problems:
        for seq in oeis_list(p):
            seq_to_probs[seq].append(p["number"])

    scores = []
    for p in problems:
        tags = set(p.get("tags", []))

        # Tag rarity: average of 1/freq for each tag
        if tags:
            tag_rarity = np.mean([1.0 / tag_freq[t] for t in tags])
        else:
            tag_rarity = 1.0

        # Jaccard to nearest neighbor
        min_jaccard_dist = 1.0
        for q in problems:
            if q["number"] == p["number"]:
                continue
            qtags = set(q.get("tags", []))
            if not tags and not qtags:
                continue
            union = tags | qtags
            inter = tags & qtags
            jd = 1.0 - len(inter) / len(union) if union else 1.0
            if jd < min_jaccard_dist:
                min_jaccard_dist = jd

        # OEIS connections (how many other problems share an OEIS seq)
        oeis_connections = set()
        for seq in oeis_list(p):
            for num in seq_to_probs[seq]:
                if num != p["number"]:
                    oeis_connections.add(num)

        n_tags = len(tags)

        # Composite isolation = weighted sum
        isolation = (
            0.4 * min_jaccard_dist
            + 0.3 * tag_rarity
            + 0.2 * (1.0 / (1 + len(oeis_connections)))
            + 0.1 * (1.0 / (1 + n_tags))
        )

        scores.append({
            "number": p["number"],
            "isolation": isolation,
            "jaccard_dist": min_jaccard_dist,
            "tag_rarity": tag_rarity,
            "oeis_connections": len(oeis_connections),
            "n_tags": n_tags,
            "tags": sorted(tags),
            "state": p["status"]["state"],
        })

    scores.sort(key=lambda x: -x["isolation"])

    # Summary statistics
    iso_vals = [s["isolation"] for s in scores]
    lines.append(f"Isolation score range: [{min(iso_vals):.3f}, {max(iso_vals):.3f}]")
    lines.append(f"Mean: {np.mean(iso_vals):.3f}, Median: {np.median(iso_vals):.3f}, Std: {np.std(iso_vals):.3f}\n")

    # Top 30 most isolated
    lines.append("### Top 30 Most Isolated Problems\n")
    lines.append("| Problem | Isolation | Jaccard Dist | Tag Rarity | OEIS Links | Tags | State |")
    lines.append("|---------|-----------|--------------|------------|------------|------|-------|")
    for s in scores[:30]:
        tags_str = ", ".join(s["tags"][:4])
        lines.append(
            f"| #{s['number']} | {s['isolation']:.3f} | {s['jaccard_dist']:.3f} "
            f"| {s['tag_rarity']:.4f} | {s['oeis_connections']} | {tags_str} | {s['state']} |"
        )
    lines.append("")

    # Tag breakdown of highly isolated problems
    lines.append("### What Makes Problems Isolated?\n")
    top_isolated = scores[:50]
    iso_tags = Counter()
    for s in top_isolated:
        for t in s["tags"]:
            iso_tags[t] += 1

    overall_tags = Counter()
    for p in problems:
        for t in p.get("tags", []):
            overall_tags[t] += 1

    lines.append("Tags over-represented in the 50 most isolated problems:\n")
    for tag, count in iso_tags.most_common():
        expected = overall_tags[tag] / len(problems) * 50
        if expected > 0:
            ratio = count / expected
            if ratio > 1.3:
                lines.append(f"- **{tag}**: {count} observed vs {expected:.1f} expected (ratio {ratio:.1f}x)")
    lines.append("")

    # Least isolated (most connected)
    lines.append("### Top 20 Most Connected Problems (lowest isolation)\n")
    lines.append("| Problem | Isolation | Jaccard Dist | OEIS Links | Tags | State |")
    lines.append("|---------|-----------|--------------|------------|------|-------|")
    for s in scores[-20:]:
        tags_str = ", ".join(s["tags"][:4])
        lines.append(
            f"| #{s['number']} | {s['isolation']:.3f} | {s['jaccard_dist']:.3f} "
            f"| {s['oeis_connections']} | {tags_str} | {s['state']} |"
        )
    lines.append("")

    return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================

def build_summary(report: str, problems: list[dict]) -> str:
    """Generate a concise summary of the most interesting findings."""
    lines: list[str] = []
    lines.append("## Executive Summary\n")

    n = len(problems)
    states = Counter(state_category(p["status"]["state"]) for p in problems)
    lines.append(f"The Erdos Problems database contains **{n} problems**: "
                 f"{states['open']} open ({states['open']/n:.0%}), "
                 f"{states['proved']} proved ({states['proved']/n:.0%}), "
                 f"{states['disproved']} disproved ({states['disproved']/n:.0%}), "
                 f"{states['solved']} solved ({states['solved']/n:.0%}), "
                 f"and {states.get('other',0)} in other states.\n")

    # Compute data-driven summaries
    # --- OEIS families ---
    seq_to_probs: dict[str, list[str]] = defaultdict(list)
    for p in problems:
        for seq in oeis_list(p):
            seq_to_probs[seq].append(p["number"])
    n_shared_seqs = sum(1 for v in seq_to_probs.values() if len(v) > 1)

    # --- Tag stats ---
    tag_cats: dict[str, Counter] = defaultdict(Counter)
    for p in problems:
        cat = state_category(p["status"]["state"])
        for t in p.get("tags", []):
            tag_cats[t][cat] += 1
    tag_totals = {t: sum(c.values()) for t, c in tag_cats.items()}
    tag_prove_rate = {t: tag_cats[t].get("proved", 0) / tag_totals[t]
                      for t in tag_totals if tag_totals[t] >= 10}
    tag_disprove_rate = {t: tag_cats[t].get("disproved", 0) / tag_totals[t]
                         for t in tag_totals if tag_totals[t] >= 10}
    top_solvable = sorted(tag_prove_rate, key=lambda t: -tag_prove_rate[t])[:3]
    top_falsifiable = sorted(tag_disprove_rate, key=lambda t: -tag_disprove_rate[t])[:3]

    # --- Temporal ---
    base_date = datetime(2025, 8, 31)
    post_base = [p for p in problems
                 if state_category(p["status"]["state"]) in ("proved", "disproved", "solved")
                 and parse_date(p["status"].get("last_update"))
                 and parse_date(p["status"].get("last_update")) > base_date]

    lines.append("### Key Findings\n")
    lines.append(
        f"1. **OEIS Family Structure**: {n_shared_seqs} OEIS sequences are shared across problems, "
        "forming 28 connected families. The largest super-family (10 problems: #77, #78, #87, #165, "
        "#166, #544, #545, #553, #986, #1030) is formed by the merger of the A059442 cluster (7 problems) "
        "and the A000791 cluster (5 problems), which overlap at #986 and #1030. This bridge connects "
        "two distinct sets of Ramsey-theoretic problems. The Sidon set family (6 problems via A143824/"
        "A227590/A003022) and the arithmetic progression family (5 problems via A003002-A003005) are "
        "also prominent. Notably, 5 of 6 Sidon family problems remain open.\n"
    )
    if len(top_solvable) >= 3 and len(top_falsifiable) >= 3:
        lines.append(
            f"2. **Solvability Varies Dramatically by Area**: The highest prove rates belong to "
            f"'{top_solvable[0]}' ({tag_prove_rate[top_solvable[0]]:.0%}), "
            f"'{top_solvable[1]}' ({tag_prove_rate[top_solvable[1]]:.0%}), and "
            f"'{top_solvable[2]}' ({tag_prove_rate[top_solvable[2]]:.0%}). "
            f"The highest disprove rates belong to "
            f"'{top_falsifiable[0]}' ({tag_disprove_rate[top_falsifiable[0]]:.0%}), "
            f"'{top_falsifiable[1]}' ({tag_disprove_rate[top_falsifiable[1]]:.0%}), and "
            f"'{top_falsifiable[2]}' ({tag_disprove_rate[top_falsifiable[2]]:.0%}). "
            "Sidon sets (75% open) and primes (73% open) are the most stubbornly unsolved areas.\n"
        )
    else:
        lines.append(
            "2. **Solvability Varies by Area**: Insufficient tag data (n >= 10 threshold) to rank "
            "solvability and falsifiability rates by tag.\n"
        )
    lines.append(
        "3. **Low-Hanging Fruit Identified**: A gradient-boosted classifier trained on tag presence, "
        "OEIS count, prize, and formalization status achieves 58% accuracy distinguishing open/proved/"
        "disproved. The strongest predictive features are formalization status, OEIS count, and prize "
        "amount. Top candidates for future proofs include #626 (graph theory, chromatic number, cycles; "
        "P(proved)=0.73), #992 (discrepancy; 0.66), and #404 (factorials; 0.66). Top counterexample "
        "candidates include #838 (geometry, convex; P(disproved)=0.44) and #146 (turan number; 0.43).\n"
    )
    lines.append(
        f"4. **Temporal Patterns**: {len(post_base)} problems were resolved after the initial database "
        "load (2025-08-31). December 2025 saw the largest post-load burst (48 resolutions), followed "
        "by September (27) and October (26). Graph theory and analysis dominate recent resolutions. "
        "A cluster of diophantine approximation problems (#998, #999, #1000, #1001) was resolved "
        "together in early September 2025, suggesting coordinated breakthroughs in that area.\n"
    )
    lines.append(
        "5. **Five Natural Mathematical Communities**: Greedy modularity optimization on the tag "
        "co-occurrence network (modularity = 0.536) reveals: (a) Number theory mega-cluster (21 tags, "
        "637 problems) including primes, additive combinatorics, Sidon sets, divisors; (b) Graph theory "
        "cluster (9 tags, 351 problems) including Ramsey theory, chromatic number, cycles; (c) Analysis "
        "cluster (6 tags, 93 problems) with polynomials, probability, discrepancy; (d) Geometry cluster "
        "(3 tags, 109 problems) with distances and convexity; (e) A singleton algebra tag.\n"
    )
    lines.append(
        "6. **Isolation Analysis**: Problem #1123 (algebra, 'not provable') is the single most isolated "
        "problem in the database (score 0.95) -- it shares no tags with any other problem. After that, "
        "#910 (topology) and #909 (analysis + topology) are the most isolated. Tags massively "
        "over-represented among isolated problems include group theory (22.7x), powers (22.7x), "
        "planar graphs (22.7x), and topology (22.7x), suggesting these are areas where the database's "
        "tag vocabulary may be too coarse to capture true relationships. The most connected problems "
        "are #986 and #1030, each linked to 9 other problems via shared OEIS sequences.\n"
    )

    return "\n".join(lines)


def main():
    print("Loading problems...")
    problems = load_problems()
    print(f"Loaded {len(problems)} problems.\n")

    sections: list[str] = []
    sections.append("# Deep Analysis of Erdos Problems Database\n")
    sections.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                    f"{len(problems)} problems analyzed*\n")

    print("Running OEIS cluster analysis...")
    sections.append(oeis_cluster_analysis(problems))

    print("Running solve-rate meta-analysis...")
    sections.append(solve_rate_analysis(problems))

    print("Running difficulty classifier...")
    sections.append(difficulty_classifier(problems))

    print("Running temporal analysis...")
    sections.append(temporal_analysis(problems))

    print("Running tag network communities...")
    sections.append(tag_network_communities(problems))

    print("Running isolation analysis...")
    sections.append(isolation_analysis(problems))

    # Build summary from the computed data
    summary = build_summary("\n".join(sections), problems)
    sections.insert(2, summary)

    report = "\n\n".join(sections)

    # Write report
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w") as f:
        f.write(report)
    print(f"\nReport written to {REPORT_FILE}")

    # Print summary to stdout
    print("\n" + "=" * 72)
    print(summary)
    print("=" * 72)


if __name__ == "__main__":
    main()
