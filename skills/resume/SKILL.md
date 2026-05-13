---
name: resume
description: Use when the user is starting a session after a pause or compaction and wants to re-establish context before doing anything. Reads docs/JOURNAL.md in full, reads CLAUDE.md for project conventions, checks git state, summarizes where things stand, proposes a concrete next action, and waits for explicit confirmation before touching code.
argument-hint: ""
allowed-tools: Bash, Read
---

The user is resuming after a pause or after a conversation compaction. Re-establish context properly **before doing anything else**.

## Workflow

### 1. Read the journal in full

- Try `docs/JOURNAL.md`. If absent, try `JOURNAL.md` at the repo root.
- If neither exists, tell the user: "Pas de JOURNAL trouvé. Tu veux qu'on en démarre un, ou tu préfères me briefer à l'oral ?" — then stop and wait.
- Read the journal **entirely**. The most recent entry matters most, but earlier ones carry deferred decisions, refactors, and context that still apply.

### 2. Read project conventions

Read `CLAUDE.md` at the project root if present. Note the conventions on commits, naming, security, validations, testing — these guide everything you do this session. If multiple `CLAUDE.md` exist in subdirectories, read the one closest to the work area mentioned in the journal.

### 3. Check the actual git state

Run, in parallel:
- `git status`
- `git log -5 --oneline`
- `git branch --show-current`

Compare with the "Git" section of the most recent journal entry. If they diverge (new commits, uncommitted changes that were not there before, different branch), flag it in your summary.

### 4. Produce a compact briefing

Output exactly this structure, filled from what you read:

```
Repris depuis docs/JOURNAL.md (entrée du <date heure>)

Tu étais sur : <tâche en cours>
Fait depuis la pause : <commits visibles depuis la pause, ou "rien">
Reste sur cette tâche : <points non terminés>
Prochaine action proposée : <1 phrase concrète, actionnable>

Points d'attention notés à la pause :
- ...

Conventions actives (CLAUDE.md) : <2-3 puces si pertinent pour la prochaine action>

Je reprends ? (oui / non / autre direction)
```

Keep it under 25 lines. The user wants context, not a re-narration of the journal.

### 5. Wait for explicit go-ahead

**Do not** edit files, run mutating commands, or start the proposed action until the user explicitly confirms ("oui", "go", "vas-y", "ok", "yes" — any clear assent).

- If the user redirects ("non, fais plutôt X"), pivot immediately — the journal context is now in your head, you can act on the new direction without re-reading.
- If the user asks a clarifying question first, answer it from the journal, then ask again for the go.

## Rules

- Read-only during resume. No edits, no commits, no migrations, nothing mutating until the user says go.
- If the journal is long, read it all anyway. Context wins over token economy here.
- Match the journal's language in your briefing (French if the journal is in French).
- Be honest if the journal is sparse, contradictory, or doesn't cover what the user is asking about — say so and ask.
