# Coprime paths: exact thresholds, bounds, and evidence

**Author:** Alexander Richard Towell
([ORCID](https://orcid.org/0000-0001-6443-9897)).
Substantial OpenAI Codex assistance is disclosed in the manuscript and record.

The main result is **`P_cop(9) = 17`**: every two-edge-coloring of the coprime
graph on `1,…,17` has a monochromatic simple path with nine edges, while a
checked coloring at 16 avoids one. The upper bound combines a written
extremal classification with independently checked finite host lemmas.

Earlier public values `P_cop(7) = P_cop(8) = 13` were independently
recertified. A separate written argument establishes linear growth and
`limsup P_cop(k)/k ≤ 197π²/595`, with lower limit at least 2.
Those supporting results are not presented as new priority claims.

## Read and continue

- [Manuscript PDF](../../../e-jc/coprime-paths/coprime-paths.pdf) and
  [editable LaTeX](../../../e-jc/coprime-paths/coprime-paths.tex).
- [Nine-edge proof](../../../docs/coprime-path-nine-resolution-2026-10-18.md)
  and [audit](../../../docs/audits/coprime-path-nine-resolution-2026-10-18/README.md).
- [Structural bounds](../../../docs/coprime-path-structure-2026-10-18.md).
- [Literature and overlap assessment](../../../e-jc/coprime-paths/LITERATURE.md).
- [October 21 contribution assessment](../../../docs/coprime-paths-contribution-assessment-2026-10-21.md):
  hold journal submission; the possible structural increment is uniqueness
  at equality. A linked parameterized deduction is provisional and is not
  included in the October 20 DOI version.
- [Preserved auxiliary findings](exploration/README.md), including the
  endpoint and matching arguments and selected complete replayable evidence.
- [Structured record](record.json), [citation](CITATION.cff),
  [author-revision receipt](author-revision.json), and [licenses](LICENSES.md).

## Evidence and review

`P_cop(k)` counts **edges**, whereas `P_j` in the cited extremal graph theorems
counts **vertices**. The statements concern two colors, simple paths, and
edges between distinct coprime positive integers.

The main proof was accepted into this repository in
[PR #9](https://github.com/queelius/computational-explorations/pull/9)
on October 18, 2026. That PR supplies a dated public disclosure and records
AI review and passing CI. Repository acceptance is not journal acceptance.
The author revised the manuscript on October 20; human mathematical review
remains pending. There is no Lean verification, new nine-edge UNSAT
certificate, established priority, or proof of the infinite odd-path family.

## Reproduce and cite

Use the commands and expected outputs in `record.json` and the linked audits.
The [repository record guide](../../README.md) explains validation, environment
installation, and byte-reproducible packaging. Packets include the source,
certificates, tests, manuscript, licenses, and a SHA-256 inventory.
The archival selection contains 79 pinned files and omits the third-party
`e-jc.sty` template. The manuscript PDF and author-edited LaTeX are unchanged;
rebuilding its journal layout requires that template separately. All listed
mathematical checks run from the packet itself.

Generate the current contribution's citation with:

```sh
python src/research_records.py cite coprime-paths
```

Cite the exact archive version
[10.5281/zenodo.23497967](https://doi.org/10.5281/zenodo.23497967), published
October 20, 2026. The [archive record](archive/README.md) gives its frozen
packaging commit, file hashes, replay results, and verified public downloads.
The earlier software DOI `10.5281/zenodo.23433640` and original-paper DOI
`10.5281/zenodo.19058647` do **not** archive this follow-up. The public PR
date, local author revision, and DOI publication are recorded separately.

## Next work

1. Follow the [contribution assessment](../../../docs/coprime-paths-contribution-assessment-2026-10-21.md):
   review the parameterized equality proof with the author and resolve its
   precise overlap before deciding whether a journal note is justified.
2. Use the existing archival version family for substantive evidence updates,
   preserving earlier versions and checking public downloads again.
3. Treat journal submission, shorter analytic proofs, the infinite family,
   and a broader novelty assessment as separate tasks.
