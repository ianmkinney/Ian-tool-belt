---
name: evaluate-mcp
description: Evaluate an MCP server or skill for inclusion in Tool Belt. Use for AI Vault candidates, marketplace submissions, connection changes and assistant compatibility reviews.
---

# Evaluate an MCP candidate

1. Obtain the exact official repository or documentation URL. If an AI Vault item is referenced without a resolvable source, ask for the link and label provenance unknown.
2. Identify maintainer, license, transport, release/version, authentication, requested permissions, data destinations, installation requirements and update mechanism from primary sources.
3. Compare the tool to a concrete belt task. Prefer a narrow useful integration to a large untested catalog. Record alternatives and the reason for selection.
4. Separate provenance checked, configuration validated, authenticated and live-tested statuses. Never translate official ownership into a blanket safety claim.
5. Use placeholders or environment-variable references for secrets. Do not install or execute repository scripts merely to inspect them.
6. Propose a minimal scoped connection, an observable smoke test and an uninstall/rollback path. For the smoke test, from the belt repository run `python3 scripts/mcp_smoke.py <server-id>` to list tools, then add `--call <tool> --args '<json>'` for one read-only call. Record the date, versions and output. A skipped run (credentials unset) is not a test, and a pass is server evidence, not client compatibility. Pin executable package versions after verifying availability; record that hosted endpoints can change independently.
7. Update connections/README.md and the manifest only within the authorized task. Mark client compatibility untested until exercised in that client.

Example request: Assess a candidate from an AI tools directory before adding it to our belt.
