"""Sync an adopted app's managed tool belt files from a tool belt checkout."""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import ADOPTION_MARKER, BELT_REPO, validate_adoption

MARKER = 'managed by Ian-tool-belt'
MARKER_LINES = 10
MANAGED = ['AGENTS.md', '.cursor/rules/tool-belt.mdc',
           '.github/workflows/belt.yml', '.github/workflows/belt-sync.yml']
TEMPLATES = Path('templates/app-adoption')


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


def plan(belt_dir, app_dir, allow_workflow_files):
    """Return the sync plan without writing anything."""
    belt_dir, app_dir = Path(belt_dir), Path(app_dir)
    current = validate_adoption(app_dir)['beltVersion']
    latest = json.loads((belt_dir / 'belt.json').read_text())['version']
    result = {'current': current, 'latest': latest,
              'behind': is_behind(current, latest), 'files': []}
    if not result['behind']:
        return result
    for relative in MANAGED:
        source = (belt_dir / TEMPLATES / relative).read_text()
        target = app_dir / relative
        if not target.exists():
            status = 'added'
        elif not has_marker(target.read_text()):
            status = 'skipped: marker removed, owned by this repo'
        elif target.read_text() == source:
            status = 'unchanged'
        else:
            status = 'updated'
        if status in ('added', 'updated') and is_workflow(relative) and not allow_workflow_files:
            status = 'skipped: workflow files need a token with Workflows write permission'
        result['files'].append((relative, status))
    result['files'].append((ADOPTION_MARKER, f'version {current} -> {latest}'))
    return result


def apply(belt_dir, app_dir, result):
    """Write planned changes and return the paths that changed."""
    belt_dir, app_dir = Path(belt_dir), Path(app_dir)
    changed = []
    for relative, status in result['files']:
        if status in ('added', 'updated'):
            target = app_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(belt_dir / TEMPLATES / relative, target)
            changed.append(relative)
    if result['behind']:
        marker = {'belt': BELT_REPO, 'beltVersion': result['latest']}
        (app_dir / ADOPTION_MARKER).write_text(json.dumps(marker, indent=2) + '\n')
        changed.append(ADOPTION_MARKER)
    return changed


def pr_body(result, allow_workflow_files):
    latest = result['latest']
    repo = f'https://github.com/{BELT_REPO}'
    lines = [f"Syncs the managed tool belt files from v{result['current']} to v{latest}.", '',
             '| File | Change |', '| --- | --- |']
    lines += [f'| `{path}` | {status} |' for path, status in result['files']]
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
    parser.add_argument('--belt', required=True, help='Tool belt checkout')
    parser.add_argument('--app', default='.', help='Adopted app repository')
    parser.add_argument('--body', required=True, help='Where to write the PR body')
    parser.add_argument('--allow-workflow-files', action='store_true')
    args = parser.parse_args(argv)
    result = plan(args.belt, args.app, args.allow_workflow_files)
    changed = apply(args.belt, args.app, result)
    if changed:
        Path(args.body).write_text(pr_body(result, args.allow_workflow_files))
    outputs = {'changed': str(bool(changed)).lower(), 'version': result['latest'],
               'paths': '\n'.join(changed)}
    if os.environ.get('GITHUB_OUTPUT'):
        write_outputs(os.environ['GITHUB_OUTPUT'], outputs)
    print(f"App v{result['current']}, belt v{result['latest']}: "
          + (f"synced {', '.join(changed)}" if changed else 'up to date'))
    return outputs


if __name__ == '__main__':
    main()
