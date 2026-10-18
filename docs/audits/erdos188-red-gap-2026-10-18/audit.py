"""Exact periodic red-pair certificate, standard library only.

Alexander Richard Towell, with substantial OpenAI Codex assistance.
New code: MIT. Source configuration: Carson Crocker, CC BY 4.0.
See README.md for the written all-translates implication and exact scope.
"""

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path
import sys

Vec = tuple[F, F]
SOURCE_SHA256 = "b15251de28f6f552f4364d2170a58e923b730590d8797dfe5d09e007d2f87b2e"


class AuditError(ValueError):
    """The certificate was not established; this alone is not a counterexample."""


class PairKind(Enum):
    NEAR = "near"
    FAR = "far"


@dataclass(frozen=True)
class Config:
    p1: Vec
    p2: Vec
    centres: tuple[Vec, ...]
    apothems: tuple[F, ...]


def dot(a: Vec, b: Vec) -> F:
    return a[0] * b[0] + a[1] * b[1]


def inverse_rows(p1: Vec, p2: Vec) -> tuple[Vec, Vec]:
    det = p1[0] * p2[1] - p1[1] * p2[0]
    if det == 0:
        raise AuditError("singular period lattice")
    return (p2[1] / det, -p2[0] / det), (-p1[1] / det, p1[0] / det)


def parse_config(data: object) -> Config:
    """Read exact rational strings; reject silent shape/float coercions."""
    if not isinstance(data, dict) or set(data) != {"P1", "P2", "centres", "h", "k"}:
        raise AuditError("configuration must have exactly P1, P2, centres, h, k")
    if type(data["k"]) is not int or data["k"] != 24:
        raise AuditError("this algebraic radius proof is for regular 24-gons only")

    def rational(x: object) -> F:
        if not isinstance(x, str):
            raise AuditError("coordinates and apothems must be exact rational strings")
        try:
            return F(x)
        except (ValueError, ZeroDivisionError) as exc:
            raise AuditError("invalid rational string") from exc

    def vector(x: object) -> Vec:
        if not isinstance(x, list) or len(x) != 2:
            raise AuditError("expected two rational coordinates")
        return rational(x[0]), rational(x[1])

    if not isinstance(data["centres"], list) or not data["centres"]:
        raise AuditError("nonempty list of centers required")
    if not isinstance(data["h"], list) or len(data["h"]) != len(data["centres"]):
        raise AuditError("one apothem per center required")
    cfg = Config(vector(data["P1"]), vector(data["P2"]),
                 tuple(vector(c) for c in data["centres"]),
                 tuple(rational(h) for h in data["h"]))
    if any(h <= 0 for h in cfg.apothems):
        raise AuditError("all apothems must be positive")
    inverse_rows(cfg.p1, cfg.p2)
    return cfg


def radius_factor(candidate: F = F(100863, 100000)) -> F:
    """Prove candidate > sec(pi/24) by rational square comparisons."""
    root2_lower, root6_lower = F(1414213, 1000000), F(2449489, 1000000)
    if not (0 < root2_lower and root2_lower**2 < 2
            and 0 < root6_lower and root6_lower**2 < 6):
        raise AuditError("invalid radical lower bounds")
    cos_squared_lower = (4 + root2_lower + root6_lower) / 8
    if candidate <= 0 or candidate**2 * cos_squared_lower <= 1:
        raise AuditError("radius factor not proved above sec(pi/24)")
    return candidate


def classify(q: F, radius_sum: F, lower: F, upper: F) -> tuple[PairKind, F]:
    """Strictly separate two closed disks from the closed distance interval."""
    if q < 0 or radius_sum < 0 or lower < 0 or upper < lower:
        raise AuditError("invalid pair-classification inputs")
    room = lower - radius_sum
    if room > 0 and q < room**2:
        return PairKind.NEAR, room**2 - q
    far_margin = q - (upper + radius_sum)**2
    if far_margin > 0:
        return PairKind.FAR, far_margin
    raise AuditError("pair is not certified outside the closed distance interval")


def certify(cfg: Config, gap: F = F(1, 1000)) -> dict:
    """Check all nine images after proving the omitted images are far."""
    if not isinstance(gap, F) or not 0 <= gap < 1:
        raise AuditError("gap must be an exact rational in [0,1)")
    lower, upper = 1 - gap, 1 + gap
    factor = radius_factor()
    radii = tuple(h * factor for h in cfg.apothems)
    if len(radii) != len(cfg.centres) or not radii or any(r <= 0 for r in radii):
        raise AuditError("nonempty matching positive-radius data required")
    same_margins = [lower - 2 * r for r in radii]
    if min(same_margins) <= 0:
        raise AuditError("same-cell diameter not below the excluded interval")
    rows = inverse_rows(cfg.p1, cfg.p2)
    threshold = upper + 2 * max(radii)
    window_ratios = [threshold**2 * dot(row, row) for row in rows]
    if any(ratio >= 1 for ratio in window_ratios):
        raise AuditError("nine-image window is not certified complete for this lattice")

    # A separate integer lattice shift of each center leaves the infinite set fixed.
    normalized = []
    for centre in cfg.centres:
        coordinates = [dot(row, centre) for row in rows]
        a, b = (x.numerator // x.denominator for x in coordinates)
        normalized.append((centre[0] - a * cfg.p1[0] - b * cfg.p2[0],
                           centre[1] - a * cfg.p1[1] - b * cfg.p2[1]))
    counts = {kind: 0 for kind in PairKind}
    minima = {kind: None for kind in PairKind}
    witnesses = {kind: None for kind in PairKind}
    for a, b in itertools.product(range(-1, 2), repeat=2):
        shift = (a * cfg.p1[0] + b * cfg.p2[0], a * cfg.p1[1] + b * cfg.p2[1])
        for i, ci in enumerate(normalized):
            for j, cj in enumerate(normalized):
                if i == j and a == b == 0:
                    continue
                difference = (ci[0] + shift[0] - cj[0], ci[1] + shift[1] - cj[1])
                q, s = dot(difference, difference), radii[i] + radii[j]
                try:
                    kind, margin = classify(q, s, lower, upper)
                except AuditError as exc:
                    raise AuditError(f"uncertified cells {i+1},{j+1}, image ({a},{b}), "
                                     f"center distance squared {q}") from exc
                counts[kind] += 1
                if minima[kind] is None or margin < minima[kind]:
                    minima[kind] = margin
                    witnesses[kind] = {"cells_one_based": [i + 1, j + 1],
                                       "normalized_image": [a, b],
                                       "center_distance_squared": str(q),
                                       "radius_sum": str(s)}
    return {
        "status": "PASS", "cells": len(radii),
        "excluded_distance_interval": [str(lower), str(upper)],
        "radius_factor": str(factor), "max_radius_upper": str(max(radii)),
        "same_cell_min_distance_margin": str(min(same_margins)),
        "window_threshold": str(threshold),
        "window_squared_ratios": [str(v) for v in window_ratios],
        "images_per_ordered_pair": 9,
        "ordered_pairs": sum(counts.values()),
        "near_pairs": counts[PairKind.NEAR], "far_pairs": counts[PairKind.FAR],
        "min_squared_margins": {k.value: str(v) if v is not None else None
                                for k, v in minima.items()},
        "margin_witnesses": {k.value: v for k, v in witnesses.items()},
        "normalized_centres": [[str(x), str(y)] for x, y in normalized],
    }


def check_source_digest(raw: bytes) -> None:
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise AuditError("configuration SHA-256 differs from the pinned source")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).with_name("cfg_k60.json")
    if len(sys.argv) > 2:
        print("usage: python audit.py [cfg_k60.json]", file=sys.stderr)
        return 2
    try:
        raw = path.read_bytes()
        check_source_digest(raw)
        result = certify(parse_config(json.loads(raw)))
        result["source_sha256"] = SOURCE_SHA256
        print(json.dumps(result, indent=2))
    except (AuditError, OSError, json.JSONDecodeError) as exc:
        print(f"NOT ESTABLISHED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
