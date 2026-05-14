---
name: zencheckpoint
description: Sauvegarde l'état courant de la session SANS compacter — commit + push de ce qui est commitable, écrit une entrée session-focused dans docs/JOURNAL.md (ce qui a été fait, décisions, fichiers touchés, prochaine étape), puis confirme que la compaction est sûre. À utiliser comme bookmark mi-tâche, ou juste avant de taper /compact manuellement.
argument-hint: ""
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

L'utilisateur veut sauvegarder l'état actuel de la session sans détruire le contexte. Tu fais un checkpoint propre, puis tu lui confirmes qu'il peut compacter en sécurité s'il le souhaite.

**Important** : tu ne lances **jamais** `/compact` toi-même. Claude Code exclut explicitement `/compact` du tool `SlashCommand`. La compaction reste une action que l'utilisateur déclenche manuellement. Ton rôle ici est uniquement de sécuriser le contexte avant.

Le hook `PreCompact` fera de toute façon le même travail si l'utilisateur tape `/compact` sans avoir lancé ce skill — donc ce skill est essentiellement un *checkpoint à la demande*, utile aussi en milieu de tâche pour bookmarker sans compacter.

## Workflow

### 0. Vérifier que le répertoire est un repo git

Lance `git rev-parse --is-inside-work-tree`. Si ça échoue, saute l'étape 1 entièrement, écris uniquement l'entrée du journal, et mentionne "pas de repo git" dans la confirmation.

### 1. Commit + push des changements commitables

- `git status` et `git log -5 --oneline` d'abord.
- Stage les fichiers propres. Saute les WIP à moitié écrits (et préviens l'utilisateur — ne commit pas de code cassé).
- Commit avec un message significatif qui résume la session, en suivant la convention existante du projet.
- Push si un remote est configuré.

### 2. Mettre à jour le journal

Ajoute une nouvelle entrée en haut de `docs/JOURNAL.md` (ou `JOURNAL.md` à la racine). Crée `docs/JOURNAL.md` si aucun n'existe.

Cette entrée est **focalisée session**, plus courte qu'un handoff complet :

```markdown
## YYYY-MM-DD HH:MM — Checkpoint

### Fait dans cette session
- ...

### Décisions techniques
- ...

### Fichiers touchés
- path/to/file
- ...

### Prochaine étape claire
- ... (1 ligne actionnable)
```

Garde ça serré. Le but est de bookmarker l'état, pas d'écrire une revue de sprint.

### 3. Confirmer

Sors exactement ce bloc, ni plus, ni moins :

```
✓ Checkpoint
✓ Commit : <sha> <message>   (ou : "rien à committer")
✓ Push : <branche> → <remote>   (ou : "pas de remote")
✓ Journal : docs/JOURNAL.md

🧘 It's safe to compact now. Type /compact to proceed.
```

Si quelque chose a échoué (push refusé, journal non écrivable, WIP non commitable), liste-le explicitement à la place de la ligne `✓` correspondante, et **omets** la ligne finale `🧘 It's safe to compact` — le but étant justement de ne pas inviter à compacter quand le checkpoint n'est pas propre.

### 4. Custom instructions pour `/compact` (optionnel)

Si l'utilisateur veut des instructions custom au moment où il tapera `/compact`, il peut consulter `.claude/zenvibe.md` du projet (si présent) qui contient le texte recommandé. Tu **ne le lis pas** ici et tu ne l'affiches pas — ce fichier est juste là pour qu'il puisse copier-coller dans `/compact <texte>` quand il le décide.

## Règles

- **Ne lance jamais `/compact` toi-même.** C'est explicitement exclu du tool `SlashCommand` de Claude Code. L'utilisateur seul déclenche la compaction.
- Ne commit jamais de WIP cassé — alerte et laisse les fichiers en place.
- Ne commit jamais ce qui ressemble à un secret (`.env*`, `*.key`, `*.pem`, `credentials*`, etc.).
- Si `git status` est propre et que le journal couvre déjà l'état courant, dis-le franchement et émets quand même le message `🧘 It's safe to compact now`.
- Le hook `PreCompact` refera le même travail si l'utilisateur tape `/compact` ensuite — c'est idempotent et sans danger.
