"""Load html-edit tool tests into the belt unittest run."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / 'tools/html-edit/tests'


def load_tests(loader, standard_tests, pattern):
    path = str(TESTS)
    if path not in sys.path:
        sys.path.insert(0, path)
    import test_html_edit  # noqa: WPS433

    return loader.loadTestsFromModule(test_html_edit)
