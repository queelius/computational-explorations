# Coprime Ramsey repair validation

Date: **2026-10-17**. Base commit: `f5f43ddf6df291742c029fd073f6e99034a5fb85`.
These are working-tree repairs following the
[historical audit](coprime-ramsey-citation-audit.md), not a published release.
The original audit artifacts retain their pre-repair observations and hashes.

## Changes and compatibility

- `check_extensions` separates an extensible witness, exhaustive failure, and
  an inconclusive sample. The tuple wrapper remains available, but false now
  means **not proved UNSAT**, not necessarily SAT.
- Full-witness validation requires all and only canonical coprime edges and
  binary integer colors. Missing, extra, reversed, or invalid-palette entries
  fail validation before clique checks.
- `count_avoiding_colorings` includes unconstrained variables and reports
  exhaustion. Exact integer and density helpers raise
  `IncompleteEnumerationError` when enumeration is truncated; callers can
  inspect its `.result` or use the structured counting API directly.
- CLI summaries label unknown thresholds as undetermined, correct classical
  comparisons, and reference the dated evidence instead of printing stale
  static conclusions. `python-sat` is now a declared dependency.

The [correction notice](coprime-ramsey-corrections.md) explains the mathematical
and archival changes. Original cited paper files were preserved. Current
summaries and the E-JC manuscript distinguish proofs from historical reports.

## Verification

**124 tests passed in 36.03 seconds**, including all three `TestRCop4` cases.
Coverage of the two repaired modules was **91%** overall: **88%** for
`coprime_ramsey_sat` and **96%** for `coprime_ramsey_variants`. These are focused
line-coverage figures; the existing coverage configuration excludes `main`
bodies, which are exercised by separate CLI regression tests.

Run from the repository root with Python 3.10.20 and the recorded dependencies:

```bash
COVERAGE_FILE=/tmp/coprime-repair.coverage timeout 240s python -m pytest \
  tests/test_coprime_evidence.py tests/test_coprime_ramsey_sat.py \
  tests/test_coprime_ramsey_variants.py tests/test_nt_graph_ramsey.py::TestRGCD \
  --timeout=30 --cov=coprime_ramsey_sat --cov=coprime_ramsey_variants \
  --cov-report=term-missing --cov-report=json:/tmp/coprime-repair-coverage.json \
  --junitxml=/tmp/coprime-repair-pytest.xml --durations=10 -q
```

The regression suite was observed failing before the relevant fixes. It covers
the concrete satisfiable-target/failed-seed counterexample, zero budgets,
exhaustion exactly at the cap, returned witnesses, malformed inputs,
unconstrained edge counts, and incomplete density calculations.

An independent read-only review found no remaining issues in the repaired
scope. Separately implemented brute-force checks agreed with counts for
`n=0..6, k=2..5` across count caps, and with exhaustive extensions for base
`n=2..6, k=2..5`. The final CLI changes also passed review. The E-JC manuscript
compiled successfully in a temporary directory; `git diff --check` was clean.

**Full-suite limitation:** `timeout 180s python -m pytest -q` exited 2 during
collection. The pre-existing nested f-string at `src/synthesis.py:941` is a
syntax error under Python 3.10, the declared minimum. This unrelated module
was left unchanged. Scikit-learn was installed in the validation environment
after the first baseline attempt found it missing. No full-suite pass is claimed.

## Evidence and local bundle

[Repair artifacts](audits/coprime-ramsey-repair-2026-10-17/) contain the test
log, JUnit report, coverage JSON, full-suite error, dependency versions, and a
SHA-256 manifest of the source, tests, documentation, and saved evidence.
The [pinned requirements](audits/coprime-ramsey-repair-2026-10-17/requirements.txt)
support the focused command; they are not a full-repository dependency lock.

A local draft bundle is prepared at
`dist/coprime-ramsey-repair-2026-10-17.tar.gz`. It contains the three relevant
Python modules, selected tests, configuration, correction and validation
records, and the earlier audit witnesses. It is a reproducibility subset,
not a full repository release. Its manifest identifies the exact included
files. No Git tag, GitHub release, new DOI, commit, or push accompanies it.

Publishing still requires selecting the intended public commit range; local
HEAD contains changes beyond public main. Remaining research work includes
the two longer path reproductions, solver certificate preservation, and Lean
definition/proof repairs. Seed/model caps limit enumeration, not the duration
of individual SAT calls; the shell timeout bounds the verification run.
