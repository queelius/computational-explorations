# Coprime paths: contribution and submission assessment

**Date:** October 21, 2026. **Recommendation:** hold journal submission.
This is an AI-assisted mathematical and editorial assessment for Alexander
Richard Towell, not human peer review or a novelty certification.

## Judgment

The present 16-page manuscript does not yet have an established case for
journal significance. Its written proof and reproducible finite evidence
support a useful research record. That does not automatically make the
increment substantial enough for the proposed journals. Conversely, the
bounded review does not establish that the work is unpublishable.

The best potential journal contribution is a sharp structural **uniqueness
result at equality**, with the coprime threshold as an application. Before
reworking the paper around it, determine whether that uniqueness is already
known and whether its proof offers enough insight to justify a short note.
Do not add more numerical cases merely to lengthen a submission.

## What each part contributes

| Part | Evidence and contribution boundary | Editorial assessment |
| --- | --- | --- |
| `P_cop(9) = 17` | Written structural proof plus independently checked finite host lemmas and a lower coloring. No human proof review or formal verification. | A concrete extension of a narrow parameter; significance depends on the structural explanation. |
| Seventeen-vertex, 48-edge classification | Separate AI audits found no definite gap in contraction, deletion, closure, or reconstruction. | Strongest part of the present draft, but a fixed boundary case alone has a limited audience. |
| Equality classification for all orders `n >= 13` | The existing proof appears to extend; the [parameterized deduction](coprime-path-equality-family-2026-10-21.md) records the changes. | More coherent formulation. The possible increment is uniqueness, not a new edge bound or construction. |
| `P_cop(7) = P_cop(8) = 13` | Earlier public results, now independently recertified. | Reproducibility contribution; not new numerical results. |
| Linear growth and the upper constant | Standard density and path bounds; the deletion construction improves the full-host constant by `4/595`, approximately 0.672%. Optimality and priority are unestablished. | Supporting context, not currently a persuasive independent journal contribution. |

Here `P_cop(k)` measures path edges; `P_10` measures ten vertices.
The classification is constrained by vertex-cover size. It is not the
ordinary connected extremal equality problem for `P_10`-free graphs.

## Literature boundary

[Füredi–Kostochka–Verstraëte (FKV), Theorem 1.4](https://arxiv.org/pdf/1507.05338v2)
already gives the strict stability bound at the relevant density. Its
explicit sharpness construction, after removing a universal vertex, is
`K_3 ∨ (K_3 ∪ I_(n-6))`. The edge bound for graphs with vertex-cover number
at least five is therefore a corollary, not a new theorem of principle.
Their Theorem 1.6 stops at the equality relevant to our application.

[Füredi–Kostochka–Luo–Verstraëte (FKVL), Theorem 2.3](https://users.renyi.hu/~furedi/PUBS3/furedi_238_kostochka_ruthluo_verstraete_Erdos-Gallai-stability_II.pdf)
extends the necessary stability input to smaller orders. Its strict
threshold still does not directly classify our equality case. The
parameterized note derives the bound down to `n = 13`; it does not attribute
the uniqueness conclusion to that published theorem.

The additional bounded search inspected relevant statements in
[Ma–Ning](https://arxiv.org/pdf/1708.00704v2),
[Ning–Yuan](https://arxiv.org/pdf/2207.13650v2), and
[Ma–Yuan](https://arxiv.org/pdf/2010.13667v2), together with connected-path
extremal and path-saturation results. No inspected statement was identified
as the exact uniqueness theorem needed here. Strict inequalities,
minimum-degree hypotheses, and different extremal classes prevent the
immediate applications considered. This is a bounded exclusion of those
applications, not an exhaustive review of the papers or their consequences.
The second literature pass ended without a complete citation-chain review.

[Du–Xi–Deng–Ma, Table 12 and Open Problem 9.2](https://arxiv.org/html/2605.26815v2)
explicitly connect earlier repository results to non-complete edge targets.
That establishes relevance and prior attribution. It neither validates the
new proof nor establishes the significance or novelty of this particular
threshold. An external citation is not a journal-readiness test.

See also the earlier [source-by-source comparison](../e-jc/coprime-paths/LITERATURE.md).

## Decision and next checkpoint

1. Walk through the parameterized equality argument with the author,
   especially the eleven-vertex closure cases and Hall reconstruction.
   Record the actual review scope and corrections.
2. Resolve the narrow overlap question: is uniqueness of
   `K_3 ∨ (K_3 ∪ I_(n-6))` at `e = 3n - 3`, for connected `P_10`-free
   graphs with vertex-cover number at least five, already published or an
   immediate known corollary? Consult the closest papers and their citation
   chains; no outside person has been contacted.
3. If that uniqueness is new and mathematically informative, prepare a
   compact structural note with the Ramsey value as an application. If it
   is known, reassess the application on its own merits; do not describe
   the supporting stability theory as our contribution.
4. If the remaining increment is too small, retain the reproducible public
   research note and move on. A journal submission is optional.

## Provenance and archive scope

This assessment examined the author-edited manuscript and proof at project
commit `100ebcd0b8745720ff3d4c79777a437f26b334f6`, with two separate AI review
tasks and a root review. The literature task supplied bounded findings but
did not finish a final synthesis because its model became unavailable.
No new scientific computation, Lean proof, or human verification was
performed for this assessment. Previously archived computation remains
evidence for its stated finite checks, not for novelty or every deduction.

The [existing archive](https://doi.org/10.5281/zenodo.23497967) remains the
citation for the October 20 manuscript and evidence. It does **not** contain
this October 21 assessment or the parameterized deduction. The edited TeX,
PDF, and frozen packet remain unchanged. This assessment does not warrant
a separate DOI deposit.
