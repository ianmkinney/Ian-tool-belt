# Break room rules for bots

Do this at the start of every turn:

1. **Run `breakroom start --as "<your exact registry name>"`** (or set `BREAKROOM_AGENT`).
2. **Active announcements are standing instructions from Ian.** They override older memory, notes, and habits. If one conflicts with what you remember, the announcement wins. Newest wins among announcements.
3. **Check before you start work:** `breakroom check "<title>"`. If a card already exists, join it with `breakroom help ID "..."` instead of duplicating it.
4. **Claim it:** `breakroom claim "<title>" --product <app> [--goal ...] [--cost free|low|high]`.
5. **On long work, send a heartbeat at least every 24h:** `breakroom heartbeat ID`. Cards without one go stale and another bot can take them over. Use `breakroom update ID --status ... --link ... --blocked-on ...` as things change.
6. **Comment on the card instead of sending side DMs:** use `help`, `advise`, or `object`. For handoffs with no card, use `breakroom log --to X --kind handoff "..."`.
7. **Don't ping Ian. Use `breakroom ask-ian ID "question"`.** Questions get batched into `breakroom ian-queue` and `breakroom digest`.
8. **Never send messages or emails as Ian without his approval.** Write a draft and let him press send.
9. **When you finish, run `breakroom done ID`.** If you're dropping the work, run `breakroom release ID`.
10. Before restating a price, name, or policy, check `breakroom decisions`. Ian's decisions go into the ledger with `breakroom decide`. To find who owns something, use `breakroom who <topic>`.
