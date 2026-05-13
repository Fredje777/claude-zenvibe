---
name: compact
description: Use when the user wants to compact the current conversation manually and wants a clean checkpoint first. Commits and pushes committable changes, writes a session-focused entry in docs/JOURNAL.md (what was done, decisions, files touched, next step), then outputs the /compact command with project-appropriate instructions ready to paste.
argument-hint: ""
allowed-tools: Bash, Read, Write, Edit
---

The user wants to compact the conversation. Make a clean checkpoint first, then hand them the `/compact` command to run.

## Workflow

### 1. Commit + push committable changes

- `git status` and `git log -5 --oneline` first.
- Stage cleanly-committable files. Skip half-written WIP (and warn the user about them — don't commit broken code).
- Commit with a meaningful message that summarizes the session, following the project's existing convention.
- Push if a remote is configured.

### 2. Update the journal

Append a new entry at the top of `docs/JOURNAL.md` (or `JOURNAL.md` at root). Create `docs/JOURNAL.md` if neither exists.

This entry is **session-focused**, not a full handoff like `/zenvibe:pause`:

```markdown
## YYYY-MM-DD HH:MM — Compact

### Fait dans cette session
- ...

### Décisions techniques
- ...

### Fichiers touchés
- path/to/file
- ...

### Prochaine étape claire
- ... (1 ligne actionnable)
```

Keep it tight. The point is to preserve what would otherwise be lost in compaction, not to write a sprint review.

### 3. Build the `/compact` instructions

Look for `.claude/zenvibe.md` in the project root. If present, use its content **verbatim** as the compact instructions — this lets each project define its own priorities.

If absent, use this generic template:

```
Garde en détail : les conventions du projet (commits, sécurité données, validations obligatoires), l'état d'avancement courant, les décisions techniques prises sur l'architecture et l'API, et toute question ouverte non résolue. Tu peux résumer brièvement les itérations de code et les tâtonnements.
```

### 4. Confirm and output the command

Output exactly:

```
Checkpoint OK.
✓ Commit : <sha> <message>   (ou : "rien à committer")
✓ Push : <branche> → <remote>   (ou : "pas de remote")
✓ Journal : docs/JOURNAL.md

Pour compacter maintenant, copie-colle :

/compact <instructions>
```

Replace `<instructions>` with the actual text from step 3, on a single line (no internal newlines) so it can be pasted directly.

## Rules

- **Never run `/compact` yourself.** Only output the command for the user to run. `/compact` is a UI-level action the user must trigger.
- Never commit broken WIP — warn instead and leave the files in place.
- If `git status` is clean and the journal already covers the current state, skip step 1 cleanly and still produce step 4.
- The custom `.claude/zenvibe.md` file is optional per project. Do not create it automatically — only read it if it exists.
