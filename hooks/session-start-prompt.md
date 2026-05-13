Un fichier `JOURNAL.md` existe dans ce projet (`docs/JOURNAL.md` ou `JOURNAL.md` racine) et a été modifié récemment. L'utilisateur a probablement quitté une session de travail il y a peu.

Au **premier** message de l'utilisateur dans cette session :

- Si sa demande est exactement `/zen-resume` → ignore cette consigne, le skill se charge déjà du briefing complet.
- Sinon, **avant** de répondre à sa demande, lis uniquement la dernière entrée du JOURNAL (la première du fichier — newest first) et préfixe ta réponse par un mini-briefing de 3-4 lignes maximum :

```
👋 Dernière entrée du JOURNAL : <date> — <type: Pause/Compact/autre>.
Tu en étais à : <tâche en cours ou prochaine étape, 1 phrase>.
Briefing complet : `/zen-resume`
```

Puis enchaîne avec ta réponse à la demande utilisateur dans le même message.

**Règles** :

- Lis **uniquement** la dernière entrée du JOURNAL. Pas de `git status`, pas de `CLAUDE.md` — ces lectures appartiennent à `/zen-resume`.
- Si le JOURNAL est vide, illisible, ou si tu n'arrives pas à identifier une entrée datée → ne dis rien sur le briefing et démarre normalement.
- Le mini-briefing est un *teaser*, pas un substitut à `/zen-resume`. Ne le développe pas.
- Ne propose pas spontanément de reprendre la tâche — laisse l'utilisateur conduire. S'il veut reprendre, il lancera `/zen-resume`.
- Adapte la langue du briefing à celle du JOURNAL.
