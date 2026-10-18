# Exact nine-edge-path audit

The [proof](../../coprime-path-nine-resolution-2026-10-18.md) establishes
P_cop(9)=17. Paths are simple and their parameter counts edges.

## Evidence and dependencies

- `lower-n16-k9.json`: complete 79-edge avoiding coloring. Independent
  subset dynamic programming finds longest path lengths (8,8).
- The [previous structural archive](../coprime-path-nine-2026-10-18/README.md)
  supplies all finite lemmas used by the upper bound. Its paths, checker,
  tests, historical note, and manifest remain unchanged.
- The new written proof classifies the possible 48-edge color via published
  stability and contraction lemmas, simplicial vertex deletion, Hamiltonian
  closure, and explicit path extension arguments. `sources.json` records
  primary sources and hashes of the three locally inspected PDFs.
- `tests/test_coprime_path_nine_resolution.py` checks the lower witness,
  all 1,351 fault patterns in the auxiliary K(4,5) matching argument,
  endpoint paths in the triangle-join family, and all surviving nonempty
  i=5 closure patterns (90 and 15), finding explicit Hamilton cycles.
- `searches.json` records five inconclusive SAT probes. None is a proof
  dependency or a certificate of nonexistence.
- `independent-checks.json` records the isolated lower-witness check and
  verification of all 12 hashes in the prior structural manifest.
- `focused-tests.txt` records 510 passing focused tests, including the 16
  new auxiliary tests. `coverage.json` reports 100% statement coverage for
  both path certificate checkers; the repository configuration excludes
  `main` bodies, whose CLI behavior has separate integration tests.
- `manifest.json` hashes this evidence, the proof, its checkers, and tests.

## Reproduce

From the repository root:

```sh
python3 -I -S -O src/coprime_path_certificates.py witness \
  docs/audits/coprime-path-nine-resolution-2026-10-18/lower-n16-k9.json
python -m pytest -q tests/test_coprime_path_nine_resolution.py \
  tests/test_coprime_path_structure_certificates.py
```

The existing structural archive documents isolated standard-library commands
for all three upper-bound finite lemmas. CI runs the focused tests under
Python 3.10 and 3.13, checks the lower coloring in an isolated interpreter,
and runs the routine suite.

The auxiliary tests corroborate finite proof steps. They do not formally
verify the published theorems or the complete mathematical deduction.
There is no new UNSAT certificate or Lean formalization. Historical cited
artifacts and the existing release are unchanged. No novelty claim is made.
