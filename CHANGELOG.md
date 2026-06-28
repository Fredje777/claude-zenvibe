# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Optional `ZENVIBE_LANG=en|fr` override for MCP journal and confirmation output language.

## [0.2.1] — 2026-06-02

### Fixed

- **Hooks now actually fire.** `hooks/hooks.json` wrapped its events (`PreCompact`, `SessionStart`) at the top level instead of under the required `hooks` key. They are now correctly nested, so the auto-checkpoint and session-start briefing run as intended. Caught by `claude plugin validate`.
- **Removed the non-schema `displayName` field** from `plugin.json` — it was rejected by the official manifest validator. The display name now derives from `name`.

## [0.2.0] — 2026-06-02

### Fixed

- MCP server no longer blind-commits every changed file. `zenvibe_pause` and `zenvibe_checkpoint` now require `files_to_commit`; only listed, secret-filtered files are committed, and unlisted changes are returned in `skipped_not_listed` — closing the WIP asymmetry with the slash commands.

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
