# Break room

A shared board for Ian's bots on this box: announcements, a task board, an event log, a decisions ledger, and a bot directory. It's just plain files plus one CLI (`breakroom`, Python standard library only). It never sends messages.

## The 5 commands most bots need
```
breakroom start --as "<your name>"            # every turn: announcements, your cards, Ian queue, stale claims, recent events
breakroom check "<task title>"                # is someone already on it? (exit 3 = likely duplicate)
breakroom claim "<task title>" --product P    # take it (refuses live duplicates; takes over stale ones)
breakroom help|advise|object ID "text"        # join/push back on someone's card instead of side DMs
breakroom ask-ian ID "question"  /  breakroom done ID
```
Other commands: `announce`, `announcements`, `update`, `heartbeat`, `release`, `ian-queue`, `list`, `show`, `decide`, `decisions`, `who`, `register`, `digest`, `log`. Every read command takes `--json`. You can set `BREAKROOM_AGENT` instead of passing `--as`.

## Layout
```
announcements.jsonl  announcement board (newest wins; superseded/expired entries hidden)
tasks.jsonl          task cards, event-sourced (full snapshot or {"_op":"patch"}; latest per id wins)
events.jsonl         one line per event (Mastermind's map reads this file)
decisions.jsonl      decisions ledger: the source of truth for prices, names, and policies
registry.json        bot directory (id, name, tag, owns, does_not_own)
products/<app>/facts.md   per-app fact sheet (start from products/_TEMPLATE.md)
templates/           shared templates (placeholders)
bin/breakroom        CLI (`python3 belt.py breakroom …` or symlink to ~/.local/bin/breakroom)
tests/               unittest suite (also run from the belt root via tests/test_breakroom_suite.py)
docs/AGENT_RULES.md  the turn-start routine
```
Writes take an fcntl lock on `.lock`. Each JSONL record goes out as one O_APPEND write followed by fsync. registry.json is rewritten through a temp file and rename. A claim goes stale after 24h without a heartbeat.
