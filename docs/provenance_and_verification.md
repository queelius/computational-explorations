# Provenance and Verification Report

## Date: March 16, 2026

This document tracks prior art, novelty assessment, and verification status
for all findings from the March 15-16, 2026 research session.

---

## 1. PRIOR ART CHECK

### 1.1 Coprime Graph Perfectness (NPG-31)

**Our claim**: χ(G(n)) = ω(G(n)) = 1 + π(n) for the integer coprime graph.

**PRIOR ART EXISTS**:
- Syarifudin & Wardhana, "The Clique Numbers and Chromatic Numbers of The
  Coprime Graph of a Dihedral Group" — shows coprime graphs of finite groups
  are weakly perfect (χ = ω).
- The integer coprime graph G(n) on {1,...,n} is a specific case. The fact
  that ω(G(n)) = 1 + π(n) (vertex 1 plus all primes) is folklore.
- The perfectness (not just weak perfectness) needs checking against the
  Strong Perfect Graph Theorem.

**STATUS**: Our result is a REDISCOVERY + computational verification (SAT-based
exact verification for n ≤ 30). The computational verification adds value but
the theoretical result is not novel. We should cite the existing literature.

**Sources**:
- [Syarifudin & Wardhana on Semantic Scholar](https://www.semanticscholar.org/paper/The-Clique-Numbers-and-Chromatic-Numbers-of-The-of-Syarifudin-Wardhana/15edeacce18b214a3b41ef1edbf80f62e102686a)
- [Tandfonline: On graphs with equal coprime index and clique number](https://www.tandfonline.com/doi/full/10.1080/09728600.2023.2218442)

### 1.2 Coprime Ramsey Numbers

**Our claim**: R_cop(3) = 11, R_cop(4) = 59.

**NO PRIOR ART FOUND**: Searches for "coprime Ramsey" return no results combining
coprime graphs with Ramsey numbers for cliques. The concept of R_cop(k) appears
to be NOVEL to this project.

**Related work**:
- General Ramsey theory extensively studied (R(5,5) bounds narrowed to [43,46]
  by Angeltveit & McKay 2024).
- Coprime graph properties studied (clique numbers, chromatic numbers,
  independence) but NOT Ramsey-type questions.

**STATUS**: R_cop(k) appears GENUINELY NOVEL. However, the concept is natural
enough that it may have been studied under a different name. Thorough literature
search recommended before publication.

### 1.3 Multiplicative Schur Numbers

**Our claim**: MS(k) = 2^((3^k+1)/2) - 1, giving MS(1)=3, MS(2)=31, MS(3)=16383.
Here MS(k) = max N such that [2..N] can be k-colored avoiding monochromatic {a,b,ab}.

**PRIOR ART EXISTS (partial)**:
- Mattos, Mergoni Cecchelli, Parczyk, "On Product Schur Triples in the Integers",
  SIAM J. Discrete Math (2024/2025). Studies xy=z colorings.
- The paper provides asymptotic bounds on monochromatic solutions, not exact
  Schur numbers. Our exact values MS(1)=3, MS(2)=31 may be new, but the
  area is actively studied.

**STATUS**: The exact formula MS(k) = 2^((3^k+1)/2) - 1 needs verification against
the SIAM paper's results. The formula may be novel even if the problem area isn't.

**Sources**:
- [SIAM: On Product Schur Triples](https://epubs.siam.org/doi/10.1137/24M1632875)

### 1.4 S(G,k) Order-Invariance (NPG-27)

**Our claim**: S(G,1) and S(G,2) depend only on |G| for abelian groups.
S(G,3) breaks at order 9.

**PARTIAL PRIOR ART**:
- Green & Ruzsa (2005) settled max sum-free set size for general abelian groups.
  This determines S(G,1).
- The 2-coloring order-invariance for S(G,2) appears less studied.
- The k=3 failure at order 9 appears NOVEL.

**STATUS**: S(G,1) invariance may follow from Green-Ruzsa. S(G,2) invariance
and the k=3 failure are likely novel findings worth publishing.

### 1.5 Density Schur DS(k, α)

**Our claim**: DS(2, α) has three phase regimes.

**IMPORTANT CAVEAT**: The 0-indexed vs 1-indexed distinction changes the values.
Our Lean proof (NPG-2) uses 0-indexed {0,...,N-1} where 0+0=0 forces Schur.
The 1-indexed version on {1,...,N} gives different values.

**STATUS**: Needs careful definition reconciliation before any publication.

---

## 2. RECENT ERDŐS PROBLEM SOLUTIONS (2025-2026)

Our YAML database is from August 31, 2025. Since then:

### Solutions verified by Terence Tao (Jan 2026):
- **#728**: Solved by Kevin Barreto + AcerFur using GPT-5.2 Pro, formalized by
  Aristotle in Lean. First autonomous AI solution to an Erdős problem.
  [arXiv:2601.07421](https://arxiv.org/html/2601.07421v1)
- **#397**: Solved by Neel Somani, verified by Tao.
- **#729**: Solved alongside #728 and #397.
- **#347**: Proved by Enrique Barschkis, formalized in Lean (Jan 2026).

### AI-assisted solutions (Dec 2025):
- **#1026**: Solved by Boris Alexeev using Aristotle AI tool.
  [Tao's blog post](https://terrytao.wordpress.com/2025/12/08/the-story-of-erdos-problem-126/)

### Other recent solutions (2025-2026):
- **#570**: Solved by Cambie, Freschi, Morawski, Petrova, Pokrovskiy.
- Numerous problems solved via literature search by GPT-5 (Oct 2025).

### Database statistics (as of Jan 2026):
- 1,183 problems in database (up from our 1,135)
- 491 (42%) solved (up from our 400 proved+solved+disproved)
- 22 formally verified in Lean
- 279 proved as of Jan 2026

**ACTION**: Update our local YAML from the GitHub repository to get the latest
status changes: https://github.com/teorth/erdosproblems

### Key community context:
- Tao on Mastodon: AI systems "better suited for being systematically applied
  to the 'long tail' of obscure Erdős problems"
- Kevin Barreto sets the bar for AI proofs: Lean formalization required
- Aristotle (Harmonic's system) is the primary auto-formalization tool
- The community is "extremely progressive" about AI contributions (from earlier
  forum research)

**Sources**:
- [erdosproblems.com](https://www.erdosproblems.com/)
- [GitHub: teorth/erdosproblems](https://github.com/teorth/erdosproblems)
- [Scientific American: AI uncovers solutions](https://www.scientificamerican.com/article/ai-uncovers-solutions-to-erdos-problems-moving-closer-to-transforming-math/)
- [Tao Mastodon](https://mathstodon.xyz/@tao/115591487350860999)
- [TechCrunch: AI cracking math](https://techcrunch.com/2026/01/14/ai-models-are-starting-to-crack-high-level-math-problems/)

---

## 3. COMPUTATIONAL VERIFICATION STATUS

### 3.1 R_cop(4) = 59: STRONG EVIDENCE, NOT RIGOROUS PROOF

**Lower bound (SAT)**: Glucose4 finds avoiding colorings at n ≤ 58. ✓ Verified.
**Upper bound (extension)**: 100 colorings of [58] fail to extend to [59].
This is STRONG EVIDENCE but not a complete proof — we checked 100 colorings,
not ALL avoiding colorings at n=58.

**To make rigorous**: Need to either:
(a) Prove n=59 SAT instance is UNSAT (direct solve — hard, timed out), OR
(b) Prove there are exactly K avoiding colorings at n=58, check ALL K extensions, OR
(c) Provide a mathematical argument for why no extension can work.

**The clause/variable ratio argument** (ratio ~109, UNSAT threshold ~4.27) is
heuristic, not proof. Real SAT instances can be SAT even at high ratios.

**Direct UNSAT proof attempt**: Running Glucose4 on the full n=59 formula
(1,085 variables, ~118K clauses). After 30+ minutes, still solving. The instance
is genuinely hard for CDCL solvers. A DRAT proof certificate would provide
machine-checkable verification.

**Database update (2026-03-16)**: Pulled latest from github.com/teorth/erdosproblems.
213 problems solved since Aug 2025. 1,183 total problems. 118 new Lean verifications.
None of our specifically attacked problems overlap with the new solutions.

### 3.2 Other exact values: verified by SAT

All P_cop, C_cop, R_cop(s,t), GR_cop values are SAT-verified (complete search
at each n). These are rigorous within the correctness of the SAT solver.

### 3.3 MS(k) formula: verified for k=1,2,3

MS(1)=3, MS(2)=31, MS(3)=16383 each verified by SAT. The formula MS(k)=2^((3^k+1)/2)-1
fits all three points. However, 3 points is minimal for a conjecture — MS(4) would
be the real test (but MS(4) = 2^41-1 ≈ 2.2 trillion, infeasible to verify).

### 3.4 S(G,k) order-invariance: verified exhaustively

S(G,1) and S(G,2) invariant through order 20 (all abelian groups checked).
S(G,3) failure at order 9 verified exactly. These are rigorous.

---

## 4. NOVELTY ASSESSMENT

| Finding | Novel? | Prior Art | Confidence |
|---------|--------|-----------|------------|
| R_cop(k) concept + values | **YES** | None found | High |
| R_cop(4) = 59 | **YES** | None found | High (but see §3.1) |
| R_cop(3;3) = 53 | **YES** | None found | High |
| P_cop, C_cop values | **YES** | None found | High |
| Coprime graph perfect | **NO** | Syarifudin-Wardhana | Our SAT verification adds value |
| α(G(n)) = ⌊n/2⌋ | **PROBABLY NO** | Likely folklore | Easy observation |
| S(G,2) order-invariance | **LIKELY YES** | Green-Ruzsa covers k=1 only | Medium |
| S(G,3) breaks at order 9 | **LIKELY YES** | Not found | High |
| DS(2,α) phase transitions | **YES** | Novel concept | Medium (definition sensitivity) |
| MS(k) formula | **POSSIBLY** | SIAM paper covers related area | Need to check SIAM paper |
| NPG-30: R_cop always prime | **YES** | Novel conjecture | 4/4 evidence |
| Schur-Sidon Fourier bridge | **YES** | Novel computational connection | High |

---

## 5. RECOMMENDATIONS

1. **UPDATE YAML**: Pull latest from github.com/teorth/erdosproblems to get
   problems solved since Aug 2025. ~91 new solutions to incorporate.

2. **CHECK MS FORMULA**: Read the SIAM product Schur paper in detail.

3. **RIGOROUS R_cop(4)**: Either prove n=59 UNSAT directly, or enumerate ALL
   avoiding colorings at n=58 and check exhaustively.

4. **CITE COPRIME PERFECTNESS**: Reference existing literature in NPG-31.

5. **DS DEFINITION**: Settle on 0-indexed or 1-indexed and document clearly.

6. **LEAN FORMALIZATION**: R_cop(3)=11 is the best candidate for a novel Lean proof.
