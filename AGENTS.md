# Standing instruction — shared context store (AGENTS.md)

This file is the store's standing instruction. In this repo it is named
`AGENTS.md` (the cross-tool standard); `CLAUDE.md` sits alongside it so
Claude Code finds it too. During setup, paste everything below the line
into your agent's global config — for Claude Code that's
`~/.claude/CLAUDE.md` — replacing `<PATH-TO-REPO>` with the absolute path
of this repo on your machine (e.g. `/Users/you/context-store`).

---

## Shared context store (read first, write back last)

I keep a personal context store at `<PATH-TO-REPO>` — a git repo of plain
Markdown (`profile.md`, `goals.md`, `decisions.md`, `projects/*.md`,
`log/YYYY-MM-DD.md`). It exists so I explain myself once and every
assistant picks it up. Use it in every session:

**At session start, before doing any work**, load the store:

```
python3 <PATH-TO-REPO>/tools/context.py start --project <current-project-slug>
```

(Use the slug of the project we're working on; omit `--project` if none
applies.) If the repo or the script isn't present on this machine, fall
back to reading `profile.md`, `goals.md`, `decisions.md`, and the
relevant `projects/<slug>.md` directly from wherever the store is cloned.

**At session end**, write back a summary with:

```
python3 <PATH-TO-REPO>/tools/context.py log "<summary>" --project <current-project-slug>
```

The summary must cover: (1) what changed — what was built, fixed, or
learned; (2) decisions I made, with brief reasoning; (3) what's next.
The script appends it to today's log and commits it (and pushes, if a
remote named `origin` exists).

**Rules:**

- Never edit `profile.md`, `goals.md`, `decisions.md`, or `projects/*.md`
  as part of a routine write-back. The log is append-only. If a session
  produces a new standing decision, note it in the log entry; promote it
  to `decisions.md` only as a separate, deliberate change that you flag
  to me.
- This store is **private**. Never copy, sync, or paste its contents
  anywhere I have not asked you to. Keep personal and work context in
  separate stores; never mix them.

**Distill & revoke (weekly):**

- Once a week, the week's log entries get distilled into the curated
  files (`profile.md`, `goals.md`, `decisions.md`, `projects/*.md`):
  durable facts and decisions are promoted; one-off detail stays in the
  logs.
- When a newer fact or decision supersedes an older one, mark the old
  text in place as `Revoked YYYY-MM-DD: <reason>` — never silently
  delete or overwrite it. The logs remain the audit trail of what was
  believed when.
