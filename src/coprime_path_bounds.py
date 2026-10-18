"""Sufficient bounds for two-color coprime paths, whose lengths count edges.

Erdős–Gallai forces a monochromatic k-edge path when an induced host has
more than (k-1)*vertices edges. These bounds need not be exact thresholds.
See docs/coprime-path-structure-2026-10-18.md for proofs and limitations.
"""

import argparse
from dataclasses import asdict, dataclass
from math import isqrt
import json
from typing import Iterable, Iterator


@dataclass(frozen=True)
class GraphCounts:
    n: int
    vertices: int
    edges: int


@dataclass(frozen=True)
class PathBound:
    path_edges: int
    lower_bound: int
    upper_bound: GraphCounts | None


def _integer(value: int, name: str, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def induced_counts(
    limit: int, excluded_multiples: Iterable[int] = ()
) -> Iterator[GraphCounts]:
    """Count the retained vertices and coprime edges for every n=1..limit.

    Remove all multiples of any supplied positive divisor. Overlaps are
    counted once; odd divisors are also supported. Validation occurs when
    iteration starts. Memory is O(limit); no graph or edge list is built.
    """
    _integer(limit, "limit", 0)
    excluded = tuple(excluded_multiples)
    for divisor in excluded:
        _integer(divisor, "exclusion divisor", 1)
    excluded = tuple(sorted(set(excluded)))

    smallest_prime = list(range(limit + 1))
    for prime in range(2, isqrt(limit) + 1):
        if smallest_prime[prime] == prime:
            for multiple in range(prime * prime, limit + 1, prime):
                if smallest_prime[multiple] == multiple:
                    smallest_prime[multiple] = prime

    # multiples[d] counts earlier retained vertices divisible by d.
    multiples = [0] * (limit + 1)
    vertices = edges = 0
    for n in range(1, limit + 1):
        if not any(n % divisor == 0 for divisor in excluded):
            # Generate (d, mu(d)) for squarefree divisors of n from its
            # distinct primes, including (1,1) when n=1.
            terms = [(1, 1)]
            remainder = n
            while remainder > 1:
                prime = smallest_prime[remainder]
                terms += [(d * prime, -sign) for d, sign in terms]
                while remainder % prime == 0:
                    remainder //= prime
            edges += sum(sign * multiples[d] for d, sign in terms)
            for divisor, _ in terms:
                multiples[divisor] += 1
            vertices += 1
        yield GraphCounts(n, vertices, edges)


def density_bounds(
    path_edges: Iterable[int], limit: int, excluded_multiples: Iterable[int] = ()
) -> tuple[PathBound, ...]:
    """Return cover lower bounds and first sufficient density bounds up to limit.

    k must be at least 3. Results are sorted by distinct k. A None upper
    bound means this sufficient test found no bound within the finite range;
    it is not a nonexistence result or evidence of a path-avoiding coloring.
    """
    _integer(limit, "limit", 0)
    lengths = tuple(path_edges)
    for k in lengths:
        _integer(k, "path_edges", 3)
    lengths = sorted(set(lengths))
    found: dict[int, GraphCounts] = {}
    for counts in induced_counts(limit, excluded_multiples):
        # Larger k require a larger ratio; previously found bounds persist
        # through graph nesting even if the current density decreases.
        while len(found) < len(lengths):
            k = lengths[len(found)]
            if counts.edges <= (k - 1) * counts.vertices:
                break
            found[k] = counts
        if len(found) == len(lengths):
            break
    return tuple(PathBound(k, 4 * ((k - 1) // 2) + 1, found.get(k))
                 for k in lengths)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path_edges", type=int, nargs="+", help="target edge lengths, >=3")
    parser.add_argument("--max-n", type=int, default=1000, help="finite counting limit")
    parser.add_argument("--exclude-multiples", type=int, nargs="+", default=[30, 42, 70])
    args = parser.parse_args()
    try:
        whole = density_bounds(args.path_edges, args.max_n)
        induced = density_bounds(args.path_edges, args.max_n, args.exclude_multiples)
    except ValueError as error:
        parser.error(str(error))
    rows = []
    for full, reduced in zip(whole, induced):
        rows.append({
            "path_edges": full.path_edges,
            "lower_bound": full.lower_bound,
            "whole_graph_upper": None if full.upper_bound is None else asdict(full.upper_bound),
            "induced_upper": None if reduced.upper_bound is None else asdict(reduced.upper_bound),
        })
    print(json.dumps({
        "definition": "two edge colors; simple path length counts edges",
        "max_n": args.max_n,
        "excluded_multiples": sorted(set(args.exclude_multiples)),
        "bounds": rows,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
