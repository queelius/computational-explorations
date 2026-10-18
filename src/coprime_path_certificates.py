"""Independent, standard-library validation of coprime-path evidence.

Witness checking uses subset dynamic programming, not the search's DFS.
Formula checking recognizes simple paths structurally; a checked UNSAT proof
of any subset of these valid constraints is sufficient for an upper bound.
"""
from dataclasses import dataclass
import argparse
import gzip
import hashlib
from itertools import combinations
import json
from math import gcd
from pathlib import Path
import sys
from typing import Sequence


@dataclass(frozen=True)
class PathProblem:
    n: int
    path_edges: int

    def __post_init__(self):
        if any(type(value) is not int or value < 1
               for value in (self.n, self.path_edges)):
            raise ValueError('n and path_edges must be positive integers')

    @property
    def edges(self) -> tuple[tuple[int, int], ...]:
        return tuple(pair for pair in combinations(range(1, self.n + 1), 2)
                     if gcd(*pair) == 1)


def validate_witness(problem: PathProblem, coloring: Sequence[Sequence[int]]) -> tuple[int, int]:
    """Require a complete avoiding coloring; return each color's longest path.

    The dynamic program stores all possible endpoints of paths with each vertex
    subset. Time is O(n² 2**n), so this checker is intended for small instances.
    """
    if not isinstance(coloring, (list, tuple)):
        raise ValueError('coloring must contain explicit edge/color rows')
    assignment = {}
    for row in coloring:
        if (not isinstance(row, (list, tuple)) or len(row) != 3
                or any(type(value) is not int for value in row)):
            raise ValueError('each coloring row must contain three integers')
        a, b, color = row
        if not 1 <= a < b <= problem.n or color not in (0, 1) or (a, b) in assignment:
            raise ValueError('invalid, noncanonical, or repeated colored edge')
        assignment[a, b] = color
    if set(assignment) != set(problem.edges):
        raise ValueError('coloring must cover exactly all coprime edges')

    maxima = []
    for color in (0, 1):
        neighbors = [0] * problem.n
        for (a, b), value in assignment.items():
            if value == color:
                neighbors[a - 1] |= 1 << (b - 1)
                neighbors[b - 1] |= 1 << (a - 1)
        endpoints = [0] * (1 << problem.n)
        for vertex in range(problem.n):
            endpoints[1 << vertex] = 1 << vertex
        longest = 0
        for mask, ends in enumerate(endpoints):
            if ends:
                longest = max(longest, mask.bit_count() - 1)
            while ends:
                endpoint = ends & -ends
                ends -= endpoint
                available = neighbors[endpoint.bit_length() - 1] & ~mask
                while available:
                    next_vertex = available & -available
                    available -= next_vertex
                    endpoints[mask | next_vertex] |= next_vertex
        maxima.append(longest)
    if max(maxima) >= problem.path_edges:
        raise ValueError('coloring contains a forbidden monochromatic simple path')
    return tuple(maxima)


def validate_formula(problem: PathProblem, clauses: Sequence[Sequence[int]]) -> int:
    """Check clause semantics, independently of how constraints were found.

    Variables index lexicographically ordered coprime edges, starting at one.
    Allow only uniform-sign clauses on a simple path, plus two-literal
    tautologies used to register otherwise unconstrained variables. This does
    not assert UNSAT; a separate proof checker must establish that fact.
    """
    edges = problem.edges
    count = 0
    for clause in clauses:
        if (not isinstance(clause, (list, tuple)) or not clause
                or any(type(v) is not int or not 1 <= abs(v) <= len(edges)
                       for v in clause)):
            raise ValueError('clause contains invalid variables')
        if len(clause) == 2 and clause[0] == -clause[1]:
            continue
        if (len(clause) != problem.path_edges
                or len(set(map(abs, clause))) != len(clause)
                or len({v > 0 for v in clause}) != 1):
            raise ValueError('clause must exclude one monochromatic path')
        adjacency: dict[int, set[int]] = {}
        for variable in clause:
            a, b = edges[abs(variable) - 1]
            adjacency.setdefault(a, set()).add(b)
            adjacency.setdefault(b, set()).add(a)
        degrees = [len(neighbors) for neighbors in adjacency.values()]
        if (len(adjacency) != problem.path_edges + 1 or degrees.count(1) != 2
                or any(degree not in (1, 2) for degree in degrees)):
            raise ValueError('clause edges do not have simple-path degrees')
        visited = set()
        pending = [next(iter(adjacency))]
        while pending:
            vertex = pending.pop()
            if vertex not in visited:
                visited.add(vertex)
                pending.extend(adjacency[vertex] - visited)
        if visited != set(adjacency):
            raise ValueError('clause path is disconnected')
        count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    witness = modes.add_parser('witness', help='independently check a complete coloring')
    witness.add_argument('input', type=Path)
    formula = modes.add_parser('formula', help='check path clauses and emit DIMACS')
    formula.add_argument('input', type=Path)
    formula.add_argument('--dimacs-out', type=Path, required=True)
    args = parser.parse_args()
    try:
        opener = gzip.open if args.input.suffix == '.gz' else open
        with opener(args.input, 'rt', encoding='utf-8') as source:
            record = json.load(source)
        if not isinstance(record, dict):
            raise ValueError('evidence must be a JSON object')
        problem = PathProblem(record['n'], record['path_edges'])
        report = {'n': problem.n, 'path_edges': problem.path_edges, 'edges': len(problem.edges)}
        if args.mode == 'witness':
            report.update(witness_valid=True, longest_paths=validate_witness(problem, record['coloring']))
        else:
            clauses = record['clauses']
            count = validate_formula(problem, clauses)
            dimacs = f'p cnf {len(problem.edges)} {len(clauses)}\n'
            dimacs += ''.join(' '.join(map(str, clause)) + ' 0\n' for clause in clauses)
            data = dimacs.encode('ascii')
            with args.dimacs_out.open('xb') as target:
                target.write(data)
            report.update(formula_semantics_valid=True, unsat_checked=False,
                          path_clauses=count, clauses=len(clauses),
                          dimacs_sha256=hashlib.sha256(data).hexdigest())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
