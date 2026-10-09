# GitHub Actions

Workflows live in `.github/workflows`. Every action is pinned to a full commit SHA (with the release tag in a comment). Each workflow defaults to `contents: read` and grants write access only to the job that needs it.

| Workflow | Trigger | What it does | Permissions |
| --- | --- | --- | --- |
| **Belt checks** (`checks.yml`) | push, pull request | Validates both manifests, runs the unit tests, checks styling tokens, exports all four targets | read |
| **Update a belt variable** (`update-variable.yml`) | manual | Sets one allowlisted value in `belt.json`, validates, tests, opens a draft PR | contents and PRs: write |
| **Check pinned package versions** (`bump-pins.yml`) | Mondays 13:17 UTC, or manual | Looks up the latest stable release of each npm/PyPI package pin; if newer, bumps it (and matching server args), validates, tests, opens a draft PR | contents and PRs: write |
| **Run belt task** (`run-task.yml`) | manual | Runs one allowlisted task and uploads its log and outputs as an artifact for 14 days | read |
| **Workflow security lint** (`zizmor.yml`) | push, pull request | Runs zizmor on `.github/workflows` and fails on findings, shown as annotations | read |
| **Workflow syntax lint** (`actionlint.yml`) | push, pull request | Runs actionlint on `.github/workflows`, the app workflow templates, and the versioning caller templates, and fails on findings | read |
| **release** (`release.yml`) | push to `main` | Runs release-please through `release-please-reusable.yml`: keeps the release PR current; merging it bumps `belt.json`, tags and publishes a release | contents and PRs: write |
| **pr-title** (`pr-title.yml`) | pull request | Requires a Conventional Commit PR title through `pr-title-reusable.yml` | PRs: read |

## Update a belt variable

Open **Actions → Update a belt variable → Run workflow**, then enter a path and a value. Allowed paths are defined in `scripts/belt_set.py`:

- `version`, `description`
- `servers.<id>.url`, `servers.<id>.status`, and the same under `personalServers`
- `packages.<id>.version` (stdio server args that install the package are updated too)
- `models.<id>.status`, `models.<id>.defaultPreset`, `models.<id>.presets.<preset>.baseUrl` or `.model`

Anything else is rejected. A value that fails validation (for example a plain-HTTP server URL) is rolled back, and no PR is opened. Credentials and header mappings are deliberately not settable. Run the same thing locally with `python3 scripts/belt_set.py belt.json <path> <value>`.

## Weekly pin check

The pin check runs `python3 scripts/check_pins.py belt.json --apply`. Pre-releases are never proposed. The PR branch name is derived from the change, so an unmerged bump is not proposed twice. Registry lookup failures are reported in the run summary and do not change anything. Run `python3 scripts/check_pins.py belt.json` locally for a report without changes.

## Run belt task

Choose a task from the list: `validate`, `unit-tests`, `check-styling`, `check-pins` (report only), `export-all` or `export-<target>`. Export tasks accept a local model preset. Tasks are fixed argument lists in `scripts/tasks.py`, run without a shell. The workflow input is a fixed choice list, and the script rejects any other name. The local AI health check is deliberately absent: a GitHub runner cannot reach a model on Ian's computer. `python3 scripts/tasks.py list` shows the same tasks locally.

## Workflow security lint

[zizmor](https://github.com/zizmorcore/zizmor) (MIT) is a static security linter for GitHub Actions. It flags template injection from `${{ }}` expressions in `run:` blocks, overly broad `permissions`, actions not pinned by SHA, impostor commits, known-vulnerable actions and credentials left in the checkout. These workflows accept free-text input and push branches with a token, so the lint keeps that surface checked on every change.

The version comes from the `zizmor` pypi package in `belt.json`, so the weekly pin check covers it. The job uses the official [zizmor-action](https://github.com/zizmorcore/zizmor-action), pinned by SHA. It runs a digest-pinned container image, prints results as annotations, and needs no GitHub Advanced Security or code-scanning upload. The action only accepts zizmor versions listed at its pinned commit. When a pin-bump PR raises zizmor, bump the action SHA in `zizmor.yml` to a release that lists that version; otherwise the lint job fails with `Unknown version`.

Run it locally with either command:

```sh
uvx zizmor@1.30.1 .github/workflows
pipx run zizmor==1.30.1 .github/workflows
```

Set `GH_TOKEN` (for example `GH_TOKEN=$(gh auth token)`) to enable the online audits CI runs, or add `--offline` to skip them. `--persona pedantic` shows the stricter style findings that the default persona hides.

Two findings are ignored inline with `# zizmor: ignore[artipacked]`, each with a comment. They are in `bump-pins.yml` and `update-variable.yml`, where the checkout keeps its credential because `git push` relies on it. Neither job uploads artifacts. The same token is also in the job-wide `GH_TOKEN` for `gh`. Removing both would mean scoping `GH_TOKEN` to the PR step and pushing through `gh auth setup-git`. That is possible later but has not been exercised on GitHub.

App workflow templates use `@__BELT_SHA__` placeholders until `belt_sync` substitutes a real commit SHA on adopt or sync. Those templates are not scanned by zizmor (placeholders are not valid pins); **Belt checks** run `scripts/check_belt_workflow_pins.py` instead, which fails if any file under `templates/` or `.github/workflows/` references `ianmkinney/Ian-tool-belt/...@main`. The reusable `belt-sync-reusable.yml` takes a `belt-ref` input matching the caller's pin, checks out the belt at that ref, and `belt_sync.py --fetch-ref main` reads the latest belt while writing the newest SHA into the app's workflows.

## Workflow syntax lint

[actionlint](https://github.com/rhysd/actionlint) (MIT) is a static checker for GitHub Actions workflow files. It catches workflow syntax and unknown keys, typed mistakes in `${{ }}` expressions, action inputs/outputs, reusable-workflow inputs/secrets, `needs:` dependencies, runner labels, cron syntax, and shellcheck/pyflakes issues in `run:` scripts. zizmor is the security scanner; actionlint is the structural baseline. Both run on every push and pull request.

The version comes from the `actionlint` pypi package in `belt.json` (`actionlint-py`, a third-party MIT wrapper that vendors the official binary). The weekly pin check covers it. actionlint-py versions are four-part (`1.7.12.25`): the first three match upstream actionlint, and the last is the wrapper build. `scripts/check_pins.py` treats extra numeric segments as part of a stable pin so those bumps are proposed automatically. The official GitHub release binary and `rhysd/actionlint` Docker image have stronger provenance (checksums, attestations), but they are not a kind the pin check already understands.

The job installs that pin with pip and runs actionlint on `.github/workflows`, `templates/app-adoption/.github/workflows`, and the versioning caller templates. `shellcheck` is already on `ubuntu-latest`; `pyflakes` is not, so Python `run:` scripts skip that extra check until it is installed.

Run it locally with either command (paths match CI):

```sh
uvx --from actionlint-py==1.7.12.25 actionlint -color \
  .github/workflows/*.yml \
  templates/app-adoption/.github/workflows/*.yml \
  templates/versioning/release.yml \
  templates/versioning/pr-title.yml
pipx run --spec actionlint-py==1.7.12.25 actionlint -color \
  .github/workflows/*.yml \
  templates/app-adoption/.github/workflows/*.yml \
  templates/versioning/release.yml \
  templates/versioning/pr-title.yml
```

`pr-title.yml` and `release.yml` use GitHub's `$/` self-repository syntax for same-repo reusable workflows. That syntax shipped after actionlint v1.7.12, so `.github/actionlint.yaml` ignores only the matching "invalid reusable workflow call" errors on those two files. Do not broaden the ignore: a real bad `uses:` elsewhere should still fail.

## One-time repository setting

The two PR-opening workflows use the built-in `GITHUB_TOKEN` and the `gh` CLI, with no third-party action. GitHub only lets them open pull requests if a maintainer enables **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests**. Without it, the run validates and pushes the branch, then fails at the PR step.

Pull requests opened with `GITHUB_TOKEN` do not trigger other workflows, so **Belt checks** will not start on them automatically. The workflow already ran validation and tests before opening the PR. To get the normal check, push a commit to the branch, or close and reopen the PR. A fine-grained personal access token or GitHub App token would avoid this, but it is a credential to manage, so it is not configured here.

None of these workflows has run on GitHub from this branch yet, except **Belt checks** and **Workflow security lint** on push. After this change, actionlint and zizmor both run in CI.
