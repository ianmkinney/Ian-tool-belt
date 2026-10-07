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

**A portable workshop for building useful software.**

[MCP](https://modelcontextprotocol.io/) connections, original workflow skills and shared rules, versioned together. This is Ian's and ChatGPT's working belt: open source first, designed for API development, data pipelines and browser-tested applications.

**Status:** working manifest validator; configuration exporters for Claude Code, VS Code, Cursor and OpenCode; a local AI profile (Ollama by default) with a health check; scaffolding for skills and packages; styling tokens; and GitHub Actions for variable updates, weekly pin checks, allowlisted tasks and a zizmor security lint of the workflows themselves. No local model has been installed or exercised yet. There is no running gateway, authenticated service, marketplace or live cross-assistant proof yet.

## What's in the pouches?

| Tools | Skills | Rules |
| --- | --- | --- |
| GitHub MCP — read-only repository access | Build an API slice | Small, reviewable changes |
| Context7 — library documentation | Reconcile data | Keep credentials outside Git |
| Playwright — isolated browser testing | Verify a browser flow | Verify outcomes before claiming success |
| Local AI — your own model via Ollama (optional) | Evaluate an MCP candidate | [Working agreement](rules/working-agreement.md) |
| [Connection catalog](connections/README.md) | [Add your own](skills/README.md#add-a-skill) | [Engineering contract](rules/engineering.md) |

Also in the belt: [packages](docs/design.md#packages) (pinned tools such as [zizmor](docs/automation.md#workflow-security-lint) and the [MCP Inspector](connections/README.md#smoke-test-a-connection), and reusable files) and [styling tokens](styling/README.md).

## Try the belt locally

Python 3.10+ is enough to validate and export. These commands do not start servers, install packages, read credentials or contact services.

```sh
python3 scripts/validate.py belt.json
python3 scripts/export.py belt.json --target claude-code --out dist/claude-code
python3 scripts/export.py belt.json --target vscode --out dist/vscode
python3 scripts/export.py belt.json --target cursor --out dist/cursor
python3 scripts/export.py belt.json --target opencode --out dist/opencode
python3 -m unittest discover -s tests -v
```

Use a new output directory each time. Inspect generated files before merging them into any existing assistant setup. See [setup and compatibility](docs/setup.md) for authentication, skill loading and limitations.

## Local AI

No local model? Everything above still works. When you are ready, follow [getting started with Ollama](docs/local-ai.md): install it, run `ollama pull gemma4:e2b`, then check it with:

```sh
python3 scripts/local_ai_check.py --chat
```

The same guide shows how to hand the belt to a local model through OpenCode or Claude Code.

## Smoke-test a connection

With Node.js 22.19+, `python3 scripts/mcp_smoke.py playwright` starts the server through the pinned MCP Inspector and lists its tools. See [smoke-test a connection](connections/README.md#smoke-test-a-connection).

## Grow the belt

```sh
python3 scripts/new.py skill review-sql --description "Review SQL changes. Use when a migration or query changes."
python3 scripts/new.py package api-client --kind files --description "Shared HTTP client"
python3 scripts/belt_set.py belt.json models.local-ai.presets.ollama.model gemma4:e4b
python3 scripts/check_pins.py belt.json
```

Each command validates the result and leaves `belt.json` unchanged if it is invalid. The same operations run in [GitHub Actions](docs/automation.md).

## One source of truth

`belt.json` declares our connections (work and personal), local model presets, packages, skills, rules and target adapters. `AGENTS.md` records the decision to treat this repository as **our tool belt**. It is durable project context, not automatic account-wide memory.

- [Clean code, tests and session PR contract](rules/engineering.md)
- [Skills and examples](skills/README.md)
- [Design and format](docs/design.md)
- [Local AI with Ollama](docs/local-ai.md)
- [GitHub Actions](docs/automation.md)
- [Roadmap](docs/roadmap.md)
- [Brand guide](branding/README.md) and [styling tokens](styling/README.md)
- [Contributing](CONTRIBUTING.md)

## Open by design

Keep the local format and tools useful without a paywall. Share working examples and teach reproducible workflows. Courses, workshops and implementation services are possible future ways to sustain the project; they are not launched offerings.

MIT licensed. Third-party tools retain their own licenses and terms. “Pack once. Build anywhere.” is our direction, not a claim that every assistant supports every capability.
