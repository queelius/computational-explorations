# Publishable Candidates — Ranked by Strength

## Tier 1: Strong Novel Results (arXiv + DOI)

### P1. "Coprime Ramsey Numbers"
**Venue**: Discrete Mathematics, JCTA, or Electronic Journal of Combinatorics
**Content**: R_cop(k) definition + exact values (2, 11, 59), R_cop(3;3)=53, 25+ variant values, primality conjecture, coprime graph structural properties
**Novelty**: HIGH — no prior art found for coprime Ramsey numbers
**Status**: Paper written (5pp LaTeX), compiled, ready for DOI
**Verification**: R_cop(3) verified 2 ways (incremental + SAT). R_cop(4) lower bound verified, upper bound via 100-seed extension check.
**What's needed**: Either prove n=59 UNSAT directly, or soften claim to "strong computational evidence"

### P2. "S(G,k) Order-Invariance for Abelian Groups"
**Venue**: J. Combinatorial Theory Series A, or Integers journal
**Content**: S(G,2) depends only on |G| (through order 20), breaks at k=3 (order 9), S(Z/nZ,3)=n-1 for n≤14, S(Z/nZ,2) sequence
**Novelty**: MEDIUM-HIGH — S(G,1) may follow from Green-Ruzsa, S(G,2) invariance + k=3 failure appear novel
**Status**: Paper written (5pp LaTeX), compiled
**Verification**: Exhaustive computation for all abelian groups

### P3. "MS(k) = 2^((3^k+1)/2) - 1: Exact Multiplicative Schur Numbers"
**Venue**: Integers journal, or Electronic J. Combinatorics
**Content**: MS(1)=3, MS(2)=31, MS(3)=16383, closed-form formula
**Novelty**: MEDIUM — product Schur actively studied (Mattos et al. SIAM 2024), exact values may be new
**What's needed**: Check SIAM paper for overlap. If our values are new, short note suffices.

---

## Tier 2: Novel but Needs More Work

### P4. "The AI Acceleration of Mathematical Problem-Solving: Evidence from 1,183 Erdős Problems"
**Venue**: Notices of the AMS, Mathematical Intelligencer, or PNAS (brief communication)
**Content**: 108x AI multiplier, survival analysis, difficulty curve, formalization paradox (φ=-0.274), prediction model, the "structured > deep" refutation
**Novelty**: HIGH as a data-driven analysis. Novel application of survival analysis to math problems.
**What's needed**: More rigorous statistical analysis, comparison with other problem databases

### P5. "Network Science of Mathematical Problems"
**Venue**: Applied Mathematics journal, PLoS ONE, or PNAS
**Content**: Problem network with community detection, centrality, temporal evolution, solved vs open subgraph comparison
**Novelty**: MEDIUM-HIGH — network science applied to mathematical knowledge is novel
**What's needed**: Agent still running. Need clean results.

### P6. "Coding Theory of Ramsey Avoiding Colorings"
**Venue**: IEEE Trans. Information Theory (short paper)
**Content**: The 156 avoiding colorings at R_cop(3)-1 as a binary code, rate, distance, structure
**Novelty**: MEDIUM — novel framing of Ramsey theory as coding theory
**What's needed**: Agent still running.

### P7. "Survival Analysis of Open Mathematical Problems"
**Venue**: Significance Magazine, Chance, JRSS, or PNAS (brief communication)
**Content**: Kaplan-Meier (median survival #966), Cox hazards (C=0.611; prize HR=2.70 p<0.0001, OEIS HR=0.62 p<0.001, formalization HR=0.53 p<0.0001), competing risks (proved:disproved 3.16:1, Ramsey 1:1), AI changepoint (3.73x multiplier at #750), Weibull AFT (best fit, prize AF=0.56)
**Novelty**: HIGH — survival analysis of math problem resolution is genuinely new
**Status**: COMPLETE. 103 tests, 80% coverage, proper inference.
**Strength**: This is the user's STRONGEST territory (M.S. Stats). Proper methodology.

---

## Tier 3: Blog Post / Preprint Only

### P8. "What We Learned From 3,000 Tests on Erdős Problems"
**Venue**: Blog post (metafunctor.com), with Zenodo DOI
**Content**: Full project narrative, all discoveries, methodology, what went wrong
**Status**: Agent writing blog post now

### P9. Coprime Graph Pseudorandomness
**Content**: Discrepancy, expander mixing, derandomization potential
**Status**: Agent running

### P10. Nonlinear Partition Regularity Landscape
**Content**: Pythagorean Schur numbers, coprime Pythagorean Ramsey
**Status**: Agent running

### P11. Constant Relations Discovery
**Content**: PSLQ-style search for relations between computed constants
**Status**: Agent running

---

## Publication Strategy

1. **Immediate (DOI only)**: Mint DOIs for P1 and P2 papers on Zenodo. No journal submission yet — get priority, gather feedback.

2. **Short-term (1-2 months)**: Submit P1 (Coprime Ramsey) to Electronic J. Combinatorics or Discrete Mathematics. It's the strongest result and most clearly novel.

3. **Medium-term**: If P4 (AI acceleration) and P7 (survival analysis) produce strong results, submit to an interdisciplinary venue. These are the most novel APPLICATIONS of statistics/CS to mathematical sociology.

4. **Blog post**: Publish P8 immediately after session. No peer review needed, establishes narrative.

5. **GitHub repo**: Make public. The code + tests + docs ARE the artifact. DOI the repo on Zenodo.
