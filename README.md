# Tool Belt

Portable AI workspaces, defined as code.

Tool Belt is an early open-source project for packaging MCP connections, instructions, skills, and assistant adapters into reproducible, versioned repositories. Bring your configuration to compatible assistants without maintaining each integration separately.

**Status: specification starter.** This repository does not yet provide a gateway, working assistant adapters, a marketplace, or a demonstrated cross-assistant runtime.

## Starting point

- `examples/personal/belt.json`: proposed manifest format
- `examples/personal/rules.md`: example portable instructions
- `docs/design.md`: boundaries, adapters, permissions, and reproducibility
- `docs/roadmap.md`: first proof and subsequent milestones
- `scripts/validate.py`: dependency-free structural validator for this draft

Requires Python 3.10 or newer. From the repository root:

```sh
python3 scripts/validate.py examples/personal/belt.json
```

## First proof

Use one belt with two explicitly supported AI clients. Update its shared instructions and regenerate both configurations. Verify that both clients can discover the same sample tool and retrieve the updated instructions. Document differences; configuration portability is not a guarantee of identical model behavior.

## Open development

The local format and runner are intended to remain free and open source. Education, implementation services, hosted execution, and organization features are possible future ways to sustain development. No paid service is implemented or promised.

Licensed under MIT. Contributions and design feedback are welcome; see CONTRIBUTING.md.
