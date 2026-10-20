# Research records

This is the durable entry point for continuing, reproducing, citing, and
archiving this repository's research. The
[`catalog.json`](catalog.json) locates curated contribution records.
Existing `discoveries/` folders remain the broader topic inventory; inclusion
there alone does not certify a claim or publication readiness.

## Start here

- [Coprime paths](records/coprime-paths/README.md): exact nine-edge threshold,
  earlier certified values, linear bounds, manuscript, and review status.
- [Workspace and preservation](../docs/workspace-layout.md): active checkout,
  original local edits, and recovery records.
- [Cross-project research index](https://github.com/queelius/research-records):
  curated discovery, archival DOIs, and publication receipts.

## One contribution record

Use `research/records/<stable-id>/record.json` for structured facts:

- Exact claims, assumptions, evidence type, limitations, and unresolved work.
- Canonical author names, ORCID, predecessor credits, and AI assistance.
- Immutable source commits and per-file SHA-256 hashes and licenses.
- Reproduction commands as argument arrays, expected results, and scope.
- Separate public-disclosure, verification, acceptance, and archive events.
- Human review, formal verification, novelty assessment, and archive status.

The [JSON Schema](record.schema.json) defines the contract. Record IDs remain
stable; increment the record version for substantive changes. Cite an exact
version DOI when one exists, otherwise identify the immutable source commit
and the record version. An earlier paper's DOI must not be assigned to later
evidence it does not contain. The root `CITATION.cff` describes the historical
October 17 software release; use contribution-specific citations for new work.

Keep proofs, code, tests, certificates, and manuscripts in their existing
paths. Records link them; they do not create another authoritative copy.
Useful exploratory notes belong in a clearly labeled `exploration/` directory.
Private session logs, environments, temporary renders, and credentials do not
belong in public records. Promote unique useful findings before clearing
agent scratch. Update a record's next steps at every research handoff.

## Validate and reproduce

From a full Git clone, using Python 3.10 or later:

```sh
python -m pip install -c requirements-test.txt '.[test]'
python src/research_records.py validate
python src/research_records.py cite coprime-paths
python -m pytest -q tests/test_research_records.py
python src/research_records.py package coprime-paths --output /tmp/coprime-paths.zip
```

The validator checks metadata, references, working files, and pinned Git
objects. Fetch full history if a shallow clone lacks a source commit.
An evidence change requires a reviewed commit and updated pin and hash.
The packager reads only the explicit artifact list from Git, fixes ZIP
timestamps and permissions, and hashes every payload file. It refuses to
overwrite an existing output. Two builds from the same record and sources
must be byte-identical. Reproduction commands are displayed, never silently
executed by metadata validation or packaging.

## Public disclosure and archives

Publish verified source and evidence with a dated public release or PR and
record its URL. Preserve corrections as successor records; never rewrite
historical evidence or claim a Git author timestamp proves public availability.
Hashes establish artifact identity, while publicly observable events document
disclosure. Neither by itself certifies correctness, novelty, or legal priority.

For archival publication, follow the central index's
[PUBLISHING.md](https://github.com/queelius/research-records/blob/main/PUBLISHING.md):
search all existing Zenodo records, reuse the appropriate version family,
stage a self-contained packet, rerun its checks, inspect metadata, publish
when authorized, and verify public downloads against local hashes.
Record the exact version DOI and publication date separately from earlier
disclosure. Add the canonical source and archival links to the central index.
An organization-only change does not warrant a new DOI.

After committing a record, derive its central-index metadata with:

```sh
python src/research_records.py export-index coprime-paths \
  --metadata-commit FULL_COMMIT_SHA
```

This exports a curated subset with a hash and immutable URL for the owning
record. It refuses to label uncommitted metadata as that commit. Add the
result to the central catalog with a short README; regenerate it after
substantive source-record changes instead of editing parallel factual copies.
