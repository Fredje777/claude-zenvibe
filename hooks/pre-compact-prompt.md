Une compaction de la conversation est sur le point d'avoir lieu (manuelle via `/compact`, ou automatique parce que le contexte est plein).

Avant qu'elle ne se produise, fais un checkpoint propre :

1. Lance `git status`. Si des fichiers sont en état commitable, commit avec un message qui résume ce qu'on vient de faire dans la session. Suis la convention de commits du projet (regarde `git log -5 --oneline`). Ne commite jamais de WIP cassé ni de fichier qui ressemble à un secret (`.env`, `*.key`, `credentials*`).

2. Ouvre ou crée `docs/JOURNAL.md` (fallback : `JOURNAL.md` à la racine) et ajoute une entrée datée **en haut** du fichier :

   ```markdown
   ## YYYY-MM-DD HH:MM — Compact (auto)

   ### Fait dans cette session
   - ...

   ### Décisions techniques
   - ...

   ### Fichiers touchés
   - ...

   ### Prochaine étape claire
   - ... (1 ligne actionnable)
   ```

3. Push si un remote est configuré (`git push`). Ne force jamais, ne saute jamais les hooks.

4. Confirme à l'utilisateur en une ligne : `Checkpoint OK avant compact.`

Si rien n'est à committer ou journaliser (conversation très courte, ou checkpoint déjà fait juste avant), dis-le simplement (`Rien à checkpointer.`) et laisse la compaction se faire.

Une fois ce checkpoint terminé, la compaction technique va suivre. Au prochain message utilisateur après compaction, si tu as perdu le contexte, lis `docs/JOURNAL.md` et `CLAUDE.md` pour te réorienter — ou suggère à l'utilisateur de lancer `/zenresume`.
