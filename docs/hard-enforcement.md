# Hard enforcement: Claude Code hooks

The standing instruction in `AGENTS.md` is soft — a model can skip it.
Hooks are the hard version: commands the Claude Code harness itself runs
at fixed points in a session. The model cannot skip them.

- **Read side — `SessionStart` hook.** Runs `tools/context.py start` at
  every session start and injects the output into the session's context.
  Every new session starts already loaded with this store.
- **Write side — `Stop` hook.** When a session tries to end, a check
  script verifies that today's log has a fresh entry. If it doesn't, the
  hook blocks the stop and sends the model back to log first. A session
  cannot finish without the write-back.
- **Boundary guard.** Both hooks stay silent when the session's working
  directory is a work directory. Personal context is never injected into
  work sessions.

Hooks are a Claude Code (CLI) feature. Chat AIs have no hook system; they
use the packet flow in `ANY-AI-INSTRUCTIONS.md` instead.

## The setup blurb

Paste the block below to Claude Code on your machine, as-is (edit the
two paths first if your store lives somewhere else). It installs the
global instruction, both hooks, and proves each one works.

```
Set up hard enforcement for my personal context store on this machine.
The store is cloned at ~/context-store (change this if yours differs).
It has tools/context.py (start / log / packet / status) and an AGENTS.md
standing instruction. Do all of the following, then prove each one works:

1. GLOBAL INSTRUCTION: Append the below-the-line section of the repo's
   AGENTS.md to ~/.claude/CLAUDE.md (create it if missing), replacing
   <PATH-TO-REPO> with the store's absolute path. Don't remove anything
   already in that file.

2. READ ENFORCEMENT — SessionStart hook: Merge into
   ~/.claude/settings.json (preserve all existing settings; only
   add/merge the hooks keys): a SessionStart hook with matcher
   "startup|resume" running a wrapper script
   ~/.claude/hooks/context_store_start.sh that:
   - exits 0 silently if the current directory is under ~/work or any
     work directory (NEVER inject personal context into work sessions);
   - otherwise runs: cd to the store, a quiet git pull --ff-only
     (ignore failure if offline), then
     python3 tools/context.py start, printing its output to stdout
     (SessionStart hook stdout is added to the session context).

3. WRITE ENFORCEMENT — Stop hook: Add a Stop hook running
   ~/.claude/hooks/context_store_check.py (write it, Python stdlib
   only). The script must:
   - exit 0 silently for work directories (same rule as above);
   - exit 0 if the store's log/<today>.md exists and was modified
     within the last 30 minutes;
   - exit 0 if a file ~/.claude/context-store.skip was touched within
     the last 2 hours (my manual escape hatch);
   - otherwise print to stderr: "Context store write-back missing.
     Before ending, run: python3 <store>/tools/context.py log
     \"<summary: what changed / decisions / what's next>\" — or, if
     this session changed nothing, log exactly that." and exit 2
     (exit 2 on a Stop hook blocks the stop and shows stderr to you).

4. TEST AND SHOW ME THE EVIDENCE:
   - Start a fresh session in a personal project: show that the context
     store content (index/profile) is present in the session context
     without you having to ask for it.
   - In a test session, try to end WITHOUT logging: show the Stop hook
     blocking you. Then log via context.py and show the session ending
     cleanly, the new entry in log/<today>.md, and the commit pushed.
   - Start a session under ~/work (or a stand-in folder): show both
     hooks stayed silent.

Report what you changed file-by-file. If any hook doesn't behave as
described, fix it and retest — don't just describe the setup as done.
```
