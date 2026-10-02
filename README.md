# Your Tool Belt

**Start empty. Build your own workshop.**

This template starts with no MCP connections, credentials, personal context or installed skills. It includes a manifest, a validator, configuration exporters and reusable engineering instructions. Connection exports for the empty belt are intentionally empty.

## Start your own repository

```sh
git clone --branch template --single-branch https://github.com/ianmkinney/Ian-tool-belt.git my-tool-belt
cd my-tool-belt
git remote remove origin
git branch -m main
```

Create your own empty GitHub repository. Replace YOUR_ACCOUNT and YOUR_REPOSITORY below with its real names, then push:

```sh
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

The template branch shares the source repository's public commit history. For a fresh history, download the branch archive, extract it, run `git init -b main`, then add and commit the files before adding your own remote. GitHub's repository-level “Use this template” button is not enabled by this branch alone.

## Start prompting

Open the folder in your coding assistant and use this prompt:

> Read AGENTS.md and belt.json. Help me build my tool belt for [describe my work]. Ask only for missing details that change the setup. Propose a small set of officially documented MCP connections and original skills. Keep credentials symbolic and report what remains untested. Validate and test changes, and keep one session PR green using rules/engineering.md. Use sub-agents for independent work if your host supports them.

## Validate and export

Python 3.10+ is required. No third-party Python dependencies are needed.

```sh
python3 scripts/validate.py belt.json
python3 -m unittest discover -s tests -v
python3 scripts/export.py belt.json --target claude-code --out dist/claude-code
python3 scripts/export.py belt.json --target vscode --out dist/vscode
```

Exports go to new directories only. Merge generated connection configuration through your client's documented setup flow. Explicitly load INSTRUCTIONS.md and relevant skills; native skill discovery is not configured. Client authentication and live compatibility tests remain your setup tasks. Neither export creates a gateway or installs anything into ChatGPT.

## Add a connection

Use HTTPS for remote MCP. Add secret variable names to secretRefs and map headers through headersFromEnv; never write actual tokens into files. For example, after checking official provider documentation:

```json
{
  "id": "example",
  "transport": "http",
  "url": "https://example.com/mcp",
  "headersFromEnv": {
    "Authorization": {"env": "EXAMPLE_TOKEN", "prefix": "Bearer "}
  },
  "status": "needs-credentials"
}
```

The URL above is illustrative, not a working service. Add original skills in `skills/<name>/SKILL.md` with name and description frontmatter, and reference them from belt.json. Rules and skills must remain within this directory.

MIT licensed. Tool Belt project: https://github.com/ianmkinney/Ian-tool-belt
