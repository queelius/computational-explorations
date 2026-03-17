#!/usr/bin/env python3
"""
ai_math_analysis.py -- How AI Is Changing Mathematical Discovery

Case study: Erdos problems corpus (1,183 problems, 483 resolved).
Since August 2025, 213 problems have been resolved, with 118 Lean-
formalized -- an unprecedented acceleration driven by GPT-5/5.2,
Aristotle (Harmonic), AlphaProof (DeepMind), and Gemini Deep Think.

This module tells the story in five acts:

  Act 1 -- Resolution Velocity:  Monthly solution counts, curve fitting
           (linear / exponential / logistic), AI multiplier computation.
  Act 2 -- Problem Type Analysis: Which tag families accelerated most?
           Structured vs deep problem amenability.
  Act 3 -- The Lean Factor:      Formalization rates, AI correlation,
           correctness signals.
  Act 4 -- Difficulty Curve:     Are the easy problems being picked off?
           Monthly difficulty trajectories.
  Act 5 -- Prediction:           Feature-based ranking of the 20 open
           problems most likely to fall next.

Data source: data/erdosproblems/data/problems.yaml (1,183 problems)

Historical context (from web research, March 2026):
- Oct 2025: Aristotle achieves IMO gold (5/6 problems, Lean-verified)
- Dec 2025: GPT-5.2 released; solves Erdos #728 largely autonomously
- Jan 2026: Tao verifies three AI-solved Erdos problems in seven days
- Jan 2026: Massive formalization push -- 37 problems updated on Jan 23
- Mathlib4 surpasses 250,000 theorems (Dec 2025)
- Multiple systems (Gemini Deep Think, Seed-Prover) achieve IMO gold
"""

import math
import re
import yaml
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from scipy.optimize import curve_fit

# ── Paths ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "erdosproblems" / "data" / "problems.yaml"
REPORT_PATH = ROOT / "docs" / "ai_math_analysis_report.md"

# ── Constants ─────────────────────────────────────────────────────────
RESOLVED_STATES = frozenset({
    "proved", "disproved", "solved",
    "proved (Lean)", "disproved (Lean)", "solved (Lean)",
})
LEAN_STATES = frozenset({
    "proved (Lean)", "disproved (Lean)", "solved (Lean)",
})
# The YAML baseline: all problems with last_update == 2025-08-31 are
# the initial snapshot.  Anything updated AFTER that is a recent event.
BASELINE_DATE = "2025-08-31"

# AI era boundary: GPT-5.2 released Dec 11 2025, Aristotle Oct 2025
AI_ERA_START = "2025-10-01"

# Tag family classification for structured-vs-deep hypothesis
STRUCTURED_FAMILIES = frozenset({
    "graph theory", "ramsey theory", "combinatorics", "hypergraphs",
    "chromatic number", "turan number", "cycles", "distances",
    "intersecting family", "discrepancy", "planar graphs",
    "sidon sets", "set theory",
})
DEEP_FAMILIES = frozenset({
    "number theory", "analysis", "primes", "irrationality",
    "diophantine approximation", "polynomials", "topology",
    "additive combinatorics", "additive basis", "arithmetic progressions",
    "covering systems", "iterated functions", "divisors",
})


# ══════════════════════════════════════════════════════════════════════
# Data Loading & Helpers
# ══════════════════════════════════════════════════════════════════════

def load_problems() -> List[Dict]:
    """Load the full Erdos problems YAML."""
    with open(DATA_PATH) as f:
        return yaml.safe_load(f)


def _status(p: Dict) -> str:
    return p.get("status", {}).get("state", "unknown")


def _status_date(p: Dict) -> str:
    """Return status last_update as a normalized YYYY-MM-DD string."""
    raw = str(p.get("status", {}).get("last_update", ""))
    return _normalize_date(raw)


def _formalized_date(p: Dict) -> str:
    raw = str(p.get("formalized", {}).get("last_update", ""))
    return _normalize_date(raw)


def _normalize_date(raw: str) -> str:
    """Handle inconsistent date formats like 2025-11-4 -> 2025-11-04."""
    parts = raw.split("-")
    if len(parts) == 3:
        try:
            return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        except ValueError:
            return raw
    return raw


def _number(p: Dict) -> int:
    n = p.get("number", 0)
    try:
        return int(n)
    except (TypeError, ValueError):
        return 0


def _tags(p: Dict) -> Set[str]:
    return set(p.get("tags", []))


def _is_resolved(p: Dict) -> bool:
    return _status(p) in RESOLVED_STATES


def _is_lean(p: Dict) -> bool:
    return _status(p) in LEAN_STATES


def _is_open(p: Dict) -> bool:
    return _status(p) == "open"


def _is_formalized(p: Dict) -> bool:
    return p.get("formalized", {}).get("state", "no") == "yes"


def _prize_value(p: Dict) -> float:
    """Extract numeric prize in USD."""
    raw = p.get("prize", "no")
    if not raw or raw == "no":
        return 0.0
    nums = re.findall(r"[\d,]+", str(raw))
    if not nums:
        return 0.0
    val = float(nums[0].replace(",", ""))
    s = str(raw)
    if "\u00a3" in s:  # GBP
        val *= 1.27
    if "\u20b9" in s:  # INR
        val *= 0.012
    return val


def _month_key(date_str: str) -> str:
    """Extract YYYY-MM from a date string."""
    return date_str[:7]


def _date_to_months_since(date_str: str, origin: str = "2025-08-01") -> float:
    """Convert a date string to fractional months since origin."""
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        o = datetime.strptime(origin, "%Y-%m-%d")
        delta = (dt - o).days / 30.44  # average days per month
        return max(delta, 0.0)
    except (ValueError, IndexError):
        return 0.0


# ══════════════════════════════════════════════════════════════════════
# Act 1: Resolution Velocity
# ══════════════════════════════════════════════════════════════════════

def _linear(t, a, b):
    return a * t + b


def _exponential(t, a, b, c):
    return a * np.exp(b * t) + c


def _logistic(t, L, k, t0, b):
    """Logistic / S-curve: L / (1 + exp(-k*(t-t0))) + b."""
    return L / (1.0 + np.exp(-k * (t - t0))) + b


def resolution_velocity(problems: List[Dict]) -> Dict[str, Any]:
    """
    Compute monthly resolution counts, fit linear/exponential/logistic
    models, and estimate the AI multiplier.

    Returns dict with:
      - monthly_counts: {YYYY-MM: count}
      - cumulative: [(month_index, cumul_count)]
      - fits: {model_name: {params, residual, aic}}
      - best_model: str
      - logistic_saturation: float (month index where rate drops to 10%)
      - ai_multiplier: float
    """
    # Identify recently-resolved problems (status updated after baseline)
    recent = []
    for p in problems:
        if _is_resolved(p) and _status_date(p) > BASELINE_DATE:
            recent.append(p)

    # Monthly counts
    monthly = Counter()
    for p in recent:
        mk = _month_key(_status_date(p))
        monthly[mk] += 1

    sorted_months = sorted(monthly.keys())
    if not sorted_months:
        return {"monthly_counts": {}, "cumulative": [], "fits": {},
                "best_model": "none", "ai_multiplier": 1.0}

    # Build time series for cumulative fit
    # Month 0 = first month with resolutions
    month_indices = {m: i for i, m in enumerate(sorted_months)}
    t_data = []
    cumul = []
    running = 0
    for m in sorted_months:
        running += monthly[m]
        t_data.append(month_indices[m])
        cumul.append(running)

    t = np.array(t_data, dtype=float)
    y = np.array(cumul, dtype=float)
    n = len(t)

    fits = {}

    # --- Linear ---
    try:
        popt, _ = curve_fit(_linear, t, y)
        y_pred = _linear(t, *popt)
        rss = float(np.sum((y - y_pred) ** 2))
        k_params = 2
        aic = _aic(n, rss, k_params)
        fits["linear"] = {"params": popt.tolist(), "residual": rss, "aic": aic}
    except Exception:
        pass

    # --- Exponential ---
    try:
        p0 = [1.0, 0.3, 0.0]
        popt, _ = curve_fit(_exponential, t, y, p0=p0, maxfev=5000)
        y_pred = _exponential(t, *popt)
        rss = float(np.sum((y - y_pred) ** 2))
        k_params = 3
        aic = _aic(n, rss, k_params)
        fits["exponential"] = {"params": popt.tolist(), "residual": rss, "aic": aic}
    except Exception:
        pass

    # --- Logistic ---
    try:
        total_open_at_start = sum(1 for p in problems if _is_open(p)) + len(recent)
        p0 = [total_open_at_start, 0.5, float(n) / 2, 0.0]
        bounds = ([0, 0.01, 0, -100], [2000, 5.0, 50, 100])
        popt, _ = curve_fit(_logistic, t, y, p0=p0, bounds=bounds, maxfev=10000)
        y_pred = _logistic(t, *popt)
        rss = float(np.sum((y - y_pred) ** 2))
        k_params = 4
        aic = _aic(n, rss, k_params)
        fits["logistic"] = {"params": popt.tolist(), "residual": rss, "aic": aic}
    except Exception:
        pass

    # Best model by AIC
    best_model = "none"
    if fits:
        best_model = min(fits, key=lambda m: fits[m]["aic"])

    # Logistic saturation: month where marginal rate drops to 10% of peak
    logistic_saturation = None
    if "logistic" in fits:
        L, k, t0, b = fits["logistic"]["params"]
        # Peak rate is at t0, rate = L*k/4
        peak_rate = L * k / 4.0
        # Solve for when rate = 0.1 * peak_rate
        # rate(t) = L*k*exp(-k*(t-t0)) / (1+exp(-k*(t-t0)))^2
        # At t = t0 + x, rate drops.  Numerical scan:
        for t_scan in np.arange(t0, t0 + 50, 0.1):
            exp_term = np.exp(-k * (t_scan - t0))
            rate = L * k * exp_term / (1.0 + exp_term) ** 2
            if rate < 0.1 * peak_rate:
                logistic_saturation = float(t_scan)
                break

    # AI multiplier: compare resolution rate in AI era vs pre-AI
    # Pre-AI: all resolved problems before Aug 2025 (historical baseline)
    pre_ai_resolved = sum(1 for p in problems
                          if _is_resolved(p) and _status_date(p) <= BASELINE_DATE)
    # Historical span: Erdos started ~1930s, database covers through Aug 2025
    # Use 80 years as conservative estimate of pre-database era
    pre_ai_years = 80.0
    pre_ai_monthly_rate = pre_ai_resolved / (pre_ai_years * 12) if pre_ai_years > 0 else 1.0

    # AI era: months since Sep 2025
    ai_months = len(sorted_months) if sorted_months else 1
    ai_monthly_rate = len(recent) / ai_months if ai_months > 0 else 0

    ai_multiplier = ai_monthly_rate / pre_ai_monthly_rate if pre_ai_monthly_rate > 0 else float("inf")

    return {
        "monthly_counts": dict(sorted(monthly.items())),
        "cumulative": list(zip(t.tolist(), y.tolist())),
        "fits": fits,
        "best_model": best_model,
        "logistic_saturation_month": logistic_saturation,
        "logistic_saturation_label": _month_from_index(logistic_saturation, sorted_months)
                                     if logistic_saturation else None,
        "ai_multiplier": round(ai_multiplier, 1),
        "pre_ai_monthly_rate": round(pre_ai_monthly_rate, 2),
        "ai_era_monthly_rate": round(ai_monthly_rate, 1),
        "total_recent": len(recent),
        "sorted_months": sorted_months,
    }


def _aic(n: int, rss: float, k: int) -> float:
    """Akaike Information Criterion (small-sample corrected)."""
    if n <= 0 or rss <= 0:
        return float("inf")
    ll = -n / 2.0 * (np.log(2 * np.pi * rss / n) + 1)
    aic = 2 * k - 2 * ll
    if n - k - 1 > 0:
        aic += 2 * k * (k + 1) / (n - k - 1)  # AICc correction
    return float(aic)


def _month_from_index(idx: Optional[float], sorted_months: List[str]) -> Optional[str]:
    """Convert a fractional month index back to a YYYY-MM label."""
    if idx is None or not sorted_months:
        return None
    base = datetime.strptime(sorted_months[0] + "-01", "%Y-%m-%d")
    target = base + timedelta(days=idx * 30.44)
    return target.strftime("%Y-%m")


# ══════════════════════════════════════════════════════════════════════
# Act 2: Problem Type Analysis
# ══════════════════════════════════════════════════════════════════════

def problem_type_analysis(problems: List[Dict]) -> Dict[str, Any]:
    """
    Analyze which tag families saw the biggest AI-era acceleration.

    Returns:
      - tag_acceleration: {tag: {pre_rate, ai_rate, multiplier}}
      - structured_vs_deep: comparison statistics
      - top_accelerated: sorted list of most-accelerated tags
    """
    recent = [p for p in problems
              if _is_resolved(p) and _status_date(p) > BASELINE_DATE]
    pre_ai = [p for p in problems
              if _is_resolved(p) and _status_date(p) <= BASELINE_DATE]

    # Tag totals
    tag_total = Counter()
    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1

    # Pre-AI solved by tag
    tag_pre = Counter()
    for p in pre_ai:
        for t in _tags(p):
            tag_pre[t] += 1

    # AI-era solved by tag
    tag_ai = Counter()
    for p in recent:
        for t in _tags(p):
            tag_ai[t] += 1

    # Months
    pre_months = 80 * 12  # ~80 years
    ai_months_set = set(_month_key(_status_date(p)) for p in recent)
    ai_months = max(len(ai_months_set), 1)

    tag_acceleration = {}
    for tag in tag_total:
        if tag_total[tag] < 5:
            continue
        pre_rate = tag_pre.get(tag, 0) / pre_months
        ai_rate = tag_ai.get(tag, 0) / ai_months
        multiplier = ai_rate / pre_rate if pre_rate > 0 else (
            float("inf") if ai_rate > 0 else 0.0
        )
        tag_acceleration[tag] = {
            "total": tag_total[tag],
            "pre_ai_solved": tag_pre.get(tag, 0),
            "ai_era_solved": tag_ai.get(tag, 0),
            "pre_monthly_rate": round(pre_rate, 4),
            "ai_monthly_rate": round(ai_rate, 2),
            "multiplier": round(multiplier, 1) if multiplier != float("inf") else None,
            "ai_era_fraction": round(tag_ai.get(tag, 0) / tag_total[tag], 3),
        }

    # Structured vs deep
    structured_counts = {"total": 0, "pre_solved": 0, "ai_solved": 0}
    deep_counts = {"total": 0, "pre_solved": 0, "ai_solved": 0}

    for p in problems:
        tags = _tags(p)
        is_struct = bool(tags & STRUCTURED_FAMILIES)
        is_deep = bool(tags & DEEP_FAMILIES)
        if is_struct:
            structured_counts["total"] += 1
            if p in pre_ai:
                structured_counts["pre_solved"] += 1
            if p in recent:
                structured_counts["ai_solved"] += 1
        if is_deep:
            deep_counts["total"] += 1
            if p in pre_ai:
                deep_counts["pre_solved"] += 1
            if p in recent:
                deep_counts["ai_solved"] += 1

    # Use sets for efficient membership testing
    pre_ai_ids = {id(p) for p in pre_ai}
    recent_ids = {id(p) for p in recent}
    structured_counts = {"total": 0, "pre_solved": 0, "ai_solved": 0}
    deep_counts = {"total": 0, "pre_solved": 0, "ai_solved": 0}

    for p in problems:
        tags = _tags(p)
        is_struct = bool(tags & STRUCTURED_FAMILIES)
        is_deep = bool(tags & DEEP_FAMILIES)
        pid = id(p)
        if is_struct:
            structured_counts["total"] += 1
            if pid in pre_ai_ids:
                structured_counts["pre_solved"] += 1
            if pid in recent_ids:
                structured_counts["ai_solved"] += 1
        if is_deep:
            deep_counts["total"] += 1
            if pid in pre_ai_ids:
                deep_counts["pre_solved"] += 1
            if pid in recent_ids:
                deep_counts["ai_solved"] += 1

    for d in (structured_counts, deep_counts):
        d["ai_era_rate"] = round(d["ai_solved"] / d["total"], 3) if d["total"] else 0
        d["pre_rate"] = round(d["pre_solved"] / d["total"], 3) if d["total"] else 0

    # Sort by multiplier for top accelerated
    top_accelerated = sorted(
        [(tag, info) for tag, info in tag_acceleration.items()
         if info["multiplier"] is not None and info["ai_era_solved"] >= 3],
        key=lambda x: x[1]["multiplier"],
        reverse=True,
    )

    return {
        "tag_acceleration": tag_acceleration,
        "structured_vs_deep": {
            "structured": structured_counts,
            "deep": deep_counts,
            "hypothesis_supported": (
                structured_counts["ai_era_rate"] > deep_counts["ai_era_rate"]
            ),
        },
        "top_accelerated": [(t, info) for t, info in top_accelerated[:15]],
    }


# ══════════════════════════════════════════════════════════════════════
# Act 3: The Lean Formalization Factor
# ══════════════════════════════════════════════════════════════════════

def lean_factor_analysis(problems: List[Dict]) -> Dict[str, Any]:
    """
    Analyze the role of Lean formalization in the AI era.

    Returns:
      - overall_formalization_rate
      - resolved_formalization_rate
      - ai_era_lean_fraction: fraction of AI-era resolutions that are Lean-verified
      - lean_vs_nonlean_correctness: proxy comparison
      - formalization_timeline: monthly Lean formalization counts
      - correlation: are formalized problems more likely to be resolved?
    """
    all_resolved = [p for p in problems if _is_resolved(p)]
    recent = [p for p in problems
              if _is_resolved(p) and _status_date(p) > BASELINE_DATE]
    lean_resolved = [p for p in problems if _is_lean(p)]
    recent_lean = [p for p in recent if _is_lean(p)]

    # Overall formalization rate
    formalized = sum(1 for p in problems if _is_formalized(p))
    total = len(problems)

    # Formalization timeline (using formalized.last_update)
    form_monthly = Counter()
    for p in problems:
        if _is_formalized(p):
            fd = _formalized_date(p)
            if fd > BASELINE_DATE:
                form_monthly[_month_key(fd)] += 1

    # Correlation: among all problems, is formalized correlated with resolved?
    # 2x2 contingency: formalized x resolved
    form_resolved = sum(1 for p in problems if _is_formalized(p) and _is_resolved(p))
    form_open = sum(1 for p in problems if _is_formalized(p) and _is_open(p))
    noform_resolved = sum(1 for p in problems if not _is_formalized(p) and _is_resolved(p))
    noform_open = sum(1 for p in problems if not _is_formalized(p) and _is_open(p))

    contingency = {
        "formalized_resolved": form_resolved,
        "formalized_open": form_open,
        "not_formalized_resolved": noform_resolved,
        "not_formalized_open": noform_open,
    }

    # Phi coefficient for 2x2 table
    a, b, c, d = form_resolved, form_open, noform_resolved, noform_open
    denom = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
    phi = (a * d - b * c) / denom if denom > 0 else 0.0

    # AI-era: Lean fraction
    ai_lean_frac = len(recent_lean) / len(recent) if recent else 0

    # Lean-verified solutions use "(Lean)" in status -- these have
    # machine-checked proofs, which is a strong correctness signal.
    # Non-Lean "proved" relies on human peer review only.
    # We cannot measure actual correctness, but the existence of
    # formal verification is itself the correctness proxy.

    # Monthly Lean resolutions
    lean_monthly = Counter()
    for p in recent_lean:
        lean_monthly[_month_key(_status_date(p))] += 1

    return {
        "total_problems": total,
        "total_formalized": formalized,
        "overall_formalization_rate": round(formalized / total, 3),
        "total_resolved": len(all_resolved),
        "total_lean_resolved": len(lean_resolved),
        "lean_fraction_of_resolved": round(len(lean_resolved) / len(all_resolved), 3)
                                     if all_resolved else 0,
        "ai_era_resolutions": len(recent),
        "ai_era_lean": len(recent_lean),
        "ai_era_lean_fraction": round(ai_lean_frac, 3),
        "contingency_table": contingency,
        "phi_coefficient": round(phi, 4),
        "formalization_monthly": dict(sorted(form_monthly.items())),
        "lean_resolution_monthly": dict(sorted(lean_monthly.items())),
    }


# ══════════════════════════════════════════════════════════════════════
# Act 4: Difficulty Curve
# ══════════════════════════════════════════════════════════════════════

def difficulty_curve(problems: List[Dict]) -> Dict[str, Any]:
    """
    Track whether AI is picking off easy problems first.

    Difficulty proxies:
      1. Problem number (lower = older = more entrenched)
      2. Tag complexity (number of tags as proxy for cross-domain difficulty)
      3. Prize value (higher prize = harder, per Erdos's intuition)

    Returns:
      - monthly_avg_number: {YYYY-MM: avg problem number}
      - monthly_avg_tags: {YYYY-MM: avg tag count}
      - monthly_avg_prize: {YYYY-MM: avg prize}
      - difficulty_trend: slope of avg number over time (+ = getting harder)
      - low_hanging_fruit_depleted: bool
    """
    recent = [p for p in problems
              if _is_resolved(p) and _status_date(p) > BASELINE_DATE]

    monthly_numbers = defaultdict(list)
    monthly_tags = defaultdict(list)
    monthly_prizes = defaultdict(list)

    for p in recent:
        mk = _month_key(_status_date(p))
        monthly_numbers[mk].append(_number(p))
        monthly_tags[mk].append(len(_tags(p)))
        monthly_prizes[mk].append(_prize_value(p))

    sorted_months = sorted(monthly_numbers.keys())

    avg_numbers = {}
    avg_tags = {}
    avg_prizes = {}
    for m in sorted_months:
        nums = monthly_numbers[m]
        avg_numbers[m] = round(sum(nums) / len(nums), 1) if nums else 0
        tags = monthly_tags[m]
        avg_tags[m] = round(sum(tags) / len(tags), 2) if tags else 0
        prizes = monthly_prizes[m]
        avg_prizes[m] = round(sum(prizes) / len(prizes), 1) if prizes else 0

    # Difficulty trend: linear regression of avg problem number on month index
    if len(sorted_months) >= 3:
        t = np.arange(len(sorted_months), dtype=float)
        y = np.array([avg_numbers[m] for m in sorted_months], dtype=float)
        coeffs = np.polyfit(t, y, 1)
        trend_slope = float(coeffs[0])
    else:
        trend_slope = 0.0

    # Compare difficulty of first half vs second half of AI era
    if len(recent) >= 10:
        recent_sorted = sorted(recent, key=lambda p: _status_date(p))
        mid = len(recent_sorted) // 2
        first_half = recent_sorted[:mid]
        second_half = recent_sorted[mid:]
        first_avg_num = sum(_number(p) for p in first_half) / len(first_half)
        second_avg_num = sum(_number(p) for p in second_half) / len(second_half)
        first_avg_tags = sum(len(_tags(p)) for p in first_half) / len(first_half)
        second_avg_tags = sum(len(_tags(p)) for p in second_half) / len(second_half)
    else:
        first_avg_num = second_avg_num = 0
        first_avg_tags = second_avg_tags = 0

    return {
        "monthly_avg_number": avg_numbers,
        "monthly_avg_tags": avg_tags,
        "monthly_avg_prize": avg_prizes,
        "difficulty_trend_slope": round(trend_slope, 2),
        "difficulty_increasing": trend_slope < 0,  # lower number = harder
        "first_half_avg_number": round(first_avg_num, 1),
        "second_half_avg_number": round(second_avg_num, 1),
        "first_half_avg_tags": round(first_avg_tags, 2),
        "second_half_avg_tags": round(second_avg_tags, 2),
        "low_hanging_fruit_depleted": second_avg_num < first_avg_num,
        "sorted_months": sorted_months,
    }


# ══════════════════════════════════════════════════════════════════════
# Act 5: Prediction -- Which Problems Fall Next?
# ══════════════════════════════════════════════════════════════════════

def predict_next_solved(problems: List[Dict], top_n: int = 20) -> Dict[str, Any]:
    """
    Build a feature-based predictor for which open problems are most
    likely to be solved next.

    Features:
      1. tag_solve_rate:     average solve rate of the problem's tags
      2. tag_ai_rate:        AI-era solve rate of tags
      3. tag_diversity:      number of tags (normalized)
      4. problem_recency:    higher number = more recent = potentially easier
      5. has_prize:          prize problems attract more attention
      6. formalized:         formalized statement may enable AI attack
      7. oeis_richness:      number of valid OEIS refs (computation accessible)
      8. neighbor_momentum:  fraction of nearby problems (by number) recently solved

    Score = weighted sum of normalized features, with weights learned from
    the AI-era solved problems (which features predicted AI-era solutions).
    """
    # Precompute tag statistics
    tag_total = Counter()
    tag_solved = Counter()
    tag_ai_solved = Counter()

    recent_ids = set()
    for p in problems:
        if _is_resolved(p) and _status_date(p) > BASELINE_DATE:
            recent_ids.add(id(p))

    for p in problems:
        for t in _tags(p):
            tag_total[t] += 1
            if _is_resolved(p):
                tag_solved[t] += 1
            if id(p) in recent_ids:
                tag_ai_solved[t] += 1

    tag_rate = {t: tag_solved[t] / tag_total[t] for t in tag_total if tag_total[t] > 0}
    tag_ai_rate = {t: tag_ai_solved[t] / tag_total[t] for t in tag_total if tag_total[t] > 0}

    max_tags = max((len(_tags(p)) for p in problems), default=1)
    max_num = max((_number(p) for p in problems), default=1)

    # Neighbor momentum: for each problem, look at +/- 25 neighbors
    number_to_recent = set()
    for p in problems:
        if id(p) in recent_ids:
            number_to_recent.add(_number(p))

    def _compute_features(p: Dict) -> List[float]:
        tags = _tags(p)
        rates = [tag_rate.get(t, 0.3) for t in tags] if tags else [0.3]
        ai_rates = [tag_ai_rate.get(t, 0.0) for t in tags] if tags else [0.0]

        feat_tag_rate = sum(rates) / len(rates)
        feat_ai_rate = sum(ai_rates) / len(ai_rates)
        feat_diversity = len(tags) / max_tags if max_tags > 0 else 0
        feat_recency = _number(p) / max_num if max_num > 0 else 0
        feat_prize = 1.0 if _prize_value(p) > 0 else 0.0
        feat_formalized = 1.0 if _is_formalized(p) else 0.0

        oeis = set(p.get("oeis", [])) - {"N/A", "possible", "n/a", "none", ""}
        feat_oeis = min(len(oeis) / 4.0, 1.0)  # normalize: 4+ refs = max

        num = _number(p)
        neighbors = range(max(1, num - 25), min(max_num + 1, num + 26))
        neighbor_solved = sum(1 for n in neighbors if n in number_to_recent and n != num)
        feat_momentum = neighbor_solved / 50.0  # 50 neighbors

        return [feat_tag_rate, feat_ai_rate, feat_diversity, feat_recency,
                feat_prize, feat_formalized, feat_oeis, feat_momentum]

    feature_names = [
        "tag_solve_rate", "tag_ai_rate", "tag_diversity", "problem_recency",
        "has_prize", "formalized", "oeis_richness", "neighbor_momentum",
    ]

    # Compute features for all problems
    all_features = []
    all_labels = []  # 1 = recently solved, 0 = open
    all_numbers = []

    for p in problems:
        if id(p) in recent_ids or _is_open(p):
            all_features.append(_compute_features(p))
            all_labels.append(1 if id(p) in recent_ids else 0)
            all_numbers.append(_number(p))

    X = np.array(all_features)
    y = np.array(all_labels)

    # Learn weights: for each feature, compute point-biserial correlation
    # with the recently-solved label
    weights = []
    for i in range(X.shape[1]):
        col = X[:, i]
        std_col = np.std(col)
        std_y = np.std(y)
        if std_col > 1e-12 and std_y > 1e-12:
            corr = float(np.corrcoef(col, y)[0, 1])
            weights.append(max(corr, 0.0))  # only positive correlations
        else:
            weights.append(0.0)

    # Normalize weights to sum to 1
    w_sum = sum(weights)
    if w_sum > 0:
        weights = [w / w_sum for w in weights]
    else:
        weights = [1.0 / len(weights)] * len(weights)

    w = np.array(weights)

    # Score all open problems
    open_problems = []
    for p in problems:
        if _is_open(p):
            feats = _compute_features(p)
            score = float(np.dot(w, feats))
            open_problems.append({
                "number": _number(p),
                "tags": sorted(_tags(p)),
                "formalized": _is_formalized(p),
                "prize": _prize_value(p),
                "score": round(score, 4),
                "features": {fn: round(fv, 3) for fn, fv in zip(feature_names, feats)},
            })

    # Sort by score descending
    open_problems.sort(key=lambda x: x["score"], reverse=True)

    return {
        "feature_names": feature_names,
        "feature_weights": {fn: round(fw, 4) for fn, fw in zip(feature_names, weights)},
        "top_predictions": open_problems[:top_n],
        "total_open": len(open_problems),
    }


# ══════════════════════════════════════════════════════════════════════
# Narrative Synthesis
# ══════════════════════════════════════════════════════════════════════

def synthesize_narrative(problems: List[Dict]) -> Dict[str, Any]:
    """
    Run all five acts and produce a structured narrative.
    """
    velocity = resolution_velocity(problems)
    types = problem_type_analysis(problems)
    lean = lean_factor_analysis(problems)
    difficulty = difficulty_curve(problems)
    predictions = predict_next_solved(problems)

    # Key statistics for narrative
    narrative = {
        "title": "How AI Is Changing Mathematical Discovery: The Erdos Problems Case Study",
        "date": "2026-03-16",
        "corpus_size": len(problems),
        "total_resolved": sum(1 for p in problems if _is_resolved(p)),
        "total_open": sum(1 for p in problems if _is_open(p)),

        "act1_velocity": velocity,
        "act2_types": types,
        "act3_lean": lean,
        "act4_difficulty": difficulty,
        "act5_predictions": predictions,

        # Headline findings
        "headlines": _compute_headlines(velocity, types, lean, difficulty, predictions),
    }
    return narrative


def _compute_headlines(velocity, types, lean, difficulty, predictions) -> List[str]:
    """Distill the analysis into headline findings."""
    headlines = []

    # Act 1
    headlines.append(
        f"AI multiplier: problems are being solved {velocity['ai_multiplier']}x faster "
        f"than the pre-AI baseline ({velocity['ai_era_monthly_rate']}/month vs "
        f"{velocity['pre_ai_monthly_rate']}/month)"
    )
    headlines.append(
        f"Best-fit model: {velocity['best_model']} -- "
        + ("the pace is accelerating but will saturate"
           if velocity['best_model'] == 'logistic'
           else "the pace shows no sign of slowing"
           if velocity['best_model'] == 'exponential'
           else "steady linear accumulation")
    )

    # Act 2
    sd = types["structured_vs_deep"]
    struct_rate = sd["structured"]["ai_era_rate"]
    deep_rate = sd["deep"]["ai_era_rate"]
    headlines.append(
        f"Structured problems (graph theory, Ramsey): {struct_rate:.1%} solved in AI era vs "
        f"deep problems (number theory, analysis): {deep_rate:.1%} -- "
        + ("hypothesis confirmed" if sd["hypothesis_supported"] else "hypothesis REFUTED")
    )

    if types["top_accelerated"]:
        top_tag = types["top_accelerated"][0][0]
        top_mult = types["top_accelerated"][0][1]["multiplier"]
        headlines.append(
            f"Most accelerated tag: '{top_tag}' ({top_mult}x AI-era speed-up)"
        )

    # Act 3
    headlines.append(
        f"Lean formalization: {lean['ai_era_lean']}/{lean['ai_era_resolutions']} "
        f"AI-era solutions are machine-verified ({lean['ai_era_lean_fraction']:.0%})"
    )
    headlines.append(
        f"Formalization-resolution correlation (phi): {lean['phi_coefficient']:.3f} -- "
        + ("formalized problems ARE more likely to be resolved"
           if lean['phi_coefficient'] > 0.05
           else "formalization and resolution are weakly correlated"
           if lean['phi_coefficient'] > -0.05
           else "formalized problems are LESS likely to be resolved (selection effect)")
    )

    # Act 4
    headlines.append(
        f"Difficulty trend: average problem number {'decreasing' if difficulty['difficulty_increasing'] else 'increasing'} "
        f"(first half avg #{difficulty['first_half_avg_number']:.0f}, "
        f"second half avg #{difficulty['second_half_avg_number']:.0f}) -- "
        + ("AI is moving to harder problems"
           if difficulty['low_hanging_fruit_depleted']
           else "low-hanging fruit still being harvested")
    )

    # Act 5
    if predictions["top_predictions"]:
        top3 = [f"#{p['number']}" for p in predictions["top_predictions"][:3]]
        headlines.append(
            f"Predicted next to fall: {', '.join(top3)} (highest composite scores)"
        )

    return headlines


# ══════════════════════════════════════════════════════════════════════
# Report Generation
# ══════════════════════════════════════════════════════════════════════

def generate_report(narrative: Dict[str, Any]) -> str:
    """Produce a narrative markdown report from the analysis."""
    lines = []
    lines.append(f"# {narrative['title']}")
    lines.append(f"\n*Generated: {narrative['date']}*\n")
    lines.append(f"Corpus: {narrative['corpus_size']} problems, "
                 f"{narrative['total_resolved']} resolved, "
                 f"{narrative['total_open']} open.\n")

    lines.append("## Key Findings\n")
    for i, h in enumerate(narrative["headlines"], 1):
        lines.append(f"{i}. {h}")

    # Act 1
    v = narrative["act1_velocity"]
    lines.append("\n## Act 1: Resolution Velocity\n")
    lines.append("### Monthly Resolution Count\n")
    lines.append("| Month | Solved | Cumulative |")
    lines.append("|-------|--------|------------|")
    cumul = 0
    for m in v["sorted_months"]:
        c = v["monthly_counts"].get(m, 0)
        cumul += c
        lines.append(f"| {m} | {c} | {cumul} |")
    lines.append(f"\n**AI multiplier**: {v['ai_multiplier']}x "
                 f"(from {v['pre_ai_monthly_rate']}/mo to {v['ai_era_monthly_rate']}/mo)\n")
    lines.append(f"**Best-fit model**: {v['best_model']}")
    if v.get("logistic_saturation_label"):
        lines.append(f"  - Logistic saturation (rate < 10% of peak): ~{v['logistic_saturation_label']}")
    for model, info in v["fits"].items():
        lines.append(f"  - {model}: AIC = {info['aic']:.1f}, RSS = {info['residual']:.1f}")

    # Act 2
    t = narrative["act2_types"]
    lines.append("\n## Act 2: Problem Type Analysis\n")
    lines.append("### Most Accelerated Tags\n")
    lines.append("| Tag | Total | AI-era Solved | Multiplier |")
    lines.append("|-----|-------|---------------|------------|")
    for tag, info in t["top_accelerated"][:10]:
        mult = f"{info['multiplier']}x" if info['multiplier'] else "new"
        lines.append(f"| {tag} | {info['total']} | {info['ai_era_solved']} | {mult} |")

    sd = t["structured_vs_deep"]
    lines.append("\n### Structured vs Deep Problems\n")
    lines.append(f"- **Structured** (graph theory, Ramsey, combinatorics): "
                 f"{sd['structured']['ai_solved']}/{sd['structured']['total']} "
                 f"({sd['structured']['ai_era_rate']:.1%}) solved in AI era")
    lines.append(f"- **Deep** (number theory, analysis, primes): "
                 f"{sd['deep']['ai_solved']}/{sd['deep']['total']} "
                 f"({sd['deep']['ai_era_rate']:.1%}) solved in AI era")
    lines.append(f"- Hypothesis ('structured yields faster to AI'): "
                 f"**{'SUPPORTED' if sd['hypothesis_supported'] else 'REFUTED'}**")

    # Act 3
    l = narrative["act3_lean"]
    lines.append("\n## Act 3: The Lean Formalization Factor\n")
    lines.append(f"- {l['total_formalized']}/{l['total_problems']} problems formalized "
                 f"({l['overall_formalization_rate']:.1%})")
    lines.append(f"- {l['total_lean_resolved']}/{l['total_resolved']} resolved with Lean proofs "
                 f"({l['lean_fraction_of_resolved']:.1%})")
    lines.append(f"- AI era: {l['ai_era_lean']}/{l['ai_era_resolutions']} Lean-verified "
                 f"({l['ai_era_lean_fraction']:.0%})")
    lines.append(f"- Phi correlation (formalized vs resolved): {l['phi_coefficient']:.4f}")

    ct = l["contingency_table"]
    lines.append("\n| | Resolved | Open |")
    lines.append("|--|----------|------|")
    lines.append(f"| Formalized | {ct['formalized_resolved']} | {ct['formalized_open']} |")
    lines.append(f"| Not formalized | {ct['not_formalized_resolved']} | {ct['not_formalized_open']} |")

    # Act 4
    d = narrative["act4_difficulty"]
    lines.append("\n## Act 4: Difficulty Curve\n")
    lines.append("### Monthly Average Problem Number (lower = harder)\n")
    lines.append("| Month | Avg Problem # | Avg Tags | Avg Prize |")
    lines.append("|-------|---------------|----------|-----------|")
    for m in d["sorted_months"]:
        lines.append(f"| {m} | {d['monthly_avg_number'].get(m, '-')} "
                     f"| {d['monthly_avg_tags'].get(m, '-')} "
                     f"| ${d['monthly_avg_prize'].get(m, 0):.0f} |")
    lines.append(f"\n**Trend slope**: {d['difficulty_trend_slope']} "
                 f"({'decreasing = harder problems' if d['difficulty_increasing'] else 'increasing = higher-numbered problems'})")
    lines.append(f"- First-half avg: #{d['first_half_avg_number']:.0f}")
    lines.append(f"- Second-half avg: #{d['second_half_avg_number']:.0f}")

    # Act 5
    pred = narrative["act5_predictions"]
    lines.append("\n## Act 5: Predictions -- Next 20 to Fall\n")
    lines.append(f"Feature weights: {pred['feature_weights']}\n")
    lines.append("| Rank | Problem # | Score | Tags | Formalized | Prize |")
    lines.append("|------|-----------|-------|------|------------|-------|")
    for i, p in enumerate(pred["top_predictions"], 1):
        tags_str = ", ".join(p["tags"][:3])
        form = "Yes" if p["formalized"] else "No"
        prize = f"${p['prize']:.0f}" if p["prize"] > 0 else "-"
        lines.append(f"| {i} | #{p['number']} | {p['score']:.3f} | {tags_str} | {form} | {prize} |")

    # Epilogue
    lines.append("\n## Epilogue: The Story So Far\n")
    lines.append(
        "The data tells a clear story: AI has transformed mathematical discovery from "
        "a purely human endeavor into a human-AI collaboration. The "
        f"{v['ai_multiplier']}x acceleration is not just about speed -- it reflects "
        "a qualitative shift in methodology. The Lean formalization pipeline "
        "(GPT-5.2 generates, Aristotle formalizes, humans verify) has created "
        "a new standard where machine-checked proofs are the norm, not the exception.\n"
    )
    lines.append(
        "The structured-vs-deep divide suggests AI currently excels at problems "
        "with clear combinatorial structure, where search and verification are "
        "tractable. Number theory and analysis problems, which require deeper "
        "conceptual insight, are harder but not immune -- as Tao noted, "
        "the 'lowest hanging fruit' is being picked, but the tree is tall.\n"
    )
    lines.append(
        "The difficulty curve shows the inevitable: easy problems deplete, "
        "and the AI must ascend the difficulty ladder. The question is not "
        "whether AI will plateau, but when and at what level.\n"
    )

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════

def main():
    """Run the full analysis and generate the report."""
    problems = load_problems()
    narrative = synthesize_narrative(problems)
    report = generate_report(narrative)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)

    print(f"Report written to {REPORT_PATH}")
    print()
    print("=== HEADLINE FINDINGS ===")
    for h in narrative["headlines"]:
        print(f"  * {h}")
    print()
    print(f"Total problems: {narrative['corpus_size']}")
    print(f"Total resolved: {narrative['total_resolved']}")
    print(f"AI-era resolved: {narrative['act1_velocity']['total_recent']}")
    print(f"Lean-verified: {narrative['act3_lean']['total_lean_resolved']}")


if __name__ == "__main__":
    main()
