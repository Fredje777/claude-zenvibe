## 2026-05-14 11:32 — Pause

> Note de pause: pause après publication v0.1.0 sur GitHub.

### Tâches terminées (itération en cours)
- Brainstorming complet (spec finale `docs/superpowers/specs/2026-05-13-public-release-design.md`, 11 sections, 3 rounds d'approbation)
- Plan d'implémentation détaillé (`docs/superpowers/plans/2026-05-13-public-release.md`, 15 phases / 38 tasks / 128 steps)
- Phase 0 → 14 exécutée en mode subagent-driven (30 commits sur `release/v0.1`, mergée dans `main` en `95e5ddf` avec `--no-ff`)
- Traduction complète vers l'anglais : 3 commands (`zenpause`/`zenresume`/`zencheckpoint`), 2 hooks (`pre-compact-prompt.md`, `session-start-prompt.md`), MCP server (`mcp/server.py` module docstring + 5 warning strings + suppression de `GENERIC_COMPACT_INSTRUCTIONS`), `docs/web-project.md`, `commands/*.md` frontmatter descriptions, `plugin.json` description
- Smart bilingual implémenté côté MCP : `MESSAGES` dict EN/FR (18 clés × 2 langues) + helper `_t(key, language)` + paramètre `language: Literal["en", "fr"] = "en"` sur `zenvibe_pause` et `zenvibe_checkpoint` (pas sur `zenvibe_resume` qui retourne du contenu brut)
- Smart bilingual côté slash commands : règle "Output language" en tête de chaque body — détection via CLAUDE.md ou journal existant, défaut anglais
- `install.sh` créé (~310 lignes bash + Python inline) : preflight (git, python3, rsync, uv, `~/.claude/`, desktop app dir), confirmation gate, OS detection (macos/linux/windows/unknown), rsync copy, JSON safety (backup timestamped + atomic rewrite tmp→`os.replace` + parse validation), `register_plugin`, `enable_plugin`, `configure_desktop_mcp` (résout `uv` via `command -v`), `print_summary` per-surface. Flags : `--check`, `--cli`, `--yes`, `--help`. Idempotent.
- `uninstall.sh` symétrique avec les mêmes garanties JSON, jamais ne touche les JOURNAL.md utilisateur
- `LICENSE` (MIT 2026 Fred Fonteyne), `CHANGELOG.md` (Keep-a-Changelog, 0.1.0 entry)
- `README.md` réécrit complet (intro Draft D "Vibe-code with a safety net", 11 sections, ~170 lignes)
- `docs/INSTALL.md` complet (11 sections : prerequisites + path quick reference table macOS/Linux/Windows, macOS quick install, Linux quick install, Windows WSL + Git Bash, web Project setup, what install.sh does, manual fallback, verifying, troubleshooting 6 cases, uninstall, FAQ 6 questions)
- `scripts/sync-install.sh` supprimé (dossier `scripts/` retiré du repo)
- Suite de tests pytest locale : `tests/conftest.py` (fixtures `tmp_repo`, `fr_claude_md`, `en_claude_md`) + `tests/test_mcp_messages.py` (10 tests, dont parité des clés EN/FR + dispatch `_t()` + comportements `zenvibe_pause` et `zenvibe_checkpoint` en EN/FR) + `tests/test_session_start_briefing.py` (6 tests : silence sur `resume`/`clear`, silence sans journal, silence sur journal stale >14 jours, émission sur journal récent, silence sur stdin malformé)
- 16/16 tests passent en `uv run --with pytest --with mcp pytest tests/`
- `.gitignore` étendu (`*.backup-*`, `*.iml`, `.pytest_cache/` ajoutés ; `.idea/`, `__pycache__/`, `*.pyc` déjà présents)
- Repo publié sur GitHub : https://github.com/Fredje777/claude-zenvibe (public, MIT, tag `v0.1.0` poussé)
- Smoke test : `git clone` frais depuis le repo public + `./install.sh --check` → 6 preflight ✓, exit 0

### Tâche en cours
- (aucune — release shippée et publiée)

### Tâches restantes (par ordre)
1. **Vérification manuelle 13.3** : ouvrir un terminal, `cd` dans n'importe quel projet, `claude`, taper `/zen` → auto-complete sur les 3 commandes ; essayer `/zenpause test post-release` pour valider la sortie en conditions réelles
2. **Vérification manuelle 13.4** : quitter Claude.app complètement (Cmd+Q), relancer, demander en chat "what MCP tools are available?" → doit lister `zenvibe_pause`, `zenvibe_resume`, `zenvibe_checkpoint`
3. **Vérifier le rendu du README sur github.com** (`gh repo view Fredje777/claude-zenvibe --web`) — table de commandes, surface coverage, architecture tree doivent être lisibles
4. **Ouvrir 1-2 issues "good first issue"** sur le repo public pour amorcer l'engagement (ex. "PowerShell installer port", "Linux Claude desktop fallback", "Detect language from JOURNAL.md content not just file presence")
5. (optionnel, plus tard) v0.1.1 : ajouter une variable d'env `ZENVIBE_LANG=en|fr` pour forcer la langue (en plus de la détection auto)
6. (optionnel, plus tard) inscrire le repo dans le marketplace claude-plugins-official quand il sera plus mûr (1-2 itérations d'usage)

### Décisions techniques prises cette session
- **Plugin technique nommé `zenvibe`, displayName `ZenVibe`**, commandes `/zenpause` etc. (sans préfixe `:`) — pour avoir des commandes courtes facilement tapables sans confusion avec `/compact` ni `/help`
- **`/compact` jamais lancée par le plugin** : Claude Code l'exclut explicitement du tool `SlashCommand` (vérifié via context7 sur les docs CC officielles, changelog 1.0.123 mentionne SlashCommand mais `/compact` est dans la liste des exclus). `/zencheckpoint` est positionnée comme "checkpoint propre + invitation à compacter", pas "compacte pour moi"
- **Source de vérité unique : `docs/JOURNAL.md`** (fallback `JOURNAL.md` racine). Pas de fichier d'état séparé. Git comme filet de sécurité en-dessous.
- **Smart bilingual conservatif** : EN par défaut, FR uniquement sur signaux clairs (CLAUDE.md FR ou journal contient des entrées FR). Évite les faux positifs FR sur projets EN.
- **MCP tool `zenvibe_resume` ne prend pas `language`** car il retourne du contenu brut (journal_content, claude_md_content, git_status) — c'est Claude qui formate le briefing et choisit la langue
- **Installer en pure bash + Python inline pour la sécurité JSON** : pas de jq (dépendance externe), pas de sed (fragile sur JSON). Chaque mutation = read → modify → atomic rewrite via tmp+`os.replace` + validation parse. Backup timestamped avant chaque édition.
- **Installer cross-OS via `uname` switch** : macOS (full), Linux (CC CLI only, desktop skipped car pas d'app Claude sur Linux), Windows-Git-Bash (community best-effort), Windows-PowerShell (out of scope v0.1)
- **Tests pytest locaux seulement, pas de CI v0.1** : pragmatique, ajouter quand le repo aura des contributeurs
- **Repo publié simple (pas de marketplace.json)** : install par `git clone + ./install.sh`. Marketplace différé pour quand le plugin sera mûr.
- **Pas de sync-install.sh séparé** : `install.sh` est utilisé à la fois par les nouveaux users (premier install) et par Fred lui-même pour iterate (idempotent, fait des backups automatiquement)
- **`displayName: "ZenVibe"` ajouté en pari** : si CC honore le champ, ça affiche la casse correcte ("ZenVibe" vs "Zenvibe") ; sinon cosmétique inoffensif. À vérifier manuellement après restart desktop.

### Questions ouvertes
- L'app desktop affiche-t-elle bien "ZenVibe" (capital V) après ajout du `displayName` dans plugin.json, ou toujours "Zenvibe" ? (vérifier en 13.4)
- Le hook `SessionStart` se déclenche-t-il correctement avec `source=compact` post-compaction dans la pratique ? (testable mais demande de provoquer une compaction)
- Les utilisateurs vont-ils trouver l'auto-complete `/zen` ? Faut-il ajouter une mention explicite dans le SessionStart prompt ?
- Est-ce que la règle "smart bilingual" est trop conservative ? (peut-être qu'un projet 100% EN avec un README FR devrait switcher en FR)

### Git
- Branche : main
- Dernier commit : 95e5ddf release: v0.1.0 public release
- Tag : v0.1.0 (poussé sur origin)
- Remote : https://github.com/Fredje777/claude-zenvibe (public)

### Points d'attention pour la reprise
- **Avant tout test live** : nouvelle session terminal `claude` requise (la session courante a chargé l'ancienne version FR des command bodies — le `/zenvibe:zenpause` ci-dessus a été exécuté avec la version FR cached, pas la version EN nouvellement publiée)
- **Si l'app desktop ne charge pas le MCP renommé** après Cmd+Q + restart : vérifier `python3 -c "import json; print(json.load(open('$HOME/Library/Application Support/Claude/claude_desktop_config.json'))['mcpServers']['zenvibe'])"` — doit pointer vers `/Users/fred/.claude/plugins/zenvibe/mcp/server.py`
- **Backups JSON multiples** dans `~/.claude/plugins/` et `~/Library/Application Support/Claude/` (timestamps des différentes itérations d'aujourd'hui) — safe à nettoyer dans quelques jours
- **La branche `release/v0.1` n'a pas été supprimée** localement, on peut la garder ou faire `git branch -d release/v0.1` après confirmation que main contient bien tout
- **Pas de README sur le repo source GitHub si on regarde de l'extérieur** = ne contient PAS encore de demo GIF ni de screenshots — à ajouter en v0.1.1 quand t'auras des retours d'usage réels
- **Pas de CONTRIBUTING.md** délibérément (cf §9 spec out-of-scope) — à créer si le repo prend du trafic
