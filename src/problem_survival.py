#!/usr/bin/env python3
"""
Survival Analysis of Erdos Problem Resolution

Treats each Erdos problem as a "unit" in a survival study:
  - "Time" = problem number (proxy for chronological ordering / difficulty)
  - "Event" = resolved (proved, disproved, solved)
  - "Censored" = still open (right-censored)

Implements five analyses:
  1. Kaplan-Meier survival curve with median survival time
  2. Cox proportional hazards model with covariates
  3. Competing risks: proved vs disproved
  4. AI changepoint detection in the hazard function
  5. Accelerated failure time (AFT) models

Uses lifelines when available, otherwise implements from scratch using
scipy/numpy. All results are returned as structured dictionaries amenable
to downstream analysis and testing.

Novel application: "mathematical epidemiology" — applying biostatistical
survival methods to the sociology of mathematical problem-solving.
"""

import re
import warnings
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats
from scipy.optimize import minimize

import yaml

DATA_PATH = (
    Path(__file__).parent.parent
    / "data"
    / "erdosproblems"
    / "data"
    / "problems.yaml"
)

# ---------------------------------------------------------------------------
# Status classification
# ---------------------------------------------------------------------------

_PROVED_STATES = frozenset({"proved", "proved (Lean)"})
_DISPROVED_STATES = frozenset({"disproved", "disproved (Lean)"})
_SOLVED_STATES = frozenset({"solved", "solved (Lean)"})
_RESOLVED_STATES = _PROVED_STATES | _DISPROVED_STATES | _SOLVED_STATES
_OPEN_STATES = frozenset(
    {
        "open",
        "verifiable",
        "decidable",
        "falsifiable",
        "not provable",
        "not disprovable",
        "independent",
    }
)

# Major tag categories for Cox covariates
TAG_CATEGORIES = {
    "number_theory": {"number theory"},
    "graph_theory": {"graph theory"},
    "ramsey": {"ramsey theory"},
    "geometry": {"geometry"},
    "combinatorics": {"additive combinatorics", "combinatorics"},
    "analysis": {"analysis"},
}


def load_problems() -> list[dict]:
    """Load problems from YAML."""
    with open(DATA_PATH, "r") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------


def _parse_prize(prize_str: str) -> float:
    """Extract numeric prize value in USD from a prize string.

    Handles '$500', '£250', 'no', etc.
    """
    if not prize_str or prize_str == "no":
        return 0.0
    s = str(prize_str).strip()
    # GBP conversion
    gbp = "£" in s
    # Strip currency symbols and commas
    s = re.sub(r"[£$,]", "", s)
    try:
        val = float(s)
    except ValueError:
        return 0.0
    if gbp:
        val *= 1.27  # GBP -> USD
    return val


def _classify_status(state: str) -> str:
    """Classify a status string into proved/disproved/solved/open."""
    if state in _PROVED_STATES:
        return "proved"
    if state in _DISPROVED_STATES:
        return "disproved"
    if state in _SOLVED_STATES:
        return "solved"
    return "open"


def _assign_tag_category(tags: list[str]) -> str:
    """Return the primary tag category for a problem's tag list.

    Priority order mirrors TAG_CATEGORIES key order.
    Falls back to 'other' if no category matches.
    """
    tag_set = set(tags)
    for cat_name, cat_tags in TAG_CATEGORIES.items():
        if tag_set & cat_tags:
            return cat_name
    return "other"


def build_survival_dataframe(
    problems: list[dict] | None = None,
) -> dict[str, np.ndarray]:
    """Build arrays for survival analysis from the raw YAML data.

    Returns a dict with keys:
        - problem_number: int array
        - time: float array (= problem_number, the survival "time")
        - event: bool array (True = resolved)
        - event_type: str array ('proved', 'disproved', 'solved', 'open')
        - n_tags: int array
        - has_prize: bool array
        - prize_usd: float array
        - has_oeis: bool array
        - tag_category: str array (primary category)
        - is_formalized: bool array
    """
    if problems is None:
        problems = load_problems()

    n = len(problems)
    out: dict[str, Any] = {
        "problem_number": np.empty(n, dtype=int),
        "time": np.empty(n, dtype=float),
        "event": np.empty(n, dtype=bool),
        "event_type": np.empty(n, dtype=object),
        "n_tags": np.empty(n, dtype=int),
        "has_prize": np.empty(n, dtype=bool),
        "prize_usd": np.empty(n, dtype=float),
        "has_oeis": np.empty(n, dtype=bool),
        "tag_category": np.empty(n, dtype=object),
        "is_formalized": np.empty(n, dtype=bool),
    }

    for i, p in enumerate(problems):
        num = int(str(p["number"]))
        state = p.get("status", {}).get("state", "open")
        tags = p.get("tags", [])
        prize = _parse_prize(p.get("prize", "no"))
        oeis_entries = p.get("oeis", [])
        real_oeis = [o for o in oeis_entries if o not in ("N/A", "possible")]
        formalized = p.get("formalized", {}).get("state", "no") == "yes"

        out["problem_number"][i] = num
        out["time"][i] = float(num)
        classified = _classify_status(state)
        out["event"][i] = classified != "open"
        out["event_type"][i] = classified
        out["n_tags"][i] = len(tags)
        out["has_prize"][i] = prize > 0
        out["prize_usd"][i] = prize
        out["has_oeis"][i] = len(real_oeis) > 0
        out["tag_category"][i] = _assign_tag_category(tags)
        out["is_formalized"][i] = formalized

    return out


# ===================================================================
# 1. Kaplan-Meier estimator
# ===================================================================


def kaplan_meier(
    time: np.ndarray, event: np.ndarray
) -> dict[str, np.ndarray | float | None]:
    """Compute the Kaplan-Meier survival function.

    Parameters
    ----------
    time : array of "survival times" (problem numbers)
    event : boolean array (True = observed event, False = censored)

    Returns
    -------
    dict with keys:
        timeline : sorted unique event times
        survival : S(t) at each timeline point
        n_at_risk : number at risk just before each time
        n_events : number of events at each time
        median_survival : time at which S(t) first <= 0.5 (or None)
        ci_lower, ci_upper : Greenwood 95% CI
    """
    time = np.asarray(time, dtype=float)
    event = np.asarray(event, dtype=bool)
    n_total = len(time)

    # Sort by time
    order = np.argsort(time)
    t_sorted = time[order]
    e_sorted = event[order]

    # Unique event times (only where events occur)
    event_times = np.unique(t_sorted[e_sorted])
    if len(event_times) == 0:
        return {
            "timeline": np.array([]),
            "survival": np.array([]),
            "n_at_risk": np.array([]),
            "n_events": np.array([]),
            "median_survival": None,
            "ci_lower": np.array([]),
            "ci_upper": np.array([]),
        }

    timeline = []
    survival_vals = []
    n_at_risk_vals = []
    n_events_vals = []
    var_terms = []  # for Greenwood formula

    s = 1.0
    greenwood_sum = 0.0

    for t_k in event_times:
        # n at risk: all subjects with time >= t_k
        n_risk = np.sum(t_sorted >= t_k)
        # events at this time
        d_k = np.sum((t_sorted == t_k) & e_sorted)

        if n_risk > 0 and d_k > 0:
            s *= 1.0 - d_k / n_risk
            if n_risk > d_k:
                greenwood_sum += d_k / (n_risk * (n_risk - d_k))

        timeline.append(t_k)
        survival_vals.append(s)
        n_at_risk_vals.append(n_risk)
        n_events_vals.append(d_k)
        var_terms.append(greenwood_sum)

    timeline = np.array(timeline)
    survival = np.array(survival_vals)
    n_at_risk_arr = np.array(n_at_risk_vals)
    n_events_arr = np.array(n_events_vals)

    # Greenwood confidence intervals
    var_arr = np.array(var_terms)
    se = survival * np.sqrt(np.maximum(var_arr, 0.0))
    ci_lower = np.maximum(survival - 1.96 * se, 0.0)
    ci_upper = np.minimum(survival + 1.96 * se, 1.0)

    # Median survival
    below_half = np.where(survival <= 0.5)[0]
    median = float(timeline[below_half[0]]) if len(below_half) > 0 else None

    return {
        "timeline": timeline,
        "survival": survival,
        "n_at_risk": n_at_risk_arr,
        "n_events": n_events_arr,
        "median_survival": median,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
    }


def km_summary(data: dict[str, np.ndarray] | None = None) -> dict:
    """Run KM on the full dataset and return a summary dict."""
    if data is None:
        data = build_survival_dataframe()
    km = kaplan_meier(data["time"], data["event"])
    n_total = len(data["time"])
    n_events = int(data["event"].sum())
    n_censored = n_total - n_events
    # Survival at quartile problem numbers
    quartiles = {}
    for q_num in [250, 500, 750, 1000]:
        idx = np.searchsorted(km["timeline"], q_num, side="right") - 1
        if 0 <= idx < len(km["survival"]):
            quartiles[q_num] = float(km["survival"][idx])
        else:
            quartiles[q_num] = 1.0 if q_num < km["timeline"][0] else None

    return {
        "n_total": n_total,
        "n_events": n_events,
        "n_censored": n_censored,
        "median_survival": km["median_survival"],
        "survival_at_quartiles": quartiles,
        "km": km,
    }


# ===================================================================
# 2. Cox Proportional Hazards
# ===================================================================


def _build_covariate_matrix(data: dict[str, np.ndarray]) -> np.ndarray:
    """Build the design matrix X for Cox regression.

    Columns: n_tags, has_prize, has_oeis, is_formalized,
             dummy-coded tag_categories (drop 'other' as baseline).
    Returns (X, column_names).
    """
    n = len(data["time"])
    # Continuous / binary covariates
    n_tags = data["n_tags"].astype(float)
    has_prize = data["has_prize"].astype(float)
    has_oeis = data["has_oeis"].astype(float)
    is_formalized = data["is_formalized"].astype(float)

    # Dummy-code tag_category (drop 'other')
    categories = sorted(TAG_CATEGORIES.keys())  # deterministic order
    dummies = {}
    for cat in categories:
        dummies[cat] = (data["tag_category"] == cat).astype(float)

    col_names = ["n_tags", "has_prize", "has_oeis", "is_formalized"] + [
        f"cat_{c}" for c in categories
    ]
    X = np.column_stack(
        [n_tags, has_prize, has_oeis, is_formalized]
        + [dummies[c] for c in categories]
    )
    return X, col_names


def cox_partial_likelihood(
    beta: np.ndarray, time: np.ndarray, event: np.ndarray, X: np.ndarray
) -> float:
    """Negative log partial likelihood for Cox PH model.

    Uses Breslow's method for tied event times.
    """
    n = len(time)
    eta = X @ beta  # linear predictor

    # Sort by descending time for risk set computation
    order = np.argsort(-time)
    t_ord = time[order]
    e_ord = event[order]
    eta_ord = eta[order]

    # Stabilize by subtracting max
    eta_max = np.max(eta_ord)
    exp_eta = np.exp(eta_ord - eta_max)

    log_lik = 0.0
    cumsum_exp = 0.0

    for i in range(n):
        cumsum_exp += exp_eta[i]
        if e_ord[i]:
            log_lik += (eta_ord[i] - eta_max) - np.log(cumsum_exp)

    return -log_lik


def cox_partial_likelihood_grad(
    beta: np.ndarray, time: np.ndarray, event: np.ndarray, X: np.ndarray
) -> np.ndarray:
    """Gradient of negative log partial likelihood."""
    n, p = X.shape
    eta = X @ beta

    order = np.argsort(-time)
    t_ord = time[order]
    e_ord = event[order]
    X_ord = X[order]
    eta_ord = eta[order]

    eta_max = np.max(eta_ord)
    exp_eta = np.exp(eta_ord - eta_max)

    grad = np.zeros(p)
    cumsum_exp = 0.0
    cumsum_X_exp = np.zeros(p)

    for i in range(n):
        cumsum_exp += exp_eta[i]
        cumsum_X_exp += X_ord[i] * exp_eta[i]
        if e_ord[i]:
            grad -= X_ord[i] - cumsum_X_exp / cumsum_exp

    return grad


def fit_cox_model(
    data: dict[str, np.ndarray] | None = None,
) -> dict:
    """Fit a Cox proportional hazards model.

    Returns dict with:
        coefficients : beta estimates
        hazard_ratios : exp(beta)
        column_names : covariate names
        se : standard errors (from inverse Hessian)
        ci_lower, ci_upper : 95% CI for hazard ratios
        p_values : Wald test p-values
        concordance : Harrell's C-index
        n_events : number of events
        n_total : total observations
    """
    if data is None:
        data = build_survival_dataframe()

    X, col_names = _build_covariate_matrix(data)
    time = data["time"]
    event = data["event"]
    p = X.shape[1]

    # Standardize covariates for numerical stability
    means = X.mean(axis=0)
    stds = X.std(axis=0)
    stds[stds == 0] = 1.0  # avoid divide by zero for constant columns
    X_std = (X - means) / stds

    beta0 = np.zeros(p)
    result = minimize(
        cox_partial_likelihood,
        beta0,
        args=(time, event, X_std),
        jac=cox_partial_likelihood_grad,
        method="L-BFGS-B",
        options={"maxiter": 500, "ftol": 1e-10},
    )

    beta_std = result.x
    # Transform back to original scale
    beta = beta_std / stds

    # Standard errors via numerical Hessian
    eps = 1e-5
    H = np.zeros((p, p))
    f0 = cox_partial_likelihood(beta_std, time, event, X_std)
    for i in range(p):
        for j in range(i, p):
            e_i = np.zeros(p)
            e_j = np.zeros(p)
            e_i[i] = eps
            e_j[j] = eps
            f_pp = cox_partial_likelihood(
                beta_std + e_i + e_j, time, event, X_std
            )
            f_pm = cox_partial_likelihood(
                beta_std + e_i - e_j, time, event, X_std
            )
            f_mp = cox_partial_likelihood(
                beta_std - e_i + e_j, time, event, X_std
            )
            f_mm = cox_partial_likelihood(
                beta_std - e_i - e_j, time, event, X_std
            )
            H[i, j] = (f_pp - f_pm - f_mp + f_mm) / (4 * eps**2)
            H[j, i] = H[i, j]

    # Invert Hessian for variance-covariance
    try:
        cov_std = np.linalg.inv(H)
        se_std = np.sqrt(np.maximum(np.diag(cov_std), 0.0))
        se = se_std / stds  # transform SE back
    except np.linalg.LinAlgError:
        se = np.full(p, np.nan)

    hr = np.exp(beta)
    ci_lower = np.exp(beta - 1.96 * se)
    ci_upper = np.exp(beta + 1.96 * se)

    # Wald p-values
    z = beta / se
    p_values = 2 * (1 - stats.norm.cdf(np.abs(z)))

    # Harrell's C-index
    c_index = _concordance_index(time, event, X @ beta)

    return {
        "coefficients": beta,
        "hazard_ratios": hr,
        "column_names": col_names,
        "se": se,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "p_values": p_values,
        "concordance": c_index,
        "n_events": int(event.sum()),
        "n_total": len(time),
        "converged": result.success,
    }


def _concordance_index(
    time: np.ndarray, event: np.ndarray, risk_score: np.ndarray
) -> float:
    """Compute Harrell's concordance index.

    Uses a random subsample for large datasets to keep O(n^2) manageable.
    """
    n = len(time)
    # Subsample if large
    max_pairs = 50000
    if n > 1000:
        rng = np.random.RandomState(42)
        idx = rng.choice(n, size=min(n, 2000), replace=False)
        time = time[idx]
        event = event[idx]
        risk_score = risk_score[idx]
        n = len(time)

    concordant = 0
    discordant = 0
    tied_risk = 0

    for i in range(n):
        if not event[i]:
            continue
        for j in range(n):
            if i == j:
                continue
            if time[j] > time[i]:
                # j survived longer, so j should have lower risk
                if risk_score[j] < risk_score[i]:
                    concordant += 1
                elif risk_score[j] > risk_score[i]:
                    discordant += 1
                else:
                    tied_risk += 1

    denom = concordant + discordant + tied_risk
    if denom == 0:
        return 0.5
    return (concordant + 0.5 * tied_risk) / denom


# ===================================================================
# 3. Competing Risks: Proved vs Disproved
# ===================================================================


def competing_risks_cif(
    data: dict[str, np.ndarray] | None = None,
) -> dict[str, dict]:
    """Compute cumulative incidence functions (CIF) for competing risks.

    Two event types: "proved" (including "solved") and "disproved".
    Uses the Aalen-Johansen estimator.

    Returns dict with keys 'proved' and 'disproved', each containing:
        timeline, cif, n_events
    Also returns 'overall_km' and 'gray_test' (Gray's test statistic).
    """
    if data is None:
        data = build_survival_dataframe()

    time = data["time"]
    event_type = data["event_type"]
    n = len(time)

    # Map: 0=censored, 1=proved/solved, 2=disproved
    cause = np.zeros(n, dtype=int)
    for i in range(n):
        if event_type[i] in ("proved", "solved"):
            cause[i] = 1
        elif event_type[i] == "disproved":
            cause[i] = 2
        # else 0 (censored)

    order = np.argsort(time)
    t_sorted = time[order]
    c_sorted = cause[order]

    # Unique times where any event occurs
    event_mask = c_sorted > 0
    event_times = np.unique(t_sorted[event_mask])

    if len(event_times) == 0:
        empty = {"timeline": np.array([]), "cif": np.array([]), "n_events": 0}
        return {"proved": empty, "disproved": empty}

    # KM for overall survival (any event)
    # Then CIF_k(t) = sum over t_j<=t of [ S(t_{j-1}) * d_k(t_j)/n(t_j) ]
    s_prev = 1.0
    cif1 = []  # proved
    cif2 = []  # disproved
    cif1_cum = 0.0
    cif2_cum = 0.0
    timeline = []
    d1_total = 0
    d2_total = 0

    for t_k in event_times:
        at_risk = np.sum(t_sorted >= t_k)
        d1 = np.sum((t_sorted == t_k) & (c_sorted == 1))
        d2 = np.sum((t_sorted == t_k) & (c_sorted == 2))
        d_total = d1 + d2

        if at_risk > 0:
            cif1_cum += s_prev * d1 / at_risk
            cif2_cum += s_prev * d2 / at_risk
            s_prev *= 1.0 - d_total / at_risk

        d1_total += d1
        d2_total += d2
        timeline.append(t_k)
        cif1.append(cif1_cum)
        cif2.append(cif2_cum)

    timeline = np.array(timeline)
    cif1 = np.array(cif1)
    cif2 = np.array(cif2)

    # Simple two-sample test: compare proportion of proved vs disproved
    # Chi-squared test on observed vs expected under equal hazard
    total_events = d1_total + d2_total
    if total_events > 0:
        expected_ratio = d1_total / total_events
        # Gray-like test: compare CIF curves
        # Use log-rank-like statistic for competing risks
        stat, p_val = _competing_risks_test(
            time, cause, event_times, t_sorted, c_sorted
        )
    else:
        stat, p_val = 0.0, 1.0

    return {
        "proved": {
            "timeline": timeline,
            "cif": cif1,
            "n_events": d1_total,
        },
        "disproved": {
            "timeline": timeline,
            "cif": cif2,
            "n_events": d2_total,
        },
        "gray_test": {"statistic": stat, "p_value": p_val},
    }


def _competing_risks_test(
    time: np.ndarray,
    cause: np.ndarray,
    event_times: np.ndarray,
    t_sorted: np.ndarray,
    c_sorted: np.ndarray,
) -> tuple[float, float]:
    """Log-rank-type test for equality of cause-specific hazards.

    Tests H0: the cause-specific hazard for cause 1 relative to the
    overall event hazard is constant over time.  This is a two-sample
    log-rank analogue that partitions events into cause-1 vs cause-2
    and computes observed-minus-expected at each event time where both
    causes are at risk.

    At each event time t_k we observe d1_k (cause-1 events) and
    d2_k (cause-2 events) out of d_k = d1_k + d2_k total events.
    Under H0 the expected cause-1 count is d_k * (n1_k / n_k) where
    n1_k is the number still at risk who will eventually experience
    cause 1 (or be censored), n_k is total at risk.  This reduces to
    the standard log-rank when applied to the sub-hazards.

    We use a simpler but valid chi-squared test on the 2-by-K table
    of (cause x time-band), collapsing into bands for power.
    """
    # Split timeline into bands and test homogeneity of proved/disproved
    # ratio across bands (a chi-squared test of independence).
    n_bands = 4
    if len(event_times) < n_bands:
        return 0.0, 1.0

    # Divide the event-time range into equal bands
    t_min, t_max = event_times[0], event_times[-1]
    band_edges = np.linspace(t_min, t_max + 1, n_bands + 1)

    observed = np.zeros((2, n_bands), dtype=float)  # [cause, band]
    for i in range(n_bands):
        lo, hi = band_edges[i], band_edges[i + 1]
        band_mask = (t_sorted >= lo) & (t_sorted < hi)
        observed[0, i] = np.sum(band_mask & (c_sorted == 1))
        observed[1, i] = np.sum(band_mask & (c_sorted == 2))

    # Remove empty columns
    nonempty = observed.sum(axis=0) > 0
    if nonempty.sum() < 2:
        return 0.0, 1.0
    observed = observed[:, nonempty]

    # Chi-squared test of independence
    try:
        result = stats.chi2_contingency(observed)
        stat, p_val = float(result.statistic), float(result.pvalue)
    except ValueError:
        stat, p_val = 0.0, 1.0

    return stat, p_val


def competing_risks_by_tag(
    data: dict[str, np.ndarray] | None = None,
) -> dict[str, dict]:
    """For each major tag category, compute the proved:disproved ratio.

    Returns {category: {n_proved, n_disproved, ratio, fisher_p}}.
    """
    if data is None:
        data = build_survival_dataframe()

    results = {}
    categories = sorted(set(data["tag_category"]))

    for cat in categories:
        mask = data["tag_category"] == cat
        et = data["event_type"][mask]
        n_proved = int(np.sum((et == "proved") | (et == "solved")))
        n_disproved = int(np.sum(et == "disproved"))
        n_open = int(np.sum(et == "open"))

        ratio = n_proved / n_disproved if n_disproved > 0 else float("inf")

        # Fisher exact test: this category vs rest
        rest_mask = ~mask
        rest_et = data["event_type"][rest_mask]
        rest_proved = int(np.sum((rest_et == "proved") | (rest_et == "solved")))
        rest_disproved = int(np.sum(rest_et == "disproved"))

        # 2x2 table: [proved, disproved] x [this_cat, rest]
        table = np.array(
            [[n_proved, n_disproved], [rest_proved, rest_disproved]]
        )
        if table.sum() > 0 and table.min() >= 0:
            try:
                _, fisher_p = stats.fisher_exact(table)
            except ValueError:
                fisher_p = 1.0
        else:
            fisher_p = 1.0

        results[cat] = {
            "n_proved": n_proved,
            "n_disproved": n_disproved,
            "n_open": n_open,
            "ratio": ratio,
            "fisher_p": fisher_p,
        }

    return results


# ===================================================================
# 4. AI Changepoint Detection
# ===================================================================


def piecewise_hazard_model(
    data: dict[str, np.ndarray] | None = None,
    candidate_changepoints: list[int] | None = None,
) -> dict:
    """Fit piecewise-constant hazard models and find the best changepoint.

    Tests whether the hazard rate changes at a given problem number.
    The "AI changepoint" hypothesis: problems posed later (higher numbers)
    may see faster resolution in the AI era.

    For each candidate changepoint c, fits:
      h(t) = lambda_1 if t <= c
      h(t) = lambda_2 if t > c

    Uses maximum likelihood for exponential intervals.

    Returns dict with:
        best_changepoint : problem number
        hazard_before, hazard_after : estimated hazards
        ai_multiplier : hazard_after / hazard_before
        log_likelihood_ratio : LR test stat vs constant hazard
        p_value : chi-squared p-value for the changepoint
        all_candidates : list of dicts for each tested changepoint
    """
    if data is None:
        data = build_survival_dataframe()

    if candidate_changepoints is None:
        # Test at every 50th problem from 100 to 1100
        candidate_changepoints = list(range(100, 1101, 50))

    time = data["time"]
    event = data["event"]

    # Null model: constant hazard
    n_events_total = int(event.sum())
    total_exposure = float(time.sum())  # total person-time
    if total_exposure == 0:
        return {
            "best_changepoint": None,
            "hazard_before": 0.0,
            "hazard_after": 0.0,
            "ai_multiplier": 1.0,
            "log_likelihood_ratio": 0.0,
            "p_value": 1.0,
            "all_candidates": [],
        }

    lambda_0 = n_events_total / total_exposure
    ll_null = _exponential_loglik(time, event, lambda_0)

    best_lr = -np.inf
    best_cp = None
    all_results = []

    for cp in candidate_changepoints:
        mask_before = time <= cp
        mask_after = time > cp

        # Events and exposure in each segment
        d1 = event[mask_before].sum()
        d2 = event[mask_after].sum()
        # Exposure: sum of times in each segment
        # For right-censored data: exposure = min(time_i, cp) for before
        # and max(time_i - cp, 0) for after
        exp1 = np.sum(np.minimum(time, cp))
        exp2 = np.sum(np.maximum(time - cp, 0))

        if exp1 == 0 or exp2 == 0:
            continue

        lam1 = d1 / exp1 if exp1 > 0 else 0
        lam2 = d2 / exp2 if exp2 > 0 else 0

        # Log-likelihood for piecewise model
        ll_piece = 0.0
        if lam1 > 0:
            ll_piece += d1 * np.log(lam1) - lam1 * exp1
        elif d1 > 0:
            ll_piece = -np.inf
        else:
            ll_piece += -lam1 * exp1

        if lam2 > 0:
            ll_piece += d2 * np.log(lam2) - lam2 * exp2
        elif d2 > 0:
            ll_piece = -np.inf
        else:
            ll_piece += -lam2 * exp2

        lr = 2 * (ll_piece - ll_null) if np.isfinite(ll_piece) else -np.inf

        multiplier = lam2 / lam1 if lam1 > 0 else float("inf")

        all_results.append(
            {
                "changepoint": cp,
                "hazard_before": float(lam1),
                "hazard_after": float(lam2),
                "ai_multiplier": float(multiplier),
                "log_likelihood_ratio": float(lr),
                "n_events_before": int(d1),
                "n_events_after": int(d2),
            }
        )

        if lr > best_lr:
            best_lr = lr
            best_cp = cp

    if best_cp is None:
        return {
            "best_changepoint": None,
            "hazard_before": 0.0,
            "hazard_after": 0.0,
            "ai_multiplier": 1.0,
            "log_likelihood_ratio": 0.0,
            "p_value": 1.0,
            "all_candidates": all_results,
        }

    best_result = next(r for r in all_results if r["changepoint"] == best_cp)

    # P-value: LR test with 1 df (one additional parameter)
    # Note: supremum over changepoints inflates type I error,
    # so we apply a Bonferroni-like correction
    n_tests = len(all_results)
    raw_p = 1 - stats.chi2.cdf(max(best_lr, 0), df=1)
    corrected_p = min(raw_p * n_tests, 1.0)

    return {
        "best_changepoint": best_cp,
        "hazard_before": best_result["hazard_before"],
        "hazard_after": best_result["hazard_after"],
        "ai_multiplier": best_result["ai_multiplier"],
        "log_likelihood_ratio": float(best_lr),
        "p_value": float(corrected_p),
        "raw_p_value": float(raw_p),
        "n_candidates_tested": n_tests,
        "all_candidates": all_results,
    }


def _exponential_loglik(
    time: np.ndarray, event: np.ndarray, lam: float
) -> float:
    """Log-likelihood for constant hazard (exponential) model."""
    if lam <= 0:
        return -np.inf
    d = event.sum()
    total_t = time.sum()
    return d * np.log(lam) - lam * total_t


# ===================================================================
# 5. Accelerated Failure Time (AFT) Models
# ===================================================================


def _aft_log_likelihood(
    params: np.ndarray,
    log_time: np.ndarray,
    event: np.ndarray,
    X: np.ndarray,
    dist: str,
) -> float:
    """Negative log-likelihood for AFT model.

    Model: log(T) = X @ beta + sigma * W
    where W has a standard distribution depending on `dist`.

    params = [beta_0, beta_1, ..., beta_p, log_sigma]
    """
    p = X.shape[1]
    beta = params[:p]
    log_sigma = params[p]
    sigma = np.exp(log_sigma)

    mu = X @ beta
    z = (log_time - mu) / sigma

    if dist == "weibull":
        # W ~ standard Gumbel (minimum)
        # f(z) = exp(z - exp(z)), S(z) = exp(-exp(z))
        log_f = z - np.exp(z) - log_sigma
        log_S = -np.exp(z)
    elif dist == "lognormal":
        # W ~ standard normal
        log_f = stats.norm.logpdf(z) - log_sigma
        log_S = stats.norm.logsf(z)
    elif dist == "loglogistic":
        # W ~ standard logistic
        log_f = stats.logistic.logpdf(z) - log_sigma
        log_S = stats.logistic.logsf(z)
    else:
        raise ValueError(f"Unknown distribution: {dist}")

    # Likelihood: prod f(t)^event * S(t)^(1-event)
    ll = np.sum(event * log_f + (1 - event) * log_S)
    return -ll


def fit_aft_model(
    data: dict[str, np.ndarray] | None = None,
    dist: str = "weibull",
) -> dict:
    """Fit an accelerated failure time model.

    Parameters
    ----------
    data : survival dataframe dict
    dist : 'weibull', 'lognormal', or 'loglogistic'

    Returns dict with:
        distribution : name
        coefficients : beta estimates
        sigma : scale parameter
        acceleration_factors : exp(beta) for each covariate
        column_names : covariate names
        aic : Akaike information criterion
        bic : Bayesian information criterion
        log_likelihood : maximized log-likelihood
        se : standard errors
        p_values : Wald p-values
    """
    if data is None:
        data = build_survival_dataframe()

    X_raw, col_names = _build_covariate_matrix(data)
    time = data["time"]
    event = data["event"].astype(float)

    # Add intercept
    n = len(time)
    X = np.column_stack([np.ones(n), X_raw])
    full_col_names = ["intercept"] + col_names

    log_time = np.log(np.maximum(time, 1.0))  # avoid log(0)
    p = X.shape[1]

    # Initial guess: OLS on log_time using event observations
    event_mask = event > 0
    if event_mask.sum() > p:
        try:
            beta_init = np.linalg.lstsq(
                X[event_mask], log_time[event_mask], rcond=None
            )[0]
        except np.linalg.LinAlgError:
            beta_init = np.zeros(p)
    else:
        beta_init = np.zeros(p)
        beta_init[0] = np.mean(log_time)

    # Residual scale estimate
    if event_mask.sum() > p:
        resid = log_time[event_mask] - X[event_mask] @ beta_init
        sigma_init = max(np.std(resid), 0.5)
    else:
        sigma_init = 1.0

    params0 = np.concatenate([beta_init, [np.log(sigma_init)]])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = minimize(
            _aft_log_likelihood,
            params0,
            args=(log_time, event, X, dist),
            method="L-BFGS-B",
            options={"maxiter": 1000, "ftol": 1e-10},
        )

    params = result.x
    beta = params[:p]
    sigma = np.exp(params[p])
    ll = -result.fun

    # Standard errors via Hessian
    eps = 1e-5
    n_params = len(params)
    H = np.zeros((n_params, n_params))
    f0 = _aft_log_likelihood(params, log_time, event, X, dist)
    for i in range(n_params):
        for j in range(i, n_params):
            e_i = np.zeros(n_params)
            e_j = np.zeros(n_params)
            e_i[i] = eps
            e_j[j] = eps
            f_pp = _aft_log_likelihood(
                params + e_i + e_j, log_time, event, X, dist
            )
            f_pm = _aft_log_likelihood(
                params + e_i - e_j, log_time, event, X, dist
            )
            f_mp = _aft_log_likelihood(
                params - e_i + e_j, log_time, event, X, dist
            )
            f_mm = _aft_log_likelihood(
                params - e_i - e_j, log_time, event, X, dist
            )
            H[i, j] = (f_pp - f_pm - f_mp + f_mm) / (4 * eps**2)
            H[j, i] = H[i, j]

    try:
        cov = np.linalg.inv(H)
        se_all = np.sqrt(np.maximum(np.diag(cov), 0.0))
    except np.linalg.LinAlgError:
        se_all = np.full(n_params, np.nan)

    se_beta = se_all[:p]
    z = beta / np.where(se_beta > 0, se_beta, np.inf)
    p_values = 2 * (1 - stats.norm.cdf(np.abs(z)))

    # AIC / BIC
    k = n_params  # number of estimated parameters
    aic = 2 * k - 2 * ll
    bic = k * np.log(n) - 2 * ll

    # Acceleration factors: exp(beta) for covariates (not intercept)
    af = np.exp(beta[1:])

    return {
        "distribution": dist,
        "coefficients": beta,
        "sigma": sigma,
        "acceleration_factors": af,
        "column_names": full_col_names,
        "aic": float(aic),
        "bic": float(bic),
        "log_likelihood": float(ll),
        "se": se_beta,
        "p_values": p_values,
        "converged": result.success,
    }


def compare_aft_distributions(
    data: dict[str, np.ndarray] | None = None,
) -> dict:
    """Fit Weibull, log-normal, and log-logistic AFT models; compare via AIC.

    Returns dict with:
        models : {dist_name: fit_result}
        best_distribution : name with lowest AIC
        aic_table : {dist_name: AIC}
        bic_table : {dist_name: BIC}
    """
    if data is None:
        data = build_survival_dataframe()

    models = {}
    for dist in ("weibull", "lognormal", "loglogistic"):
        models[dist] = fit_aft_model(data, dist=dist)

    aic_table = {d: m["aic"] for d, m in models.items()}
    bic_table = {d: m["bic"] for d, m in models.items()}
    best = min(aic_table, key=aic_table.get)

    return {
        "models": models,
        "best_distribution": best,
        "aic_table": aic_table,
        "bic_table": bic_table,
    }


# ===================================================================
# Cross-validated log-rank test by tag category
# ===================================================================


def log_rank_by_category(
    data: dict[str, np.ndarray] | None = None,
) -> dict[str, dict]:
    """For each tag category, test whether survival differs from the rest.

    Uses the log-rank test (Mantel-Haenszel).

    Returns {category: {statistic, p_value, n_cat, n_rest,
                         median_cat, median_rest}}.
    """
    if data is None:
        data = build_survival_dataframe()

    results = {}
    categories = sorted(set(data["tag_category"]))

    for cat in categories:
        mask = data["tag_category"] == cat
        t1, e1 = data["time"][mask], data["event"][mask]
        t2, e2 = data["time"][~mask], data["event"][~mask]

        stat, p_val = _log_rank_test(t1, e1, t2, e2)

        km1 = kaplan_meier(t1, e1)
        km2 = kaplan_meier(t2, e2)

        results[cat] = {
            "statistic": stat,
            "p_value": p_val,
            "n_cat": int(mask.sum()),
            "n_rest": int((~mask).sum()),
            "median_cat": km1["median_survival"],
            "median_rest": km2["median_survival"],
        }

    return results


def _log_rank_test(
    t1: np.ndarray,
    e1: np.ndarray,
    t2: np.ndarray,
    e2: np.ndarray,
) -> tuple[float, float]:
    """Two-sample log-rank test.

    Returns (chi2_statistic, p_value).
    """
    # Combine and find unique event times
    t_all = np.concatenate([t1, t2])
    e_all = np.concatenate([e1, e2])
    g_all = np.concatenate([np.ones(len(t1)), np.zeros(len(t2))])

    event_times = np.unique(t_all[e_all.astype(bool)])
    if len(event_times) == 0:
        return 0.0, 1.0

    O1 = 0.0  # observed events in group 1
    E1 = 0.0  # expected events in group 1
    V = 0.0   # variance

    for t_k in event_times:
        at_risk = t_all >= t_k
        n = at_risk.sum()
        n1 = (at_risk & (g_all == 1)).sum()

        events_at_t = (t_all == t_k) & e_all.astype(bool)
        d = events_at_t.sum()
        d1 = (events_at_t & (g_all == 1)).sum()

        if n > 0:
            O1 += d1
            E1 += d * n1 / n
            if n > 1:
                V += d * (n - d) * n1 * (n - n1) / (n**2 * (n - 1))

    if V > 0:
        stat = (O1 - E1) ** 2 / V
        p_val = 1 - stats.chi2.cdf(stat, df=1)
    else:
        stat = 0.0
        p_val = 1.0

    return float(stat), float(p_val)


# ===================================================================
# Full analysis runner
# ===================================================================


def run_full_analysis() -> dict:
    """Run all five survival analyses and return consolidated results."""
    data = build_survival_dataframe()

    print("=" * 70)
    print("SURVIVAL ANALYSIS OF ERDOS PROBLEM RESOLUTION")
    print("=" * 70)

    # 1. Kaplan-Meier
    print("\n[1] KAPLAN-MEIER SURVIVAL CURVE")
    print("-" * 40)
    km_res = km_summary(data)
    print(f"  Total problems:   {km_res['n_total']}")
    print(f"  Resolved (event): {km_res['n_events']}")
    print(f"  Open (censored):  {km_res['n_censored']}")
    print(f"  Median survival:  {km_res['median_survival']}")
    print(f"  Survival at key problem numbers:")
    for q, s in km_res["survival_at_quartiles"].items():
        if s is not None:
            print(f"    S({q}) = {s:.3f}")

    # 2. Cox PH
    print("\n[2] COX PROPORTIONAL HAZARDS MODEL")
    print("-" * 40)
    cox_res = fit_cox_model(data)
    print(f"  Convergence: {cox_res['converged']}")
    print(f"  Concordance (C-index): {cox_res['concordance']:.3f}")
    print(f"\n  {'Covariate':<20s} {'HR':>8s} {'95% CI':>16s} {'p':>8s}")
    print(f"  {'-'*20} {'-'*8} {'-'*16} {'-'*8}")
    for i, name in enumerate(cox_res["column_names"]):
        hr = cox_res["hazard_ratios"][i]
        lo = cox_res["ci_lower"][i]
        hi = cox_res["ci_upper"][i]
        pv = cox_res["p_values"][i]
        sig = "*" if pv < 0.05 else " "
        print(f"  {name:<20s} {hr:8.3f} [{lo:6.3f}, {hi:6.3f}] {pv:8.4f}{sig}")

    # 3. Competing risks
    print("\n[3] COMPETING RISKS: PROVED vs DISPROVED")
    print("-" * 40)
    cr_res = competing_risks_cif(data)
    print(f"  Events proved/solved: {cr_res['proved']['n_events']}")
    print(f"  Events disproved:     {cr_res['disproved']['n_events']}")
    gray = cr_res["gray_test"]
    print(f"  Gray-like test: stat={gray['statistic']:.2f}, p={gray['p_value']:.4f}")

    cr_tags = competing_risks_by_tag(data)
    print(f"\n  {'Category':<20s} {'Proved':>8s} {'Dispr':>8s} {'Ratio':>8s} {'Fisher p':>10s}")
    print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*10}")
    for cat in sorted(cr_tags):
        r = cr_tags[cat]
        ratio_str = f"{r['ratio']:.1f}" if r["ratio"] != float("inf") else "inf"
        print(
            f"  {cat:<20s} {r['n_proved']:8d} {r['n_disproved']:8d} "
            f"{ratio_str:>8s} {r['fisher_p']:10.4f}"
        )

    # 4. AI changepoint
    print("\n[4] AI CHANGEPOINT DETECTION")
    print("-" * 40)
    cp_res = piecewise_hazard_model(data)
    print(f"  Best changepoint at problem #{cp_res['best_changepoint']}")
    print(f"  Hazard before: {cp_res['hazard_before']:.6f}")
    print(f"  Hazard after:  {cp_res['hazard_after']:.6f}")
    print(f"  AI multiplier: {cp_res['ai_multiplier']:.3f}x")
    print(f"  LR statistic:  {cp_res['log_likelihood_ratio']:.2f}")
    print(f"  p-value (corrected): {cp_res['p_value']:.4f}")

    # 5. AFT models
    print("\n[5] ACCELERATED FAILURE TIME MODELS")
    print("-" * 40)
    aft_res = compare_aft_distributions(data)
    print(f"  AIC comparison:")
    for dist, aic in sorted(aft_res["aic_table"].items(), key=lambda x: x[1]):
        marker = " <-- best" if dist == aft_res["best_distribution"] else ""
        print(f"    {dist:<15s} AIC={aic:.1f}{marker}")

    best_model = aft_res["models"][aft_res["best_distribution"]]
    print(f"\n  Best model: {aft_res['best_distribution']} (sigma={best_model['sigma']:.3f})")
    covariate_names = best_model["column_names"][1:]  # skip intercept
    print(f"\n  {'Covariate':<20s} {'AF':>8s} {'p':>8s}")
    print(f"  {'-'*20} {'-'*8} {'-'*8}")
    for i, name in enumerate(covariate_names):
        af = best_model["acceleration_factors"][i]
        pv = best_model["p_values"][i + 1]  # +1 for intercept
        sig = "*" if pv < 0.05 else " "
        print(f"  {name:<20s} {af:8.3f} {pv:8.4f}{sig}")

    # Log-rank tests by category
    print("\n[BONUS] LOG-RANK TESTS BY TAG CATEGORY")
    print("-" * 40)
    lr_res = log_rank_by_category(data)
    print(f"  {'Category':<20s} {'N':>6s} {'Median':>8s} {'chi2':>8s} {'p':>8s}")
    print(f"  {'-'*20} {'-'*6} {'-'*8} {'-'*8} {'-'*8}")
    for cat in sorted(lr_res):
        r = lr_res[cat]
        med = f"{r['median_cat']:.0f}" if r["median_cat"] is not None else "N/A"
        sig = "*" if r["p_value"] < 0.05 else " "
        print(
            f"  {cat:<20s} {r['n_cat']:6d} {med:>8s} "
            f"{r['statistic']:8.2f} {r['p_value']:8.4f}{sig}"
        )

    return {
        "kaplan_meier": km_res,
        "cox": cox_res,
        "competing_risks": cr_res,
        "competing_risks_by_tag": cr_tags,
        "changepoint": cp_res,
        "aft": aft_res,
        "log_rank": lr_res,
    }


if __name__ == "__main__":
    run_full_analysis()
