---
name: zenresume
description: Re-establish context after a pause or compaction. Reads docs/JOURNAL.md in full, reads CLAUDE.md for project conventions, checks git state, summarizes where things stand, proposes a concrete next action, and waits for explicit confirmation before touching code.
argument-hint: ""
allowed-tools:
  - Bash
  - Read
---

The user is resuming after a pause or a conversation compaction. Re-establish context properly **before doing anything else**.

**Output language:** Default to English. If `CLAUDE.md` is in French OR the journal contains French entries, write your briefing in French. Otherwise English.

## Workflow

### 1. Read the journal in full

- Try `docs/JOURNAL.md`. If absent, try `JOURNAL.md` at the repo root.
- If neither exists, say: "No JOURNAL found. Want to start one, or would you rather brief me verbally?" — then stop and wait.
- Read the journal **entirely**. The latest entry matters most, but earlier ones carry deferred decisions, refactors, and context still in play.

### 2. Read project conventions

Read `CLAUDE.md` at the project root if present. Note the conventions on commits, naming, security, validations, testing — they guide everything you do this session. If multiple `CLAUDE.md` exist in subdirectories, read the one closest to the work area mentioned in the journal.

### 3. Check the actual git state

Run, in parallel:
- `git status`
- `git log -5 --oneline`
- `git branch --show-current`

Compare with the "Git" section of the latest journal entry. If they diverge (new commits, unexpected uncommitted changes, different branch), flag it in your summary.

### 4. Produce a compact briefing

Output exactly this structure, filled from what you read:

```
Resumed from docs/JOURNAL.md (entry of <date time>)

You were on: <current task>
Since the pause: <commits visible since pause, or "nothing">
Remaining on this task: <unfinished points>
Proposed next action: <one concrete, actionable sentence>

Attention points noted at pause:
- ...

Active conventions (CLAUDE.md): <2–3 bullets if relevant to the next action>

Shall I resume? (yes / no / different direction)
```

Keep it under 25 lines. The user wants context, not a re-narration of the journal.

### 5. Wait for an explicit go-ahead

**Do not** edit files, run mutating commands, or start the proposed action until the user explicitly confirms ("yes", "go", "ok", "oui", "vas-y" — any clear assent).

- If the user redirects ("no, do X instead"), pivot immediately — the journal context is now in your head, you can act on the new direction without re-reading.
- If the user asks a clarifying question first, answer it from the journal, then ask for the go again.

## Rules

- Read-only during resume. No edits, no commits, no migrations, nothing mutating until the user says go.
- If the journal is long, read it all anyway. Context wins over token economy here.
- Match the language of the journal in your briefing.
- Be honest if the journal is sparse, contradictory, or doesn't cover what the user is asking about — say so and ask.
