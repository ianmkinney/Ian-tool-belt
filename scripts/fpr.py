"""Fetch and update a feature branch from a remote-tracking ref.

  python3 belt.py fpr new <branch> [--base <base>]
  python3 belt.py fpr sync [--base <base>] [--rebase]
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


class FprError(Exception):
    def __init__(self, message, code=1):
        super().__init__(message)
        self.code = code


def git(repo, args, check=True, echo=True):
    shown = 'git ' + ' '.join(args)
    if echo:
        print(shown)
    env = os.environ.copy()
    env['GIT_EDITOR'] = 'true'
    env['GIT_MERGE_AUTOEDIT'] = 'no'
    env['GIT_TERMINAL_PROMPT'] = '0'
    result = subprocess.run(
        ['git', *args], cwd=repo, text=True, capture_output=True, check=False, env=env,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or '').strip()
        raise FprError(detail or f'{shown} failed')
    return result


def ensure_clean(repo):
    print('Checking for uncommitted work')
    result = git(repo, ['status', '--porcelain'], echo=False)
    if result.stdout.strip():
        raise FprError('Uncommitted work. Commit or stash first. fpr will not discard changes.')


def origin_default(repo):
    result = git(repo, ['symbolic-ref', 'refs/remotes/origin/HEAD'], check=False, echo=False)
    prefix = 'refs/remotes/origin/'
    ref = result.stdout.strip()
    if result.returncode == 0 and ref.startswith(prefix) and ref[len(prefix):]:
        return ref[len(prefix):]
    print('origin/HEAD is unset; using main')
    return 'main'


def fetch(repo):
    print('Fetching origin')
    git(repo, ['fetch', 'origin', '--prune'])


def current_branch(repo):
    result = git(repo, ['rev-parse', '--abbrev-ref', 'HEAD'], echo=False)
    name = result.stdout.strip()
    if name == 'HEAD':
        raise FprError('Detached HEAD. Check out a branch before fpr sync.')
    return name


def remote_branch_exists(repo, branch):
    result = git(repo, ['rev-parse', '--verify', '--quiet', f'refs/remotes/origin/{branch}'],
                 check=False, echo=False)
    return result.returncode == 0


def git_dir(repo):
    result = git(repo, ['rev-parse', '--git-path', '.'], echo=False)
    path = Path(result.stdout.strip())
    if not path.is_absolute():
        path = Path(repo) / path
    return path


def rebase_in_progress(repo):
    path = git_dir(repo)
    return (path / 'rebase-merge').exists() or (path / 'rebase-apply').exists()


def merge_in_progress(repo):
    return (git_dir(repo) / 'MERGE_HEAD').exists()


def _abort(repo, kind, default, result):
    detail = (result.stderr or result.stdout or '').strip()
    if kind == 'rebase' and rebase_in_progress(repo):
        abort = git(repo, ['rebase', '--abort'], check=False)
        if abort.returncode != 0:
            raise FprError(
                f'Rebase onto origin/{default} failed and could not be aborted.\n{detail}')
        raise FprError(
            f'Rebase onto origin/{default} hit conflicts and was aborted. '
            f'The working tree is clean.\n{detail}')
    if kind == 'merge' and merge_in_progress(repo):
        abort = git(repo, ['merge', '--abort'], check=False)
        if abort.returncode != 0:
            raise FprError(
                f'Merge of origin/{default} failed and could not be aborted.\n{detail}')
        raise FprError(
            f'Merge of origin/{default} hit conflicts and was aborted. '
            f'The working tree is clean.\n{detail}')
    raise FprError(detail or f'{kind} of origin/{default} failed')


def rebase_onto(repo, default):
    print(f'Rebasing onto origin/{default}')
    result = git(repo, ['rebase', f'origin/{default}'], check=False)
    if result.returncode != 0:
        _abort(repo, 'rebase', default, result)


def merge_default(repo, default):
    print(f'Merging origin/{default}')
    result = git(repo, ['merge', '--no-edit', f'origin/{default}'], check=False)
    if result.returncode != 0:
        _abort(repo, 'merge', default, result)


def remote_is_ahead(repo, branch):
    result = git(repo, ['rev-list', '--count', f'HEAD..origin/{branch}'], echo=False)
    return result.stdout.strip() not in {'', '0'}


def remote_authors(repo, branch, default):
    result = git(repo, ['log', '--format=%ae', f'origin/{default}..origin/{branch}'], echo=False)
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def committer_email(repo):
    result = git(repo, ['config', '--get', 'user.email'], check=False, echo=False)
    if result.returncode != 0:
        return ''
    return result.stdout.strip()


def assert_rebase_allowed(repo, branch, default):
    if branch == 'main' or branch == origin_default(repo):
        raise FprError(f'Refusing to rebase {branch}. That is the default branch.')
    if remote_is_ahead(repo, branch):
        raise FprError(
            f'origin/{branch} has commits this checkout does not have. '
            'Refusing rebase. Run python3 belt.py fpr sync to merge.')
    email = committer_email(repo)
    if not email:
        raise FprError(
            'git user.email is unset. Refusing to rebase a pushed branch. '
            'Run python3 belt.py fpr sync to merge.')
    others = remote_authors(repo, branch, default) - {email}
    if others:
        names = ', '.join(sorted(others))
        raise FprError(
            f'origin/{branch} includes commits from {names}. '
            'Refusing rebase. Run python3 belt.py fpr sync to merge.')


def check_branch_name(name):
    if not name or name.startswith('-') or name in {'.', '..'} or any(
            part in {'', '.', '..'} for part in name.split('/')):
        raise FprError(f'Invalid branch name {name!r}.')


def local_main_is_behind(repo):
    local = git(repo, ['rev-parse', '--verify', '--quiet', 'refs/heads/main'],
                check=False, echo=False)
    if local.returncode != 0 or not remote_branch_exists(repo, 'main'):
        return False
    behind = git(repo, ['rev-list', '--count', 'refs/heads/main..refs/remotes/origin/main'], echo=False)
    return behind.stdout.strip() not in {'', '0'}


def warn_if_local_main_is_behind(repo):
    if not local_main_is_behind(repo):
        return False
    print('Warning: local main is behind origin/main. Leaving it alone. '
          'origin/<base> after fetch is the source of truth.')
    return True


def resolve_base(repo, base):
    chosen = base if base else origin_default(repo)
    if base:
        check_branch_name(base)
    if not remote_branch_exists(repo, chosen):
        raise FprError(
            f'origin/{chosen} does not exist after fetch. '
            'fpr uses that remote-tracking ref and will not fall back to a local branch.')
    return chosen


def create_branch(repo, name, base=None):
    check_branch_name(name)
    ensure_clean(repo)
    fetch(repo)
    warn_if_local_main_is_behind(repo)
    chosen = resolve_base(repo, base)
    print(f'Creating {name} from origin/{chosen}')
    git(repo, ['switch', '-c', name, f'origin/{chosen}'])


def sync_branch(repo, rebase=False, base=None):
    ensure_clean(repo)
    fetch(repo)
    behind = warn_if_local_main_is_behind(repo)
    chosen = resolve_base(repo, base)
    branch = current_branch(repo)
    if branch == 'main' and behind:
        print('Not updating local main.')
        return
    pushed = remote_branch_exists(repo, branch)
    if not pushed:
        print(f'{branch} has not been pushed. Rebasing onto origin/{chosen}.')
        rebase_onto(repo, chosen)
        return
    if rebase:
        assert_rebase_allowed(repo, branch, chosen)
        rebase_onto(repo, chosen)
        print(f'Pushing {branch} with --force-with-lease')
        git(repo, ['push', '--force-with-lease', 'origin', branch])
        return
    print(f'{branch} is on origin. Merging origin/{chosen}.')
    merge_default(repo, chosen)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['new', 'sync'])
    parser.add_argument('branch', nargs='?')
    parser.add_argument('--rebase', action='store_true')
    parser.add_argument('--base', help='remote branch to stack on; fpr uses origin/<base> after fetch')
    args = parser.parse_args(argv)
    if args.action == 'new' and not args.branch:
        print('usage: python3 belt.py fpr new <branch> [--base <base>]', file=sys.stderr)
        return 2
    if args.action == 'sync' and args.branch:
        print('usage: python3 belt.py fpr sync [--base <base>] [--rebase]', file=sys.stderr)
        return 2
    if args.rebase and args.action != 'sync':
        print('--rebase is only for fpr sync', file=sys.stderr)
        return 2
    repo = Path.cwd()
    try:
        if args.action == 'new':
            create_branch(repo, args.branch, base=args.base)
        else:
            sync_branch(repo, rebase=args.rebase, base=args.base)
    except FprError as error:
        print(error, file=sys.stderr)
        return error.code
    return 0


if __name__ == '__main__':
    sys.exit(main())
