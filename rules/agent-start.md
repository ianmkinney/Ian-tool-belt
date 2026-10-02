# Agent startup protocol

Use this protocol when another agent is asked to use a belt. It describes how to load guidance and discover available capabilities; it does not install tools or grant permissions.

## 1. Establish access and scope

Identify the requested task, target project and client. If you have the source repository, read AGENTS.md, belt.json and every file listed in its rules array. Resolve manifest paths relative to the directory containing belt.json. If you have an exported bundle, read this INSTRUCTIONS.md and compatibility.json; it already contains the shared rules. Preserve the target project's own instructions and the host's higher-priority policies.

If you only have a repository link, fetch the actual files through an authorized repository integration or ask for the relevant files. Do not claim to have loaded a belt from its name, README summary or URL alone. If files, execution or MCP are unavailable, state that limitation and continue with the guidance you can actually read.

## 2. Select the workflow

For the source belt, inspect the name and description frontmatter of the SKILL.md files listed in belt.json. For an export, use the relative skill paths listed below in INSTRUCTIONS.md. Read the full body of the skill that matches the task; do not load all skills by default. If none fits, use the shared rules and the project's existing workflow. A skill is guidance, not an executable capability or a permission grant.

## 3. Check tools before using them

Inspect the host's actual available tools and match them to the task. A manifest entry is a connection declaration, not a live session. Do not invent a tool name or assume a provider-specific name is identical across clients. Prefer an existing authorized host integration where it satisfies the task; record that it is host-provided, not authenticated by this belt.

If setup is requested and supported, validate and export a reviewed configuration into a new directory, then use the client's documented trust and connection process. Keep secret references symbolic and use the client's secure credential flow or environment. Never ask for tokens in chat or place them in Git. Confirm tool discovery and a harmless authorized call before calling the connection verified. No exporter currently connects ChatGPT or aggregates tools through a gateway.

## 4. Execute and verify

Apply the selected skill and shared engineering rules to the target project. When changing code, inspect its branch and PR state; open one new session PR or reuse the matching open PR. Delegate independent work only when the host provides sub-agents, with explicit ownership and a return contract. Keep test fixes and review follow-ups on the same PR. Track CI against the latest head while the session is active.

## 5. Report observable state

State the belt or commit read, skill selected, tool source, changes made, tests actually run and outstanding setup or review blockers. Distinguish declared, configuration-generated, tool-discovered and live-call-verified states. Do not imply a changed declaration or successful export proves authentication, permission enforcement or cross-assistant compatibility. Do not promise automatic loading or monitoring after the session ends.
