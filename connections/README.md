# Connection catalog

Configured here means declared in the manifest. No credentials have been supplied and no live MCP session has been tested by this project.

| Connection | Why it belongs | Setup | Current evidence |
| --- | --- | --- | --- |
| GitHub official MCP | Repository inspection and PR context | Set GITHUB_MCP_TOKEN in the launching client's environment with minimum required repo access | Official endpoint documented; read-only URL selected; authentication untested |
| Context7 by Upstash | Documentation for the actual libraries in a project | Set CONTEXT7_API_KEY in the launching client's environment | Official endpoint/header documented; authentication untested |
| Playwright by Microsoft | UI regression checks and browser workflows | Install Node.js and required browser/runtime dependencies | Package version 0.0.83 appears in upstream package.json; registry installation and execution untested |

## Local AI model

| Connection | Why it belongs | Setup | Current evidence |
| --- | --- | --- | --- |
| `local-ai` (OpenAI-compatible) | A private model on Ian's own computer for agent clients and project code | Install Ollama (default preset) or another runtime; optional `LOCAL_AI_BASE_URL`, `LOCAL_AI_MODEL`, `LOCAL_AI_API_KEY`. See [local AI guide](../docs/local-ai.md) | Presets match runtime documentation; health check unit-tested against a stub server; no local runtime has been exercised by this project |

This is a model endpoint, not an MCP server. It is declared under `models` in `belt.json`. Agent clients such as OpenCode use it as their model and the belt's MCP connections as their tools. No local runtime is installed yet; Ollama is the recommendation.

## Work connections

GitHub starts read-only. This declaration does not reuse ChatGPT's connected GitHub credentials. Enabling writes is a separate intentional configuration change. Restrict repository access in the token itself.

The Context7 profile uses a key even if the service also permits limited unauthenticated usage. Never put source secrets or private customer data in documentation queries.

Playwright uses an isolated, headless browser. Isolation here means a temporary browser profile, not a security sandbox. No existing personal browser session is attached. A fixed npm package version is not a complete transitive dependency lock or supply-chain verification. Verify package availability before first use.

## Personal connections (outside work)

`personalServers` in `belt.json` holds MCP connections for personal life rather than work: for example, a notes app, a calendar or a home service. It uses exactly the same schema as `servers`. It is **empty** until Ian chooses services; none are assumed.

Exports leave personal connections out by default, so dropping the belt into a work or client project never carries them along. Include them only where they belong:

```sh
python3 scripts/export.py belt.json --target cursor --out dist/cursor-personal --include-personal
```

To add one: evaluate it with the `evaluate-mcp` skill, add an entry to `personalServers` with an HTTPS URL or pinned stdio command, add any credential variable names to `secretRefs`, add a row to the table below, and validate. Server ids must be unique across work and personal connections. Use separate, minimally scoped credentials for personal services.

| Connection | Why it belongs | Setup | Current evidence |
| --- | --- | --- | --- |
| *(none yet)* | | | |

## Official sources checked 2026-10-02 UTC

- https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md
- https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md
- https://github.com/upstash/context7/blob/master/packages/mcp/README.md
- https://github.com/microsoft/playwright-mcp/blob/main/README.md
- https://github.com/microsoft/playwright-mcp/blob/main/package.json

Local AI sources, checked 2026-10-07 UTC: https://docs.ollama.com/quickstart, https://docs.ollama.com/api/openai-compatibility, https://lmstudio.ai/docs/developer/openai-compat, https://github.com/ggml-org/llama.cpp/tree/master/tools/server

## Candidates, not connected

An MCP server that exposes a local Ollama model to other MCP clients was considered and not added. See [the local AI guide](../docs/local-ai.md#why-there-is-no-local-model-as-an-mcp-server) for the candidates checked.

n8n orchestration, scoped database access, AWS and deployment integrations may be useful later. Add them only after selecting a concrete task, endpoint and permission boundary. No AI Vault inventory was available for this update; no integration is represented as imported from it.
