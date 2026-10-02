# Draft 0.2 design

The root belt.json is our working profile. The original examples/personal/belt.json remains a valid minimal 0.1-draft example.

## Manifest fields

`formatVersion`, `name`, `version`, `description`, `rules`, `skills`, `servers`, `adapters`, and `secretRefs` are required. Rules and skills are relative file paths within the belt directory; skills point to SKILL.md files. HTTP servers declare an HTTPS URL and optional headersFromEnv mapping header names to an environment variable and prefix. Stdio servers declare an executable and argument list. The validator never executes them.

Statuses are declarations: needs-credentials, needs-local-setup or untested. They are not inferred authentication state. Secret references contain environment variable names only. Arbitrary literal authentication headers are not part of this format.

## Adapters

The exporter translates connection declarations for Claude Code and VS Code, keeps secret references symbolic, copies portable skills, and emits a compatibility report. Unsupported targets fail. Instruction loading is manual and explicitly reported. Output directories must not already exist; the exporter never merges client configuration automatically.

## Future runtime

A later gateway may expose multiple servers through one endpoint. It must independently enforce authorization and credential isolation. Prose rules and skill instructions are not access controls. Composed belts need conflict reporting and restrictions that child belts cannot widen. None of this runtime behavior is implemented yet.

## Reproducibility and trust

A fixed executable package version reduces drift but is not a complete dependency lock. Future lockfiles must capture dependency hashes and client versions. Hosted services can change independently. Reproducible configuration does not imply identical model outputs.

Verification records must distinguish official provenance, local validation, authentication, live tool invocation and client behavior. A future marketplace must publish precisely what was checked and when.
