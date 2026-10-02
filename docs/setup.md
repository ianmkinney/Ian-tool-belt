# Setup and compatibility

## Generate, inspect, then merge

Run the commands in README.md. The exporter writes only to a new directory and never installs into an assistant automatically. It emits configuration, `INSTRUCTIONS.md`, skill copies, and `compatibility.json`.

| Target | Generated connection file | Instruction/skill handling | Verification |
| --- | --- | --- | --- |
| Claude Code | `.mcp.json` | Explicitly attach INSTRUCTIONS.md and the selected skills, or configure supported native loading yourself | JSON structure tested; live client untested |
| VS Code | `.vscode/mcp.json` | Same explicit loading requirement | JSON structure tested; live client untested |
| ChatGPT | None | Requires a supported hosted integration and client-specific setup | Not supported by this exporter |

This is not a gateway. Each exported client connects directly to the declared servers. Local stdio Playwright cannot be made available to a remote-only client just by uploading this file.

## Credentials

Provide `GITHUB_MCP_TOKEN` and `CONTEXT7_API_KEY` through the environment used to launch your client. The exporter writes variable references, never their values. It does not read `.env` files. Claude Code and VS Code use different environment-variable syntax; the exporter translates it. Do not commit tokens into generated headers. Missing values must be resolved before connecting.

After reviewing configuration, use the target client's own trust and MCP setup flow. Confirm tool discovery, then perform a harmless read-only call. For GitHub, inspect only a repository authorized by the credential. For Context7, request public library documentation. For Playwright, use a local test page with synthetic data. Record actual results; do not infer compatibility from successful export.

## Skills and rules

The generated instruction file combines the rules and lists relative paths to copied SKILL.md files. The exporter does not automatically enable native skill discovery or inject system instructions. Ask the assistant to read INSTRUCTIONS.md and the relevant skill explicitly. Host policies always retain precedence.

## Official client references

- https://code.claude.com/docs/en/mcp
- https://code.visualstudio.com/docs/agents/reference/mcp-configuration

References checked 2026-10-02 UTC. Client schemas and capabilities can change.
