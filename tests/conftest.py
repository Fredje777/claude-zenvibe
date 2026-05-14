"""pytest fixtures for ZenVibe tests."""
import subprocess
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
