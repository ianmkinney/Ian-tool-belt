import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import belt_sync
import export as exporter

ADOPTION = ROOT / 'templates/app-adoption'
WORKFLOW = ROOT / '.github/workflows/belt-sync-reusable.yml'
OWNED = '# Our own agent rules\n'
CURSOR_RULES = {'.cursor/rules/engineering.mdc', '.cursor/rules/working-agreement.mdc'}


def load_yaml(path):
    data = yaml.safe_load(path.read_text())
    data['on'] = data.pop(True, data.get('on'))
    return data


class BeltSyncWorkflowTests(unittest.TestCase):
    def test_reusable_workflow(self):
        workflow = load_yaml(WORKFLOW)
        self.assertIn('workflow_call', workflow['on'])
        job = workflow['jobs']['sync']
        self.assertEqual(job['permissions'], {'contents': 'write', 'pull-requests': 'write'})
        upstream = [s for s in job['steps'] if s.get('with', {}).get('repository')][0]['with']
        self.assertEqual(upstream['repository'], 'ianmkinney/Ian-tool-belt')
        self.assertEqual(upstream['ref'], '${{ inputs.belt-ref }}')
        self.assertIn('belt.json', upstream['sparse-checkout'])
        self.assertIn('workflow_call', workflow['on'])
        self.assertTrue(workflow['on']['workflow_call']['inputs']['belt-ref']['required'])
        sync = [s for s in job['steps'] if s.get('id') == 'sync'][0]
        self.assertIn('scripts/belt_sync.py', sync['run'])
        self.assertIn('--fetch-ref main', sync['run'])
        pr = [s for s in job['steps'] if 'create-pull-request' in s.get('uses', '')][0]
        self.assertRegex(pr['uses'], r'^peter-evans/create-pull-request@[0-9a-f]{40}$')
        self.assertIs(pr['with']['draft'], True)
        self.assertEqual(pr['with']['branch'], 'tool-belt/sync')
        self.assertTrue(pr['with']['title'].startswith('chore: sync tool belt to v'))

    def test_caller_runs_weekly_and_on_demand(self):
        caller = load_yaml(ADOPTION / '.github/workflows/belt-sync.yml')
        self.assertEqual(caller['on']['schedule'], [{'cron': '17 13 * * 1'}])
        self.assertIn('workflow_dispatch', caller['on'])
        self.assertEqual(caller['jobs']['sync']['with']['belt-ref'], '__BELT_SHA__')

    def test_every_managed_file_carries_marker(self):
        pin = 'f' * 40
        files = belt_sync.managed_files(ROOT, pin, '0.3.0')
        self.assertEqual(set(files), set(belt_sync.TEMPLATE_FILES) | CURSOR_RULES)
        for relative, content in files.items():
            with self.subTest(file=relative):
                self.assertTrue(belt_sync.has_marker(content))

    def test_cursor_rules_reuse_the_cursor_export(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'cursor'
            exporter.export_belt(ROOT / 'belt.json', 'cursor', out)
            managed = belt_sync.managed_files(ROOT, 'f' * 40, '0.3.0')
            for relative in CURSOR_RULES:
                with self.subTest(file=relative):
                    exported = (out / relative).read_text()
                    self.assertEqual(managed[relative].replace(belt_sync.MARKER_COMMENT, ''), exported)
                    front = yaml.safe_load(managed[relative].split('---')[1])
                    self.assertIs(front['alwaysApply'], True)
                    self.assertTrue(managed[relative].startswith('---\n'))


class BeltSyncLogicTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.belt = Path(temp.name) / 'belt'
        self.app = Path(temp.name) / 'app'
        (self.belt / 'templates').mkdir(parents=True)
        shutil.copytree(ADOPTION, self.belt / 'templates/app-adoption')
        shutil.copytree(ROOT / 'rules', self.belt / 'rules')
        self.app.mkdir()
        self.body = Path(temp.name) / 'body.md'
        self.init_belt_git()
        self.commit_belt('0.3.0')
        self.old_pin = belt_sync.belt_commit_sha(self.belt)
        self.run_sync('--adopt', '--pin-sha', self.old_pin)
        self.body.unlink()
        self.set_belt_version('0.4.0')
        self.commit_belt('0.4.0')
        self.new_pin = belt_sync.belt_commit_sha(self.belt)

    def set_belt_version(self, version):
        rules = json.loads((ROOT / 'belt.json').read_text())['rules']
        (self.belt / 'belt.json').write_text(json.dumps({'version': version, 'rules': rules}))

    def init_belt_git(self):
        subprocess.check_call(['git', 'init', '-q', str(self.belt)])
        subprocess.check_call(['git', '-C', str(self.belt), 'config', 'user.email', 't@example.com'])
        subprocess.check_call(['git', '-C', str(self.belt), 'config', 'user.name', 'test'])

    def commit_belt(self, version):
        self.set_belt_version(version)
        subprocess.check_call(['git', '-C', str(self.belt), 'add', '-A'])
        subprocess.check_call(
            ['git', '-C', str(self.belt), 'commit', '-q', '-m', f'belt {version}', '--allow-empty'],
        )

    def run_sync(self, *flags):
        if '--pin-sha' not in flags:
            flags = ('--pin-sha', belt_sync.belt_commit_sha(self.belt), *flags)
        return belt_sync.main(['--belt', str(self.belt), '--app', str(self.app),
                               '--body', str(self.body), *flags])

    def app_files(self):
        return {p: p.read_bytes() for p in self.app.rglob('*') if p.is_file()}

    def test_version_comparison(self):
        self.assertTrue(belt_sync.is_behind('0.2.0', '0.3.0'))
        self.assertTrue(belt_sync.is_behind('0.9.0', '0.10.0'))
        self.assertTrue(belt_sync.is_behind('1.2.3', '2.0.0'))
        self.assertFalse(belt_sync.is_behind('0.3.0', '0.3.0'))
        self.assertFalse(belt_sync.is_behind('0.4.0', '0.3.0'))
        for bad in ['v1.0.0', '1.0', 'latest']:
            with self.assertRaises(ValueError):
                belt_sync.parse_version(bad)

    def test_marker_detection(self):
        self.assertTrue(belt_sync.has_marker('<!-- managed by Ian-tool-belt -->\n# Hi\n'))
        self.assertTrue(belt_sync.has_marker('---\nalwaysApply: true\n---\n<!-- managed by Ian-tool-belt -->\n'))
        self.assertFalse(belt_sync.has_marker(OWNED))
        self.assertFalse(belt_sync.has_marker('\n' * belt_sync.MARKER_LINES + 'managed by Ian-tool-belt'))

    def test_adopt_writes_every_managed_file_and_marker(self):
        for relative, content in belt_sync.managed_files(self.belt, self.old_pin, '0.3.0').items():
            self.assertEqual((self.app / relative).read_text(), content)
        self.assertEqual(json.loads((self.app / '.tool-belt.json').read_text())['beltVersion'], '0.3.0')
        self.assertIn(f'@{self.old_pin}', (self.app / '.github/workflows/belt.yml').read_text())

    def test_sync_bumps_stale_workflow_pin_at_same_version(self):
        self.set_belt_version('0.3.0')
        self.commit_belt('0.3.0')
        new_pin = belt_sync.belt_commit_sha(self.belt)
        self.assertNotEqual(new_pin, self.old_pin)
        outputs = self.run_sync('--allow-workflow-files', '--pin-sha', new_pin)
        self.assertEqual(outputs['changed'], 'true')
        self.assertIn(f'@{new_pin}', (self.app / '.github/workflows/belt.yml').read_text())
        self.assertNotIn(f'@{self.old_pin}', (self.app / '.github/workflows/belt.yml').read_text())

    def test_up_to_date_app_is_untouched(self):
        self.set_belt_version('0.3.0')
        self.commit_belt('0.3.0')
        pin = belt_sync.belt_commit_sha(self.belt)
        for name in ('belt.yml', 'belt-sync.yml'):
            path = self.app / '.github/workflows' / name
            path.write_text(belt_sync.substitute_belt_pins(path.read_text(), pin, '0.3.0'))
        before = self.app_files()
        self.assertEqual(self.run_sync('--allow-workflow-files', '--pin-sha', pin)['changed'], 'false')
        self.assertEqual(self.app_files(), before)
        self.assertFalse(self.body.exists())

    def test_behind_app_updates_managed_files_and_skips_owned(self):
        (self.belt / 'templates/app-adoption/AGENTS.md').write_text(
            '<!-- managed by Ian-tool-belt -->\nNew rules\n')
        engineering = self.belt / 'rules/engineering.md'
        engineering.write_text(engineering.read_text() + '\nNew engineering rule.\n')
        (self.belt / 'rules/working-agreement.md').write_text('# Changed agreement\n')
        (self.app / '.cursor/rules/working-agreement.mdc').write_text(OWNED)
        (self.app / '.github/workflows/belt-sync.yml').unlink()
        outputs = self.run_sync('--allow-workflow-files')
        self.assertEqual(outputs['changed'], 'true')
        self.assertEqual(outputs['version'], '0.4.0')
        paths = set(outputs['paths'].split())
        self.assertIn('.tool-belt.json', paths)
        self.assertIn('AGENTS.md', paths)
        self.assertIn('.cursor/rules/engineering.mdc', paths)
        self.assertIn('.github/workflows/belt-sync.yml', paths)
        self.assertTrue({'.github/workflows/belt.yml', '.github/workflows/belt-sync.yml'} & paths)
        self.assertIn('New rules', (self.app / 'AGENTS.md').read_text())
        self.assertIn('New engineering rule.', (self.app / '.cursor/rules/engineering.mdc').read_text())
        self.assertEqual((self.app / '.cursor/rules/working-agreement.mdc').read_text(), OWNED)
        self.assertEqual(json.loads((self.app / '.tool-belt.json').read_text())['beltVersion'], '0.4.0')
        body = self.body.read_text()
        self.assertIn('v0.3.0 to v0.4.0', body)
        self.assertIn('releases/tag/v0.4.0', body)
        self.assertIn('CHANGELOG.md', body)
        self.assertIn('`.cursor/rules/working-agreement.mdc` | skipped: marker removed', body)
        self.assertNotIn('Close and reopen', body)

    def test_adopt_never_overwrites_owned_files(self):
        (self.app / 'AGENTS.md').write_text(OWNED)
        self.run_sync('--adopt')
        self.assertEqual((self.app / 'AGENTS.md').read_text(), OWNED)

    def test_workflow_files_need_a_token(self):
        workflow = self.belt / 'templates/app-adoption/.github/workflows/belt.yml'
        workflow.write_text(workflow.read_text() + '# changed\n')
        outputs = self.run_sync()
        self.assertNotIn('.github/workflows/belt.yml', outputs['paths'].split())
        self.assertNotIn('# changed', (self.app / '.github/workflows/belt.yml').read_text())
        body = self.body.read_text()
        self.assertIn('Workflows write permission', body)
        self.assertIn('Close and reopen', body)

    def test_unadopted_app_fails_without_adopt(self):
        (self.app / '.tool-belt.json').unlink()
        with self.assertRaises(OSError):
            self.run_sync()


if __name__ == '__main__':
    unittest.main()
