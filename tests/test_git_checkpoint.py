"""Allowlist behaviour of _do_git_checkpoint — the WIP-asymmetry fix.

These exercise the git path directly (the part the slash commands had but the
MCP server lacked): the server must commit ONLY the files the caller lists.
"""
import subprocess
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).parent.parent / "mcp"
sys.path.insert(0, str(SERVER_DIR))

import server  # noqa: E402


def _status(repo: Path) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout


def test_commits_only_listed_files(tmp_repo):
    """A listed file is committed; an unlisted (WIP) file is left untouched."""
    (tmp_repo / "clean.py").write_text("def ok():\n    return 1\n")
    (tmp_repo / "wip.py").write_text("def broken(:\n")  # caller judged WIP

    result = server._do_git_checkpoint(
        tmp_repo, "feat: clean only", files_to_commit=["clean.py"]
    )

    assert result["commit_sha"] is not None
    assert result["skipped_not_listed"] == ["wip.py"]
    status = _status(tmp_repo)
    assert "wip.py" in status      # still uncommitted
    assert "clean.py" not in status  # committed → gone from status


def test_listed_secret_is_still_skipped(tmp_repo):
    """Secrets are dropped even when the caller mistakenly lists them."""
    (tmp_repo / "app.py").write_text("x = 1\n")
    (tmp_repo / ".env").write_text("SECRET=1\n")

    result = server._do_git_checkpoint(
        tmp_repo, "feat: app", files_to_commit=["app.py", ".env"]
    )

    assert ".env" in result["skipped_suspicious"]
    assert ".env" in _status(tmp_repo)  # never committed


def test_listed_file_not_changed_is_ignored(tmp_repo):
    """A listed path that did not actually change is harmless (no crash)."""
    (tmp_repo / "real.py").write_text("x = 1\n")

    result = server._do_git_checkpoint(
        tmp_repo, "feat: real", files_to_commit=["real.py", "ghost.py"]
    )

    assert result["commit_sha"] is not None
    assert "ghost.py" not in result["skipped_not_listed"]


def test_empty_allowlist_commits_nothing(tmp_repo):
    """An empty list commits nothing and reports the changed file as unlisted."""
    (tmp_repo / "a.py").write_text("x = 1\n")

    result = server._do_git_checkpoint(
        tmp_repo, "feat: none", files_to_commit=[]
    )

    assert result["commit_sha"] is None
    assert result["skipped_not_listed"] == ["a.py"]
