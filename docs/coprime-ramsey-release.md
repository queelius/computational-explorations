# Coprime Ramsey corrections release

Version: **coprime-ramsey-2026.10.17**. Author: **Alexander Richard Towell**.

This release makes the coprime Ramsey corrections and reproducibility evidence
available from the cited repository. It builds on public commit `4bef9df`.
Original paper files and cited paths are preserved.

## What changed

- Extension searches distinguish a witness, exhaustive failure, and a seed
  limit. A sampled failure cannot establish an upper bound.
- Witnesses must cover exactly the canonical coprime edges with valid colors.
- Counting includes unconstrained edge variables and reports incomplete
  enumeration explicitly; exact-count helpers raise at a nonexhaustive cap.
- Current summaries and the corrected manuscript use the prime-clique proof
  of 59, distinguish edge and vertex parameters, include the Gallai transfer,
  and correct the supported R_cop(5) interval to 181–197.
- The synthesis CLI parses on the declared Python 3.10 minimum. Test extras
  now declare the scientific packages and parallel test runner used here.
- `CITATION.cff` describes this software snapshot. The original paper DOI is
  a related reference, not the software's identifier or preferred citation.

See the [correction notice](coprime-ramsey-corrections.md) for mathematical
errata and API compatibility details. The
[corrected manuscript](../e-jc/coprime-ramsey-ejc.pdf) is included as a research
artifact; this release makes no claim of journal acceptance or submission.

## Validation and reproduction

The release-specific run passed **172 tests** on Python 3.10.20, covering the
two coprime modules, gcd scaling, and synthesis. Line coverage was 88%, 96%,
and 71% for the two coprime modules and synthesis respectively (83% combined).
Existing coverage settings exclude CLI bodies; dedicated coprime CLI tests
still exercise those entry points.

```bash
python -m pytest tests/test_coprime_evidence.py \
  tests/test_coprime_ramsey_sat.py tests/test_coprime_ramsey_variants.py \
  tests/test_nt_graph_ramsey.py::TestRGCD tests/test_synthesis.py --timeout=60 -q
```

Synthesis and other data-dependent tests require the external
`teorth/erdosproblems` checkout at `data/erdosproblems`, with
`data/problems.yaml` inside it. Validation used commit
`350c521bd45292ddcdb751e86604a652c68558c5`. The coprime-only command omits
`tests/test_synthesis.py` and does not need that dataset.

Fresh independent checks again validate the witnesses at 10, 58, and 52
against all 42 triangles, 49,815 four-cliques, and 6,684 triangles respectively.
The corrected E-JC manuscript builds in eight pages. Citation metadata passes
CFF 1.2.0 schema validation.

The broader run completed with **1,011 passed and 10 setup errors** in 325.65
seconds before its ten-error stopping limit. All errors came from the shared
`TestUnitDistancesComputation.ud_results` geometry fixture exceeding the
120-second timeout. That fixture and its implementation are unchanged from
public commit `4bef9df`; this run does not establish whether it completes with
a larger time budget. No assertion failures were reported before stopping.

The exact command, selection rule, excluded node IDs and complete output are
saved in [release evidence](audits/coprime-ramsey-release-2026-10-17/).
Of 5,963 collected cases, 5,952 were selected; the remainder after the stopping
limit were not completed. The default full suite includes searches with
declared 15–60 minute runtimes; the bounded regression run excludes `slow`
tests and timeout markers greater than 300 seconds. Neither run constitutes
a full-suite pass or a direct SAT upper-bound rerun at 53 or 59.

The earlier [audit](coprime-ramsey-citation-audit.md) and
[repair validation](coprime-ramsey-repair-validation.md) remain historical
records. Their baseline commit IDs, observations, hashes and test counts refer
to those earlier working trees. The release evidence and attached source
manifest identify this branch separately.

## Publication and remaining scope

The [GitHub release](https://github.com/queelius/computational-explorations/releases/tag/coprime-ramsey-2026.10.17)
provides the exact tagged source and verification artifacts. The repository's
Zenodo integration archived the software at version DOI
[10.5281/zenodo.23433640](https://doi.org/10.5281/zenodo.23433640). Use that DOI
to cite this snapshot. All 310 files in the downloaded archive match the
tagged source manifest by path, size, and SHA-256. The release's
`zenodo-verification.json` attachment records the comparison against commit
`9b6fd18bf0ea736736ec4bad6fa1c332afe0bcb7`. This DOI link was added to the
repository after archiving; the release tag remains unchanged. The original
paper remains at [10.5281/zenodo.19058647](https://doi.org/10.5281/zenodo.19058647).

Completing Lean proofs, preserving UNSAT certificates for every variant, and
independently reproducing the two longer path thresholds remain separate
research tasks. No completeness claim for those items accompanies this release.
