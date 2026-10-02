# Connection catalog

Agents: follow the [startup guide](../docs/agent-guide.md) before using these profiles. Discover the host's actual tools; these declarations do not activate services.

Configured here means declared in the manifest. No credentials have been supplied and no live MCP session has been tested by this project.

| Connection | Why it belongs | Setup | Current evidence |
| --- | --- | --- | --- |
| GitHub official MCP | Repository inspection and PR context | Set GITHUB_MCP_TOKEN in the launching client's environment with minimum required repo access | Official endpoint documented; read-only URL selected; authentication untested |
| Context7 by Upstash | Documentation for the actual libraries in a project | Set CONTEXT7_API_KEY in the launching client's environment | Official endpoint/header documented; authentication untested |
| Playwright by Microsoft | UI regression checks and browser workflows | Install Node.js and required browser/runtime dependencies | Package version 0.0.83 appears in upstream package.json; registry installation and execution untested |

GitHub starts read-only. This declaration does not reuse ChatGPT's connected GitHub credentials. Enabling writes is a separate intentional configuration change. Restrict repository access in the token itself.

The Context7 profile uses a key even if the service also permits limited unauthenticated usage. Never put source secrets or private customer data in documentation queries.

Playwright uses an isolated, headless browser. Isolation here means a temporary browser profile, not a security sandbox. No existing personal browser session is attached. A fixed npm package version is not a complete transitive dependency lock or supply-chain verification. Verify package availability before first use.

## Official sources checked 2026-10-02 UTC

- https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md
- https://github.com/github/github-mcp-server/blob/main/docs/server-configuration.md
- https://github.com/upstash/context7/blob/master/packages/mcp/README.md
- https://github.com/microsoft/playwright-mcp/blob/main/README.md
- https://github.com/microsoft/playwright-mcp/blob/main/package.json

## Candidates, not connected

n8n orchestration, scoped database access, AWS and deployment integrations may be useful later. Add them only after selecting a concrete task, endpoint and permission boundary. No AI Vault inventory was available for this update; no integration is represented as imported from it.
