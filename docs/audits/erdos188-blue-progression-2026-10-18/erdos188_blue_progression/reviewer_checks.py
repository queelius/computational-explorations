"""Small independent exact oracles for the Claim B acceptance logic.

Alexander Richard Towell, with substantial OpenAI Codex assistance. MIT.
This is a separate AI review/control suite, not human review or full replay.
It imports the subject under test but computes its reference values separately.
"""

from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

from . import audit


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def alternating_oracle(x, parity):
    """Exact 50-term sine/cosine series and its one-sided tail enclosure.

    For 0 <= x <= 4 the omitted terms decrease strictly in magnitude:
    their ratios are at most 16/(101*102) for cosine, smaller for sine.
    This uses a recurrence and alternating-tail bound, rather than the
    subject's factorial polynomial and symmetric Lagrange remainder.
    """
    term, total = x ** parity, Q(0)
    for k in range(50):
        total += term
        term *= -x*x / ((2*k+parity+1)*(2*k+parity+2))
    return min(total, total+term), max(total, total+term)


def trig_controls():
    # Includes exact binary floats used in the source's direction partition,
    # rational grid points, both endpoints, and points close to pi/2 and pi.
    samples = sorted({Q(k, 32) for k in range(129)} | {
        Q(float(3.1416*k/40000)) for k in (1, 2, 41, 9999, 10000,
                                             19999, 20000, 39999, 40000)
    })
    for x in samples:
        observed = audit.trig_bounds(x)
        for parity, interval in enumerate(observed):
            lo, hi = alternating_oracle(x, parity)
            require(Q(interval[0], audit.SCALE) <= lo <= hi <=
                    Q(interval[1], audit.SCALE), "trigonometric enclosure")
    return len(samples)


def pi_control():
    """Independent identity pi/4 = atan(1/2) + atan(1/3).

    The sum lies in (0,pi/2), and its tangent is 1 by the addition formula.
    Fifty alternating terms enclose each arctangent without using Machin's
    identity or production pi_bounds().
    """
    low = high = Q(0)
    for x in (Q(1, 2), Q(1, 3)):
        partial = sum(((-1)**k*x**(2*k+1)/Q(2*k+1)
                       for k in range(50)), Q(0))
        low += 4*partial
        high += 4*(partial+x**101/101)
    subject_low, subject_high = audit.pi_bounds()
    require(subject_low < low < high < subject_high,
            "Machin enclosure does not contain independent pi interval")
    return {"identity": "pi/4 = atan(1/2) + atan(1/3)",
            "terms_per_arctangent": 50, "production_enclosure_confirmed": True}


def rejection(name, operation, results):
    try:
        operation()
    except audit.InvalidCertificate:
        results.append(name)
        return
    raise RuntimeError("accepted negative control: " + name)


def corner_controls():
    """Compare accepted j=0 certificates with direct rational corner distances.

    Exact translated centers are deliberately recovered from large signed
    lattice shifts, testing interval cancellation and both translation signs.
    All tested distances are separated from the acceptance threshold, except
    the explicit exact-boundary controls below.
    """
    tested = accepted = rejected = 0
    for shear in (Q(-11, 37), Q(0), Q(13, 43)):
        p1, p2 = (Q(1, 4), Q(0)), (shear, Q(1, 4))
        for a, b in ((0, 0), (-100003, 100019), (100003, -100019)):
            for target in ((Q(1, 8), Q(1, 8)), (Q(-1, 17), Q(1, 7)),
                           (Q(2, 7), Q(9, 37))):
                centre = tuple(target[k] - a*p1[k] - b*p2[k] for k in range(2))
                distance = max(sum((corner[k]-target[k])**2 for k in range(2))
                               for corner in ((Q(0), Q(0)), (Q(1, 4), Q(0)),
                                              (Q(0), Q(1, 4)), (Q(1, 4), Q(1, 4))))
                for radius in (Q(1, 10), Q(1, 5), Q(1, 2), Q(1)):
                    config = audit.Config(p1, p2, (centre,), (radius,))
                    expected = distance < radius*radius
                    try:
                        result = audit.verify_tree(config,
                            (Q(0), Q(1, 10000), Q(1, 20000)),
                            (0,), ((0,), (0,), (a,), (b,)), 60, 0)
                        require(expected and result['leaves'] == 1,
                                "accepted square outside exact disk")
                        accepted += 1
                    except audit.InvalidCertificate:
                        require(not expected, "unexpected rejection of separated oracle case")
                        rejected += 1
                    tested += 1
    return {"cases": tested, "accepted": accepted, "rejected": rejected}


def failure_controls():
    results = []
    p1, p2 = (Q(1, 4), Q(0)), (Q(0), Q(1, 4))
    config = audit.Config(p1, p2, ((Q(1, 8), Q(1, 8)),), (Q(1),))
    box = Q(0), Q(1, 10000), Q(1, 20000)
    witness = ((0,), (0,), (0,), (0,))

    def check(codes=(0,), w=witness, cfg=config, angles=box, depth=2):
        return audit.verify_tree(cfg, angles, codes, w, 60, depth)

    # A 3-4-5 right triangle makes the far corner exactly tangent to a
    # rational disk: max distance from (-1/2,-3/4) to [0,1/4]^2 is 5/4.
    tangent = audit.Config(p1, p2, ((Q(-1, 2), Q(-3, 4)),), (Q(5, 4),))
    rejection("exact tangent corner", lambda: check(cfg=tangent), results)
    rejection("tangent minus one grid unit", lambda: check(cfg=audit.Config(
        p1, p2, tangent.centres, (Q(5, 4)-Q(1, audit.SCALE),))), results)
    require(check(cfg=audit.Config(p1, p2, tangent.centres,
                   (Q(5, 4)+Q(1, audit.SCALE),)))['leaves'] == 1,
            "one grid unit of strict corner slack should pass")
    results.append("tangent plus one grid unit passes")
    rejection("missing root leaf", lambda: check(codes=()), results)
    rejection("missing fourth child", lambda: check(codes=(-1,0,0,0)), results)
    rejection("unused trailing node", lambda: check(codes=(0,0)), results)
    rejection("oversized leaf index", lambda: check(codes=(1,)), results)
    rejection("negative non-split code", lambda: check(codes=(-2,)), results)
    rejection("bool tree code", lambda: check(codes=(False,)), results)
    rejection("noninteger translation", lambda: check(w=((0,),(0,),(Q(0),),(0,))), results)
    rejection("negative cell index", lambda: check(w=((-1,),(0,),(0,),(0,))), results)
    rejection("j=60", lambda: check(w=((0,),(60,),(0,),(0,))), results)
    rejection("negative j", lambda: check(w=((0,),(-1,),(0,),(0,))), results)
    rejection("nonpositive shrunken radius", lambda: check(
        w=((0,),(59,),(0,),(0,)), angles=(Q(0),Q(1),Q(1,2))), results)
    rejection("midpoint outside interval", lambda: check(angles=(Q(0),Q(1,10),Q(1))), results)
    rejection("zero angle width", lambda: check(angles=(Q(0),Q(0),Q(0))), results)
    rejection("too-deep split", lambda: check(codes=(-1,),depth=0), results)
    rejection("unequal witness vector lengths", lambda: check(w=((0,),(0,),(),(0,))), results)
    rejection("direction coverage empty", lambda: audit.verify_directions([]), results)
    rejection("direction coverage omits start", lambda: audit.verify_directions([(Q(1),Q(4))]), results)
    rejection("direction coverage gap", lambda: audit.verify_directions([(Q(0),Q(1)),(Q(2),Q(4))]), results)
    rejection("direction coverage overlap", lambda: audit.verify_directions([(Q(0),Q(3)),(Q(2),Q(4))]), results)
    rejection("direction coverage stops short of pi", lambda: audit.verify_directions([(Q(0),Q(3))]), results)
    require(audit.verify_directions([(Q(2),Q(4)),(Q(0),Q(2))]) == 2,
            "complete reordered angular tiling rejected")
    results.append("complete reordered angular tiling passes")
    return results


if __name__ == "__main__":
    # Keep the exact source pin explicit; no source search code is imported.
    path = Path(__file__).with_name("cfg_k60.json")
    source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    require(source_hash == "b15251de28f6f552f4364d2170a58e923b730590d8797dfe5d09e007d2f87b2e", "source pin")
    print(json.dumps({"status": "PASS", "source_sha256": source_hash,
                      "subject_sha256": hashlib.sha256(Path(audit.__file__).read_bytes()).hexdigest(),
                      "reviewer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      "trig_oracle_samples": trig_controls(),
                      "pi_oracle": pi_control(),
                      "corner_oracle": corner_controls(),
                      "controls": failure_controls(),
                      "scope": "Finite controls and separate AI mathematical review; not full replay or formal proof."},
                     indent=2))
