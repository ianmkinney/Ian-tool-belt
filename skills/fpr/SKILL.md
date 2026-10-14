---
name: fpr
description: Fetch, pull, and rebase so a feature branch starts from the latest main and stays current. Use before creating any feature branch, before opening or updating a PR, and when a PR shows merge conflicts or is behind main.
---

# fpr

Fetch, pull, rebase. Run this before creating any feature branch, before opening or updating a PR, and when a PR shows merge conflicts or is behind main.

Prefer `python3 belt.py fpr`. The default base is the remote default branch: `git symbolic-ref refs/remotes/origin/HEAD` (the short name). If that ref is missing, use `main`.

Local main can be stale on agent machines. `origin/<base>` right after fetch is the source of truth. fpr branches and updates from that remote-tracking ref and leaves a stale local main alone. If local `main` exists and is behind `origin/main`, it prints a warning and does not move it.

## New branch

Never branch from a local branch. Fetch, then start from `origin/<base>`.

```sh
git fetch origin --prune
git switch -c <branch> origin/<base>
```

`python3 belt.py fpr new <branch>` uses the remote default. Stack on another branch with `--base`:

```sh
python3 belt.py fpr new topic --base api
```

That is `git switch -c topic origin/api` after fetch. If `origin/<base>` does not exist after fetch, fpr stops and does not fall back to a local branch.

## Existing branch, never pushed

```sh
git fetch origin
git rebase origin/<base>
```

`python3 belt.py fpr sync` rebases onto the remote default when `origin/<branch>` does not exist. `python3 belt.py fpr sync --base api` rebases onto `origin/api`.

## Pushed branch or open PR

Default to a merge. It does not rewrite history and does not force-push.

```sh
git fetch origin
git merge origin/<base>
```

`python3 belt.py fpr sync` merges `origin/<default>` when the branch is already on origin. `python3 belt.py fpr sync --base api` merges `origin/api`.

Rebase plus `git push --force-with-lease` is allowed only when the branch is yours alone and no one else has pushed. Pass `--rebase`:

```sh
python3 belt.py fpr sync --rebase
```

Never use plain `--force`. Never rebase `main` or any shared branch.

## Uncommitted work

Stop. Commit or stash first. Never discard changes. `belt.py fpr` refuses a dirty tree.

## Conflicts

Resolve them keeping both sides' intent, run the repo's checks, and continue. If you are unsure, `git rebase --abort` or `git merge --abort` and report what conflicted. `belt.py fpr` aborts the rebase or merge, leaves a clean tree, and exits non-zero.

## Before every PR push

If the branch is behind the default branch, run fpr again before you push.
