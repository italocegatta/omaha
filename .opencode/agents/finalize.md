---
description: Sync, archive, condense roadmap record, order next slices, commit, and push one slice
mode: subagent
permission:
  read: allow
  edit: allow
  glob: allow
  grep: allow
  bash: allow
  skill: allow
  task: allow
  todowrite: allow
  question: allow
---

You are finalize.

Workflow — follow this order exactly:
1. Load `openspec-sync-specs`.
2. Load `openspec-archive-change`.
3. Read selected slice in `openspec/roadmap.md`, linked change, and `openspec/config.yaml`. Use exact `Candidate OpenSpec change id`.
4. Confirm review resolved test drift and all configured quality-gate requirements pass. Do not change code or tests during finalization; return failed work to the orchestrator for `apply` and `review`.
5. **FIRST: Sync delta specs from the change to main specs.** This is mandatory before archiving. Never skip sync.
6. **THEN: Archive the applied change.** Only after sync succeeds.
7. **AFTER archive: Run repository OpenSpec spec verification.** Do not recommend a next slice if verification fails.
8. **THEN: Update `openspec/roadmap.md`.** Condense finalized change entry and order ready next slices as specified below.
9. Run refresh-for-test receipt when runtime code is touched.

**Rule: sync ALWAYS runs before archive. No exceptions.** If sync fails, do not archive — report the error to the orchestrator.

## Post-archive roadmap gate

After archive and successful spec verification, before `git add` and commit,
update `openspec/roadmap.md`. Mark slice `Archived` with archive path and date,
then reduce its entry to essential record:

- Change title and final status/date.
- One concise sentence describing the goal or delivered outcome.
- Archive path.
- One short caveat only when needed for future reactivation or operation.

Remove implementation logs, verbose `Progress`, test counts, file lists,
acceptance criteria, design decisions, and other detail already preserved in
the main specs or archived change. Never copy `proposal.md`, `design.md`, or
`tasks.md` content into the roadmap. The roadmap is a planning register, not
the change history.

Then inspect `Ready` slices and, only when recommendation changes, update
`## Recommended Execution Order` with logical next work:

- Put unblocked prerequisites before dependent slices.
- Prefer slices that unlock the most subsequent work or reduce current risk.
- Respect domain and global `Applying` WIP limits.
- Add one short reason note for a changed order.
- Do not create, delete, rewrite, or reopen slices. Do not alter lifecycle,
  priority, candidate change id, spec link, or archived change folders.

Verify roadmap diff is concise: finalized slice is reduced, next-slice order
reflects dependencies, and no unrelated planning content changed. Only then
continue with Git finalization.

Git finalization:
- After archiving: `git add` all tracked changes related to the slice.
- Check for modified files unrelated to the change via `git status`.
- If unrelated modified files exist: ask via `question` tool whether to include them.
- Commit with clear message referencing the slice id.
- `git push` to remote — **use timeout 480000ms (8 minutes)**; pre-commit hooks run lint + tests on push.
- Verify worktree is clean (`git status --porcelain` should be empty).

Constraints:
- Do not implement code.
- Do not reopen scope.
- Do not touch unrelated slices unless explicitly confirmed by user.
