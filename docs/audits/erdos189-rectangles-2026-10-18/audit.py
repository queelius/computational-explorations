#!/usr/bin/env python3
"""Exact diagonal geometry and positive-hint LRAT audit; Python standard library.

Copyright (c) 2026 Alexander Richard Towell. MIT license.
Substantial OpenAI Codex assistance. See README.md for scope and trust boundary.
No source-deposit code is imported. Failures remain active under python -O.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Iterable, TextIO


class AuditError(ValueError):
    """Malformed input, unsupported proof step, or failed mathematical check."""


@dataclass(frozen=True)
class Formula:
    variables: int
    clauses: tuple[tuple[int, ...], ...]


def integer_tokens(tokens: Iterable[str]) -> list[int]:
    try:
        return [int(token) for token in tokens]
    except ValueError as error:
        raise AuditError('noninteger token') from error


def validate_clause(clause: tuple[int, ...], variables: int) -> None:
    if any(lit == 0 or abs(lit) > variables for lit in clause):
        raise AuditError('literal outside the variable domain')
    # A deliberately strict proof-language subset suffices for this deposit.
    if len({abs(lit) for lit in clause}) != len(clause):
        raise AuditError('duplicate variable or tautological clause unsupported')


def read_points(stream: TextIO) -> dict[int, tuple[int, int]]:
    points = {}
    for line in stream:
        tokens = line.split()
        if not tokens or tokens[0].startswith('#'):
            continue
        if len(tokens) != 3:
            raise AuditError('point row must have three integers')
        index, x, y = integer_tokens(tokens)
        if index in points:
            raise AuditError('duplicate point ID')
        points[index] = (x, y)
    if not points or sorted(points) != list(range(1, len(points) + 1)):
        raise AuditError('point IDs must be 1 through n, with n positive')
    if len(set(points.values())) != len(points):
        raise AuditError('coincident points')
    return points


def parse_dimacs(stream: TextIO) -> Formula:
    header = None
    clauses = []
    pending = []
    for line in stream:
        tokens = line.split()
        if not tokens or tokens[0] == 'c':
            continue
        if tokens[0] == 'p':
            if header is not None or len(tokens) != 4 or tokens[1] != 'cnf':
                raise AuditError('invalid or repeated DIMACS header')
            variables, count = integer_tokens(tokens[2:])
            if variables < 1 or count < 0:
                raise AuditError('invalid DIMACS dimensions')
            header = variables, count
            continue
        if header is None:
            raise AuditError('clauses before DIMACS header')
        for literal in integer_tokens(tokens):
            if literal:
                pending.append(literal)
            else:
                clause = tuple(pending)
                validate_clause(clause, header[0])
                clauses.append(clause)
                pending = []
    if header is None or pending or len(clauses) != header[1]:
        raise AuditError('missing header, unterminated clause, or clause-count mismatch')
    return Formula(header[0], tuple(clauses))


def diagonal_rectangles(points: dict[int, tuple[int, int]]) -> set[tuple[int, ...]]:
    """Enumerate every area-one rectangle for s = 192^(-1/4).

    Buckets use twice the midpoint and squared diagonal length divided by s^2.
    See README.md: equal diagonals give a rectangle, and area = |det(d,e)|/32.
    """
    buckets = defaultdict(list)
    for a, b in combinations(sorted(points), 2):
        x, y = points[a]
        u, v = points[b]
        dx, dy = u-x, v-y
        buckets[(x+u, y+v, dx*dx + dx*dy + dy*dy)].append((a, b, dx, dy))
    rectangles = set()
    for diagonals in buckets.values():
        for (a, b, dx, dy), (c, d, ex, ey) in combinations(diagonals, 2):
            if len({a, b, c, d}) == 4 and abs(dx*ey - dy*ex) == 32:
                rectangles.add(tuple(sorted((a, b, c, d))))
    return rectangles


def check_encoding(points: dict[int, tuple[int, int]], formula: Formula) -> int:
    if formula.variables != len(points):
        raise AuditError('point count and variable count differ')
    rectangles = diagonal_rectangles(points)
    expected = Counter({(1,): 1})
    for rectangle in rectangles:
        expected[tuple(sorted(rectangle))] += 1
        expected[tuple(sorted(-x for x in rectangle))] += 1
    actual = Counter(tuple(sorted(clause)) for clause in formula.clauses)
    if actual != expected:
        raise AuditError(
            f'geometric CNF mismatch: {sum((expected-actual).values())} missing, '
            f'{sum((actual-expected).values())} extra clauses')
    return len(rectangles)


def verify_lrat(formula: Formula, stream: TextIO) -> dict[str, int]:
    """Check every record in the positive-hint LRAT subset.

    Each hinted clause must be unit or conflicting under the negated proposed
    clause and earlier forced literals. Conflict must be the final hint.
    No original unit is assumed implicitly; all propagation is justified by
    a live clause ID. Deleted IDs cannot be used. Unsupported RAT is rejected.
    """
    database = {index: clause for index, clause in enumerate(formula.clauses, 1)}
    for clause in formula.clauses:
        validate_clause(clause, formula.variables)
    last_addition = len(database)
    finished = False
    stats = {'records': 0, 'additions': 0, 'deletion_records': 0,
             'deleted_clauses': 0, 'propagation_hints': 0, 'peak_live_clauses': len(database)}
    for line_number, line in enumerate(stream, 1):
        tokens = line.split()
        if not tokens:
            continue
        if finished:
            raise AuditError(f'line {line_number}: material after the empty clause')
        try:
            identifier = integer_tokens(tokens[:1])[0]
            if identifier < 1 or len(tokens) < 3:
                raise AuditError('malformed proof record')
            stats['records'] += 1
            if tokens[1] == 'd':
                deleted = integer_tokens(tokens[2:])
                if not deleted or deleted[-1] != 0 or any(x <= 0 for x in deleted[:-1]):
                    raise AuditError('malformed deletion list')
                for index in deleted[:-1]:
                    if index not in database:
                        raise AuditError('deletion references absent clause')
                    del database[index]
                stats['deletion_records'] += 1
                stats['deleted_clauses'] += len(deleted)-1
                continue
            if identifier <= last_addition:
                raise AuditError('addition IDs must strictly increase above original IDs')
            fields = integer_tokens(tokens[1:])
            if fields.count(0) != 2 or fields[-1] != 0:
                raise AuditError('addition needs exactly two zero terminators')
            separator = fields.index(0)
            clause = tuple(fields[:separator])
            hints = fields[separator+1:-1]
            validate_clause(clause, formula.variables)
            if not hints or any(index <= 0 for index in hints):
                raise AuditError('missing positive hints or unsupported RAT step')
            values = [0] * (formula.variables + 1)
            for literal in clause:
                values[abs(literal)] = -1 if literal > 0 else 1
            conflict = False
            for position, index in enumerate(hints):
                if index not in database:
                    raise AuditError('hint references absent clause')
                unit = 0
                for literal in database[index]:
                    value = values[abs(literal)] * (1 if literal > 0 else -1)
                    if value > 0:
                        raise AuditError('hinted clause is already satisfied')
                    if value == 0:
                        if unit:
                            raise AuditError('hinted clause is not unit or conflicting')
                        unit = literal
                stats['propagation_hints'] += 1
                if unit == 0:
                    if position != len(hints)-1:
                        raise AuditError('unused hints after conflict')
                    conflict = True
                else:
                    values[abs(unit)] = 1 if unit > 0 else -1
            if not conflict:
                raise AuditError('hints do not establish contradiction')
            database[identifier] = clause
            last_addition = identifier
            stats['additions'] += 1
            stats['peak_live_clauses'] = max(stats['peak_live_clauses'], len(database))
            if not clause:
                finished = True
        except AuditError as error:
            raise AuditError(f'line {line_number}: {error}') from error
    if not finished:
        raise AuditError('proof ended without a derived empty clause')
    stats['final_clause_id'] = last_addition
    stats['final_live_clauses'] = len(database)
    return stats


def file_digest(path: Path) -> str:
    digest = sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certdir', type=Path, help='directory with cert180.pts/.cnf/.lrat')
    args = parser.parse_args()
    started = perf_counter()
    try:
        with (args.certdir/'cert180.pts').open() as stream:
            points = read_points(stream)
        with (args.certdir/'cert180.cnf').open() as stream:
            formula = parse_dimacs(stream)
        rectangle_count = check_encoding(points, formula)
        geometry_seconds = perf_counter()-started
        print(f'Geometry PASS: {len(points)} points, {rectangle_count} rectangles, '
              f'{len(formula.clauses)} clauses', file=sys.stderr, flush=True)
        proof_started = perf_counter()
        with (args.certdir/'cert180.lrat').open() as stream:
            statistics = verify_lrat(formula, stream)
        result = {'status': 'PASS', 'points': len(points), 'rectangles': rectangle_count,
                  'clauses': len(formula.clauses), 'proof': statistics,
                  'geometry_seconds': geometry_seconds,
                  'proof_seconds': perf_counter()-proof_started,
                  'inputs_sha256': {name: file_digest(args.certdir/name) for name in
                                    ('cert180.pts', 'cert180.cnf', 'cert180.lrat')}}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (AuditError, OSError) as error:
        print(f'AUDIT FAIL: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
