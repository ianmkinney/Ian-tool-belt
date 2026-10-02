# Our workflow skills

Agents: start with the [agent guide](../docs/agent-guide.md), inspect each manifest-listed skill's description, and read the full body only when it matches the task.

These are original, repository-contained instruction packages, not copies of system or plugin skills. They are not installed into your ChatGPT account by being committed here.

| Skill | Example task |
| --- | --- |
| build-api-slice | Ship one backend-to-frontend feature in the existing stack |
| reconcile-data | Reconcile Postgres/Snowflake exports and spreadsheet results |
| verify-browser-flow | Reproduce and verify a web user journey |
| evaluate-mcp | Check provenance, permissions and compatibility of a proposed tool |

Each folder contains a portable SKILL.md with name and trigger description. Read only the skill needed for the current task. The exporter includes copies under `skills/`; import them through your client's documented skill mechanism or explicitly attach the relevant file. Automatic discovery is not configured by this prototype.

Skills guide behavior; they do not grant permissions or enforce runtime policy. Their metadata is validated, but their effectiveness has not been benchmarked across assistants.
