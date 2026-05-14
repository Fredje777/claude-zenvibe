# ZenVibe — Public Release Design

**Date:** 2026-05-13
**Status:** Approved for implementation
**Target:** Open-source ZenVibe on GitHub at `Fredje777/claude-zenvibe` (public, MIT).

---

## 1. Goal

Take the locally-working ZenVibe plugin and publish it on GitHub for a broader audience — primarily **junior "vibe coders"** who want to chat-and-ship with Claude without losing context, work, or audit trail.

Two big changes from the current state:

1. **Language:** all source code, docs, and command bodies move from mixed French/English to **English**. Runtime output stays **smart bilingual** (English by default, French when the host project is French).
2. **Repo polish:** add LICENSE, CHANGELOG, repo URLs, and a public-facing README opening with a tagline-driven intro aimed at the target audience.

No new features. No architectural changes. No file renames. Existing slash commands (`/zenpause`, `/zenresume`, `/zencheckpoint`), MCP tools (`zenvibe_pause`, `zenvibe_resume`, `zenvibe_checkpoint`), and hooks (`PreCompact`, `SessionStart`) keep their names.

---

## 2. Non-goals

- No new commands, no new hooks, no new MCP tools.
- No marketplace integration (decided: install manuel for v0.1).
- No CONTRIBUTING.md, Code of Conduct, issue/PR templates, demo GIFs (v0.1+).
- No marketing/landing page beyond the README.
- No automated release pipeline (manual `gh repo create` + push).

---

## 3. Translation plan

### 3.1 Source files → 100% English

These files become English-only:

- `README.md` (full rewrite — see §4)
- `commands/zenpause.md`, `commands/zenresume.md`, `commands/zencheckpoint.md` (frontmatter `description` + body)
- `hooks/pre-compact-prompt.md`
- `hooks/session-start-prompt.md`
- `hooks/scripts/session-start-briefing.py` (comments + docstring)
- `mcp/server.py` (module docstring, function docstrings, comments, error messages)
- `docs/web-project.md` (the claude.ai web Project preset — its system prompt is currently FR and stays inline, but the surrounding doc becomes EN; the system prompt itself moves to EN and Claude follows project-language for output)
- `scripts/sync-install.sh` (echo strings)
- `.claude-plugin/plugin.json` `description` field

### 3.2 Runtime output → smart bilingual

The *content* the plugin writes/displays adapts to project language. Two mechanisms:

**A. Slash commands (Claude interprets the body):**

Each command body adds an explicit rule near the top:

> **Output language:** Default to English. If `CLAUDE.md` exists at the project root and is written in French, OR if the journal (`docs/JOURNAL.md` or `JOURNAL.md`) already contains French entries, write your output (confirmation messages, new journal entry) in French. Otherwise English. Apply the same rule consistently across the whole skill execution.

Claude already reads CLAUDE.md / journal as part of the workflow (for /zenresume) or has them in tool reach. The detection is a tiny additional read.

**B. MCP tools (Python):**

Add an optional argument to all three tools:

```python
language: Literal["en", "fr"] = "en"
```

Claude detects language client-side (using its `Read` tool on CLAUDE.md / JOURNAL.md) and passes `language="fr"` when applicable. The server keeps localized strings in a small dict:

```python
MESSAGES = {
    "en": {
        "safe_to_compact": "🧘 It's safe to compact now. Type /compact to proceed.",
        "checkpoint_partial": "⚠ Partial checkpoint — fix the git errors before compacting.",
        "pause_heading": "Pause",
        "checkpoint_heading": "Checkpoint",
        # …
    },
    "fr": {
        "safe_to_compact": "🧘 Tu peux compacter sans risque. Tape /compact pour lancer.",
        "checkpoint_partial": "⚠ Checkpoint partiel — corrige les erreurs git avant de compacter.",
        "pause_heading": "Pause",
        "checkpoint_heading": "Checkpoint",
        # …
    },
}
```

All section headers and templates use the dict. The Python code (variable names, comments) stays English regardless.

### 3.3 Brand and identifiers (unchanged)

| Item | Value |
|---|---|
| Display name | ZenVibe |
| Plugin name | `zenvibe` |
| Commands | `/zenpause`, `/zenresume`, `/zencheckpoint` |
| MCP tools | `zenvibe_pause`, `zenvibe_resume`, `zenvibe_checkpoint` |
| Per-project config | `.claude/zenvibe.md` |

---

## 4. README structure (new)

Top-to-bottom outline of the new `README.md`:

### 4.1 Header & intro (the "Draft D" we agreed on)

```markdown
# ZenVibe

> Vibe-code with a safety net.

You chat. Claude codes. You ship. Magic, right?

But sometimes Claude forgets. Sometimes you walk away and come back lost. Sometimes you push code that "looked right" — and find a half-finished file in main two days later.

**ZenVibe is a Claude Code plugin that catches you when you fall.**

| Command | When to use |
|---|---|
| `/zenpause` | Walking away. Commits, pushes, writes a full recap. |
| `/zenresume` | Coming back. Reads the recap, tells you where you were. |
| `/zencheckpoint` | Before compacting. Saves your state cleanly. |

It also works **automatically**: every time Claude compacts a conversation, ZenVibe checkpoints first. Every time you reopen a recent project, ZenVibe greets you with a one-line briefing of where you left off.

You keep the vibe. ZenVibe keeps the safety.
```

### 4.2 Sections that follow (in order)

1. **Requirements** — Claude Code v2.x or later, Git, `uv` (only if you want the MCP server on desktop).
2. **Quick start** — 3-line install (clone, run sync script, restart Claude Code).
3. **What's in the box** — the table of commands + hooks + MCP tools + web project preset.
4. **Surface coverage** — kept table from current README (terminal / VS Code / desktop / web).
5. **Installation details** — sub-sections per surface.
6. **Project journal — how it works** — explains `docs/JOURNAL.md` as single source of truth.
7. **Per-project customization** — `.claude/zenvibe.md` for custom `/compact` instructions.
8. **Architecture** — file tree.
9. **Why "ZenVibe"?** — short note on the name + audience (kept light, no manifesto).
10. **Contributing** — single line: "PRs welcome. Open an issue first for non-trivial changes."
11. **License** — MIT, link to LICENSE file.

---

## 5. New files

### 5.1 `LICENSE`

Standard MIT license text. Copyright year 2026, holder "Fred Fonteyne".

### 5.2 `CHANGELOG.md`

Minimal, single entry for v0.1.0:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] — 2026-05-13

### Added
- Three slash commands: `/zenpause`, `/zenresume`, `/zencheckpoint`
- Two automatic hooks: `PreCompact`, `SessionStart`
- MCP server with `zenvibe_pause`, `zenvibe_resume`, `zenvibe_checkpoint` tools (for the Claude desktop app)
- Web Project preset for claude.ai (`docs/web-project.md`)
- Smart bilingual output (English default, French when project uses French)

### Notes
- Initial public release.
```

### 5.3 Updates to `.claude-plugin/plugin.json`

Add:

```json
{
  "homepage": "https://github.com/Fredje777/claude-zenvibe",
  "repository": "https://github.com/Fredje777/claude-zenvibe"
}
```

Keep existing fields (name, displayName, version, description in English, author, keywords, license).

### 5.4 `.gitignore` additions

Append:

```
*.backup-*
.idea/
*.iml
```

---

## 6. Publication workflow

After all source changes are committed locally:

```bash
cd "/Users/fred/Claude app/zenvibe"
gh repo create Fredje777/claude-zenvibe \
  --public \
  --source=. \
  --description "Vibe-code with a safety net. Pause/resume/checkpoint sessions in Claude Code, with auto-protection before context compaction." \
  --push
```

This creates the public repo, sets the remote, and pushes all current commits in one shot. No squash — full history goes up (it shows the iteration honestly).

After push:
- The user manually verifies the repo on github.com
- We do NOT update the local install (`~/.claude/plugins/zenvibe/`) yet — the source-of-truth dir stays at `/Users/fred/Claude app/zenvibe/`. To pick up the English changes locally, the user runs `./scripts/sync-install.sh` and restarts Claude surfaces.

---

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Smart bilingual mis-detection (Claude writes EN in a FR project) | The rule is explicit and conservative: only switch to FR when *clear* signals exist (CLAUDE.md FR content, OR existing FR journal). Default to EN. |
| Public README too marketing-y / off-putting for senior devs | Intro is upbeat but short. The sections that follow are technical and neutral. Senior devs skip the intro and land on "What's in the box". |
| MCP tool schema change (added `language` param) breaks existing client integrations | The user is the only consumer right now. After release, the param is optional with a default — fully backward compatible. |
| `gh repo create` fails (name taken, network) | Manual fallback: create on github.com UI, then `git remote add origin … && git push -u origin main`. |
| Smart bilingual increases token usage (Claude reads CLAUDE.md + journal just to detect language) | Already done as part of the existing workflow for `/zenresume`. For `/zenpause` and `/zencheckpoint`, the language check is a small additional read — acceptable. |

---

## 8. Out of scope (explicit)

- Marketplace.json — deferred.
- CI workflows (linting, testing) — none for v0.1; can add later if the plugin grows.
- Localization beyond EN/FR — only EN/FR for now (the two languages the author actively uses); the MCP `language` param is `Literal["en", "fr"]` for now, extensible later.
- Renaming of commands/MCP tools — frozen at current names.

---

## 9. Approval

This design was iterated and approved across three sections (translation plan, intro text draft D, repo polish) on 2026-05-13.

Next step: writing-plans skill → implementation plan → execution.
