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

`./belt` is the same CLI. The scripts under `scripts/` still work; `belt.py` wraps them.

## Where to look next

- **Agents:** [`AGENTS.md`](AGENTS.md) and [`belt.index.json`](belt.index.json) (generated from `belt.json`; CI fails if they drift)
- **Setup, credentials, what each client gets:** [docs/setup.md](docs/setup.md)
- **Local Ollama / OpenCode / ollmcp:** [docs/local-ai.md](docs/local-ai.md)
- **Connections and smoke tests:** [connections/README.md](connections/README.md)
- **Format:** [docs/design.md](docs/design.md)
- **GitHub Actions, pin checks, adoption kit:** [docs/automation.md](docs/automation.md)
- **Skills:** [skills/README.md](skills/README.md)
- **Break room (team board for bots):** [docs/breakroom.md](docs/breakroom.md)
- **Engineering contract:** [rules/engineering.md](rules/engineering.md)

`python3 belt.py doctor --offline` and `python3 -m unittest discover -s tests -v` never start servers or read secrets.

MIT licensed. Third-party tools keep their own licenses. “Pack once. Build anywhere.” is the direction, not a claim that every assistant supports every capability.
