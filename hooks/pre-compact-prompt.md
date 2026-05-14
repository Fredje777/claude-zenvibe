A compaction of the conversation is about to happen (either user-triggered via `/compact`, or automatic because the context is full).

Before it proceeds, make a clean checkpoint:

1. Run `git status`. If files are in a committable state, commit them with a message summarizing what was done in this session. Follow the project's commit convention (check `git log -5 --oneline`). Never commit broken WIP, and never commit anything that looks like a secret (`.env*`, `*.key`, `credentials*`, etc.).

2. Open or create `docs/JOURNAL.md` (fallback: `JOURNAL.md` at root) and prepend a dated entry **at the top** of the file:

   ```markdown
   ## YYYY-MM-DD HH:MM — Checkpoint (auto)

   ### Done this session
   - ...

   ### Technical decisions
   - ...

   ### Files touched
   - ...

   ### Clear next step
   - ... (one actionable line)
   ```

   **Output language:** Match the project. If `CLAUDE.md` is in French OR the existing journal contains French entries, write the new entry in French. Otherwise English.

3. Push if a remote is configured (`git push`). Never force, never skip hooks.

4. Confirm to the user in one line: `Checkpoint OK before compact.`

If nothing is committable or worth journaling (very short conversation, or checkpoint already done just before), say so plainly (`Nothing to checkpoint.`) and let the compaction proceed.

Once this checkpoint is done, the technical compaction will follow. On the next user message after compaction, if you have lost context, read `docs/JOURNAL.md` and `CLAUDE.md` to reorient — or suggest the user run `/zenresume`.
