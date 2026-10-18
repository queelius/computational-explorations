# Computational Explorations in Number Theory, Combinatorics, and Beyond

A curiosity-driven research project exploring mathematical structure through computation, spanning Erdős problems, Ramsey theory, additive combinatorics, and cross-domain pattern discovery.

## Headline Results

| Discovery | Value | Status |
|-----------|-------|--------|
| Coprime Ramsey R_cop(3) | **11** | Exact (incremental extension) |
| Coprime Ramsey R_cop(4) | **59** | Checked witness at 58 + prime-clique upper bound |
| Multi-color R_cop(3; 3) | **53** | Checked witness at 52 + prime-clique upper bound |
| Coprime Ramsey variants | [Full table](discoveries/coprime-ramsey/) | Verification status recorded per family |
| S(G,k) order-invariance | Holds k≤2, fails k=3 | Verified order ≤ 20 |
| Coprime graph perfectness | χ = ω = 1+π(n) | Verified n ≤ 30 (prior art exists) |
| Coprime Ramsey primality | All 4 known values prime | **Explained** (corollary of Du et al. Thm 4.4) |

## Repository Structure

```
src/                    # Python modules — computational experiments
tests/                  # Unit, integration, and long-running research tests
lean/                   # Lean 4 formalizations (mixed status; coprime Ramsey incomplete)
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

- [Running verification](docs/verification.md) — Fresh environment, independent witness checker, routine tests, and CI scope
- [Coprime path certificates (2026-10-18)](docs/audits/coprime-paths-2026-10-18/README.md) — Independently checked evidence that P_cop(7) = P_cop(8) = 13
- [Coprime path structural bounds (2026-10-18)](docs/coprime-path-structure-2026-10-18.md) — Linear growth, explicit density bounds, and limitations of the current proof methods
- [Nine-edge-path constraints (2026-10-18)](docs/coprime-path-nine-2026-10-18.md) — Any avoiding coloring at 17 must be connected in both colors, with a 47/48 edge split; the exact threshold remains unresolved
- [Crocker's red-distance certificate (2026-10-18)](docs/audits/erdos188-red-gap-2026-10-18/README.md) — Independent exact exclusion of distances [0.999, 1.001] for the specified Erdős 188 coloring; the blue-progression claim is outside this audit
- [Coprime Ramsey release](docs/coprime-ramsey-release.md) — Versioned corrections, witnesses, and verification scope
- [Coprime Ramsey corrections (2026-10-17)](docs/coprime-ramsey-corrections.md) — Current proof status and errata for the archived manuscript
- [Coprime Ramsey audit](docs/coprime-ramsey-citation-audit.md) — Reproduced checks, witnesses, and remaining gaps
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
| NPG-29 (proved) | R_cop(4) = 59 | Witness at 58 + K_18 prime clique at 59, R(4,4)=18 |
| ~~NPG-30~~ | ~~Coprime clique Ramsey numbers are always prime~~ | **Explained**: corollary of Du et al. Thm 4.4 (see below) |
| NPG-31 | Coprime graph G(n) is perfect | SAT n ≤ 30; prior art for groups |

### NPG-30 resolved: primality is automatic, not mysterious

Du, Xi, Deng & Ma (2026, [arXiv:2605.26815](https://arxiv.org/abs/2605.26815), Thm 4.4) prove the
prime-index identity R_cop(k) = p_{R(k,k)-1}, the (R(k,k)-1)-th prime, where R(k,k) is the
classical diagonal Ramsey number. (Their Theorem 4.4 is for the *edge*-coprime variant -- a
2-coloring of the edges of the coprime graph, which is exactly the R_cop of this repository. For the
*vertex*-coprime variant they prove a different identity, p_{sum_i(k_i-1)}, in their Theorem 3.2; do
not conflate the two.) Primality is then automatic: R_cop(k) is the value of the prime
function p at index R(k,k)-1, so it is prime *by construction*. The four observed values are exactly
this map (verified in Python via sympy.prime / sympy.primepi):

| k | R(k,k) | index R(k,k)-1 | R_cop(k) = p_{R(k,k)-1} |
|---|--------|----------------|--------------------------|
| 2 | 2  | 1  | p_1  = 2  |
| 3 | 6  | 5  | p_5  = 11 |
| 4 | 18 | 17 | p_17 = 59 |
| 3;3 (multicolor, R(3,3,3)=17) | 17 | 16 | p_16 = 53 |

So NPG-30 ("always prime") is no longer a standalone conjecture; it is a corollary of the prime-map.
Identifying the primes arising on the **two-color diagonal** remains tied to the unknown
R(k,k) values for k ≥ 5. In the unrestricted mixed family every prime occurs:
R(2,t)=t gives R_cop(2,t)=p_(t-1). See
[docs/rcop5-reconciliation.md](docs/rcop5-reconciliation.md) for the R_cop(5) case.

## Methodology

- **Python** with numpy, scipy, sklearn, pysat (SAT solving)
- **Lean 4** with Mathlib for formal proofs
- **SAT solvers**: Glucose4, CaDiCaL195 via python-sat
- **AI assistance**: Claude (Anthropic), with the October audit and repairs assisted by Codex (OpenAI); verification scope and remaining gaps are documented in the [audit](docs/coprime-ramsey-citation-audit.md).

## Provenance

- Erdős database: [teorth/erdosproblems](https://github.com/teorth/erdosproblems)
- Coprime graph perfectness: Prior art — Syarifudin & Wardhana (groups case)
- Product Schur triples: Related work — Mattos et al. (SIAM J. Discrete Math, 2024)
- Coprime Ramsey numbers R_cop(k): introduced here (no prior art, March 2026);
  since cited and theorized by Du, Xi, Deng & Ma (2026), who prove these values
  equal classical Ramsey numbers via a prime-index map (see "Cited by" below)
- Full provenance report: [docs/provenance_and_verification.md](docs/provenance_and_verification.md)

## Author

**Alex Towell** — M.S. Mathematics, M.S. Computer Science, Ph.D. student (CS), SIUE
atowell@siue.edu · [GitHub](https://github.com/queelius)

## License

Code: MIT. Papers: CC-BY-4.0.

## DOIs

The corrected software and witnesses are archived as
[coprime-ramsey-2026.10.17](https://doi.org/10.5281/zenodo.23433640).
See the [release record](docs/coprime-ramsey-release.md) for verification scope.

| Paper | DOI |
|-------|-----|
| Coprime Ramsey Numbers (original paper; [corrections](docs/coprime-ramsey-corrections.md)) | [10.5281/zenodo.19058647](https://doi.org/10.5281/zenodo.19058647) |
| Schur Number Extensions | [10.5281/zenodo.19058653](https://doi.org/10.5281/zenodo.19058653) |
| Survival Analysis of Erdős Problems | [10.5281/zenodo.19058655](https://doi.org/10.5281/zenodo.19058655) |

## Cited by

- Z. Du, W. Xi, Z. Deng, L. Ma, *Prime Certificates for Exact Vertex-Coprime
  Ramsey Numbers*, [arXiv:2605.26815](https://arxiv.org/abs/2605.26815) (2026).
  Cites the coprime Ramsey values computed here (R_cop(3)=11, R_cop(3;3)=53,
  R_cop(4)=59) and proves, via a prime-index map to classical Ramsey numbers
  (their Theorem 4.4), why they take these values.
