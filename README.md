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

---

## Requirements

- **Claude Code** (CLI v2.x or later) — install from https://claude.com/code
- **git** — `brew install git` / `apt install git`
- **python3** ≥ 3.11 — `brew install python` / `apt install python3`
- **uv** (only for the desktop app MCP server) — `brew install uv` / https://docs.astral.sh/uv/getting-started/installation/

ZenVibe runs on **macOS** (fully supported), **Linux** (CC CLI only — no Claude desktop app), and **Windows** (via WSL or Git Bash — see [`docs/INSTALL.md`](docs/INSTALL.md)).

---

## Quick start

```bash
git clone https://github.com/Fredje777/claude-zenvibe.git
cd claude-zenvibe
./install.sh
```

Then start a new `claude` session (or restart VS Code's Claude Code panel) and type `/zen` to autocomplete on the three commands.

For platform-specific procedures and troubleshooting, see [`docs/INSTALL.md`](docs/INSTALL.md).

---

## What's in the box

### Slash commands (CC CLI + VS Code)

- `/zenpause [optional note]` — full handoff before stepping away.
- `/zenresume` — re-establish context after a pause or compaction; read-only until you confirm.
- `/zencheckpoint` — save state cleanly; output an "It's safe to compact now" message.

### Hooks (CC CLI + VS Code)

- **`PreCompact`** — automatic checkpoint (commit + journal + push) before any compaction, whether you typed `/compact` or it triggered automatically.
- **`SessionStart`** — on opening a project with a recent `docs/JOURNAL.md` (<14 days), Claude prefaces its first answer with a 3-line briefing.

### MCP tools (Claude desktop app)

- `zenvibe_pause`, `zenvibe_resume`, `zenvibe_checkpoint` — same workflows, invoked by Claude in the desktop app via natural language ("ZenVibe pause on /Users/me/myproject").

### Web Project preset (claude.ai)

A copy-paste system prompt in [`docs/web-project.md`](docs/web-project.md) turns a claude.ai Project into a narrative ZenVibe assistant (produces journal entries and git commands for you to run locally).

---

## Surface coverage

| Surface | Mechanism | Status |
|---|---|---|
| Terminal (Claude Code CLI) | Slash commands + hooks | ✅ Native |
| VS Code (extension Claude Code) | Slash commands + hooks | ✅ Native (shares `~/.claude/`) |
| Claude desktop app | MCP server (3 tools) | ✅ Configured by `install.sh` |
| Web claude.ai | Project + system prompt | ✅ Manual setup (one-time) |

---

## Project journal — how it works

ZenVibe writes everything to `docs/JOURNAL.md` (fallback: `JOURNAL.md` at the repo root, created if neither exists). Entries are prepended, newest first.

The journal is the **single source of truth**. Git is the safety net beneath it. Nothing important is stored outside your project — no hidden state, no opaque cache.

---

## Smart bilingual output

ZenVibe writes journals and confirmation messages in **English by default**. It switches to **French** automatically when the project's `CLAUDE.md` is in French OR the existing journal already has French entries. No configuration needed.

If you want a different language, you can [open an issue](https://github.com/Fredje777/claude-zenvibe/issues) — adding a new locale takes a few minutes (see `MESSAGES` in `mcp/server.py`).

---

## Per-project customization (optional)

You can create `.claude/zenvibe.md` at the root of any project to keep custom instructions you want to paste into `/compact <instructions>`. Example:

```markdown
Keep in detail: commit conventions, current sprint state, DB schema decisions,
LLM prompt choices, and any open question. Summarize code iterations briefly.
```

ZenVibe never reads it automatically (Claude Code excludes `/compact` from programmatic invocation). It is there for you to copy-paste when you decide.

---

## Architecture

```
zenvibe/  (install dir, identical to source dir)
├── .claude-plugin/plugin.json          plugin manifest
├── .mcp.json                           MCP server for CC CLI
├── commands/
│   ├── zenpause.md                     /zenpause
│   ├── zenresume.md                    /zenresume
│   └── zencheckpoint.md                /zencheckpoint
├── hooks/
│   ├── hooks.json                      PreCompact + SessionStart
│   ├── pre-compact-prompt.md
│   ├── session-start-prompt.md
│   └── scripts/
│       └── session-start-briefing.py
├── mcp/
│   └── server.py                       MCP server (PEP 723, uv run --script)
├── docs/
│   ├── INSTALL.md                      detailed install + troubleshooting + FAQ
│   └── web-project.md                  claude.ai Project preset
├── install.sh                          one-command installer
└── uninstall.sh                        clean removal
```

---

## Troubleshooting

See [`docs/INSTALL.md`](docs/INSTALL.md#9-troubleshooting) for common issues. Most install problems come from a missing prereq — re-run `./install.sh --check` to diagnose.

---

## Uninstall

```bash
./uninstall.sh
```

It removes the plugin files and config entries, with backups taken before each edit. Your project `JOURNAL.md` files are never touched.

Details in [`docs/INSTALL.md`](docs/INSTALL.md#10-uninstalling).

---

## Why "ZenVibe"?

"Vibe coding" — chatting with an AI to ship code — is the fastest way to learn and to build. It also has obvious failure modes: lost context, broken state, no audit trail. ZenVibe gives the vibe coder a soft floor without slowing them down. The name leans into the calm, not the panic.

---

## Contributing

PRs welcome. Open an issue first for non-trivial changes so we can talk through the design.

---

## License

[MIT](LICENSE) — © 2026 Fred Fonteyne.
