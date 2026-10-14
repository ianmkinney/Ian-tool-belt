---
name: fpr
description: Fetch, pull, and rebase so a feature branch starts from the latest main and stays current. Use before creating any feature branch, before opening or updating a PR, and when a PR shows merge conflicts or is behind main.
---

# fpr

Fetch, pull, rebase. Run this before creating any feature branch, before opening or updating a PR, and when a PR shows merge conflicts or is behind main.

Prefer `python3 belt.py fpr`. The default branch is `git symbolic-ref refs/remotes/origin/HEAD` (the short name). If that ref is missing, use `main`.

## New branch

Never branch from a stale local main.

```sh
git fetch origin --prune
git switch -c <branch> origin/<default>
```

`python3 belt.py fpr new <branch>` does this.

## Existing branch, never pushed

```sh
git fetch origin
git rebase origin/<default>
```

`python3 belt.py fpr sync` rebases when `origin/<branch>` does not exist.

## Pushed branch or open PR

Default to a merge. It does not rewrite history and does not force-push.

```sh
git fetch origin
git merge origin/<default>
```

`python3 belt.py fpr sync` merges when the branch is already on origin.

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
