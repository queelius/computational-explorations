# Coprime paths: E-JC working manuscript

**Status: AI-assisted editorial draft; human mathematical review pending,
October 20, 2026.** The author's edited LaTeX copy was imported verbatim on
October 20, superseding the October 18 draft.
This is a separate follow-up to the historical manuscript in the parent
directory. It has not been submitted or accepted. No arXiv submission is
needed for this preparation route.

- [Read the manuscript](coprime-paths.pdf).
- [Edit its single-file LaTeX source](coprime-paths.tex).
- [Read the historical October 18 literature comparison](LITERATURE.md),
  preserved as an archived artifact; the October 21 assessment supersedes
  its unresolved structural-overlap conclusion.
- [Read the October 21 contribution assessment](../../docs/coprime-paths-contribution-assessment-2026-10-21.md):
  the structural classification is a corollary of published work; the
  present journal submission is not recommended.
- [Read the short attributed proof and walkthrough](../../docs/coprime-path-equality-family-2026-10-21.md).
- [Contribution record](../../research/records/coprime-paths/README.md):
  evidence pins, provenance, reproducible packet, citation, and next steps.

The previously considered venues are the **Electronic Journal of Combinatorics**
and **Discrete Mathematics**. Neither is a current submission commitment:
the October 21 assessment recommends retaining the archived research note.
The central result is
`P_cop(9) = 17`, supported by the 17-vertex extremal classification and
checked finite host lemmas. Earlier exact values are identified as prior
public results. The linear bounds provide context; their priority is not
established. Paths in `P_cop(k)` have **k edges**, whereas `P_j` in the
extremal arguments has **j vertices**.

The October 21 overlap review located Ma–Yuan's published equality
refinement, which gives the classification directly. The author's LaTeX
and PDF below are preserved historical versions and do not yet include
this attribution. Use the linked short proof for the current review;
the longer argument in Section 3 is not needed for that deduction.

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
3. **Published equality theorem.** Read Theorem 3 in Yuan (2024), credited
   to Ma–Yuan, and the linked short deduction. Check 2-connectivity and
   circumference after augmentation, the three edge counts, and why the
   universal vertex lies in the joining part of each remaining container.
4. **Historical proof (optional).** Section 3.2-3.4 supplies a longer
   independent route through contractions, simplicial deletions, closure,
   and Hall reconstruction. Reviewing that route is separate from using
   the shorter published corollary; it does not establish structural novelty.
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
The follow-up evidence and unchanged author-edited manuscript are now archived
at [10.5281/zenodo.23497967](https://doi.org/10.5281/zenodo.23497967).
The [archive receipt](../../research/records/coprime-paths/archive/README.md)
records the exact packet, verification, dates, and public-download hashes.
Its journal style is excluded; layout rebuilding requires that template
separately. Human mathematical review remains pending, and no journal
submission or acceptance is asserted. Substantive updates should reuse the
same archival family.

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
