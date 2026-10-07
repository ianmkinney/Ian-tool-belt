import json
import os
import unittest
from unittest.mock import patch

from belt_fixture import ROOT, BeltCase, load_script
from validate import validate

exporter = load_script('export')
beltfile = load_script('beltfile')

TARGETS = [
    ('claude-code', '.mcp.json', 'mcpServers', '${GITHUB_MCP_TOKEN}'),
    ('vscode', '.vscode/mcp.json', 'servers', '${env:GITHUB_MCP_TOKEN}'),
    ('cursor', '.cursor/mcp.json', 'mcpServers', '${env:GITHUB_MCP_TOKEN}'),
    ('opencode', 'opencode.json', 'mcp', '{env:GITHUB_MCP_TOKEN}'),
]
SKILL_ROOTS = {'claude-code': 'skills', 'vscode': 'skills', 'cursor': '.cursor/skills', 'opencode': '.opencode/skills'}


class BeltTests(BeltCase):
    def invalid(self):
        self.write()
        with self.assertRaises((ValueError, TypeError)):
            validate(self.manifest)

    def test_real_manifests(self):
        self.assertEqual(validate(ROOT / 'belt.json')['name'], 'our-tool-belt')
        self.assertEqual(validate(ROOT / 'examples/personal/belt.json')['formatVersion'], '0.1-draft')

    def test_real_manifest_keeps_its_canonical_formatting(self):
        text = (ROOT / 'belt.json').read_text()
        self.assertEqual(beltfile.dump(json.loads(text)), text)

    def test_all_exports_keep_credentials_symbolic(self):
        secrets = {'GITHUB_MCP_TOKEN': 'SECRET_SENTINEL', 'CONTEXT7_API_KEY': 'OTHER_SECRET',
                   'LOCAL_AI_API_KEY': 'LOCAL_SECRET'}
        with patch.dict(os.environ, secrets):
            for target, relative, key, reference in TARGETS:
                with self.subTest(target=target):
                    out = self.root / target
                    report = exporter.export_belt(self.manifest, target, out)
                    configs = json.loads((out / relative).read_text())[key]
                    self.assertEqual(configs['github']['headers']['Authorization'], 'Bearer ' + reference)
                    self.assertTrue(configs['github']['url'].endswith('/readonly'))
                    playwright = configs['playwright']
                    args = playwright['command'] if target == 'opencode' else playwright['args']
                    self.assertIn('--isolated', args)
                    self.assertEqual(playwright['type'], 'local' if target == 'opencode' else 'stdio')
                    self.assertEqual(report['liveClientTest'], 'not-performed')
                    self.assertEqual(report['localModel']['reachability'], 'not-checked')
                    for p in out.rglob('*'):
                        if p.is_file():
                            for value in secrets.values():
                                self.assertNotIn(value, p.read_text())
                    instructions = (out / 'INSTRUCTIONS.md').read_text()
                    self.assertIn('One pull request per work session', instructions)
                    self.assertIn('Delegate independent work', instructions)
                    self.assertIn('PR titles and releases', instructions)
                    for skill in self.data['skills']:
                        name = skill.split('/')[1]
                        exported = out / SKILL_ROOTS[target] / name / 'SKILL.md'
                        self.assertEqual(exported.read_text(), (self.source / skill).read_text())
                        self.assertIn(f'{SKILL_ROOTS[target]}/{name}/SKILL.md', instructions)

    def test_cursor_export_uses_native_rule_and_skill_locations(self):
        out = self.root / 'cursor'
        report = exporter.export_belt(self.manifest, 'cursor', out)
        rule = (out / '.cursor/rules/engineering.mdc').read_text()
        self.assertTrue(rule.startswith('---\ndescription: "Engineering and pull-request contract"\n'
                                        'alwaysApply: true\n---\n'))
        self.assertIn('One pull request per work session', rule)
        self.assertTrue((out / '.cursor/rules/working-agreement.mdc').is_file())
        self.assertNotIn('type', json.loads((out / '.cursor/mcp.json').read_text())['mcpServers']['github'])
        self.assertEqual(report['rulesAndSkills'], 'native-locations-generated-untested')

    def test_opencode_export_wires_the_default_ollama_preset(self):
        out = self.root / 'opencode'
        report = exporter.export_belt(self.manifest, 'opencode', out)
        config = json.loads((out / 'opencode.json').read_text())
        provider = config['provider']['local-ai']
        self.assertEqual(provider['npm'], '@ai-sdk/openai-compatible')
        self.assertEqual(provider['options'], {'baseURL': 'http://localhost:11434/v1',
                                               'apiKey': '{env:LOCAL_AI_API_KEY}'})
        self.assertEqual(config['model'], 'local-ai/gemma4:e2b')
        self.assertEqual(config['instructions'], ['INSTRUCTIONS.md'])
        self.assertFalse(config['mcp']['github']['oauth'])
        self.assertNotIn('oauth', config['mcp']['playwright'])
        self.assertEqual(report['localModel']['clientWiring'], 'provider-config-generated')

    def test_opencode_preset_without_model_fails_before_writing(self):
        out = self.root / 'lm'
        with self.assertRaisesRegex(ValueError, 'has no model'):
            exporter.export_belt(self.manifest, 'opencode', out, preset='lm-studio')
        self.assertFalse(out.exists())
        self.data['models'][0]['presets']['lm-studio']['model'] = 'qwen-local'
        self.write()
        exporter.export_belt(self.manifest, 'opencode', out, preset='lm-studio')
        config = json.loads((out / 'opencode.json').read_text())
        self.assertEqual(config['provider']['local-ai']['options']['baseURL'], 'http://localhost:1234/v1')

    def test_unknown_preset_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unknown preset'):
            exporter.export_belt(self.manifest, 'cursor', self.root / 'x', preset='nope')

    def test_env_example_lists_ollama_defaults_and_alternatives(self):
        out = self.root / 'vscode'
        exporter.export_belt(self.manifest, 'vscode', out)
        example = (out / 'local-ai.env.example').read_text()
        self.assertIn('LOCAL_AI_BASE_URL=http://localhost:11434/v1\n', example)
        self.assertIn('LOCAL_AI_MODEL=gemma4:e2b\n', example)
        self.assertIn('LOCAL_AI_API_KEY=\n', example)
        self.assertIn('# lm-studio: LOCAL_AI_BASE_URL=http://localhost:1234/v1', example)

    def test_personal_connections_are_opt_in(self):
        self.data['personalServers'] = [{'id': 'home-notes', 'transport': 'http',
                                         'url': 'https://notes.example.com/mcp', 'headersFromEnv': {},
                                         'status': 'untested'}]
        self.write()
        work = self.root / 'work'
        report = exporter.export_belt(self.manifest, 'claude-code', work)
        self.assertNotIn('home-notes', json.loads((work / '.mcp.json').read_text())['mcpServers'])
        self.assertEqual(report['personalConnections'], 'excluded')
        home = self.root / 'home'
        report = exporter.export_belt(self.manifest, 'claude-code', home, include_personal=True)
        self.assertIn('home-notes', json.loads((home / '.mcp.json').read_text())['mcpServers'])
        self.assertEqual(report['personalConnections'], 'included')

    def test_personal_and_work_server_ids_must_not_collide(self):
        self.data['personalServers'] = [dict(self.data['servers'][1])]
        self.invalid()

    def test_skill_support_files_are_exported_but_symlinks_are_not(self):
        folder = self.source / 'skills/evaluate-mcp'
        (folder / 'references').mkdir()
        (folder / 'references/checklist.md').write_text('checklist')
        outside = self.root / 'private.txt'
        outside.write_text('private')
        (folder / 'leak.txt').symlink_to(outside)
        out = self.root / 'cursor'
        exporter.export_belt(self.manifest, 'cursor', out)
        self.assertEqual((out / '.cursor/skills/evaluate-mcp/references/checklist.md').read_text(), 'checklist')
        self.assertFalse((out / '.cursor/skills/evaluate-mcp/leak.txt').exists())

    def test_existing_output_is_untouched(self):
        out = self.root / 'existing'
        out.mkdir()
        (out / 'keep').write_text('mine')
        with self.assertRaises(ValueError):
            exporter.export_belt(self.manifest, 'cursor', out)
        self.assertEqual(list(out.iterdir()), [out / 'keep'])
        self.assertEqual((out / 'keep').read_text(), 'mine')

    def test_unknown_target_does_not_write(self):
        out = self.root / 'unknown'
        with self.assertRaises(ValueError):
            exporter.export_belt(self.manifest, 'chatgpt', out)
        self.assertFalse(out.exists())

    def test_undeclared_target_does_not_write(self):
        self.data['adapters'] = ['claude-code']
        self.write()
        out = self.root / 'cursor'
        with self.assertRaises(ValueError):
            exporter.export_belt(self.manifest, 'cursor', out)
        self.assertFalse(out.exists())

    def test_traversal_and_symlinks_are_rejected(self):
        outside = self.root / 'private.md'
        outside.write_text('private')
        for value in ['../private.md', str(outside), 'missing.md']:
            with self.subTest(value=value):
                self.data['rules'] = [value]
                self.invalid()
        (self.source / 'link.md').symlink_to(outside)
        self.data['rules'] = ['link.md']
        self.invalid()

    def test_duplicate_server_is_rejected(self):
        self.data['servers'].append(self.data['servers'][0])
        self.invalid()

    def test_undeclared_secret_is_rejected(self):
        self.data['secretRefs'] = []
        self.invalid()

    def test_unsafe_urls_are_rejected(self):
        for url in ['http://example.com/mcp', 'https://user:password@example.com/mcp',
                    'https://example.com/mcp?token=abc', 'http://localhost:3000/mcp']:
            with self.subTest(url=url):
                self.data['servers'][0]['url'] = url
                self.invalid()

    def test_literal_headers_are_rejected(self):
        self.data['servers'][0]['headers'] = {'Authorization': 'secret'}
        self.invalid()

    def test_invalid_skill_metadata_is_rejected(self):
        (self.source / self.data['skills'][0]).write_text('No frontmatter')
        self.invalid()

    def test_skill_name_must_match_folder(self):
        path = self.source / self.data['skills'][0]
        path.write_text(path.read_text().replace('name: build-api-slice', 'name: other-name'))
        self.invalid()

    def test_invalid_manifest_variants(self):
        baseline = json.loads(json.dumps(self.data))
        for field, value in [('formatVersion', '9'), ('name', 'Bad Name'), ('version', 'latest'),
                             ('rules', 'rules.md'), ('description', False), ('adapters', ['unknown']),
                             ('secretRefs', ['bad-token']), ('skills', [None]), ('packages', {}),
                             ('models', None), ('personalServers', 'none')]:
            with self.subTest(field=field):
                self.data = json.loads(json.dumps(baseline))
                self.data[field] = value
                self.invalid()

    def test_new_sections_require_format_03(self):
        self.data['formatVersion'] = '0.2-draft'
        self.invalid()
        for key in ['models', 'packages', 'personalServers']:
            self.data.pop(key)
        self.data['secretRefs'] = ['GITHUB_MCP_TOKEN', 'CONTEXT7_API_KEY']
        self.invalid()
        self.data['adapters'] = ['claude-code', 'vscode']
        self.write()
        self.assertEqual(validate(self.manifest)['formatVersion'], '0.2-draft')
        out = self.root / 'legacy'
        report = exporter.export_belt(self.manifest, 'vscode', out)
        self.assertNotIn('localModel', report)
        self.assertFalse((out / 'local-ai.env.example').exists())

    def test_invalid_server_variants(self):
        baseline = json.loads(json.dumps(self.data))
        for key, value in [('transport', 'sse'), ('status', 'connected'), ('id', 'Bad ID'),
                           ('headersFromEnv', []), ('url', None)]:
            with self.subTest(key=key):
                self.data = json.loads(json.dumps(baseline))
                self.data['servers'][0][key] = value
                self.invalid()
        self.data = json.loads(json.dumps(baseline))
        self.data['servers'][2]['args'] = 'shell'
        self.invalid()

    def test_invalid_model_variants(self):
        baseline = json.loads(json.dumps(self.data))
        cases = [
            lambda m: m.update(api='anthropic'),
            lambda m: m.update(defaultPreset='missing'),
            lambda m: m.update(presets={}),
            lambda m: m['env'].update(apiKey='UNDECLARED_KEY'),
            lambda m: m['env'].update(baseUrl='lower_case'),
            lambda m: m['presets']['ollama'].update(baseUrl='http://192.168.1.20:11434/v1'),
            lambda m: m['presets']['ollama'].update(baseUrl='http://user:pw@localhost:11434/v1'),
            lambda m: m['presets']['ollama'].update(docs='http://example.com'),
            lambda m: m['presets']['ollama'].update(token='x'),
            lambda m: m.update(status='connected'),
        ]
        for index, mutate in enumerate(cases):
            with self.subTest(case=index):
                self.data = json.loads(json.dumps(baseline))
                mutate(self.data['models'][0])
                self.invalid()

    def test_loopback_and_https_model_urls_are_allowed(self):
        for url in ['http://127.0.0.1:11434/v1', 'http://[::1]:1234/v1', 'https://ai.example.com/v1']:
            with self.subTest(url=url):
                self.data['models'][0]['presets']['ollama']['baseUrl'] = url
                self.write()
                validate(self.manifest)

    def test_invalid_package_variants(self):
        baseline = json.loads(json.dumps(self.data))
        cases = [
            lambda p: p[0].update(version='^0.0.83'),
            lambda p: p[0].update(version='latest'),
            lambda p: p[0].update(kind='cargo'),
            lambda p: p[0].update(name='Not A Name'),
            lambda p: p[0].update(description=''),
            lambda p: p[1].update(path='../outside'),
            lambda p: p[1].update(path='missing'),
            lambda p: p.append(dict(p[0])),
        ]
        for index, mutate in enumerate(cases):
            with self.subTest(case=index):
                self.data = json.loads(json.dumps(baseline))
                mutate(self.data['packages'])
                self.invalid()

    def test_files_package_requires_readme(self):
        (self.source / 'styling/README.md').unlink()
        self.invalid()

    def test_server_args_must_match_npm_pin(self):
        self.data['packages'][0]['version'] = '0.0.84'
        self.invalid()

    def test_zizmor_workflow_uses_the_belt_pin(self):
        pin = next(p for p in validate(ROOT / 'belt.json')['packages'] if p['id'] == 'zizmor')
        self.assertEqual((pin['kind'], pin['name']), ('pypi', 'zizmor'))
        workflow = (ROOT / '.github/workflows/zizmor.yml').read_text()
        self.assertRegex(workflow, r'uses: zizmorcore/zizmor-action@[0-9a-f]{40} # v')
        self.assertIn('version: ${{ steps.pin.outputs.version }}', workflow)
        self.assertNotIn(pin['version'], workflow)

    def test_rule_edit_reaches_every_client(self):
        p = self.source / self.data['rules'][0]
        p.write_text(p.read_text() + '\nUpdated shared rule.\n')
        for target, *_ in TARGETS:
            out = self.root / target
            exporter.export_belt(self.manifest, target, out)
            self.assertIn('Updated shared rule.', (out / 'INSTRUCTIONS.md').read_text())
        self.assertIn('Updated shared rule.',
                      (self.root / 'cursor/.cursor/rules/working-agreement.mdc').read_text())


if __name__ == '__main__':
    unittest.main()
