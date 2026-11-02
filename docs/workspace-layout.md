# Workspace and preservation

Use the repository itself as the normal place to work. On the author's
machine, the layout is:

```text
~/github/research/computational-explorations/    main checkout
    research/                                 durable contribution records
    docs/, src/, tests/, e-jc/                 tracked research and manuscript
    .local/                                   ignored local support files
        artifacts/                            builds and verification outputs
        recovery/                             preserved private worktree files
        consolidation-2026-10-20/              recovery bundle and receipts
~/github/research-records/                     public cross-project index
```

These absolute locations are conveniences, not research dependencies. Fresh
clones use the repository-relative instructions in
[`research/README.md`](../research/README.md).

## Worktrees are temporary

The coprime-path work was merged into public `main` in
[PR #11](https://github.com/queelius/computational-explorations/pull/11).
On October 20, its extra worktree was removed after preserving all local
files, and this original checkout was switched to `main`. The old Codex
compatibility symlink and empty project worktree directories were removed.

For future isolated work, use a short-lived worktree, merge the reviewed
changes, preserve any unique local files, and remove the worktree. Check
`git worktree list` before cleanup. A linked worktree shares Git objects and
does not provide an independent backup.

## Local support files

`/.local/` is explicitly ignored by `.gitignore`. The former sibling
`local-artifacts/computational-explorations/` directory was moved intact to
`.local/artifacts/`. Untracked worktree context was moved to
`.local/recovery/coprime-paths-worktree/` and checked against file hashes.

Use `.local/` for environments, raw logs, generated packets, and private
recovery copies. Relocated virtual environments can contain stale absolute
paths; recreate them as needed. Never upload this directory wholesale.
Promote useful findings, evidence, and reproduction instructions into tracked
files before treating scratch as disposable. Back up unique recovery
material before pruning it.

## Preserved unpublished work

The earlier checkout contained 23 local commits plus uncommitted edits,
including Schur investigations and journal revisions. Its complete
nonignored state is preserved on the local branch
`preserve/unpublished-2026-10-20` at
`c6f55df6662540da4eb9b68356449c22aa1a2ac0`.
The older recovery branches and stash also remain.

A separate Git bundle, file archive, and SHA-256 inventory are in
`.local/consolidation-2026-10-20/`. These contain private material and are
not public evidence. Inspect the preserved branch with `git show` or
`git diff`; integrate coherent changes selectively after reviewing them.
Do not merge or push the recovery branch wholesale.

The published path results are already in `main`. Older unpublished Schur
and editorial work remains a separate review queue, preserved rather than
implicitly approved by this cleanup. `AGENTS.md` was retained byte for byte.

## Durable records

Start at [`research/README.md`](../research/README.md). Source commits,
manuscript versions, proof evidence, review status, public disclosures, and
archives are recorded separately. A future researcher should be able to
resume from those files without an agent session or this machine.
