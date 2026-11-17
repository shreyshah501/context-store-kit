# Enforcement for models without hooks

Claude Code has hooks: a `Stop` hook can block a session from ending
until it logs (see `docs/hard-enforcement.md`). Most other assistants
don't. For them the standing instruction in `AGENTS.md` is only a
request — and a request fades. In real use, a model with only the
instruction went from logging every session to logging nothing for over
a week, with no error and no warning. Sessions just end when the user
stops replying; there is no end-of-session moment that forces the
write-back.

The weekly distill does not save you here. It only promotes log entries
that exist. If nothing was logged, there is nothing to distill — the
store quietly goes stale while every job reports success.

## The pattern: a scheduled write-back

Don't rely on per-session memory. Run a **recurring write-back job**
(nightly is the right cadence) whose only task is to catch up the store.
Any assistant with a scheduled-task / recurring-agent feature can do
this; the job spec below is written to be pasted into one.

The job, every night:

1. **Review the day.** Look back over the day's sessions in every chat
   and project since the last log entry. Identify substantive work:
   a decision made, an artifact built, a plan changed, a fact learned
   that a future session would need.
2. **Log it.** For each substantive session, append one entry via
   `tools/context.py log "<what changed / decisions / what's next>"
   --project <slug>`. One entry per session, not one per message.
   Skip routine chatter. Never log secrets.
3. **Push.** Commit and push so the shared copy moves. If the
   assistant's working copy has no remote, push through whatever
   connector or API it has — and if it cannot push at all, it must
   say so plainly instead of silently staying local. A local-only
   commit is not a write-back.
4. **Staleness check.** If there has been substantive work and no log
   entry for more than a day, say so in the job's report. Silence is
   the failure mode; the job's job is to notice it.

## Reconcile before you write

Other agents write to the same store. Before appending, pull or
otherwise fetch the current remote head and merge it into the working
copy. Logs are append-only: never overwrite another agent's entries,
never rewrite a log file's history — add your entries alongside theirs.
If the remote has moved and you can't merge cleanly, stop and flag it
to the user rather than pushing over someone else's work.

## The job spec

Paste this into your assistant's scheduled-task setup, filling in the
paths and cadence it asks for. Run it nightly, after the user's day is
done.

```
Nightly context-store write-back.

Store: <PATH-TO-REPO> (private git repo; remote named origin if present).

Every run:
1. Read the store's log/ directory. Note the date and time of the
   newest entry.
2. Review the user's sessions since that entry, across all chats and
   projects. Identify substantive work: decisions made, artifacts
   built or changed, plans started/changed/cancelled, facts a future
   session would need.
3. For each substantive session, append one log entry with:
   python3 <PATH-TO-REPO>/tools/context.py log "<what changed /
   decisions / what's next>" --project <slug>
   Skip routine chatter. Never log secrets (passwords, keys, tokens).
4. Before pushing, reconcile with the remote: pull the latest head
   (or fetch and merge it) so no other agent's entries are lost.
   Logs are append-only — add entries, never overwrite.
5. Commit and push. If this machine cannot push, report that
   explicitly; a local-only commit does not count as done.
6. Report briefly: how many entries were written, or "nothing
   substantive today" if there was none. If substantive work
   happened and no entry could be written, say so — do not stay
   silent.

Do not edit profile.md, goals.md, decisions.md, or projects/*.md in
this job. Promotion to the standing files is the weekly distill's
work, not this job's.
```

## If your assistant has no scheduler at all

- **End-of-day prompt.** Make it a habit: once a day, ask your
  assistant "log today to the context store." One prompt, one
  minute, same entries as the job would write.
- **Make the distill report staleness.** The weekly distill job
  should state the date of the newest log entry as its first finding.
  If the newest entry is a week old, that is the finding — the store
  is stale, and the distill should say so instead of quietly
  promoting nothing.
- **Chat AIs** (no file access, no scheduler) still use the packet
  flow in `ANY-AI-INSTRUCTIONS.md`: paste the packet in, get a
  formatted log entry back, and hand it to an agent with repo access
  to commit.
