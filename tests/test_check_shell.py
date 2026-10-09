import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_shell


class CheckShellTests(unittest.TestCase):
    def test_discover_finds_suffix_and_shebang(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'tracked.sh').write_text('#!/bin/sh\necho ok\n')
            script = root / 'bin' / 'tool'
            script.parent.mkdir()
            script.write_text('#!/usr/bin/env bash\necho ok\n')
            subprocess.run(['git', 'init'], cwd=root, check=True, capture_output=True)
            subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)
            found = {p.name for p in check_shell.discover(root)}
            self.assertEqual(found, {'tracked.sh', 'tool'})

    def test_run_succeeds_with_no_scripts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(['git', 'init'], cwd=root, check=True, capture_output=True)
            self.assertEqual(check_shell.main(['--root', str(root), '--shellcheck', 'false']), 0)

    def test_run_reports_shellcheck_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'bad.sh').write_text('#!/bin/sh\nunset foo\n$foo\n')
            subprocess.run(['git', 'init'], cwd=root, check=True, capture_output=True)
            subprocess.run(['git', 'add', '.'], cwd=root, check=True, capture_output=True)
            shellcheck = Path(subprocess.check_output(['bash', '-lc', 'command -v shellcheck'],
                                                      text=True).strip())
            self.assertNotEqual(check_shell.main(['--root', str(root), '--shellcheck', str(shellcheck)]), 0)


if __name__ == '__main__':
    unittest.main()
