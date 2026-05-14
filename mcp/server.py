#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=1.0"]
# ///
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
from __future__ import annotations

import datetime
import re
import subprocess
from pathlib import Path
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("zenvibe")

# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

SUSPICIOUS_PATTERNS = [
    re.compile(r"(^|/)\.env(\.|$)"),
    re.compile(r"\.key$"),
    re.compile(r"\.pem$"),
    re.compile(r"\.pfx$"),
    re.compile(r"\.p12$"),
    re.compile(r"id_rsa"),
    re.compile(r"credentials", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"\.npmrc$"),
]

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


def _resolve_repo(project_path: str) -> Path:
    """Expand ~ and resolve the project path, raising if it doesn't exist."""
    path = Path(project_path).expanduser().resolve()
    if not path.is_dir():
        raise ValueError(f"Project path does not exist or is not a directory: {path}")
    return path


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _is_git_repo(path: Path) -> bool:
    return _git(["rev-parse", "--is-inside-work-tree"], path).returncode == 0


def _filter_suspicious(files: list[str]) -> tuple[list[str], list[str]]:
    safe: list[str] = []
    suspicious: list[str] = []
    for f in files:
        if any(p.search(f) for p in SUSPICIOUS_PATTERNS):
            suspicious.append(f)
        else:
            safe.append(f)
    return safe, suspicious


def _find_or_create_journal(repo: Path) -> Path:
    docs_journal = repo / "docs" / "JOURNAL.md"
    root_journal = repo / "JOURNAL.md"
    if docs_journal.exists():
        return docs_journal
    if root_journal.exists():
        return root_journal
    (repo / "docs").mkdir(parents=True, exist_ok=True)
    docs_journal.touch()
    return docs_journal


def _prepend_to_journal(journal: Path, entry: str) -> None:
    existing = journal.read_text(encoding="utf-8") if journal.exists() else ""
    sep = "\n\n" if existing.strip() else ""
    journal.write_text(entry + sep + existing, encoding="utf-8")


def _now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def _do_git_checkpoint(
    repo: Path, commit_message: str
) -> dict[str, Any]:
    """Stage safe modified files, commit, push. Returns a result dict."""
    result: dict[str, Any] = {
        "is_git_repo": False,
        "branch": None,
        "commit_sha": None,
        "pushed": False,
        "skipped_suspicious": [],
        "errors": [],
        "warnings": [],
    }

    if not _is_git_repo(repo):
        result["warnings"].append("Not a git repo — git step skipped.")
        return result

    result["is_git_repo"] = True
    result["branch"] = _git(["branch", "--show-current"], repo).stdout.strip() or None

    # Collect modified + untracked files (porcelain v1)
    status = _git(["status", "--porcelain"], repo)
    candidates: list[str] = []
    for line in status.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        # Handle renames "old -> new"
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        candidates.append(path)

    if not candidates:
        result["warnings"].append("Working tree clean — nothing to commit.")
        return result

    safe, suspicious = _filter_suspicious(candidates)
    if suspicious:
        result["skipped_suspicious"] = suspicious

    if not safe:
        result["warnings"].append("All modified files look like secrets — nothing committed.")
        return result

    add = _git(["add", "--", *safe], repo)
    if add.returncode != 0:
        result["errors"].append(f"git add failed: {add.stderr.strip()}")
        return result

    commit = _git(["commit", "-m", commit_message], repo)
    if commit.returncode != 0:
        result["errors"].append(f"git commit failed: {commit.stderr.strip() or commit.stdout.strip()}")
        return result

    sha = _git(["rev-parse", "--short", "HEAD"], repo).stdout.strip()
    result["commit_sha"] = sha

    # Push if remote configured
    remote_check = _git(["remote"], repo)
    if remote_check.stdout.strip():
        push = _git(["push"], repo)
        if push.returncode == 0:
            result["pushed"] = True
        else:
            # Try setting upstream if missing
            if "no upstream branch" in push.stderr.lower() and result["branch"]:
                push2 = _git(["push", "-u", "origin", result["branch"]], repo)
                if push2.returncode == 0:
                    result["pushed"] = True
                else:
                    result["errors"].append(f"git push -u failed: {push2.stderr.strip()}")
            else:
                result["errors"].append(f"git push failed: {push.stderr.strip()}")
    else:
        result["warnings"].append("No remote configured — no push.")

    return result


def _bullets(items: list[str] | None) -> str:
    if not items:
        return "- _(rien)_"
    return "\n".join(f"- {item}" for item in items)


def _numbered(items: list[str] | None) -> str:
    if not items:
        return "1. _(rien)_"
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1))


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


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
        git_lines.append(
            f"{_t('git_branch_prefix', language)}{git_result['branch']}"
        )
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


@mcp.tool()
def zenvibe_resume(project_path: str) -> dict[str, Any]:
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
    repo = _resolve_repo(project_path)
    errors: list[str] = []

    # Locate journal
    journal_path = None
    for candidate in (repo / "docs" / "JOURNAL.md", repo / "JOURNAL.md"):
        if candidate.exists():
            journal_path = candidate
            break

    journal_content = ""
    if journal_path:
        try:
            journal_content = journal_path.read_text(encoding="utf-8")
        except OSError as e:
            errors.append(f"Cannot read journal: {e}")
    else:
        errors.append("No JOURNAL.md found (neither docs/JOURNAL.md nor root JOURNAL.md).")

    # CLAUDE.md
    claude_md_content = None
    claude_md = repo / "CLAUDE.md"
    if claude_md.exists():
        try:
            claude_md_content = claude_md.read_text(encoding="utf-8")
        except OSError as e:
            errors.append(f"Cannot read CLAUDE.md: {e}")

    # Git state
    git_status = ""
    recent_commits: list[str] = []
    branch = None
    if _is_git_repo(repo):
        git_status = _git(["status", "--short"], repo).stdout
        recent_commits = _git(["log", "-5", "--oneline"], repo).stdout.splitlines()
        branch = _git(["branch", "--show-current"], repo).stdout.strip() or None

    return {
        "journal_path": str(journal_path.relative_to(repo)) if journal_path else None,
        "journal_content": journal_content,
        "claude_md_content": claude_md_content,
        "git_status": git_status,
        "recent_commits": recent_commits,
        "branch": branch,
        "errors": errors,
    }


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


if __name__ == "__main__":
    mcp.run()
