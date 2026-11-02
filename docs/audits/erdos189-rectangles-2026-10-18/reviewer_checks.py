#!/usr/bin/env python3
"""Reproduce the one independent reviewer's bounded checks.

Usage: python reviewer_checks.py PATH_TO_CERT_DIRECTORY

Preserves the independent side enumeration, the 5,868-trace two-variable
semantic oracle, and the ten additional boundary controls executed during
the review. See review.md for the read set, commands, results, and limits.
No source-deposit implementation is imported. Standard library only.

Copyright (c) 2026 Alexander Richard Towell. MIT license.
Substantial OpenAI Codex assistance; AI review is not human peer review.
"""
from __future__ import annotations

import argparse
import io
import json
from itertools import combinations, permutations, product
from pathlib import Path
from typing import Iterator

from audit import AuditError, Formula, diagonal_rectangles, read_points, verify_lrat


def side_rectangles(points: dict[int, tuple[int, int]]) -> set[tuple[int, ...]]:
    """Independent construction using perpendicular adjacent sides.

    Twice their inner product, after omitting the positive common scale,
    is 2*ux*vx + ux*vy + uy*vx + 2*uy*vy. Unit area requires side determinant
    16. No equal-diagonal or midpoint buckets are used here.
    """
    coordinate_to_id = {xy: i for i, xy in points.items()}
    answer = set()
    ids = sorted(points)
    for a in ids:
        ax, ay = points[a]
        for b, c in combinations((i for i in ids if i != a), 2):
            bx, by = points[b]
            cx, cy = points[c]
            ux, uy = bx-ax, by-ay
            vx, vy = cx-ax, cy-ay
            if 2*ux*vx + ux*vy + uy*vx + 2*uy*vy != 0:
                continue
            if abs(ux*vy - uy*vx) != 16:
                continue
            d = coordinate_to_id.get((bx+cx-ax, by+cy-ay))
            if d is not None:
                answer.add(tuple(sorted((a, b, c, d))))
    return answer


def check_geometry(certdir: Path) -> dict[str, int]:
    with (certdir/'cert180.pts').open() as stream:
        deposited = read_points(stream)
    lattice = {i: xy for i, xy in enumerate(product(range(-5, 6), repeat=2), 1)}
    counts = {}
    for name, points in [('deposited', deposited), ('full_11x11_lattice', lattice)]:
        side = side_rectangles(points)
        diagonal = diagonal_rectangles(points)
        if side != diagonal:
            raise RuntimeError((name, side-diagonal, diagonal-side))
        counts[name] = len(side)
    return counts


class _CandidateConsumed(Exception):
    """The verifier requested another record after accepting this candidate."""


def _candidate_stream(line: str) -> Iterator[str]:
    yield line
    raise _CandidateConsumed


def candidate_is_accepted(formula: Formula, line: str) -> bool:
    """Observe one accepted step without requiring a complete refutation.

    The original inline run recognized the final missing-empty-clause error
    message. This typed sentinel observes the same step boundary without
    coupling the saved oracle to diagnostic wording. It intentionally uses
    verify_lrat's existing record iterator and does not modify that verifier.
    """
    try:
        verify_lrat(formula, _candidate_stream(line))
    except _CandidateConsumed:
        return True
    except AuditError:
        return False
    raise RuntimeError('verifier returned without consuming the candidate sentinel')


def check_small_semantic_oracle() -> dict[str, int]:
    """Exhaust all distinct-ID hint orderings for the stated small domain.

    Original formulas are satisfiable, two-variable formulas containing one
    to three distinct nonempty, nontautological clauses. Every candidate
    nontautological clause, including empty, is checked against all models.
    This does not exhaust multi-addition or deletion traces.
    """
    clauses = [tuple(x for x in vals if x) for vals in product((0, 1, -1), (0, 2, -2))]
    assignments = list(product((False, True), repeat=2))

    def holds(clause: tuple[int, ...], assignment: tuple[bool, ...]) -> bool:
        return any(assignment[abs(l)-1] == (l > 0) for l in clause)

    checked = accepted = 0
    for count in range(1, 4):
        for originals in combinations(clauses[1:], count):
            models = [a for a in assignments if all(holds(c, a) for c in originals)]
            if not models:
                continue
            formula = Formula(2, originals)
            for candidate in clauses:
                entailed = all(holds(candidate, a) for a in models)
                for length in range(1, count+1):
                    for hints in permutations(range(1, count+1), length):
                        checked += 1
                        line = ' '.join(map(str, (count+1, *candidate, 0, *hints, 0)))+'\n'
                        if candidate_is_accepted(formula, line):
                            accepted += 1
                            if not entailed:
                                raise RuntimeError(('unsound', originals, candidate, hints))
    return {'traces': checked, 'accepted_additions': accepted,
            'nonentailed_acceptances': 0}


def check_boundary_controls() -> list[str]:
    """The ten supplementary acceptance/rejection fixtures from the review."""
    checks = {
        'empty_original_clause': (
            Formula(1, ((),)), '2 0 1 0\n', True),
        'invalid_deletion_zero_inside': (
            Formula(1, ((1,), (-1,))), '2 d 1 0 2 0\n', False),
        'duplicate_deletion': (
            Formula(1, ((1,), (-1,))), '2 d 1 1 0\n', False),
        'absent_deletion': (
            Formula(1, ((1,), (-1,))), '2 d 99 0\n', False),
        'reuse_deleted_addition_id': (
            Formula(2, ((1, 2), (-1, 2), (1, -2), (-1, -2))),
            '5 2 0 1 2 0\n5 d 5 0\n5 2 0 1 2 0\n', False),
        'tautological_added_clause': (
            Formula(1, ((1,), (-1,))), '3 1 -1 0 1 2 0\n', False),
        'duplicate_added_variable': (
            Formula(1, ((1,), (-1,))), '3 1 1 0 1 2 0\n', False),
        'already_satisfied_hint': (
            Formula(1, ((1,),)), '2 -1 0 1 0\n', False),
        'blank_lines_after_empty': (
            Formula(1, ((1,), (-1,))), '3 0 1 2 0\n\n', True),
        'empty_clause_without_hints': (
            Formula(1, ((),)), '2 0 0\n', False),
    }
    passed = []
    for name, (formula, proof, expected) in checks.items():
        try:
            verify_lrat(formula, io.StringIO(proof))
            actual = True
        except AuditError:
            actual = False
        if actual != expected:
            raise RuntimeError((name, actual, expected))
        passed.append(name)
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certdir', type=Path)
    args = parser.parse_args()
    results = {
        'geometry': check_geometry(args.certdir),
        'semantic_oracle': check_small_semantic_oracle(),
        'boundary_controls': check_boundary_controls(),
        'status': 'PASS',
    }
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
