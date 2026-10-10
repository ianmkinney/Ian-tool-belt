# Contributing

Open an issue describing the user problem before proposing a large extension. Keep the first milestone focused on one belt and two clients. Include reproducible verification for adapter behavior. Never submit secrets, customer data, or unlicensed third-party content. Clearly label proposals and untested compatibility claims.

After changing `belt.json`, skills, rules, scripts or workflows, run `python3 belt.py index` and commit `belt.index.json` and the generated section of `AGENTS.md`. `python3 belt.py index --check` is what CI runs. Use `python3 belt.py` for everyday commands; `scripts/` remains the implementation.
