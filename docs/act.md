# Run GitHub Actions locally with act

[act](https://github.com/nektos/act) (MIT, [LICENSE](https://raw.githubusercontent.com/nektos/act/master/LICENSE)) runs GitHub Actions workflows on your machine. The belt pins **0.2.89** (`nektos/act` github-release tag `v0.2.89`, published 2026-06-01).

actionlint, zizmor, ShellCheck and gitleaks inspect workflow files. act executes them, so a contributor or agent can see a job run before pushing. It does not replace those linters.

Running a job requires Docker. `act --version` and `act -l` do not.

## When to use it

From a repository that contains `.github/workflows/`:

```sh
act -l
act push
act pull_request
act push -j validate-and-test
act -W .github/workflows/checks.yml
```

- `act -l` lists jobs and the events that trigger them.
- `act push` and `act pull_request` run workflows for that event. The default event is `push`.
- `-j <job-id>` limits the run to one job. The id is the key under `jobs:` in the workflow file.
- `-W <file>` limits the run to one workflow file.

Use it when you change a workflow and want evidence the job starts, or when a bot cannot push yet and still needs a dry run. Prefer the linters for syntax, security, shell and secrets; use act when the question is whether the job actually runs.

## Docker

Install and start Docker before executing a job. act pulls the workflow's runner image (often `catthehacker/ubuntu:act-*` for `ubuntu-latest`) the first time you run a job. If Docker is not running, job execution fails immediately and the log says the Docker daemon is unavailable.

`act --version` only prints the CLI version. The belt's CI job stops there so GitHub Actions does not try to run act inside another Actions runner.

## Install the pinned release

Linux x86_64 matches the asset CI downloads:

```sh
curl -fsSL -o act_Linux_x86_64.tar.gz "https://github.com/nektos/act/releases/download/v0.2.89/act_Linux_x86_64.tar.gz"
curl -fsSL -o checksums.txt "https://github.com/nektos/act/releases/download/v0.2.89/checksums.txt"
grep -F ' act_Linux_x86_64.tar.gz' checksums.txt | sha256sum -c -
tar -xzf act_Linux_x86_64.tar.gz act
./act --version
```

`./act --version` prints `act version 0.2.89`. Other operating systems use the matching archive from the [v0.2.89 release](https://github.com/nektos/act/releases/tag/v0.2.89); check it against the same `checksums.txt` and extract the `act` binary.

The `act` entry in `belt.json` is the pin `belt.py list` and the weekly pin check read. It is not exported as an MCP connection. CI (`.github/workflows/act.yml`) reads that pin, downloads `act_Linux_x86_64.tar.gz`, verifies `checksums.txt`, and runs `act --version`. It does not pass an event name, so it never emulates a workflow.

## Reading output

`act -l` prints one line per job: the stage or workflow name, the job name, and the triggering event. Use that list to pick a `-j` filter.

A job run prints each step as it starts and when it finishes, then a short summary. A non-zero exit means a step failed; the failing step name is above the summary. Secrets and repository `vars` are empty unless you pass `-s NAME=value` or a local `.secrets` file. Keep those files out of Git.

The first run is slower because Docker pulls the runner image. Later runs reuse it.

## Remove

1. Delete the `act` entry from `packages` in `belt.json`.
2. Remove `.github/workflows/act.yml`.
3. Delete this file and drop the act mentions from `docs/automation.md`, `docs/design.md`, `docs/setup.md`, `README.md`, and `scripts/belt_index.py`.
4. Run `python3 belt.py index` and commit the regenerated `belt.index.json` and `AGENTS.md`.
5. Delete any local `act` binary you extracted.

Nothing else in the belt calls act.
