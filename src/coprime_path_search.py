"""Bounded lazy SAT search for coprime paths, with portable proof artifacts."""
import argparse
from dataclasses import dataclass
from enum import Enum
import gzip
import hashlib
import json
import math
from pathlib import Path
from threading import Timer
import time

from pysat.solvers import Glucose4

from coprime_path_certificates import PathProblem


class SearchStatus(Enum):
    SAT = 'sat'
    UNSAT = 'unsat'
    INCONCLUSIVE = 'inconclusive'


@dataclass(frozen=True)
class PathSearchResult:
    status: SearchStatus
    clauses: tuple[tuple[int, ...], ...]
    coloring: tuple[tuple[int, int, int], ...] | None
    proof: tuple[str, ...] | None
    rounds: int
    elapsed_seconds: float


def solve_path_problem(problem: PathProblem, *, seconds: float = 600,
                       max_rounds: int | None = None) -> PathSearchResult:
    """Add valid path exclusions until a witness, UNSAT, or a limit is reached.

    DFS separates a candidate coloring from the valid colorings. The independent
    checker uses a different, subset-DP algorithm. UNSAT is a solver result until
    both clause semantics and its DRAT proof have been checked separately.
    The time budget covers solving and separation, not artifact serialization.
    """
    if (type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0):
        raise ValueError('seconds must be a finite nonnegative number')
    if max_rounds is not None and (type(max_rounds) is not int or max_rounds < 0):
        raise ValueError('max_rounds must be a nonnegative integer or None')
    started = time.monotonic()
    deadline = started + seconds
    edges = problem.edges
    variables = {edge: index + 1 for index, edge in enumerate(edges)}
    clauses = [[len(edges), -len(edges)]] if edges else []
    rounds = 0

    def result(status, coloring=None, proof=None):
        return PathSearchResult(status, tuple(map(tuple, clauses)), coloring,
                                proof, rounds, time.monotonic() - started)

    def find_path(colors, color):
        adjacency = [[] for _ in range(problem.n + 1)]
        for (a, b), value in zip(edges, colors):
            if value == color:
                adjacency[a].append(b)
                adjacency[b].append(a)
        failed = set()

        def extend(path, used):
            if time.monotonic() >= deadline:
                raise TimeoutError
            if len(path) == problem.path_edges + 1:
                return path
            state = (used, path[-1])
            if state in failed:
                return None
            for vertex in adjacency[path[-1]]:
                if not used & (1 << vertex):
                    found = extend(path + [vertex], used | (1 << vertex))
                    if found is not None:
                        return found
            failed.add(state)
            return None

        for vertex in range(1, problem.n + 1):
            found = extend([vertex], 1 << vertex)
            if found is not None:
                return found
        return None

    if time.monotonic() >= deadline:
        return result(SearchStatus.INCONCLUSIVE)
    with Glucose4(bootstrap_with=clauses, with_proof=True) as solver:
        timer = Timer(max(0, deadline - time.monotonic()), solver.interrupt)
        timer.daemon = True
        timer.start()
        try:
            while max_rounds is None or rounds < max_rounds:
                if time.monotonic() >= deadline:
                    break
                sat = solver.solve_limited(expect_interrupt=True)
                if sat is None:
                    break
                if sat is False:
                    return result(SearchStatus.UNSAT, proof=tuple(solver.get_proof()))
                positive = {literal for literal in solver.get_model() if literal > 0}
                colors = [int(index + 1 in positive) for index in range(len(edges))]
                paths = [path for color in (0, 1)
                         if (path := find_path(colors, color)) is not None]
                if not paths:
                    coloring = tuple((a, b, c) for (a, b), c in zip(edges, colors))
                    return result(SearchStatus.SAT, coloring=coloring)
                for path in paths:
                    positive_clause = [variables[tuple(sorted(pair))]
                                       for pair in zip(path, path[1:])]
                    for clause in (positive_clause, [-v for v in positive_clause]):
                        solver.add_clause(clause)
                        clauses.append(clause)
                rounds += 1
        except TimeoutError:
            pass
        finally:
            timer.cancel()
            timer.join()
    return result(SearchStatus.INCONCLUSIVE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('n', type=int)
    parser.add_argument('path_edges', type=int)
    parser.add_argument('--seconds', type=float, default=600)
    parser.add_argument('--max-rounds', type=int)
    parser.add_argument('--output', type=Path, required=True, help='new artifact directory')
    args = parser.parse_args()
    try:
        problem = PathProblem(args.n, args.path_edges)
        args.output.mkdir(parents=True, exist_ok=False)
        found = solve_path_problem(problem, seconds=args.seconds, max_rounds=args.max_rounds)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    identity = {'n': problem.n, 'path_edges': problem.path_edges}
    files = {}
    if found.coloring is not None:
        files['witness.json'] = (json.dumps({**identity, 'coloring': found.coloring}, indent=2) + '\n').encode()
    else:
        formula = json.dumps({**identity, 'clauses': found.clauses}, separators=(',', ':')).encode()
        files['formula.json.gz'] = gzip.compress(formula, mtime=0)
    if found.proof is not None:
        files['proof.drat.gz'] = gzip.compress(('\n'.join(found.proof) + '\n').encode(), mtime=0)
    for name, data in files.items():
        (args.output / name).write_bytes(data)
    summary = {**identity, 'solver_status': found.status.value,
               'rounds': found.rounds, 'elapsed_seconds': found.elapsed_seconds,
               'clauses': len(found.clauses), 'seconds_budget': args.seconds,
               'max_rounds': args.max_rounds,
               'files_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
    (args.output / 'search.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))
    return int(found.status is SearchStatus.INCONCLUSIVE)


if __name__ == '__main__':
    raise SystemExit(main())
