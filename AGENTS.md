# Tool Belt project context

## Durable project decision

Ian designated `ianmkinney/Ian-tool-belt` as **our tool belt** on 2026-10-01 (America/New_York). In this repository, “our belt” refers to the root `belt.json` and its referenced rules, skills and connections. Preserve this identity unless Ian changes it.

This file is project-scoped memory, not a claim of account-wide assistant memory or automatic cross-chat recall. Future assistants should read it when working in this repo.

<!-- belt-index:start -->
## Belt map

Generated from `belt.json`. Do not edit between the markers; run `python3 belt.py index`.
Machine-readable copy: [`belt.index.json`](belt.index.json).

### Commands

- `python3 belt.py use` — Write this belt into the current project for Cursor, OpenCode, Claude Code or VS Code.
- `python3 belt.py doctor` — Validate the belt, report missing env vars, and check local AI if it is running.
- `python3 belt.py list` — Print every item in the belt with its one-line description.
- `python3 belt.py add skill|package ...` — Scaffold a skill or package and register it in belt.json.
- `python3 belt.py set PATH VALUE` — Change one allowlisted belt.json field and validate.
- `python3 belt.py run TASK` — Run one allowlisted task (validate, tests, export, pins).
- `python3 belt.py index` — Regenerate belt.index.json and the AGENTS.md belt map. CI runs index --check.
- `python3 belt.py breakroom …` — Passthrough to the breakroom team-board CLI (tools/breakroom/bin/breakroom).

### Drop this belt into a project

```sh
python3 path/to/Ian-tool-belt/belt.py use
```

Auto-detects Cursor, OpenCode, Claude Code or VS Code. Pass a target if several are present. Existing files are left alone unless `--force`. Personal connections stay out unless `--include-personal`.

### Connections, skills, rules

**Servers**
- `github` — Read-only GitHub repos and PRs over MCP. Use when inspecting code or PRs; needs GITHUB_MCP_TOKEN.
- `context7` — Library docs for the installed version. Use when writing against a dependency; needs CONTEXT7_API_KEY. Never send secrets or private source.
- `playwright` — Headless isolated browser via MCP. Use to verify a UI flow; needs Node.js. Does not attach to your real browser profile.

**Skills**
- `build-api-slice` — Build a narrow API feature with a usable frontend path. Use for Python, Rails, Spring, React or Next.js feature requests, API contracts and micro-SaaS prototypes.
- `reconcile-data` — Reconcile exports and build repeatable data transformations. Use for Postgres or Snowflake extracts, CSV files, Pandas pipelines and Excel reconciliation reports.
- `verify-browser-flow` — Verify a web application user journey using browser evidence. Use for React or Next.js UI checks, regression reproduction and frontend-to-API troubleshooting.
- `evaluate-mcp` — Evaluate an MCP server or skill for inclusion in Tool Belt. Use for AI Vault candidates, marketplace submissions, connection changes and assistant compatibility reviews.
- `break-room` — Coordinate with Ian's other bots on the shared break room board. Use every turn on the team box for announcements, tasks, comments, and Ian queue instead of side channels.

**Rules**
- `working-agreement` — Shared operating rules: small changes, secrets out of Git, honest verification. Always apply.
- `engineering` — Clean code, tests, one PR per session, Conventional Commit titles, keep CI green. Follow on every code change.

### Local model

Optional `local-ai` (default preset `ollama`, model `gemma4:e2b`). Check with `python3 belt.py doctor`.

- **opencode:** `python3 belt.py use opencode` — OpenCode reads opencode.json, including the local-ai provider.
- **claude-code:** `python3 belt.py use claude-code` — ollama launch claude in that project; attach INSTRUCTIONS.md and skills/.
- **ollmcp:** `python3 belt.py use claude-code --out dist/claude-code && uvx ollmcp==0.35.1 --servers-json dist/claude-code/.mcp.json --model gemma4:e2b` — Not an export adapter. HTTP header placeholders are not expanded; see docs/local-ai.md.

### Not exported as connections

- `styling` — files package; copy styling/ yourself. Client exports do not include it.
- `breakroom` — Team-board CLI and data dir; use belt.py breakroom or symlink bin/breakroom. Not an MCP export.
- `zizmor` — CI-only pin read by zizmor.yml; not an MCP server or export.
- `actionlint` — CI-only pin read by actionlint.yml; not an MCP server or export.
- `shellcheck` — CI-only pin read by shellcheck.yml and actionlint -shellcheck; not an MCP server or export.
- `gitleaks` — CI-only pin read by gitleaks.yml; not an MCP server or export.
- `mcp-inspector` — Used by scripts/mcp_smoke.py; not declared as a connection.
- `ollmcp` — Optional client. Load the claude-code export with --servers-json; not a fifth adapter.
- `playwright-mcp` — Consumed through the playwright server args, not copied as its own export.
- `personalServers` — Outside-work connections. Omitted from exports and this index unless --include-personal.
- `chatgpt` — Not an export adapter. Needs a hosted integration this belt does not generate.
<!-- belt-index:end -->

## Product direction

Open source and configuration as code come first. Keep the core useful without a paid hosted service. Education, courses and implementation help are potential sustainability paths, not implemented products. Portable configurations must report unsupported capabilities honestly.

## Engineering

Read README.md and docs/design.md before changing the format. Keep secrets outside the repository. Use synthetic examples; do not publish personal history or client details. Add original reusable skills rather than copying private or platform-provided instructions.

Run `python3 belt.py doctor --offline` (or `python3 scripts/validate.py belt.json`) and `python3 -m unittest discover -s tests -v` when changing validation or export behavior. After changing `belt.json`, descriptions, scripts or workflows, run `python3 belt.py index` and commit `belt.index.json` plus this file. CI fails if they are stale. To drop the belt into a project, run `python3 belt.py use` from the belt checkout with `--app` pointing at that project. Existing scripts under `scripts/` keep working; `belt.py` wraps them.

Regenerate every client export (claude-code, vscode, cursor, opencode) into a fresh ignored output directory, or let `belt.py use` copy into the project (it skips existing files unless `--force`). Never auto-overwrite a user's assistant configuration without `--force`. Add skills and packages with `python3 belt.py add`. Change belt variables with `python3 belt.py set` so validation guards the edit.

The local AI connection (Ollama by default) is optional. Nothing may require it to be running; only `scripts/local_ai_check.py` (via `python3 belt.py doctor`) contacts it. Personal (outside-work) connections belong in `personalServers` and stay out of exports unless `--include-personal`.

## Required coding and PR workflow

Read and follow `rules/engineering.md` for every code change. It is part of the exported belt, not merely a preference in a conversation. Keep comments minimal and useful; cover changed behavior with tests. Find and reuse the session's open PR, or open one draft PR on a new session branch. Push all fixes to that PR. After each push inspect checks and review feedback for the latest head, fix failures, and continue until checks pass or a concrete blocker is documented. Never label unconfigured or pending checks as green. Do not merge or promise unattended monitoring without authorization.

## Parallel work

Use available sub-agents for independent subtasks and PR/CI monitoring as described in `rules/engineering.md`. Assign isolated ownership, prevent competing branch writes, verify returned work, and retain main-agent accountability. Do not claim delegation or ongoing monitoring when the host lacks that capability.
