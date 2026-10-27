#!/usr/bin/env bash
# One-command setup for your context store.
# Usage: ./setup.sh [--name "Your Name"] [--timezone Area/City]
set -euo pipefail
cd "$(dirname "$0")"
python3 tools/context.py init "$@"
echo
echo "Done. Now:"
echo "  1. Paste the below-the-line section of AGENTS.md into your agent's"
echo "     global config (Claude Code: ~/.claude/CLAUDE.md)."
echo "  2. Create a PRIVATE repo on your git host, add it as 'origin', and push:"
echo "       git remote add origin <your-private-repo-url>"
echo "       git add -A && git commit -m 'My context store' && git push -u origin main"
