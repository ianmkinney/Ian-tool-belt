# markdownlint-cli2

[markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) (MIT, [LICENSE](https://github.com/DavidAnson/markdownlint-cli2/blob/v0.23.3/LICENSE)) lints Markdown structure. David Anson publishes it. The belt pins **0.23.3**, the npm `latest` dist-tag of package `markdownlint-cli2` and the git tag `v0.23.3` (published 2026-09-20). That tag is commit `916ad0aaa108c64d294101002066f530ea170b10` (`Update to version 0.23.3`). The repository has no GitHub Releases; the weekly pin check reads npm.

[typos](typos.md) checks spelling. [lychee](lychee.md) checks links. This linter checks headings, lists, fences and the other structure rules. It is not an MCP connection. The package requires Node.js 22 or newer.

## When to run

The **Markdown lint** workflow (`.github/workflows/markdownlint.yml`) runs on every push and pull request. Run the same command locally before editing Markdown.

The opt-in [pre-commit](pre-commit.md) config runs the official `markdownlint-cli2` hook at tag `v0.23.3`. That hook does not pass `--fix`, so it reports findings and does not rewrite files. `language_version: system` uses the Node on `PATH`. The Pre-commit workflow installs Node 22 before the hooks run, because the package `engines` field is `>=22`.

## Command

The version comes from the `markdownlint-cli2` npm package in `belt.json`. CI installs that exact version and runs `markdownlint-cli2` with no extra arguments. [`.markdownlint-cli2.jsonc`](../.markdownlint-cli2.jsonc) is read automatically. The `globs` entry is `**/*.md`. The install step ignores zizmor's `adhoc-packages` check: the version is the belt pin, and this repo has no npm lockfile.

```sh
npm install --global markdownlint-cli2@0.23.3
markdownlint-cli2
```

## Config

The config starts from markdownlint defaults (`"default": true`). Three rules are off, each because the docs are already written that way:

- `MD013` — prose, tables and commands already run past 80 columns
- `MD034` — docs cite canonical URLs as bare links
- `MD041` — `README.md` opens with the tool-belt banner fence, then the h1

`MD033` stays on. `allowed_elements` is `App`, `app` and `bot` so the angle-bracket placeholders in `tools/breakroom/products/_TEMPLATE.md` are not treated as HTML.

Generated files are excluded: `AGENTS.md` (from `python3 belt.py index`), `CHANGELOG.md` (release-please) and `site/**` (the Pages build). `gitignore: true` also skips anything `.gitignore` already ignores, including a local `site/` directory.

## Reading results

Exit code 0 means no findings. A non-zero exit prints one line per finding: `path:line[:column] error MDnnn/name description`. Fix the Markdown, or add a rule to the config only when it conflicts with an existing style, with a one-line reason.

## Pre-commit

`.pre-commit-config.yaml` (and the copy under `templates/pre-commit/`) uses hook id `markdownlint-cli2` from [DavidAnson/markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) at `v0.23.3`. The same number is the npm pin. Tests require that rev to match. The weekly pin check updates `belt.json` only; bump the hook rev in the same change.

## Remove

1. Delete the `markdownlint-cli2` entry from `packages` in `belt.json`.
2. Remove `.github/workflows/markdownlint.yml` and `.markdownlint-cli2.jsonc`.
3. Remove the `DavidAnson/markdownlint-cli2` repo from `.pre-commit-config.yaml` and `templates/pre-commit/.pre-commit-config.yaml`.
4. Remove the Node 22 setup step from `.github/workflows/pre-commit.yml` if nothing else needs it.
5. Delete this file. Drop the Markdown lint row and section from [automation.md](automation.md), and the markdownlint mentions in [setup.md](setup.md), [design.md](design.md), [pre-commit.md](pre-commit.md), [typos.md](typos.md) and the README.
6. Drop the markdownlint-cli2 lines from `scripts/belt_index.py`.
7. Run `python3 belt.py index` and commit `belt.index.json` and `AGENTS.md`.
