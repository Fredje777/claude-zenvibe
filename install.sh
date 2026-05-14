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

main "$@"
