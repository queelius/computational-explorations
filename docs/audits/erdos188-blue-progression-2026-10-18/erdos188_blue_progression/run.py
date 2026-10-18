"""Regenerate untrusted proposals and independently check every accepted leaf."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction as Q
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

from .audit import Config, InvalidCertificate, Verifier, verify_directions, SCALE

HERE = Path(__file__).resolve().parent
CFG_SHA = 'b15251de28f6f552f4364d2170a58e923b730590d8797dfe5d09e007d2f87b2e'
SEARCH_SHA = '494104edad838f4a9044d9fb8fedcbb856f39e57e29a1d66b26f60f2b4f06dcd'
_search = _verifier = None


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def initialize() -> None:
    global _search, _verifier
    cfg = HERE/'cfg_k60.json'
    source = HERE/'vendor'/'claimB_arb.py'
    if digest(cfg) != CFG_SHA or digest(source) != SEARCH_SHA:
        raise InvalidCertificate('pinned input hash mismatch')
    os.environ['V2CFG'] = str(cfg)
    sys.path.insert(0, str(source.parent))
    import claimB_arb
    _search = claimB_arb
    _verifier = Verifier(Config.from_json(json.loads(cfg.read_text())))


def work(task: tuple[int, float, float, int, int]) -> dict:
    index, lo, hi, depth, refinements = task
    pending = [(lo, hi, 0)]
    records = []
    search_failures = 0
    while pending:
        left, right, level = pending.pop()
        mid = 0.5*(left+right)
        m = _search
        out = m.stage1(left, right, mid, m.HR, m.HMAX, m.CEN, m.L, m.HH, m.P2[0], 60, depth, m.NX, m.NY, m.W0)
        if out[0] != 1:
            search_failures += 1
            if level >= refinements or not left < mid < right:
                raise InvalidCertificate(f'unresolved search box {left!r},{right!r} at level {level}')
            pending.extend([(mid, right, level+1), (left, mid, level+1)])
            continue
        codes = out[5].tolist()
        witness = tuple(v.tolist() for v in out[6:])
        # Acceptance errors abort, rather than silently refining an invalid proof.
        result = _verifier.verify((Q(left), Q(right), Q(mid)), codes, witness, 60, depth)
        hasher = hashlib.sha256()
        for array in out[5:]:
            hasher.update(len(array).to_bytes(8, 'little'))
            hasher.update(array.astype('<i8').tobytes())
        records.append(dict(result, left=str(Q(left)), right=str(Q(right)), midpoint=str(Q(mid)), refinement=level, witness_sha256=hasher.hexdigest()))
    return {'initial_index': index, 'search_failures': search_failures, 'records': records}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--intervals', type=int, default=40000)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--depth', type=int, default=14)
    parser.add_argument('--refinements', type=int, default=8)
    parser.add_argument('--pilot', type=int, default=0, help='evenly spaced initial intervals; cannot establish full coverage')
    args = parser.parse_args()
    if min(args.intervals, args.workers) <= 0 or args.pilot < 0 or args.refinements < 0:
        parser.error('invalid positive run parameters')
    args.output.mkdir(parents=True, exist_ok=True)
    initialize()
    import numpy as np
    # Exactness of floating endpoints is recovered using Fraction, and their
    # complete tiling is independently checked after all actual acceptances.
    edges = np.linspace(0.0, 3.1416, args.intervals+1).tolist()
    indices = list(range(args.intervals)) if not args.pilot else sorted(set(np.linspace(0, args.intervals-1, args.pilot, dtype=int).tolist()))
    expected = set(indices)
    started = time.monotonic()
    hashes = {name: digest(HERE/name) for name in ('audit.py','run.py','cfg_k60.json','vendor/claimB_arb.py')}
    records = []
    failures = 0
    completed = set()
    with (args.output/'intervals.jsonl').open('w') as log:
        with ProcessPoolExecutor(max_workers=args.workers, initializer=initialize) as pool:
            futures = [pool.submit(work, (i, edges[i], edges[i+1], args.depth, args.refinements)) for i in indices]
            for future in as_completed(futures):
                item = future.result()
                i = item['initial_index']
                if i in completed or i not in expected:
                    raise InvalidCertificate('unexpected/duplicate completed task')
                completed.add(i)
                records.extend(item['records'])
                failures += item['search_failures']
                log.write(json.dumps(item, sort_keys=True)+'\n')
                if len(completed) % 1000 == 0 or len(completed) == len(indices):
                    log.flush()
                    print(json.dumps({'completed_initial':len(completed),'total_initial':len(indices),'seconds':round(time.monotonic()-started,2)}), flush=True)
    if completed != expected:
        raise InvalidCertificate('incomplete task set')
    if hashes != {name:digest(HERE/name) for name in hashes}:
        raise InvalidCertificate('checker/input changed during run')
    count = None if args.pilot else verify_directions([(Q(r['left']),Q(r['right'])) for r in records])
    result = {
        'status': 'PILOT_ONLY' if args.pilot else 'FULL_COVER_VERIFIED',
        'initial_intervals':len(indices), 'certified_intervals':len(records),
        'direction_tiling_checked': count is not None,
        'leaves':sum(r['leaves'] for r in records),
        'nodes':sum(r['nodes'] for r in records),
        'search_boxes_requiring_refinement':failures,
        'maximum_refinement':max(r['refinement'] for r in records),
        'minimum_integer_margin':min(r['minimum_integer_margin'] for r in records),
        'margin_denominator':SCALE*SCALE, 'worst_j':max(r['worst_j'] for r in records),
        'elapsed_seconds':time.monotonic()-started,
        'source_hashes':hashes, 'interval_log_sha256':digest(args.output/'intervals.jsonl'),
        'parameters':{'intervals':args.intervals,'workers':args.workers,'depth':args.depth,'refinements':args.refinements,'pilot':args.pilot},
        'python':sys.version, 'dependencies':{p:importlib.metadata.version(p) for p in ('numpy','numba')},
        'claim':'For all x in R^2 and unit u, exists integer 0<=j<60 with x+j*u red in the pinned periodic coloring.',
        'trust':'Written geometry and Taylor bounds, Python integer/Fraction semantics and execution; not kernel verification or human peer review.'
    }
    (args.output/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True),flush=True)


if __name__ == '__main__':
    main()
