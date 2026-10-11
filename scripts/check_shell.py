"""Run shellcheck on tracked shell scripts in the belt repository."""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHEBANG = re.compile(rb'^#!.*\b(?:bash|sh|dash|zsh|ksh)\b')
SUFFIXES = {'.sh', '.bash'}


def tracked_files(root):
    try:
        out = subprocess.run(['git', 'ls-files', '-z'], cwd=root, capture_output=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return sorted(p for p in root.rglob('*') if p.is_file())
    return [root / part.decode() for part in out.split(b'\0') if part]


def is_shell_script(path):
    if path.suffix.lower() in SUFFIXES:
        return True
    try:
        with path.open('rb') as handle:
            return bool(SHEBANG.match(handle.readline()))
    except OSError:
        return False


def discover(root):
    return sorted(path for path in tracked_files(root) if path.is_file() and is_shell_script(path))


def run(shellcheck, paths, root):
    if not paths:
        return 0
    argv = [shellcheck, '--external-sources', '--severity=warning', *paths]
    return subprocess.run(argv, cwd=root).returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='repository root (default: belt root)')
    parser.add_argument('--shellcheck', default='shellcheck', help='shellcheck command or path')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    shellcheck = shutil.which(args.shellcheck) or args.shellcheck
    paths = [str(p.relative_to(root)) for p in discover(root)]
    return run(shellcheck, paths, root)


if __name__ == '__main__':
    sys.exit(main())
