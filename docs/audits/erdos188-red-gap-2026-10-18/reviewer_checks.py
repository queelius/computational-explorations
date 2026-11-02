"""Separate exact cross-check for the fixed Erdős 188 red-distance claim.

Alexander Richard Towell, with substantial OpenAI Codex assistance. MIT.
No production audit functions or source-deposit programs are imported.
See review.md for the distinct all-translates argument and review limits.
"""

from fractions import Fraction
import hashlib
import json
from math import lcm
from pathlib import Path


PIN = "b15251de28f6f552f4364d2170a58e923b730590d8797dfe5d09e007d2f87b2e"
FACTOR = Fraction(100863, 100000)
LOWER, UPPER = Fraction(999, 1000), Fraction(1001, 1000)


class Rejected(ValueError):
    """This sufficient disk criterion was not established."""


def require(condition, message):
    if not condition:
        raise Rejected(message)


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, "duplicate JSON key")
        obj[key] = value
    return obj


def rational(value):
    require(isinstance(value, str), "rational strings required")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise Rejected("invalid rational") from exc


def secant_via_double_angle(c):
    """A different exact test that c > sec(pi/24), with positive branches.

    t = 2/c^2 - 1 and s = 4*t^2 - 2. If 0 < s < sqrt(3), then
    t^2 < (2+sqrt(3))/4 = cos(pi/12)^2. Positivity of t and the
    relevant cosines gives 1/c^2 < (1+cos(pi/12))/2 = cos(pi/24)^2.
    """
    require(c > 0, "nonpositive secant candidate")
    t = 2 / c**2 - 1
    s = 4 * t**2 - 2
    require(t > 0 and s > 0 and s**2 < 3, "double-angle secant test failed")
    return {"t": str(t), "s": str(s), "3_minus_s_squared": str(3 - s**2)}


def load_geometry(data):
    require(isinstance(data, dict), "JSON object required")
    require(set(data) == {"P1", "P2", "centres", "h", "k"}, "wrong schema")
    require(type(data["k"]) is int and data["k"] == 24, "24-gons required")

    def vector(xs):
        require(isinstance(xs, list) and len(xs) == 2, "bad vector")
        return tuple(map(rational, xs))

    p1, p2 = vector(data["P1"]), vector(data["P2"])
    require(p1[1] == 0 and p1[0] > 0 and p2[1] > 0,
            "this check requires the source's upper-triangular positive lattice")
    require(isinstance(data["centres"], list) and len(data["centres"]) > 0,
            "no cells")
    require(isinstance(data["h"], list)
            and len(data["h"]) == len(data["centres"]), "radius count")
    centers = [vector(point) for point in data["centres"]]
    radii = [rational(h) * FACTOR for h in data["h"]]
    require(all(r > 0 for r in radii), "nonpositive radius")
    return p1, p2, centers, radii


def ceildiv(n, d):
    require(d > 0, "positive divisor required")
    return -((-n) // d)


def verify(data):
    secant_via_double_angle(FACTOR)
    p1, p2, centers, radii = load_geometry(data)
    values = [*p1, *p2, *(x for point in centers for x in point),
              *radii, LOWER, UPPER]
    scale = lcm(*(value.denominator for value in values))

    def integer(value):
        scaled = value * scale
        require(scaled.denominator == 1, "inexact integer scaling")
        return scaled.numerator

    length, shear, height = integer(p1[0]), integer(p2[0]), integer(p2[1])
    points = [(integer(x), integer(y)) for x, y in centers]
    sizes = [integer(r) for r in radii]
    low, high = integer(LOWER), integer(UPPER)
    require(all(2 * r < low for r in sizes), "same-cell diameter too large")
    examined = near = far = 0
    near_min = far_min = None
    translations = set()
    for i, (xi, yi) in enumerate(points):
        for j, (xj, yj) in enumerate(points):
            dx, dy = xi - xj, yi - yj
            radius_sum = sizes[i] + sizes[j]
            reach = high + radius_sum
            # Every possibly non-far center satisfies |dy+bH| <= reach.
            bmin = ceildiv(-reach - dy, height)
            bmax = (reach - dy) // height
            for b in range(bmin, bmax + 1):
                offset_x = dx + b * shear
                # It also satisfies |dx+bA+aL| <= reach.
                amin = ceildiv(-reach - offset_x, length)
                amax = (reach - offset_x) // length
                for a in range(amin, amax + 1):
                    if i == j and a == b == 0:
                        continue
                    xx, yy = offset_x + a * length, dy + b * height
                    distance_squared = xx * xx + yy * yy
                    near_room = low - radius_sum
                    if near_room > 0 and distance_squared < near_room * near_room:
                        near += 1
                        margin = near_room * near_room - distance_squared
                        near_min = margin if near_min is None else min(near_min, margin)
                    elif distance_squared > reach * reach:
                        far += 1
                        margin = distance_squared - reach * reach
                        far_min = margin if far_min is None else min(far_min, margin)
                    else:
                        raise Rejected(f"undecided pair {i+1},{j+1}, translate {a},{b}")
                    examined += 1
                    translations.add((a, b))
    return {
        "status": "PASS", "cells": len(points), "integer_scale": scale,
        "pair_specific_candidates": examined, "near": near, "far": far,
        "candidate_translates": [list(t) for t in sorted(translations)],
        "near_min_squared_margin": str(Fraction(near_min, scale**2))
            if near_min is not None else None,
        "far_min_squared_margin": str(Fraction(far_min, scale**2))
            if far_min is not None else None,
        "same_cell_min_margin": str(Fraction(min(low - 2 * r for r in sizes), scale)),
    }


def self_tests(source):
    """Small controls also exercise inclusive translation and gap boundaries."""
    controls = []

    def rejects(name, operation):
        try:
            operation()
        except Rejected:
            controls.append(name)
            return
        raise Rejected("negative control incorrectly accepted: " + name)

    for n in range(-21, 22):
        for d in range(1, 10):
            c = ceildiv(n, d)
            require((c - 1) * d < n <= c * d, "bad integer ceiling")
    controls.append("387 signed integer ceiling cases")
    secant_via_double_angle(FACTOR)
    rejects("smaller secant factor", lambda: secant_via_double_angle(Fraction(100862, 100000)))
    rejects("duplicate JSON key", lambda: json.loads('{"k":24,"k":24}',
                                                    object_pairs_hook=unique_object))

    def fixture(x, h="1/10"):
        return {"P1": ["10", "0"], "P2": ["0", "10"], "k": 24,
                "centres": [["0", "0"], [str(x), "0"]], "h": [h, h]}

    require(verify(fixture(3))["near"] == 0, "safe fixture failed")
    controls.append("safe separated disks")
    require(verify(fixture(Fraction(1, 10)))["near"] == 2, "overlap fixture failed")
    controls.append("safe overlapping disks")
    rejects("unit pair at original centers", lambda: verify(fixture(1)))
    rejects("unit pair across period", lambda: verify(fixture(9)))
    # Both endpoint cases lie exactly on the boundary of the closed interval.
    s = FACTOR / 5
    rejects("closed near endpoint", lambda: verify(fixture(LOWER - s)))
    rejects("closed far endpoint", lambda: verify(fixture(UPPER + s)))
    rejects("diameter endpoint", lambda: verify(fixture(3, str(LOWER / (2 * FACTOR)))))
    changed = json.loads(json.dumps(source))
    x, y = map(rational, changed["centres"][0])
    changed["centres"][1] = [str(x + 1), str(y)]
    rejects("actual-source red unit centers", lambda: verify(changed))
    shifted = json.loads(json.dumps(source))
    p1, p2 = map(lambda xs: list(map(rational, xs)), [source["P1"], source["P2"]])
    for i, point in enumerate(shifted["centres"]):
        a, b = 19 * i - 800, 31 * i - 1400
        shifted["centres"][i] = [str(rational(point[j]) + a * p1[j] + b * p2[j])
                                  for j in range(2)]
    shifted_result = verify(shifted)
    require(shifted_result["near"] == 408, "independent lattice shifts changed near pairs")
    controls.append("all 90 centers independently shifted by large signed lattice vectors")
    return controls


def main():
    path = Path(__file__).with_name("cfg_k60.json")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PIN, "source SHA-256 mismatch")
    data = json.loads(raw, object_pairs_hook=unique_object)
    require(len(data["centres"]) == 90, "wrong source size")
    result = verify(data)
    result["source_sha256"] = PIN
    result["secant_check"] = secant_via_double_angle(FACTOR)
    result["controls"] = self_tests(data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
