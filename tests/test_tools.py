import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from belt_fixture import ROOT, BeltCase, load_script
from validate import validate

new = load_script('new')
belt_set = load_script('belt_set')
check_pins = load_script('check_pins')
tasks = load_script('tasks')


def quiet(function, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
        code = function(*args, **kwargs)
    return code, out.getvalue(), err.getvalue()


class ScaffoldTests(BeltCase):
    def test_new_skill_is_created_registered_and_valid(self):
        code, out, _ = quiet(new.main, ['--belt', str(self.manifest), 'skill', 'review-sql',
                                        '--description', 'Review SQL changes. Use when: a migration changes.'])
        self.assertEqual(code, 0, out)
        self.assertIn('skills/review-sql/SKILL.md', self.reload()['skills'])
        text = (self.source / 'skills/review-sql/SKILL.md').read_text()
        self.assertIn('name: review-sql\n', text)
        self.assertIn('description: "Review SQL changes. Use when: a migration changes."\n', text)
        validate(self.manifest)

    def test_duplicate_or_bad_skill_changes_nothing(self):
        before = self.manifest.read_text()
        for args in [['skill', 'evaluate-mcp', '--description', 'x'],
                     ['skill', 'Bad_Name', '--description', 'x'],
                     ['skill', 'blank', '--description', '  ']]:
            with self.subTest(args=args):
                code, _, err = quiet(new.main, ['--belt', str(self.manifest), *args])
                self.assertEqual(code, 1)
                self.assertIn('Scaffold failed', err)
        self.assertEqual(self.manifest.read_text(), before)
        self.assertFalse((self.source / 'skills/blank').exists())

    def test_files_package_gets_folder_and_entry(self):
        code, _, _ = quiet(new.main, ['--belt', str(self.manifest), 'package', 'api-client',
                                      '--kind', 'files', '--description', 'Shared HTTP client'])
        self.assertEqual(code, 0)
        self.assertTrue((self.source / 'packages/api-client/README.md').is_file())
        package = self.reload()['packages'][-1]
        self.assertEqual(package, {'id': 'api-client', 'kind': 'files', 'path': 'packages/api-client',
                                   'version': '0.1.0', 'description': 'Shared HTTP client'})

    def test_registry_package_needs_an_exact_pin(self):
        code, _, _ = quiet(new.main, ['--belt', str(self.manifest), 'package', 'zod', '--kind', 'npm',
                                      '--name', 'zod', '--version', '3.23.8', '--description', 'Schema pin'])
        self.assertEqual(code, 0)
        self.assertEqual(self.reload()['packages'][-1]['name'], 'zod')
        before = self.manifest.read_text()
        for extra in [['--name', 'left-pad'], ['--name', 'left-pad', '--version', '^1.0.0']]:
            with self.subTest(extra=extra):
                code, _, _ = quiet(new.main, ['--belt', str(self.manifest), 'package', 'left-pad',
                                              '--kind', 'npm', '--description', 'x', *extra])
                self.assertEqual(code, 1)
        self.assertEqual(self.manifest.read_text(), before)

    def test_invalid_files_package_is_rolled_back(self):
        code, _, _ = quiet(new.main, ['--belt', str(self.manifest), 'package', 'broken', '--kind', 'files',
                                      '--version', 'latest', '--description', 'x'])
        self.assertEqual(code, 1)
        self.assertFalse((self.source / 'packages/broken').exists())
        self.assertNotIn('broken', [p['id'] for p in self.reload()['packages']])


class BeltSetTests(BeltCase):
    def set(self, path, value):
        return quiet(belt_set.main, [str(self.manifest), path, value])

    def test_settable_variables(self):
        for path, value, read in [
            ('servers.playwright.status', 'untested', lambda b: b['servers'][2]['status']),
            ('servers.context7.url', 'https://mcp.context7.com/mcp/v2', lambda b: b['servers'][1]['url']),
            ('models.local-ai.presets.lm-studio.model', 'qwen-local',
             lambda b: b['models'][0]['presets']['lm-studio']['model']),
            ('models.local-ai.defaultPreset', 'lm-studio', lambda b: b['models'][0]['defaultPreset']),
            ('version', '0.3.1', lambda b: b['version']),
        ]:
            with self.subTest(path=path):
                code, out, err = self.set(path, value)
                self.assertEqual(code, 0, err)
                self.assertEqual(read(self.reload()), value)

    def test_package_pin_updates_server_args_too(self):
        code, _, _ = self.set('packages.playwright-mcp.version', '0.0.90')
        self.assertEqual(code, 0)
        belt = self.reload()
        self.assertEqual(belt['packages'][0]['version'], '0.0.90')
        self.assertIn('@playwright/mcp@0.0.90', belt['servers'][2]['args'])

    def test_disallowed_or_invalid_changes_leave_file_unchanged(self):
        before = self.manifest.read_text()
        for path, value in [('servers.github.headersFromEnv', '{}'), ('secretRefs', 'X'),
                            ('servers.github.url', 'http://insecure.example.com'),
                            ('servers.missing.status', 'untested'), ('servers.github.status', 'connected'),
                            ('models.local-ai.presets.ghost.model', 'x'),
                            ('packages.playwright-mcp.version', 'latest')]:
            with self.subTest(path=path):
                code, _, err = self.set(path, value)
                self.assertEqual(code, 1)
                self.assertIn('Update failed', err)
        self.assertEqual(self.manifest.read_text(), before)

    def test_unchanged_value_is_a_no_op(self):
        before = self.manifest.read_text()
        code, out, _ = self.set('servers.github.status', 'needs-credentials')
        self.assertEqual(code, 0)
        self.assertIn('nothing changed', out)
        self.assertEqual(self.manifest.read_text(), before)


class CheckPinsTests(BeltCase):
    def test_version_comparison(self):
        self.assertTrue(check_pins.is_newer('0.0.84', '0.0.83'))
        self.assertTrue(check_pins.is_newer('0.1.0', '0.0.99'))
        self.assertFalse(check_pins.is_newer('0.0.83', '0.0.83'))
        self.assertFalse(check_pins.is_newer('0.0.82', '0.0.83'))
        self.assertFalse(check_pins.is_newer('0.0.90-alpha', '0.0.83'))
        self.assertTrue(check_pins.is_newer('1.7.12.25', '1.7.12.24'))
        self.assertTrue(check_pins.is_newer('1.7.13', '1.7.12.25'))
        self.assertFalse(check_pins.is_newer('1.7.12.25', '1.7.12.25'))
        self.assertFalse(check_pins.is_newer('1.7.12', '1.7.12.25'))
        self.assertFalse(check_pins.is_newer('1.7.12.25-rc1', '1.7.12.24'))

    def test_report_only_does_not_modify(self):
        before = self.manifest.read_text()
        code, out, _ = quiet(check_pins.main, [str(self.manifest)], lookup=lambda kind, name: '0.0.99')
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)[0]['status'], 'newer-available')
        self.assertEqual(self.manifest.read_text(), before)

    def test_apply_bumps_pin_and_server_args(self):
        report = self.root / 'pins.json'
        code, _, _ = quiet(check_pins.main, [str(self.manifest), '--apply', '--report', str(report)],
                           lookup=lambda kind, name: '0.0.99')
        self.assertEqual(code, 0)
        belt = self.reload()
        self.assertEqual(belt['packages'][0]['version'], '0.0.99')
        self.assertIn('@playwright/mcp@0.0.99', belt['servers'][2]['args'])
        self.assertEqual(json.loads(report.read_text())[0]['status'], 'bumped')
        validate(self.manifest)

    def test_lookup_failure_is_reported_without_changes(self):
        def offline(kind, name):
            raise OSError('network unreachable')
        before = self.manifest.read_text()
        code, out, err = quiet(check_pins.main, [str(self.manifest), '--apply'], lookup=offline)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)[0]['status'], 'lookup-failed')
        self.assertIn('network unreachable', err)
        self.assertEqual(self.manifest.read_text(), before)

    def test_files_packages_are_not_looked_up(self):
        seen = []
        check_pins.check(self.reload(), lambda kind, name: seen.append(name) or '0.0.83')
        self.assertEqual(seen, ['@playwright/mcp', '@modelcontextprotocol/inspector', 'zizmor',
                                 'actionlint-py', 'ollmcp'])

    def test_registry_urls(self):
        captured = []

        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(request, timeout):
            captured.append(request.full_url)
            body = {'version': '1.2.3'} if 'npmjs' in request.full_url else {'info': {'version': '4.5.6'}}
            return Response(json.dumps(body).encode())

        with patch.object(check_pins, 'urlopen', fake_urlopen):
            self.assertEqual(check_pins.fetch_latest('npm', '@playwright/mcp'), '1.2.3')
            self.assertEqual(check_pins.fetch_latest('pypi', 'requests'), '4.5.6')
        self.assertEqual(captured, ['https://registry.npmjs.org/@playwright/mcp/latest',
                                    'https://pypi.org/pypi/requests/json'])


class TaskRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / 'out'

    def test_only_allowlisted_tasks_run(self):
        for task in ['rm -rf /', 'validate; echo hi', 'local-ai-check', '']:
            with self.subTest(task=task):
                with self.assertRaises(ValueError):
                    tasks.run(task, self.out)
        with self.assertRaises(ValueError):
            tasks.run('validate', self.out, preset='ollama; ls')

    def test_every_adapter_has_an_export_task(self):
        for adapter in validate(ROOT / 'belt.json')['adapters']:
            self.assertIn(f'export-{adapter}', tasks.TASKS)

    def test_validate_task_writes_log(self):
        self.assertEqual(tasks.run('validate', self.out), 0)
        log = (self.out / 'validate.log').read_text()
        self.assertIn('Valid belt: our-tool-belt', log)
        self.assertIn('[exit 0]', log)

    def test_export_task_writes_artifacts(self):
        self.assertEqual(tasks.run('export-cursor', self.out), 0)
        self.assertTrue((self.out / 'exports/cursor/.cursor/mcp.json').is_file())

    def test_failing_step_returns_nonzero(self):
        self.assertNotEqual(tasks.run('export-opencode', self.out, preset='lm-studio'), 0)
        self.assertIn('has no model', (self.out / 'export-opencode.log').read_text())


if __name__ == '__main__':
    unittest.main()
