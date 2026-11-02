# Coprime paths: the nine-edge threshold, linear bounds, and evidence

**Alexander Richard Towell**  
Southern Illinois University Edwardsville  
ORCID: https://orcid.org/0000-0001-6443-9897

## Contribution and scope

Let \(G_n\) have vertices \(1,\ldots,n\), with edges between distinct coprime
integers. Let \(P_{\mathrm{cop}}(k)\) be the least \(n\) such that every
two-coloring of its edges contains a monochromatic simple path with \(k\)
edges. The main result is

\[
P_{\mathrm{cop}}(9)=17.
\]

A complete coloring at 16 avoids a nine-edge path in either color. The
upper bound combines a written extremal classification with independently
checked finite lemmas about the host graph. The packet contains the
written deduction, exact certificates, standalone checkers, search code,
tests, and references to the published graph-theoretic ingredients.

Supporting material independently recertifies the earlier reported values
\(P_{\mathrm{cop}}(7)=P_{\mathrm{cop}}(8)=13\), and proves

\[
2\leq\liminf_{k\to\infty}\frac{P_{\mathrm{cop}}(k)}k
\leq\limsup_{k\to\infty}\frac{P_{\mathrm{cop}}(k)}k
\leq\frac{197\pi^2}{595}.
\]

The earlier values are not claimed as new discoveries. Selected endpoint
and matching explorations are preserved with their historical status;
they are not dependencies of the main proof. The infinite odd-path
formula remains unresolved.

## Files and reproduction

`coprime-paths-2026.10.20.zip` contains 79 explicitly pinned source files,
structured metadata, citation data, reproduction instructions, and a
SHA-256 inventory. Its SHA-256 is:

```text
ce2d2015c0238343633e6e4eeaca6849535c8ead52ada0d1355cbfd8392d8de6
```

Extract the ZIP and read `coprime-paths/README.md`. Create a fresh Python
3.10 environment and run the listed commands from `coprime-paths/source/`.
The companion `VERIFICATION.json` records staged replay, tests, environment,
and the precise scope of each check.

The packet is reproducible from
[metadata and packaging commit afb384e](https://github.com/queelius/computational-explorations/tree/afb384ee910a6f25cadaeabb9cf8a74729a02666)
using `python src/research_records.py package coprime-paths --output packet.zip`.
Later publication receipts change live metadata, so use this exact commit
to reproduce these archive bytes. The packet retains the prepublication
metadata as it stood at assembly; the companion `CITATION.cff` supplies the
archive's exact version DOI.

The author-edited manuscript PDF and LaTeX are included unchanged. The
journal's `e-jc.sty` is excluded because redistribution terms were not
established. Rebuilding the journal layout requires that template
separately. The mathematical proof and listed computational checks do not.
The manuscript PDF is also supplied separately for convenient reading.

## Evidence, review, attribution, and dates

The complete deduction is a written proof, not a proof-assistant
formalization. Passing tests and certificate checks establish the stated
finite results; they do not verify every written argument or imported
theorem. No new nine-edge SAT UNSAT certificate is claimed. Human
mathematical review, journal acceptance, and a comprehensive novelty
assessment remain pending.

Substantial OpenAI Codex assistance contributed to investigation, arguments,
programming, verification, editorial preparation, and organization.
Independent AI review is distinguished from human peer review. The author
supplied the October 20 manuscript revision.

Predecessor contributions and graph-theoretic ingredients are credited in
the manuscript, written proof, and structured record. Original code is
MIT-licensed; original research prose is CC BY 4.0. Consult the packet's
`source/research/records/coprime-paths/LICENSES.md` and per-file metadata.

The nine-edge proof was publicly disclosed in
[PR #9](https://github.com/queelius/computational-explorations/pull/9) on
October 18, 2026. The author-revised manuscript and organized evidence
became public in
[PR #11](https://github.com/queelius/computational-explorations/pull/11)
on October 20. The archive's publication date is recorded separately.
Neither a DOI nor these disclosure dates establish novelty or legal
priority.

The canonical source remains
[computational-explorations](https://github.com/queelius/computational-explorations).
The curated discovery entry is in
[research-records](https://github.com/queelius/research-records/tree/main/records/computational-explorations-coprime-paths).
