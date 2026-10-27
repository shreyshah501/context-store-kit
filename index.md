# Context store — index

Read this first. It is the manifest: what each file holds and when to
read it.

| File | Holds | Read it when |
|---|---|---|
| `profile.md` | Who the user is: identity, context, preferences | Every session |
| `goals.md` | Durable goals and what progress looks like | Every session |
| `decisions.md` | Standing decisions and the reasoning behind them | Every session |
| `projects/<slug>.md` | Per-project state: what's true, what's next | When working on that project |
| `log/YYYY-MM-DD.md` | Append-only daily session logs (the audit trail) | When you need recent history |

Standing files carry YAML frontmatter (`updated`, `status`, `tags`).
Weekly, log entries are distilled into the standing files; superseded
text is marked `Revoked YYYY-MM-DD: <reason>` in place, never deleted.
