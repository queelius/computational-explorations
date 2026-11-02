# Preserved auxiliary research

These notes and selected complete certificates originated in the October 18,
2026 investigation. They were promoted from local agent storage on October 20
so future work can inspect them. The original dates describe private work,
not established public disclosure dates. `import.json` records byte identity.

The main proof of `P_cop(9) = 17` is already in
[`docs/coprime-path-nine-resolution-2026-10-18.md`](../../../../docs/coprime-path-nine-resolution-2026-10-18.md).
Neither auxiliary result below is a dependency of that proof. Historical
notes saying the threshold is unresolved predate its resolution.

## Endpoint constraint

[`g17-endpoint-five.md`](g17-endpoint-five.md) records a necessary condition
under a hypothetical avoiding coloring. The complete cut archive covers
30,793 host orbits: 30,749 direct paths and 44 exceptions. A second archive
contains 1,079 path-forcing implications and explicit contradictions for
all 44 exceptions.

The original note's `attempts/009-...` and `attempts/012-...` references now
resolve to the correspondingly numbered directories beside this README.
Generator code and partial searches remain local historical scratch; the
complete positive witnesses and replay scripts are retained here.

From this directory, run with normal Python assertions enabled:

```sh
python 009-near-extremal-structure/validate_endpoint_cuts.py
python 009-near-extremal-structure/test_validation.py
python 012-endpoint-forced-edges/validate.py
python 012-endpoint-forced-edges/test_validation.py
```

Expected: 30,793 cut orbits, 44 exceptions, 44 replayed contradictions,
1,079 implications, and 3 + 7 regression tests. These are preserved
exploratory validators: they use `assert`, so **do not use `python -O`**.
They are not the hardened independent checkers in `src/`, and their replay
does not establish the full mathematical deduction or a novelty claim.

## Matching constraint

[`g17-matching-five.md`](g17-matching-five.md) gives a written Tutte–Berge
argument: a 17-vertex graph with at least 42 edges and at least five edges
after each four-vertex deletion has matching number at least five.
The source of the standard matching theorem is credited in the note.
The note is retained for further review; no new human or formal verification
is asserted by this import.

## Failed approaches worth retaining

Bounded SAT searches did not provide an upper-bound certificate. The claim
that every six/eight crossing graph contains the required path was false;
the 44 exceptions led to the subsequent path-forcing argument. A numerical
BGLS relaxation left slack and its provisional exclusions were never promoted.
One intermediate propagation archive confused complete case visitation with
complete proof. Only the final complete archive is included here.

The infinite odd-path family, a shorter entirely analytic host argument,
and novelty of the asymptotic refinement remain open research tasks.
No failed search is evidence of nonexistence.
