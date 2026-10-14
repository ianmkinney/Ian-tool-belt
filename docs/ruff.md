# Ruff Python linter and formatter

[Ruff](https://github.com/astral-sh/ruff) (MIT, [LICENSE](https://raw.githubusercontent.com/astral-sh/ruff/0.17.0/LICENSE)) lints and formats Python. The belt pins **0.17.0**, the PyPI release of package `ruff` and GitHub tag `0.17.0` (published 2026-10-09). Docs: [docs.astral.sh/ruff](https://docs.astral.sh/ruff/).

The belt is Python-first (`belt.py`, `scripts/`, `tests/`, `tools/`) and had no Python linter. Ruff covers that tree the way [ShellCheck](https://www.shellcheck.net/) covers shell. It is not an MCP connection.

## When to run

The **Python lint** workflow (`.github/workflows/ruff.yml`) runs on every push and pull request. Run the same commands locally before editing Python.

## Command

The version comes from the `ruff` pypi package in `belt.json`. CI installs that pin and runs both commands. `tools/breakroom/bin/breakroom` has no `.py` suffix, so directory discovery skips it.

```sh
python3 -m pip install 'ruff==0.17.0'
ruff check belt.py scripts tests tools
ruff format --check --force-exclude belt.py scripts tests tools
```

[`ruff.toml`](../ruff.toml) sets `target-version = "py310"` because Ruff 0.17 would otherwise assume 3.11, and belt checks still run on 3.10. `extend-select = ["E402"]` keeps the `noqa: E402` comments on the imports in `belt.py` that follow `sys.path.insert`.

`tools/breakroom/bin/breakroom` has no `.py` suffix, so the workflow's directory scan skips it. Pre-commit still selects it by the Python shebang, so `ruff.toml` excludes that file from lint. The `belt` shim is the same kind of extensionless file; it is in the format exclude with the rest of the tree.

`[lint] ignore` lists rules that already fire on this tree. The fixes would change behavior or restyle modules. Other default rules still fail the job. Drop a code from that list in the change that cleans it up.

`[format] exclude` lists `belt`, `belt.py`, `scripts/**`, `tests/**` and `tools/**`. `ruff format` would rewrite almost every Python file (quotes, wrapping, docstring indentation). `--force-exclude` makes that list apply even though CI and pre-commit pass paths on the command line. Remove a glob in the same change that formats that path.

The weekly pin check reads the latest stable PyPI release. A newer Ruff can open a bump PR. The `astral-sh/ruff-pre-commit` rev in `.pre-commit-config.yaml` is `v0.17.0` (the hook repo prefixes `v`; the Ruff tag does not). Tests require that rev to match the belt pin.

## Reading results

Exit code 0 means `ruff check` found no violations and `ruff format --check` found nothing outside the format exclude. A non-zero check lists the file, the rule code (for example `F401`) and the line. The format command names each file it would rewrite.

## Pre-commit

`.pre-commit-config.yaml` (and the copy under `templates/pre-commit/`) runs `ruff-check` and `ruff-format` from [astral-sh/ruff-pre-commit](https://github.com/astral-sh/ruff-pre-commit) at `v0.17.0`. Both hooks set `types_or` to Python so the formatter does not rewrite Markdown code blocks. The hooks pass `--force-exclude`, so they honor `ruff.toml`.

## Remove

1. Delete the `ruff` entry from `packages` in `belt.json`.
2. Remove `.github/workflows/ruff.yml` and `ruff.toml`.
3. Remove the `astral-sh/ruff-pre-commit` repo from `.pre-commit-config.yaml` and `templates/pre-commit/.pre-commit-config.yaml`.
4. Delete this file. Drop the Python lint row and section from [automation.md](automation.md), the ruff row from [pre-commit.md](pre-commit.md), and the ruff mentions in [setup.md](setup.md), [design.md](design.md) and the README.
5. Run `python3 belt.py index` and commit `belt.index.json` and `AGENTS.md`.
