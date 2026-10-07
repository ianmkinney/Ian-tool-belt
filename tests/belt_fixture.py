import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def load_script(name):
    spec = importlib.util.spec_from_file_location(f'belt_{name}', ROOT / f'scripts/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BeltCase(unittest.TestCase):
    """Copies the real belt into a temporary directory so tests can edit it freely."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'belt'
        self.source.mkdir()
        for name in ['rules', 'skills', 'styling']:
            shutil.copytree(ROOT / name, self.source / name)
        self.data = json.loads((ROOT / 'belt.json').read_text())
        self.manifest = self.source / 'belt.json'
        self.write()

    def write(self):
        self.manifest.write_text(json.dumps(self.data, indent=2) + '\n')

    def reload(self):
        return json.loads(self.manifest.read_text())
