# ZenVibe — Public Release Design

**Date:** 2026-05-13
**Status:** Approved for implementation
**Target:** Open-source ZenVibe on GitHub at `Fredje777/claude-zenvibe` (public, MIT).

---

## 1. Goal

Take the locally-working ZenVibe plugin and publish it on GitHub for a broader audience — primarily **junior "vibe coders"** who want to chat-and-ship with Claude without losing context, work, or audit trail.

Three big changes from the current state:

1. **Language:** all source code, docs, and command bodies move from mixed French/English to **English**. Runtime output stays **smart bilingual** (English by default, French when the host project is French).
2. **Hassle-free installer:** a single `install.sh` that covers all three surfaces (CC CLI / VS Code, Claude desktop app, instructions for claude.ai web), with preflight checks for all required tools and a clear summary of what was done.
3. **Repo polish:** add LICENSE, CHANGELOG, repo URLs, and a public-facing README opening with a tagline-driven intro aimed at the target audience.

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
- `.claude-plugin/plugin.json` `description` field
- `scripts/sync-install.sh` is **removed** (replaced by `install.sh` at the repo root — see §10).

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

### 5.5 `install.sh` (new)

User-facing installer at the repo root. Detailed behavior in §10.

### 5.6 `uninstall.sh` (new)

Clean removal of plugin files + JSON config entries (restores from backup if any). Detailed in §10.

### 5.7 `docs/INSTALL.md` (new)

Extended install guide: prerequisites, surface-by-surface details, manual fallback if `install.sh` fails, troubleshooting, uninstall, FAQ. Linked from README "Quick start" and "Troubleshooting" sections.

---

## 6. Installer (`install.sh`) — detailed design

The installer is **the** main UX of v0.1. It must Just Work for someone who clones the repo on a fresh Mac.

### 6.1 Usage

```bash
./install.sh           # full install (CC CLI + VS Code; desktop app if available)
./install.sh --check   # preflight checks only, no changes
./install.sh --cli     # CC CLI only, skip desktop config
./install.sh --help    # usage
```

### 6.2 Preflight checks (always run, never skipped)

| Tool / path | Required for | Failure handling |
|---|---|---|
| `git` | Plugin commands (commit/push) and clone | Hard fail with install hint (`brew install git` or `https://git-scm.com/`) |
| `python3` | SessionStart hook + MCP server | Hard fail with install hint |
| `rsync` | File copy | Hard fail with install hint |
| `uv` | MCP server (desktop) | Soft warn; if missing, desktop config is skipped with explanation |
| `~/.claude/` exists | CC CLI installed | Hard fail with link to https://claude.com/code |
| `~/Library/Application Support/Claude/` exists (macOS only) | Desktop app installed | Soft warn; if missing, desktop config is skipped |
| OS is macOS | Desktop config path | Soft warn on Linux/Windows; CC CLI install proceeds, desktop section is skipped |

Each check prints `✓ <tool>` or `✗ <tool> — <fix hint>`. A summary table at the end of preflight tells the user *what* will be installed and *what* will be skipped (with reasons), before any change is made.

The user is asked **one yes/no confirmation** before the actual install starts (skippable with `--yes`). This is the "no surprises" gate.

### 6.3 Install actions (idempotent, safe to re-run)

In order:

1. **Backup existing JSON configs** (timestamped):
   - `~/.claude/plugins/installed_plugins.json` → `.backup-YYYYMMDD-HHMMSS`
   - `~/.claude/settings.json` → `.backup-YYYYMMDD-HHMMSS`
   - `~/Library/Application Support/Claude/claude_desktop_config.json` → `.backup-YYYYMMDD-HHMMSS` (macOS only)
   - Backups are kept for the user to restore manually if needed; we don't auto-delete.

2. **Copy plugin files** to `~/.claude/plugins/zenvibe/` via rsync (`--delete --exclude .git/ --exclude '*.backup-*'`).

3. **Register the plugin** in `~/.claude/plugins/installed_plugins.json`:
   - Add or update key `zenvibe@local`
   - `scope: "user"`, `installPath: "~/.claude/plugins/zenvibe"`, `version` from `plugin.json`, current timestamp

4. **Enable the plugin** in `~/.claude/settings.json`:
   - Set `enabledPlugins["zenvibe@local"] = true`

5. **Configure desktop MCP** in `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS only, if `uv` and desktop app are both present):
   - Add or update `mcpServers.zenvibe = { command: "<uv path>", args: ["run", "--script", "<install dir>/mcp/server.py"] }`
   - Resolves `<uv path>` via `command -v uv` so it works regardless of whether `uv` is in `/opt/homebrew/bin` or `/usr/local/bin`.

6. **Print a final summary** with three sections:
   - **CC CLI / VS Code:** "✓ Installed. Restart your `claude` session or VS Code Claude Code panel."
   - **Desktop app:** "✓ MCP configured. Quit (Cmd+Q) and reopen Claude.app." OR "⚠ Skipped — <reason>."
   - **Web (claude.ai):** "→ Manual step: see `docs/web-project.md` for the Project preset to paste into claude.ai."

### 6.4 JSON manipulation safety

All JSON edits go through `python3 -c` snippets (not `sed`/`jq`/`awk`), with:
- Read → parse → modify → atomic rewrite (`tmp` file + `os.replace`)
- Validation that the result parses as JSON before writing
- Backups already taken in step 1

### 6.5 Uninstaller (`uninstall.sh`)

Symmetric to install:

1. Confirm with the user.
2. Remove `~/.claude/plugins/zenvibe/` directory.
3. Remove `zenvibe@local` key from `installed_plugins.json` and `settings.json`.
4. Remove `mcpServers.zenvibe` from `claude_desktop_config.json`.
5. Backups created before each edit (same convention as install).

It does NOT delete the user's `docs/JOURNAL.md` files in their projects — those are user data.

### 6.6 Cross-platform note (v0.1 stance)

- **macOS:** full support, both CC CLI and desktop.
- **Linux:** CC CLI install supported; desktop section skipped (no Claude desktop app on Linux as of this writing).
- **Windows:** untested; installer prints a clear "Windows support is community-best-effort" notice and skips desktop config. CC CLI parts likely work via WSL or native Git Bash.

This is documented in README "Requirements" and in `docs/INSTALL.md`.

### 6.7 Publication workflow (separate from installer)

After all source changes are committed locally on the maintainer's machine:

```bash
cd "/Users/fred/Claude app/zenvibe"
gh repo create Fredje777/claude-zenvibe \
  --public \
  --source=. \
  --description "Vibe-code with a safety net. Pause/resume/checkpoint sessions in Claude Code, with auto-protection before context compaction." \
  --push
```

This creates the public repo, sets the remote, and pushes all current commits in one shot. No squash — full history goes up (it shows the honest iteration).

After push:
- Verify on github.com.
- For the maintainer's own machine: run `./install.sh` from the repo to refresh the installed copy with the new English version (idempotent, takes <5 s).

---

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Smart bilingual mis-detection (Claude writes EN in a FR project) | The rule is explicit and conservative: only switch to FR when *clear* signals exist (CLAUDE.md FR content, OR existing FR journal). Default to EN. |
| Public README too marketing-y / off-putting for senior devs | Intro is upbeat but short. The sections that follow are technical and neutral. Senior devs skip the intro and land on "What's in the box". |
| MCP tool schema change (added `language` param) breaks existing client integrations | The user is the only consumer right now. After release, the param is optional with a default — fully backward compatible. |
| `gh repo create` fails (name taken, network) | Manual fallback: create on github.com UI, then `git remote add origin … && git push -u origin main`. |
| Smart bilingual increases token usage (Claude reads CLAUDE.md + journal just to detect language) | Already done as part of the existing workflow for `/zenresume`. For `/zenpause` and `/zencheckpoint`, the language check is a small additional read — acceptable. |
| `install.sh` corrupts a user's JSON config | Pre-edit backups (timestamped) + atomic rewrite (tmp file + `os.replace`) + post-write parse validation. Manual restore is one `cp` away. |
| `install.sh` fails on a non-Mac (Linux user clones the repo) | Detect `uname` early; skip macOS-specific steps with a clear warning; CC CLI install proceeds. Document explicitly in README + INSTALL.md. |
| User runs `install.sh` from a wrong directory | Script resolves its own location via `$(cd "$(dirname "$0")" && pwd)` and uses that as source. Independent of caller's `cwd`. |
| Missing `uv` blocks the whole install when user only wants CC CLI | `uv` is soft-warn: missing → desktop section skipped with explanation, CC CLI install proceeds. `--cli` flag forces this mode explicitly. |

---

## 8. Documentation scope

The user's directive: "documente un maximum". Concretely:

- **`README.md`** — primary entry point. Audience-aware intro (Draft D) + comprehensive sections (Quick start, What's in the box, Surface coverage, Installation summary, Project journal explanation, Configuration, Architecture, Troubleshooting pointer, License). ~250–400 lines.
- **`docs/INSTALL.md`** — extended install reference: prerequisites in detail, surface-by-surface manual install (for users who want to understand or whose `install.sh` fails), troubleshooting common issues, uninstall procedure, FAQ. Linked from README in 2–3 places.
- **`docs/web-project.md`** — claude.ai Project preset (already exists; translated and slightly expanded).
- **`CHANGELOG.md`** — keep-a-changelog format, single 0.1.0 entry.
- **Inline comments** — `install.sh`, `uninstall.sh`, `hooks/scripts/session-start-briefing.py`, and `mcp/server.py` get block comments explaining intent, not just mechanics.
- **Each command body** (`commands/*.md`) — starts with a one-line purpose statement, then the workflow. The body itself IS documentation for Claude *and* (when read) for the user trying to understand what the command does.
- **Hooks** — each hook prompt (`pre-compact-prompt.md`, `session-start-prompt.md`) opens with a one-line "Why this exists" paragraph.

No man pages, no Sphinx docs site, no per-API reference — overkill for v0.1.

---

## 9. Out of scope (explicit)

- Marketplace.json — deferred.
- CI workflows (linting, testing) — none for v0.1; can add later if the plugin grows.
- Localization beyond EN/FR — only EN/FR for now (the two languages the author actively uses); the MCP `language` param is `Literal["en", "fr"]` for now, extensible later.
- Renaming of commands/MCP tools — frozen at current names.
- Windows native install (no Claude desktop app there; users can use WSL).
- GUI installer (terminal-only is fine for the target audience that lives in CC anyway).

---

## 10. Approval

This design was iterated and approved across:
- 2026-05-13: initial three sections (translation plan, intro text draft D, repo polish).
- 2026-05-13 (update): added §6 Installer + §8 Documentation scope after explicit request for hassle-free install with preflight checks and maximum documentation.

Next step: writing-plans skill → implementation plan → execution.
