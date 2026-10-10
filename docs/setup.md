# Setup and compatibility

## One command into a project

From the app directory, with a checkout of this belt:

```sh
python3 path/to/Ian-tool-belt/belt.py use
```

`use` auto-detects Cursor (`.cursor/`), OpenCode (`opencode.json`), Claude Code (`.mcp.json`) or VS Code (`.vscode/mcp.json`). An empty project defaults to Cursor. If more than one marker is present, pass the target: `python3 belt.py use opencode`. Existing files are skipped; `--force` overwrites. `--include-personal` is the only way personal servers are copied.

`python3 belt.py doctor` validates the belt, lists which env vars are missing, and checks local AI when it is running. `doctor --offline` skips network and local AI (what CI runs).

## Generate into a new directory, then merge by hand

`python3 belt.py use cursor --out dist/cursor` (or `python3 scripts/export.py belt.json --target cursor --out dist/cursor`) writes only to a new directory and never installs into an assistant automatically. It emits configuration, `INSTRUCTIONS.md`, skill copies, `local-ai.env.example` and `compatibility.json`.

| Target | Generated connection file | Instruction/skill handling | Verification |
| --- | --- | --- | --- |
| Claude Code | `.mcp.json` | Explicitly attach INSTRUCTIONS.md and the selected skills, or configure supported native loading yourself | JSON structure tested; live client untested |
| VS Code | `.vscode/mcp.json` | Same explicit loading requirement | JSON structure tested; live client untested |
| Cursor | `.cursor/mcp.json` | Rules as `.cursor/rules/*.mdc` with `alwaysApply: true`; skills in `.cursor/skills/<name>/` | Locations follow Cursor's docs; structure tested; live client untested |
| OpenCode | `opencode.json` | `instructions` points at INSTRUCTIONS.md; skills in `.opencode/skills/<name>/`; local model provider included | Locations follow OpenCode's docs; structure tested; live client untested |
| ChatGPT | None | Requires a supported hosted integration and client-specific setup | Not supported by this exporter |

This is not a gateway. Each exported client connects directly to the declared servers. Local stdio Playwright cannot be made available to a remote-only client just by uploading this file.

### Cursor

`python3 belt.py use cursor --app path/to/app` writes `.cursor/mcp.json`, `.cursor/rules/*.mdc` and `.cursor/skills/`. Cursor resolves `${env:NAME}` from the environment it was launched with. Open **Customize** in Cursor to confirm that the MCP servers, rules and skills appear, then make a harmless call. `INSTRUCTIONS.md` is a combined copy for clients or chats that do not read `.cursor/`.

Packages that are not MCP connections (zizmor, actionlint, shellcheck, gitleaks, mcp-inspector, ollmcp, styling) are listed in `compatibility.json` and [belt.index.json](../belt.index.json) `skipped`; they are not copied into `.cursor/`.

### Local agent clients

To give the belt to a local model through OpenCode, Claude Code or ollmcp, see [local AI](local-ai.md#hand-the-belt-to-the-local-model). ollmcp reads the Claude Code export's `.mcp.json` via `--servers-json`; it is not a fifth export adapter.

## Credentials

Provide `GITHUB_MCP_TOKEN` and `CONTEXT7_API_KEY` through the environment used to launch your client. `LOCAL_AI_API_KEY` is optional and only needed if your local runtime requires a key; Ollama does not. The exporter writes variable references, never their values. It does not read `.env` files. Each client uses different environment-variable syntax (`${VAR}`, `${env:VAR}` or `{env:VAR}`); the exporter translates it. Do not commit tokens into generated headers. Missing values must be resolved before connecting.

After reviewing configuration, use the target client's own trust and MCP setup flow. Confirm tool discovery, then perform a harmless read-only call. For GitHub, inspect only a repository authorized by the credential. For Context7, request public library documentation. For Playwright, use a local test page with synthetic data. Record actual results; do not infer compatibility from successful export.

To check a server itself before involving a client, run `python3 scripts/mcp_smoke.py <server-id>` (see [smoke-test a connection](../connections/README.md#smoke-test-a-connection)). It drives the pinned MCP Inspector, not your assistant, so a pass proves the server answers MCP but not that a client loads it.

## Skills and rules

For Claude Code and VS Code, the generated instruction file combines the rules and lists relative paths to copied SKILL.md files. The exporter does not enable native skill discovery for these clients or inject system instructions; ask the assistant to read INSTRUCTIONS.md and the relevant skill explicitly. Cursor and OpenCode exports place rules and skills where those clients document automatic loading; confirm they appear before relying on them. Host policies always retain precedence.

## Official client references

- https://code.claude.com/docs/en/mcp
- https://code.visualstudio.com/docs/agents/reference/mcp-configuration
- https://cursor.com/docs/context/mcp, https://cursor.com/docs/context/rules, https://cursor.com/docs/context/skills
- https://opencode.ai/docs/mcp-servers/, https://opencode.ai/docs/rules/, https://opencode.ai/docs/skills/, https://opencode.ai/docs/config/

Claude Code and VS Code references checked 2026-10-02 UTC; Cursor and OpenCode references checked 2026-10-07 UTC. Client schemas and capabilities can change.

## App adoption kit (versioning and engineering contract)

This is separate from `belt.py use`, which drops MCP connections, skills and rules into an assistant. The adoption kit makes an app repo follow this belt's PR-title and release-please workflows.

[`templates/app-adoption/`](../templates/app-adoption/) holds `AGENTS.md`, `.github/workflows/belt.yml`, `.github/workflows/belt-sync.yml` and the `.tool-belt.json` marker. Cursor rules are not duplicated there: the kit installs `.cursor/rules/engineering.mdc` and `working-agreement.mdc` rendered by the same code as the Cursor export, plus a sync marker line. From a checkout of this repo, run `python3 scripts/belt_sync.py --adopt --app path/to/app` to write all of them (existing files without the marker are left alone), then commit in the app. `belt.yml` runs the shared PR-title check and release-please. Check the marker with `python3 scripts/validate.py path/to/app`.

Weekly sync: `.github/workflows/belt-sync.yml` in the kit runs every Monday at 13:17 UTC, and on demand, through [`belt-sync-reusable.yml`](../.github/workflows/belt-sync-reusable.yml). When the app's `.tool-belt.json` is behind `belt.json` on our `main`, [`scripts/belt_sync.py`](../scripts/belt_sync.py) re-copies the managed files and opens or updates one draft PR on `tool-belt/sync`. See [automation](automation.md) and [tokens](../templates/versioning/README.md#optional-token).

Versioning templates live in [`templates/versioning/`](../templates/versioning/README.md). The callers use reusable workflows at `ianmkinney/Ian-tool-belt@main`. This repo's version in `belt.json` is bumped only by release-please.
