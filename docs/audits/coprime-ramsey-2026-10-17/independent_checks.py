"""Reproduce the audit probes and NEW lower-bound witnesses, not historical runs.

Run from any directory with the repository's python-sat dependency installed.
Writes JSON evidence beside this file. Does not modify research implementations.
"""

import importlib.metadata
import json
import math
import platform
import subprocess
import sys
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from coprime_ramsey_sat import (  # noqa: E402
    check_extension_unsat,
    encode_rcop_sat,
    validate_avoiding_coloring,
)
from coprime_ramsey_variants import count_avoiding_colorings_sat  # noqa: E402


def write_json(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2) + "\n")


def primes_through(n):
    return [p for p in range(2, n + 1)
            if all(p % d for d in range(2, math.isqrt(p) + 1))]


def check_and_save(n, k, colors, rank, color_function, construction):
    """Independently enumerate all relevant tuples; do not use repo validators."""
    primes = primes_through(n)
    assert 1 + len(primes) == rank
    prime_indices = {p: i + 1 for i, p in enumerate(primes)}
    labels = {1: 0}
    labels.update({v: prime_indices[next(p for p in primes if v % p == 0)]
                   for v in range(2, n + 1)})
    coloring = {}
    for a, b in combinations(range(1, n + 1), 2):
        if math.gcd(a, b) == 1:
            assert labels[a] != labels[b]
            color = color_function(labels[a], labels[b])
            assert type(color) is int and 0 <= color < colors
            coloring[a, b] = color
    checked = 0
    for vertices in combinations(range(1, n + 1), k):
        edges = list(combinations(vertices, 2))
        if all(math.gcd(a, b) == 1 for a, b in edges):
            checked += 1
            assert len({coloring[e] for e in edges}) > 1, vertices
    record = dict(n=n, forbidden_clique_size=k, colors=colors,
                  construction=construction, edges=len(coloring),
                  cliques_checked=checked, valid=True,
                  provenance="New audit construction; not an original SAT witness",
                  coloring=[[a, b, c] for (a, b), c in sorted(coloring.items())])
    filename = f"witness-n{n}-k{k}-c{colors}.json"
    write_json(filename, record)
    return {key: value for key, value in record.items() if key != "coloring"} | {
        "file": filename}


def main():
    if not __debug__:
        raise RuntimeError("Run without -O: this audit requires assertion checks.")
    # A C5 edge coloring supplies a triangle-avoiding K5 coloring.
    witnesses = [check_and_save(
        10, 3, 2, 5, lambda a, b: int((b - a) % 5 not in (1, 4)),
        "C5 red edges and its complement; least-prime-divisor pullback")]

    # Paley(17) and its complement both have clique number three.
    residues = {x * x % 17 for x in range(1, 17)}
    witnesses.append(check_and_save(
        58, 4, 2, 17, lambda a, b: int((b - a) % 17 not in residues),
        "Quadratic-residue coloring of K17; least-prime-divisor pullback"))

    # F16 = F2[x]/(x^4+x+1); exponents modulo 3 partition nonzero
    # differences into three size-five classes. Check every triangle below.
    exponents = {}
    value = 1
    for exponent in range(15):
        assert value not in exponents
        exponents[value] = exponent
        value <<= 1
        if value & 16:
            value ^= 0b10011
    assert value == 1 and set(exponents) == set(range(1, 16))
    witnesses.append(check_and_save(
        52, 3, 3, 16, lambda a, b: exponents[a ^ b] % 3,
        "F16 nonzero-difference exponent classes modulo 3; prime-label pullback"))

    solver, edge_variables, _ = encode_rcop_sat(7, 3)
    try:
        target_sat = solver.solve()
        assert target_sat
        model = set(solver.get_model())
        valid = {edge: int(var not in model) for edge, var in edge_variables.items()}
    finally:
        solver.delete()
    sampled = check_extension_unsat(6, 7, 3, num_seeds=1)
    probes = {
        "sampled_extension_6_to_7_one_seed": list(sampled),
        "direct_target_n7_sat": target_sat,
        "empty_coloring_accepted": validate_avoiding_coloring(7, 3, {}),
        "out_of_palette_coloring_accepted": validate_avoiding_coloring(
            7, 3, {edge: color + 2 for edge, color in valid.items()}),
        "n2_triangle_avoiding_count_actual": count_avoiding_colorings_sat(2, 3),
        "n2_triangle_avoiding_count_expected": 2,
        "n8_n9_n10_n11_counts": {
            str(n): count_avoiding_colorings_sat(n, 3) for n in (8, 9, 10, 11)},
        "n11_edge_count": sum(math.gcd(a, b) == 1
                              for a, b in combinations(range(1, 12), 2)),
    }
    result = {
        "head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": platform.python_version(),
        "python_sat": importlib.metadata.version("python-sat"),
        "witnesses": witnesses,
        "probes": probes,
        "scope": "Lower-bound witnesses and diagnostic probes; no upper SAT proof certificates",
    }
    write_json("independent-checks.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
