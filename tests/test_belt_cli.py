import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from belt_fixture import ROOT, BeltCase, load_script

spec = importlib.util.spec_from_file_location('belt_cli', ROOT / 'belt.py')
belt_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(belt_cli)
belt_index = load_script('belt_index')
validate = load_script('validate')


class DetectTargetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Path(self.temp.name)

    def test_empty_project_defaults_to_cursor(self):
        self.assertEqual(belt_cli.detect_target(self.app), 'cursor')

    def test_explicit_target_wins(self):
        (self.app / '.cursor').mkdir()
        self.assertEqual(belt_cli.detect_target(self.app, 'opencode'), 'opencode')

    def test_cursor_dir_is_detected(self):
        (self.app / '.cursor').mkdir()
        self.assertEqual(belt_cli.detect_target(self.app), 'cursor')

    def test_opencode_json_is_detected(self):
        (self.app / 'opencode.json').write_text('{}')
        self.assertEqual(belt_cli.detect_target(self.app), 'opencode')

    def test_multiple_clients_require_an_explicit_target(self):
        (self.app / '.cursor').mkdir()
        (self.app / 'opencode.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Multiple clients'):
            belt_cli.detect_target(self.app)

    def test_vscode_folder_alone_is_not_a_client_marker(self):
        (self.app / '.vscode').mkdir()
        self.assertEqual(belt_cli.detect_target(self.app), 'cursor')


class UseBeltTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Path(self.temp.name) / 'app'
        self.app.mkdir()

    def test_use_writes_cursor_files_into_an_empty_project(self):
        result = belt_cli.use_belt(ROOT / 'belt.json', self.app, target='cursor')
        self.assertEqual(result['target'], 'cursor')
        self.assertTrue((self.app / '.cursor/mcp.json').is_file())
        self.assertTrue((self.app / '.cursor/rules/engineering.mdc').is_file())
        self.assertTrue((self.app / '.cursor/skills/build-api-slice/SKILL.md').is_file())
        servers = json.loads((self.app / '.cursor/mcp.json').read_text())['mcpServers']
        self.assertEqual(set(servers), {'github', 'context7', 'playwright'})
        self.assertNotIn('home-notes', servers)
        self.assertTrue(result['copy']['written'])
        self.assertFalse(result['copy']['skipped'])

    def test_use_leaves_existing_files_alone_without_force(self):
        (self.app / '.cursor').mkdir()
        (self.app / '.cursor/mcp.json').write_text('mine')
        result = belt_cli.use_belt(ROOT / 'belt.json', self.app, target='cursor')
        self.assertEqual((self.app / '.cursor/mcp.json').read_text(), 'mine')
        self.assertIn('.cursor/mcp.json', result['copy']['skipped'])
        self.assertTrue((self.app / '.cursor/skills/build-api-slice/SKILL.md').is_file())

    def test_force_overwrites(self):
        (self.app / '.cursor').mkdir()
        (self.app / '.cursor/mcp.json').write_text('mine')
        belt_cli.use_belt(ROOT / 'belt.json', self.app, target='cursor', force=True)
        servers = json.loads((self.app / '.cursor/mcp.json').read_text())['mcpServers']
        self.assertIn('playwright', servers)

    def test_out_writes_a_fresh_export_directory(self):
        out = Path(self.temp.name) / 'dist-cursor'
        result = belt_cli.use_belt(ROOT / 'belt.json', self.app, target='cursor', out=out)
        self.assertIsNone(result['copy'])
        self.assertTrue((out / '.cursor/mcp.json').is_file())
        self.assertFalse((self.app / '.cursor').exists())

    def test_cli_use_returns_error_when_files_are_skipped(self):
        (self.app / '.cursor').mkdir()
        (self.app / '.cursor/mcp.json').write_text('mine')
        code = belt_cli.main(['use', 'cursor', '--app', str(self.app)])
        self.assertEqual(code, 1)


class DoctorListIndexTests(unittest.TestCase):
    def test_offline_doctor_reports_missing_env_and_stays_green(self):
        environ = {k: v for k, v in os.environ.items()
                   if k not in ('GITHUB_MCP_TOKEN', 'CONTEXT7_API_KEY', 'LOCAL_AI_API_KEY')}
        with patch.dict(os.environ, environ, clear=True):
            result = belt_cli.doctor_belt(ROOT / 'belt.json', os.environ, offline=True)
        names = {item['name']: item for item in result['env']}
        self.assertFalse(names['GITHUB_MCP_TOKEN']['set'])
        self.assertTrue(names['LOCAL_AI_API_KEY']['optional'])
        self.assertTrue(belt_cli.doctor_ok(result, strict=False))
        self.assertFalse(belt_cli.doctor_ok(result, strict=True))
        self.assertIsNone(result['localAi'])
        self.assertIsNone(result['pins'])

    def test_list_json_omits_personal_server_details(self):
        index = belt_index.build(ROOT / 'belt.json')
        self.assertEqual(index['personalServers']['count'], 0)
        self.assertNotIn('servers', index['personalServers'])
        ids = {item['id'] for item in index['packages']}
        self.assertEqual(ids, {'playwright-mcp', 'mcp-inspector', 'styling', 'breakroom', 'zizmor',
                               'actionlint', 'shellcheck', 'gitleaks', 'ollmcp'})
        self.assertTrue(any(item['id'] == 'github' for item in index['servers']))
        self.assertTrue(any(item['id'] == 'cursor' for item in index['adapters']))

    def test_generated_index_matches_checked_in_files(self):
        index = belt_index.build(ROOT / 'belt.json')
        self.assertEqual(belt_index.check(index), [])

    def test_index_check_fails_when_the_file_is_stale(self):
        original = (ROOT / 'belt.index.json').read_text()
        self.addCleanup(lambda: (ROOT / 'belt.index.json').write_text(original))
        (ROOT / 'belt.index.json').write_text('{}\n')
        self.assertEqual(belt_cli.main(['index', '--check']), 1)

    def test_cli_list_json_equals_checked_in_index(self):
        from io import StringIO
        with patch('sys.stdout', new=StringIO()) as out:
            code = belt_cli.main(['list', '--json'])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), (ROOT / 'belt.index.json').read_text())


class DescriptionSchemaTests(BeltCase):
    def test_server_description_must_be_one_line(self):
        self.data['servers'][0]['description'] = 'line one\nline two'
        self.write()
        with self.assertRaises((ValueError, TypeError)):
            validate.validate(self.manifest)

    def test_every_declared_adapter_has_export_info(self):
        belt = validate.validate(ROOT / 'belt.json')
        self.assertEqual(set(belt['adapters']), set(validate.ADAPTERS))
        for name in belt['adapters']:
            self.assertIn('description', validate.ADAPTER_INFO[name])


class DocLinkTests(unittest.TestCase):
    def test_relative_markdown_links_resolve(self):
        import re
        pattern = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
        roots = [ROOT / 'README.md', ROOT / 'AGENTS.md', ROOT / 'CONTRIBUTING.md',
                 *sorted((ROOT / 'docs').glob('*.md')), ROOT / 'connections/README.md',
                 ROOT / 'skills/README.md']
        missing = []
        for path in roots:
            for match in pattern.finditer(path.read_text()):
                target = match.group(1)
                if target.startswith(('http://', 'https://', 'mailto:', '#')):
                    continue
                relative, _, _anchor = target.partition('#')
                if not relative:
                    continue
                dest = (path.parent / relative).resolve()
                if not dest.exists():
                    missing.append(f'{path.relative_to(ROOT)} -> {target}')
        self.assertEqual(missing, [])


class WrapperTests(BeltCase):
    def test_add_skill_wraps_new_py(self):
        code = belt_cli.main(['--belt', str(self.manifest), 'add', 'skill', 'review-sql',
                              '--description', 'Review SQL changes. Use when a migration changes.'])
        self.assertEqual(code, 0)
        self.assertIn('skills/review-sql/SKILL.md', self.reload()['skills'])

    def test_set_wraps_belt_set(self):
        code = belt_cli.main(['--belt', str(self.manifest), 'set', 'servers.playwright.status', 'untested'])
        self.assertEqual(code, 0)
        self.assertEqual(self.reload()['servers'][2]['status'], 'untested')


if __name__ == '__main__':
    unittest.main()
