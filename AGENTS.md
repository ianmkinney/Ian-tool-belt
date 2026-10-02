# New belt instructions

This branch is a blank starter for a new owner. Do not assume it is Ian's personal belt or reuse credentials, account names or preferences from another project.

Read belt.json and rules/engineering.md before changes. Tailor tools and skills to the user's actual task. Check official sources for integration details. Keep tokens out of Git, preserve uncertainty, and do not call a declared connection authenticated or tested.

Use one task/session branch and PR; reuse a matching open PR. Write clear code with minimal intent-focused comments and meaningful tests for changed behavior. Inspect the latest head's CI and review feedback after every push, fix failures, and report concrete blockers. Use available sub-agents for independent tasks with isolated ownership. Do not promise unattended monitoring or merge without authorization.

Run `python3 scripts/validate.py belt.json`, `python3 -m unittest discover -s tests -v`, and both export targets to fresh directories before publishing format or exporter changes. Existing assistant configuration must never be overwritten automatically.
