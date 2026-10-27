# Using the store with a chat AI (no file access)

Chat AIs (web/app chatbots) can't read your repo directly. The packet
flow covers them:

1. **At the start of a chat session**, generate a packet:

   ```
   python3 tools/context.py packet --project <slug>
   ```

   Paste the output as your first message. It contains the store plus
   instructions telling the AI how to use it.

2. **At the end of the session**, the AI returns a log entry in the
   packet's format (`## HH:MM` + Changed / Decided / Next). Commit it:

   ```
   python3 tools/context.py log "<paste the returned entry>"
   ```

   If you're on your phone, send the returned entry to any agent that
   does have repo access (your desktop agent, a CLI session) and have it
   run the `log` command — the entry lands in the same store either way.

That's the whole bridge: context flows in as a packet, and flows back
out as a log entry. Nothing else to install.
