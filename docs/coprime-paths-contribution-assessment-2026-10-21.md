# Coprime paths: contribution and submission assessment

**Updated:** October 21, 2026, after the targeted overlap review.
**Recommendation:** retain the current contribution as an archived research
note; do not pursue the present journal draft on the strength of its
structural classification. This is an AI-assisted assessment, not human
peer review or an editorial decision by a journal.

## Decisive finding

The entire structural theorem, including equality uniqueness for every
`n >= 12`, is a direct corollary of **Ma–Yuan's published stability
refinement**. It is stated as Theorem 3 in
[Long-Tu Yuan, *Circumference, minimum degree and clique number*, E-JC
31(4) (2024), #P4.64, page 2](https://www.combinatorics.org/ojs/index.php/eljc/article/download/v31i4p64/pdf/).
The [short deduction and proof walkthrough](coprime-path-equality-family-2026-10-21.md)
make the substitution and every exception explicit. The equality
classification should not be presented as a new structural contribution.

This resolves the main novelty question left open in the
[earlier assessment](https://github.com/queelius/computational-explorations/blob/161d39034acacdaa1dc04dfc28b4977ed693d74e/docs/coprime-paths-contribution-assessment-2026-10-21.md).
The older FKV/FKVL statements stopped at a strict density threshold; the
later theorem explicitly includes the equality alternatives. Checking the
older statements was insufficient to establish the contribution boundary.

## What remains attributable to this project

| Part | Current assessment |
| --- | --- |
| `P_cop(9) = 17` | A concrete coprime Ramsey application with checked finite host lemmas and a lower coloring. This review has not located that exact application elsewhere, but it is not an exhaustive novelty certification. |
| Extremal classification and its `n >= 12` formulation | A corollary of Ma–Yuan, not a new classification. Our longer written proof may retain expository value, but it is unnecessary for the short deduction. |
| `P_cop(7) = P_cop(8) = 13` | Earlier public values, independently recertified here. Reproducibility is the contribution. |
| Linear growth and improved upper constant | Standard density/path methods, including a 0.672% improvement over the full-host constant. Priority and optimality remain unestablished. |
| Reproducible evidence packet | Useful public documentation, certificate checking, and attribution. These benefits do not themselves establish journal significance. |

Here `P_cop(k)` counts edges and `P_10` counts vertices. The arithmetic
host reduction remains a separate argument; the published classification
does not itself state the coprime Ramsey value.

## Journal recommendation

The case for the current 16-page journal manuscript is weaker after this
finding. Its longest structural component is an established corollary,
and the remaining exact application is narrow. I recommend treating the
public, citable research note as the endpoint for this contribution unless
an independent expert identifies a compelling reason for a short journal
note. This is a judgment about the present evidence for significance, not
a proof that no journal could accept the application.

A future submission would need an accurate attribution-led rewrite and
human verification. It should lead with the coprime application, cite the
short stability corollary, and move detailed computational material to a
supplement. Do not inflate the paper with extra numerical cases or claim
the known equality theorem as an advance. No outside reviewer has been
contacted and no submission has been made.

## Targeted search and its limits

The decisive cited work is Ma–Yuan,
[*A Stability Result of the Pósa Lemma*, SIAM J. Discrete Math. 38(2)
(2024), 1757–1783](https://doi.org/10.1137/20M1382143).
Its bibliographic record was checked; full-text access was restricted.
Yuan's accessible published Theorem 3 supplies the exact statement needed.
This is a different paper from their 2020 clique-stability preprint
`arXiv:2010.13667v2`, which the earlier review had examined.

Two additional routes were checked before the decisive source was found:

- **Matching and cover numbers:** Shi–Ma,
  [*Maximum size of a graph with given matching number and covering number*](https://doi.org/10.1016/j.dam.2025.12.064),
  DAM 386 (2026), 70–74, Theorem 1.2, also gives our equality graph when
  matching number is four and cover number is five. Its statement was
  available in the publisher's indexed excerpt; its full proof was not
  accessible. That restricted result alone did not settle the path problem.
- **Later cycle stability:** Dong–Ning–Yuan–Zhang,
  [arXiv:2511.01509v1](https://arxiv.org/abs/2511.01509v1), Lemma 2.2,
  applies at a lower threshold but leaves additional configurations.
  Following this literature led to the decisive published equality theorem.

The earlier [literature comparison](../e-jc/coprime-paths/LITERATURE.md)
is preserved as a frozen archive input; its unresolved equality conclusion
is superseded here. The search remains bounded for the coprime
application and asymptotic constant. It no longer leaves the classification
as a plausible new structural result.

## Review, provenance, and archive scope

The follow-up proof check improved the earlier `n >= 13` deduction to
`n >= 12` and found explicit order-eleven counterexamples. A separate AI
review agreed; exhaustive small-graph checks and an added-edge control
corroborate those examples. The final short proof then follows directly
from the published equality theorem. The finite checks do not establish
novelty, the cited theorem, or human review.

The source examined is the author-edited manuscript at project commit
`161d39034acacdaa1dc04dfc28b4977ed693d74e`. Its mathematical statements have
not been contradicted by this review. The correction concerns attribution,
the length of the available proof, and our assessment of significance.

The [October 20 archive](https://doi.org/10.5281/zenodo.23497967) remains the
version-specific citation for the manuscript and evidence it contains.
It does not contain these October 21 findings. Cite this updated source
note as well when discussing attribution. The author's TeX and PDF are
preserved, and this review has not created a new DOI or replaced archived
files. Any future revised manuscript should use the existing archive family.
