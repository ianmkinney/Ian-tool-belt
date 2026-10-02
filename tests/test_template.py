import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate import validate
spec=importlib.util.spec_from_file_location('belt_export',ROOT/'scripts/export.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TemplateTests(unittest.TestCase):
    def test_manifest_references_are_valid(self):
        validate(ROOT/'belt.json')

    def test_export_both_targets(self):
        belt=validate(ROOT/'belt.json')
        with tempfile.TemporaryDirectory() as temp:
            for target,path,key in [('claude-code','.mcp.json','mcpServers'),('vscode','.vscode/mcp.json','servers')]:
                out=Path(temp)/target
                report=module.export_belt(ROOT/'belt.json',target,out)
                data=json.loads((out/path).read_text())
                self.assertEqual(set(data[key]),{server['id'] for server in belt['servers']})
                self.assertEqual(report['authentication'],'not-performed')
                self.assertIn('One pull request per work session',(out/'INSTRUCTIONS.md').read_text())

    def test_existing_output_is_protected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                module.export_belt(ROOT/'belt.json','vscode',temp)

if __name__=='__main__':
    unittest.main()
