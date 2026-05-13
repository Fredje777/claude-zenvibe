#!/usr/bin/env bash
# Sync the ZenVibe dev source to the installed location used by Claude Code
# CLI, the Claude Code VS Code extension, and the Claude desktop app.
#
# Run this after editing files in this repo. Restart the relevant Claude
# surface afterwards (the desktop app definitely needs a restart; CC CLI
# picks up changes on the next session).

set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL_DIR="$HOME/.claude/plugins/zen"

if [[ ! -d "$SOURCE_DIR/.claude-plugin" ]]; then
  echo "✗ $SOURCE_DIR does not look like the ZenVibe source (no .claude-plugin/)." >&2
  exit 1
fi

mkdir -p "$INSTALL_DIR"

# rsync mirror: --delete removes files in dest that no longer exist in src
# Excludes: .git history (not needed at install location), DS_Store, IDE junk.
rsync -a --delete \
  --exclude '.git/' \
  --exclude '.DS_Store' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  "$SOURCE_DIR/" "$INSTALL_DIR/"

echo "✓ Synced $SOURCE_DIR → $INSTALL_DIR"
echo ""
echo "Pense à :"
echo "  - relancer l'app desktop Claude pour recharger le MCP server"
echo "  - redémarrer une nouvelle session CC CLI pour recharger commands/hooks"
