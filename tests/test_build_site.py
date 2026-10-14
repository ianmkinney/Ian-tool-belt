import json
import tempfile
import unittest
from pathlib import Path

from belt_fixture import ROOT, load_script

build_site = load_script('build_site')


class BuildSiteTests(unittest.TestCase):
    def test_build_succeeds_and_covers_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'site'
            code = build_site.main(['--out', str(out), '--base', '/Ian-tool-belt/'])
            self.assertEqual(code, 0)
            self.assertTrue((out / 'index.html').is_file())
            index = json.loads((ROOT / 'belt.index.json').read_text())
            errors = build_site.validate_site(out, index, '/Ian-tool-belt/')
            self.assertEqual(errors, [])
            self.assertIn('--tb-color-blueprint-navy', (out / 'assets/style.css').read_text())
            self.assertIn('prefers-reduced-motion', (out / 'assets/style.css').read_text())

    def test_check_flag_runs_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'site'
            self.assertEqual(build_site.main(['--out', str(out), '--check']), 0)


if __name__ == '__main__':
    unittest.main()
