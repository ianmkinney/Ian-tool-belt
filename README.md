```text
             T O O L   B E L T
           Pack once. Build anywhere.

   o==o==o==o==[  TB  ]==o==o==o==o
      |  _____  |  _____  |  _____  |
      | | </> | | | {*} | | | [=] | |
      | |TOOLS| | |SKILL| | |RULES| |
      | |_____| | |_____| | |_____| |
       \_______/ \_______/ \_______/
```

# Our Tool Belt

Portable MCP connections, skills and rules for APIs, data and browser-tested apps. One command drops them into a project. Python 3.10+, no extra packages.

## Add this belt to a project

From the project directory:

```sh
python3 path/to/Ian-tool-belt/belt.py use
```

That writes Cursor files by default (`.cursor/mcp.json`, rules, skills). Pass `opencode`, `claude-code` or `vscode` when you want that client. Existing files are left alone; add `--force` only if you mean to overwrite. Personal connections stay out unless you pass `--include-personal`.

Then set `GITHUB_MCP_TOKEN` and `CONTEXT7_API_KEY` in the client environment if you need those servers. Playwright needs Node.js. A local model is optional.

## Commands

| Command | What it does |
| --- | --- |
| `python3 belt.py use` | Export the belt into this project |
| `python3 belt.py doctor` | Validate, report missing env vars, check local AI if it is running |
| `python3 belt.py list` | Everything in the belt, one line each (`--json` for agents) |
| `python3 belt.py add skill\|package ...` | Scaffold and register a skill or package |
| `python3 belt.py set PATH VALUE` | Change one allowlisted `belt.json` field |
| `python3 belt.py run TASK` | Allowlisted task (validate, tests, export, pins) |
| `python3 belt.py fpr new <branch> [--base <base>]` | Start a branch from `origin/<base>` after fetch |
| `python3 belt.py fpr sync [--base <base>]` | Merge or rebase onto that remote-tracking ref |

`./belt` is the same CLI. The scripts under `scripts/` still work; `belt.py` wraps them.

## Where to look next

- **Agents:** [`AGENTS.md`](AGENTS.md) and [`belt.index.json`](belt.index.json) (generated from `belt.json`; CI fails if they drift)
- **Setup, credentials, what each client gets:** [docs/setup.md](docs/setup.md)
- **Local Ollama / OpenCode / ollmcp / llm:** [docs/local-ai.md](docs/local-ai.md) and [docs/llm.md](docs/llm.md)
- **Connections and smoke tests:** [connections/README.md](connections/README.md)
- **Format:** [docs/design.md](docs/design.md)
- **GitHub Actions, pin checks, adoption kit:** [docs/automation.md](docs/automation.md)
- **Python lint and format (ruff):** [docs/ruff.md](docs/ruff.md)
- **Opt-in pre-commit hooks (local lint before commit):** [docs/pre-commit.md](docs/pre-commit.md)
- **Link check (lychee):** [docs/lychee.md](docs/lychee.md)
- **Spell check (typos):** [docs/typos.md](docs/typos.md)
- **Local GitHub Actions dry-run (act, Docker required):** [docs/act.md](docs/act.md)
- **Skills:** [skills/README.md](skills/README.md)
- **Break room (team board for bots):** [docs/breakroom.md](docs/breakroom.md)
- **Engineering contract:** [rules/engineering.md](rules/engineering.md)

`python3 belt.py doctor --offline` and `python3 -m unittest discover -s tests -v` never start servers or read secrets.

## App adoption

App workflow templates pin reusable belt workflows to a **commit SHA** (`@__BELT_SHA__` / `v__BELT_VERSION__` until `python3 scripts/belt_sync.py --adopt` or the weekly sync substitutes them). Never use `@main` on `ianmkinney/Ian-tool-belt` workflow references; Belt checks run `scripts/check_belt_workflow_pins.py`. See [docs/automation.md](docs/automation.md) for the adoption kit, sync PRs and versioning templates.

MIT licensed. Third-party tools keep their own licenses. “Pack once. Build anywhere.” is the direction, not a claim that every assistant supports every capability.
