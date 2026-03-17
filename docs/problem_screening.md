# Problem Screening: Ranked Candidates for Next Attack

**Date**: February 2026
**Basis**: problems.yaml database (1,135 problems), existing proof notes, technique transfer analysis
**Scope**: Open problems where we can make progress with our current toolkit (Fourier analysis, Mobius inversion, Ramsey/probabilistic, regularity, AI/Lean formalization)
**Context**: Active work on #883 (coprime graphs), #143 (primitive sets), #483 (Schur numbers), #43 (Sidon disjoint differences)

---

## Ranked Problem List

### 1. Problem #143 -- Primitive Sets ($500)

**Tags**: primitive sets | **Status**: open | **Formalized**: yes | **Prize**: $500

The KLL 2025 paper (arXiv:2502.09539) appears to directly imply a resolution via its contrapositive: if A satisfies |kx - y| >= 1 for all distinct x, y and k >= 1, then A has zero upper logarithmic density, which is precisely what #143 asks. The remaining gap is verifying that KLL's theorem covers real-valued A (not just integers) and that the epsilon = 1 threshold requires no special treatment. Our existing analysis in `proofs/kll_techniques_for_143.md` lays out the full verification plan. This is the single most likely problem to fall in the near term, and we already have the conceptual roadmap. The key next step is a careful reading of the KLL proof to confirm the exact hypotheses. If the reduction works, this is essentially a literature citation plus a short verification argument.

**Techniques**: GCD graph machinery (KLL), Mobius function, measure-theoretic density arguments
**Connection to existing work**: Direct extension of #883 coprime graph analysis; KLL's GCD graphs are structurally identical to our coprime analysis framework
**Tractability**: HIGH -- may already be implied by published results

---

### 2. Problem #483 -- Schur Numbers (no prize listed, but gateway problem)

**Tags**: number theory, additive combinatorics, Ramsey theory | **Status**: open | **Formalized**: no

Our Kelley-Meka adaptation for Schur numbers (`proofs/problem_483_attack.md` and `proofs/kelley_meka_schur.md`) has a well-developed outline: model k-coloring as balanced functions, expand via Fourier on Z/NZ, and apply density increment on Bohr sets. The key technical challenge is that sum-free sets can have density 1/2 (unlike AP-free sets which must be sparse), so the density increment must exploit the multicolor partition constraint rather than single-set density alone. Three of four problems in the #483 cluster (#484, #645, #721) are already proved, suggesting that technique transfer from those solutions may close the remaining gap. The attack plan has concrete lemmas (KM-1, KM-2) to verify and computational experiments ready to run. This is the highest-priority gateway problem due to its connectivity (degree 680 in the relationship graph) and the maturity of our approach.

**Techniques**: Kelley-Meka Fourier analysis, Bohr set density increment, multicolor bootstrap
**Connection to existing work**: Direct adaptation of KM methods we studied for #138; cluster siblings mostly solved
**Tractability**: MEDIUM-HIGH -- outline complete, key lemmas identified

---

### 3. Problem #138 -- Van der Waerden Number Growth ($500)

**Tags**: additive combinatorics | **Status**: open | **Formalized**: yes | **Prize**: $500 | **OEIS**: A005346

**CORRECTED ASSESSMENT** (Feb 2026): Problem #138 asks to prove W(k)^{1/k} → ∞, where W(k) is the van der Waerden number. This requires **super-exponential lower bounds** on W(k) — fundamentally different from the Kelley-Meka breakthrough, which improves upper bounds on AP-free set sizes (and hence upper bounds on W(k)). The current best lower bound is W(k) ≫ 2^k (Kozik-Shabanov 2016), giving W(k)^{1/k} → 2, far from → ∞. To resolve #138, one would need W(k) ≥ c^k for every constant c, which requires genuinely new construction techniques (probabilistic or algebraic). The initial Tier 1 rating from the technique transfer matrix was incorrect — Kelley-Meka does NOT apply to this problem's direction.

Known bounds:
- **Upper**: W(k) ≤ tower(k) (Gowers 2001, improved by Kelley-Meka for k=3)
- **Lower**: W(k) ≥ C · 2^k (Kozik-Shabanov 2016); W(p+1) ≥ p · 2^p for primes (Berlekamp 1968)
- **Gap**: Exponential vs. tower — Problem #138 asks to close this from below

**Techniques**: Algebraic constructions over finite fields, probabilistic lower bounds, Lovász Local Lemma
**Connection to existing work**: Weak — our Fourier toolkit targets upper bounds, not lower bounds
**Tractability**: LOW -- requires breakthrough in lower bound techniques

---

### 4. Problem #43 -- Sidon Sets with Disjoint Differences ($100)

**Tags**: number theory, Sidon sets, additive combinatorics | **Status**: open | **Formalized**: no | **Prize**: $100 | **OEIS**: A143824, A227590, A003022

This is our strongest candidate for AI-assisted resolution. The problem has three tags (high connectivity), partial results exist (Tao's upper bounds, Barreto's analysis), and the Sidon set framework is partially formalized in Mathlib. Our plan (`docs/techniques_and_solutions.md`, Pairing 2) is to formalize in Lean 4 and deploy AI search, following the model of Problem #124 which was solved by Aristotle in 6 hours via Lean formalization. The key mathematical content is bounding additive energy E(A union B) under the constraint (A-A) intersect (B-B) = {0}. This is finite for fixed N, making computational verification possible. The $100 prize is modest but the problem serves as a proof-of-concept for our AI+formalization pipeline, which scales to higher-value targets.

**Techniques**: Lean formalization, AI proof search (Aristotle-style), energy methods, polynomial method over finite fields
**Connection to existing work**: Sidon sets connect to #30 cluster; formalization pipeline validated on #124
**Tractability**: MEDIUM-HIGH -- AI-amenable, finite verification possible

---

### 5. Problem #30 -- Sidon Sets ($1,000)

**Tags**: number theory, Sidon sets, additive combinatorics | **Status**: open | **Formalized**: yes | **Prize**: $1,000 | **OEIS**: A143824, A227590, A003022

The flagship Sidon problem with the highest prize in the Sidon cluster. The technique transfer matrix rates the Sidon cluster (#30-44) as Tier 2 (4/5 match) for Kelley-Meka + polynomial method hybrid. The problem is already formalized, which is a significant advantage. Our approach is to combine Fourier analysis on difference sets with algebraic constructions over finite fields. The Sidon cluster has strong internal coherence: progress on #43 (rank 4 above) directly feeds into #30 via shared techniques on difference set structure. The $1,000 prize justifies sustained effort. The key obstacle is that Sidon set problems require constructive bounds (not just existence arguments), and our Fourier toolkit is better suited to density upper bounds than to constructions.

**Techniques**: Fourier + polynomial hybrid, finite field algebraic constructions, formalized framework
**Connection to existing work**: #43 is a stepping stone; shared OEIS sequences; same Sidon machinery
**Tractability**: MEDIUM -- substantial but well-structured challenge

---

### 6. Problem #883 -- Coprime Graphs (no prize)

**Tags**: number theory, graph theory | **Status**: open | **Formalized**: no

Our most developed attack. The proof outline in `proofs/problem_883_resolution.md` establishes triangle forcing for sets exceeding the 2n/3 threshold via a residue-class argument: any A with |A| > 2n/3 contains an element coprime to 6, which creates a triangle with {2, 3}. Computational verification passes for all n <= 24. The remaining gap is the full odd cycle spectrum (all odd cycles of length <= n/3 + 1), not just triangles. Our Mobius counting framework (NPG-7-R) proves M(A) > 0.25|A|^2 implies triangle forcing via Mantel's theorem, and the extremal set achieves density 0.24, confirming the threshold is tight. The coprime triangle forcing proof (`proofs/coprime_triangle_forcing.md`) is approximately 90% complete. Despite having no prize, this is the highest-connectivity problem (degree 810) and resolving it would be a meaningful publication bridging number theory and extremal graph theory.

**Techniques**: Mobius inversion, Mantel/Turan extremal graph theory, character sums, residue class analysis
**Connection to existing work**: Central to our research program; connects to #143 via KLL, to #483 via additive structure
**Tractability**: MEDIUM-HIGH for triangle case (nearly done), MEDIUM for full cycle spectrum

---

### 7. Problem #592 -- Ramsey ($1,000)

**Tags**: set theory, Ramsey theory | **Status**: open | **Formalized**: yes | **Prize**: $1,000

A $1,000 Ramsey problem. The technique transfer documents identify probabilistic + discrepancy methods as the primary approach, with the Campos et al. (2023) book graph method providing the most recent structural advance in graph Ramsey. The parallel structure between discrepancy problems (#161, #162) and Ramsey variants (#591, #592) suggests that Spencer-Beck discrepancy techniques could bound coloring problems. The formalization status is a positive indicator. However, Ramsey problems are notoriously resistant to incremental progress -- the recent breakthrough on R(3,3,...,3) bounds came from a genuinely new idea (structured random graphs), and #592 likely requires a comparable innovation. This is a high-reward but high-risk target. We should monitor for CGMS-style breakthroughs that might make this suddenly tractable.

**Techniques**: Probabilistic method, book graph method (Campos+), discrepancy, stepping-up lemma
**Connection to existing work**: Parallel structure with #483 (coloring + additive constraint); Ramsey transfer identified
**Tractability**: LOW-MEDIUM -- requires new ideas beyond current toolkit

---

### 8. Problem #593 -- Hypergraph Chromatic ($500)

**Tags**: set theory, graph theory, hypergraphs, chromatic number | **Status**: open | **Formalized**: no | **Prize**: $500

Four tags make this the most cross-connected unformalized prize problem. The technique transfer matrix places hypergraph Ramsey extensions in Tier 2 (book graph r-uniform extension). This problem sits at the intersection of set theory, graph theory, hypergraphs, and chromatic number -- exactly the kind of multi-domain problem where technique synthesis has the highest payoff. The lack of formalization is both a risk (less AI assistance) and an opportunity (formalizing it would be a contribution in itself). The hypergraph setting means that regularity-based approaches (hypergraph regularity lemma) and container methods are natural tools. The recent progress on hypergraph Ramsey by Conlon-Fox-Sudakov and the formalization update (Jan 2026) suggest active community interest.

**Techniques**: Hypergraph regularity, container method, book graph extension, chromatic polynomial
**Connection to existing work**: Chromatic number connects to #625; hypergraph structure connects to #564
**Tractability**: MEDIUM -- rich structure but technically demanding

---

### 9. Problem #625 -- Chromatic Number ($1,000)

**Tags**: graph theory, chromatic number | **Status**: open | **Formalized**: no | **Prize**: $1,000

A $1,000 chromatic number problem. Our technique documents identify this as a target for probabilistic method (random graph coloring) and additive-to-graph-theory transfer (Fourier analysis on coloring constraints). The connection to #74 (infinite chromatic, deletable to bipartite, $500) provides a potential cluster approach. The lack of formalization limits AI-assisted attacks. Chromatic number problems are generally hard because they require both upper bounds (coloring algorithms) and lower bounds (independence number bounds), and the gap between best known bounds tends to be wide. The problem is worth tracking because a breakthrough on #593 (rank 8) or general chromatic techniques could cascade here, but as a standalone target it is difficult.

**Techniques**: Probabilistic method, random graph coloring, Fourier transfer from additive combinatorics
**Connection to existing work**: Related to #593 via chromatic number tag; Fourier connection through #483
**Tractability**: LOW-MEDIUM -- hard standalone, but could benefit from cascade

---

### 10. Problem #52 -- Sum-Product ($250)

**Tags**: number theory, additive combinatorics | **Status**: open | **Formalized**: no | **Prize**: $250 | **OEIS**: A263996 | **Comments**: sum-product problem

The Erdos-Szemeredi sum-product conjecture. The technique transfer matrix identifies a Mobius-GCD hybrid approach as Tier 2 (4/5 match). Sum-product problems sit at the frontier of additive combinatorics, with recent progress by Rudnev, Shkredov, and others pushing exponents closer to the conjectured optimal. Our Mobius counting framework could contribute if we develop a "multiplicative Fourier" approach using Dirichlet character sums, as proposed in the technique transfer matrix. The sum-product problem connects structurally to the Sidon cluster (both concern additive vs. multiplicative structure) and to #883 (coprimality encodes multiplicative independence). The $250 prize is moderate. The main risk is that sum-product is an extremely active area where many experts are working, making it hard to find an unclaimed angle.

**Techniques**: Mobius-GCD hybrid, multiplicative Fourier (Dirichlet characters), polynomial method
**Connection to existing work**: Mobius framework from #883; additive-multiplicative duality shared with Sidon problems
**Tractability**: LOW-MEDIUM -- active competition, but our hybrid approach is relatively novel

---

## Summary Table

| Rank | Problem | Prize | Techniques | Tractability | Connection to Current Work |
|------|---------|-------|------------|--------------|---------------------------|
| 1 | **#143** (Primitive sets) | $500 | KLL/GCD graphs | HIGH | Direct from #883 |
| 2 | **#483** (Schur numbers) | -- | Kelley-Meka Fourier | MEDIUM-HIGH | Core research target |
| 3 | **#138** (VdW growth) | $500 | Algebraic/probabilistic | LOW | Lower bounds needed (KM irrelevant) |
| 4 | **#43** (Sidon disjoint) | $100 | AI/Lean + energy | MEDIUM-HIGH | Pipeline for #30 |
| 5 | **#30** (Sidon) | $1,000 | Fourier + algebraic | MEDIUM | #43 feeds directly |
| 6 | **#883** (Coprime graphs) | -- | Mobius + Mantel | MEDIUM-HIGH | 90% complete (triangles) |
| 7 | **#592** (Ramsey) | $1,000 | Probabilistic + book | LOW-MEDIUM | Parallel to #483 |
| 8 | **#593** (Hypergraph chrom.) | $500 | Containers + regularity | MEDIUM | Connects #625, #564 |
| 9 | **#625** (Chromatic) | $1,000 | Probabilistic + Fourier | LOW-MEDIUM | Cascade from #593 |
| 10 | **#52** (Sum-product) | $250 | Mobius hybrid | LOW-MEDIUM | Shares #883 tools |

---

## Strategic Recommendations

**Immediate (next 2 weeks)**:
- Verify KLL applicability to #143 (read arXiv:2502.09539 in full) -- potential $500
- Finalize #883 triangle forcing proof for submission
- Run `src/kelley_meka_schur.py` experiments for #138 bound verification

**Short-term (next 2 months)**:
- Launch Lean formalization of #43 for AI-assisted attack -- potential $100
- Complete #483 Fourier lemmas (KM-1, KM-2) and write up
- Check whether KM result already resolves #138 -- potential $500

**Medium-term (next 6 months)**:
- #30 Sidon cluster systematic attack leveraging #43 results -- potential $1,000
- #883 full odd cycle spectrum via spectral/regularity methods
- Monitor Ramsey landscape for #592 opportunities

**Total addressable prize value**: $3,850 across ranked problems
**Expected yield (optimistic)**: $1,100--$1,600 based on tractability assessments
