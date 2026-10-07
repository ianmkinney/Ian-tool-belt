import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate import validate_adoption

WORKFLOWS = ROOT / '.github/workflows'
VERSIONING = ROOT / 'templates/versioning'
ADOPTION = ROOT / 'templates/app-adoption'
REMOTE = 'ianmkinney/Ian-tool-belt/.github/workflows/'
TYPES = {'feat', 'fix', 'chore', 'docs', 'refactor', 'test', 'ci', 'perf', 'build', 'revert'}


def load_yaml(path):
    data = yaml.safe_load(path.read_text())
    # YAML 1.1 reads the bare key `on` as boolean true.
    data['on'] = data.pop(True, data.get('on'))
    return data


def load_json(path):
    return json.loads(path.read_text())


def called_workflows(workflow):
    return {job['uses'] for job in workflow['jobs'].values() if 'uses' in job}


class VersioningTests(unittest.TestCase):
    def test_all_workflow_yaml_parses(self):
        paths = [*WORKFLOWS.glob('*.yml'), *VERSIONING.glob('*.yml'),
                 *(ADOPTION / '.github/workflows').glob('*.yml')]
        self.assertGreaterEqual(len(paths), 7)
        for path in paths:
            with self.subTest(path=path.name):
                workflow = load_yaml(path)
                self.assertTrue(workflow['on'])
                self.assertTrue(workflow['jobs'])

    def test_release_please_reusable_workflow(self):
        workflow = load_yaml(WORKFLOWS / 'release-please-reusable.yml')
        inputs = workflow['on']['workflow_call']['inputs']
        self.assertEqual(inputs['release-type']['default'], 'node')
        self.assertEqual(inputs['config-file']['default'], '')
        self.assertIn('manifest-file', inputs)
        job = workflow['jobs']['release-please']
        self.assertEqual(job['permissions'], {'contents': 'write', 'pull-requests': 'write'})
        self.assertEqual(job['steps'][0]['uses'], 'googleapis/release-please-action@v4')

    def test_pr_title_reusable_workflow(self):
        workflow = load_yaml(WORKFLOWS / 'pr-title-reusable.yml')
        self.assertIn('workflow_call', workflow['on'])
        step = workflow['jobs']['conventional-title']['steps'][0]
        self.assertEqual(step['uses'], 'amannn/action-semantic-pull-request@v5')
        self.assertEqual(set(step['with']['types'].split()), TYPES)

    def test_repo_callers_use_local_reusable_workflows(self):
        self.assertEqual(called_workflows(load_yaml(WORKFLOWS / 'release.yml')),
                         {'./.github/workflows/release-please-reusable.yml'})
        self.assertEqual(called_workflows(load_yaml(WORKFLOWS / 'pr-title.yml')),
                         {'./.github/workflows/pr-title-reusable.yml'})

    def test_template_callers_reference_published_workflows(self):
        expected = {
            VERSIONING / 'release.yml': {REMOTE + 'release-please-reusable.yml@main'},
            VERSIONING / 'pr-title.yml': {REMOTE + 'pr-title-reusable.yml@main'},
            ADOPTION / '.github/workflows/belt.yml': {REMOTE + 'release-please-reusable.yml@main',
                                                      REMOTE + 'pr-title-reusable.yml@main'},
            ADOPTION / '.github/workflows/belt-sync.yml': {REMOTE + 'belt-sync-reusable.yml@main'},
        }
        for path, uses in expected.items():
            with self.subTest(path=path.name):
                self.assertEqual(called_workflows(load_yaml(path)), uses)
                for target in uses:
                    self.assertTrue((WORKFLOWS / target.split('/')[-1].split('@')[0]).is_file())

    def test_manifest_matches_belt_version(self):
        version = load_json(ROOT / 'belt.json')['version']
        self.assertEqual(load_json(ROOT / '.release-please-manifest.json'), {'.': version})
        self.assertEqual(validate_adoption(ADOPTION)['beltVersion'], version)

    def test_release_please_bumps_belt_files(self):
        package = load_json(ROOT / 'release-please-config.json')['packages']['.']
        self.assertEqual(package['release-type'], 'simple')
        bumped = {(f['path'], f['jsonpath']) for f in package['extra-files']}
        self.assertEqual(bumped, {('belt.json', '$.version'),
                                  ('templates/app-adoption/.tool-belt.json', '$.beltVersion')})
        for path, _ in bumped:
            self.assertTrue((ROOT / path).is_file())

    def test_versioning_templates_exist_and_parse(self):
        for name in ['release.yml', 'pr-title.yml', 'release-please-config.json',
                     '.release-please-manifest.json', 'README.md']:
            self.assertTrue((VERSIONING / name).is_file(), name)
        config = load_json(VERSIONING / 'release-please-config.json')
        self.assertEqual(config['packages']['.']['release-type'], 'node')
        self.assertIn('.', load_json(VERSIONING / '.release-please-manifest.json'))
        readme = (VERSIONING / 'README.md').read_text()
        for phrase in ['Workflow permissions', 'create and approve pull requests',
                       'squash', 'VERCEL_GIT_COMMIT_SHA', 'SOURCE_COMMIT', 'GIT_SHA']:
            self.assertIn(phrase, readme)

    def test_adoption_agent_files_point_to_belt_rules(self):
        rule = (ADOPTION / '.cursor/rules/tool-belt.mdc').read_text()
        front = yaml.safe_load(rule.split('---')[1])
        self.assertIs(front['alwaysApply'], True)
        self.assertTrue(front['description'])
        for text in [(ADOPTION / 'AGENTS.md').read_text(), rule]:
            for phrase in ['https://github.com/ianmkinney/Ian-tool-belt', 'rules/engineering.md',
                           'rules/working-agreement.md', 'draft PR', 'Conventional Commit',
                           'release-please', 'Secrets', 'CI green', 'Tests for every change']:
                self.assertIn(phrase.lower(), text.lower())

    def test_adoption_marker_rejects_bad_markers(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / '.tool-belt.json'
            for data in [{'belt': 'someone/else', 'beltVersion': '0.2.0'},
                         {'belt': 'ianmkinney/Ian-tool-belt', 'beltVersion': 'latest'},
                         {'belt': 'ianmkinney/Ian-tool-belt'},
                         ['ianmkinney/Ian-tool-belt']]:
                with self.subTest(data=data):
                    marker.write_text(json.dumps(data))
                    with self.assertRaises(ValueError):
                        validate_adoption(temp)
            Path(marker).unlink()
            with self.assertRaises(OSError):
                validate_adoption(temp)


if __name__ == '__main__':
    unittest.main()
