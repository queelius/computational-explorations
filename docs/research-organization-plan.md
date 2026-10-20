# Research Organization Implementation Plan

> For agentic workers: use the executing-plans workflow and preserve the
> original checkout. This dated plan records the authorized October 20, 2026
> organization task; ongoing instructions live in `research/README.md`.

**Goal:** Make research attributable, discoverable, reproducible, and reusable
without relying on an agent's hidden working directory or conversation.

**Architecture:** The owning repository retains source, evidence, manuscripts,
and structured contribution records. The cross-project `research-records`
repository indexes those records. Exact archived versions and dated public
disclosures are separate from development state and review status.

**Tech stack:** Git, JSON Schema, Python 3.10+, pytest, deterministic ZIP files.

**Spec:** The design and constraints below.

## Design and constraints

- Keep existing cited paths and the GitHub remote. Leave `AGENTS.md` unchanged.
- Preserve the dirty original checkout, local history, manuscript edits, and
  exploratory research before moving the active linked worktree.
- Use a visible worktree under `~/github/research/worktrees/`. Retain a
  compatibility symlink for existing session references.
- Store durable contribution metadata under `research/records/<id>/`.
  `research/catalog.json` locates records; a schema and validator enforce
  their contracts. Do not maintain independent copies of claim metadata.
- Record authors, ORCID, scope, assumptions, limitations, licenses, credits,
  evidence, exact source commits, reproduction commands, and review states.
- Record externally observable disclosure dates separately from Git author
  dates, DOI publication dates, and repository acceptance. Hashes identify
  bytes; they do not independently prove when those bytes became public.
- Generate citations and archive inventories from structured records.
  Packaging reads an explicit file allowlist from immutable Git commits.
  Reject missing, altered, duplicate, or escaping paths.
- Promote useful historical research notes with their original dates and
  limitations. Do not publish private session logs, environments, credentials,
  downloaded third-party papers, or unreviewed operational scratch.
- Index the first curated coprime-path contribution. Existing topic folders
  remain the inventory for other work pending contribution-specific review.
- Publish the reviewed source and central-index changes through GitHub.
  Do not create a DOI merely for this organizational change. The record must
  explicitly identify which results lack an archival DOI; existing unrelated
  DOIs must not be represented as archiving the new contribution.

## Review focus

1. A fresh clone must validate without local worktrees or hidden files.
2. Modified evidence, duplicate records, and path traversal must fail closed.
3. A package must rebuild identically and must not include unlisted files.
4. Metadata must not upgrade AI review into human review or a local date into
   an independently established public disclosure.
5. Existing historical evidence, cited releases, and user edits must survive.

## Tasks

### Task 1: Preserve and relocate the active work

- [x] Snapshot original files and Git references outside agent storage.
- [x] Relocate the linked worktree and compare file hashes.
- [x] Document the visible workspace and recovery locations.

### Task 2: Add contribution records and reproducible tooling

- [x] Write meaningful validator/packaging tests and observe expected failures.
- [x] Add the schema, catalog, validator, citation generation, and deterministic
  packaging from pinned Git objects.
- [x] Register coprime paths, scoped evidence, author revision provenance, and
  dated public events. Promote useful research notes with accurate status.
- [x] Run unit/integration tests, inspect coverage, and reproduce relevant
  finite checks. Verify a packet extracted outside the working tree.

### Task 3: Make the organization discoverable and durable

- [x] Link the records from the repository and manuscript documentation.
- [x] Add CI validation and the curated cross-project index entry.
- [x] Obtain an independent review; fix material issues and run checks.
- [ ] Commit and publish the source/index changes; verify public links and CI.
- [ ] Recheck preservation and record the remaining human-review and archival
  work in the contribution's lifecycle record.
