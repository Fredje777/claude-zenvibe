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
