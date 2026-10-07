# Setup and compatibility

## Generate, inspect, then merge

Run the commands in README.md. The exporter writes only to a new directory and never installs into an assistant automatically. It emits configuration, `INSTRUCTIONS.md`, skill copies, `local-ai.env.example` and `compatibility.json`.

| Target | Generated connection file | Instruction/skill handling | Verification |
| --- | --- | --- | --- |
| Claude Code | `.mcp.json` | Explicitly attach INSTRUCTIONS.md and the selected skills, or configure supported native loading yourself | JSON structure tested; live client untested |
| VS Code | `.vscode/mcp.json` | Same explicit loading requirement | JSON structure tested; live client untested |
| Cursor | `.cursor/mcp.json` | Rules as `.cursor/rules/*.mdc` with `alwaysApply: true`; skills in `.cursor/skills/<name>/` | Locations follow Cursor's docs; structure tested; live client untested |
| OpenCode | `opencode.json` | `instructions` points at INSTRUCTIONS.md; skills in `.opencode/skills/<name>/`; local model provider included | Locations follow OpenCode's docs; structure tested; live client untested |
| ChatGPT | None | Requires a supported hosted integration and client-specific setup | Not supported by this exporter |

This is not a gateway. Each exported client connects directly to the declared servers. Local stdio Playwright cannot be made available to a remote-only client just by uploading this file.

### Dropping the belt into a project for Cursor

```sh
python3 scripts/export.py belt.json --target cursor --out dist/cursor
```

Review `dist/cursor`, then copy `.cursor/` into the project root. If the project already has `.cursor/mcp.json` or rules with the same names, merge them by hand. Cursor resolves `${env:NAME}` from the environment it was launched with. Open **Customize** in Cursor to confirm that the MCP servers, rules and skills appear, then make a harmless call. `INSTRUCTIONS.md` is a combined copy for clients or chats that do not read `.cursor/`.

### Local agent clients

To give the belt to a local model through OpenCode or Claude Code, see [local AI](local-ai.md#hand-the-belt-to-the-local-model).

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
