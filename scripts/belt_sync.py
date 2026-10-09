"""Sync an adopted app's managed tool belt files from a tool belt checkout."""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export import cursor_rule
from validate import ADOPTION_MARKER, BELT_REPO, validate_adoption

MARKER = 'managed by Ian-tool-belt'
MARKER_LINES = 10
MARKER_COMMENT = f'<!-- {MARKER}: belt-sync updates this file. Delete this line to own it. -->\n'
TEMPLATES = Path('templates/app-adoption')
TEMPLATE_FILES = ['AGENTS.md', '.github/workflows/belt.yml', '.github/workflows/belt-sync.yml']
BELT_SHA_PLACEHOLDER = '__BELT_SHA__'
BELT_VERSION_PLACEHOLDER = '__BELT_VERSION__'
BELT_USES_AT = re.compile(
    r'(ianmkinney/Ian-tool-belt/\.github/workflows/[^\s@]+@)([0-9a-f]{40}|\w+)\s*(#\s*v[\d.]+)?',
    re.IGNORECASE,
)


def parse_version(text):
    parts = text.split('.')
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f'Invalid version: {text}')
    return tuple(int(p) for p in parts)


def is_behind(app_version, belt_version):
    return parse_version(app_version) < parse_version(belt_version)


def has_marker(text):
    return any(MARKER in line for line in text.splitlines()[:MARKER_LINES])


def is_workflow(relative):
    return relative.startswith('.github/workflows/')


def workflow_pins_differ(app_dir, pin_sha):
    """True when managed workflow files exist but do not pin the given belt SHA."""
    app_dir = Path(app_dir)
    for relative in ('.github/workflows/belt.yml', '.github/workflows/belt-sync.yml'):
        path = app_dir / relative
        if not path.exists():
            continue
        if not has_marker(path.read_text()):
            continue
        if f'@{pin_sha}' not in path.read_text():
            return True
    return False


def belt_commit_sha(belt_dir):
    return subprocess.check_output(
        ['git', '-C', str(belt_dir), 'rev-parse', 'HEAD'], text=True,
    ).strip()


def fetch_belt_source(belt_dir, ref):
    """Update belt_dir to origin/<ref> so sync reads the latest belt on that branch."""
    ref = ref.removeprefix('origin/')
    subprocess.check_call(['git', '-C', str(belt_dir), 'fetch', 'origin', ref, '--depth', '1'])
    subprocess.check_call(['git', '-C', str(belt_dir), 'checkout', f'origin/{ref}'])


def substitute_belt_pins(text, sha, version):
    """Replace template placeholders and normalize any existing belt workflow pins."""
    version = version.removeprefix('v')
    out = text.replace(f'@{BELT_SHA_PLACEHOLDER}', f'@{sha}')
    out = out.replace(f'v{BELT_VERSION_PLACEHOLDER}', f'v{version}')
    out = out.replace(BELT_SHA_PLACEHOLDER, sha)

    def repl(match):
        suffix = f' # v{version}' if match.group(3) else f' # v{version}'
        return f'{match.group(1)}{sha}{suffix}'

    return BELT_USES_AT.sub(repl, out)


def managed_cursor_rule(text):
    """Render a belt rule exactly as `export.py --target cursor` does, plus the marker."""
    rendered = cursor_rule(text)
    end = rendered.index('\n---\n', 3) + len('\n---\n')
    return rendered[:end] + MARKER_COMMENT + rendered[end:]


def managed_files(belt_dir, pin_sha, version):
    """Return {app-relative path: content} for every file the belt manages."""
    belt_dir = Path(belt_dir)
    files = {}
    for relative in TEMPLATE_FILES:
        raw = (belt_dir / TEMPLATES / relative).read_text()
        files[relative] = substitute_belt_pins(raw, pin_sha, version) if is_workflow(relative) else raw
    for entry in json.loads((belt_dir / 'belt.json').read_text())['rules']:
        files[f'.cursor/rules/{Path(entry).stem}.mdc'] = managed_cursor_rule((belt_dir / entry).read_text())
    return files


def plan(belt_dir, app_dir, pin_sha, version, allow_workflow_files, adopt=False):
    """Return the sync plan without writing anything."""
    belt_dir, app_dir = Path(belt_dir), Path(app_dir)
    latest = version
    if adopt and not (app_dir / ADOPTION_MARKER).exists():
        current = None
    else:
        current = validate_adoption(app_dir)['beltVersion']
    pin_stale = workflow_pins_differ(app_dir, pin_sha)
    behind = current is None or is_behind(current, latest) or pin_stale
    result = {'current': current, 'latest': latest, 'sync': behind or adopt, 'files': []}
    if not result['sync']:
        return result
    for relative, content in managed_files(belt_dir, pin_sha, version).items():
        target = app_dir / relative
        if not target.exists():
            status = 'added'
        elif not has_marker(target.read_text()):
            status = 'skipped: marker removed, owned by this repo'
        elif target.read_text() == content:
            status = 'unchanged'
        else:
            status = 'updated'
        if status in ('added', 'updated') and is_workflow(relative) and not allow_workflow_files:
            status = 'skipped: workflow files need a token with Workflows write permission'
        result['files'].append((relative, status, content))
    if current != latest:
        result['files'].append((ADOPTION_MARKER, f'version {current or "none"} -> {latest}', None))
    return result


def apply(app_dir, result):
    """Write planned changes and return the paths that changed."""
    app_dir = Path(app_dir)
    changed = []
    for relative, status, content in result['files']:
        if status in ('added', 'updated'):
            target = app_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            changed.append(relative)
    if result['sync'] and result['current'] != result['latest']:
        marker = {'belt': BELT_REPO, 'beltVersion': result['latest']}
        (app_dir / ADOPTION_MARKER).write_text(json.dumps(marker, indent=2) + '\n')
        changed.append(ADOPTION_MARKER)
    return changed


def pr_body(result, allow_workflow_files):
    latest = result['latest']
    repo = f'https://github.com/{BELT_REPO}'
    pin = result.get('pin_sha', '')
    lines = [f"Syncs the managed tool belt files from v{result['current']} to v{latest}.", '']
    if pin:
        lines.append(f'Workflow pins updated to belt commit `{pin}` (v{latest}).')
    lines += ['', '| File | Change |', '| --- | --- |']
    lines += [f'| `{path}` | {status} |' for path, status, _ in result['files']]
    lines += ['', f'- Release: {repo}/releases/tag/v{latest}',
              f'- Changelog: {repo}/blob/main/CHANGELOG.md', '',
              f'Files whose `{MARKER}` header was removed belong to this repo and are never '
              'overwritten. Review before merging.']
    if not allow_workflow_files:
        lines += ['', 'Opened with the default `GITHUB_TOKEN`, so CI does not run on this PR '
                  'by itself. Close and reopen it to trigger CI, or add a `BELT_SYNC_TOKEN` '
                  'fine-grained PAT.']
    return '\n'.join(lines) + '\n'


def write_outputs(path, outputs):
    with open(path, 'a') as handle:
        for key, value in outputs.items():
            handle.write(f'{key}<<BELT_SYNC_EOF\n{value}\nBELT_SYNC_EOF\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--belt', default=str(Path(__file__).resolve().parents[1]),
                        help='Tool belt checkout (default: this checkout)')
    parser.add_argument('--app', default='.', help='Adopted app repository')
    parser.add_argument('--body', help='Where to write the PR body')
    parser.add_argument('--allow-workflow-files', action='store_true')
    parser.add_argument('--adopt', action='store_true',
                        help='First-time setup: write every managed file and the marker, at any version')
    parser.add_argument('--pin-sha', help='40-char SHA to pin in workflow uses lines (default: belt HEAD)')
    parser.add_argument('--fetch-ref', help='Fetch origin/<ref> into --belt before syncing (e.g. main)')
    args = parser.parse_args(argv)
    belt_dir = Path(args.belt)
    if args.fetch_ref:
        fetch_belt_source(belt_dir, args.fetch_ref)
    version = json.loads((belt_dir / 'belt.json').read_text())['version']
    pin_sha = args.pin_sha or belt_commit_sha(belt_dir)
    if len(pin_sha) != 40 or not all(c in '0123456789abcdef' for c in pin_sha.lower()):
        raise ValueError(f'pin-sha must be a 40-character commit SHA, got: {pin_sha!r}')
    allow_workflow_files = args.allow_workflow_files or args.adopt
    result = plan(belt_dir, args.app, pin_sha, version, allow_workflow_files, args.adopt)
    result['pin_sha'] = pin_sha
    changed = apply(args.app, result)
    if changed and args.body:
        Path(args.body).write_text(pr_body(result, allow_workflow_files))
    outputs = {'changed': str(bool(changed)).lower(), 'version': result['latest'],
               'paths': '\n'.join(changed)}
    if os.environ.get('GITHUB_OUTPUT'):
        write_outputs(os.environ['GITHUB_OUTPUT'], outputs)
    print(f"App v{result['current']}, belt v{result['latest']}: "
          + (f"synced {', '.join(changed)}" if changed else 'up to date'))
    return outputs


if __name__ == '__main__':
    main()
