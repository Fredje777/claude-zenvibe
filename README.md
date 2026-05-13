# ZenVibe

Pauses, reprises et compactages propres pour les sessions Claude Code.

ZenVibe gère les trois moments où une session Claude Code perd habituellement son contexte :

- **Pause** — tu t'arrêtes pour quelques heures et tu veux pouvoir reprendre proprement.
- **Reprise** — tu reviens et tu veux te remettre en contexte sans relire tout l'historique.
- **Compaction** — la conversation se compacte (manuellement ou automatiquement) et tu veux préserver le fil.

Le principe est simple : **`docs/JOURNAL.md` est la source unique de vérité**. ZenVibe l'écrit, le lit, et utilise Git comme filet de sécurité.

---

## Composants

### Skills (commandes slash)

| Commande | Quand | Action |
|---|---|---|
| `/zenvibe:pause [note]` | Tu pars pour quelques heures | Commit + push + entrée détaillée dans `docs/JOURNAL.md` (sprint, décisions, questions ouvertes, points d'attention) |
| `/zenvibe:resume` | Tu reviens d'une pause ou d'une compaction | Lit le JOURNAL + `CLAUDE.md`, résume l'état, propose la prochaine action, attend ton feu vert |
| `/zenvibe:compact` | Tu veux compacter consciemment | Checkpoint léger (commit + push + journal session) puis sort la commande `/compact <instructions>` prête à coller |

### Hook

| Événement | Action |
|---|---|
| `PreCompact` | Avant toute compaction (manuelle ou auto), Claude reçoit l'instruction de faire un checkpoint propre : commit, JOURNAL.md, push. Filet de sécurité si tu oublies de lancer `/zenvibe:compact` à temps. |

---

## Installation

Dans Claude Code, utilise la commande `/plugin` pour gérer les plugins.

### Depuis ce dépôt (local)

```
/plugin install /chemin/vers/zenvibe
```

### Depuis un dépôt git (une fois publié)

```
/plugin install https://github.com/<user>/zenvibe
```

Une fois installé, les commandes `/zenvibe:pause`, `/zenvibe:resume` et `/zenvibe:compact` apparaissent dans `/help`, et le hook `PreCompact` se déclenche automatiquement à chaque compaction.

---

## Configuration par projet (optionnel)

Tu peux créer un fichier `.claude/zenvibe.md` à la racine d'un projet pour personnaliser les instructions de compaction propres à ce projet. Si absent, ZenVibe utilise un template générique.

Exemple `.claude/zenvibe.md` :

```markdown
Garde en détail : les conventions de commits du repo, l'état du Sprint courant,
le schéma DB en cours d'évolution, les choix sur les prompts LLM, et toute
question ouverte. Résume brièvement les tâtonnements de code.
```

---

## Conventions

ZenVibe écrit toujours dans `docs/JOURNAL.md` (fallback : `JOURNAL.md` à la racine, créé s'il n'existe pas). Les entrées sont ajoutées **en haut** du fichier (newest first).

ZenVibe ne commite jamais :
- Les fichiers WIP cassés (signalés à l'utilisateur)
- Les fichiers qui ressemblent à des secrets (`.env`, `*.key`, `credentials*`)

ZenVibe ne fait jamais `git push --force` ni `--no-verify`.

---

## Licence

MIT
