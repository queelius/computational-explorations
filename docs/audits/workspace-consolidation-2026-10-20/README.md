# Workspace consolidation — October 20, 2026

At the author's request, the original repository became the primary `main`
checkout. The coprime-path work was already merged publicly; its extra
worktree and old compatibility symlink were removed. Local artifacts now
live under the repository's explicitly ignored `.local/` directory.

The [structured receipt](receipt.json) records the locations, Git references,
preservation checks, and remaining work. Before switching, all 331 original
nonignored path states were saved in a named local branch, independent Git
bundle, file archive, and hash inventory. All 61,513 local files and symlinks
from the removed worktree were moved and checked. `AGENTS.md` was retained
without changing its bytes.

The [workspace guide](../../workspace-layout.md) describes daily use and
recovery. Private backups and raw agent context remain local; verified
research, reproduction instructions, and publication receipts are tracked.
Older unpublished work remains available for selective review.

## Durable research

- [Coprime-path archive](../../../research/records/coprime-paths/archive/README.md):
  exact evidence packet, manuscript, citation, and public-download receipt.
- [Schur archive handoff](../../schur-archive-handoff-2026-10-20.md):
  the existing June manuscript and the independently replayed lower witness.
- [Central index](https://github.com/queelius/research-records):
  curated source pins, claims, archive versions, and citations.

## Operational correction

The initial stash command saved the edits but its cleanup failed because an
explicit excluded `.local` path was itself ignored. No data was lost.
The complete original state and recovery-branch blobs were checked before
restoring only the staged paths from the old HEAD and switching branches.
For future cleanup, avoid passing ignored directories as explicit stash
pathspecs; always inspect both the stash and working state after an error.
