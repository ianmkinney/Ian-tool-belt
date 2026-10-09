# Draft 0.3 design

The root belt.json is our working profile. The original examples/personal/belt.json remains a valid minimal 0.1-draft example, and 0.2-draft manifests still validate.

## Manifest fields

`formatVersion`, `name`, `version`, `description`, `rules`, `skills`, `servers`, `adapters`, and `secretRefs` are required in every version. 0.3-draft also requires `models`, `packages` and `personalServers` (each may be empty). Rules and skills are relative file paths within the belt directory. Skills point to SKILL.md files whose `name` matches their folder, as Cursor and OpenCode require. HTTP servers declare an HTTPS URL and an optional headersFromEnv mapping header names to an environment variable and prefix. Stdio servers declare an executable and argument list. The validator never executes them.

Statuses are declarations: needs-credentials, needs-local-setup or untested. They are not inferred authentication state. Secret references contain environment variable names only. Arbitrary literal authentication headers are not part of this format.

### Personal servers

`personalServers` uses the server schema for connections outside work. Ids must be unique across `servers` and `personalServers`. Exporters omit personal servers unless `--include-personal` is passed, and the compatibility report states which happened.

### Models

A model entry describes an OpenAI-compatible endpoint: `id`, `api` (`openai-compatible`), `env` (the variable names for base URL, model and API key; the key variable must be in `secretRefs`), named `presets` (each with `baseUrl`, `model` and a `docs` HTTPS link), a `defaultPreset` and a `status`. Preset URLs may use plain HTTP only for loopback hosts. An empty preset model means "set one before use". Models are not MCP servers and are never contacted by validation or export. See [local AI](local-ai.md).

### Packages

A package is something reusable the belt ships or pins. `npm` and `pypi` packages declare a registry `name` and an exact `version` pin; ranges are rejected. If a stdio server argument installs an npm package (`name@version`), it must use the package's pin, so a bump changes one value. Workflows read pins from `belt.json` too: the zizmor lint takes its version from the `zizmor` pypi package, the actionlint job takes its version from the `actionlint` pypi package (`actionlint-py`), and the shellcheck job (and actionlint's `run:` checks) take theirs from the `shellcheck` pypi package (`shellcheck-py`). `files` packages point to a folder inside the belt containing a README.md and carry their own version. `scripts/new.py` scaffolds both skills and packages and registers them.

## Adapters

The exporter translates connection declarations for Claude Code, VS Code, Cursor and OpenCode. It keeps secret references symbolic in each client's interpolation syntax, copies skill folders (regular files only; symlinks are skipped), and emits a compatibility report. Unsupported or undeclared targets fail before anything is written. Output directories must not already exist; the exporter never merges client configuration automatically.

| Target | Connections | Rules | Skills | Local model |
| --- | --- | --- | --- | --- |
| claude-code | `.mcp.json` | `INSTRUCTIONS.md`, loaded manually | `skills/<name>/` | env example only |
| vscode | `.vscode/mcp.json` | `INSTRUCTIONS.md`, loaded manually | `skills/<name>/` | env example only |
| cursor | `.cursor/mcp.json` | `.cursor/rules/*.mdc` (`alwaysApply: true`) and `INSTRUCTIONS.md` | `.cursor/skills/<name>/` | env example only |
| opencode | `opencode.json` `mcp` | `INSTRUCTIONS.md` via `instructions` | `.opencode/skills/<name>/` | `local-ai` provider and default model |

Cursor and OpenCode outputs use locations those clients document for native loading. This is labeled `native-locations-generated-untested` until verified in a live client.

## Future runtime

A later gateway may expose multiple servers through one endpoint. It must independently enforce authorization and credential isolation. Prose rules and skill instructions are not access controls. Composed belts need conflict reporting and restrictions that child belts cannot widen. None of this runtime behavior is implemented yet.

## Reproducibility and trust

A fixed executable package version reduces drift but is not a complete dependency lock. The weekly pin check proposes newer stable releases as pull requests; a human still reviews release notes. Future lockfiles must capture dependency hashes and client versions. Hosted services can change independently. Reproducible configuration does not imply identical model outputs, and local models vary by hardware, quantization and context length.

Verification records must distinguish official provenance, local validation, authentication, live tool invocation and client behavior. A future marketplace must publish precisely what was checked and when.
