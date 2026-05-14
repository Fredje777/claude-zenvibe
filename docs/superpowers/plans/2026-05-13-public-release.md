# ZenVibe Public Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Translate ZenVibe to English with smart bilingual runtime, add a hassle-free cross-platform installer with preflight checks, expand documentation, and publish v0.1 to GitHub as `Fredje777/claude-zenvibe`.

**Architecture:** No new features, no command renames. Existing structure preserved (3 commands, 2 hooks, 3 MCP tools, web Project preset). The MCP server gains a `language: "en" | "fr"` parameter on each tool plus a `MESSAGES` translation dict. The installer is a single `install.sh` at the repo root, written in bash with inline `python3` snippets for safe JSON manipulation, branching per OS (macOS / Linux / Windows-Git-Bash). Symmetric `uninstall.sh` provided.

**Tech Stack:** Python 3.11+ (MCP server, install JSON manipulation), bash (installer), rsync (file copy), `uv` (MCP server runtime), git, `gh` CLI for publication. Tests use pytest (dev-only, no CI for v0.1).

---

## File Structure

**Source location:** `/Users/fred/Claude app/zenvibe/` (dev source).
**Install location (live):** `~/.claude/plugins/zenvibe/` (created by `install.sh`).

### Files modified

| Path | Change |
|---|---|
| `.claude-plugin/plugin.json` | Translate `description`; add `homepage`, `repository` |
| `.gitignore` | Append `*.backup-*`, `.idea/`, `*.iml` |
| `.mcp.json` | No change (already English-neutral) |
| `README.md` | Full rewrite (Draft D intro + 11 sections) |
| `commands/zenpause.md` | Translate body + add "Output language" rule |
| `commands/zenresume.md` | Translate body + add "Output language" rule |
| `commands/zencheckpoint.md` | Translate body + add "Output language" rule |
| `docs/web-project.md` | Translate (system prompt becomes EN with project-language directive) |
| `hooks/hooks.json` | No change |
| `hooks/pre-compact-prompt.md` | Translate |
| `hooks/session-start-prompt.md` | Translate |
| `hooks/scripts/session-start-briefing.py` | Translate comments + docstring |
| `mcp/server.py` | Translate prose; add `MESSAGES` dict; add `language` arg to each tool; refactor headings to use the dict |

### Files created

| Path | Purpose |
|---|---|
| `LICENSE` | MIT license text (year 2026, holder "Fred Fonteyne") |
| `CHANGELOG.md` | Keep-a-changelog, single 0.1.0 entry |
| `install.sh` | User-facing installer (preflight + 6 install actions + per-OS branching) |
| `uninstall.sh` | Clean removal (with backups before edits) |
| `docs/INSTALL.md` | 11-section extended install guide |
| `tests/test_mcp_messages.py` | pytest: smart bilingual dispatch tests |
| `tests/test_session_start_briefing.py` | pytest: hook script logic tests |
| `tests/conftest.py` | pytest fixtures (tmp repo, fake CLAUDE.md, etc.) |
| `tests/README.md` | One-paragraph: "How to run: `uv run --with pytest pytest tests/`" |

### Files deleted

| Path | Reason |
|---|---|
| `scripts/sync-install.sh` | Replaced by `install.sh` at repo root |

### Files unchanged

`hooks/hooks.json`, `.mcp.json`, `docs/superpowers/specs/2026-05-13-public-release-design.md`.

---

## Phase 0 — Pre-flight

### Task 0.1: Create release branch

**Files:** none (git only)

- [ ] **Step 1: Create and switch to release branch**

```bash
cd "/Users/fred/Claude app/zenvibe"
git checkout -b release/v0.1
```

- [ ] **Step 2: Verify clean baseline**

```bash
git status
```

Expected: `nothing to commit, working tree clean`. If not, stash or commit pending work first.

- [ ] **Step 3: Note the starting commit SHA for rollback if needed**

```bash
git rev-parse --short HEAD
```

Expected output looks like `4b08c12`. Note it down in a scratch buffer.

---

## Phase 1 — Python test scaffolding (TDD setup)

### Task 1.1: Create the `tests/` directory and conftest

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/README.md`

- [ ] **Step 1: Create `tests/conftest.py`**

```python
"""pytest fixtures for ZenVibe tests."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """A temporary directory initialized as a git repo with an initial commit."""
    repo = tmp_path / "fake-project"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("test\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)
    return repo


@pytest.fixture
def fr_claude_md(tmp_repo: Path) -> Path:
    """Returns the tmp_repo with a French CLAUDE.md at root."""
    (tmp_repo / "CLAUDE.md").write_text(
        "# Projet de test\n\nCe projet est écrit en français pour les tests.\n"
    )
    return tmp_repo


@pytest.fixture
def en_claude_md(tmp_repo: Path) -> Path:
    """Returns the tmp_repo with an English CLAUDE.md at root."""
    (tmp_repo / "CLAUDE.md").write_text(
        "# Test project\n\nThis project is in English for tests.\n"
    )
    return tmp_repo
```

- [ ] **Step 2: Create `tests/README.md`**

```markdown
# Tests

Run the suite with:

```bash
uv run --with pytest pytest tests/
```

Tests are local-only (no CI in v0.1). They cover the MCP server's smart-bilingual dispatch and the SessionStart hook script's gating logic.
```

- [ ] **Step 3: Verify pytest can discover the conftest**

```bash
cd "/Users/fred/Claude app/zenvibe"
uv run --with pytest pytest tests/ --collect-only 2>&1 | head -5
```

Expected: no error, output mentions `tests/conftest.py`. May say "no tests ran" — fine.

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "test: scaffold pytest with fr/en CLAUDE.md fixtures"
```

---

## Phase 2 — MCP smart bilingual (TDD)

### Task 2.1: Test the `MESSAGES` dict and `_t()` helper

**Files:**
- Create: `tests/test_mcp_messages.py`

- [ ] **Step 1: Write the failing test for the translation helper**

Create `tests/test_mcp_messages.py`:

```python
"""Smart bilingual dispatch in the MCP server."""
import sys
from pathlib import Path

# Allow importing the MCP server module
SERVER_DIR = Path(__file__).parent.parent / "mcp"
sys.path.insert(0, str(SERVER_DIR))

import server  # noqa: E402


def test_messages_dict_has_en_and_fr():
    """MESSAGES must define both languages."""
    assert "en" in server.MESSAGES
    assert "fr" in server.MESSAGES


def test_messages_have_same_keys():
    """EN and FR dicts must define the same keys (no missing translation)."""
    en_keys = set(server.MESSAGES["en"].keys())
    fr_keys = set(server.MESSAGES["fr"].keys())
    assert en_keys == fr_keys, f"Mismatch: EN={en_keys - fr_keys}, FR={fr_keys - en_keys}"


def test_t_returns_en_by_default():
    assert server._t("safe_to_compact", "en").startswith("🧘 It's safe")


def test_t_returns_fr_when_requested():
    assert "compacter" in server._t("safe_to_compact", "fr").lower()


def test_t_falls_back_to_en_on_unknown_language():
    """Unknown language code falls back to English (no crash)."""
    assert server._t("safe_to_compact", "xx") == server._t("safe_to_compact", "en")


def test_t_raises_on_unknown_key():
    """An unknown message key is a programming error and should raise."""
    import pytest
    with pytest.raises(KeyError):
        server._t("nonexistent_key", "en")
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd "/Users/fred/Claude app/zenvibe"
uv run --with pytest --with mcp pytest tests/test_mcp_messages.py -v
```

Expected: ALL FAIL because `MESSAGES` and `_t` don't exist yet on `server` module.

- [ ] **Step 3: Implement `MESSAGES` and `_t` in `mcp/server.py`**

In `mcp/server.py`, after the existing `GENERIC_COMPACT_INSTRUCTIONS` constant block (around line 35), add:

```python
# ---------------------------------------------------------------------------
# Smart-bilingual messages
# ---------------------------------------------------------------------------
#
# All user-visible strings written by the MCP tools route through `_t(key, lang)`.
# Add a new pair (en + fr) here, then reference it by key in the tools.
#
# Claude (the caller) is responsible for deciding the language from project
# signals (CLAUDE.md content, existing journal language) and passing it via
# the `language` argument of each tool. Default is English.

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "safe_to_compact": "🧘 It's safe to compact now. Type /compact to proceed.",
        "checkpoint_partial": "⚠ Partial checkpoint — fix the git errors before compacting.",
        "pause_heading": "Pause",
        "checkpoint_heading": "Checkpoint",
        "pause_note_prefix": "> Pause note: ",
        "summary_prefix": "**Summary:** ",
        "completed_section": "### Completed tasks (current iteration)",
        "current_task_section": "### Current task",
        "remaining_section": "### Remaining tasks (in order)",
        "decisions_section": "### Technical decisions made this session",
        "open_questions_section": "### Open questions",
        "files_touched_section": "### Files touched",
        "next_step_section": "### Clear next step",
        "git_section": "### Git",
        "git_branch_prefix": "- Branch: ",
        "git_last_commit_prefix": "- Last commit: ",
        "git_none": "- _(not a git repo or nothing to commit)_",
        "attention_section": "### Attention points for the resume",
        "session_done_section": "### Done this session",
    },
    "fr": {
        "safe_to_compact": "🧘 Tu peux compacter sans risque. Tape /compact pour lancer.",
        "checkpoint_partial": "⚠ Checkpoint partiel — corrige les erreurs git avant de compacter.",
        "pause_heading": "Pause",
        "checkpoint_heading": "Checkpoint",
        "pause_note_prefix": "> Note de pause : ",
        "summary_prefix": "**Résumé :** ",
        "completed_section": "### Tâches terminées (itération en cours)",
        "current_task_section": "### Tâche en cours",
        "remaining_section": "### Tâches restantes (par ordre)",
        "decisions_section": "### Décisions techniques prises cette session",
        "open_questions_section": "### Questions ouvertes",
        "files_touched_section": "### Fichiers touchés",
        "next_step_section": "### Prochaine étape claire",
        "git_section": "### Git",
        "git_branch_prefix": "- Branche : ",
        "git_last_commit_prefix": "- Dernier commit : ",
        "git_none": "- _(pas de repo git ou rien à committer)_",
        "attention_section": "### Points d'attention pour la reprise",
        "session_done_section": "### Fait dans cette session",
    },
}


def _t(key: str, language: str) -> str:
    """Resolve a localized message. Falls back to English on unknown language."""
    lang_dict = MESSAGES.get(language) or MESSAGES["en"]
    return lang_dict[key]  # KeyError on unknown key — caller bug
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --with pytest --with mcp pytest tests/test_mcp_messages.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_mcp_messages.py mcp/server.py
git commit -m "feat(mcp): smart-bilingual MESSAGES dict + _t() helper with tests"
```

---

### Task 2.2: Add `language` parameter to `zenvibe_pause` and refactor headings via `_t()`

**Files:**
- Modify: `mcp/server.py` (the `zenvibe_pause` tool around lines 200–280)
- Modify: `tests/test_mcp_messages.py` (add test for pause output)

- [ ] **Step 1: Write the failing test for pause output language**

Append to `tests/test_mcp_messages.py`:

```python
def test_zenvibe_pause_writes_english_journal_by_default(tmp_repo):
    result = server.zenvibe_pause(
        project_path=str(tmp_repo),
        summary="did stuff",
        commit_message="feat: stuff",
        completed=["a"],
        current_task="b",
        remaining=["c"],
        decisions=["d"],
        open_questions=["e"],
    )
    journal = (tmp_repo / "docs" / "JOURNAL.md").read_text()
    assert "## " in journal
    assert "— Pause" in journal
    assert "### Completed tasks" in journal
    assert "Branch:" in journal


def test_zenvibe_pause_writes_french_journal_when_requested(tmp_repo):
    server.zenvibe_pause(
        project_path=str(tmp_repo),
        summary="fait des trucs",
        commit_message="feat: trucs",
        completed=["a"],
        current_task="b",
        remaining=["c"],
        decisions=["d"],
        open_questions=["e"],
        language="fr",
    )
    journal = (tmp_repo / "docs" / "JOURNAL.md").read_text()
    assert "— Pause" in journal
    assert "### Tâches terminées" in journal
    assert "Branche :" in journal
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run --with pytest --with mcp pytest tests/test_mcp_messages.py::test_zenvibe_pause_writes_english_journal_by_default tests/test_mcp_messages.py::test_zenvibe_pause_writes_french_journal_when_requested -v
```

Expected: FAIL because `zenvibe_pause` doesn't accept `language`, and uses hardcoded French headings.

- [ ] **Step 3: Refactor `zenvibe_pause` in `mcp/server.py`**

Replace the existing `zenvibe_pause` function (around lines 200–280) entirely with this version. The diff is: signature gains `language: Literal["en", "fr"] = "en"`, the `parts` list uses `_t()` keys, and the docstring updates the language note.

```python
@mcp.tool()
def zenvibe_pause(
    project_path: str,
    summary: str,
    commit_message: str,
    completed: list[str],
    current_task: str,
    remaining: list[str],
    decisions: list[str],
    open_questions: list[str],
    attention_points: list[str] | None = None,
    note: str | None = None,
    language: Literal["en", "fr"] = "en",
) -> dict[str, Any]:
    """Save session state before stepping away for hours.

    Workflow:
    1. Commit + push committable files (skipping suspicious paths).
    2. Write a detailed entry at the top of docs/JOURNAL.md.
    3. Return a summary of actions taken.

    Args:
        project_path: Absolute (or ~) path of the project to act on.
        summary: One-sentence summary of what was done this session.
        commit_message: Commit message to use (follow project convention).
        completed: List of completed tasks in the current iteration.
        current_task: Current task and its precise state (one sentence).
        remaining: Remaining tasks in priority order.
        decisions: Technical decisions made this session.
        open_questions: Open questions for the user.
        attention_points: Optional — refactors, code smells, WIP to resume.
        note: Optional — free-form pause note provided by the user.
        language: Output language for the journal entry ("en" or "fr").
            The caller (Claude) decides based on project signals (CLAUDE.md
            language, existing journal language). Defaults to "en".

    Returns:
        A dict with `commit_sha`, `pushed`, `journal_path`, `branch`,
        `errors`, `warnings`, `skipped_suspicious`.
    """
    repo = _resolve_repo(project_path)
    git_result = _do_git_checkpoint(repo, commit_message)

    journal = _find_or_create_journal(repo)
    now = _now()

    parts = [f"## {now} — {_t('pause_heading', language)}"]
    if note:
        parts.append(f"\n{_t('pause_note_prefix', language)}{note}")
    parts.append(f"\n{_t('summary_prefix', language)}{summary}")
    parts.append(f"\n{_t('completed_section', language)}\n" + _bullets(completed))
    parts.append(f"\n{_t('current_task_section', language)}\n- " + current_task)
    parts.append(f"\n{_t('remaining_section', language)}\n" + _numbered(remaining))
    parts.append(f"\n{_t('decisions_section', language)}\n" + _bullets(decisions))
    parts.append(f"\n{_t('open_questions_section', language)}\n" + _bullets(open_questions))

    git_lines = []
    if git_result["branch"]:
        git_lines.append(f"{_t('git_branch_prefix', language)}{git_result['branch']}")
    if git_result["commit_sha"]:
        git_lines.append(
            f"{_t('git_last_commit_prefix', language)}"
            f"{git_result['commit_sha']} {commit_message}"
        )
    if not git_lines:
        git_lines.append(_t("git_none", language))
    parts.append(f"\n{_t('git_section', language)}\n" + "\n".join(git_lines))

    if attention_points:
        parts.append(
            f"\n{_t('attention_section', language)}\n" + _bullets(attention_points)
        )

    entry = "\n".join(parts)
    _prepend_to_journal(journal, entry)

    return {
        "journal_path": str(journal.relative_to(repo)),
        **git_result,
    }
```

Also, at the top of the file, add the import for `Literal` if missing. Search for `from typing import`. If absent, add at the top:

```python
from typing import Any, Literal
```

(Otherwise extend the existing `from typing import ...` line to include `Literal`.)

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run --with pytest --with mcp pytest tests/test_mcp_messages.py -v
```

Expected: 5 previous tests still PASS + 2 new tests PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp/server.py tests/test_mcp_messages.py
git commit -m "feat(mcp): zenvibe_pause accepts language='en'|'fr', headings use _t()"
```

---

### Task 2.3: Add `language` parameter to `zenvibe_checkpoint`

**Files:**
- Modify: `mcp/server.py` (`zenvibe_checkpoint` function around lines 340–410)
- Modify: `tests/test_mcp_messages.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_mcp_messages.py`:

```python
def test_zenvibe_checkpoint_default_en_message(tmp_repo):
    result = server.zenvibe_checkpoint(
        project_path=str(tmp_repo),
        summary="did x",
        commit_message="feat: x",
        decisions=["d"],
        files_touched=["a.py"],
        next_step="do y",
    )
    assert result["safe_to_compact"] is True
    assert "safe to compact" in result["next_step_message"].lower()


def test_zenvibe_checkpoint_french_message(tmp_repo):
    result = server.zenvibe_checkpoint(
        project_path=str(tmp_repo),
        summary="fait x",
        commit_message="feat: x",
        decisions=["d"],
        files_touched=["a.py"],
        next_step="faire y",
        language="fr",
    )
    assert result["safe_to_compact"] is True
    assert "compacter sans risque" in result["next_step_message"].lower()
    journal = (tmp_repo / "docs" / "JOURNAL.md").read_text()
    assert "— Checkpoint" in journal
    assert "### Fait dans cette session" in journal
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest --with mcp pytest tests/test_mcp_messages.py::test_zenvibe_checkpoint_default_en_message tests/test_mcp_messages.py::test_zenvibe_checkpoint_french_message -v
```

Expected: FAIL.

- [ ] **Step 3: Refactor `zenvibe_checkpoint`**

Replace the existing `zenvibe_checkpoint` function entirely with:

```python
@mcp.tool()
def zenvibe_checkpoint(
    project_path: str,
    summary: str,
    commit_message: str,
    decisions: list[str],
    files_touched: list[str],
    next_step: str,
    language: Literal["en", "fr"] = "en",
) -> dict[str, Any]:
    """Save a clean checkpoint — without compacting.

    Workflow:
    1. Commit + push committable changes.
    2. Write a session-focused entry at the top of docs/JOURNAL.md.
    3. Return a message confirming it is safe to compact.

    The user remains the sole decider of WHEN to type `/compact`. Claude Code
    explicitly excludes `/compact` from its `SlashCommand` tool, so we never
    trigger compaction ourselves.

    Args:
        project_path: Project path.
        summary: One-sentence summary of what was done this session.
        commit_message: Commit message.
        decisions: Technical decisions made this session.
        files_touched: Main files touched.
        next_step: Clear next step (one actionable line).
        language: Output language for the journal entry ("en" or "fr").
            Defaults to "en".

    Returns:
        A dict with `safe_to_compact` (bool), `next_step_message`, plus the
        git result and the journal path.
    """
    repo = _resolve_repo(project_path)
    git_result = _do_git_checkpoint(repo, commit_message)

    journal = _find_or_create_journal(repo)
    now = _now()

    parts = [
        f"## {now} — {_t('checkpoint_heading', language)}",
        f"\n{_t('summary_prefix', language)}{summary}",
        f"\n{_t('session_done_section', language)}\n- " + summary,
        f"\n{_t('decisions_section', language)}\n" + _bullets(decisions),
        f"\n{_t('files_touched_section', language)}\n" + _bullets(files_touched),
        f"\n{_t('next_step_section', language)}\n- " + next_step,
    ]
    _prepend_to_journal(journal, "\n".join(parts))

    safe = not git_result["errors"]
    if safe:
        next_step_message = _t("safe_to_compact", language)
    else:
        next_step_message = _t("checkpoint_partial", language)

    return {
        "journal_path": str(journal.relative_to(repo)),
        "safe_to_compact": safe,
        "next_step_message": next_step_message,
        **git_result,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --with pytest --with mcp pytest tests/test_mcp_messages.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp/server.py tests/test_mcp_messages.py
git commit -m "feat(mcp): zenvibe_checkpoint accepts language and uses _t()"
```

---

### Task 2.4: `zenvibe_resume` — no localization (read-only), but translate docstring

**Files:**
- Modify: `mcp/server.py` (`zenvibe_resume` tool around lines 280–340)

The `zenvibe_resume` tool returns raw journal/CLAUDE.md content; Claude formats the briefing. No need for `language` param. Only the docstring needs to be translated to English.

- [ ] **Step 1: Translate the `zenvibe_resume` docstring**

Replace the existing docstring with:

```python
    """Read the context to resume after a pause or compaction.

    Workflow:
    1. Read docs/JOURNAL.md (or JOURNAL.md at root) in full.
    2. Read CLAUDE.md at the project root if present.
    3. Capture git state (status, log -5, branch).
    4. Return everything structured so Claude composes the briefing.

    Args:
        project_path: Absolute (or ~) project path.

    Returns:
        A dict with `journal_content`, `claude_md_content`, `git_status`,
        `recent_commits` (list), `branch`, `errors`.
    """
```

Also translate any inline comments in the function body from French to English (e.g., `# Locate journal`, `# CLAUDE.md`, `# Git state` are likely already in English — verify and translate if any FR slipped in).

- [ ] **Step 2: Run all tests to verify nothing broke**

```bash
uv run --with pytest --with mcp pytest tests/ -v
```

Expected: all 9 tests still PASS.

- [ ] **Step 3: Commit**

```bash
git add mcp/server.py
git commit -m "docs(mcp): translate zenvibe_resume docstring to English"
```

---

### Task 2.5: Translate the rest of `mcp/server.py` (module docstring, helpers, constants, comments)

**Files:**
- Modify: `mcp/server.py` (top of file + helper functions)

- [ ] **Step 1: Translate the module docstring**

Replace the `"""ZenVibe MCP server."""` block at the top with:

```python
"""ZenVibe MCP server.

Exposes three tools — `zenvibe_pause`, `zenvibe_resume`, `zenvibe_checkpoint` —
that mirror the ZenVibe slash commands on surfaces where slash commands
are not available (Claude desktop app, claude.ai web with custom integrations).

Design:
- The LLM does the thinking (what to commit, what to write in the journal).
- This server does the IO (git operations, file read/write).
- Tools take structured arguments produced by the LLM; the server validates,
  performs the side effects, and returns a structured result.
- Output language is controlled by the caller via a `language` argument on
  each tool (currently "en" or "fr"). Default: "en".
"""
```

- [ ] **Step 2: Translate `GENERIC_COMPACT_INSTRUCTIONS`**

Replace the existing constant with both EN and FR versions, and make the function that uses it (if any — currently it's referenced by zenvibe_checkpoint via the GENERIC_COMPACT_INSTRUCTIONS name, but we removed the compact-command-builder when refactoring to checkpoint) decide based on `language`. After the refactor in Task 2.3, `GENERIC_COMPACT_INSTRUCTIONS` is now **unused**. Verify and remove.

```bash
grep -n "GENERIC_COMPACT_INSTRUCTIONS" mcp/server.py
```

If only the definition remains and no callers, **delete** the constant and its surrounding comment.

- [ ] **Step 3: Translate `SUSPICIOUS_PATTERNS` comments and any helper docstrings**

Walk through the file from top to bottom. For each docstring or comment not yet in English, translate it. Specifically:
- `_resolve_repo` docstring
- `_git` docstring (probably none — leave if absent)
- `_is_git_repo` docstring (probably none)
- `_filter_suspicious` docstring
- `_find_or_create_journal` docstring
- `_prepend_to_journal` docstring
- `_now` docstring
- `_do_git_checkpoint` docstring + inline comments (especially `# Handle renames "old -> new"` etc. — these are likely already English)
- `_bullets`, `_numbered` docstrings

Translate any FR strings inside warning/error messages — e.g., `"Pas un repo git — étape git sautée."` becomes `"Not a git repo — git step skipped."`. Same for "git status propre — rien à committer.", etc.

Specific replacements (search and replace):

| French | English |
|---|---|
| `"Pas un repo git — étape git sautée."` | `"Not a git repo — git step skipped."` |
| `"git status propre — rien à committer."` | `"Working tree clean — nothing to commit."` |
| `"Tous les fichiers modifiés ressemblent à des secrets — aucun commit fait."` | `"All modified files look like secrets — nothing committed."` |
| `"Pas de remote configuré — pas de push."` | `"No remote configured — no push."` |

These are warning strings inside `_do_git_checkpoint` (around line 145–195). Keep them as English regardless of `language` (they are technical diagnostics, not localized user content).

- [ ] **Step 4: Run all tests**

```bash
uv run --with pytest --with mcp pytest tests/ -v
```

Expected: all tests still PASS.

- [ ] **Step 5: Quick sanity start of the server**

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' | timeout 5 uv run --script mcp/server.py 2>&1 | tail -1 | python3 -c "import json, sys; d=json.loads(sys.stdin.read()); assert d['result']['serverInfo']['name'] == 'zenvibe'; print('✓ server initialize OK')"
```

(macOS users without `timeout`: replace with `gtimeout` after `brew install coreutils`, or run the command, sleep 3 in another tab, and kill the process.)

Expected: `✓ server initialize OK`.

- [ ] **Step 6: Commit**

```bash
git add mcp/server.py
git commit -m "docs(mcp): translate module docstring, helpers, and warnings to English"
```

---

## Phase 3 — Translate hooks

### Task 3.1: Translate `hooks/pre-compact-prompt.md`

**Files:**
- Modify: `hooks/pre-compact-prompt.md` (rewrite content in English, keep structure)

- [ ] **Step 1: Replace the file content**

Overwrite `hooks/pre-compact-prompt.md` with:

```markdown
A compaction of the conversation is about to happen (either user-triggered via `/compact`, or automatic because the context is full).

Before it proceeds, make a clean checkpoint:

1. Run `git status`. If files are in a committable state, commit them with a message summarizing what was done in this session. Follow the project's commit convention (check `git log -5 --oneline`). Never commit broken WIP, and never commit anything that looks like a secret (`.env*`, `*.key`, `credentials*`, etc.).

2. Open or create `docs/JOURNAL.md` (fallback: `JOURNAL.md` at root) and prepend a dated entry **at the top** of the file:

   ```markdown
   ## YYYY-MM-DD HH:MM — Checkpoint (auto)

   ### Done this session
   - ...

   ### Technical decisions
   - ...

   ### Files touched
   - ...

   ### Clear next step
   - ... (one actionable line)
   ```

   **Output language:** Match the project. If `CLAUDE.md` is in French OR the existing journal contains French entries, write the new entry in French. Otherwise English.

3. Push if a remote is configured (`git push`). Never force, never skip hooks.

4. Confirm to the user in one line: `Checkpoint OK before compact.`

If nothing is committable or worth journaling (very short conversation, or checkpoint already done just before), say so plainly (`Nothing to checkpoint.`) and let the compaction proceed.

Once this checkpoint is done, the technical compaction will follow. On the next user message after compaction, if you have lost context, read `docs/JOURNAL.md` and `CLAUDE.md` to reorient — or suggest the user run `/zenresume`.
```

- [ ] **Step 2: Quick smoke check — file exists and is readable**

```bash
head -1 "/Users/fred/Claude app/zenvibe/hooks/pre-compact-prompt.md"
```

Expected: `A compaction of the conversation is about to happen ...`

- [ ] **Step 3: Commit**

```bash
git add hooks/pre-compact-prompt.md
git commit -m "i18n(hooks): translate pre-compact prompt to English with project-language rule"
```

---

### Task 3.2: Translate `hooks/session-start-prompt.md`

**Files:**
- Modify: `hooks/session-start-prompt.md`

- [ ] **Step 1: Replace the file content**

Overwrite with:

```markdown
A `JOURNAL.md` file exists in this project (`docs/JOURNAL.md` or root `JOURNAL.md`) and was modified recently. The user has probably stepped away from a working session not long ago.

On the **first** user message in this session:

- If the request is exactly `/zenresume` → ignore this guidance; the command handles the full briefing itself.
- Otherwise, **before** responding to the request, read only the latest entry of the journal (the first one in the file — newest first) and prefix your response with a mini-briefing of at most 3–4 lines:

```
👋 Last JOURNAL entry: <date> — <type: Pause/Checkpoint/other>.
You were on: <current task or next step, one sentence>.
Full briefing: `/zenresume`
```

Then continue with your response to the user's request in the same message.

**Rules:**

- Read **only** the latest journal entry. No `git status`, no `CLAUDE.md` — those reads belong to `/zenresume`.
- If the journal is empty, unreadable, or you cannot identify a dated entry → say nothing about the briefing and start normally.
- The mini-briefing is a *teaser*, not a substitute for `/zenresume`. Do not expand it.
- Do not spontaneously offer to resume the task — let the user drive. If they want to resume, they will run `/zenresume`.
- Match the language of the journal in your briefing (write French if the journal is in French).
```

- [ ] **Step 2: Smoke check**

```bash
head -1 "/Users/fred/Claude app/zenvibe/hooks/session-start-prompt.md"
```

Expected: `A \`JOURNAL.md\` file exists in this project ...`

- [ ] **Step 3: Commit**

```bash
git add hooks/session-start-prompt.md
git commit -m "i18n(hooks): translate session-start prompt to English"
```

---

### Task 3.3: Translate `hooks/scripts/session-start-briefing.py` (comments + docstring)

**Files:**
- Modify: `hooks/scripts/session-start-briefing.py`

- [ ] **Step 1: Replace the module docstring**

Replace the existing docstring at the top with:

```python
"""SessionStart hook: inject a mini-briefing if a recent JOURNAL.md exists.

Silent unless:
  - source is "startup" or "compact" (not "resume" or "clear")
  - cwd contains docs/JOURNAL.md or JOURNAL.md
  - that journal was modified within the last 14 days

Otherwise emits nothing, so non-ZenVibe projects stay completely quiet.
"""
```

- [ ] **Step 2: Translate inline comments**

Search for any French comments and translate them. Likely candidates:
- `# Only on startup or compact, not on /clear or --resume` (probably already English — verify)
- `# Find journal`
- `# Only inject on a fresh launch or post-compaction reload.` (already English likely)

Run:

```bash
grep -nE "# .*[éèàâêîôûçÉÈÀÂÊÎÔÛÇ]" hooks/scripts/session-start-briefing.py
```

For each line found, translate the comment.

- [ ] **Step 3: Verify the script still runs silently for a non-startup source**

```bash
echo '{"source":"resume","cwd":"/tmp"}' | CLAUDE_PLUGIN_ROOT="/Users/fred/Claude app/zenvibe" python3 "/Users/fred/Claude app/zenvibe/hooks/scripts/session-start-briefing.py"; echo "exit=$?"
```

Expected: empty output, `exit=0`.

- [ ] **Step 4: Commit**

```bash
git add hooks/scripts/session-start-briefing.py
git commit -m "i18n(hooks): translate session-start-briefing.py comments"
```

---

### Task 3.4: Test the SessionStart briefing script

**Files:**
- Create: `tests/test_session_start_briefing.py`

- [ ] **Step 1: Write the test file**

```python
"""Tests for the SessionStart hook briefing script."""
import json
import os
import subprocess
import time
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parent.parent / "hooks" / "scripts" / "session-start-briefing.py"
)
PLUGIN_ROOT = Path(__file__).parent.parent


def run_hook(stdin_json: dict, plugin_root: Path = PLUGIN_ROOT) -> tuple[str, int]:
    """Run the hook script with the given JSON on stdin. Returns (stdout, rc)."""
    proc = subprocess.run(
        ["python3", str(SCRIPT)],
        input=json.dumps(stdin_json),
        text=True,
        capture_output=True,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(plugin_root)},
        timeout=5,
    )
    return proc.stdout, proc.returncode


def test_silent_on_resume_source(tmp_repo):
    """source=resume must not emit anything (user is continuing a session)."""
    (tmp_repo / "docs").mkdir()
    (tmp_repo / "docs" / "JOURNAL.md").write_text("## 2026-05-13 — Pause\n")
    out, rc = run_hook({"source": "resume", "cwd": str(tmp_repo)})
    assert out == ""
    assert rc == 0


def test_silent_on_clear_source(tmp_repo):
    out, rc = run_hook({"source": "clear", "cwd": str(tmp_repo)})
    assert out == ""
    assert rc == 0


def test_silent_when_no_journal(tmp_repo):
    """No journal in cwd → nothing to brief about."""
    out, rc = run_hook({"source": "startup", "cwd": str(tmp_repo)})
    assert out == ""
    assert rc == 0


def test_silent_when_journal_stale(tmp_repo):
    """Journal modified more than 14 days ago → silent."""
    (tmp_repo / "docs").mkdir()
    journal = tmp_repo / "docs" / "JOURNAL.md"
    journal.write_text("## old\n")
    # Set mtime to 30 days ago
    thirty_days_ago = time.time() - (30 * 86400)
    os.utime(journal, (thirty_days_ago, thirty_days_ago))
    out, rc = run_hook({"source": "startup", "cwd": str(tmp_repo)})
    assert out == ""
    assert rc == 0


def test_emits_briefing_on_recent_journal(tmp_repo):
    """source=startup + recent journal → emits the prompt."""
    (tmp_repo / "docs").mkdir()
    (tmp_repo / "docs" / "JOURNAL.md").write_text(
        "## 2026-05-13 14:00 — Pause\n\nSome content.\n"
    )
    out, rc = run_hook({"source": "startup", "cwd": str(tmp_repo)})
    assert rc == 0
    assert "JOURNAL.md" in out
    assert "/zenresume" in out


def test_silent_on_malformed_stdin(tmp_repo):
    """Garbage stdin → silent exit 0 (never crash the session)."""
    proc = subprocess.run(
        ["python3", str(SCRIPT)],
        input="not json",
        text=True,
        capture_output=True,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)},
        timeout=5,
    )
    assert proc.stdout == ""
    assert proc.returncode == 0
```

- [ ] **Step 2: Run the tests**

```bash
uv run --with pytest pytest tests/test_session_start_briefing.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_session_start_briefing.py
git commit -m "test(hooks): cover session-start-briefing gating logic"
```

---

## Phase 4 — Translate slash commands

### Task 4.1: Translate `commands/zenpause.md`

**Files:**
- Modify: `commands/zenpause.md` (replace body, keep frontmatter format with EN description)

- [ ] **Step 1: Replace the file content**

Overwrite with:

```markdown
---
name: zenpause
description: Save the full state of the session before stepping away for hours. Commits and pushes everything committable, writes a detailed entry in docs/JOURNAL.md (completed tasks, current task with state, remaining tasks in order, technical decisions, open questions, git state), and flags attention points for the resume.
argument-hint: "[optional note, e.g. 'lunch break, resume with auth JWT']"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

You produce a complete handoff so the user (or yourself) can resume cleanly hours later.

**Output language:** Default to English. If `CLAUDE.md` exists at the project root and is written in French, OR if the existing journal (`docs/JOURNAL.md` or `JOURNAL.md`) contains French entries, write your output (confirmation message, new journal entry) in French. Otherwise English. Detect once and stay consistent across the whole skill execution.

## Workflow

### 0. Verify the working directory is a git repo

Run `git rev-parse --is-inside-work-tree`. If it fails, the project is not under git: skip step 1 and the "Git" section of step 3, write only the journal entry, and mention in the confirmation that no git checkpoint was made.

### 1. Commit + push everything committable

- Run `git status` and `git diff --stat` to see what changed.
- Run `git log -10 --oneline` to learn the project's commit message convention.
- For each modified file: if it is in a clean, working state, include it in the commit. If it is clearly WIP or half-written (broken syntax, stub functions, partial refactor), **do not commit it** — flag it in step 3 instead.
- Stage the clean files and commit with a message that **summarizes what was actually done this session**, not "WIP".
- If a remote is configured, run `git push`. If push fails for a missing upstream, set it (`git push -u origin <branch>`) and retry. Never use `--force` or `--no-verify`.

### 2. Locate (or create) the journal

Look for the journal in this order:

1. `docs/JOURNAL.md`
2. `JOURNAL.md` at the repo root
3. If neither exists, create `docs/JOURNAL.md` (run `mkdir -p docs` first).

### 3. Prepend a new entry to the journal

The newest entry goes **at the top** of the file. Use this structure (translate headings to French if the project is in French):

```markdown
## YYYY-MM-DD HH:MM — Pause

> Pause note: <text passed as argument, if any>

### Completed tasks (current iteration)
- ...

### Current task
- ... (precise state: what is done, what remains on this task)

### Remaining tasks (in order)
1. ...
2. ...

### Technical decisions made this session
- ...

### Open questions
- ...

### Git
- Branch: <branch>
- Last commit: <short sha> <message>

### Attention points for the resume
- (optional — refactors to do, uncommitted WIP files, tests to write, code smells)
```

Be specific. File paths, function names, the *why* behind each decision. Future-you must be able to act on this without re-reading the whole chat. Avoid generic phrases like "improved performance" — say *what* and *where*.

### 4. Confirm

Output exactly one short block — no preamble, no recap of the journal content:

```
State saved.
✓ Commit: <short sha> <message>
✓ Push: <branch> → <remote>   (or: "nothing to commit")
✓ Journal: docs/JOURNAL.md

Have a good break. On return: /zenresume
```

If anything failed (push refused, journal unwritable, uncommitted WIP files), say so explicitly with the affected files. Never claim success that did not happen.

## Rules

- Never commit files that look like secrets: `.env*`, `*.key`, `*.pem`, `*.pfx`, `*.p12`, `id_rsa*`, `credentials*`, `secrets*`, `.npmrc` with tokens, or anything else that looks sensitive. Trust the project's `.gitignore` first, but if something suspicious is staged, warn the user and unstage it.
- Never force-push or skip hooks.
- If `git status` is clean AND nothing meaningful happened this session, you may write a minimal journal entry ("session with no changes") and exit. Do not fabricate work.
- The journal is the single source of truth. Do not create a separate state file.
```

- [ ] **Step 2: Smoke check the frontmatter**

```bash
head -8 "/Users/fred/Claude app/zenvibe/commands/zenpause.md"
```

Expected: starts with `---`, `name: zenpause`, description in English.

- [ ] **Step 3: Commit**

```bash
git add commands/zenpause.md
git commit -m "i18n(cmd): translate /zenpause to English with project-language rule"
```

---

### Task 4.2: Translate `commands/zenresume.md`

**Files:**
- Modify: `commands/zenresume.md`

- [ ] **Step 1: Replace the file content**

Overwrite with:

```markdown
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
```

- [ ] **Step 2: Smoke check**

```bash
head -8 "/Users/fred/Claude app/zenvibe/commands/zenresume.md"
```

Expected: name=zenresume, English description.

- [ ] **Step 3: Commit**

```bash
git add commands/zenresume.md
git commit -m "i18n(cmd): translate /zenresume to English with project-language rule"
```

---

### Task 4.3: Translate `commands/zencheckpoint.md`

**Files:**
- Modify: `commands/zencheckpoint.md`

- [ ] **Step 1: Replace the file content**

Overwrite with:

```markdown
---
name: zencheckpoint
description: Save the current session state WITHOUT compacting — commit + push committable files, write a session-focused entry in docs/JOURNAL.md (what was done, decisions, files touched, next step), then confirm it is safe to compact. Use as a mid-task bookmark, or right before typing /compact manually.
argument-hint: ""
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

The user wants to save the current state without destroying context. You make a clean checkpoint, then confirm they can compact safely if they wish.

**Output language:** Default to English. If `CLAUDE.md` is in French OR the journal contains French entries, write your output in French. Otherwise English.

**Important:** you never run `/compact` yourself. Claude Code explicitly excludes `/compact` from the `SlashCommand` tool. Compaction stays an action the user triggers manually. Your role here is solely to secure context beforehand.

The `PreCompact` hook does the same work automatically if the user types `/compact` without running this skill first — so this skill is essentially an *on-demand checkpoint*, also useful mid-task to bookmark without compacting.

## Workflow

### 0. Verify the working directory is a git repo

Run `git rev-parse --is-inside-work-tree`. If it fails, skip step 1 entirely, write only the journal entry, and mention "not a git repo" in the confirmation.

### 1. Commit + push committable changes

- Run `git status` and `git log -5 --oneline` first.
- Stage clean files. Skip half-written WIP (and warn the user — never commit broken code).
- Commit with a meaningful message that summarizes the session, following the project's existing convention.
- Push if a remote is configured.

### 2. Update the journal

Prepend a new entry at the top of `docs/JOURNAL.md` (or `JOURNAL.md` at root). Create `docs/JOURNAL.md` if neither exists.

This entry is **session-focused**, shorter than a full handoff:

```markdown
## YYYY-MM-DD HH:MM — Checkpoint

### Done this session
- ...

### Technical decisions
- ...

### Files touched
- path/to/file
- ...

### Clear next step
- ... (one actionable line)
```

Keep it tight. The point is to bookmark the state, not write a sprint review.

### 3. Confirm

Output exactly this block, no more, no less:

```
✓ Checkpoint
✓ Commit: <sha> <message>   (or: "nothing to commit")
✓ Push: <branch> → <remote>   (or: "no remote")
✓ Journal: docs/JOURNAL.md

🧘 It's safe to compact now. Type /compact to proceed.
```

If something failed (push refused, journal unwritable, uncommittable WIP), list it explicitly in place of the relevant `✓` line, and **omit** the final `🧘 It's safe to compact` line — precisely because we do not want to invite a compaction when the checkpoint is not clean.

### 4. Custom `/compact` instructions (optional)

If the user wants custom instructions when they later type `/compact`, they can keep them in `.claude/zenvibe.md` in their project. You do **not** read it here and you do not display it — that file is just available for them to copy-paste into `/compact <text>` when they decide.

## Rules

- **Never run `/compact` yourself.** It is explicitly excluded from the `SlashCommand` tool. The user alone triggers compaction.
- Never commit broken WIP — warn instead and leave the files in place.
- Never commit anything that looks like a secret (`.env*`, `*.key`, `*.pem`, `credentials*`, etc.).
- If `git status` is clean and the journal already covers the current state, say so plainly and still emit the `🧘 It's safe to compact now` message.
- The `PreCompact` hook will redo the same work if the user types `/compact` afterwards — it is idempotent and safe.
```

- [ ] **Step 2: Smoke check**

```bash
head -8 "/Users/fred/Claude app/zenvibe/commands/zencheckpoint.md"
```

- [ ] **Step 3: Commit**

```bash
git add commands/zencheckpoint.md
git commit -m "i18n(cmd): translate /zencheckpoint to English with project-language rule"
```

---

## Phase 5 — Translate web Project preset

### Task 5.1: Translate `docs/web-project.md`

**Files:**
- Modify: `docs/web-project.md`

- [ ] **Step 1: Replace the file content**

Overwrite with this English version. The embedded system prompt that the user pastes into claude.ai becomes English with a project-language directive.

```markdown
# ZenVibe on claude.ai (web)

claude.ai does not run user slash commands or local MCP servers. But you can **simulate** ZenVibe by creating a **Project** whose instructions reproduce the workflows.

## Setting up the Project

1. Go to https://claude.ai
2. Click **Projects** in the sidebar
3. **+ Create Project** → name it `ZenVibe`
4. In the **Project knowledge / Custom instructions** section (name varies by UI version), paste the **system prompt** below

The Project has no access to `git` or to your disk. It works in **narrative assistant** mode: you describe the state, it produces journal entries and git commands for you to run yourself.

---

## System prompt to paste into the Project

```
You are ZenVibe (web mode), an assistant that helps manage pauses, resumes,
and compactions of coding sessions. You do NOT have access to local files
or to git — you produce text artifacts that the user executes themselves.

Output language: default to English. If the user writes in French, or
mentions a French project / French CLAUDE.md, switch to French and stay
consistent across the conversation.

The user can invoke you with three intents:

──────────────────────────────────────────────────────────────────
INTENT 1 — "pause" / "ZenVibe pause" / "I'm stepping away"
──────────────────────────────────────────────────────────────────

Ask the user (if they haven't said yet):
- What they were working on
- What they did this session (summary)
- State of progress
- Technical decisions made
- Open questions
- Optional pause note

Then produce TWO artifacts:

A) A JOURNAL.md entry ready to paste, format:

```markdown
## YYYY-MM-DD HH:MM — Pause

> Pause note: ...

**Summary:** ...

### Completed tasks (current iteration)
- ...

### Current task
- ... (precise state)

### Remaining tasks (in order)
1. ...

### Technical decisions made this session
- ...

### Open questions
- ...

### Git
- Branch: ...
- Last commit: (fill in after the commit)

### Attention points for the resume
- ... (optional)
```

B) A sequence of git commands to run in a terminal:

```bash
cd <project>
git status
git add <files>      # list of safe files to commit
git commit -m "<concise message>"
git push
```

Remind the user not to commit: .env*, *.key, *.pem, id_rsa*,
credentials*, secrets*, .npmrc with tokens.

──────────────────────────────────────────────────────────────────
INTENT 2 — "resume" / "briefing after pause"
──────────────────────────────────────────────────────────────────

Ask the user to paste the content of docs/JOURNAL.md (at least the latest
entry) plus the current `git status`.

Then produce a compact briefing:

```
You were on: ...
Since the pause: ...
Remaining: ...
Proposed next action: ...

Attention points:
- ...

Shall I resume? (yes / no)
```

Wait for assent before proposing code.

──────────────────────────────────────────────────────────────────
INTENT 3 — "compact" / "prepare a compact"
──────────────────────────────────────────────────────────────────

Ask the user:
- Summary of the session
- Technical decisions
- Files touched
- Clear next step

Produce:

A) A "Checkpoint" JOURNAL.md entry (shorter than Pause)

B) The git commands to run (same as pause)

C) The /compact command to paste into Claude Code CLI:

/compact Keep in detail: project conventions (commits, data safety,
mandatory validations), current progress, technical decisions on
architecture and API, and any open question. Briefly summarize code
iterations and back-and-forth.

──────────────────────────────────────────────────────────────────
GENERAL RULES
──────────────────────────────────────────────────────────────────

- You respond in English by default; switch to French when the user does.
- You never pretend to have executed code or commands — you produce
  artifacts for the user to run.
- You refuse to produce commands that would expose secrets.
- You adapt verbosity: short briefing, detailed journal.
```

---

## How to use it after

In a conversation of the `ZenVibe` Project, just type:

- "ZenVibe pause. Here is what I did: …"
- "Resume after pause. Here is my JOURNAL: …"
- "Prepare a compact. We did: …"

Claude will produce the artifacts (JOURNAL entries + git commands) for you to copy-paste into your terminal.

## Limits

- No real execution (no git, no write)
- No automatic hooks (`PreCompact`, `SessionStart`) — those only exist in Claude Code CLI
- No memory across conversations (unless you attach the JOURNAL to the Project)

For the fully automated workflow, use **Claude Code CLI** (terminal or VS Code) — that is where ZenVibe truly shines.
```

- [ ] **Step 2: Smoke check**

```bash
head -3 "/Users/fred/Claude app/zenvibe/docs/web-project.md"
```

Expected: `# ZenVibe on claude.ai (web)`

- [ ] **Step 3: Commit**

```bash
git add docs/web-project.md
git commit -m "i18n(docs): translate web-project.md to English with project-language rule"
```

---

## Phase 6 — Plugin manifest + .gitignore

### Task 6.1: Update `.claude-plugin/plugin.json`

**Files:**
- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 1: Replace the file content**

Overwrite with:

```json
{
  "name": "zenvibe",
  "displayName": "ZenVibe",
  "version": "0.1.0",
  "description": "Vibe-code with a safety net. Pause, resume, and checkpoint Claude Code sessions; auto-protect context before compaction.",
  "author": {
    "name": "Fred Fonteyne",
    "email": "frederic.fonteyne@gmail.com"
  },
  "homepage": "https://github.com/Fredje777/claude-zenvibe",
  "repository": "https://github.com/Fredje777/claude-zenvibe",
  "keywords": [
    "workflow",
    "context-management",
    "compaction",
    "journal",
    "checkpoint",
    "productivity"
  ],
  "license": "MIT"
}
```

- [ ] **Step 2: Validate the JSON parses**

```bash
python3 -c "import json; json.load(open('/Users/fred/Claude app/zenvibe/.claude-plugin/plugin.json')); print('✓')"
```

Expected: `✓`

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "manifest: English description + homepage/repository URLs"
```

---

### Task 6.2: Update `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Append the new patterns**

Open `.gitignore` and append (preserving existing entries):

```
*.backup-*
.idea/
*.iml
.pytest_cache/
__pycache__/
*.pyc
```

(If some of these already exist, don't duplicate. The new ones for sure: `*.backup-*`, `.idea/`, `*.iml`, `.pytest_cache/`.)

- [ ] **Step 2: Verify**

```bash
grep -E "backup-|idea|pytest_cache" "/Users/fred/Claude app/zenvibe/.gitignore"
```

Expected: each pattern present.

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: gitignore backups, IDE files, pytest cache"
```

---

## Phase 7 — LICENSE and CHANGELOG

### Task 7.1: Create `LICENSE`

**Files:**
- Create: `LICENSE`

- [ ] **Step 1: Write the MIT license text**

Create `/Users/fred/Claude app/zenvibe/LICENSE` with this exact content:

```
MIT License

Copyright (c) 2026 Fred Fonteyne

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Commit**

```bash
git add LICENSE
git commit -m "chore: add MIT LICENSE file"
```

---

### Task 7.2: Create `CHANGELOG.md`

**Files:**
- Create: `CHANGELOG.md`

- [ ] **Step 1: Write the changelog**

Create `/Users/fred/Claude app/zenvibe/CHANGELOG.md`:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-13

### Added

- Three slash commands: `/zenpause`, `/zenresume`, `/zencheckpoint`.
- Two automatic hooks: `PreCompact` (auto-checkpoint before any compaction) and `SessionStart` (mini-briefing on opening a recent project).
- MCP server with three tools (`zenvibe_pause`, `zenvibe_resume`, `zenvibe_checkpoint`) for the Claude desktop app.
- Web Project preset in `docs/web-project.md` for claude.ai.
- Smart bilingual output: English by default, French when project signals indicate French (CLAUDE.md content or existing journal language).
- Hassle-free installer (`install.sh`) with preflight checks and per-OS branching (macOS / Linux / Windows-Git-Bash).
- Symmetric `uninstall.sh` with backup-before-edit safety.

### Notes

- Initial public release. Local-only test suite (no CI).
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add CHANGELOG with 0.1.0 entry"
```

---

## Phase 8 — Installer (`install.sh`)

The installer is the largest single piece. Build it incrementally so each step is testable.

### Task 8.1: Create the script skeleton with `--help`

**Files:**
- Create: `install.sh`

- [ ] **Step 1: Write the skeleton**

Create `/Users/fred/Claude app/zenvibe/install.sh`:

```bash
#!/usr/bin/env bash
# ZenVibe installer.
#
# Usage:
#   ./install.sh           # full install (CC CLI + desktop where available)
#   ./install.sh --check   # preflight checks only, no changes
#   ./install.sh --cli     # CC CLI only, skip desktop config
#   ./install.sh --yes     # don't ask the install confirmation
#   ./install.sh --help    # this message
#
# The script is idempotent: re-running it upgrades the install.
# JSON edits are backed up before any change.
set -euo pipefail

# Resolve script's own directory (the source of truth for the install).
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Output paths (computed later based on detected OS).
INSTALL_DIR=""
CC_SETTINGS=""
CC_INSTALLED_PLUGINS=""
DESKTOP_CONFIG=""

# Modes
MODE_CHECK_ONLY=false
MODE_CLI_ONLY=false
MODE_ASSUME_YES=false

usage() {
  sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

main() {
  parse_args "$@"
  if $MODE_CHECK_ONLY; then
    echo "=== Preflight (--check, no changes will be made) ==="
  else
    echo "=== ZenVibe installer ==="
  fi
  echo "Source: $SOURCE_DIR"
  echo ""
  # Sub-steps will be added in subsequent tasks.
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --help|-h) usage; exit 0 ;;
      --check)   MODE_CHECK_ONLY=true ;;
      --cli)     MODE_CLI_ONLY=true ;;
      --yes|-y)  MODE_ASSUME_YES=true ;;
      *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
  done
}

main "$@"
```

- [ ] **Step 2: Make it executable and test `--help`**

```bash
chmod +x "/Users/fred/Claude app/zenvibe/install.sh"
"/Users/fred/Claude app/zenvibe/install.sh" --help
```

Expected: prints the usage block (lines 2–12 of the script, with leading `# ` stripped).

- [ ] **Step 3: Test unknown option exits 2**

```bash
"/Users/fred/Claude app/zenvibe/install.sh" --garbage 2>&1; echo "exit=$?"
```

Expected: error message + `exit=2`.

- [ ] **Step 4: Commit**

```bash
git add install.sh
git commit -m "feat(install): skeleton with --help/--check/--cli/--yes flags"
```

---

### Task 8.2: Add OS detection and path resolution

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Add the `detect_os` and `resolve_paths` functions**

Insert these functions in `install.sh` after `parse_args()`:

```bash
# Detect the operating system. Sets the OS variable to one of: macos, linux, windows, unknown.
detect_os() {
  local u="$(uname -s)"
  case "$u" in
    Darwin*)            OS="macos" ;;
    Linux*)             OS="linux" ;;
    MINGW*|MSYS*|CYGWIN*) OS="windows" ;;
    *)                  OS="unknown" ;;
  esac
}

# Resolve install paths based on OS.
resolve_paths() {
  case "$OS" in
    macos|linux)
      INSTALL_DIR="$HOME/.claude/plugins/zenvibe"
      CC_SETTINGS="$HOME/.claude/settings.json"
      CC_INSTALLED_PLUGINS="$HOME/.claude/plugins/installed_plugins.json"
      ;;
    windows)
      INSTALL_DIR="$HOME/.claude/plugins/zenvibe"
      CC_SETTINGS="$HOME/.claude/settings.json"
      CC_INSTALLED_PLUGINS="$HOME/.claude/plugins/installed_plugins.json"
      ;;
    *)
      echo "✗ Unsupported OS: $(uname -s)" >&2
      exit 1
      ;;
  esac

  case "$OS" in
    macos)
      DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
      ;;
    windows)
      # In Git Bash, $APPDATA is set
      if [[ -n "${APPDATA:-}" ]]; then
        DESKTOP_CONFIG="$APPDATA/Claude/claude_desktop_config.json"
      else
        DESKTOP_CONFIG=""  # Skipped: cannot resolve
      fi
      ;;
    linux)
      DESKTOP_CONFIG=""  # No Claude desktop app on Linux
      ;;
  esac
}
```

Then in `main()`, call them right after the header echoes:

```bash
  detect_os
  resolve_paths
  echo "Detected OS: $OS"
  echo "Plugin install dir: $INSTALL_DIR"
  if [[ -n "$DESKTOP_CONFIG" ]]; then
    echo "Desktop config: $DESKTOP_CONFIG"
  else
    echo "Desktop config: (not applicable on $OS)"
  fi
  echo ""
```

- [ ] **Step 2: Test on the current machine**

```bash
"/Users/fred/Claude app/zenvibe/install.sh" --check
```

Expected on macOS: `Detected OS: macos`, `Desktop config: /Users/fred/Library/Application Support/Claude/...`.

- [ ] **Step 3: Commit**

```bash
git add install.sh
git commit -m "feat(install): OS detection and path resolution (macOS/Linux/Windows)"
```

---

### Task 8.3: Add preflight checks (command availability + paths)

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Add the preflight functions**

Append to `install.sh` (after `resolve_paths()`):

```bash
# Tracks accumulated preflight failures
PREFLIGHT_HARD_FAIL=false
PREFLIGHT_WARNINGS=()

# Print ✓ if command exists, ✗ if hard-required and missing, ⚠ if soft.
check_command() {
  local cmd="$1"
  local hint="$2"
  local severity="$3"  # "required" or "recommended"
  if command -v "$cmd" >/dev/null 2>&1; then
    printf "  ✓ %-10s\n" "$cmd"
  else
    if [[ "$severity" == "required" ]]; then
      printf "  ✗ %-10s  required — install: %s\n" "$cmd" "$hint"
      PREFLIGHT_HARD_FAIL=true
    else
      printf "  ⚠ %-10s  recommended — install: %s\n" "$cmd" "$hint"
      PREFLIGHT_WARNINGS+=("$cmd is missing — $hint")
    fi
  fi
}

preflight() {
  echo "Preflight checks:"

  # Required everywhere
  check_command git    "https://git-scm.com/  (or: brew install git / apt install git)" required
  check_command python3 "https://www.python.org/  (or: brew install python / apt install python3)" required
  check_command rsync  "(usually pre-installed; brew install rsync / apt install rsync if not)" required

  # Recommended for desktop MCP
  if ! $MODE_CLI_ONLY; then
    check_command uv "https://docs.astral.sh/uv/  (or: brew install uv)" recommended
  fi

  # Claude Code CLI presence
  if [[ -d "$HOME/.claude" ]]; then
    printf "  ✓ %-30s (Claude Code CLI detected)\n" "~/.claude/"
  else
    printf "  ✗ %-30s install Claude Code first: https://claude.com/code\n" "~/.claude/"
    PREFLIGHT_HARD_FAIL=true
  fi

  # Desktop app presence (macOS / Windows only)
  if [[ -n "$DESKTOP_CONFIG" ]]; then
    local desktop_dir
    desktop_dir="$(dirname "$DESKTOP_CONFIG")"
    if [[ -d "$desktop_dir" ]]; then
      printf "  ✓ %-30s (Claude desktop app detected)\n" "$desktop_dir"
    else
      printf "  ⚠ %-30s desktop app not detected — desktop MCP step will be skipped\n" "$desktop_dir"
      PREFLIGHT_WARNINGS+=("Claude desktop app not found at $desktop_dir — skipping desktop MCP")
    fi
  fi

  echo ""
  if $PREFLIGHT_HARD_FAIL; then
    echo "✗ One or more required tools are missing. Install them and re-run." >&2
    exit 1
  fi
  if (( ${#PREFLIGHT_WARNINGS[@]} > 0 )); then
    echo "Warnings (non-blocking):"
    for w in "${PREFLIGHT_WARNINGS[@]}"; do
      echo "  - $w"
    done
    echo ""
  fi
}
```

In `main()`, call `preflight` after the path echoes:

```bash
  preflight
  if $MODE_CHECK_ONLY; then
    echo "✓ Preflight only — no changes made."
    exit 0
  fi
```

- [ ] **Step 2: Test `--check` mode**

```bash
"/Users/fred/Claude app/zenvibe/install.sh" --check
```

Expected: prints each tool check (most ✓), confirms preflight-only, exits 0 cleanly.

- [ ] **Step 3: Test `--cli` mode skips `uv` check**

```bash
"/Users/fred/Claude app/zenvibe/install.sh" --check --cli
```

Expected: same as above but no `uv` line.

- [ ] **Step 4: Commit**

```bash
git add install.sh
git commit -m "feat(install): preflight checks for required + recommended tools"
```

---

### Task 8.4: Add user confirmation gate

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Add `confirm_install`**

Add this function after `preflight()`:

```bash
# Ask the user "yes/no" before any file change. Skipped if --yes.
confirm_install() {
  if $MODE_ASSUME_YES; then
    return 0
  fi
  echo "About to install:"
  echo "  • Copy plugin files to: $INSTALL_DIR"
  echo "  • Register plugin in:   $CC_INSTALLED_PLUGINS"
  echo "  • Enable plugin in:     $CC_SETTINGS"
  if [[ -n "$DESKTOP_CONFIG" ]] && ! $MODE_CLI_ONLY && [[ -d "$(dirname "$DESKTOP_CONFIG")" ]]; then
    echo "  • Add MCP server to:    $DESKTOP_CONFIG"
  else
    echo "  • Desktop MCP:          (skipped)"
  fi
  echo ""
  echo "All JSON files are backed up before being edited."
  echo ""
  read -r -p "Proceed? [y/N] " ans
  case "$ans" in
    y|Y|yes|YES) return 0 ;;
    *) echo "Aborted."; exit 0 ;;
  esac
}
```

In `main()`, call it after preflight (before any modification):

```bash
  confirm_install
```

- [ ] **Step 2: Test that the prompt appears (then abort)**

```bash
echo "n" | "/Users/fred/Claude app/zenvibe/install.sh"
```

Expected: prints the plan, asks Proceed?, prints `Aborted.`, exits 0.

- [ ] **Step 3: Test `--yes` skips prompt**

(Don't run for real yet — the install steps aren't implemented. Verify the function returns 0 by adding `echo "would install"` after `confirm_install` temporarily — or just inspect that the code branches correctly. Skip if you trust the diff.)

- [ ] **Step 4: Commit**

```bash
git add install.sh
git commit -m "feat(install): confirmation prompt with summary of planned actions"
```

---

### Task 8.5: Add the file-copy step (rsync) and JSON safety helpers

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Add backup + rsync + python-json helper**

Append to `install.sh`:

```bash
# Create a timestamped backup of a JSON file if it exists.
# Sets BACKUP_PATH global for the caller.
backup_json() {
  local path="$1"
  BACKUP_PATH=""
  if [[ -f "$path" ]]; then
    local ts
    ts="$(date +%Y%m%d-%H%M%S)"
    BACKUP_PATH="${path}.backup-${ts}"
    cp "$path" "$BACKUP_PATH"
  fi
}

# Run an inline Python snippet that mutates a JSON file safely (read → modify → atomic rewrite).
# Args: JSON path, python expression that takes a dict named `data` and modifies in place.
mutate_json() {
  local path="$1"
  local py_mutation="$2"
  python3 - "$path" <<PY
import json
import os
import sys
import tempfile

path = sys.argv[1]
if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {}

${py_mutation}

# Atomic write
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-install-", suffix=".json")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    # Validate it parses
    with open(tmp) as f:
        json.load(f)
    os.replace(tmp, path)
except Exception:
    if os.path.exists(tmp):
        os.unlink(tmp)
    raise
PY
}

# Copy plugin files using rsync.
copy_files() {
  echo "→ Copying plugin files to $INSTALL_DIR ..."
  mkdir -p "$INSTALL_DIR"
  rsync -a --delete \
    --exclude '.git/' \
    --exclude '*.backup-*' \
    --exclude '__pycache__/' \
    --exclude '.pytest_cache/' \
    --exclude '.idea/' \
    --exclude 'tests/' \
    "$SOURCE_DIR/" "$INSTALL_DIR/"
  echo "  ✓ files copied"
}
```

Note: `tests/` is excluded from the install copy — they are dev-only.

In `main()`, after `confirm_install`, add:

```bash
  copy_files
```

- [ ] **Step 2: Run a dry install on a temporary location to verify rsync behaves**

```bash
TMP_INSTALL="$(mktemp -d)"
# Temporarily override INSTALL_DIR by editing the script? No — just run a manual rsync to confirm the command:
rsync -a --delete --exclude '.git/' --exclude '*.backup-*' --exclude '__pycache__/' --exclude '.pytest_cache/' --exclude '.idea/' --exclude 'tests/' "/Users/fred/Claude app/zenvibe/" "$TMP_INSTALL/"
ls "$TMP_INSTALL/"
rm -rf "$TMP_INSTALL"
```

Expected: shows install.sh, commands/, docs/, hooks/, mcp/, LICENSE, CHANGELOG.md, README.md, etc. NOT `.git/`, `tests/`.

- [ ] **Step 3: Commit**

```bash
git add install.sh
git commit -m "feat(install): file copy via rsync + JSON mutate/backup helpers"
```

---

### Task 8.6: Register the plugin in `installed_plugins.json` and enable in `settings.json`

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Add the registration functions**

Append to `install.sh`:

```bash
register_plugin() {
  echo "→ Registering plugin in $CC_INSTALLED_PLUGINS ..."
  mkdir -p "$(dirname "$CC_INSTALLED_PLUGINS")"
  backup_json "$CC_INSTALLED_PLUGINS"
  if [[ -n "$BACKUP_PATH" ]]; then
    echo "  • backup: $BACKUP_PATH"
  fi

  local version
  version="$(python3 -c "import json; print(json.load(open('$INSTALL_DIR/.claude-plugin/plugin.json'))['version'])")"

  mutate_json "$CC_INSTALLED_PLUGINS" "
from datetime import datetime, timezone
data.setdefault('version', 2)
data.setdefault('plugins', {})
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
existing = data['plugins'].get('zenvibe@local', [{}])
existing[0] = {
    'scope': 'user',
    'installPath': '$INSTALL_DIR',
    'version': '$version',
    'installedAt': existing[0].get('installedAt', now),
    'lastUpdated': now,
}
data['plugins']['zenvibe@local'] = existing
"
  echo "  ✓ registered as zenvibe@local v$version"
}

enable_plugin() {
  echo "→ Enabling plugin in $CC_SETTINGS ..."
  mkdir -p "$(dirname "$CC_SETTINGS")"
  backup_json "$CC_SETTINGS"
  if [[ -n "$BACKUP_PATH" ]]; then
    echo "  • backup: $BACKUP_PATH"
  fi

  mutate_json "$CC_SETTINGS" "
data.setdefault('enabledPlugins', {})['zenvibe@local'] = True
"
  echo "  ✓ enabled"
}
```

In `main()`, after `copy_files`:

```bash
  register_plugin
  enable_plugin
```

- [ ] **Step 2: Dry-run the JSON mutation in isolation**

Test the helper independently with a fake file (do NOT touch the real `~/.claude/`):

```bash
TMP_JSON="$(mktemp -t zenvibe-test.XXXXXX.json)"
echo '{"version":2,"plugins":{}}' > "$TMP_JSON"
source /dev/stdin <<'BASH'
$(awk '/^backup_json\(\)/,/^}/' "/Users/fred/Claude app/zenvibe/install.sh")
$(awk '/^mutate_json\(\)/,/^}/' "/Users/fred/Claude app/zenvibe/install.sh")
BASH
mutate_json "$TMP_JSON" "
from datetime import datetime, timezone
data.setdefault('plugins', {})
data['plugins']['zenvibe@local'] = [{'scope': 'user', 'installPath': '/tmp/fake', 'version': '0.1.0'}]
"
cat "$TMP_JSON"
rm -f "$TMP_JSON"
```

Expected: the JSON now contains the `zenvibe@local` entry, formatted with 2-space indent.

- [ ] **Step 3: Commit**

```bash
git add install.sh
git commit -m "feat(install): register zenvibe@local in installed_plugins + enable in settings"
```

---

### Task 8.7: Configure the desktop app MCP (macOS + Windows)

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Add `configure_desktop_mcp`**

Append:

```bash
configure_desktop_mcp() {
  if $MODE_CLI_ONLY; then
    echo "→ Desktop MCP: skipped (--cli)"
    return
  fi
  if [[ -z "$DESKTOP_CONFIG" ]]; then
    echo "→ Desktop MCP: skipped (no desktop app on $OS)"
    return
  fi
  if [[ ! -d "$(dirname "$DESKTOP_CONFIG")" ]]; then
    echo "→ Desktop MCP: skipped (Claude desktop app not installed)"
    return
  fi
  if ! command -v uv >/dev/null 2>&1; then
    echo "→ Desktop MCP: skipped (uv not installed — install with 'brew install uv' and re-run)"
    return
  fi

  echo "→ Configuring desktop MCP in $DESKTOP_CONFIG ..."
  backup_json "$DESKTOP_CONFIG"
  if [[ -n "$BACKUP_PATH" ]]; then
    echo "  • backup: $BACKUP_PATH"
  fi

  local uv_path
  uv_path="$(command -v uv)"

  mutate_json "$DESKTOP_CONFIG" "
data.setdefault('mcpServers', {})['zenvibe'] = {
    'command': '$uv_path',
    'args': ['run', '--script', '$INSTALL_DIR/mcp/server.py'],
}
"
  echo "  ✓ MCP server 'zenvibe' added (command: $uv_path)"
}
```

In `main()`, after `enable_plugin`:

```bash
  configure_desktop_mcp
```

- [ ] **Step 2: Commit**

```bash
git add install.sh
git commit -m "feat(install): add zenvibe MCP server to claude_desktop_config.json"
```

---

### Task 8.8: Final summary printing

**Files:**
- Modify: `install.sh`

- [ ] **Step 1: Add `print_summary`**

Append:

```bash
print_summary() {
  echo ""
  echo "=== Install complete ==="
  echo ""
  echo "✓ CC CLI / VS Code: /zenpause, /zenresume, /zencheckpoint available"
  echo "  → Start a new \`claude\` session (or restart VS Code Claude Code panel)"
  echo ""
  if $MODE_CLI_ONLY; then
    echo "→ Desktop app: skipped (--cli)"
  elif [[ -z "$DESKTOP_CONFIG" ]]; then
    echo "→ Desktop app: not applicable on $OS"
  elif [[ ! -d "$(dirname "$DESKTOP_CONFIG")" ]]; then
    echo "→ Desktop app: not detected — skipped"
  elif ! command -v uv >/dev/null 2>&1; then
    echo "→ Desktop app: skipped (uv missing). Install uv and re-run to enable."
  else
    echo "✓ Desktop app: MCP server 'zenvibe' configured"
    echo "  → Quit Claude.app entirely (Cmd+Q) and reopen for it to pick up the new MCP"
  fi
  echo ""
  echo "→ Web (claude.ai): manual step — see docs/web-project.md to create a ZenVibe Project"
  echo ""
  echo "Backups of any JSON config that was modified are stored alongside with a"
  echo "  '.backup-YYYYMMDD-HHMMSS' suffix. Restore with 'cp' if anything went wrong."
  echo ""
}
```

In `main()`, after `configure_desktop_mcp`:

```bash
  print_summary
```

- [ ] **Step 2: Now run the installer end-to-end on the real machine**

```bash
"/Users/fred/Claude app/zenvibe/install.sh" --yes
```

Expected:
- preflight all ✓
- files copied
- JSON registrations done
- desktop MCP configured
- summary printed

After running, verify:

```bash
test -d ~/.claude/plugins/zenvibe && echo "✓ install dir"
python3 -c "import json; d=json.load(open(open('/Users/fred/.claude/plugins/installed_plugins.json'))) if False else json.load(open('/Users/fred/.claude/plugins/installed_plugins.json')); print('✓ registered' if 'zenvibe@local' in d['plugins'] else '✗')"
python3 -c "import json; d=json.load(open('/Users/fred/.claude/settings.json')); print('✓ enabled' if d['enabledPlugins'].get('zenvibe@local') else '✗')"
python3 -c "import json; d=json.load(open('/Users/fred/Library/Application Support/Claude/claude_desktop_config.json')); print('✓ MCP' if 'zenvibe' in d['mcpServers'] else '✗')"
```

Expected: 4 lines of `✓`.

- [ ] **Step 3: Run installer again — verify idempotency**

```bash
"/Users/fred/Claude app/zenvibe/install.sh" --yes
```

Expected: succeeds without errors; new timestamped backups are created; final state same as before.

- [ ] **Step 4: Commit**

```bash
git add install.sh
git commit -m "feat(install): final summary with per-surface next steps"
```

---

## Phase 9 — Uninstaller (`uninstall.sh`)

### Task 9.1: Create `uninstall.sh`

**Files:**
- Create: `uninstall.sh`

- [ ] **Step 1: Write the script**

Create `/Users/fred/Claude app/zenvibe/uninstall.sh`:

```bash
#!/usr/bin/env bash
# ZenVibe uninstaller.
#
# Usage:
#   ./uninstall.sh         # remove plugin + JSON entries
#   ./uninstall.sh --yes   # skip confirmation
#   ./uninstall.sh --help
#
# Note: your project JOURNAL.md files are NEVER touched — they belong to you.
set -euo pipefail

MODE_ASSUME_YES=false

usage() {
  sed -n '2,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --help|-h) usage; exit 0 ;;
      --yes|-y)  MODE_ASSUME_YES=true ;;
      *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
  done
}

detect_os() {
  local u="$(uname -s)"
  case "$u" in
    Darwin*)            OS="macos" ;;
    Linux*)             OS="linux" ;;
    MINGW*|MSYS*|CYGWIN*) OS="windows" ;;
    *)                  OS="unknown" ;;
  esac
}

resolve_paths() {
  INSTALL_DIR="$HOME/.claude/plugins/zenvibe"
  CC_SETTINGS="$HOME/.claude/settings.json"
  CC_INSTALLED_PLUGINS="$HOME/.claude/plugins/installed_plugins.json"
  case "$OS" in
    macos)   DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json" ;;
    windows) DESKTOP_CONFIG="${APPDATA:-}/Claude/claude_desktop_config.json" ;;
    *)       DESKTOP_CONFIG="" ;;
  esac
}

backup_json() {
  local path="$1"
  BACKUP_PATH=""
  if [[ -f "$path" ]]; then
    local ts
    ts="$(date +%Y%m%d-%H%M%S)"
    BACKUP_PATH="${path}.backup-${ts}"
    cp "$path" "$BACKUP_PATH"
  fi
}

mutate_json() {
  local path="$1"
  local py_mutation="$2"
  python3 - "$path" <<PY
import json
import os
import sys
import tempfile

path = sys.argv[1]
if not os.path.exists(path):
    sys.exit(0)
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

${py_mutation}

fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-uninstall-", suffix=".json")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    with open(tmp) as f:
        json.load(f)
    os.replace(tmp, path)
except Exception:
    if os.path.exists(tmp):
        os.unlink(tmp)
    raise
PY
}

confirm() {
  if $MODE_ASSUME_YES; then return 0; fi
  echo "About to uninstall ZenVibe:"
  echo "  • Remove install dir:     $INSTALL_DIR"
  echo "  • Remove from:            $CC_INSTALLED_PLUGINS (key zenvibe@local)"
  echo "  • Remove from:            $CC_SETTINGS (enabledPlugins.zenvibe@local)"
  if [[ -n "$DESKTOP_CONFIG" ]]; then
    echo "  • Remove from:            $DESKTOP_CONFIG (mcpServers.zenvibe)"
  fi
  echo ""
  echo "Your project JOURNAL.md files will NOT be touched."
  echo ""
  read -r -p "Proceed? [y/N] " ans
  case "$ans" in
    y|Y|yes|YES) return 0 ;;
    *) echo "Aborted."; exit 0 ;;
  esac
}

main() {
  parse_args "$@"
  detect_os
  resolve_paths
  echo "=== ZenVibe uninstaller ==="
  echo ""
  confirm

  if [[ -d "$INSTALL_DIR" ]]; then
    echo "→ Removing $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
    echo "  ✓ removed"
  else
    echo "→ Install dir not found (already removed?)"
  fi

  if [[ -f "$CC_INSTALLED_PLUGINS" ]]; then
    echo "→ Removing zenvibe@local from installed_plugins.json"
    backup_json "$CC_INSTALLED_PLUGINS"
    [[ -n "$BACKUP_PATH" ]] && echo "  • backup: $BACKUP_PATH"
    mutate_json "$CC_INSTALLED_PLUGINS" "data.get('plugins', {}).pop('zenvibe@local', None)"
    echo "  ✓ removed"
  fi

  if [[ -f "$CC_SETTINGS" ]]; then
    echo "→ Removing zenvibe@local from settings.json enabledPlugins"
    backup_json "$CC_SETTINGS"
    [[ -n "$BACKUP_PATH" ]] && echo "  • backup: $BACKUP_PATH"
    mutate_json "$CC_SETTINGS" "data.get('enabledPlugins', {}).pop('zenvibe@local', None)"
    echo "  ✓ removed"
  fi

  if [[ -n "$DESKTOP_CONFIG" ]] && [[ -f "$DESKTOP_CONFIG" ]]; then
    echo "→ Removing zenvibe from claude_desktop_config.json mcpServers"
    backup_json "$DESKTOP_CONFIG"
    [[ -n "$BACKUP_PATH" ]] && echo "  • backup: $BACKUP_PATH"
    mutate_json "$DESKTOP_CONFIG" "data.get('mcpServers', {}).pop('zenvibe', None)"
    echo "  ✓ removed"
  fi

  echo ""
  echo "✓ Uninstalled. Restart Claude Code surfaces to clear cached state."
}

main "$@"
```

- [ ] **Step 2: Make executable and verify `--help`**

```bash
chmod +x "/Users/fred/Claude app/zenvibe/uninstall.sh"
"/Users/fred/Claude app/zenvibe/uninstall.sh" --help
```

- [ ] **Step 3: Dry-run abort to verify the prompt**

```bash
echo "n" | "/Users/fred/Claude app/zenvibe/uninstall.sh"
```

Expected: prints the plan, asks Proceed?, prints `Aborted.`, exits 0.

- [ ] **Step 4: Commit**

```bash
git add uninstall.sh
git commit -m "feat(uninstall): symmetric uninstaller with backups before edits"
```

---

## Phase 10 — README rewrite

### Task 10.1: Rewrite `README.md`

**Files:**
- Modify: `README.md` (full rewrite)

- [ ] **Step 1: Replace the file content**

Overwrite `README.md` with this complete English version:

````markdown
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

See [`docs/INSTALL.md`](docs/INSTALL.md#troubleshooting) for common issues. Most install problems come from a missing prereq — re-run `./install.sh --check` to diagnose.

---

## Uninstall

```bash
./uninstall.sh
```

It removes the plugin files and config entries, with backups taken before each edit. Your project `JOURNAL.md` files are never touched.

Details in [`docs/INSTALL.md`](docs/INSTALL.md#uninstalling).

---

## Why "ZenVibe"?

"Vibe coding" — chatting with an AI to ship code — is the fastest way to learn and to build. It also has obvious failure modes: lost context, broken state, no audit trail. ZenVibe gives the vibe coder a soft floor without slowing them down. The name leans into the calm, not the panic.

---

## Contributing

PRs welcome. Open an issue first for non-trivial changes so we can talk through the design.

---

## License

[MIT](LICENSE) — © 2026 Fred Fonteyne.
````

- [ ] **Step 2: Verify rendering by reading a few sections**

```bash
head -30 "/Users/fred/Claude app/zenvibe/README.md"
```

Expected: title `# ZenVibe`, tagline, opening paragraph, command table.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(README): full rewrite with public-facing intro + sections"
```

---

## Phase 11 — `docs/INSTALL.md`

### Task 11.1: Create `docs/INSTALL.md`

**Files:**
- Create: `docs/INSTALL.md`

- [ ] **Step 1: Write the file**

Create `/Users/fred/Claude app/zenvibe/docs/INSTALL.md` with this content (11 sections):

````markdown
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
````

- [ ] **Step 2: Smoke check**

```bash
head -10 "/Users/fred/Claude app/zenvibe/docs/INSTALL.md"
```

Expected: title `# Installation Guide`, intro paragraph.

- [ ] **Step 3: Commit**

```bash
git add docs/INSTALL.md
git commit -m "docs: comprehensive INSTALL.md (11 sections, per-OS, troubleshooting, FAQ)"
```

---

## Phase 12 — Delete `scripts/sync-install.sh`

### Task 12.1: Remove the obsolete dev script

**Files:**
- Delete: `scripts/sync-install.sh`

- [ ] **Step 1: Remove the file and its parent dir if empty**

```bash
cd "/Users/fred/Claude app/zenvibe"
git rm scripts/sync-install.sh
rmdir scripts 2>/dev/null || true   # only removes if empty; harmless otherwise
```

- [ ] **Step 2: Commit**

```bash
git commit -m "chore: remove scripts/sync-install.sh (replaced by install.sh)"
```

---

## Phase 13 — Local validation

### Task 13.1: Run the full test suite

**Files:** none

- [ ] **Step 1: Run pytest**

```bash
cd "/Users/fred/Claude app/zenvibe"
uv run --with pytest --with mcp pytest tests/ -v
```

Expected: all tests PASS (the MCP messages + session-start-briefing tests).

### Task 13.2: Run the installer against the live install

- [ ] **Step 1: Run install.sh and verify all surfaces**

```bash
"/Users/fred/Claude app/zenvibe/install.sh" --yes
```

Expected output: preflight ✓, files copied, registered, enabled, desktop MCP configured, final summary.

- [ ] **Step 2: Verify file content shipped to install dir**

```bash
head -3 ~/.claude/plugins/zenvibe/README.md
head -3 ~/.claude/plugins/zenvibe/commands/zenpause.md
head -3 ~/.claude/plugins/zenvibe/mcp/server.py
```

Expected: all in English.

### Task 13.3: Manually exercise the slash commands

- [ ] **Step 1: In a fresh `claude` session inside a test project**

In a separate terminal, open `claude` inside a real or scratch project:

```bash
cd /tmp/scratch-zenvibe-test && git init -q && echo "test" > a.txt && claude
```

Inside the session, type:
1. `/help` — expect `/zenpause`, `/zenresume`, `/zencheckpoint` listed.
2. `/zenpause testing the public release` — expect commit + journal entry + confirmation, in English.
3. `/zenresume` — expect briefing referring to the entry just written, in English.

If any of these fails, debug before publishing.

### Task 13.4: Verify the desktop app MCP

- [ ] **Step 1: Restart Claude.app (Cmd+Q + reopen)**

- [ ] **Step 2: In a new chat, ask "What MCP tools are available?"**

Expect: list including `zenvibe_pause`, `zenvibe_resume`, `zenvibe_checkpoint`.

---

## Phase 14 — Publish to GitHub

### Task 14.1: Final review before publication

- [ ] **Step 1: Confirm git status is clean**

```bash
cd "/Users/fred/Claude app/zenvibe"
git status
```

Expected: `nothing to commit, working tree clean`.

- [ ] **Step 2: Skim recent commits**

```bash
git log --oneline release/v0.1 ^main
```

Expected: all the commits for this release, sensible messages.

- [ ] **Step 3: Merge release branch into main**

```bash
git checkout main
git merge --no-ff release/v0.1 -m "release: v0.1.0 public release"
```

- [ ] **Step 4: Tag the release**

```bash
git tag -a v0.1.0 -m "v0.1.0 — initial public release"
```

### Task 14.2: Create the GitHub repo and push

- [ ] **Step 1: Verify gh auth**

```bash
gh auth status
```

Expected: logged in as Fredje777, scope includes `repo`.

- [ ] **Step 2: Create the public repo and push**

```bash
cd "/Users/fred/Claude app/zenvibe"
gh repo create Fredje777/claude-zenvibe \
  --public \
  --source=. \
  --description "Vibe-code with a safety net. Pause/resume/checkpoint sessions in Claude Code, with auto-protection before context compaction." \
  --push
```

Expected: creates `Fredje777/claude-zenvibe`, sets remote, pushes `main`.

- [ ] **Step 3: Push tags**

```bash
git push origin v0.1.0
```

- [ ] **Step 4: Verify the repo is live**

```bash
gh repo view Fredje777/claude-zenvibe --web
```

Opens the repo in the browser. Verify:
- README renders correctly (intro table is readable)
- LICENSE shows MIT badge
- CHANGELOG visible
- All files present (commands/, hooks/, mcp/, docs/, install.sh, uninstall.sh)

### Task 14.3: Smoke-test installing from the live repo

- [ ] **Step 1: Clone fresh to a different location and run the installer**

```bash
cd /tmp
rm -rf /tmp/claude-zenvibe-smoke
git clone https://github.com/Fredje777/claude-zenvibe.git claude-zenvibe-smoke
cd claude-zenvibe-smoke
./install.sh --check
```

Expected: preflight passes (same as before). This validates that the repo as-cloned-from-GitHub still works end-to-end.

- [ ] **Step 2: Clean up**

```bash
rm -rf /tmp/claude-zenvibe-smoke
```

---

## Self-review checklist

Before declaring the plan complete, run through:

- [ ] **Spec coverage:** every section of `docs/superpowers/specs/2026-05-13-public-release-design.md` maps to at least one task here.
- [ ] **No placeholders:** no `TBD`, `TODO`, `…`, or "fill in details" anywhere.
- [ ] **Type consistency:** function names (`_t`, `_do_git_checkpoint`, `_resolve_repo`, etc.) match exactly across tasks.
- [ ] **All bullets are checkboxes (`- [ ]`):** for tracking.
- [ ] **All file paths absolute:** `/Users/fred/Claude app/zenvibe/...` everywhere.
- [ ] **Every code change has a test or smoke check:** for prose (READMEs, commands), a `head -N` is acceptable; for logic (MCP, hook script), pytest.
- [ ] **Every step is a single action:** if a step has multiple actions, it should be split.
