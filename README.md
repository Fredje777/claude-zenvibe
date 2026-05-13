# ZenVibe

Pauses, reprises et compactages propres pour les sessions Claude — sur **toutes les surfaces**.

ZenVibe gère les trois moments où une session Claude perd habituellement son contexte :

- **Pause** — tu t'arrêtes pour quelques heures et tu veux pouvoir reprendre proprement.
- **Reprise** — tu reviens et tu veux te remettre en contexte sans relire tout l'historique.
- **Compaction** — la conversation se compacte (manuellement ou automatiquement) et tu veux préserver le fil.

Le principe est simple : **`docs/JOURNAL.md` est la source unique de vérité**. ZenVibe l'écrit, le lit, et utilise Git comme filet de sécurité.

---

## Couverture par surface

| Surface | Mécanisme | Status |
|---|---|---|
| **Terminal (Claude Code CLI)** | Slash commands + hooks | ✅ Natif |
| **VS Code (extension Claude Code)** | Slash commands + hooks | ✅ Natif (partage `~/.claude/`) |
| **App desktop Claude.ai** | MCP server (3 tools) | ✅ Via MCP |
| **Web claude.ai** | Project + system prompt | ✅ Via Project (mode narratif) |

---

## Composants

### Slash commands (CC CLI + VS Code)

| Commande | Quand | Action |
|---|---|---|
| `/zenpause [note]` | Tu pars pour quelques heures | Commit + push + entrée détaillée dans `docs/JOURNAL.md` (sprint, décisions, questions, points d'attention) |
| `/zenresume` | Tu reviens d'une pause ou d'une compaction | Lit le JOURNAL + `CLAUDE.md`, résume l'état, propose la prochaine action, attend ton feu vert |
| `/zencompact` | Tu veux compacter consciemment | Checkpoint léger + sort la commande `/compact <instructions>` prête à coller |

### Hooks (CC CLI + VS Code)

| Événement | Action |
|---|---|
| `PreCompact` | Avant toute compaction (manuelle ou auto), Claude reçoit l'instruction de faire un checkpoint propre : commit, JOURNAL.md, push. Filet de sécurité si tu oublies de lancer `/zencompact`. |
| `SessionStart` | À l'ouverture (mode `startup` ou `compact`), si un `JOURNAL.md` récent (<14 jours) existe, Claude affiche un mini-briefing 3-lignes au premier message. Silencieux sinon. |

### MCP tools (App desktop)

| Tool | Args | Action |
|---|---|---|
| `zen_pause` | `project_path, summary, commit_message, completed, current_task, remaining, decisions, open_questions, attention_points?, note?` | Exécute le commit/push + écrit l'entrée JOURNAL |
| `zen_resume` | `project_path` | Lit JOURNAL + CLAUDE.md + état git, renvoie le contexte structuré |
| `zen_compact` | `project_path, summary, commit_message, decisions, files_touched, next_step` | Checkpoint + renvoie la commande `/compact` à coller |

### Project preset (Web)

`docs/web-project.md` contient un system prompt copiable pour créer un Project ZenVibe sur claude.ai. Mode narratif (pas d'exécution réelle, le LLM produit les artefacts que tu copies dans ton terminal).

---

## Installation

### Pour Claude Code CLI + VS Code + App desktop (en une fois)

L'app desktop ne suit pas les symlinks pour la discovery des plugins, donc on installe en copiant le dossier dans `~/.claude/plugins/zen/`. Pour une install locale depuis le dépôt cloné :

```bash
./scripts/sync-install.sh
```

Ce script copie le dossier dans `~/.claude/plugins/zen/` (mirror rsync avec `--delete`). À relancer après chaque modif du source.

Tu dois aussi enregistrer le plugin dans `~/.claude/plugins/installed_plugins.json` et l'activer dans `~/.claude/settings.json` (voir `expert-comptable@local` comme modèle), ou plus simplement utiliser `/plugin` dans Claude Code pour gérer l'installation.

Une fois installé :
- Les 3 slash commands apparaissent dans `/help` (terminal + VS Code)
- Les hooks `PreCompact` et `SessionStart` se déclenchent automatiquement
- Le plugin apparaît dans **Customize → Plugins personnels** de l'app desktop

Une fois installé :
- Les 3 slash commands apparaissent dans `/help`
- Les hooks `PreCompact` et `SessionStart` se déclenchent automatiquement
- Le MCP server `zen` est aussi exposé (via `.mcp.json`) — utile si tu préfères l'interface MCP plutôt que les slash commands

### Pour exposer aussi le MCP server dans l'app desktop

Le plugin est déjà visible dans la liste de l'app desktop après `sync-install.sh`, mais le MCP server (qui permet d'utiliser ZenVibe **comme un tool** depuis l'app, sans dépendre du système de plugins) demande une config en plus.

Ajoute dans `~/Library/Application Support/Claude/claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "zen": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--script",
        "/Users/fred/.claude/plugins/zen/mcp/server.py"
      ]
    }
  }
}
```

Redémarre l'app. Au prochain démarrage, les 3 tools `zen_*` (`zen_pause`, `zen_resume`, `zen_compact`) sont disponibles à Claude. Tu invoques en langage naturel : « Fais une pause ZenVibe sur le projet `/Users/fred/dev/kslb-bilans` ».

**Prérequis** : `uv` installé (`brew install uv`). `uv run --script` installe automatiquement la dépendance `mcp` à la première exécution.

### Pour claude.ai (web)

Suis les instructions de [`docs/web-project.md`](docs/web-project.md) : crée un Project, colle le system prompt fourni.

---

## Configuration par projet (optionnel)

Tu peux créer un fichier `.claude/zen.md` à la racine d'un projet pour personnaliser les instructions de compaction. Si absent, ZenVibe utilise un template générique.

Exemple `.claude/zen.md` :

```markdown
Garde en détail : les conventions de commits du repo, l'état du Sprint courant,
le schéma DB en cours d'évolution, les choix sur les prompts LLM, et toute
question ouverte.
```

---

## Conventions

ZenVibe écrit toujours dans `docs/JOURNAL.md` (fallback : `JOURNAL.md` à la racine, créé s'il n'existe pas). Les entrées sont ajoutées **en haut** du fichier (newest first).

ZenVibe ne commit jamais :
- Les fichiers WIP cassés (signalés à l'utilisateur)
- Les fichiers qui ressemblent à des secrets : `.env*`, `*.key`, `*.pem`, `*.pfx`, `*.p12`, `id_rsa*`, `credentials*`, `secrets*`, `.npmrc`

ZenVibe ne fait jamais `git push --force` ni `--no-verify`.

---

## Architecture

```
zen/  (install dir; source dir s'appelle zenvibe/)
├── .claude-plugin/plugin.json          manifeste CC (name: "zen")
├── .mcp.json                           MCP server pour CC CLI
├── commands/
│   ├── zenpause.md                     /zenpause
│   ├── zenresume.md                    /zenresume
│   └── zencompact.md                   /zencompact
├── hooks/
│   ├── hooks.json                      PreCompact + SessionStart
│   ├── pre-compact-prompt.md
│   ├── session-start-prompt.md
│   └── scripts/
│       └── session-start-briefing.py
├── mcp/
│   └── server.py                       MCP server (PEP 723, uv run --script)
└── docs/
    └── web-project.md                  system prompt claude.ai Project
```

---

## Licence

MIT
