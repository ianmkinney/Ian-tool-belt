# Connection catalog

Configured here means declared in the manifest. No credentials have been supplied. Only the [smoke test](#smoke-test-a-connection) below has opened live MCP sessions, outside any assistant client; client sessions remain untested.

| Connection | Why it belongs | Setup | Current evidence |
| --- | --- | --- | --- |
| GitHub official MCP | Repository inspection and PR context | Set GITHUB_MCP_TOKEN in the launching client's environment with minimum required repo access | Official endpoint documented; read-only URL selected; authentication untested |
| Context7 by Upstash | Documentation for the actual libraries in a project | Set CONTEXT7_API_KEY in the launching client's environment | Official endpoint/header documented; smoke-test `tools/list` over HTTP answered (2 tools) with a placeholder key on 2026-10-07, so reachability is shown but authentication is untested |
| Playwright by Microsoft | UI regression checks and browser workflows | Install Node.js and required browser/runtime dependencies | Smoke test on 2026-10-07 (Linux, Node 22.23): 0.0.83 installed from npm, listed 25 tools, `browser_tabs` `{"action":"list"}` returned `about:blank`; untested in an assistant client |

## Smoke-test a connection

`scripts/mcp_smoke.py` runs the pinned [MCP Inspector](https://github.com/modelcontextprotocol/inspector) (`mcp-inspector` in `packages`) in CLI mode against one server from `belt.json`. It lists the server's tools and, with `--call`, makes one named call. Choose only read-only, repeatable tools. It needs Node.js 22.19 or newer; `npx` downloads the pinned Inspector and the server package on first use.

```sh
python3 scripts/mcp_smoke.py playwright
python3 scripts/mcp_smoke.py playwright --call browser_tabs --args '{"action":"list"}'
GITHUB_MCP_TOKEN=... python3 scripts/mcp_smoke.py github
```

Credentials come only from the variables named in `headersFromEnv`. A server whose variables are unset is skipped with a message and exit code 0. Values are never printed and are redacted from relayed output, but a header is passed to the Inspector as a command-line argument, so it is visible in the local process list while the run lasts. Each run uses a temporary Inspector storage directory, a memory-only secret store and `--stored-auth-only`, so it neither reads your stored OAuth tokens nor waits on a browser login.

A passing run shows that the server starts and answers MCP. It does not show that a given assistant client loads the server, and a pass with a credential that the server never checks is not evidence of authentication. Record the date, versions and observed result in the table above.

## Local AI model

| Connection | Why it belongs | Setup | Current evidence |
| --- | --- | --- | --- |
| `local-ai` (OpenAI-compatible) | A private model on Ian's own computer for agent clients and project code | Install Ollama (default preset) or another runtime; optional `LOCAL_AI_BASE_URL`, `LOCAL_AI_MODEL`, `LOCAL_AI_API_KEY`. See [local AI guide](../docs/local-ai.md) | Presets match runtime documentation; health check unit-tested against a stub server; no local runtime has been exercised by this project |

This is a model endpoint, not an MCP server. It is declared under `models` in `belt.json`. Agent clients such as OpenCode, Claude Code or [ollmcp](../docs/local-ai.md#ollmcp-ollama-native-terminal-client) use it as their model and the belt's MCP connections as their tools. No local runtime is installed yet; Ollama is the recommendation. ollmcp is pinned in `packages` and is not started by validation, export or CI.

## Work connections

GitHub starts read-only. This declaration does not reuse ChatGPT's connected GitHub credentials. Enabling writes is a separate intentional configuration change. Restrict repository access in the token itself.

The Context7 profile uses a key even if the service also permits limited unauthenticated usage. Never put source secrets or private customer data in documentation queries.

Playwright uses an isolated, headless browser. Isolation here means a temporary browser profile, not a security sandbox. No existing personal browser session is attached. A fixed npm package version is not a complete transitive dependency lock or supply-chain verification. Verify package availability before first use.

## Personal connections (outside work)

`personalServers` in `belt.json` holds MCP connections for personal life rather than work: for example, a notes app, a calendar or a home service. It uses exactly the same schema as `servers`. It is **empty** until Ian chooses services; none are assumed.

Exports leave personal connections out by default, so dropping the belt into a work or client project never carries them along. Include them only where they belong:

```sh
python3 belt.py use cursor --out dist/cursor-personal --include-personal
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

Smoke-test tool sources, checked 2026-10-07 UTC: https://github.com/modelcontextprotocol/inspector (README, `clients/cli/README.md`, `docs/cli-smoke-testing.md`, `docs/secret-storage.md`, LICENSE), https://registry.npmjs.org/@modelcontextprotocol/inspector

Local AI sources, checked 2026-10-07 UTC: https://docs.ollama.com/quickstart, https://docs.ollama.com/api/openai-compatibility, https://lmstudio.ai/docs/developer/openai-compat, https://github.com/ggml-org/llama.cpp/tree/master/tools/server

ollmcp sources, checked 2026-10-08 UTC: https://github.com/jonigl/mcp-client-for-ollama (README at v0.35.1, LICENSE MIT, `mcp_client_for_ollama/server/discovery.py` and `connector.py` for `--servers-json` and header handling), https://pypi.org/pypi/ollmcp/0.35.1, https://pypi.org/pypi/mcp-client-for-ollama/0.35.1

## Candidates, not connected

An MCP server that exposes a local Ollama model to other MCP clients was considered and not added. See [the local AI guide](../docs/local-ai.md#why-there-is-no-local-model-as-an-mcp-server) for the candidates checked.

n8n orchestration, scoped database access, AWS and deployment integrations may be useful later. Add them only after selecting a concrete task, endpoint and permission boundary. No AI Vault inventory was available for this update; no integration is represented as imported from it.
