A `JOURNAL.md` file exists in this project (`docs/JOURNAL.md` or root `JOURNAL.md`) and was modified recently. The user has probably stepped away from a working session not long ago.

On the **first** user message in this session:

- If the request is exactly `/zenresume` → ignore this guidance; the command handles the full briefing itself.
- Otherwise, **before** responding to the request, read only the latest entry of the journal (the first one in the file — newest first) and prefix your response with a mini-briefing of at most 3–4 lines:

```
👋 Last JOURNAL entry: <date> — <type: Pause/Checkpoint/other>.
You were on: <current task or next step, one sentence>.
Full briefing: `/zenresume`
```

Then continue with your response to the user's request in the same message.

**Rules:**

- Read **only** the latest journal entry. No `git status`, no `CLAUDE.md` — those reads belong to `/zenresume`.
- If the journal is empty, unreadable, or you cannot identify a dated entry → say nothing about the briefing and start normally.
- The mini-briefing is a *teaser*, not a substitute for `/zenresume`. Do not expand it.
- Do not spontaneously offer to resume the task — let the user drive. If they want to resume, they will run `/zenresume`.
- Match the language of the journal in your briefing (write French if the journal is in French).
