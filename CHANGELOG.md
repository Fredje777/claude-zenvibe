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
