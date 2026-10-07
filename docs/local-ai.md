# Local AI: getting started with Ollama

The belt declares one local model connection, `local-ai`, in `belt.json` under `models`. It speaks the OpenAI-compatible API, so any runtime with that API works. **Ollama is the recommended default.** LM Studio, llama.cpp and vLLM are alternative presets.

Nothing in this repository needs a local model to be running. Validation, exports, tests and CI never contact it. Only `scripts/local_ai_check.py` does, and only when you run it.

Install steps and model names below were checked against Ollama's documentation on 2026-10-07 UTC. Ollama changes often; if a step differs, follow [docs.ollama.com](https://docs.ollama.com/quickstart).

## 1. Install Ollama

**macOS** (Sonoma 14 or newer; Apple silicon uses the GPU, Intel Macs run on CPU only). Download `ollama.dmg` from [ollama.com/download](https://ollama.com/download), drag Ollama into Applications and open it. On first launch it offers to link the `ollama` command into `/usr/local/bin`.

**Windows** (Windows 10 22H2 or newer). Download and run `OllamaSetup.exe` from [ollama.com/download](https://ollama.com/download), or in PowerShell:

```powershell
irm https://ollama.com/install.ps1 | iex
```

It installs into your user account without administrator rights and runs in the background.

**Linux.**

```sh
curl -fsSL https://ollama.com/install.sh | sh
```

If the server is not already running as a service, start it with `ollama serve` in another terminal.

Confirm the CLI works on any platform:

```sh
ollama -v
```

## 2. Pull a first model

```sh
ollama pull gemma4:e2b
ollama run gemma4:e2b    # optional: chat in the terminal, /bye to leave
```

`gemma4:e2b` is the local model Ollama's quickstart uses. It is about a 7.2 GB download, and Ollama recommends 8 GB of available VRAM (or unified memory on a Mac). It is the belt's default because it is small enough to prove the setup works. It is not a recommendation for heavy agent work. Larger tags such as `gemma4:e4b` or `gemma4:12b` are listed on [ollama.com/library/gemma4](https://ollama.com/library/gemma4). Choose based on your hardware.

To change the belt's default model:

```sh
python3 scripts/belt_set.py belt.json models.local-ai.presets.ollama.model gemma4:e4b
```

Or override it for one shell session with `LOCAL_AI_MODEL=gemma4:e4b`.

## 3. Run the health check

From the belt checkout (Python 3.10+, no packages to install):

```sh
python3 scripts/local_ai_check.py           # is the endpoint up, and which models does it list?
python3 scripts/local_ai_check.py --chat    # also send one tiny chat request
```

| Exit code | Meaning |
| --- | --- |
| 0 | Endpoint reachable; the configured model is listed (and replied, with `--chat`) |
| 1 | Endpoint unreachable or returned an HTTP error. Is Ollama running? |
| 2 | Endpoint reachable, but the configured model is not pulled or loaded |
| 3 | Configuration error (unknown preset, unsafe URL) |

Add `--json` for machine-readable output, or `--preset lm-studio` to check another runtime. The API key is sent as a bearer token when set and is never printed.

## Configuration

The settings come from the selected preset in `belt.json`. These environment variables override them:

| Variable | Ollama default | Purpose |
| --- | --- | --- |
| `LOCAL_AI_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible base URL |
| `LOCAL_AI_MODEL` | `gemma4:e2b` | Model name as the runtime lists it |
| `LOCAL_AI_API_KEY` | empty | Optional. Ollama ignores it; set it only if your runtime requires one |

| Preset | Base URL | Model | Notes |
| --- | --- | --- | --- |
| `ollama` (default) | `http://localhost:11434/v1` | `gemma4:e2b` | [OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility) |
| `lm-studio` | `http://localhost:1234/v1` | set one | Start the local server in LM Studio; use the model identifier it shows |
| `llama-cpp` | `http://localhost:8080/v1` | set one | `llama-server` defaults to port 8080 |
| `vllm` | `http://localhost:8000/v1` | set one | `vllm serve` defaults to port 8000 |

Every export writes `local-ai.env.example` with these values. Copy them into your shell profile or an untracked `.env`. The repository ignores `.env` files.

Plain HTTP is accepted only for `localhost`, `127.0.0.1` and `::1`. Keep Ollama bound to your own machine. To reach a model on another computer, use an SSH tunnel to a local port or an HTTPS endpoint you control. Do not expose an unauthenticated model server to your network.

### Use it from a project's own code

Any OpenAI SDK works by changing the base URL. Ollama needs a non-empty key string but ignores its value:

```python
import os
from openai import OpenAI

client = OpenAI(base_url=os.environ.get("LOCAL_AI_BASE_URL", "http://localhost:11434/v1"),
                api_key=os.environ.get("LOCAL_AI_API_KEY") or "ollama")
reply = client.chat.completions.create(
    model=os.environ.get("LOCAL_AI_MODEL", "gemma4:e2b"),
    messages=[{"role": "user", "content": "Say hello in one sentence."}])
print(reply.choices[0].message.content)
```

## Hand the belt to the local model

A model alone cannot read files or call MCP tools. An **agent client** does that and uses the local model as its brain. The belt is loaded into the client, which then gives the model the belt's rules, skills and MCP connections. Ollama documents two such clients, and the belt exports for both.

### OpenCode (recommended for a fully local setup)

```sh
python3 scripts/export.py belt.json --target opencode --out dist/opencode
```

This produces:

- `opencode.json`: the belt's MCP connections; a `local-ai` provider using `@ai-sdk/openai-compatible` at the preset's base URL; the default model `local-ai/gemma4:e2b`; and `INSTRUCTIONS.md` as an instruction file
- `INSTRUCTIONS.md`: the belt's rules and a skill index
- `.opencode/skills/<name>/SKILL.md`: skills in a location OpenCode discovers natively

Review the files, then copy them into the target project's root. If the project already has an `opencode.json`, merge by hand. Install OpenCode as described in [Ollama's OpenCode guide](https://docs.ollama.com/integrations/opencode), then run `opencode` in the project. `ollama launch opencode` also works: it adds an inline model selection, and the project's `opencode.json` still applies. Use `--preset lm-studio` (after setting that preset's model) to target another runtime.

### Claude Code through Ollama

`ollama launch claude` runs Claude Code against a local model via Ollama's Anthropic-compatible API ([guide](https://docs.ollama.com/integrations/claude-code)). Use the belt's existing `claude-code` export (`.mcp.json`, `INSTRUCTIONS.md`, `skills/`) in that project and ask the assistant to read `INSTRUCTIONS.md`.

### What to expect

- **Context length.** Agent clients need a large context window. Ollama defaults to 4k tokens below 24 GiB of VRAM. Ollama's guides ask for 64k or more for coding agents. Set this with the slider in the Ollama app, or with `OLLAMA_CONTEXT_LENGTH=64000 ollama serve`. Confirm with `ollama ps`. A larger context needs more memory.
- **Tool calling.** Using MCP connections requires a model that supports tool calls, and small models follow multi-step skills less reliably than hosted ones. Treat each skill as untested on a local model until you have tried it.
- **Credentials.** MCP connections still need their own environment variables (for example `GITHUB_MCP_TOKEN`). Running the model locally does not make hosted MCP services local.

None of this has been run end to end in this repository yet; there is no local runtime here. The export structure is unit-tested. The live path is a roadmap item.

## Why there is no "local model as an MCP server"

We looked for a well-maintained MCP server that exposes Ollama to other MCP clients, such as Cursor calling a local model as a tool. Ollama does not publish an official one. On 2026-10-07 the community options were `ask-ollama-mcp` (single maintainer, about 130 weekly downloads), `ollama-mcp` (AGPL-3.0, last release November 2025) and a few forks. None met the bar of official provenance or broad, active maintenance, so none is declared. The supported direction is the reverse: the local model drives a client that uses the belt's MCP connections. To revisit this, run the `evaluate-mcp` skill on a specific candidate.
