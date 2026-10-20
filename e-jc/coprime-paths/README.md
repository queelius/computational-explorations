# Coprime paths: E-JC working manuscript

**Status: AI-assisted editorial draft; human mathematical review pending,
October 20, 2026.** The author's edited LaTeX copy was imported verbatim on
October 20, superseding the October 18 draft.
This is a separate follow-up to the historical manuscript in the parent
directory. It has not been submitted or accepted. No arXiv submission is
needed for this preparation route.

- [Read the manuscript](coprime-paths.pdf).
- [Edit its single-file LaTeX source](coprime-paths.tex).
- [Read the bounded literature comparison](LITERATURE.md).

The target is the **Electronic Journal of Combinatorics**, with **Discrete
Mathematics** as a possible later alternative. The central result is
`P_cop(9) = 17`, supported by the 17-vertex extremal classification and
checked finite host lemmas. Earlier exact values are identified as prior
public results. The linear bounds provide context; their priority is not
established. Paths in `P_cop(k)` have **k edges**, whereas `P_j` in the
extremal arguments has **j vertices**.

## Build

From the repository root, using TeX Live and `latexmk`:

```sh
cd e-jc
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -outdir=coprime-paths coprime-paths/coprime-paths.tex
```

The unchanged `e-jc.sty` in the parent directory supplies the journal
format. The draft overrides the template's publication dateline and
footer so it does not imply journal publication. The bibliography is
embedded, avoiding a separate BibTeX build. After inspecting the PDF,
`latexmk -c -outdir=coprime-paths coprime-paths/coprime-paths.tex` removes
temporary build products and keeps the PDF.

## Author review route

Review the proof in this order and record corrections directly in the
source or in a separate review note:

1. **Definitions and lower bound.** Check the edge/vertex convention and
   the two four-vertex covers in `G_16`.
2. **Finite lemmas and reduction (Section 2).** Reproduce the three
   certificate checks in Appendix A. Understand the transversal branching,
   deletion-orbit coverage, component-size bounds, and why the 13-vertex
   component case is excluded. A checker exit code alone is insufficient
   for reviewing the mathematical reduction.
3. **Published hypotheses (Section 3).** Compare the stated specializations
   with the original sources. Check the strict inequalities, the
   2-connectivity of contractions, and the Ali-Staton order condition
   `n >= 2*delta + 2`. The original Ali-Staton theorem is the dependency;
   a broader boundary formulation in a later secondary statement is not.
4. **Equality classification (Section 3.2-3.4).** Verify the at-most-one-leaf
   contraction argument, seven simplicial deletions, the three closure
   cases, and Hall's condition in reconstruction. These are the main
   author-review checkpoints.
5. **Asymptotics (Section 4).** Check the independent deleted set,
   inclusion-exclusion coefficient, error estimates, and the strict
   density condition. The constant is asymptotic, not a finite-k guarantee.
6. **Attribution and overlap.** Check the literature note, all citations,
   and the relationship to the earlier manuscript and repository releases.
   Assess whether this contribution meets the journal's significance bar.

The [E-JC submission checklist](https://www.combinatorics.org/ojs/index.php/eljc/about/submissions)
requires authors using an AI-obtained proof to rewrite it in their own
words and be able to vouch for every step.
Human verification and rewriting are still pending. A separate AI review
does not satisfy that requirement. At submission, also confirm author
agreement, publication/overlap status, no simultaneous journal review,
and no other E-JC submission by an author in the last three calendar
months. Those factual declarations have not been made here.

The initial submission is a PDF, with optional separate appendices;
source files are requested after acceptance. This guide does not certify
eligibility or editorial acceptance. Recheck the linked requirements when
the human-revised manuscript is ready.

## Evidence and public record

The manuscript cites the immutable evidence revision
[`8bda81e8d3f867bb1450b0e492592164416ba98f`](https://github.com/queelius/computational-explorations/tree/8bda81e8d3f867bb1450b0e492592164416ba98f).
Its [nine-edge audit](../../docs/audits/coprime-path-nine-resolution-2026-10-18/README.md)
links the proof, independent checkers, tests, and manifests.

The existing Zenodo records
[23433640](https://doi.org/10.5281/zenodo.23433640) and
[19058647](https://doi.org/10.5281/zenodo.19058647) describe earlier
material. They do not archive this follow-up or its new path evidence.
After author review, a versioned GitHub release and an appropriate Zenodo
archive can supply the public record without arXiv. No new archival
record or journal submission is created by preparing this draft.

## Preparation checks

The 114 existing tests for the nine-edge resolution, structural certificate
checker, and bounds calculator passed during manuscript preparation and
again after the October 20 revision (7.56 seconds), including CLI
integration checks. The latter two modules measured 100%
statement coverage under the repository's existing exclusions; `main`
bodies have separate subprocess tests. No source code or tests were changed.
The full routine suite previously passed on the evidence revision's
reviewed source; it was not repeated for this documentation-only change.

A fresh AI reviewer checked the October 18 transcription, source hypotheses,
certificate scope, and literature comparison. The review identified a
missing order hypothesis in a quoted lemma and three minor attribution
or parameter-pinning issues, all corrected in this draft. This is an
additional automated review, not the required human verification.

The October 20 source matches the author's supplied file byte for byte.
Its 16-page PDF builds without LaTeX warnings or box diagnostics; every
page was visually inspected. The two newly added journal DOIs were
checked against publisher metadata.
A separate AI comparison found no mathematical regression in the revision
and rechecked the certificate commands and FKVL theorem-number pin. It did
not replace human mathematical review or establish novelty.

The original cited manuscript, evidence archives, release tag, and
`AGENTS.md` are preserved. The proof notes at the evidence revision
document their successive historical states; the earlier conditional note
is intentionally not rewritten to conceal that history.
