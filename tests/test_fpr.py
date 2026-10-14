import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from belt_fixture import ROOT, load_script

fpr = load_script('fpr')
export = load_script('export')
_spec = importlib.util.spec_from_file_location('belt_cli_fpr', ROOT / 'belt.py')
belt_cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(belt_cli)


def git(repo, *args, check=True):
    result = subprocess.run(
        ['git', *args], cwd=repo, text=True, capture_output=True, check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout or f'git {args[0]} failed')
    return result


def identity(repo, email):
    git(repo, 'config', 'user.email', email)
    git(repo, 'config', 'user.name', 'Tester')


class Pair:
    def __init__(self, root, default='main'):
        self.root = Path(root)
        self.origin = self.root / 'origin'
        self.work = self.root / 'work'
        self.origin.mkdir()
        git(self.origin, 'init', '-b', default)
        identity(self.origin, 'me@example.com')
        (self.origin / 'README').write_text('one\n')
        git(self.origin, 'add', 'README')
        git(self.origin, 'commit', '-m', 'one')
        if default != 'main':
            git(self.origin, 'symbolic-ref', 'HEAD', f'refs/heads/{default}')
        git(self.root, 'clone', str(self.origin), 'work')
        identity(self.work, 'me@example.com')

    def commit_on_origin(self, name, text, message, branch=None):
        if branch:
            git(self.origin, 'switch', branch)
        (self.origin / name).write_text(text)
        git(self.origin, 'add', name)
        git(self.origin, 'commit', '-m', message)

    def sha(self, repo, rev='HEAD'):
        return git(repo, 'rev-parse', rev).stdout.strip()


class FprTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pair = Pair(self.temp.name)

    def run_fpr(self, argv, repo=None):
        repo = repo or self.pair.work
        previous = Path.cwd()
        os.chdir(repo)
        out, err = StringIO(), StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = fpr.main(argv)
        finally:
            os.chdir(previous)
        return code, out.getvalue(), err.getvalue()

    def test_new_branch_uses_origin_not_stale_local_main(self):
        local_main = self.pair.sha(self.pair.work, 'main')
        self.pair.commit_on_origin('extra', 'two\n', 'two')
        code, out, err = self.run_fpr(['new', 'topic'])
        self.assertEqual((code, err), (0, ''), err)
        self.assertIn('git fetch origin --prune', out)
        self.assertIn('git switch -c topic origin/main', out)
        self.assertIn('Warning: local main is behind origin/main. Leaving it alone.', out)
        self.assertEqual(self.pair.sha(self.pair.work, 'topic'), self.pair.sha(self.pair.origin, 'main'))
        self.assertEqual(self.pair.sha(self.pair.work, 'main'), local_main)
        self.assertNotEqual(local_main, self.pair.sha(self.pair.work, 'topic'))

    def test_base_stacks_on_origin_not_a_stale_local_branch(self):
        git(self.pair.origin, 'switch', '-c', 'api')
        self.pair.commit_on_origin('api.txt', 'api\n', 'api')
        git(self.pair.work, 'fetch', 'origin')
        git(self.pair.work, 'switch', '-c', 'api', 'origin/api')
        git(self.pair.work, 'switch', 'main')
        local_api = self.pair.sha(self.pair.work, 'api')
        local_main = self.pair.sha(self.pair.work, 'main')
        self.pair.commit_on_origin('more.txt', 'more\n', 'api moves')
        git(self.pair.origin, 'switch', 'main')
        self.pair.commit_on_origin('main2.txt', 'moved\n', 'main moves')
        code, out, err = self.run_fpr(['new', 'topic', '--base', 'api'])
        self.assertEqual((code, err), (0, ''), err)
        self.assertIn('git fetch origin --prune', out)
        self.assertIn('git switch -c topic origin/api', out)
        self.assertNotIn('git switch -c topic api', out)
        self.assertIn('Warning: local main is behind origin/main. Leaving it alone.', out)
        self.assertEqual(self.pair.sha(self.pair.work, 'topic'), self.pair.sha(self.pair.origin, 'api'))
        self.assertEqual(self.pair.sha(self.pair.work, 'api'), local_api)
        self.assertEqual(self.pair.sha(self.pair.work, 'main'), local_main)
        self.assertNotEqual(local_api, self.pair.sha(self.pair.work, 'topic'))

    def test_missing_base_does_not_fall_back_to_a_local_branch(self):
        git(self.pair.work, 'switch', '-c', 'nope')
        git(self.pair.work, 'switch', 'main')
        before = self.pair.sha(self.pair.work, 'main')
        code, _out, err = self.run_fpr(['new', 'topic', '--base', 'nope'])
        self.assertEqual(code, 1)
        self.assertIn('origin/nope does not exist after fetch', err)
        self.assertIn('will not fall back to a local branch', err)
        self.assertNotIn('topic', git(self.pair.work, 'branch', '--list').stdout)
        self.assertEqual(self.pair.sha(self.pair.work, 'main'), before)
        self.assertEqual(git(self.pair.work, 'branch', '--show-current').stdout.strip(), 'main')

    def test_sync_base_rebases_onto_origin(self):
        git(self.pair.origin, 'switch', '-c', 'api')
        self.pair.commit_on_origin('api.txt', 'api\n', 'api')
        local_main = self.pair.sha(self.pair.work, 'main')
        self.run_fpr(['new', 'feature'])
        (self.pair.work / 'feature.txt').write_text('feature\n')
        git(self.pair.work, 'add', 'feature.txt')
        git(self.pair.work, 'commit', '-m', 'feature')
        code, out, err = self.run_fpr(['sync', '--base', 'api'])
        self.assertEqual((code, err), (0, ''), err)
        self.assertIn('git rebase origin/api', out)
        self.assertNotIn('--force', out)
        self.assertTrue((self.pair.work / 'feature.txt').is_file())
        self.assertTrue((self.pair.work / 'api.txt').is_file())
        self.assertEqual(self.pair.sha(self.pair.work, 'HEAD^'), self.pair.sha(self.pair.origin, 'api'))
        self.assertEqual(self.pair.sha(self.pair.work, 'main'), local_main)

    def test_sync_leaves_a_stale_local_main_alone(self):
        local_main = self.pair.sha(self.pair.work, 'main')
        self.pair.commit_on_origin('extra', 'two\n', 'two')
        code, out, err = self.run_fpr(['sync'])
        self.assertEqual((code, err), (0, ''), err)
        self.assertIn('Warning: local main is behind origin/main. Leaving it alone.', out)
        self.assertIn('Not updating local main.', out)
        self.assertNotIn('git merge', out)
        self.assertNotIn('git rebase', out)
        self.assertEqual(self.pair.sha(self.pair.work, 'main'), local_main)
        self.assertEqual(git(self.pair.work, 'branch', '--show-current').stdout.strip(), 'main')

    def test_dirty_tree_is_refused(self):
        (self.pair.work / 'README').write_text('dirty\n')
        code, _out, err = self.run_fpr(['new', 'topic'])
        self.assertEqual(code, 1)
        self.assertIn('Uncommitted work', err)
        self.assertNotIn('topic', git(self.pair.work, 'branch', '--list').stdout)
        self.assertEqual((self.pair.work / 'README').read_text(), 'dirty\n')

    def test_unpushed_branch_rebases(self):
        self.run_fpr(['new', 'feature'])
        (self.pair.work / 'feature.txt').write_text('feature\n')
        git(self.pair.work, 'add', 'feature.txt')
        git(self.pair.work, 'commit', '-m', 'feature')
        self.pair.commit_on_origin('main.txt', 'main\n', 'main moves')
        code, out, err = self.run_fpr(['sync'])
        self.assertEqual((code, err), (0, ''), err)
        self.assertIn('git rebase origin/main', out)
        self.assertNotIn('--force', out)
        self.assertTrue((self.pair.work / 'feature.txt').is_file())
        self.assertTrue((self.pair.work / 'main.txt').is_file())
        self.assertEqual(git(self.pair.work, 'rev-list', '--merges', 'HEAD').stdout, '')
        self.assertEqual(self.pair.sha(self.pair.work, 'HEAD^'), self.pair.sha(self.pair.origin, 'main'))

    def test_pushed_branch_merges_by_default(self):
        self.run_fpr(['new', 'feature'])
        (self.pair.work / 'feature.txt').write_text('feature\n')
        git(self.pair.work, 'add', 'feature.txt')
        git(self.pair.work, 'commit', '-m', 'feature')
        git(self.pair.work, 'push', 'origin', 'feature')
        self.pair.commit_on_origin('main.txt', 'main\n', 'main moves')
        code, out, err = self.run_fpr(['sync'])
        self.assertEqual((code, err), (0, ''), err)
        self.assertIn('git merge --no-edit origin/main', out)
        self.assertNotIn('--force', out)
        parents = git(self.pair.work, 'rev-list', '--parents', '-n', '1', 'HEAD').stdout.split()
        self.assertEqual(len(parents), 3)

    def test_rebase_flag_force_with_lease_when_branch_is_ours(self):
        self.run_fpr(['new', 'feature'])
        (self.pair.work / 'feature.txt').write_text('feature\n')
        git(self.pair.work, 'add', 'feature.txt')
        git(self.pair.work, 'commit', '-m', 'feature')
        git(self.pair.work, 'push', 'origin', 'feature')
        self.pair.commit_on_origin('main.txt', 'main\n', 'main moves')
        code, out, err = self.run_fpr(['sync', '--rebase'])
        self.assertEqual((code, err), (0, ''), err)
        self.assertIn('git push --force-with-lease origin feature', out)
        self.assertNotIn('--force', out.replace('--force-with-lease', ''))
        self.assertEqual(git(self.pair.work, 'rev-list', '--merges', 'HEAD').stdout, '')
        self.assertEqual(self.pair.sha(self.pair.work), self.pair.sha(self.pair.origin, 'feature'))
        self.assertEqual(self.pair.sha(self.pair.work, 'HEAD^'), self.pair.sha(self.pair.origin, 'main'))

    def test_rebase_refuses_when_someone_else_pushed(self):
        self.run_fpr(['new', 'feature'])
        (self.pair.work / 'feature.txt').write_text('feature\n')
        git(self.pair.work, 'add', 'feature.txt')
        git(self.pair.work, 'commit', '-m', 'feature')
        git(self.pair.work, 'push', 'origin', 'feature')
        other = self.pair.root / 'other'
        git(self.pair.root, 'clone', str(self.pair.origin), 'other')
        identity(other, 'other@example.com')
        git(other, 'switch', 'feature')
        (other / 'other.txt').write_text('other\n')
        git(other, 'add', 'other.txt')
        git(other, 'commit', '-m', 'other')
        git(other, 'push', 'origin', 'feature')
        before = self.pair.sha(self.pair.work)
        code, _out, err = self.run_fpr(['sync', '--rebase'])
        self.assertEqual(code, 1)
        self.assertIn('does not have', err)
        self.assertEqual(self.pair.sha(self.pair.work), before)
        self.assertEqual(self.pair.sha(self.pair.origin, 'feature'), self.pair.sha(other))

    def test_rebase_refuses_other_authors_already_fetched(self):
        self.run_fpr(['new', 'feature'])
        (self.pair.work / 'feature.txt').write_text('feature\n')
        git(self.pair.work, 'add', 'feature.txt')
        git(self.pair.work, 'commit', '-m', 'feature')
        git(self.pair.work, 'push', 'origin', 'feature')
        other = self.pair.root / 'other'
        git(self.pair.root, 'clone', str(self.pair.origin), 'other')
        identity(other, 'other@example.com')
        git(other, 'switch', 'feature')
        (other / 'other.txt').write_text('other\n')
        git(other, 'add', 'other.txt')
        git(other, 'commit', '-m', 'other')
        git(other, 'push', 'origin', 'feature')
        git(self.pair.work, 'fetch', 'origin')
        git(self.pair.work, 'merge', '--ff-only', 'origin/feature')
        before = self.pair.sha(self.pair.work)
        code, _out, err = self.run_fpr(['sync', '--rebase'])
        self.assertEqual(code, 1)
        self.assertIn('other@example.com', err)
        self.assertEqual(self.pair.sha(self.pair.work), before)

    def test_rebase_conflict_aborts_clean(self):
        self.pair.commit_on_origin('notes.txt', 'base\n', 'base')
        git(self.pair.work, 'pull', '--ff-only')
        self.run_fpr(['new', 'feature'])
        (self.pair.work / 'notes.txt').write_text('branch\n')
        git(self.pair.work, 'add', 'notes.txt')
        git(self.pair.work, 'commit', '-m', 'branch')
        before = self.pair.sha(self.pair.work)
        self.pair.commit_on_origin('notes.txt', 'main\n', 'main')
        code, _out, err = self.run_fpr(['sync'])
        self.assertEqual(code, 1)
        self.assertIn('aborted', err)
        self.assertIn('working tree is clean', err)
        self.assertEqual(self.pair.sha(self.pair.work), before)
        self.assertEqual(git(self.pair.work, 'status', '--porcelain').stdout, '')
        self.assertNotIn('<<<<<<<', (self.pair.work / 'notes.txt').read_text())
        git_dir = Path(git(self.pair.work, 'rev-parse', '--git-path', '.').stdout.strip())
        if not git_dir.is_absolute():
            git_dir = self.pair.work / git_dir
        self.assertFalse((git_dir / 'rebase-merge').exists())

    def test_merge_conflict_aborts_clean(self):
        self.pair.commit_on_origin('notes.txt', 'base\n', 'base')
        git(self.pair.work, 'pull', '--ff-only')
        self.run_fpr(['new', 'feature'])
        (self.pair.work / 'notes.txt').write_text('branch\n')
        git(self.pair.work, 'add', 'notes.txt')
        git(self.pair.work, 'commit', '-m', 'branch')
        git(self.pair.work, 'push', 'origin', 'feature')
        before = self.pair.sha(self.pair.work)
        self.pair.commit_on_origin('notes.txt', 'main\n', 'main')
        code, _out, err = self.run_fpr(['sync'])
        self.assertEqual(code, 1)
        self.assertIn('aborted', err)
        self.assertIn('working tree is clean', err)
        self.assertEqual(self.pair.sha(self.pair.work), before)
        self.assertEqual(git(self.pair.work, 'status', '--porcelain').stdout, '')
        git_dir = Path(git(self.pair.work, 'rev-parse', '--git-path', '.').stdout.strip())
        if not git_dir.is_absolute():
            git_dir = self.pair.work / git_dir
        self.assertFalse((git_dir / 'MERGE_HEAD').exists())

    def test_rebase_refuses_the_default_branch(self):
        before = self.pair.sha(self.pair.work)
        code, _out, err = self.run_fpr(['sync', '--rebase'])
        self.assertEqual(code, 1)
        self.assertIn('default branch', err)
        self.assertEqual(self.pair.sha(self.pair.work), before)
        self.assertEqual(git(self.pair.work, 'branch', '--show-current').stdout.strip(), 'main')

    def test_missing_origin_head_falls_back_to_main(self):
        git(self.pair.work, 'update-ref', '-d', 'refs/remotes/origin/HEAD')
        self.assertEqual(fpr.origin_default(self.pair.work), 'main')

    def test_symbolic_ref_selects_the_remote_default(self):
        trunk = tempfile.TemporaryDirectory()
        self.addCleanup(trunk.cleanup)
        pair = Pair(trunk.name, default='trunk')
        pair.commit_on_origin('more', 'more\n', 'more', branch='trunk')
        local = pair.sha(pair.work, 'trunk')
        code, out, err = self.run_fpr(['new', 'topic'], repo=pair.work)
        self.assertEqual((code, err), (0, ''), err)
        self.assertIn('git switch -c topic origin/trunk', out)
        self.assertEqual(pair.sha(pair.work, 'topic'), pair.sha(pair.origin, 'trunk'))
        self.assertNotEqual(pair.sha(pair.work, 'topic'), local)

    def test_belt_py_fpr_new(self):
        local_main = self.pair.sha(self.pair.work, 'main')
        self.pair.commit_on_origin('extra', 'two\n', 'two')
        previous = Path.cwd()
        os.chdir(self.pair.work)
        out, err = StringIO(), StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = belt_cli.main(['fpr', 'new', 'from-cli'])
        finally:
            os.chdir(previous)
        self.assertIn('git switch -c from-cli origin/main', out.getvalue())
        self.assertEqual(err.getvalue(), '')
        self.assertEqual(code, 0)
        self.assertEqual(self.pair.sha(self.pair.work, 'from-cli'), self.pair.sha(self.pair.origin, 'main'))
        self.assertEqual(self.pair.sha(self.pair.work, 'main'), local_main)

    def test_skill_is_registered_and_exported(self):
        belt = json.loads((ROOT / 'belt.json').read_text())
        self.assertIn('skills/fpr/SKILL.md', belt['skills'])
        skill = (ROOT / 'skills/fpr/SKILL.md').read_text()
        self.assertIn('before creating any feature branch', skill)
        self.assertIn('before opening or updating a PR', skill)
        self.assertIn('merge conflicts or is behind main', skill)
        self.assertIn('stale on agent machines', skill)
        self.assertIn('right after fetch is the source of truth', skill)
        self.assertIn('python3 belt.py fpr new topic --base api', skill)
        out = Path(self.temp.name) / 'export'
        export.export_belt(ROOT / 'belt.json', 'cursor', out)
        copied = out / '.cursor/skills/fpr/SKILL.md'
        self.assertTrue(copied.is_file())
        self.assertEqual(copied.read_text(), skill)
