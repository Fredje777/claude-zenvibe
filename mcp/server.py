#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=1.0"]
# ///
"""ZenVibe MCP server.

Exposes three tools — `zen_pause`, `zen_resume`, `zen_compact` —
that mirror the ZenVibe slash commands for surfaces where slash commands
are not available (Claude desktop app, claude.ai web with custom integrations).

Design:
- The LLM does the thinking (what to commit, what to write in the journal).
- This server does the IO (git operations, file read/write).
- Tools take structured arguments produced by the LLM; the server validates,
  performs the side effects, and returns a structured result.
"""
from __future__ import annotations

import datetime
import re
import subprocess
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("zen")

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

GENERIC_COMPACT_INSTRUCTIONS = (
    "Garde en détail : les conventions du projet (commits, sécurité données, "
    "validations obligatoires), l'état d'avancement courant, les décisions "
    "techniques prises sur l'architecture et l'API, et toute question ouverte "
    "non résolue. Tu peux résumer brièvement les itérations de code et les "
    "tâtonnements."
)


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
        result["warnings"].append("Pas un repo git — étape git sautée.")
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
        result["warnings"].append("git status propre — rien à committer.")
        return result

    safe, suspicious = _filter_suspicious(candidates)
    if suspicious:
        result["skipped_suspicious"] = suspicious

    if not safe:
        result["warnings"].append("Tous les fichiers modifiés ressemblent à des secrets — aucun commit fait.")
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
        result["warnings"].append("Pas de remote configuré — pas de push.")

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
def zen_pause(
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
) -> dict[str, Any]:
    """Sauvegarde l'état de la session avant une absence de plusieurs heures.

    Workflow :
    1. Commit + push de ce qui est commitable (fichiers sensibles écartés).
    2. Écrit une entrée détaillée en haut de docs/JOURNAL.md.
    3. Retourne un résumé des actions effectuées.

    Args:
        project_path: Chemin absolu (ou ~) du projet sur lequel agir.
        summary: Résumé en une phrase de ce qu'on a fait cette session.
        commit_message: Message de commit à utiliser (suit la convention du projet).
        completed: Liste des tâches terminées dans cette itération.
        current_task: Tâche en cours et son état précis (1 phrase).
        remaining: Tâches restantes par ordre de priorité.
        decisions: Décisions techniques prises cette session.
        open_questions: Questions ouvertes à poser à l'utilisateur.
        attention_points: Optionnel — refactos, code smells, WIP à reprendre.
        note: Optionnel — note libre de pause fournie par l'utilisateur.

    Returns:
        Un dict avec `commit_sha`, `pushed`, `journal_path`, `branch`,
        `errors`, `warnings`, `skipped_suspicious`.
    """
    repo = _resolve_repo(project_path)
    git_result = _do_git_checkpoint(repo, commit_message)

    journal = _find_or_create_journal(repo)
    now = _now()

    parts = [f"## {now} — Pause"]
    if note:
        parts.append(f"\n> Note de pause : {note}")
    parts.append(f"\n**Résumé :** {summary}")
    parts.append("\n### Tâches terminées (itération en cours)\n" + _bullets(completed))
    parts.append("\n### Tâche en cours\n- " + current_task)
    parts.append("\n### Tâches restantes (par ordre)\n" + _numbered(remaining))
    parts.append("\n### Décisions techniques prises cette session\n" + _bullets(decisions))
    parts.append("\n### Questions ouvertes\n" + _bullets(open_questions))

    git_lines = []
    if git_result["branch"]:
        git_lines.append(f"- Branche : {git_result['branch']}")
    if git_result["commit_sha"]:
        git_lines.append(f"- Dernier commit : {git_result['commit_sha']} {commit_message}")
    if not git_lines:
        git_lines.append("- _(pas de repo git ou rien à committer)_")
    parts.append("\n### Git\n" + "\n".join(git_lines))

    if attention_points:
        parts.append("\n### Points d'attention pour la reprise\n" + _bullets(attention_points))

    entry = "\n".join(parts)
    _prepend_to_journal(journal, entry)

    return {
        "journal_path": str(journal.relative_to(repo)),
        **git_result,
    }


@mcp.tool()
def zen_resume(project_path: str) -> dict[str, Any]:
    """Lit le contexte pour reprendre après une pause ou compaction.

    Workflow :
    1. Lit docs/JOURNAL.md (ou JOURNAL.md racine) en entier.
    2. Lit CLAUDE.md à la racine s'il existe.
    3. Récupère l'état git (status, log -5, branche).
    4. Retourne tout en structuré pour que le LLM compose le briefing.

    Args:
        project_path: Chemin absolu (ou ~) du projet.

    Returns:
        Un dict avec `journal_content`, `claude_md_content`, `git_status`,
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
        errors.append("Aucun JOURNAL.md trouvé (ni docs/JOURNAL.md ni JOURNAL.md racine).")

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
def zen_compact(
    project_path: str,
    summary: str,
    commit_message: str,
    decisions: list[str],
    files_touched: list[str],
    next_step: str,
) -> dict[str, Any]:
    """Prépare une compaction propre.

    Workflow :
    1. Commit + push de ce qui est commitable.
    2. Écrit une entrée *session-focused* en haut de docs/JOURNAL.md.
    3. Lit .claude/zen.md (instructions custom) ou utilise un template
       générique, puis renvoie la commande `/compact <instructions>`
       prête à coller.

    Args:
        project_path: Chemin du projet.
        summary: Résumé en une phrase de ce qu'on a fait cette session.
        commit_message: Message de commit.
        decisions: Décisions techniques de la session.
        files_touched: Fichiers principaux touchés.
        next_step: Prochaine étape claire (1 ligne actionnable).

    Returns:
        Un dict avec `compact_command` (à coller dans l'UI), plus le résultat
        git et le chemin du journal.
    """
    repo = _resolve_repo(project_path)
    git_result = _do_git_checkpoint(repo, commit_message)

    journal = _find_or_create_journal(repo)
    now = _now()

    parts = [
        f"## {now} — Compact",
        f"\n**Résumé :** {summary}",
        "\n### Fait dans cette session\n- " + summary,
        "\n### Décisions techniques\n" + _bullets(decisions),
        "\n### Fichiers touchés\n" + _bullets(files_touched),
        "\n### Prochaine étape claire\n- " + next_step,
    ]
    _prepend_to_journal(journal, "\n".join(parts))

    # Custom compact instructions per project (if any)
    custom = repo / ".claude" / "zen.md"
    if custom.exists():
        raw = custom.read_text(encoding="utf-8")
    else:
        raw = GENERIC_COMPACT_INSTRUCTIONS

    # Collapse to single line (some Claude UIs reject multi-line /compact arg)
    single_line = re.sub(r"\s+", " ", raw).strip()
    compact_command = f"/compact {single_line}"

    return {
        "journal_path": str(journal.relative_to(repo)),
        "compact_command": compact_command,
        **git_result,
    }


if __name__ == "__main__":
    mcp.run()
