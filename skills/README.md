# Our workflow skills

These are original, repository-contained instruction packages, not copies of system or plugin skills. They are not installed into your ChatGPT account by being committed here.

| Skill | Example task |
| --- | --- |
| build-api-slice | Ship one backend-to-frontend feature in the existing stack |
| reconcile-data | Reconcile Postgres/Snowflake exports and spreadsheet results |
| verify-browser-flow | Reproduce and verify a web user journey |
| evaluate-mcp | Check provenance, permissions and compatibility of a proposed tool |
| break-room | Use the shared break room board each turn on the team box |

Each folder contains a portable SKILL.md with name and trigger description. Read only the skill needed for the current task. The exporter includes copies under `skills/`; import them through your client's documented skill mechanism or explicitly attach the relevant file. Automatic discovery is not configured by this prototype.

The Cursor and OpenCode exports place skills in `.cursor/skills/` and `.opencode/skills/`, where those clients discover them natively. That discovery has not yet been confirmed in a live client.

## Add a skill

```sh
python3 belt.py add skill review-sql --description "Review SQL changes. Use when a migration or query changes."
```

This creates `skills/review-sql/SKILL.md` from a template, registers it in `belt.json` and validates the belt. Then replace the template steps with your own, add a row to the table above, and add supporting files under `scripts/`, `references/` or `assets/` in the skill folder if needed; exports copy them. Write original instructions with synthetic examples.

Skills guide behavior; they do not grant permissions or enforce runtime policy. Their metadata is validated, but their effectiveness has not been benchmarked across assistants.
