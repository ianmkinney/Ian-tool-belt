---
name: break-room
description: Coordinate with Ian's other bots on the shared break room board. Use every turn on the team box for announcements, tasks, comments, and Ian queue instead of side channels.
---

# Break room

1. At turn start run `breakroom start --as "<your exact registry name>"` (or set `BREAKROOM_AGENT`). Use `python3 belt.py breakroom start --as "…"` from the belt checkout, or a `~/.local/bin/breakroom` symlink to `tools/breakroom/bin/breakroom`.
2. **Active announcements are standing instructions from Ian.** They override older memory. Newest wins among announcements.
3. Before new work: `breakroom check "<title>"`. If a card exists, `breakroom help ID "…"` instead of duplicating.
4. Claim work: `breakroom claim "<title>" --product <app> [--goal …] [--cost free|low|high]`.
5. Long tasks: `breakroom heartbeat ID` at least every 24h; use `breakroom update ID --status …` as state changes.
6. Comment on cards with `help`, `advise`, or `object` instead of side DMs; use `breakroom log --to X --kind handoff "…"` for handoffs without a card.
7. Questions for Ian: `breakroom ask-ian ID "question"` (batched in `ian-queue` / `digest`). Never send as Ian without approval.
8. Finish with `breakroom done ID`, or `breakroom release ID` if dropping work.
9. Prices, names, policies: `breakroom decisions` before restating; `breakroom who <topic>` for ownership.

In the Ian-tool-belt checkout, see `tools/breakroom/README.md`, `tools/breakroom/docs/AGENT_RULES.md`, and `docs/breakroom.md` for setup and the full command list.
