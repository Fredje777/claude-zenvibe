---
name: zen-pause
description: Sauvegarde l'état de la session avant une absence de plusieurs heures. Commit + push de ce qui est commitable, écrit une entrée détaillée dans docs/JOURNAL.md (tâches terminées, tâche en cours, restant à faire, décisions, questions ouvertes, état Git), signale les points d'attention pour la reprise.
argument-hint: "[note optionnelle: ex. 'pause déjeuner, reprendre par l'auth JWT']"
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

Tu produis un handoff complet pour que l'utilisateur (ou toi-même) puisse reprendre proprement plusieurs heures plus tard.

## Workflow

### 0. Vérifier que le répertoire est un repo git

Lance `git rev-parse --is-inside-work-tree`. Si ça échoue, le projet n'est pas sous git : saute l'étape 1 et la section "Git" de l'étape 3, écris uniquement l'entrée du journal, et mentionne dans la confirmation qu'aucun checkpoint git n'a été fait.

### 1. Commit + push de tout ce qui est commitable

- Lance `git status` et `git diff --stat` pour voir ce qui a changé.
- Lance `git log -10 --oneline` pour apprendre la convention de messages de commit du projet.
- Pour chaque fichier modifié : s'il est dans un état stable, inclus-le dans le commit. S'il est clairement WIP / à moitié écrit (syntaxe cassée, stubs, refacto partiel), **ne le commit pas** — signale-le à l'étape 3.
- Stage les fichiers propres et commit avec un message qui **résume ce qui a vraiment été fait dans la session**, pas "WIP".
- Si un remote est configuré, `git push`. Si le push échoue par manque d'upstream, configure-le (`git push -u origin <branche>`) et retente. Jamais de `--force` ni `--no-verify`.

### 2. Localiser (ou créer) le journal

Cherche dans cet ordre :

1. `docs/JOURNAL.md`
2. `JOURNAL.md` à la racine du repo
3. Si aucun n'existe, crée `docs/JOURNAL.md` (`mkdir -p docs` d'abord).

### 3. Ajouter une nouvelle entrée en haut du journal

La nouvelle entrée va **en haut** (newest first). Utilise cette structure — adapte les titres à la langue du journal s'il en a déjà une :

```markdown
## YYYY-MM-DD HH:MM — Pause

> Note de pause: <texte fourni en argument, si présent>

### Tâches terminées (itération en cours)
- ...

### Tâche en cours
- ... (état précis : ce qui est fait, ce qui reste à faire dessus)

### Tâches restantes (par ordre)
1. ...
2. ...

### Décisions techniques prises cette session
- ...

### Questions ouvertes
- ...

### Git
- Branche : <branche>
- Dernier commit : <sha court> <message>

### Points d'attention pour la reprise
- (optionnel — refactos à faire, fichiers WIP non commités, tests à écrire, code smells)
```

Sois spécifique. Chemins de fichiers, noms de fonctions, *pourquoi* derrière chaque décision. Future-toi doit pouvoir agir sans relire toute la conversation. Évite les phrases génériques type "amélioration des perfs" — dis *quoi* et *où*.

### 4. Confirmer

Sors exactement un bloc court — pas de préambule, pas de récap du contenu du journal :

```
État sauvegardé.
✓ Commit : <sha court> <message>
✓ Push : <branche> → <remote>   (ou : "rien à committer")
✓ Journal : docs/JOURNAL.md

Bonne pause. Au retour : /zen-resume
```

Si quelque chose a échoué (push refusé, journal non écrivable, fichiers WIP laissés), dis-le explicitement avec les fichiers concernés. Ne prétends jamais une réussite qui n'a pas eu lieu.

## Règles

- Ne commit jamais de fichiers qui ressemblent à des secrets : `.env*`, `*.key`, `*.pem`, `*.pfx`, `*.p12`, `id_rsa*`, `credentials*`, `secrets*`, `.npmrc` avec tokens. Fais confiance au `.gitignore` d'abord, mais si quelque chose de suspect arrive en staging, alerte et unstage.
- Jamais de force-push ni de `--no-verify`.
- Si `git status` est propre ET que rien de significatif ne s'est passé, tu peux écrire une entrée minimale ("session sans changements") et sortir. Ne fabrique pas du travail.
- Adapte la langue du journal. Français par défaut si le projet est en français (regarde CLAUDE.md ou les commits récents).
- Le journal est l'unique source de vérité. Ne crée pas de fichier d'état séparé.
