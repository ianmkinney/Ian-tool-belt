# Typos spell checker

[typos](https://github.com/crate-ci/typos) (MIT OR Apache-2.0) is a fast spell checker for source code and documentation. The belt pins **1.51.1**, which is the PyPI release of `typos` and the GitHub tag `v1.51.1` (published 2026-10-06). Nothing else in the belt checks spelling. It complements [lychee](lychee.md) (links), [markdownlint-cli2](markdownlint.md) (Markdown structure) and ShellCheck / actionlint (syntax).

## When to run

The **Spell check** workflow (`.github/workflows/typos.yml`) runs on every push and pull request. Run the same command locally before editing docs or source.

The opt-in [pre-commit](pre-commit.md) config also runs the `crate-ci/typos` hook at tag `v1.51.1`. That hook reports findings and does not rewrite files. CI still installs the PyPI pin; the hook installs the matching GitHub release binary.

## Command

The version comes from the `typos` pypi package in `belt.json`. CI installs `typos==` that pin and runs `typos` on the repository. The job fails when typos reports a finding. [`typos.toml`](../typos.toml) is read automatically.

```sh
python3 -m pip install 'typos==1.51.1'
typos
```

`typos --format brief` prints one line per finding. The default format is `long`.

## Reading results

Exit code 0 means no findings. A non-zero exit (the default `long` format) prints one block per finding: the misspelled token, the suggested correction, then the file, line and column with the token underlined. `--format brief` is one line, `path:line:col: error: \`token\` should be \`correction\``.

Fix the word in the file. Add a regex to `extend-ignore-re` in `typos.toml` only when the token is a real name or abbreviation, or add the token to `extend-words` when it is a whole identifier. The current file ignores two patterns:

- `(BA)` — breakroom office tag on bot names, next to `(AO)` and `(SF)`
- `(ba|ao|sf)` — the literal tag strip in `tools/breakroom/bin/breakroom`

`extend-words` also keeps `fpr`, the fetch/pull/rebase command name. A token outside that list still fails. Do not ignore a whole directory to clear one finding.

## Remove

1. Delete the `typos` entry from `packages` in `belt.json`.
2. Remove `.github/workflows/typos.yml` and `typos.toml`.
3. Remove the `crate-ci/typos` repo from `.pre-commit-config.yaml` and `templates/pre-commit/.pre-commit-config.yaml`.
4. Delete this file. Drop the Spell check row and section from [automation.md](automation.md), and the typos mentions in [setup.md](setup.md), [design.md](design.md), [pre-commit.md](pre-commit.md) and the README.
5. Drop the typos lines from `scripts/belt_index.py`.
6. Run `python3 belt.py index` and commit `belt.index.json` and `AGENTS.md`.
