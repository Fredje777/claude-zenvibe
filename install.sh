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
  preflight
  if $MODE_CHECK_ONLY; then
    echo "✓ Preflight only — no changes made."
    exit 0
  fi
  confirm_install
  copy_files
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
