import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import belt_sync
import check_belt_workflow_pins as pins


class BeltWorkflowPinTests(unittest.TestCase):
    def test_substitute_placeholders(self):
        raw = ('uses: ianmkinney/Ian-tool-belt/.github/workflows/belt-sync-reusable.yml@__BELT_SHA__ '
               '# v__BELT_VERSION__\n  belt-ref: __BELT_SHA__\n')
        out = belt_sync.substitute_belt_pins(raw, 'a' * 40, '0.4.0')
        self.assertIn(f'@{"a" * 40} # v0.4.0', out)
        self.assertIn(f'belt-ref: {"a" * 40}', out)
        self.assertNotIn('__BELT_SHA__', out)

    def test_substitute_bumps_existing_pin(self):
        old = 'a' * 40
        new = 'b' * 40
        raw = (f'uses: ianmkinney/Ian-tool-belt/.github/workflows/pr-title-reusable.yml@{old} # v0.3.0\n')
        out = belt_sync.substitute_belt_pins(raw, new, '0.4.0')
        self.assertIn(f'@{new} # v0.4.0', out)
        self.assertNotIn(old, out)

    def test_guard_catches_main(self):
        with tempfile.TemporaryDirectory() as temp:
            wf = Path(temp) / 'workflows'
            wf.mkdir(parents=True)
            (wf / 'bad.yml').write_text(
                'uses: ianmkinney/Ian-tool-belt/.github/workflows/pr-title-reusable.yml@main\n')
            hits = pins.find_main_pins([Path(temp)])
            self.assertEqual(len(hits), 1)

    def test_templates_use_placeholders_not_main(self):
        hits = pins.find_main_pins([ROOT / 'templates'])
        self.assertEqual(hits, [])
        for path in [
            ROOT / 'templates/app-adoption/.github/workflows/belt.yml',
            ROOT / 'templates/app-adoption/.github/workflows/belt-sync.yml',
            ROOT / 'templates/versioning/release.yml',
            ROOT / 'templates/versioning/pr-title.yml',
        ]:
            text = path.read_text()
            self.assertIn('@__BELT_SHA__', text)
            self.assertIn('v__BELT_VERSION__', text)
            self.assertNotIn('@main', text)


if __name__ == '__main__':
    unittest.main()
