# Workspace and preservation

The active coprime-path worktree was relocated on October 20, 2026:

```
~/github/research/computational-explorations/
    Original checkout and shared Git object store; local edits preserved.
~/github/research/worktrees/computational-explorations/coprime-paths/
    Active research, manuscript, and contribution records.
~/github/research/local-artifacts/computational-explorations/
    Private preservation receipts, backups, and reproducible build outputs.
~/github/research-records/
    Public cross-project discovery and archive index.
```

These paths describe this machine, not dependencies of the research.
Fresh clones use repository-relative paths and the committed reproduction
instructions. Run `git worktree list` to discover current local checkouts.

The old `~/.codex/worktrees/4559/computational-explorations` path is a
compatibility symlink to the visible worktree. It contains no independent
research copy. New durable work belongs in tracked repository files.
Agent state, virtual environments, render previews, and raw session logs
are operational scratch. Preserve any unique useful result in a contribution
record before removing scratch.

## Original checkout

The original checkout remains on `local/research-2026-10-18`. Do not reset,
clean, switch, or bulk-merge it: it contains unpublished user work. The linked
worktree shares its Git object store, so it is not an independent backup.

Local recovery references include `preserve/local-history-2026-10-18` and
`preserve/local-edits-2026-10-18`. The latter identifies snapshot
`d06d0a29ee3aaefee5b0b967af02e752701d25a8`. A fresh October 20 file archive,
Git bundle, hash inventory, and relocation receipt are in
`local-artifacts/computational-explorations/organization-2026-10-20/`
under the research directory above.

The earlier reconciliation identified five overlapping paths requiring
selective review: `README.md`, `docs/coprime-ramsey-corrections.md`,
`e-jc/coprime-ramsey-ejc.tex`, `e-jc/coprime-ramsey-ejc.pdf`, and
`pyproject.toml`. Other local-only material also remains preserved.
Reconciliation is a separate task; this organizational change does not
approve or publish that material.

## Durable records

Start at [`research/README.md`](../research/README.md). Source commits,
manuscript versions, proof evidence, review status, public disclosures, and
archives are recorded separately. A future researcher should be able to
resume from those files without an agent session or this machine.
