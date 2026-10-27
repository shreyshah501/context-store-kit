# Context Store — explain yourself once

**The problem.** Every AI you work with starts from zero. You re-explain
who you are, what you're working on, what you decided last week, and why
— to your coding agent, your chat assistant, your phone assistant, over
and over. The context lives in your head and in scattered chat histories
that no other tool can read.

**The solution.** Keep your context in one place that *you* own: a plain
git repo of Markdown files — who you are, your goals, your standing
decisions, per-project notes, and a daily session log. One standing
instruction tells every agent: *read the store when you start, write back
when you finish.* Explain yourself once; every agent picks it up from
there.

This repo is the kit: the file layout, a small stdlib-only CLI
(`tools/context.py`), the standing instruction (`AGENTS.md`), and the
setup protocol below. It contains **no one's personal data** — your data
lives in your own private copy.

---

## How it works

Three pieces, nothing else:

1. **The store** — a git repo of Markdown:
   - `index.md` — the manifest; agents read it first and open only what
     they need (progressive disclosure)
   - `profile.md`, `goals.md`, `decisions.md` — the curated standing files
   - `projects/<slug>.md` — one note per project
   - `log/YYYY-MM-DD.md` — append-only daily session logs (the audit trail)
2. **The standing instruction** (`AGENTS.md`) — pasted once into your
   agent's global config: *run `context.py start` at session start, run
   `context.py log` at session end.*
3. **`tools/context.py`** — the mechanics: `init`, `start`, `packet`,
   `log`, `status`. Python 3 stdlib only. No server, no MCP, no database,
   no account, no cost.

Works with Claude Code and any `AGENTS.md`-aware tool directly, and with
chat AIs (which can't read files) through the packet flow in
`ANY-AI-INSTRUCTIONS.md`. Optional Claude Code hooks make read/write
enforcement automatic — see `docs/hard-enforcement.md`.

Weekly, the logs are distilled into the standing files; anything
superseded is marked `Revoked YYYY-MM-DD: <reason>` in place rather than
deleted, so the store remembers what changed and when.

---

## Quick start (humans)

> ⚠️ **Your copy must be private.** This template is public; the store
> you fill with your life must not be. On GitHub, **do not fork this
> repo** — forks of public repos stay public. Use **"Use this template"**
> and create your copy as **Private** (or clone it and push to a fresh
> private repo). Same on any other git host: your copy is private,
> always.

1. Click **Use this template → Create a new repository**, visibility
   **Private**. (No template button? `git clone` this repo, delete its
   `.git`, and push the files to your own new private repo.)
2. Clone your private copy and run setup:

   ```bash
   git clone <your-private-repo-url> context-store
   cd context-store
   ./setup.sh --name "Your Name" --timezone "Europe/London"
   ```

3. Paste the below-the-line section of `AGENTS.md` into your agent's
   global config (Claude Code: `~/.claude/CLAUDE.md`), replacing
   `<PATH-TO-REPO>` with your clone's path.
4. Start a session. Your agent loads the store, interviews you to fill
   in `profile.md` / `goals.md` / `decisions.md` (or you edit them by
   hand), and logs its first entry when it finishes.

That's it. Every later session on any connected agent starts with your
context already loaded and adds to the same log.

---

## For agents: set this up for your user

*If you are an AI agent reading this because your user pointed you at
this repo and asked for "a context store like this": the steps below are
your complete instructions. The user should not need to do anything by
hand except the one step marked HUMAN (creating the private repo, if
their git host requires an account holder for that).*

**Goal:** the user ends with a private git repo (their store) that you —
and their other agents — read at session start and write to at session
end, synced through a remote named `origin`.

1. **Get the kit.** Clone this repo, or download it, to a scratch
   location. You will copy its *files* into the user's new store — never
   put the user's data in a copy of this public repo itself.
2. **Create the user's store (HUMAN step if you can't create repos).**
   The user creates a new **private** repository on their git host
   (any name, e.g. `context-store`). Warn them explicitly: a fork of a
   public repo is public — they must use "Use this template" with
   Private visibility, or a fresh private repo. Clone their private repo
   to the user's machine at a stable path (e.g. `~/context-store`) and
   remember that path.
3. **Copy the kit in.** Copy everything from this repo except `.git`
   into the user's clone. Commit it: `Initial context store kit`.
4. **Initialize.** Run:
   `python3 tools/context.py init --name "<user's name>" --timezone "<their IANA timezone>"`
   This writes `store.config.json` and seeds any missing standing files.
5. **Interview the user — briefly.** Ask for: who they are (name,
   location, work, household — whatever they're comfortable storing),
   their durable goals, and any standing decisions or preferences every
   agent should know. Write the answers into `profile.md`, `goals.md`,
   and `decisions.md`, keeping the YAML frontmatter and updating its
   `updated:` date. Commit with a clear message. This is a deliberate
   edit, separate from routine log write-backs.
6. **Install the standing instruction.** Append the below-the-line
   section of the store's `AGENTS.md` to the user's global config for
   each agent they use (Claude Code: `~/.claude/CLAUDE.md`), replacing
   `<PATH-TO-REPO>` with the store path from step 2. Preserve anything
   already in those files.
7. **Offer hard enforcement (optional).** If the user uses Claude Code,
   show them `docs/hard-enforcement.md` — SessionStart/Stop hooks that
   make loading and write-back automatic. Install only if they say yes;
   the blurb in that file is written for you to execute.
8. **Verify, don't assert.** Run `python3 tools/context.py status`
   (shows the repo, owner, remote), then `... start` and show the user
   their own profile coming back. Log this setup session:
   `python3 tools/context.py log "Context store set up: kit copied, profile/goals/decisions seeded, standing instruction installed. Next: first real session."`
   Confirm the commit was pushed (`status` shows `origin present`;
   `log` prints `pushed to origin`).
9. **Leave it working.** Tell the user, in plain words: where their
   store lives, that it's private, that any agent they install the
   instruction on will now load it automatically, and that chat AIs can
   join via `ANY-AI-INSTRUCTIONS.md` (packet flow). Mention the weekly
   distill-and-revoke habit from `AGENTS.md`.

**Rules that apply to you from now on** (they're also in `AGENTS.md`):
read at session start, log at session end, never edit the standing files
as part of a routine write-back, never move the store's contents
anywhere the user hasn't asked, and keep personal and work context in
separate stores.

---

## Daily use

```bash
python3 tools/context.py start [--project <slug>]   # load context
python3 tools/context.py packet [--project <slug>]  # packet for a chat AI
python3 tools/context.py log "<what changed / decided / next>" [--project <slug>]
python3 tools/context.py status
```

**Phone writes:** any agent app that can reach the repo can run `log`.
With a chat AI, the packet flow (`ANY-AI-INSTRUCTIONS.md`) returns a
formatted entry you paste or forward to an agent with repo access — it
lands in the same store.

## Privacy

- This template is public and contains no personal data.
- **Your copy holds your life story. Keep it private**, review what you
  put in it, and never commit secrets (passwords, keys, tokens) to it —
  it's a context store, not a vault.
- Git history is forever-ish: the `Revoked …` convention marks
  superseded facts instead of rewriting history.

## License

MIT — see `LICENSE`. Use it, adapt it, share it.
