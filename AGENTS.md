# Tool Belt project context

## Durable project decision

Ian designated `ianmkinney/Ian-tool-belt` as **our tool belt** on 2026-10-01 (America/New_York). In this repository, “our belt” refers to the root `belt.json` and its referenced rules, skills and connections. Preserve this identity unless Ian changes it.

This file is project-scoped memory, not a claim of account-wide assistant memory or automatic cross-chat recall. Future assistants should read it when working in this repo.

## Product direction

Open source and configuration as code come first. Keep the core useful without a paid hosted service. Education, courses and implementation help are potential sustainability paths, not implemented products. Portable configurations must report unsupported capabilities honestly.

## Engineering

Read README.md and docs/design.md before changing the format. Keep secrets outside the repository. Use synthetic examples; do not publish personal history or client details. Add original reusable skills rather than copying private or platform-provided instructions.

Run `python3 scripts/validate.py belt.json` and `python3 -m unittest discover -s tests -v` when changing validation or export behavior. Regenerate both client exports into a fresh ignored output directory. Never auto-overwrite a user's assistant configuration.

## Required coding and PR workflow

Read and follow `rules/engineering.md` for every code change. It is part of the exported belt, not merely a preference in a conversation. Keep comments minimal and useful; cover changed behavior with tests. Find and reuse the session's open PR, or open one draft PR on a new session branch. Push all fixes to that PR. After each push inspect checks and review feedback for the latest head, fix failures, and continue until checks pass or a concrete blocker is documented. Never label unconfigured or pending checks as green. Do not merge or promise unattended monitoring without authorization.
