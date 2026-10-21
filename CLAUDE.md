# computational-explorations

Computational attacks on problems in combinatorics and number theory: coprime
Ramsey numbers (cited by Du-Xi-Deng-Ma, arXiv:2605.26815), Schur-type problems,
survival analysis of open problems. Sibling of `~/github/research/open-problems`
(same methodology). **This repo is CITED -- never rename the GitHub remote
(github.com/queelius/computational-explorations) or move cited content.**

Orientation: `README.md` (results + Zenodo DOIs), `docs/oeis_candidates.md`,
`discoveries/<topic>/README.md` (per-topic records, incl. verification state),
`paper/` (drafts; Zenodo-archived versions), `e-jc/` and `jis/` (journal
submission packages), `lean/` (formalizations -- several files contain sorries;
do NOT claim "Lean-verified" without checking the file builds sorry-free).

Conventions: empirical-first, verification-always. Every claimed value needs a
two-sided machine check (witness + UNSAT/exhaustion), ideally two independent
solvers or methods. Sum-free convention: x+y=z with x=y allowed; 0 never in a
sum-free set. OEIS work: sequence variable `n`, one reference per line, no
EXTENSIONS field on new sequences. Identity/email: lex@metafunctor.com.

## Lessons learned (mistakes log)

Standing practice (per Alex, 2026-06-08): every mistake gets a dated entry --
what went wrong, why, how addressed, rule going forward. Blunt and specific.

### Mistake #1 (2026-06-10) -- declared MS(3) "hard-open" without checking the repo's own draft

**What:** In the Jun-8 Schur novelty check I wrote that the exact value of the
multiplicative Schur number MS(3) "needs the hard UNSAT/upper-bound side and is
open," after a satisfiability probe to N=300. Two days later, preparing the JIS
paper, I found (a) the repo's own draft paper (`paper/schur_extensions_note.tex`,
archived on Zenodo) already CLAIMED MS(3)=16383, and (b) the value is in fact
easy in both directions: the upper bound is a four-line theorem (powers of 2
embed classical Schur: 2^i * 2^j = 2^(i+j), so S(3)=13 forces a monochromatic
product triple among {2,4,...,2^14}), and the witness 3-coloring of {2..16383}
fell to SAT in 0.4 seconds.

**Why I got it wrong:** I treated the novelty check as an external-literature
problem and never re-read the repo's own draft section on MS(k); and I declared
hardness from one shallow probe without attempting the obvious structural bound
(map products to sums via powers of a fixed base -- the first thing to try for
any multiplicative Ramsey quantity).

**How addressed:** computed MS(3)=16383 exactly (theorem + SAT witness,
independently re-verified; artifacts in `discoveries/schur-extensions/grid/`),
corrected the README's superseded line, and put the corrected statement +
conjecture MS(k)=2^(S(k)+1)-1 in the JIS paper. The audit also caught that the
old draft's extrapolated formula 2^((3^k+1)/2)-1 has the wrong form (diverges
from 2^(S(k)+1)-1 at k=4) and that its Mattos et al. citation had wrong author
initials -- both fixed in the JIS version.

**Rules:** (1) Before declaring any quantity "open" or "hard," grep the repo's
own papers/notes for prior claims about it -- the cheapest literature search is
the repo itself. (2) For a hardness claim, first spend five minutes on the
obvious structural reduction; a probe that only touches the easy side (SAT
witnesses far below threshold) says nothing about where the threshold is.

### Mistake #2 (2026-10-17) -- sampled extensions were reported as proof

**What:** The coprime SAT helper returned the same success flag after exhausting
all base colorings and after reaching an arbitrary seed limit. Its caller could
therefore announce a false exact threshold. The audit reproduced this at 6→7,
where one failed extension coexists with a satisfiable target. Witness checks
also accepted missing edges and invalid colors; counting omitted free variables
and silently returned capped lower counts as exact.

**Why:** Evidence contracts were implicit, and tests exercised expected values
without testing incomplete searches or malformed witnesses.

**How addressed:** Added structured extension and enumeration results, strict
full-witness validation, free-variable registration, and regression tests.
Reconciled current summaries with the prime-clique proof of 59, preserving the
cited original paper and recording dated errata. See
`docs/coprime-ramsey-corrections.md` and the linked validation record.

**Rules:** Distinguish exhaustion, a counterexample, and a resource limit in
return values and reports. Validate the entire witness contract. Do not promote
a sampled failure or truncated count to a universal or exact claim.

### Mistake #3 (2026-10-21) -- missed the published equality refinement

**What:** The initial coprime-path assessment left structural uniqueness as
a possible new contribution after checking older strict stability bounds.
A targeted follow-up found Theorem 3 in Yuan's 2024 E-JC paper, credited to
Ma–Yuan, which gives the entire classification as an immediate corollary.
No priority claim had been made, but the journal assessment gave too much
weight to this unresolved possibility.

**Why:** The review had checked Ma–Yuan's 2020 clique-stability preprint,
but had not followed the later citation chain to their different 2024
Pósa-lemma paper and Yuan's accessible published equality statement.

**How addressed:** Replaced the provisional novelty framing with an
attributed short proof, updated the contribution assessment with the new
literature finding, and retained the historical manuscript, frozen
literature note, and Git versions. See
`docs/coprime-path-equality-family-2026-10-21.md`.

**Rule:** Before treating an equality boundary as a potential contribution,
trace later papers and check exact published equality alternatives. A
strict inequality in one source does not establish an unresolved case.
