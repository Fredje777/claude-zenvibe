---
name: zencheckpoint
description: Save the current session state WITHOUT compacting — commit + push committable files, write a session-focused entry in docs/JOURNAL.md (what was done, decisions, files touched, next step), then confirm it is safe to compact. Use as a mid-task bookmark, or right before typing /compact manually.
argument-hint: ""
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

The user wants to save the current state without destroying context. You make a clean checkpoint, then confirm they can compact safely if they wish.

**Output language:** Default to English. If `CLAUDE.md` is in French OR the journal contains French entries, write your output in French. Otherwise English.

**Important:** you never run `/compact` yourself. Claude Code explicitly excludes `/compact` from the `SlashCommand` tool. Compaction stays an action the user triggers manually. Your role here is solely to secure context beforehand.

The `PreCompact` hook does the same work automatically if the user types `/compact` without running this skill first — so this skill is essentially an *on-demand checkpoint*, also useful mid-task to bookmark without compacting.

## Workflow

### 0. Verify the working directory is a git repo

Run `git rev-parse --is-inside-work-tree`. If it fails, skip step 1 entirely, write only the journal entry, and mention "not a git repo" in the confirmation.

### 1. Commit + push committable changes

- Run `git status` and `git log -5 --oneline` first.
- Stage clean files. Skip half-written WIP (and warn the user — never commit broken code).
- Commit with a meaningful message that summarizes the session, following the project's existing convention.
- Push if a remote is configured.

### 2. Update the journal

Prepend a new entry at the top of `docs/JOURNAL.md` (or `JOURNAL.md` at root). Create `docs/JOURNAL.md` if neither exists.

This entry is **session-focused**, shorter than a full handoff:

```markdown
## YYYY-MM-DD HH:MM — Checkpoint

### Done this session
- ...

### Technical decisions
- ...

### Files touched
- path/to/file
- ...

### Clear next step
- ... (one actionable line)
```

Keep it tight. The point is to bookmark the state, not write a sprint review.

### 3. Confirm

Output exactly this block, no more, no less:

```
✓ Checkpoint
✓ Commit: <sha> <message>   (or: "nothing to commit")
✓ Push: <branch> → <remote>   (or: "no remote")
✓ Journal: docs/JOURNAL.md

🧘 It's safe to compact now. Type /compact to proceed.
```

If something failed (push refused, journal unwritable, uncommittable WIP), list it explicitly in place of the relevant `✓` line, and **omit** the final `🧘 It's safe to compact` line — precisely because we do not want to invite a compaction when the checkpoint is not clean.

### 4. Custom `/compact` instructions (optional)

If the user wants custom instructions when they later type `/compact`, they can keep them in `.claude/zenvibe.md` in their project. You do **not** read it here and you do not display it — that file is just available for them to copy-paste into `/compact <text>` when they decide.

## Rules

- **Never run `/compact` yourself.** It is explicitly excluded from the `SlashCommand` tool. The user alone triggers compaction.
- Never commit broken WIP — warn instead and leave the files in place.
- Never commit anything that looks like a secret (`.env*`, `*.key`, `*.pem`, `credentials*`, etc.).
- If `git status` is clean and the journal already covers the current state, say so plainly and still emit the `🧘 It's safe to compact now` message.
- The `PreCompact` hook will redo the same work if the user types `/compact` afterwards — it is idempotent and safe.
