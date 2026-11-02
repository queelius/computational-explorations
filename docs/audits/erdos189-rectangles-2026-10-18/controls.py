#!/usr/bin/env python3
"""Meaningful mutations of the actual deposited data; no source code execution.

Copyright (c) 2026 Alexander Richard Towell. MIT license.
Substantial OpenAI Codex assistance.
"""
import io
from pathlib import Path
import sys
from typing import Callable

from audit import AuditError, Formula, check_encoding, parse_dimacs, read_points, verify_lrat


def reject(label: str, operation: Callable[[], object]) -> None:
    try:
        operation()
    except AuditError:
        print('Control PASS (rejected): ' + label, file=sys.stderr)
    else:
        raise AuditError('negative control was accepted: ' + label)


def main(directory: Path) -> None:
    with (directory/'cert180.pts').open() as stream:
        points = read_points(stream)
    with (directory/'cert180.cnf').open() as stream:
        formula = parse_dimacs(stream)
    check_encoding(points, formula)
    moved = dict(points)
    x, y = moved[90]
    moved[90] = (x+1, y)
    reject('move point 90', lambda: check_encoding(moved, formula))
    rectangle = next(clause for clause in formula.clauses if len(clause) == 4)
    indices = set(map(abs, rectangle))
    reduced = Formula(formula.variables, tuple(clause for clause in formula.clauses
                      if set(map(abs, clause)) != indices))
    reject('remove one rectangle clause pair', lambda: check_encoding(points, reduced))
    with (directory/'cert180.lrat').open() as stream:
        prefix = []
        for line in stream:
            prefix.append(line)
            tokens = line.split()
            if tokens[1] != 'd':
                break
    reject('truncate after first addition',
           lambda: verify_lrat(formula, io.StringIO(''.join(prefix))))
    tokens = prefix[-1].split()
    first_zero = tokens.index('0')
    tokens[first_zero+1] = str(10**12)
    corrupted = ''.join(prefix[:-1]) + ' '.join(tokens) + '\n'
    reject('replace a live hint with an unknown ID',
           lambda: verify_lrat(formula, io.StringIO(corrupted)))
    print('Source controls: 4/4 PASS', file=sys.stderr)


if __name__ == '__main__':
    main(Path(sys.argv[1]))
