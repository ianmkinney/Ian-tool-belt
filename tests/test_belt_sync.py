import json
import shutil
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
        self.assertEqual((upstream['repository'], upstream['ref']), ('ianmkinney/Ian-tool-belt', 'main'))
        self.assertEqual(set(upstream['sparse-checkout'].split()),
                         {'templates/app-adoption', 'rules', 'scripts'})
        sync = [s for s in job['steps'] if s.get('id') == 'sync'][0]
        self.assertIn('scripts/belt_sync.py', sync['run'])
        pr = [s for s in job['steps'] if 'create-pull-request' in s.get('uses', '')][0]
        self.assertRegex(pr['uses'], r'^peter-evans/create-pull-request@[0-9a-f]{40}$')
        self.assertIs(pr['with']['draft'], True)
        self.assertEqual(pr['with']['branch'], 'tool-belt/sync')
        self.assertTrue(pr['with']['title'].startswith('chore: sync tool belt to v'))

    def test_caller_runs_weekly_and_on_demand(self):
        caller = load_yaml(ADOPTION / '.github/workflows/belt-sync.yml')
        self.assertEqual(caller['on']['schedule'], [{'cron': '17 13 * * 1'}])
        self.assertIn('workflow_dispatch', caller['on'])

    def test_every_managed_file_carries_marker(self):
        files = belt_sync.managed_files(ROOT)
        self.assertEqual(set(files), set(belt_sync.TEMPLATE_FILES) | CURSOR_RULES)
        for relative, content in files.items():
            with self.subTest(file=relative):
                self.assertTrue(belt_sync.has_marker(content))

    def test_cursor_rules_reuse_the_cursor_export(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'cursor'
            exporter.export_belt(ROOT / 'belt.json', 'cursor', out)
            managed = belt_sync.managed_files(ROOT)
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
        self.set_belt_version('0.3.0')
        self.run_sync('--adopt')
        self.body.unlink()
        self.set_belt_version('0.4.0')

    def set_belt_version(self, version):
        rules = json.loads((ROOT / 'belt.json').read_text())['rules']
        (self.belt / 'belt.json').write_text(json.dumps({'version': version, 'rules': rules}))

    def run_sync(self, *flags):
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
        for relative, content in belt_sync.managed_files(self.belt).items():
            self.assertEqual((self.app / relative).read_text(), content)
        self.assertEqual(json.loads((self.app / '.tool-belt.json').read_text())['beltVersion'], '0.3.0')

    def test_up_to_date_app_is_untouched(self):
        self.set_belt_version('0.3.0')
        before = self.app_files()
        self.assertEqual(self.run_sync('--allow-workflow-files')['changed'], 'false')
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
        self.assertEqual(set(outputs['paths'].split()),
                         {'AGENTS.md', '.cursor/rules/engineering.mdc',
                          '.github/workflows/belt-sync.yml', '.tool-belt.json'})
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
