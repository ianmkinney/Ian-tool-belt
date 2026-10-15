# llm CLI for the local model

[llm](https://github.com/simonw/llm) (Apache-2.0, [LICENSE](https://github.com/simonw/llm/blob/0.36/LICENSE)) is Simon Willison's command-line tool for sending one prompt to a model. The belt pins **0.36**, the PyPI release of package `llm` and the GitHub tag `0.36` (published 2026-09-22, Python 3.10+). Docs: [llm.datasette.io](https://llm.datasette.io/). Changelog: [release 0.36](https://github.com/simonw/llm/releases/tag/0.36).

Use it when you want to pipe a file, a diff, or a question into the belt's `local-ai` model from a shell or a script. It is not an MCP server and it does not load the belt's tools. [ollmcp](local-ai.md#ollmcp-ollama-native-terminal-client), OpenCode and Claude Code are the clients that do that. Nothing in CI installs llm or requires a running model.

Checked 2026-10-15 UTC against the PyPI `0.36` metadata (`license_expression` Apache-2.0, `requires_python` >=3.10), the GitHub release `0.36` (not a prerelease), the tag's LICENSE and README, and the [endpoint docs](https://llm.datasette.io/en/stable/other-models.html#openai-endpoint).

## Install

The version comes from the `llm` pypi package in `belt.json`. Install that pin when you want the CLI. The belt does not install it for you.

```sh
python3 -m pip install 'llm==0.36'
```

`uv tool install 'llm==0.36'` is the same pin. `llm-ollama` is optional. This guide does not use it. `llm openai endpoint` talks to any OpenAI-compatible base URL, which is what every `local-ai` preset already is.

## Point it at the local-ai preset

`scripts/llm_local.py` reads the same settings as `scripts/local_ai_check.py`: `LOCAL_AI_BASE_URL`, `LOCAL_AI_MODEL` and `LOCAL_AI_API_KEY`, falling back to the preset in `belt.json`. The default preset is `ollama` at `http://localhost:11434/v1` with model `gemma4:e2b`. The helper does not contact the model and does not print an API key.

```sh
python3 scripts/llm_local.py "Reply with the single word: ready"
python3 scripts/llm_local.py --print "Reply with the single word: ready"
LOCAL_AI_MODEL=google/gemma-4-12b python3 scripts/llm_local.py --preset lm-studio "Say hello in one sentence."
```

`--print` shows the command and exits. A set API key appears as `$LOCAL_AI_API_KEY`, not the value. `--preset` selects `ollama`, `lm-studio`, `llama-cpp` or `vllm` from `belt.json`. Environment variables still override that preset. `lm-studio`, `llama-cpp` and `vllm` have an empty model until you set `LOCAL_AI_MODEL` or the preset's model. The helper stops before calling llm in that case.

The command underneath, with the ollama defaults filled in:

```sh
llm openai endpoint "${LOCAL_AI_BASE_URL:-http://localhost:11434/v1}" \
  -m "${LOCAL_AI_MODEL:-gemma4:e2b}" \
  "Reply with the single word: ready"
```

That is the form in the llm 0.36 README (`llm openai endpoint http://localhost:1234/v1 -m <model> "prompt"` pointed at LM Studio). Add `--chat` for an interactive session. Add `--models` to list the ids the endpoint advertises. Ollama must already be running and the model must already be pulled; this repository does not do either.

## Examples

Ask a question:

```sh
python3 scripts/llm_local.py "What does the belt fpr skill do? Answer in one sentence."
```

Summarize a file. The instruction is a system prompt (`-s`); the file is stdin:

```sh
python3 scripts/llm_local.py -s "Summarize this file in a few bullets" < notes.md
```

Summarize a diff:

```sh
git diff | python3 scripts/llm_local.py -s "Summarize this diff for a reviewer"
```

`llm openai endpoint` joins piped stdin with a prompt argument, stdin first. Prefer `-s` for the instruction so the file stays the prompt.

## Privacy

`llm openai endpoint` does not log the prompt or the response, and it does not send a stored OpenAI API key. The helper uses that command. See [Run against an endpoint without configuring it](https://llm.datasette.io/en/stable/other-models.html#openai-endpoint).

Other `llm` commands log prompts and responses to SQLite by default. Find the file with `llm logs path`. On macOS the docs show `~/Library/Application Support/io.datasette.llm/logs.db`. On Linux the directory is often `~/.config/io.datasette.llm/`. Turn logging off with `llm logs off`. Skip one logged prompt with `--no-log` or `-n`. Turn logging back on with `llm logs on`. `llm logs status` shows the current setting. Details: [Logging to SQLite](https://llm.datasette.io/en/stable/logging.html) and [turning logging on and off](https://llm.datasette.io/en/stable/setup.html#turning-sqlite-logging-on-and-off).

The helper adds `--key` only when `LOCAL_AI_API_KEY` is set. It never writes that value into the repo, into `--print` output, or into an error message. Ollama ignores the key, so the default preset does not send one. A key that is passed to llm is visible in the process list while that process runs.

## Remove

1. Delete the `llm` entry from `packages` in `belt.json`.
2. Delete `scripts/llm_local.py` and this file.
3. Drop the llm mentions in [local-ai.md](local-ai.md), [setup.md](setup.md), [design.md](design.md), [connections/README.md](../connections/README.md), the README, and `scripts/belt_index.py`.
4. Run `python3 belt.py index` and commit `belt.index.json` and `AGENTS.md`.

The pin grammar also accepts `major.minor` (`0.36`) so this package validates. Leave that in place unless you want to reject two-part versions again (`PIN` in `scripts/validate.py` and `STABLE` in `scripts/check_pins.py`).
