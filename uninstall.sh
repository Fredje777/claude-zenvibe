#!/usr/bin/env bash
# ZenVibe uninstaller.
#
# Usage:
#   ./uninstall.sh         # remove plugin + JSON entries
#   ./uninstall.sh --yes   # skip confirmation
#   ./uninstall.sh --help
#
# Note: your project JOURNAL.md files are NEVER touched — they belong to you.
set -euo pipefail

MODE_ASSUME_YES=false

usage() {
  sed -n '2,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --help|-h) usage; exit 0 ;;
      --yes|-y)  MODE_ASSUME_YES=true ;;
      *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
  done
}

detect_os() {
  local u="$(uname -s)"
  case "$u" in
    Darwin*)            OS="macos" ;;
    Linux*)             OS="linux" ;;
    MINGW*|MSYS*|CYGWIN*) OS="windows" ;;
    *)                  OS="unknown" ;;
  esac
}

resolve_paths() {
  INSTALL_DIR="$HOME/.claude/plugins/zenvibe"
  CC_SETTINGS="$HOME/.claude/settings.json"
  CC_INSTALLED_PLUGINS="$HOME/.claude/plugins/installed_plugins.json"
  case "$OS" in
    macos)   DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json" ;;
    windows) DESKTOP_CONFIG="${APPDATA:-}/Claude/claude_desktop_config.json" ;;
    *)       DESKTOP_CONFIG="" ;;
  esac
}

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

mutate_json() {
  local path="$1"
  local py_mutation="$2"
  python3 - "$path" <<PY
import json
import os
import sys
import tempfile

path = sys.argv[1]
if not os.path.exists(path):
    sys.exit(0)
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

${py_mutation}

fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-uninstall-", suffix=".json")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    with open(tmp) as f:
        json.load(f)
    os.replace(tmp, path)
except Exception:
    if os.path.exists(tmp):
        os.unlink(tmp)
    raise
PY
}

confirm() {
  if $MODE_ASSUME_YES; then return 0; fi
  echo "About to uninstall ZenVibe:"
  echo "  • Remove install dir:     $INSTALL_DIR"
  echo "  • Remove from:            $CC_INSTALLED_PLUGINS (key zenvibe@local)"
  echo "  • Remove from:            $CC_SETTINGS (enabledPlugins.zenvibe@local)"
  if [[ -n "$DESKTOP_CONFIG" ]]; then
    echo "  • Remove from:            $DESKTOP_CONFIG (mcpServers.zenvibe)"
  fi
  echo ""
  echo "Your project JOURNAL.md files will NOT be touched."
  echo ""
  read -r -p "Proceed? [y/N] " ans
  case "$ans" in
    y|Y|yes|YES) return 0 ;;
    *) echo "Aborted."; exit 0 ;;
  esac
}

main() {
  parse_args "$@"
  detect_os
  resolve_paths
  echo "=== ZenVibe uninstaller ==="
  echo ""
  confirm

  if [[ -d "$INSTALL_DIR" ]]; then
    echo "→ Removing $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
    echo "  ✓ removed"
  else
    echo "→ Install dir not found (already removed?)"
  fi

  if [[ -f "$CC_INSTALLED_PLUGINS" ]]; then
    echo "→ Removing zenvibe@local from installed_plugins.json"
    backup_json "$CC_INSTALLED_PLUGINS"
    [[ -n "$BACKUP_PATH" ]] && echo "  • backup: $BACKUP_PATH"
    mutate_json "$CC_INSTALLED_PLUGINS" "data.get('plugins', {}).pop('zenvibe@local', None)"
    echo "  ✓ removed"
  fi

  if [[ -f "$CC_SETTINGS" ]]; then
    echo "→ Removing zenvibe@local from settings.json enabledPlugins"
    backup_json "$CC_SETTINGS"
    [[ -n "$BACKUP_PATH" ]] && echo "  • backup: $BACKUP_PATH"
    mutate_json "$CC_SETTINGS" "data.get('enabledPlugins', {}).pop('zenvibe@local', None)"
    echo "  ✓ removed"
  fi

  if [[ -n "$DESKTOP_CONFIG" ]] && [[ -f "$DESKTOP_CONFIG" ]]; then
    echo "→ Removing zenvibe from claude_desktop_config.json mcpServers"
    backup_json "$DESKTOP_CONFIG"
    [[ -n "$BACKUP_PATH" ]] && echo "  • backup: $BACKUP_PATH"
    mutate_json "$DESKTOP_CONFIG" "data.get('mcpServers', {}).pop('zenvibe', None)"
    echo "  ✓ removed"
  fi

  echo ""
  echo "✓ Uninstalled. Restart Claude Code surfaces to clear cached state."
}

main "$@"
