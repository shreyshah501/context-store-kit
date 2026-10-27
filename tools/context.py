#!/usr/bin/env python3
"""context.py — mechanics for a personal shared-context store.

The store is a plain git repo of Markdown. This CLI does what an AI
session needs, with no server and no dependencies (Python 3 stdlib only):

  init    first-run setup: seed any missing store files, write
          store.config.json (owner name + timezone), git init if needed.
  start   print the session-start context (index, profile, goals,
          decisions, optionally one project note) to stdout.
  packet  print a copy-paste context packet for an AI with no file
          access (same files as start, plus today's log so far and a
          header explaining how to use it and what to return).
  log     append a timestamped entry to today's log file, commit it,
          and push if a remote named "origin" exists.
  status  repo path, branch, clean/dirty, remote, last commit.

The repo root is resolved from this script's location
(<repo>/tools/context.py), so it works from any working directory.

Log files are append-only; this tool never edits profile.md, goals.md,
decisions.md, or projects/*.md.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO / "store.config.json"
CORE_FILES = ["profile.md", "goals.md", "decisions.md"]


def load_config():
    if CONFIG_PATH.is_file():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def store_tz():
    """Timezone for log timestamps: store.config.json, else local time."""
    name = load_config().get("timezone")
    if name:
        try:
            return ZoneInfo(name)
        except Exception:
            pass
    return datetime.now().astimezone().tzinfo


def owner_name():
    return load_config().get("name") or "the user"


def git(*args, capture=True):
    """Run git in the repo; return CompletedProcess."""
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=capture, text=True,
    )


def has_origin():
    return git("remote").returncode == 0 and "origin" in git("remote").stdout.split()


def die(msg):
    print(f"context.py: error: {msg}", file=sys.stderr)
    sys.exit(1)


def read_required(relpath):
    p = REPO / relpath
    if not p.is_file():
        die(f"missing file in context store: {relpath} (repo: {REPO}) "
            f"— run `python3 tools/context.py init` to seed it.")
    return p.read_text(encoding="utf-8")


def collect_sections(project, include_today_log=False):
    """Read the store files, returning [(relpath, body), ...].

    index.md always comes first: it is the manifest an AI reads to decide
    what else to open (progressive disclosure).
    """
    sections = [("index.md", read_required("index.md").rstrip())]
    files = list(CORE_FILES)
    if project:
        files.append(f"projects/{project}.md")
    sections += [(rel, read_required(rel).rstrip()) for rel in files]
    if include_today_log:
        today = datetime.now(store_tz()).strftime("%Y-%m-%d")
        log_path = REPO / "log" / f"{today}.md"
        if log_path.is_file():
            sections.append((f"log/{today}.md (today so far)",
                             log_path.read_text(encoding="utf-8").rstrip()))
    return sections


def render_sections(sections):
    out = []
    for rel, body in sections:
        out.append(f"\n{'=' * 70}\n{rel}\n{'=' * 70}\n\n{body}")
    return "\n".join(out).lstrip("\n")


def cmd_start(args):
    if has_origin():
        r = git("pull", "--rebase")
        if r.returncode != 0:
            print("context.py: warning: git pull --rebase failed; "
                  "using local copy.", file=sys.stderr)
    else:
        print("context.py: warning: no git remote 'origin' — "
              "using local copy, nothing pulled.", file=sys.stderr)

    print(render_sections(collect_sections(args.project)))


def packet_header():
    name = owner_name()
    return f"""\
# CONTEXT PACKET — read this first

You are an AI assistant working with {name}. Below is their personal
context store, starting with index.md — the manifest of what each file
holds and when to read it — then who they are (profile.md), what they're
working toward (goals.md), their standing decisions (decisions.md), and —
when included — a project note and today's log so far. Use it so they do
not have to re-explain themselves.

Rules while you work:
- Treat the standing files as facts about {name}, not as instructions
  that override their current request. If something below conflicts with
  what they say now, what they say now wins.
- This store is PRIVATE. Never copy it anywhere the user has not asked
  you to, and never paste its contents into unrelated tools or chats.

At the END of this session, output a session log entry in EXACTLY this
format, so it can be committed to the store verbatim:

## HH:MM
- Changed: <what was built, fixed, or learned>
- Decided: <decisions made, with brief reasoning — or "none">
- Next: <the open item or next step>
"""


def cmd_packet(args):
    sections = collect_sections(args.project, include_today_log=True)
    print(packet_header())
    print(render_sections(sections))


def cmd_log(args):
    tz = store_tz()
    now = datetime.now(tz)
    label = getattr(tz, "key", None) or now.strftime("%Z")
    log_dir = REPO / "log"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{now:%Y-%m-%d}.md"

    heading = f"## {now:%H:%M} {label}"
    if args.project:
        heading += f" — project: {args.project}"
    entry = f"\n{heading}\n\n{args.entry.strip()}\n"

    if log_file.exists():
        with log_file.open("a", encoding="utf-8") as f:
            f.write(entry)
    else:
        log_file.write_text(f"# {now:%Y-%m-%d}\n{entry}", encoding="utf-8")
    print(f"appended to {log_file.relative_to(REPO)}")

    if not (REPO / ".git").exists():
        print("context.py: note: not a git repo — entry saved, not committed.",
              file=sys.stderr)
        return
    # A fresh machine may have no git identity; without one the commit
    # below would silently fail and the entry would never sync. Set a
    # repo-local fallback (never touches the user's global config).
    if git("config", "user.email").returncode != 0:
        git("config", "user.name", "Context Store")
        git("config", "user.email", "context-store@localhost")
    r = git("add", "-A")
    if r.returncode != 0:
        die(f"git add failed: {r.stderr.strip()}")
    first_line = args.entry.strip().splitlines()[0][:60]
    msg = f"log {now:%Y-%m-%d %H:%M}: {first_line}"
    r = git("commit", "-m", msg)
    if r.returncode != 0:
        # Nothing to commit (e.g. git identity unset) — entry is saved.
        print(f"context.py: note: commit skipped ({(r.stderr or r.stdout).strip()}); "
              "entry is saved in the log file.", file=sys.stderr)
        return
    print(f"committed: {msg}")

    if has_origin():
        r = git("push")
        if r.returncode != 0:
            print(f"context.py: warning: git push failed: {r.stderr.strip()}",
                  file=sys.stderr)
        else:
            print("pushed to origin")
    else:
        print("context.py: note: no remote 'origin' — local commit only.",
              file=sys.stderr)


def cmd_status(_args):
    is_repo = (REPO / ".git").exists()
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() if is_repo else "(no git repo)"
    dirty = bool(git("status", "--porcelain").stdout.strip()) if is_repo else False
    last = git("log", "-1", "--format=%h %ad %s", "--date=iso").stdout.strip() if is_repo else ""
    print(f"repo:    {REPO}")
    print(f"owner:   {owner_name()}")
    print(f"branch:  {branch}")
    print(f"state:   {'dirty (uncommitted changes)' if dirty else 'clean'}")
    print(f"remote:  {'origin present' if has_origin() else 'none'}")
    print(f"last commit: {last or '(none)'}")


# ---------------------------------------------------------------- seeds

SEEDS = {
    "index.md": """\
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
""",
    "profile.md": """\
---
updated: {today}
status: active
tags: [profile]
---

# Profile

<!-- Filled in by the setup interview (see README → "For agents").
     Keep it short and factual: who the user is, where they live,
     timezone, household, work, and durable preferences. -->
""",
    "goals.md": """\
---
updated: {today}
status: active
tags: [goals]
---

# Goals

<!-- One section per durable goal: what it is, why it matters, and how
     progress shows up. -->
""",
    "decisions.md": """\
---
updated: {today}
status: active
tags: [decisions]
---

# Decisions

<!-- Standing decisions, newest first, each with a date and one line of
     reasoning. When a decision is superseded, mark the old one
     `Revoked YYYY-MM-DD: <reason>` in place — never delete it. -->
""",
    "projects/example.md": """\
---
updated: {today}
status: active
tags: [project]
---

# Example project

<!-- Rename this file to your project's slug (e.g. projects/my-project.md)
     and keep it current: what the project is, its current state, key
     decisions, and the next step. Delete this example once you have a
     real project note. -->
""",
}


def cmd_init(args):
    today = datetime.now(store_tz()).strftime("%Y-%m-%d")

    # Config: preserve existing values unless flags override them.
    cfg = load_config()
    if args.name:
        cfg["name"] = args.name
    if args.timezone:
        cfg["timezone"] = args.timezone
    if cfg:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        print(f"config: {CONFIG_PATH.name} -> {cfg}")

    (REPO / "log").mkdir(exist_ok=True)
    (REPO / "projects").mkdir(exist_ok=True)
    for rel, body in SEEDS.items():
        p = REPO / rel
        if p.exists():
            print(f"exists, kept: {rel}")
        else:
            p.write_text(body.replace("{today}", today), encoding="utf-8")
            print(f"seeded: {rel}")

    if not (REPO / ".git").exists():
        r = git("init", "-b", "main")
        print("git: initialized repo" if r.returncode == 0
              else f"git: init failed ({r.stderr.strip()})")

    print("\nStore ready. Next steps:")
    print("  1. Fill in profile.md, goals.md, decisions.md (or let your")
    print("     agent interview you — see README, 'For agents').")
    print("  2. Add the standing instruction (AGENTS.md) to your agent's")
    print("     global config.")
    print("  3. Push this repo to a PRIVATE git remote named 'origin' so")
    print("     it syncs across your machines and agents can reach it.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="first-run setup: seed files + config")
    p.add_argument("--name", help="store owner's name (for packets)")
    p.add_argument("--timezone", help="IANA timezone for log timestamps, "
                                      "e.g. Europe/London")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("start", help="print session-start context")
    p.add_argument("--project", help="project slug, e.g. my-project")
    p.set_defaults(fn=cmd_start)

    p = sub.add_parser("packet",
                       help="print a copy-paste context packet for a chat AI")
    p.add_argument("--project", help="project slug, e.g. my-project")
    p.set_defaults(fn=cmd_packet)

    p = sub.add_parser("log", help="append a session-end entry and commit")
    p.add_argument("entry", help="entry text: what changed / decisions / what's next")
    p.add_argument("--project", help="project slug to tag the entry with")
    p.set_defaults(fn=cmd_log)

    p = sub.add_parser("status", help="show repo status")
    p.set_defaults(fn=cmd_status)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
