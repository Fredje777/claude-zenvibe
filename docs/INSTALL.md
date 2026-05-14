# Installation Guide

This document covers installation in depth, per operating system, with troubleshooting and uninstall procedures. For the 30-second version, see the [README Quick Start](../README.md#quick-start).

---

## 1. Prerequisites

| Tool | macOS | Linux | Windows | Required for |
|---|---|---|---|---|
| Claude Code CLI | https://claude.com/code | https://claude.com/code | https://claude.com/code | Slash commands, hooks |
| `git` | `brew install git` | `apt install git` / `dnf install git` | https://git-scm.com/download/win | Plugin checkpoint workflow |
| `python3` ≥ 3.11 | `brew install python` | `apt install python3` | https://www.python.org/downloads/ | Hook script, MCP server, JSON edits during install |
| `rsync` | pre-installed | pre-installed | included with Git for Windows | File copy during install |
| `uv` | `brew install uv` | https://docs.astral.sh/uv/ | https://docs.astral.sh/uv/ | MCP server runtime (desktop app only) |

`uv` is only needed if you want ZenVibe to work in the **Claude desktop app**. It is optional otherwise — `install.sh` will tell you what's missing.

### Path quick reference

| File | macOS | Linux | Windows |
|---|---|---|---|
| Plugin install dir | `~/.claude/plugins/zenvibe/` | `~/.claude/plugins/zenvibe/` | `%USERPROFILE%\.claude\plugins\zenvibe\` |
| CC settings | `~/.claude/settings.json` | `~/.claude/settings.json` | `%USERPROFILE%\.claude\settings.json` |
| CC plugin registry | `~/.claude/plugins/installed_plugins.json` | `~/.claude/plugins/installed_plugins.json` | `%USERPROFILE%\.claude\plugins\installed_plugins.json` |
| Desktop MCP config | `~/Library/Application Support/Claude/claude_desktop_config.json` | _(n/a — no Linux desktop app)_ | `%APPDATA%\Claude\claude_desktop_config.json` |

---

## 2. macOS — quick install

```bash
git clone https://github.com/Fredje777/claude-zenvibe.git
cd claude-zenvibe
./install.sh
```

What you should see:
- Preflight: all ✓ (or ⚠ on a missing optional)
- Confirmation prompt summarizing what will happen
- Progress lines per surface
- Final summary with restart instructions

After install:
- **Terminal:** start a new `claude` session, type `/zen` — three commands appear in autocomplete.
- **VS Code:** restart the Claude Code panel; same commands available.
- **Desktop app:** quit Claude.app (`Cmd+Q`) then reopen; the `zenvibe_*` MCP tools become available.
- **Web:** see [section 5](#5-web-claudeai-manual-project-setup).

---

## 3. Linux — quick install

```bash
git clone https://github.com/Fredje777/claude-zenvibe.git
cd claude-zenvibe
./install.sh
```

The installer detects Linux and **skips the desktop app section** with a clear warning (Claude desktop app is not available on Linux). The CC CLI and VS Code parts install normally.

`uv` is not required on Linux unless you also want to run the MCP server manually for testing.

---

## 4. Windows — via WSL (recommended)

Open a WSL Ubuntu/Debian terminal:

```bash
sudo apt update && sudo apt install -y git python3 rsync
git clone https://github.com/Fredje777/claude-zenvibe.git
cd claude-zenvibe
./install.sh
```

This installs ZenVibe against the WSL-side Claude Code. If you also use Claude Code installed on the Windows side (outside WSL), see [section 4b](#4b-windows--via-git-bash-native).

---

## 4b. Windows — via Git Bash (native)

If you do not use WSL, open **Git Bash** (ships with Git for Windows):

```bash
git clone https://github.com/Fredje777/claude-zenvibe.git
cd claude-zenvibe
./install.sh
```

The installer detects Windows (via `uname` returning `MINGW64_NT-*`), resolves `~/.claude/` to `%USERPROFILE%/.claude/` and the desktop config to `%APPDATA%/Claude/claude_desktop_config.json`.

**Windows is community best-effort.** If the script fails, fall back to the [manual install in section 7](#7-manual-install-fallback-all-platforms).

---

## 5. Web (claude.ai) — manual Project setup

claude.ai does not load plugins or MCP servers. To get a ZenVibe experience there, create a Project once:

1. Go to https://claude.ai → **Projects** → **+ Create Project** → name it `ZenVibe`.
2. In the Project **Custom instructions** (or **Project knowledge** depending on UI), paste the system prompt from [`docs/web-project.md`](web-project.md).
3. Use it by saying "ZenVibe pause", "resume after pause", or "prepare a compact" in any conversation of that Project.

It works in narrative mode — Claude produces journal entries and git commands for you to run locally.

---

## 6. What `install.sh` does, step by step

For transparency, here is the exact sequence the installer runs:

1. **Preflight:** checks `git`, `python3`, `rsync`, optionally `uv`, and the presence of `~/.claude/` and `~/Library/Application Support/Claude/` (or `%APPDATA%/Claude/` on Windows).
2. **Backup JSONs:** any file the installer will edit gets a `.backup-YYYYMMDD-HHMMSS` copy alongside.
3. **Copy plugin files:** rsync from the cloned repo to `~/.claude/plugins/zenvibe/` (excludes `.git/`, tests, IDE cruft).
4. **Register plugin:** adds `zenvibe@local` to `~/.claude/plugins/installed_plugins.json`.
5. **Enable plugin:** sets `enabledPlugins.zenvibe@local = true` in `~/.claude/settings.json`.
6. **Configure desktop MCP** *(macOS + Windows only, if `uv` and desktop app are present)*: adds the `zenvibe` server to `claude_desktop_config.json` with the resolved `uv` path.
7. **Print summary** with per-surface restart instructions.

Re-running `install.sh` is safe (idempotent). It will create new backups and update timestamps.

---

## 7. Manual install (fallback, all platforms)

If `install.sh` fails or you prefer to do it by hand:

### 7.1 Copy plugin files

```bash
mkdir -p ~/.claude/plugins/zenvibe
rsync -a --delete --exclude '.git/' --exclude 'tests/' /path/to/cloned/repo/ ~/.claude/plugins/zenvibe/
```

### 7.2 Register in `installed_plugins.json`

Open `~/.claude/plugins/installed_plugins.json` (create if missing, with `{"version":2,"plugins":{}}` as initial content) and add under `"plugins"`:

```json
"zenvibe@local": [
  {
    "scope": "user",
    "installPath": "/Users/<you>/.claude/plugins/zenvibe",
    "version": "0.1.0",
    "installedAt": "2026-05-13T00:00:00.000Z",
    "lastUpdated": "2026-05-13T00:00:00.000Z"
  }
]
```

### 7.3 Enable in `settings.json`

In `~/.claude/settings.json`, add (or merge into existing `enabledPlugins`):

```json
"enabledPlugins": {
  "zenvibe@local": true
}
```

### 7.4 Configure desktop MCP (macOS / Windows only)

Edit:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`

Add under `"mcpServers"`:

```json
"zenvibe": {
  "command": "/opt/homebrew/bin/uv",
  "args": [
    "run",
    "--script",
    "/Users/<you>/.claude/plugins/zenvibe/mcp/server.py"
  ]
}
```

Adjust the `command` path to wherever `uv` is on your system (`which uv` tells you).

---

## 8. Verifying the install

After install + restart:

- **`/help` in `claude`** → should list `/zenpause`, `/zenresume`, `/zencheckpoint`.
- **`/plugin` in `claude`** → `zenvibe@local` shown as enabled.
- **Claude desktop app → Customize panel** → `ZenVibe` listed under "Personal plugins".
- **Claude desktop app → ask "what MCP tools are available?"** → `zenvibe_pause`, `zenvibe_resume`, `zenvibe_checkpoint`.

If any of these is missing, see [Troubleshooting](#9-troubleshooting).

---

## 9. Troubleshooting

### Plugin doesn't appear in `/help`

- Restart your `claude` session (or VS Code Claude panel) — slash commands are loaded once at session start.
- Verify the install: `cat ~/.claude/plugins/zenvibe/.claude-plugin/plugin.json` should print the manifest.
- Verify it is enabled: `grep zenvibe ~/.claude/settings.json` should show `"zenvibe@local": true`.

### MCP tools don't appear in the desktop app

- Fully quit Claude.app (`Cmd+Q`, not just close the window) and reopen.
- Verify the config: `python3 -c "import json; print(json.load(open('$HOME/Library/Application Support/Claude/claude_desktop_config.json'))['mcpServers'].get('zenvibe'))"` should print a dict, not `None`.
- Make sure `uv` is the path the desktop app can find. Run `command -v uv` and check it matches the `command` in the JSON.
- Check the desktop app's logs — Claude.app → top-menu "Help" → "Show Logs" — for `mcp` errors.

### `uv: command not found`

- Install: `brew install uv` (macOS) or via the [official uv installer](https://docs.astral.sh/uv/getting-started/installation/).
- Re-run `./install.sh` — it will pick up uv on the second pass.

### `install.sh` says "Claude Code CLI not detected"

- The script looks for `~/.claude/`. If Claude Code is installed but the folder is elsewhere, run `claude --help` once first to bootstrap it, then re-run `./install.sh`.

### Smart bilingual writes English in a French project

- Make sure your project has a `CLAUDE.md` at the root, and that it actually contains French sentences (accents are a strong signal).
- Alternatively, write the first journal entry in French manually — subsequent runs will detect it and stay in French.

### Desktop app shows `ZenVibe` plugin name as `Zenvibe` (lowercase v)

- This is a Claude Code naming quirk: the display Title-cases the `name` field. The `displayName: "ZenVibe"` field is set in `plugin.json` but not yet honored by every Claude surface. Cosmetic only.

---

## 10. Uninstalling

Run from the cloned repo:

```bash
./uninstall.sh
```

It removes:
- `~/.claude/plugins/zenvibe/` (the install directory)
- `zenvibe@local` from `installed_plugins.json` and `settings.json`
- `mcpServers.zenvibe` from `claude_desktop_config.json` (macOS / Windows)

Backups are taken before each edit (`.backup-YYYYMMDD-HHMMSS`).

Your project `JOURNAL.md` files are **never touched** — they belong to you.

---

## 11. FAQ

### Does ZenVibe send anything to Anthropic / the cloud?

No. ZenVibe is local-only. It edits files in your repo (commits, journal entries) and edits your local Claude Code configs. The MCP server runs on your machine. The smart bilingual logic does not phone home.

### Can I use ZenVibe without git?

Mostly. The skills detect whether the working directory is a git repo and skip the git steps cleanly if not. The journal is still written. You lose the audit trail, of course.

### What if I'm already using a different journal format?

ZenVibe appends entries at the top of `docs/JOURNAL.md` or `JOURNAL.md`. If you use a different convention (different filename, or entries at the bottom), open an issue — making the location and order configurable is on the roadmap.

### Can I disable the SessionStart briefing?

Yes — disable the hook by editing `~/.claude/plugins/zenvibe/hooks/hooks.json` and removing the `SessionStart` array. Or uninstall and re-install with a fork that drops the hook.

### What happens if the installer fails halfway?

Each JSON edit is backed up with `.backup-YYYYMMDD-HHMMSS` before being touched. Restore manually with `cp` if needed. Plugin files copied to `~/.claude/plugins/zenvibe/` can be removed with `rm -rf ~/.claude/plugins/zenvibe/`.

### Does ZenVibe support Windows native (no WSL, no Git Bash)?

Not in v0.1. The installer is a bash script. PowerShell port is welcome — see [Contributing](../README.md#contributing).
