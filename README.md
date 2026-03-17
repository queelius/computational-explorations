# Computational Explorations in Number Theory, Combinatorics, and Beyond

A curiosity-driven research project exploring mathematical structure through computation, spanning Erdős problems, Ramsey theory, additive combinatorics, and cross-domain pattern discovery.

## Headline Results

| Discovery | Value | Status |
|-----------|-------|--------|
| Coprime Ramsey R_cop(3) | **11** | Exact (incremental extension) |
| Coprime Ramsey R_cop(4) | **59** | SAT lower bound + extension upper bound |
| Multi-color R_cop(3; 3) | **53** | Exact (SAT) |
| 25+ coprime Ramsey variants | [Full table](discoveries/coprime-ramsey/) | Exact (SAT) |
| S(G,k) order-invariance | Holds k≤2, fails k=3 | Verified order ≤ 20 |
| Coprime graph perfectness | χ = ω = 1+π(n) | Verified n ≤ 30 (prior art exists) |
| Coprime Ramsey primality | All 4 known values prime | Conjecture (NPG-30) |

## Repository Structure

```
src/                    # 56+ Python modules — computational experiments
tests/                  # 57+ test files, ~3000 tests
lean/                   # Lean 4 formalizations (2 complete, 0 sorry)
paper/                  # LaTeX papers for DOI minting
docs/                   # Research findings, provenance, OEIS candidates
discoveries/            # Organized discovery summaries
  coprime-ramsey/       # The coprime Ramsey theory we built
  schur-extensions/     # Schur number extensions (S(G,k), DS, MS)
  meta-analysis/        # Mathematical sociology, AI acceleration
  cross-domain/         # Connections to CS, stats, physics
prior-art/              # Literature references and provenance checks
proofs/                 # Informal proof documents
data/                   # Erdős problem database (from teorth/erdosproblems)
```

## Key Documents

- [Provenance & Verification](docs/provenance_and_verification.md) — Prior art checks, novelty assessments
- [DOI Candidates](docs/doi_candidates.md) — Artifacts ready for permanent citation
- [Session Findings](docs/session_2026_03_15_findings.md) — Detailed discovery log
- [Novel Conjectures](docs/novel_problems.md) — NPG-27 through NPG-31
- [OEIS Candidates](docs/oeis_candidates.md) — Sequences for submission

## Conjectures

| ID | Statement | Evidence |
|----|-----------|----------|
| NPG-27 | S(G,k) depends only on \|G\| for abelian groups, k ≤ 2 | All groups order ≤ 20 |
| NPG-28 | DS(2,α) has exact phase transition thresholds | Full phase diagram computed |
| NPG-29 | R_cop(4) = 59 | SAT + extension proof |
| NPG-30 | Coprime clique Ramsey numbers are always prime | 4/4: {2, 11, 53, 59} |
| NPG-31 | Coprime graph G(n) is perfect | SAT n ≤ 30; prior art for groups |

## Methodology

- **Python** with numpy, scipy, sklearn, pysat (SAT solving)
- **Lean 4** with Mathlib for formal proofs
- **SAT solvers**: Glucose4, CaDiCaL195 via python-sat
- **AI assistance**: Claude (Anthropic) — all results independently verified

## Provenance

- Erdős database: [teorth/erdosproblems](https://github.com/teorth/erdosproblems)
- Coprime graph perfectness: Prior art — Syarifudin & Wardhana (groups case)
- Product Schur triples: Related work — Mattos et al. (SIAM J. Discrete Math, 2024)
- Coprime Ramsey numbers R_cop(k): Novel (no prior art found, March 2026)
- Full provenance report: [docs/provenance_and_verification.md](docs/provenance_and_verification.md)

## Author

**Alex Towell** — M.S. Mathematics, M.S. Computer Science, Ph.D. student (CS), SIUE
atowell@siue.edu · [GitHub](https://github.com/queelius)

## License

Code: MIT. Papers: CC-BY-4.0.
