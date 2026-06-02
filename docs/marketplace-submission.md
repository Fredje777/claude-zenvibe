# ZenVibe — Community Marketplace Submission Packet

Reference packet for submitting ZenVibe to Anthropic's **community** marketplace
(`claude-community`). Kept in-repo so it can be reused when resubmitting or updating.

## The two Anthropic marketplaces (important)

- **`claude-plugins-official`** — curated by Anthropic at its sole discretion.
  **No application process; the submission form does NOT add plugins here.**
- **`claude-community`** — the public community marketplace where third-party
  submissions land **after review**. Users add it with
  `/plugin marketplace add anthropics/claude-plugins-community` and install as
  `@claude-community`. **This is what we submit to.**

## How to submit

1. **Validate locally first** (the review pipeline runs the same check + automated
   safety screening):

   ```bash
   claude plugin validate /path/to/claude-zenvibe
   ```

   Must print `✔ Validation passed` for the plugin manifest. (Status: passing as of v0.2.1.)

2. **Submit via an in-app form** (authenticated, tied to your account):
   - Claude.ai: <https://claude.ai/settings/plugins/submit>
   - Console: <https://platform.claude.com/plugins/submit>

3. After approval, the plugin is **pinned to a commit SHA** in the
   [`anthropics/claude-plugins-community`](https://github.com/anthropics/claude-plugins-community)
   catalog. CI bumps the pin as you push new commits. The public catalog syncs
   **nightly**, so expect a delay between approval and the listing appearing.
   Check status by searching the name in the
   [community catalog `marketplace.json`](https://github.com/anthropics/claude-plugins-community/blob/main/.claude-plugin/marketplace.json).

---

## Core fields (copy-paste)

**Plugin name:** zenvibe (display: ZenVibe)

**Short description:**
Vibe-code with a safety net. Pause, resume, and checkpoint Claude Code sessions; auto-protect context before compaction.

**Category:** Productivity

**Author / maintainer:** Fred Fonteyne — frederic.fonteyne@gmail.com

**Repository (public, MIT):** https://github.com/Fredje777/claude-zenvibe

**Latest release:** v0.2.1 — https://github.com/Fredje777/claude-zenvibe/releases/tag/v0.2.1

**Commit pin:** `6534bcc2c08eb59dec6700ca243a39e830d9fb97` (tag `v0.2.1`)

**License:** MIT

> On a new release, update `ref` + `sha` in `.claude-plugin/marketplace.json`
> (self-hosted marketplace). The community catalog re-pins automatically via CI.

---

## What it does (long description)

ZenVibe helps developers — especially newcomers "vibe coding" with Claude — keep their work safe across the three moments where a session normally loses context:

- **Pause** (`/zenpause`): full handoff before stepping away — commits + pushes committable files, writes a detailed entry to `docs/JOURNAL.md`.
- **Resume** (`/zenresume`): re-establishes context after a pause or compaction; read-only until the user confirms.
- **Checkpoint** (`/zencheckpoint`): saves state cleanly without compacting.

Two automatic hooks: **PreCompact** (checkpoint before any compaction) and **SessionStart** (3-line briefing when reopening a recent project). Plus an MCP server (3 tools) for the Claude desktop app and a claude.ai web Project preset. Smart-bilingual output (English default, French when the project signals French).

The single source of truth is `docs/JOURNAL.md` in the user's own repo.

---

## Security & quality posture

- **Local-only.** No outbound network calls in the code; the only network op is an explicit, user-initiated `git push` to the user's own remote. No telemetry, no cloud.
- **No hardcoded secrets**, with a denylist preventing commit of `.env*`, `*.key`, `*.pem`, `*.pfx`, `*.p12`, `id_rsa*`, `credentials*`, `secrets*`, `.npmrc`.
- **Least-privilege tools.** `/zenresume` is read-only; `/zenpause` / `/zencheckpoint` add Write/Edit only for the journal.
- **Git safety rails.** Never `--force`, never `--no-verify`. WIP files are never committed.
- **Passes `claude plugin validate`** (plugin manifest + hooks) as of v0.2.1.
- **Tested.** 20 local pytest cases (MCP bilingual dispatch, file-allowlist commit logic, SessionStart gating).

---

## How a reviewer can try it in 30 seconds

```
/plugin marketplace add Fredje777/claude-zenvibe
/plugin install zenvibe@fredje777
```

Then `/zen` to see the three commands. Or clone + `./install.sh` to also wire the desktop app MCP server.

---

## Notes

- Surfaces: Claude Code CLI, VS Code, Claude desktop app (MCP), claude.ai web (Project preset).
- Platforms: macOS (full), Linux (CC CLI), Windows (WSL / Git Bash).
- One external contributor already (PR #2, merged); open roadmap (#3 ZENVIBE_LANG, #4 configurable journal, #5 PowerShell installer).
