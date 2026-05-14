---
name: zenpause
description: Save the full state of the session before stepping away for hours. Commits and pushes everything committable, writes a detailed entry in docs/JOURNAL.md (completed tasks, current task with state, remaining tasks in order, technical decisions, open questions, git state), and flags attention points for the resume.
argument-hint: "[optional note, e.g. 'lunch break, resume with auth JWT']"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

You produce a complete handoff so the user (or yourself) can resume cleanly hours later.

**Output language:** Default to English. If `CLAUDE.md` exists at the project root and is written in French, OR if the existing journal (`docs/JOURNAL.md` or `JOURNAL.md`) contains French entries, write your output (confirmation message, new journal entry) in French. Otherwise English. Detect once and stay consistent across the whole skill execution.

## Workflow

### 0. Verify the working directory is a git repo

Run `git rev-parse --is-inside-work-tree`. If it fails, the project is not under git: skip step 1 and the "Git" section of step 3, write only the journal entry, and mention in the confirmation that no git checkpoint was made.

### 1. Commit + push everything committable

- Run `git status` and `git diff --stat` to see what changed.
- Run `git log -10 --oneline` to learn the project's commit message convention.
- For each modified file: if it is in a clean, working state, include it in the commit. If it is clearly WIP or half-written (broken syntax, stub functions, partial refactor), **do not commit it** — flag it in step 3 instead.
- Stage the clean files and commit with a message that **summarizes what was actually done this session**, not "WIP".
- If a remote is configured, run `git push`. If push fails for a missing upstream, set it (`git push -u origin <branch>`) and retry. Never use `--force` or `--no-verify`.

### 2. Locate (or create) the journal

Look for the journal in this order:

1. `docs/JOURNAL.md`
2. `JOURNAL.md` at the repo root
3. If neither exists, create `docs/JOURNAL.md` (run `mkdir -p docs` first).

### 3. Prepend a new entry to the journal

The newest entry goes **at the top** of the file. Use this structure (translate headings to French if the project is in French):

```markdown
## YYYY-MM-DD HH:MM — Pause

> Pause note: <text passed as argument, if any>

### Completed tasks (current iteration)
- ...

### Current task
- ... (precise state: what is done, what remains on this task)

### Remaining tasks (in order)
1. ...
2. ...

### Technical decisions made this session
- ...

### Open questions
- ...

### Git
- Branch: <branch>
- Last commit: <short sha> <message>

### Attention points for the resume
- (optional — refactors to do, uncommitted WIP files, tests to write, code smells)
```

Be specific. File paths, function names, the *why* behind each decision. Future-you must be able to act on this without re-reading the whole chat. Avoid generic phrases like "improved performance" — say *what* and *where*.

### 4. Confirm

Output exactly one short block — no preamble, no recap of the journal content:

```
State saved.
✓ Commit: <short sha> <message>
✓ Push: <branch> → <remote>   (or: "nothing to commit")
✓ Journal: docs/JOURNAL.md

Have a good break. On return: /zenresume
```

If anything failed (push refused, journal unwritable, uncommitted WIP files), say so explicitly with the affected files. Never claim success that did not happen.

## Rules

- Never commit files that look like secrets: `.env*`, `*.key`, `*.pem`, `*.pfx`, `*.p12`, `id_rsa*`, `credentials*`, `secrets*`, `.npmrc` with tokens, or anything else that looks sensitive. Trust the project's `.gitignore` first, but if something suspicious is staged, warn the user and unstage it.
- Never force-push or skip hooks.
- If `git status` is clean AND nothing meaningful happened this session, you may write a minimal journal entry ("session with no changes") and exit. Do not fabricate work.
- The journal is the single source of truth. Do not create a separate state file.
