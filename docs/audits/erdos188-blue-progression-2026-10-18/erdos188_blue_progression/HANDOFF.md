# Claim B audit handoff

**Established:** Crocker’s pinned periodic coloring has no all-blue sixty-term
unit-spaced progression, for every position and direction. The independently
implemented integer acceptance test verified **147,421,290 closed squares** in
**40,198 angular intervals**, with **150,133,030 tree nodes**. Exact angle tiling
covers a complete half-circle; direction reversal covers the rest. Combined
with the separate Claim A audit, this corroborates the source upper bound
`K_* <=60`. No new coloring or Ramsey bound is claimed; the lower bound is
outside this audit.

Full run: 165.23 seconds on eight worker processes, 40,000 initial intervals,
198 failed search boxes replaced by children, maximum angular refinement 5.
The strict corner-test minimum is exactly
`42717995227634795 / 1208925819614629174706176 >0`.
This is **not** the same margin quantity as the source’s Arb center test.

## Reproduce

```sh
python -m pip install -r docs/audits/erdos188-blue-progression-2026-10-18/erdos188_blue_progression/requirements.txt
PYTHONPATH=docs/audits/erdos188-blue-progression-2026-10-18 python -m erdos188_blue_progression.run --workers 8 --output /tmp/erdos188-blue-replay
```

Expected: `FULL_COVER_VERIFIED`, 40,198 intervals, 147,421,290 leaves, exact
direction tiling true. The ordinary unit suite uses only the standard library:

```sh
PYTHONPATH=docs/audits/erdos188-blue-progression-2026-10-18 python -m unittest erdos188_blue_progression.test_audit
PYTHONPATH=docs/audits/erdos188-blue-progression-2026-10-18 python -O -m erdos188_blue_progression.reviewer_checks
PYTHONPATH=docs/audits/erdos188-blue-progression-2026-10-18 python -m erdos188_blue_progression.real_controls
```

Twenty unit tests pass normally and with `-O`; statement/branch coverage of
`audit.py` is 100%. The separate AI reviewer checked 138 trig cases, an independent
pi identity, 108 exact rational corner cases and 24 control groups. Forty-four
mutations/binding/coverage controls reject, including altered actual generated
trees, out-of-range progression indices, incorrect lattice translates, missing
angles, wrong hashes and reduced disks. Rejecting a j<59 certificate here is
not by itself a counterexample for 59 points. Coverage and finite tests are not
proofs of general implementation soundness.

## Trust and preserved evidence

The mathematical claim follows from the written reduction in README.md and
the full finite execution. It trusts ordinary Euclidean analysis, Taylor’s
theorem, Python integers/Fractions and the execution environment. It is not
Lean/kernel verification or human peer review. The source search is reused
only to propose witnesses; its floats, success status and Arb acceptor do not
establish acceptance. The source already had several checkers, including an
integer polygon checker. Our work is diverse external corroboration, not a
claim that the original proof was missing.

Witnesses are regenerated in a full replay. The compressed per-interval log
contains hashes, counts and margins, not all 147 million witness records, and is
not independently sufficient as a proof certificate. `source-pins.json`,
`full/result.json`, `full/storage.json`, `review.md`, and the test/control logs
record the exact dependencies and checks. The ZIP was only fetched in selected
ranges; no full-archive checksum verification is claimed.

Archive base: `66f660c657488a2d5f07828ec71eb11288888a66`.
Destination base: `8bda81e8d3f867bb1450b0e492592164416ba98f`.
Start: 2026-10-18 10:06:20 UTC; setup completed within 10 minutes. Mathematical
execution finished 10:17 UTC; the remaining work is verification/publication.
The only issue found was prose confusing a decimal endpoint with its exact
binary float; this was corrected without changing the checked arithmetic.

Credit: Alexander Richard Towell; substantial OpenAI Codex assistance,
including one separately tasked AI reviewer. Construction: Carson Crocker,
with the Currier–Mody–Xie–Zhang framework and Gabriel Currier’s variable-cell
suggestion. Original source files retain CC BY4.0 attribution.

Publication and external acceptance are recorded by the hosting PR. The local
research archive separately retains the original visit clock and submission
receipt. No subsequent research cycle is implied by this packet.

Public packaging note: reproduction paths above are adapted to this repository.
The reviewed README hash in review.md refers to the preserved research-workspace
version; the mathematical text and audit.py/run.py are unchanged.
