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

**Status:** working manifest validator and configuration exporter; documented connection profiles; four original skills. No running gateway, authenticated services, marketplace or live cross-assistant proof yet.

## Give this belt to another agent

**Start with [How an agent uses Tool Belt](docs/agent-guide.md).** The agent needs access to the actual files; the repository URL alone does not install tools or load instructions.

Copy this prompt, replacing the bracketed values:

> Use the belt at [BELT_PATH] for [TASK] in [PROJECT_PATH]. Read AGENTS.md and belt.json, then all referenced rules. Inspect skill descriptions and read the matching SKILL.md. Check your actual available tools; do not assume MCP declarations are connected. Follow the target project's instructions, test changed behavior, and use one session PR with latest-head CI checks. Use sub-agents for independent work if available. Report missing setup, then carry out the authorized task.

Already exported? Ask the agent to read `INSTRUCTIONS.md`, `compatibility.json`, and the relevant copied skill. Rules are packaged; native skill discovery and live connections still require explicit setup. [Source and exported-bundle walkthroughs →](docs/agent-guide.md)

## What's in the pouches?

| Tools | Skills | Rules |
| --- | --- | --- |
| GitHub MCP — read-only repository access | Build an API slice | Small, reviewable changes |
| Context7 — library documentation | Reconcile data | Keep credentials outside Git |
| Playwright — isolated browser testing | Verify a browser flow | Verify outcomes before claiming success |
| [Connection catalog](connections/README.md) | Evaluate an MCP candidate | [Working agreement](rules/working-agreement.md) |

## Try the belt locally

Python 3.10+ is enough to validate and export. These commands do not start servers, install packages, read credentials or contact services.

```sh
python3 scripts/validate.py belt.json
python3 scripts/export.py belt.json --target claude-code --out dist/claude-code
python3 scripts/export.py belt.json --target vscode --out dist/vscode
python3 -m unittest discover -s tests -v
```

Use a new output directory each time. Inspect generated files before merging them into any existing assistant setup. See [setup and compatibility](docs/setup.md) for authentication, skill loading and limitations.

## One source of truth

`belt.json` declares our connections, skills, rules and target adapters. `AGENTS.md` records the decision to treat this repository as **our tool belt**. It is durable project context, not automatic account-wide memory.

- [Clean code, tests and session PR contract](rules/engineering.md)
- [Skills and examples](skills/README.md)
- [Design and format](docs/design.md)
- [Roadmap](docs/roadmap.md)
- [Brand guide](branding/README.md)
- [Contributing](CONTRIBUTING.md)

## Open by design

Keep the local format and tools useful without a paywall. Share working examples and teach reproducible workflows. Courses, workshops and implementation services are possible future ways to sustain the project; they are not launched offerings.

MIT licensed. Third-party tools retain their own licenses and terms. “Pack once. Build anywhere.” is our direction, not a claim that every assistant supports every capability.
