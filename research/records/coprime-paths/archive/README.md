# Archived evidence — version 2026.10.20

**Exact version DOI:** [10.5281/zenodo.23497967](https://doi.org/10.5281/zenodo.23497967)

**Version family:** [10.5281/zenodo.23497966](https://doi.org/10.5281/zenodo.23497966)

**Published:** October 20, 2026. Original nine-edge proof disclosure:
October 18, 2026.

The archive contains the evidence ZIP, unchanged author-edited manuscript
PDF, [scope note](ARCHIVE-NOTE.md), [citation](CITATION.cff), and
[staged verification receipt](VERIFICATION.json). All five public downloads
were checked against their local SHA-256 hashes; see
[`publication.json`](publication.json).

## Reproduce this exact packet

Use a full clone at commit
`afb384ee910a6f25cadaeabb9cf8a74729a02666`, install the declared test
dependencies, and run:

```sh
python src/research_records.py package coprime-paths --output packet.zip
```

Expected SHA-256:
`ce2d2015c0238343633e6e4eeaca6849535c8ead52ada0d1355cbfd8392d8de6`
(16,072,364 bytes).

The packet freezes prepublication metadata. Current `main` records the
completed publication, so its newly generated packet has different metadata
bytes. Use the pinned commit above for the archived version. It contains
79 source files and 82 hashed payload files; the inventory is an additional
ZIP entry.

Extract the packet and follow its README. A fresh Python 3.10 environment
passed all 180 included tests and 10 auxiliary tests. Standalone checks
replayed the nine-edge certificates and the earlier eight-edge UNSAT proof.
The latter used `drat-trim` at
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`; exact commands and outputs are
in `VERIFICATION.json`.

The third-party journal style is excluded. The manuscript PDF and source
are retained, but recreating the journal layout requires its template
separately. Human mathematical review remains pending.

## Publication provenance

- [`duplicate-search.json`](duplicate-search.json): all 115 account
  depositions were examined before allocating this distinct contribution
  family.
- [`preparation.json`](preparation.json): consolidated-checkout checks.
- [`draft-reservation.json`](draft-reservation.json) and
  [`draft-validation.json`](draft-validation.json): historical draft state.
- [`zenodo-rdm-metadata.json`](zenodo-rdm-metadata.json): final applied
  metadata, including both MIT and CC BY 4.0 licenses.
- [`publication.json`](publication.json): public DOI, dates, file hashes,
  download URLs, and verification. The interrupted first ZIP download was
  retried using validated byte ranges; deposited files did not change.

Use the same version family for substantive evidence updates. Metadata-only
maintenance does not require a new DOI version. The archive establishes a
durable citation and disclosure record, not peer review or novelty.
