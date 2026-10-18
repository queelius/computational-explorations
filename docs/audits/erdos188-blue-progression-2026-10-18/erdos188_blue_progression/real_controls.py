"""Reject altered actual source proposals; inspect the full-run receipt.

These finite controls do not establish Claim B without the full replay.
Alexander Richard Towell, with substantial OpenAI Codex assistance.
"""
from fractions import Fraction as Q
import hashlib
import gzip
import json
from pathlib import Path
from unittest.mock import patch

from . import run
from .audit import Config, InvalidCertificate, Verifier, verify_directions


def main() -> None:
    run.initialize()
    m = run._search
    config = Config.from_json(json.loads((run.HERE/'cfg_k60.json').read_text()))
    import numpy as np
    edges = np.linspace(0.0, 3.1416, 40001).tolist()
    results = []
    positives = []

    def reject(label, action):
        try:
            action()
        except InvalidCertificate:
            results.append(label)
            return
        raise RuntimeError('negative control accepted: '+label)

    for k in (0,10000,20000,30000,39999):
        lo, hi = edges[k:k+2]
        mid = (lo+hi)/2
        out = m.stage1(lo,hi,mid,m.HR,m.HMAX,m.CEN,m.L,m.HH,m.P2[0],60,14,m.NX,m.NY,m.W0)
        if out[0] != 1:
            raise RuntimeError('positive-control search did not complete')
        codes = out[5].tolist()
        witness = tuple(v.tolist() for v in out[6:])
        box = Q(lo),Q(hi),Q(mid)
        verifier = Verifier(config)
        result = verifier.verify(box,codes,witness,60,14)
        positives.append({'initial_index':k,**result})
        def check(c=codes,w=witness,n=60,v=verifier):
            return v.verify(box,c,w,n,14)
        reject(f'{k}:missing leaf',lambda:check(c=codes[:-1]))
        reject(f'{k}:trailing leaf',lambda:check(c=codes+[0]))
        reject(f'{k}:invalid negative code',lambda:check(c=[-2]+codes[1:]))
        reject(f'{k}:invalid cell',lambda:check(w=([len(config.centres)]*len(witness[0]),*witness[1:])))
        reject(f'{k}:j=60',lambda:check(w=(witness[0],[60]*len(witness[1]),*witness[2:])))
        reject(f'{k}:insufficient j range',lambda:check(n=59))
        reject(f'{k}:wrong lattice shift',lambda:check(w=(*witness[:2],[a+100 for a in witness[2]],witness[3])))
        small = Config(config.p1,config.p2,config.centres,tuple(Q(1,100) for _ in config.radii))
        reject(f'{k}:tiny disks',lambda:check(v=Verifier(small)))
    with patch.object(run,'CFG_SHA','0'*64):
        reject('configuration hash mismatch',run.initialize)
    with patch.object(run,'SEARCH_SHA','0'*64):
        reject('generator hash mismatch',run.initialize)

    path = run.HERE/'full'/'intervals.jsonl'
    raw = path.read_bytes() if path.exists() else gzip.decompress(path.with_suffix('.jsonl.gz').read_bytes())
    summary = json.loads((run.HERE/'full'/'result.json').read_text())
    if hashlib.sha256(raw).hexdigest() != summary['interval_log_sha256']:
        raise RuntimeError('receipt hash mismatch')
    tasks = [json.loads(line) for line in raw.splitlines()]
    if sorted(t['initial_index'] for t in tasks) != list(range(40000)):
        raise RuntimeError('receipt task coverage')
    records = [r for t in tasks for r in t['records']]
    intervals = sorted((Q(r['left']),Q(r['right'])) for r in records)
    count = verify_directions(intervals)
    if count != summary['certified_intervals'] or sum(r['leaves'] for r in records) != summary['leaves']:
        raise RuntimeError('receipt count mismatch')
    if sum(r['nodes'] for r in records) != summary['nodes'] or min(r['minimum_integer_margin'] for r in records) != summary['minimum_integer_margin']:
        raise RuntimeError('receipt node/margin mismatch')
    reject('full receipt with one interior angle removed',lambda:verify_directions(intervals[:100]+intervals[101:]))
    reject('full receipt with one angle duplicated',lambda:verify_directions(intervals+[intervals[100]]))
    print(json.dumps({'status':'PASS','positive_real_certificates':positives,
        'rejected_mutations':results,'reject_count':len(results),
        'receipt_intervals':count,'receipt_sha256':hashlib.sha256(raw).hexdigest(),
        'scope':'Five actual source trees and altered witnesses; receipt aggregation checks. Not a second full replay and not a blue59 counterexample.'},indent=2))


if __name__ == '__main__':
    main()
