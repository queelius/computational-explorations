"""Independently check positive certificates for coprime-path constraints.

Only standard-library code is used. No search/generator module is imported.
These certificates prove structural lemmas, not a Ramsey threshold.
"""
import argparse
from dataclasses import dataclass
from functools import lru_cache
import gzip
from itertools import combinations
import json
from math import comb, gcd
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


Edge = tuple[int, int]
Record = Mapping[str, Any]


def _integer(value: Any, name: str, minimum: int = 0,
             maximum: int | None = None) -> int:
    if (type(value) is not int or value < minimum
            or (maximum is not None and value > maximum)):
        raise ValueError(f'invalid {name}')
    return value


def _labels(value: Any, allowed: set[int], *, canonical: bool = False) -> tuple[int, ...]:
    if (not isinstance(value, (list, tuple)) or any(type(v) is not int for v in value)
            or len(set(value)) != len(value) or not set(value) <= allowed
            or (canonical and list(value) != sorted(value))):
        raise ValueError('invalid, repeated, or noncanonical vertex labels')
    return tuple(value)


@dataclass(frozen=True)
class PathTask:
    n: int
    target_edges: int

    def __post_init__(self) -> None:
        _integer(self.n, 'n', 2)
        _integer(self.target_edges, 'target_edges', 1, self.n - 1)

    @property
    def vertices(self) -> set[int]:
        return set(range(1, self.n + 1))

    @property
    def edges(self) -> set[Edge]:
        return {edge for edge in combinations(range(1, self.n + 1), 2)
                if gcd(*edge) == 1}

    def check_path(self, path: Any, excluded: Sequence[int] = ()) -> frozenset[Edge]:
        labels = _labels(path, self.vertices - set(excluded))
        if len(labels) != self.target_edges + 1:
            raise ValueError('incorrect path length')
        edges = frozenset(tuple(sorted(pair)) for pair in zip(labels, labels[1:]))
        if any(gcd(*edge) != 1 for edge in edges):
            raise ValueError('path contains a non-host edge')
        return edges


def _task(data: Record) -> PathTask:
    if not isinstance(data, dict) or data.get('status') != 'complete':
        raise ValueError('expected a complete certificate object')
    if (not isinstance(data.get('records'), list)
            or any(not isinstance(row, dict) for row in data['records'])):
        raise ValueError('expected explicit certificate records')
    return PathTask(data['n'], data['target_edges'])


def validate_cut_paths(data: Record) -> dict[str, int]:
    """Check every smaller-side cut; equal halves require both orientations."""
    task = _task(data)
    minimum = _integer(data['minimum_side'], 'minimum_side', 1, task.n // 2)
    expected = {side for size in range(minimum, task.n // 2 + 1)
                for side in combinations(range(1, task.n + 1), size)}
    count = len(expected)
    for row in data['records']:
        side = _labels(row['side'], task.vertices, canonical=True)
        if side not in expected:
            raise ValueError('duplicate or invalid cut')
        expected.remove(side)
        edges = task.check_path(row['path'])
        if any((a in side) == (b in side) for a, b in edges):
            raise ValueError('path edge does not cross its cut')
    if expected:
        raise ValueError('missing cuts')
    return {'n': task.n, 'target_edges': task.target_edges, 'minimum_side': minimum,
            'validated_cuts': count}


def has_edge_transversal(paths: Sequence[frozenset[Edge]], budget: int) -> bool:
    """Whether at most budget edges hit every set, by exhaustive branching.

    Any hitting set must select an edge of the first uncovered path. Branching
    over all of its edges is complete; memoization changes only the work done.
    """
    _integer(budget, 'edge budget')
    coverage: dict[Edge, int] = {}
    for index, path in enumerate(paths):
        for edge in path:
            coverage[edge] = coverage.get(edge, 0) | (1 << index)

    @lru_cache(None)
    def visit(uncovered: int, left: int) -> bool:
        if not uncovered:
            return True
        if not left:
            return False
        first = (uncovered & -uncovered).bit_length() - 1
        return any(visit(uncovered & ~coverage[edge], left - 1)
                   for edge in paths[first])

    return visit((1 << len(paths)) - 1, budget)


def _symmetry_classes(task: PathTask, value: Any) -> tuple[tuple[int, ...], ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError('expected symmetry classes')
    classes = tuple(_labels(group, task.vertices) for group in value)
    if (any(not group for group in classes)
            or sorted(v for group in classes for v in group) != sorted(task.vertices)):
        raise ValueError('classes must partition the vertices')
    for group in classes:
        for a, b in combinations(group, 2):
            swap = {a: b, b: a}
            for x, y in combinations(range(1, task.n + 1), 2):
                if (gcd(x, y) == 1) != (gcd(swap.get(x, x), swap.get(y, y)) == 1):
                    raise ValueError('class transposition is not a host symmetry')
    return classes


def validate_fault_paths(data: Record) -> dict[str, int]:
    """Check deletion-orbit coverage and path families immune to edge faults."""
    task = _task(data)
    removed = _integer(data['deleted_vertices'], 'deleted_vertices', 0,
                       task.n - task.target_edges - 1)
    faults = _integer(data['deleted_edges'], 'deleted_edges')
    classes = _symmetry_classes(task, data['classes'])

    def signature(deleted: Sequence[int]) -> tuple[int, ...]:
        return tuple(sum(v in group for v in deleted) for group in classes)

    expected = {signature(deleted)
                for deleted in combinations(range(1, task.n + 1), removed)}
    orbits, paths_checked = len(expected), 0
    for row in data['records']:
        deleted = _labels(row['deleted'], task.vertices, canonical=True)
        key = signature(deleted)
        if len(deleted) != removed or key not in expected:
            raise ValueError('duplicate or invalid deletion orbit')
        expected.remove(key)
        if not isinstance(row['paths'], (list, tuple)) or not row['paths']:
            raise ValueError('expected a nonempty path family')
        paths = [task.check_path(path, deleted) for path in row['paths']]
        if has_edge_transversal(paths, faults):
            raise ValueError('path family has a small edge transversal')
        paths_checked += len(paths)
    if expected:
        raise ValueError('missing deletion orbits')
    return {'n': task.n, 'target_edges': task.target_edges,
            'validated_orbits': orbits, 'covered_deletions': comb(task.n, removed),
            'validated_paths': paths_checked, 'edge_faults_tolerated': faults}


def validate_cut_extensions(data: Record) -> dict[str, int]:
    """Check crossing edges plus each distinguished edge outside a dense side."""
    task = _task(data)
    size = _integer(data['side_size'], 'side_size', 1, task.n - 2)
    minimum = _integer(data['minimum_side_edges'], 'minimum_side_edges', 0, comb(size, 2))
    edges = task.edges
    expected: set[tuple[tuple[int, ...], Edge]] = set()
    cuts = 0
    for side in combinations(range(1, task.n + 1), size):
        if sum(edge in edges for edge in combinations(side, 2)) < minimum:
            continue
        cuts += 1
        expected.update((side, edge) for edge in edges if not set(edge) & set(side))
    pairs = len(expected)
    for row in data['records']:
        side = _labels(row['side'], task.vertices, canonical=True)
        edge = _labels(row['edge'], task.vertices, canonical=True)
        key = (side, edge)
        if key not in expected:
            raise ValueError('duplicate or invalid extension case')
        expected.remove(key)
        used = task.check_path(row['path'])
        if edge not in used:
            raise ValueError('distinguished edge is not used')
        if any(pair != edge and ((pair[0] in side) == (pair[1] in side)) for pair in used):
            raise ValueError('edge is neither crossing nor distinguished')
    if expected:
        raise ValueError('missing extension cases')
    return {'n': task.n, 'target_edges': task.target_edges,
            'validated_pairs': pairs, 'qualified_cuts': cuts}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    cuts = modes.add_parser('cuts', help='check balanced-cut paths')
    cuts.set_defaults(validate=validate_cut_paths)
    faults = modes.add_parser('faults', help='check vertex/edge-deletion resilience')
    faults.set_defaults(validate=validate_fault_paths)
    extensions = modes.add_parser('extensions', help='check paths extending crossing cuts')
    extensions.set_defaults(validate=validate_cut_extensions)
    for mode in (cuts, faults, extensions):
        mode.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        opener = gzip.open if args.input.suffix == '.gz' else open
        with opener(args.input, 'rt', encoding='utf-8') as source:
            report = args.validate(json.load(source))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
