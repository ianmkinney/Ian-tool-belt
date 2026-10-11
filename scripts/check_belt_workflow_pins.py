"""Fail if any workflow still calls Ian-tool-belt reusable workflows at @main."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BELT_USES = re.compile(
    r'ianmkinney/Ian-tool-belt/\.github/workflows/[^\s@]+@main\b',
    re.IGNORECASE,
)
SCAN = [ROOT / '.github/workflows', ROOT / 'templates']


def find_main_pins(paths):
    hits = []
    for base in paths:
        if not base.exists():
            continue
        for path in sorted(base.rglob('*.yml')):
            for line_no, line in enumerate(path.read_text().splitlines(), 1):
                if BELT_USES.search(line):
                    try:
                        display = path.relative_to(ROOT)
                    except ValueError:
                        display = path
                    hits.append((display, line_no, line.strip()))
    return hits


def main(argv=None):
    hits = find_main_pins(SCAN)
    if hits:
        for path, line_no, line in hits:
            print(f'{path}:{line_no}: {line}', file=sys.stderr)
        sys.exit(f'Found {len(hits)} Ian-tool-belt workflow reference(s) at @main; pin to a commit SHA.')
    print('No Ian-tool-belt @main workflow references.')


if __name__ == '__main__':
    main()
