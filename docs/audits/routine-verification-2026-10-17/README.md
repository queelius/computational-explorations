# Routine Verification Assessment — 2026-10-17

This assessment follows the [coprime Ramsey release](../../coprime-ramsey-release.md).
It adds verification infrastructure; it does not replace that release's evidence
or claim that every research result has been checked. Reproduction commands are
in [Running Verification](../../verification.md).

## Historical paper notices

Dated correction notices are published on Zenodo records
[19058647](https://zenodo.org/records/19058647) and
[20636188](https://zenodo.org/records/20636188). Each links the immutable
correction notice and software DOI
[10.5281/zenodo.23433640](https://doi.org/10.5281/zenodo.23433640).

Public API readback confirmed unchanged DOI identities, file names, sizes,
checksums, and every metadata field except description. Original descriptions
remain below the notices. [The structured record](zenodo-metadata-update.json)
contains before/after descriptions and file checksums. Original paper files and
the `coprime-ramsey-2026.10.17` tag were not replaced.

## Independent witnesses and focused coverage

The standard-library checker validates all three saved witnesses under
`python -I -S -O`, recomputing 42, 6,684, and 49,815 forbidden-size cliques
respectively. [Results](witness-verification.json) include the complete edge
counts. The checker has 54 tests covering malformed inputs, direct model
construction, exact edge coverage, palette validity, monochromatic cliques,
batch failure reporting, and operation without site packages or assertions.

All 330 focused tests pass on Python 3.10.20 (112.74s) and 3.13.15 (98.47s)
against the pinned March snapshot. This includes the 89 perfectness tests after
the cycle-search repair below. Combined measured coverage is 85%; the checker
is 99% and perfectness utilities are 95%. Logs: [3.10](focused-tests.txt),
[3.13](focused-tests-python313.txt). The measured modules cover
the SAT implementation, variants, synthesis, independent checker, and
perfectness utilities.
[Coverage details](focused-coverage.json) retain missing-line information.
The main gaps are the synthesis report renderer and parts of the experimental
extension search. Existing coverage configuration excludes `main` and
`run_experiments`; subprocess CLI execution is not included in the percentage.
No broad-suite coverage percentage or Lean verification is claimed.

## Geometry timeout diagnosis

The earlier four-worker release run stopped at a shared geometry fixture.
An isolated baseline reproduced the required outcomes: 16 tests passed, with
the two relevant fixtures taking 35.97 and 27.66 seconds. Profiling five
n=9 optimization trials attributed 0.396 of 0.613 seconds to duplicate-point
checks and 0.119 seconds to unit-distance counting.

Replacing those Python pair loops with SciPy pair-distance calculations kept
search budgets, seeds, and success assertions unchanged. Boundary tests cover
strict distance tolerances, empty/single-point inputs, and nonpositive minimum
separation. All 143 geometry tests passed in 100.54 seconds; the same two
fixtures took 21.70 and 14.26 seconds. These measurements diagnose overhead,
not a portable runtime guarantee. CI uses two workers and one numerical-library
thread per worker to limit contention.

## Broader assessment and selection

The first attempt was incomplete: 2,716 tests passed, 17 historical-data
assertions failed, and one worker was lost in the exhaustive algorithm
benchmark. Adding eight checker tests while that run was active also invalidated
replacement-worker collection. [The initial report](initial-assessment.json)
preserves the failures. Subsequent runs keep the test tree fixed.

The data failures came from using a June database with assertions about the
March corpus. CI now pins the March 16 upstream commit
`19cb6116c2c194240e8f46c973e13a161f7987b2`. All 91 historical analysis tests
pass against that snapshot without changing their assertions. This does not
establish compatibility of those fixed-count assertions with current data.

A second attempt passed 2,778 tests before a worker failed in
`TestFindOddHole::test_no_odd_hole[15]`. It was interrupted for diagnosis.
The DFS rejected chords only after constructing a complete cycle, so it
enumerated paths that could never become induced cycles. It now rejects
such paths immediately, permitting the edge to the start only when closing
the cycle. No test was excluded for this failure. A deterministic recursion
budget test failed before the fix; an independent degree oracle checks all
1,024 five-vertex graphs, and positive tests cover five- and seven-cycles.
All 89 perfectness tests then passed in 4.66 seconds with 95% module coverage.

The local assessment resumes tests without passing JUnit outcomes and reruns
the entire changed perfectness module. GitHub runs the whole routine selection
from a fresh checkout. This avoids counting an interrupted batch as a full pass.

The resumed local batch passed 3,262 tests, reported 15 assertion failures, and
lost two workers to expensive tests. Its [report](third-assessment.json) is
incomplete. The subsequent [complete hosted assessment](hosted-assessment.json)
ran all 6,015 routine tests at commit `55706c7`: 6,000 passed and the same 15
assertions failed, with no worker failures. These findings led to the following
repairs:

- Declare Matplotlib in the test extra so the plotting integration test creates
  and checks a real PNG in a clean environment.
- Replace stale counts and rankings outside the historical corpus analysis
  with input-derived sets, an independent connected-family oracle, and small
  controlled ranking examples. Keep the fixed March analysis assertions.
- Correct two false mathematical assumptions: random search at n=8 has only
  36 successful colorings among 2,097,152 possibilities, and clique counts need
  not decrease with clique size. Independent exhaustive oracles now check the
  sampled outcomes and clique counts. Finite heuristic search is not guaranteed
  to succeed; triangle success and zero-trial contracts replace those assumptions.
- Remove an unused exhaustive counting pass from `witness_mdl`; the following
  enumeration already supplies the count and all witness statistics. Keep the
  exact n=10 count and n=11 nonexistence assertions.
- Allow 240 seconds for the monotonic lower-bound test, which performs two
  exhaustive searches. Its calculations and assertion are unchanged.

The dependency and assertion repairs pass 51 related tests on Python 3.10
([47.72s](assertion-repairs-python310.txt)) and 3.13
([25.95s](assertion-repairs-python313.txt)). All 12 timing-related regression
tests pass in [187.76s](timing-repairs.txt): n=10 witness setup takes 43.92s,
n=11 enumeration 54.51s, and the two-search test 89.15s. The additional
parameterized oracle increases the
routine selection to 6,016 tests. Final hosted results are linked from the
[integration PR](https://github.com/queelius/computational-explorations/pull/3).

The [collected selection](test-selection.json) lists every excluded test.
Four existing searches with declared timeouts over 300 seconds and the
three-test full algorithm benchmark now carry `slow` markers. The benchmark
enumerates 134,217,728 colorings at n=9 and has an explicit 1,800-second timeout.
Smaller algorithm tests remain routine. Incorrect assumptions were replaced
with the explicit checks described above, not hidden with exclusions or xfails.
The 14 excluded research tests have not been completed by this assessment.

## Reproducibility limits

Dependencies are constrained by the generated root `requirements-test.txt`.
The workflow pins third-party actions and the external data commit, preserves
JSON/JUnit/coverage artifacts, and bounds job durations. Its syntax was checked
with actionlint 1.7.12. Focused checks target Python 3.10 and 3.13; routine
checks target Python 3.10. Mathematical upper bounds still depend on the
arguments and limitations in the dated correction notice.
