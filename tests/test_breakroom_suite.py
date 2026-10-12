"""Load the breakroom tool's unittest modules into the belt test run."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BREAKROOM_TESTS = ROOT / 'tools' / 'breakroom' / 'tests'


def load_tests(loader, standard_tests, pattern):
    path = str(BREAKROOM_TESTS)
    if path not in sys.path:
        sys.path.insert(0, path)
    import test_breakroom  # noqa: WPS433 — path import for fork pickling in test_breakroom
    import test_scoring  # noqa: WPS433

    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(test_breakroom))
    suite.addTests(loader.loadTestsFromModule(test_scoring))
    return suite
