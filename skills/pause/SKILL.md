---
name: pause
description: Use when the user signals they are stepping away from the session for hours or longer and wants a clean, thorough handoff. Commits and pushes everything committable, writes a detailed progress entry in docs/JOURNAL.md (completed tasks, current task with state, remaining tasks in order, technical decisions, open questions, git state), flags attention points for the resume, and confirms in one short message.
argument-hint: "[note optionnelle: ex. 'pause déjeuner, reprendre par l'auth JWT']"
allowed-tools: Bash, Read, Write, Edit
---

The user is stepping away. Produce a thorough handoff so they (or you) can pick up cleanly hours later.

## Workflow

### 1. Commit + push everything committable

- Run `git status` and `git diff --stat` to see what changed.
- Run `git log -10 --oneline` to learn the project's commit message convention.
- For each modified file: if it is in a clean working state, include it in the commit. If it is clearly WIP or half-written (broken syntax, stub functions, partial refactor), **do not commit it** — instead, flag it in step 3.
- Stage the clean files and commit with a message that **summarizes what was actually done this session**, not "WIP".
- If a remote is configured, `git push`. If push fails because of missing upstream, set it (`git push -u origin <branch>`) and retry. Never use `--force` or `--no-verify`.

### 2. Locate (or create) the journal

Look for the journal in this order:

1. `docs/JOURNAL.md`
2. `JOURNAL.md` at the repo root
3. If neither exists, create `docs/JOURNAL.md` (`mkdir -p docs` first).

### 3. Append a new entry at the top of the journal

The newest entry goes at the top (most recent first). Use this structure — adapt headings to the journal's existing language (French/English) if it is already established:

```markdown
## YYYY-MM-DD HH:MM — Pause

> Note de pause: <texte fourni en argument, si présent>

### Tâches terminées (itération en cours)
- ...

### Tâche en cours
- ... (état précis : ce qui est fait sur cette tâche, ce qui reste à faire dessus)

### Tâches restantes (par ordre)
1. ...
2. ...

### Décisions techniques prises cette session
- ...

### Questions ouvertes
- ...

### Git
- Branche : <branche>
- Dernier commit : <sha court> <message>

### Points d'attention pour la reprise
- (optionnel — refactos à faire, fichiers WIP non commités, tests à écrire, code smells repérés)
```

Be specific. File paths, function names, the *why* behind each decision. Future-you must be able to act on this without re-reading the whole chat. Avoid generic phrases like "improved performance" — say *what* and *where*.

### 4. Confirm

Output exactly one short block — no preamble, no recap of the journal content:

```
État sauvegardé.
✓ Commit : <sha court> <message>
✓ Push : <branche> → <remote>   (ou : "rien à committer")
✓ Journal : docs/JOURNAL.md

Bonne pause. Au retour : /zenvibe:resume
```

If anything failed (push refused, journal unwritable, WIP files left uncommitted), say so explicitly with the affected files. Never claim success that did not happen.

## Rules

- Never commit files that look like secrets: `.env`, `*.key`, `*.pem`, `credentials*`, `secrets*`. Warn the user instead.
- Never force-push or skip hooks.
- If `git status` is clean AND nothing meaningful happened this session, you may write a minimal journal entry ("session sans changements") and exit. Do not fabricate work.
- Match the journal's existing language. Default to French if the project is in French (look at CLAUDE.md or recent commits).
- The journal is the single source of truth. Do not create a separate state file.
