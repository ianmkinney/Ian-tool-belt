# Draft design

## Belt package

A belt contains a versioned manifest, relative instruction files, skill references, connection declarations, and adapter declarations. The example intentionally contains no live server or credential. The initial validator accepts only this minimal subset; populated integration arrays require a later schema revision.

Credentials belong in a local or hosted secret store, never the belt repository. A future secret reference names a required credential without embedding its value. Installing a belt must not automatically execute downloaded code.

## Adapters

An adapter targets a specific client and supported version range. It produces that client's configuration, an instruction delivery mechanism, and a compatibility report. Reports distinguish supported, degraded, unsupported, and untested features. Unsupported required capabilities must fail compilation. Adapters do not bypass provider rules or imply all clients accept remote MCP or native skills.

Start with two clients selected after verifying their current official integration documentation. Keep generated outputs separate from manually maintained client settings. Do not overwrite existing configuration without a reviewed merge.

## Runtime

A later gateway may present selected downstream MCP tools through one endpoint. Instructions, executable scripts, and tool calls are separate capabilities. Scripts need a controlled execution environment. OAuth connections remain per-user and per-service; never forward arbitrary caller tokens to upstream services.

## Composition and permissions

Personal, company, and project belts are a future design target. Explicitly report rule conflicts. Enforce company restrictions in the runtime authorization layer; prose instructions alone cannot enforce them. A child belt cannot expand permissions granted by its parent. Keep credential namespaces isolated between clients and organizations.

## Reproducibility

Future lockfiles pin dependency versions and content hashes. This reproduces configuration and dependency bytes, not model outputs or remote service behavior. Changes should be reviewable through Git diffs and reversible by version rollback.

## Marketplace verification

Defer marketplace implementation. Future verification must state what was checked, against which version, when, and by whom. Separate publisher identity, dependency inspection, execution tests, and client compatibility. A verification badge must not imply universal safety.
