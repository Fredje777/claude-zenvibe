---
name: resume
description: Réétablit le contexte après une pause ou une compaction. Lit docs/JOURNAL.md en entier, lit CLAUDE.md pour les conventions du projet, vérifie l'état Git, résume où en sont les choses, propose une prochaine action concrète et attend le feu vert explicite avant de toucher au code.
argument-hint: ""
allowed-tools:
  - Bash
  - Read
---

L'utilisateur reprend après une pause ou après une compaction de la conversation. Réétablis le contexte **avant de faire quoi que ce soit d'autre**.

## Workflow

### 1. Lire le journal en entier

- Essaie `docs/JOURNAL.md`. Si absent, essaie `JOURNAL.md` à la racine.
- Si aucun n'existe, dis : « Pas de JOURNAL trouvé. Tu veux qu'on en démarre un, ou tu préfères me briefer à l'oral ? » — puis stoppe et attends.
- Lis le journal **entièrement**. La dernière entrée prime, mais les précédentes portent des décisions différées, des refactos, du contexte encore actif.

### 2. Lire les conventions du projet

Lis `CLAUDE.md` à la racine s'il existe. Note les conventions sur les commits, le nommage, la sécurité, les validations, les tests — elles guident tout ce que tu fais cette session. Si plusieurs `CLAUDE.md` existent en sous-dossiers, lis celui le plus proche de la zone de travail mentionnée dans le journal.

### 3. Vérifier l'état Git réel

Lance, en parallèle :
- `git status`
- `git log -5 --oneline`
- `git branch --show-current`

Compare avec la section "Git" de la dernière entrée du journal. Si ça diverge (nouveaux commits, modifs non commitées non prévues, branche différente), signale-le dans ton résumé.

### 4. Produire un briefing compact

Sors exactement cette structure, remplie depuis ce que tu as lu :

```
Repris depuis docs/JOURNAL.md (entrée du <date heure>)

Tu étais sur : <tâche en cours>
Fait depuis la pause : <commits visibles depuis la pause, ou "rien">
Reste sur cette tâche : <points non terminés>
Prochaine action proposée : <1 phrase concrète, actionnable>

Points d'attention notés à la pause :
- ...

Conventions actives (CLAUDE.md) : <2-3 puces si pertinent pour la prochaine action>

Je reprends ? (oui / non / autre direction)
```

Reste sous 25 lignes. L'utilisateur veut du contexte, pas une re-narration du journal.

### 5. Attendre un go explicite

**Ne pas** éditer de fichiers, lancer de commandes mutantes, ni démarrer l'action proposée tant que l'utilisateur n'a pas explicitement confirmé ("oui", "go", "vas-y", "ok", "yes" — n'importe quel assentiment clair).

- Si l'utilisateur redirige ("non, fais plutôt X"), pivote immédiatement — le contexte du journal est dans ta tête, tu peux agir sur la nouvelle direction sans relire.
- Si l'utilisateur pose une question d'éclaircissement d'abord, réponds depuis le journal, puis redemande le go.

## Règles

- Read-only pendant la reprise. Pas d'édits, pas de commits, pas de migrations, rien de mutant tant que l'utilisateur n'a pas dit go.
- Si le journal est long, lis-le quand même en entier. Le contexte prime sur l'économie de tokens ici.
- Adapte la langue du briefing à celle du journal (français si le journal est en français).
- Sois honnête si le journal est lacunaire, contradictoire, ou ne couvre pas ce que l'utilisateur demande — dis-le et pose la question.
