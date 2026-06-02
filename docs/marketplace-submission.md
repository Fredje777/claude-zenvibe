# ZenVibe — Plugin Directory Submission Packet

Reference packet for submitting ZenVibe to the official Claude Code plugin
directory. Form: <https://clau.de/plugin-directory-submission>

> The official marketplace (`anthropics/claude-plugins-official`) does **not**
> accept PRs for third-party plugins — submission is via the form above, with
> an Anthropic quality + security review. This file is the copy-paste source
> for that form, kept in-repo so it can be reused when resubmitting or updating.

---

## Core fields (copy-paste)

**Plugin name:** ZenVibe

**Short description (one line):**
Vibe-code with a safety net. Pause, resume, and checkpoint Claude Code sessions; auto-protect context before compaction.

**Category:** Productivity

**Author / maintainer:** Fred Fonteyne

**Contact email:** frederic.fonteyne@gmail.com

**Repository (public, MIT):** https://github.com/Fredje777/claude-zenvibe

**Latest release:** v0.2.0 — https://github.com/Fredje777/claude-zenvibe/releases/tag/v0.2.0

**Marketplace source (for the directory entry):**
- type: `github`
- repo: `Fredje777/claude-zenvibe`
- ref: `v0.2.0`
- sha: `8b5c999dbd2f145d0f775983424fd8f72d109f7c`

**License:** MIT

> When releasing a new version, update `ref` + `sha` here and in
> `.claude-plugin/marketplace.json`, then resubmit if the directory entry
> needs to track the new release.

---

## What it does (long description)

ZenVibe helps developers — especially newcomers "vibe coding" with Claude — keep their work safe across the three moments where a session normally loses context:

- **Pause** (`/zenpause`): full handoff before stepping away — commits + pushes committable files, writes a detailed entry to `docs/JOURNAL.md` (completed tasks, current task, remaining work, technical decisions, open questions, git state, attention points).
- **Resume** (`/zenresume`): re-establishes context after a pause or compaction by reading the journal + CLAUDE.md + git state, then proposes a next action and waits for explicit confirmation. Read-only until the user says go.
- **Checkpoint** (`/zencheckpoint`): saves state cleanly without compacting; outputs an "It's safe to compact now" confirmation.

Two automatic hooks:
- **PreCompact**: checkpoints (commit + journal + push) before any compaction, manual or automatic.
- **SessionStart**: a 3-line briefing when reopening a project with a recent journal.

Also ships an MCP server (3 tools: `zenvibe_pause`, `zenvibe_resume`, `zenvibe_checkpoint`) for the Claude desktop app, and a claude.ai web Project preset. Output is smart-bilingual (English by default, French when the project signals French).

The single source of truth is `docs/JOURNAL.md` in the user's own repo. Git is the safety net beneath it.

---

## Security & quality posture (for the review)

- **Local-only.** No outbound network calls anywhere in the code. The only network operation is an explicit, user-initiated `git push` to the user's own remote.
- **No telemetry, no phone-home, no cloud.** Nothing leaves the machine.
- **No hardcoded secrets.** A denylist (`.env*`, `*.key`, `*.pem`, `*.pfx`, `*.p12`, `id_rsa*`, `credentials*`, `secrets*`, `.npmrc`) prevents committing sensitive files; suspicious staged files are unstaged with a warning.
- **Least-privilege tools.** `/zenresume` is read-only (Bash, Read). `/zenpause` and `/zencheckpoint` add Write/Edit only to manage the journal.
- **Git safety rails.** Never `--force`, never `--no-verify`. WIP / half-written files are never committed (the LLM lists them as attention points instead).
- **MCP safety.** JSON config edits (installer) use read → modify → atomic rewrite + parse validation, with timestamped backups before any change.
- **Tested.** 20 local pytest cases cover the MCP smart-bilingual dispatch, the file-allowlist commit logic, and the SessionStart hook gating.

---

## How a reviewer can try it in 30 seconds

```
/plugin marketplace add Fredje777/claude-zenvibe
/plugin install zenvibe@fredje777
```

Then `/zen` to see the three commands. Or clone + `./install.sh` to also wire the desktop app MCP server.

---

## Notes

- Supported surfaces: Claude Code CLI, VS Code (Claude Code extension), Claude desktop app (via MCP), claude.ai web (via Project preset).
- Platforms: macOS (full), Linux (CC CLI), Windows (WSL / Git Bash).
- Already has one external contributor (PR #2, merged) and an open roadmap (#3 ZENVIBE_LANG, #4 configurable journal, #5 PowerShell installer).
