import contextlib
import io
import json
import unittest

from belt_fixture import ROOT, load_script

build = load_script('build_tokens')
TOKENS = json.loads((ROOT / 'styling/tokens.json').read_text())


class StylingTests(unittest.TestCase):
    def test_css_is_generated_from_json(self):
        self.assertEqual((ROOT / 'styling/tokens.css').read_text(), build.render(TOKENS))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(build.main(['--check']), 0)

    def test_brand_palette_matches_branding_guide(self):
        guide = (ROOT / 'branding/README.md').read_text()
        for name in ['charcoal', 'cream', 'brass', 'teal']:
            hex_value = TOKENS['color'][name]
            self.assertRegex(guide, rf'{name} `{hex_value}`')

    def test_site_css_includes_blueprint_tokens(self):
        build = load_script('build_site')
        css = build.css_text(ROOT)
        for name in ['blueprint-navy', 'blueprint-cyan', 'blueprint-amber']:
            self.assertIn(f'--tb-color-{name}: {TOKENS["color"][name]}', css)

    def test_package_version_matches_tokens(self):
        belt = json.loads((ROOT / 'belt.json').read_text())
        styling = next(p for p in belt['packages'] if p['id'] == 'styling')
        self.assertEqual(styling['version'], TOKENS['version'])


if __name__ == '__main__':
    unittest.main()
