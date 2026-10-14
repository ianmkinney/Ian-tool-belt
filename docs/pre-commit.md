# Pre-commit hooks

[pre-commit](https://github.com/pre-commit/pre-commit) (MIT, PyPI package `pre-commit`) runs configured checks before each `git commit`. The belt pins **4.6.2** (verified 2026-10-12 from [PyPI](https://pypi.org/project/pre-commit/) and [GitHub releases](https://github.com/pre-commit/pre-commit/releases)). It complements CI jobs for gitleaks, ShellCheck, Ruff, actionlint and zizmor by catching the same classes of problems on a laptop or in a cloud agent workspace before changes are committed.

## What runs locally

The repo root [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) wires:

| Hook repo | Belt pin | Role |
| --- | --- | --- |
| `pre-commit/pre-commit-hooks` | v6.0.0 | Trailing whitespace, EOF, merge conflicts, YAML sanity, large files |
| `gitleaks/gitleaks` | `gitleaks` package `8.30.1` (`v8.30.1`) | Staged secret scan (`--staged`) |
| `shellcheck-py/shellcheck-py` | `shellcheck` package `0.11.0.1` | ShellCheck on shell scripts |
| `rhysd/actionlint` | actionlint **v1.7.12** (matches `actionlint-py` `1.7.12.25`) | Workflow syntax on `.github/workflows` (ShellCheck on `run:` blocks stays in the CI actionlint job) |
| `woodruffw/zizmor-pre-commit` | `zizmor` package `1.30.1` | Workflow security on `.github/workflows` YAML |
| `astral-sh/ruff-pre-commit` | `ruff` package `0.17.0` (`v0.17.0`) | Ruff lint and format on Python files (respects `ruff.toml`; Markdown stays out) |

CI still lint templates under `templates/` (actionlint) and runs full-repo gitleaks history; pre-commit zizmor skips `templates/` because adoption placeholders are not valid SHA pins until `belt_sync` runs. That split matches the CI zizmor job, which only audits `.github/workflows`.

## When bots should use it

After `pre-commit install`, run hooks before committing when you touch workflows, shell, secrets-prone config or shared automation. In CI-less sandboxes, `pre-commit run --all-files` is the fastest way to mirror the **Pre-commit** workflow without pushing. Bots should not run `pre-commit install` unless the human asked for git hooks in that clone.

## Adopt in another project

Copy the template and install explicitly (nothing runs hooks until you do):

```sh
cp path/to/Ian-tool-belt/templates/pre-commit/.pre-commit-config.yaml .
python3 -m pip install 'pre-commit==4.6.2'
pre-commit install
pre-commit run --all-files
```

See [templates/pre-commit/README.md](../templates/pre-commit/README.md). The `pre-commit` entry in `belt.json` documents the PyPI pin for `belt.py list` and weekly pin checks; it is not exported as an MCP connection.

## Remove

```sh
pre-commit uninstall
rm .pre-commit-config.yaml
```

Delete the `pre-commit` package from `belt.json`, remove `.github/workflows/pre-commit.yml` if you added CI, and drop this doc section from your fork.
