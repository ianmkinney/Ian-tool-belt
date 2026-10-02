import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate import validate
spec = importlib.util.spec_from_file_location('belt_export', ROOT / 'scripts/export.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class BeltTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'belt'
        self.source.mkdir()
        for name in ['rules', 'skills']:
            shutil.copytree(ROOT / name, self.source / name)
        self.data = json.loads((ROOT / 'belt.json').read_text())
        self.manifest = self.source / 'belt.json'
        self.write()

    def write(self):
        self.manifest.write_text(json.dumps(self.data))

    def invalid(self):
        self.write()
        with self.assertRaises((ValueError, TypeError)):
            validate(self.manifest)

    def test_real_manifests(self):
        self.assertEqual(validate(ROOT / 'belt.json')['name'], 'our-tool-belt')
        self.assertEqual(validate(ROOT / 'examples/personal/belt.json')['formatVersion'], '0.1-draft')

    def test_both_exports_keep_credentials_symbolic(self):
        with patch.dict(os.environ, {'GITHUB_MCP_TOKEN':'SECRET_SENTINEL', 'CONTEXT7_API_KEY':'OTHER_SECRET'}):
            for target, relative, key, reference in [
                ('claude-code','.mcp.json','mcpServers','${GITHUB_MCP_TOKEN}'),
                ('vscode','.vscode/mcp.json','servers','${env:GITHUB_MCP_TOKEN}')]:
                out = self.root / target
                report = exporter.export_belt(self.manifest,target,out)
                configs = json.loads((out/relative).read_text())[key]
                self.assertEqual(configs['github']['headers']['Authorization'], 'Bearer '+reference)
                self.assertTrue(configs['github']['url'].endswith('/readonly'))
                self.assertIn('--isolated',configs['playwright']['args'])
                self.assertEqual(configs['playwright']['type'],'stdio')
                self.assertEqual(report['liveClientTest'],'not-performed')
                for p in out.rglob('*'):
                    if p.is_file():
                        self.assertNotIn('SECRET_SENTINEL',p.read_text())
                        self.assertNotIn('OTHER_SECRET',p.read_text())
                self.assertIn('One pull request per work session',(out/'INSTRUCTIONS.md').read_text())
                for skill in self.data['skills']:
                    self.assertEqual((out/skill).read_text(),(self.source/skill).read_text())

    def test_existing_output_is_untouched(self):
        out=self.root/'existing';out.mkdir();(out/'keep').write_text('mine')
        with self.assertRaises(ValueError):
            exporter.export_belt(self.manifest,'vscode',out)
        self.assertEqual(list(out.iterdir()),[out/'keep'])
        self.assertEqual((out/'keep').read_text(),'mine')

    def test_unknown_target_does_not_write(self):
        out=self.root/'unknown'
        with self.assertRaises(ValueError):
            exporter.export_belt(self.manifest,'chatgpt',out)
        self.assertFalse(out.exists())

    def test_traversal_and_symlinks_are_rejected(self):
        outside=self.root/'private.md';outside.write_text('private')
        for value in ['../private.md',str(outside),'missing.md']:
            with self.subTest(value=value):
                self.data['rules']=[value];self.invalid()
        (self.source/'link.md').symlink_to(outside)
        self.data['rules']=['link.md'];self.invalid()

    def test_duplicate_server_is_rejected(self):
        self.data['servers'].append(self.data['servers'][0]);self.invalid()

    def test_undeclared_secret_is_rejected(self):
        self.data['secretRefs']=[];self.invalid()

    def test_unsafe_urls_are_rejected(self):
        for url in ['http://example.com/mcp','https://user:password@example.com/mcp','https://example.com/mcp?token=abc']:
            with self.subTest(url=url):
                self.data['servers'][0]['url']=url;self.invalid()

    def test_literal_headers_are_rejected(self):
        self.data['servers'][0]['headers']={'Authorization':'secret'};self.invalid()

    def test_invalid_skill_metadata_is_rejected(self):
        (self.source/self.data['skills'][0]).write_text('No frontmatter');self.invalid()

    def test_invalid_manifest_variants(self):
        baseline=json.loads(json.dumps(self.data))
        for field,value in [('formatVersion','9'),('name','Bad Name'),('version','latest'),
                            ('rules','rules.md'),('description',False),('adapters',['unknown']),
                            ('secretRefs',['bad-token']),('skills',[None])]:
            with self.subTest(field=field):
                self.data=json.loads(json.dumps(baseline));self.data[field]=value;self.invalid()

    def test_invalid_server_variants(self):
        baseline=json.loads(json.dumps(self.data))
        for key,value in [('transport','sse'),('status','connected'),('id','Bad ID'),
                          ('headersFromEnv',[]),('url',None)]:
            with self.subTest(key=key):
                self.data=json.loads(json.dumps(baseline));self.data['servers'][0][key]=value;self.invalid()
        self.data=json.loads(json.dumps(baseline));self.data['servers'][2]['args']='shell';self.invalid()

    def test_rule_edit_reaches_both_clients(self):
        p=self.source/self.data['rules'][0];p.write_text(p.read_text()+'\nUpdated shared rule.\n')
        for target in ['claude-code','vscode']:
            out=self.root/target;exporter.export_belt(self.manifest,target,out)
            self.assertIn('Updated shared rule.',(out/'INSTRUCTIONS.md').read_text())


if __name__ == '__main__':
    unittest.main()
