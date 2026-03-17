# DOI Candidates — Citable Research Artifacts

Each discovery below is a candidate for minting a DOI on Zenodo (or similar),
giving it a permanent citable reference. DOIs establish priority and provenance.

**Existing DOIs from this project:**
- Paper: 10.5281/zenodo.18638633 (concept) / 10.5281/zenodo.18638638 (v2)
- Code: 10.5281/zenodo.18638635

---

## Tier 1: Strong Novel Results (DOI recommended)

### 1. Coprime Ramsey Numbers: R_cop(3)=11, R_cop(4)=59
**Type**: Dataset + short paper
**Content**: Definition of R_cop(k), exact values for k=2,3,4, SAT-based proofs,
the primality conjecture (NPG-30), and the full variant table (paths, cycles,
multi-color, bipartite, Gallai).
**Novelty**: HIGH — no prior art found for "coprime Ramsey numbers"
**Prior art check**: Searched "coprime Ramsey", "coprime graph Ramsey" — no results.
**Format**: Zenodo dataset with computational artifacts + arXiv preprint
**Priority**: HIGHEST — this is publishable and novel

### 2. Coprime Ramsey Variant Table (25+ exact values)
**Type**: Dataset
**Content**: P_cop(k) for k=3..8, C_cop(k) for k=3..6, R_cop(s,t) for (2,3),(2,4),(3,4),
R_cop(3;3)=53, GR_cop(3;3)=29, plus AP variants and vertex removal analysis.
**Novelty**: HIGH — entire field doesn't exist yet
**Could be**: Appendix to #1 above, or standalone dataset DOI

### 3. S(G,k) Order-Invariance (NPG-27) + k=3 Failure
**Type**: Short paper / research note
**Content**: S(G,1) and S(G,2) depend only on |G| for abelian groups (verified
through order 20). S(G,3) breaks at order 9. The S(Z/nZ,2) and S(Z/nZ,3)
sequences. The k=3 failure mechanism (group exponent).
**Novelty**: MEDIUM-HIGH — S(G,1) invariance may follow from Green-Ruzsa,
but S(G,2) invariance and k=3 failure appear novel.
**Format**: Zenodo research note

### 4. MS(k) = 2^((3^k+1)/2) - 1 Formula
**Type**: Research note
**Content**: Exact multiplicative Schur numbers MS(1)=3, MS(2)=31, MS(3)=16383,
closed-form formula, SAT verification.
**Novelty**: MEDIUM — product Schur triples actively studied (SIAM 2024 paper),
but exact values may be new. MUST check against Mattos et al. before minting.
**Depends on**: Reading the SIAM paper in detail.

### 5. Rado Number Table (general equation Ramsey)
**Type**: Dataset
**Content**: Exact 2-color Rado numbers for a+b=c (5), a+b=2c (9), a+b+c=d (11),
a+2b=3c (13). Plus 2D Schur number (4) and modular Schur numbers.
**Novelty**: MEDIUM — individual values may be known, the collection is useful.

---

## Tier 2: Interesting Findings (DOI optional)

### 6. DS(2,α) Phase Transition Structure
**Content**: Three regimes at α=0.60 and α=0.67. The 0-indexed vs 1-indexed
distinction. DS(3,0.25)=15.
**Caveat**: Definition sensitivity (floor vs ceil) must be resolved first.

### 7. Schur-Sidon Fourier Bridge
**Content**: 31-104x spectral gap between sum-free and Sidon sets.
Quantitative obstruction connecting Problems #483 and #43.
**Novelty**: The computational quantification is novel, the conceptual
connection (Fourier analysis in additive combinatorics) is well-known.

### 8. Coprime Graph Spectral Analysis
**Content**: Spectral gap, chromatic number = clique number = 1+π(n),
independence number = floor(n/2), Ramsey-Turán density.
**Caveat**: Coprime graph perfectness has prior art (Syarifudin-Wardhana).
Our SAT verification adds computational evidence.

### 9. Problem #773: Sidon-Squares Sequence
**Content**: a(n) = max Sidon subset of {1²,...,n²}, growth rate ~n^{2/3}.
**Novelty**: The sequence may already be in OEIS as A390813.

### 10. Computational Compendium
**Type**: Code repository DOI
**Content**: 56 source modules, 2,995 tests, covering ~60 Erdős problems.
**Format**: Zenodo code archive (update existing DOI 10.5281/zenodo.18638635)

---

## Tier 3: Meta-Results (blog post, not DOI)

- Resolution cascade timing (bursty patterns in all families)
- The 6/π² ubiquity conjecture
- Solvability features (graph theory easier than number theory)
- AI acceleration analysis (213 problems in 7 months)
- Interestingness quantification

---

## Minting Process

1. Prepare artifact (code, data, or writeup)
2. Upload to Zenodo with metadata (title, authors, description, keywords)
3. Zenodo auto-assigns DOI
4. Add DOI to this document and MEMORY.md

**Author**: Alex Towell (atowell@siue.edu), SIUE
**Acknowledgment**: Computational analysis performed with Claude (Anthropic)
