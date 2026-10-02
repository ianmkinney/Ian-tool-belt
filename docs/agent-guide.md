# How another agent uses Tool Belt

**Give the agent access to the files, ask it to load the belt, and verify which tools its host actually exposes.** Tool Belt currently packages configuration and instructions. Cloning it does not automatically install connections, import skills or change an assistant's system prompt.

## Copy this prompt into your agent

Replace the bracketed values with the two real paths and a concrete task:

> Use the Tool Belt repository at [BELT_PATH] for this task in [PROJECT_PATH]: [TASK]. First read AGENTS.md and belt.json, then read every referenced rules file. Inspect the listed skill descriptions and load only the skill relevant to this task. Check which tools your host actually provides; do not assume declared MCP connections are active. Follow the project's own instructions, keep credentials out of Git and chat, and report any missing capabilities. For code changes, use one session PR, test changed behavior, and check CI on its latest head. Use sub-agents for independent work if supported. Begin by reporting the selected skill and which tools are available, then carry out the authorized task.

The belt repository and the project being changed can be different folders. Open the PR in the target project; use a belt PR only when editing the belt itself.

## Choose your access route

| What the agent has | What to do | What that enables |
| --- | --- | --- |
| Local clone and file access | Read AGENTS.md, belt.json, referenced rules, then the selected SKILL.md | Apply instructions; local validation/export if Python is available |
| Authorized GitHub integration | Fetch the actual files at a chosen branch/commit and follow the same reading order | Apply instructions; repository operations allowed by that integration |
| Exported client bundle | Read INSTRUCTIONS.md and compatibility.json, then a listed skill | Apply bundled rules and manually load skills; review client configuration |
| Chat-only file attachments | Attach rules, the relevant skill and task files; explain the task | Advice and drafts within host capabilities; no new MCP access |

A GitHub URL alone is not enough if the agent cannot retrieve its contents. A client may automatically recognize AGENTS.md, but do not depend on that: explicitly ask it to read the file.

## Source repository reading order

1. **AGENTS.md:** identity, project decisions and contribution requirements.
2. **belt.json:** the manifest; paths are relative to its directory.
3. **All referenced rules:** startup, working agreement and engineering/PR contract.
4. **Skill descriptions:** choose the workflow matching the task, then read its full instructions.
5. **Connection catalog and setup:** read these when a needed tool is absent or setup is requested.

The portable [startup protocol](../rules/agent-start.md) is also included in every newly generated export. The exporter copies only manifest-listed skills, not the entire repository. It combines rule text into INSTRUCTIONS.md and emits a compatibility report.

## Example: use the existing belt for API work

From a terminal with Git and Python 3.10+:

```sh
git clone https://github.com/ianmkinney/Ian-tool-belt.git tool-belt
cd tool-belt
python3 scripts/validate.py belt.json
python3 -m unittest discover -s tests -v
```

Ask your agent:

> Use the belt in this folder to add input validation to the API in ../my-app. Read the startup instructions, select build-api-slice, inspect the app's existing tests, and implement one reviewable change. Do not deploy. Report whether GitHub and documentation tools come from your host or from a configured belt connection.

For this example, the agent reads `skills/build-api-slice/SKILL.md`. It checks the application's installed framework version before retrieving documentation. GitHub's profile in this belt is read-only, so PR creation needs an existing authorized write-capable integration or separately configured write access. Never silently broaden a token to satisfy the PR workflow.

## Optional: configure a supported client

Generate only the target you use, into a new directory:

```sh
python3 scripts/export.py belt.json --target claude-code --out dist/claude-code
# Or:
python3 scripts/export.py belt.json --target vscode --out dist/vscode
```

Review the generated `.mcp.json` or `.vscode/mcp.json`. Merge relevant entries into the target project's configuration through the client's documented setup flow; preserve its existing entries. The exporter deliberately refuses to overwrite an existing output directory. For a second export, choose a fresh path, such as `dist/claude-code-v2`.

Supply the required environment variables securely to the client process. The exporter does not read credentials or `.env` files. Follow the host's trust/authentication prompts, discover available tools, and run a harmless authorized check. See [setup](setup.md) and the [connection catalog](../connections/README.md) for prerequisites and official documentation.

Then give the agent this prompt:

> Read [EXPORT_PATH]/INSTRUCTIONS.md and compatibility.json. Choose and read a relevant skill from the paths listed in INSTRUCTIONS.md. Use only tools actually exposed by this client. Apply the rules to [TASK] in [PROJECT_PATH], and report unsupported capabilities accurately.

Do not copy this bundle into an arbitrary host's internal skill directory and assume it is installed. Native skill discovery is a future adapter feature. ChatGPT has no connection exporter in this prototype; attached instructions or repository access can still be useful, but they do not add tools.

## Agent readiness checklist

Before doing the task, the agent should be able to answer:

- Which belt files or commit did I actually read?
- Which rules apply, and which skill fits this task?
- Which tools does my host expose, and which connections are only declarations?
- Is setup needed, and is the necessary authorization available?
- Which repository/branch/PR owns the work?

Before reporting completion, identify the tests and live calls that actually ran, latest-head CI status, review blockers and any client features not verified. One brief status statement is enough; do not turn the checklist into repetitive narration.

## Troubleshooting

| Symptom | Meaning and next step |
| --- | --- |
| Agent cannot read the repository | Provide an authorized file route or attach the relevant files |
| A listed tool is missing | Inspect host setup; the manifest does not activate it |
| GitHub tool cannot create a PR | This belt uses a read-only endpoint; use separately authorized write access |
| Export reports directory exists | Use a new output path; do not delete unrelated configuration |
| Rules seem ignored | Explicitly load INSTRUCTIONS.md or the referenced source rules; host policies still take precedence |
| Skill is not discovered automatically | Explicitly load its SKILL.md; native discovery is not configured |
| No sub-agent capability | Run the workflow sequentially; do not invent delegation |
| Need a blank belt | Use the separate [template branch](https://github.com/ianmkinney/Ian-tool-belt/tree/template); it has no connections or skills initially |

Changes in this main-branch guide do not automatically update the separate template branch.
