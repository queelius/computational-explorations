# Running Verification

Run commands from the repository root. CI checks Python 3.10 and 3.13 for
the coprime regression suite, and Python 3.10 for the broader routine suite.
The [October 17 assessment](audits/routine-verification-2026-10-17/README.md)
records results and limitations separately from the immutable release evidence.

## Install a reproducible test environment

```sh
python3.10 -m venv .venv
. .venv/bin/activate
python -m pip install -c requirements-test.txt '.[test]'
git clone https://github.com/teorth/erdosproblems.git data/erdosproblems
git -C data/erdosproblems checkout 19cb6116c2c194240e8f46c973e13a161f7987b2
```

The external database is needed by synthesis and database integration tests.
This March 16 snapshot matches the historical corpus assertions in
`test_ai_math_analysis.py`; newer data legitimately changes those counts.
For an existing clone, fetch the pinned commit and check it out without
discarding local changes. The dependency constraints are generated from
`pyproject.toml`, seeded with the audited release versions; they include
transitive dependencies. The generation command appears at the top of
`requirements-test.txt`. Regenerate the file and pass both CI Python versions
when updating dependencies.

## Independently check the archived witnesses

No installation or external database is needed for this command:

```sh
python3 -I -S src/verify_coprime_witnesses.py \
  docs/audits/coprime-ramsey-release-2026-10-17/witness-*.json
```

The standard-library checker recomputes the coprime edges and every candidate
vertex subset for the requested clique size. It rejects missing, duplicate,
noncanonical, or extra edges, invalid colors, and monochromatic forbidden
cliques. Saved `valid` flags and counts are ignored. JSON results go to stdout;
the exit status is zero only if every supplied file passes. `-O` does not disable
validation. Enumeration is intended for small witnesses and grows
combinatorially with their parameters.

These files establish lower bounds at 10, 52, and 58. Upper bounds require the
separate arguments described in the [corrections](coprime-ramsey-corrections.md).

## Independently check the path certificates

The [October 18 path audit](audits/coprime-paths-2026-10-18/README.md) includes
commands to validate the complete coloring at 12, validate every clause of
the formula at 13, and check its archived UNSAT proof using pinned DRAT-trim.
The witness checker uses subset dynamic programming; the formula checker
recognizes simple paths from their edge structure. Neither requires PySAT.
Formula validation alone does **not** establish UNSAT.

The separate **Independent path certificate** CI job performs all three checks
without rerunning the SAT search. It builds the pinned proof checker and gives
proof checking a 600-second process limit. This certifies the two boundary
instances for P_cop(7) = P_cop(8) = 13; it is not a Lean formalization.

## Independently check the two-color rectangle certificate

The [Crocker rectangle audit](audits/erdos189-rectangles-2026-10-18/README.md)
reconstructs all unit-area rectangles using equal diagonals with a shared
midpoint, checks the exact CNF encoding, and replays every positive-hint LRAT
step. It uses Python's standard library and does not execute downloaded code:

```sh
python docs/audits/erdos189-rectangles-2026-10-18/reproduce.py
```

This downloads the pinned 48.7 MB source archive. See the packet for the
offline `--archive` option, exact expected counts, failure controls and trust
boundary. The routine regression suite runs the packet's fast controls via
`tests/test_erdos189_audit.py`; it does not download or replay the full external
proof. This corroborates Crocker's two-color variant, not a new solution of
the original Erdős Problem 189.

## Run the focused regression suite

Set numerical libraries to one thread to avoid oversubscribing test workers:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest -q \
  tests/test_coprime_evidence.py tests/test_coprime_ramsey_sat.py \
  tests/test_coprime_ramsey_variants.py tests/test_nt_graph_ramsey.py::TestRGCD \
  tests/test_synthesis.py tests/test_verify_coprime_witnesses.py \
  tests/test_coprime_perfectness_proof.py \
  tests/test_coprime_path_certificates.py tests/test_coprime_path_search.py \
  tests/test_coprime_path_bounds.py \
  tests/test_geometry_attacks.py::TestUnitDistanceCount \
  tests/test_geometry_attacks.py::TestHasDuplicatePoints \
  --timeout=120 --timeout-method=thread \
  --cov=coprime_ramsey_sat --cov=coprime_ramsey_variants \
  --cov=synthesis --cov=verify_coprime_witnesses --cov=coprime_perfectness_proof \
  --cov=coprime_path_certificates --cov=coprime_path_search \
  --cov=coprime_path_bounds \
  --cov-report=term-missing
```

Coverage measures the selected modules. Existing coverage configuration excludes
`main` and `run_experiments` bodies; subprocess CLI tests are still run, but
their execution is not included in that coverage percentage. No minimum
percentage is currently enforced.

## Run routine and research tests

```sh
mkdir -p test-results
python -m pytest -v -m 'not slow' -n 2 --dist=loadfile \
  --timeout=120 --timeout-method=thread --durations=30 \
  --junitxml=test-results/routine.xml
```

The `slow` marker identifies expensive research searches. Four tests with
pre-existing timeouts above 300 seconds and the three-test full algorithm
benchmark (which enumerates 134,217,728 colorings at n=9) were added to that
category. Search budgets and assertions remain intact; the benchmark now has
an explicit 1,800-second timeout. Inspect the excluded selection
with `python -m pytest --collect-only -q -m slow`, and run it explicitly with
`python -m pytest -m slow --timeout-method=thread`. Individual test timeout
markers override the default. A timeout or unfinished search is not a proof.

[GitHub Actions](../.github/workflows/verification.yml) uses the same commands,
pins the dataset and action revisions, and uploads witness, JUnit, and focused
coverage reports even when tests fail. Jobs have additional overall time
limits. Passing these jobs does not verify the Lean developments, certify all
research claims, or complete the excluded long searches.
