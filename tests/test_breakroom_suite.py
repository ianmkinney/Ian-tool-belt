"""Load the breakroom tool's unittest module into the belt test run."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BREAKROOM_TESTS = ROOT / 'tools' / 'breakroom' / 'tests'


def load_tests(loader, standard_tests, pattern):
    path = str(BREAKROOM_TESTS)
    if path not in sys.path:
        sys.path.insert(0, path)
    import test_breakroom  # noqa: WPS433 — intentional path-based import for fork pickling

    return loader.loadTestsFromModule(test_breakroom)
