---
name: zen-compact
description: Prépare une compaction manuelle propre. Commit + push de ce qui est commitable, écrit une entrée session-focused dans docs/JOURNAL.md (ce qui a été fait, décisions, fichiers touchés, prochaine étape), puis sort la commande /compact avec les instructions adaptées au projet prête à coller.
argument-hint: ""
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

L'utilisateur veut compacter la conversation. Fais un checkpoint propre d'abord, puis sors-lui la commande `/compact` à coller.

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

Cette entrée est **focalisée session**, pas un handoff complet comme `/zen-pause` :

```markdown
## YYYY-MM-DD HH:MM — Compact

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

Garde ça serré. Le but est de préserver ce qui serait perdu dans la compaction, pas d'écrire une revue de sprint.

### 3. Construire les instructions pour `/compact`

Cherche `.claude/zen.md` à la racine du projet. S'il existe, utilise son contenu **tel quel** comme instructions de compaction — ça permet à chaque projet de définir ses propres priorités.

S'il est absent, utilise ce template générique :

```
Garde en détail : les conventions du projet (commits, sécurité données, validations obligatoires), l'état d'avancement courant, les décisions techniques prises sur l'architecture et l'API, et toute question ouverte non résolue. Tu peux résumer brièvement les itérations de code et les tâtonnements.
```

### 4. Confirmer et sortir la commande

Sors exactement :

```
Checkpoint OK.
✓ Commit : <sha> <message>   (ou : "rien à committer")
✓ Push : <branche> → <remote>   (ou : "pas de remote")
✓ Journal : docs/JOURNAL.md

Pour compacter maintenant, copie-colle :

/compact <instructions>
```

Remplace `<instructions>` par le texte réel de l'étape 3, sur une seule ligne (réduis tout saut de ligne interne à un espace simple) pour qu'il soit collable directement.

## Règles

- **Ne lance jamais `/compact` toi-même.** Sors uniquement la commande pour que l'utilisateur la lance. `/compact` est une action UI que seul l'utilisateur peut déclencher.
- Ne commit jamais de WIP cassé — alerte plutôt et laisse les fichiers en place.
- Si `git status` est propre et que le journal couvre déjà l'état courant, saute proprement l'étape 1 et produis quand même l'étape 4.
- Le fichier `.claude/zen.md` custom est optionnel par projet. Ne le crée pas automatiquement — lis-le seulement s'il existe.
