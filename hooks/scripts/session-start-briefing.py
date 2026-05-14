#!/usr/bin/env python3
"""SessionStart hook: inject a mini-briefing if a recent JOURNAL.md exists.

Silent unless:
  - source is "startup" or "compact" (not "resume" or "clear")
  - cwd contains docs/JOURNAL.md or JOURNAL.md
  - that journal was modified within the last 14 days

Otherwise emits nothing, so non-ZenVibe projects stay completely quiet.
"""
from __future__ import annotations

import json
import os
import sys
import time

STALE_THRESHOLD_DAYS = 14


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    source = data.get("source", "")
    cwd = data.get("cwd") or os.getcwd()

    # Only nudge on a fresh launch or post-compaction reload.
    # On --resume / --continue or /clear, the user already controls the flow.
    if source not in ("startup", "compact"):
        return 0

    journal = None
    for candidate in (
        os.path.join(cwd, "docs", "JOURNAL.md"),
        os.path.join(cwd, "JOURNAL.md"),
    ):
        if os.path.isfile(candidate):
            journal = candidate
            break

    if not journal:
        return 0

    try:
        age_days = (time.time() - os.path.getmtime(journal)) / 86400
    except OSError:
        return 0

    if age_days > STALE_THRESHOLD_DAYS:
        return 0

    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if not plugin_root:
        return 0

    prompt_path = os.path.join(plugin_root, "hooks", "session-start-prompt.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            sys.stdout.write(f.read())
    except OSError:
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
