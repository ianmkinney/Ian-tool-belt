#!/usr/bin/env python3
"""One command entry point for Ian's tool belt.

  python3 belt.py use              write the belt into this project
  python3 belt.py doctor           validate, env vars, optional local AI
  python3 belt.py list             everything in the belt, with descriptions
  python3 belt.py add skill|package ...
  python3 belt.py set PATH VALUE
  python3 belt.py run TASK
  python3 belt.py index [--check]
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))

import belt_index  # noqa: E402
import belt_set  # noqa: E402
import check_pins  # noqa: E402
import export  # noqa: E402
import local_ai_check  # noqa: E402
import new  # noqa: E402
import tasks  # noqa: E402
from validate import ADAPTERS, validate  # noqa: E402

OPTIONAL_SECRETS = {'LOCAL_AI_API_KEY'}
CLIENT_MARKERS = {
    'cursor': ['.cursor/mcp.json', '.cursor'],
    'opencode': ['opencode.json'],
    'claude-code': ['.mcp.json'],
    'vscode': ['.vscode/mcp.json'],
}


def default_belt():
    return ROOT / 'belt.json'


def detect_target(app, explicit=None):
    if explicit:
        if explicit not in ADAPTERS:
            raise ValueError(f'Unknown target {explicit!r}; choose {", ".join(ADAPTERS)}')
        return explicit
    found = []
    for name, markers in CLIENT_MARKERS.items():
        if any((app / marker).exists() for marker in markers):
            found.append(name)
    if len(found) == 1:
        return found[0]
    if len(found) > 1:
        raise ValueError(f'Multiple clients found ({", ".join(found)}); pass a target')
    return 'cursor'


def copy_export(source, destination, force=False):
    """Copy an export tree into a project. Never deletes. Skips existing files unless force."""
    written, skipped, unchanged = [], [], []
    for path in sorted(source.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        target = destination / relative
        if target.exists():
            if target.is_file() and target.read_bytes() == path.read_bytes():
                unchanged.append(str(relative))
                continue
            if not force:
                skipped.append(str(relative))
                continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        written.append(str(relative))
    return {'written': written, 'skipped': skipped, 'unchanged': unchanged}


def use_belt(manifest, app, target=None, out=None, force=False, include_personal=False, preset=None):
    app = Path(app).resolve()
    target = detect_target(app, target)
    if out is not None:
        report = export.export_belt(manifest, target, Path(out), preset, include_personal)
        return {'target': target, 'out': str(Path(out).resolve()), 'copy': None, 'export': report}
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / 'export'
        report = export.export_belt(manifest, target, staging, preset, include_personal)
        copy = copy_export(staging, app, force=force)
    return {'target': target, 'out': str(app), 'copy': copy, 'export': report}


def doctor_belt(manifest, environ, offline=False, timeout=5):
    belt = validate(manifest)
    result = {'belt': f"{belt['name']}@{belt['version']}", 'valid': True, 'env': [],
              'localAi': None, 'pins': None}
    for name in belt['secretRefs']:
        present = bool(environ.get(name))
        result['env'].append({'name': name, 'set': present,
                              'optional': name in OPTIONAL_SECRETS})
    if not offline:
        try:
            settings = local_ai_check.resolve(belt, None, environ)
            check, code = local_ai_check.check(settings, chat=False, timeout=timeout)
            check['exit'] = code
            result['localAi'] = check
        except (OSError, ValueError, TypeError, KeyError) as error:
            result['localAi'] = {'error': str(error), 'exit': local_ai_check.BAD_CONFIG}
        try:
            result['pins'] = check_pins.check(belt)
        except (OSError, ValueError, TypeError, KeyError) as error:
            result['pins'] = [{'status': 'lookup-failed', 'error': str(error)}]
    playwright = shutil.which('node')
    result['node'] = {'present': bool(playwright),
                      'note': 'Node.js is required to run the playwright MCP server.'}
    return result


def doctor_ok(result, strict=False):
    if not result['valid']:
        return False
    if not strict:
        return True
    if any(not item['set'] and not item['optional'] for item in result['env']):
        return False
    local = result.get('localAi') or {}
    if local.get('exit', 0) not in (0, None):
        return False
    return True


def print_doctor(result):
    print(f"Valid belt: {result['belt']}")
    for item in result['env']:
        state = 'set' if item['set'] else ('unset (optional)' if item['optional'] else 'missing')
        print(f"  env {item['name']}: {state}")
    node = result['node']
    print(f"  node: {'found' if node['present'] else 'not found'} ({node['note']})")
    if result['localAi'] is None:
        print('  local AI: skipped (--offline)')
    elif result['localAi'].get('reachable'):
        models = ', '.join(result['localAi'].get('models') or []) or 'none listed'
        print(f"  local AI: reachable at {result['localAi']['baseUrl']} ({models})")
    else:
        print(f"  local AI: {result['localAi'].get('error', 'not reachable')}")
    if result['pins'] is None:
        print('  pins: skipped (--offline)')
    else:
        newer = [p for p in result['pins'] if p.get('status') == 'newer-available']
        failed = [p for p in result['pins'] if p.get('status') == 'lookup-failed']
        if failed:
            print(f"  pins: {len(failed)} lookup(s) failed")
        elif newer:
            print('  pins: newer ' + ', '.join(f"{p['id']} {p.get('latest', '')}" for p in newer))
        else:
            print('  pins: up to date (or no registry lookup needed)')


def print_list(index):
    print(f"{index['name']}@{index['version']}: {index['description']}")
    print('\nCommands')
    for item in index['commands']:
        print(f"  {item['run']}\n    {item['description']}")
    for title, key in [('Servers', 'servers'), ('Skills', 'skills'), ('Rules', 'rules'),
                       ('Packages', 'packages'), ('Adapters', 'adapters')]:
        print(f'\n{title}')
        for item in index[key]:
            print(f"  {item['id']}\n    {item['description']}")
    personal = index['personalServers']
    print(f"\nPersonal servers: {personal['count']} (details omitted unless --include-personal)")
    print('\nNot exported as connections')
    for item in index['skipped']:
        print(f"  {item['id']}\n    {item['reason']}")


def cmd_use(args):
    try:
        result = use_belt(args.belt, args.app, args.target, args.out, args.force,
                          args.include_personal, args.preset)
    except (OSError, ValueError, TypeError) as error:
        print(f'Use failed: {error}', file=sys.stderr)
        return 1
    copy = result['copy']
    print(f"Target: {result['target']}")
    print(f"Wrote to: {result['out']}")
    if copy:
        for label in ('written', 'unchanged', 'skipped'):
            if copy[label]:
                print(f"{label}: {', '.join(copy[label])}")
        if copy['skipped']:
            print('Existing files were left alone. Re-run with --force to overwrite.', file=sys.stderr)
            return 1
    else:
        print(json.dumps(result['export'], indent=2))
    return 0


def cmd_doctor(args):
    try:
        result = doctor_belt(args.belt, os.environ, args.offline, args.timeout)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'Invalid belt: {error}', file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_doctor(result)
    return 0 if doctor_ok(result, args.strict) else 1


def cmd_list(args):
    try:
        index = belt_index.build(args.belt, include_personal=args.include_personal)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'List failed: {error}', file=sys.stderr)
        return 1
    if args.json:
        print(belt_index.dump(index), end='')
    else:
        print_list(index)
    return 0


def cmd_add(args):
    argv = ['--belt', str(args.belt), args.kind, args.name, '--description', args.description]
    if args.pkg_kind:
        argv.extend(['--kind', args.pkg_kind])
    if args.pkg_name:
        argv.extend(['--name', args.pkg_name])
    if args.version:
        argv.extend(['--version', args.version])
    return new.main(argv)


def cmd_set(args):
    return belt_set.main([str(args.belt), args.path, args.value])


def cmd_run(args):
    argv = ['run', args.task, '--out', args.out]
    if args.preset:
        argv.extend(['--preset', args.preset])
    return tasks.main(argv)


def cmd_index(args):
    try:
        index = belt_index.build(args.belt)
        if args.check:
            stale = belt_index.check(index)
            if stale:
                print('Generated files are stale: ' + ', '.join(stale), file=sys.stderr)
                print('Run `python3 belt.py index` and commit the result.', file=sys.stderr)
                return 1
            print('Index is current.')
            return 0
        paths = belt_index.write(index)
        print('Wrote ' + ' and '.join(p.name for p in paths))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'Index failed: {error}', file=sys.stderr)
        return 1


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--belt', default=str(default_belt()), help='belt.json path (default: this repo)')
    sub = parser.add_subparsers(dest='command', required=True)

    use = sub.add_parser('use', aliases=['install'],
                         help='write the belt into a project (auto-detects the client when possible)')
    use.add_argument('target', nargs='?', choices=ADAPTERS, help='client; omitted = auto-detect or cursor')
    use.add_argument('--app', default='.', help='project directory (default: current directory)')
    use.add_argument('--out', help='write a fresh export directory instead of copying into --app')
    use.add_argument('--force', action='store_true', help='overwrite existing files in --app')
    use.add_argument('--include-personal', action='store_true')
    use.add_argument('--preset', help='local model preset')
    use.set_defaults(func=cmd_use)

    doctor = sub.add_parser('doctor', help='validate the belt and report local setup')
    doctor.add_argument('--offline', action='store_true',
                        help='skip pin lookup and local AI (CI and air-gapped use)')
    doctor.add_argument('--strict', action='store_true',
                        help='exit 1 when required env vars are missing or local AI is down')
    doctor.add_argument('--json', action='store_true')
    doctor.add_argument('--timeout', type=float, default=5)
    doctor.set_defaults(func=cmd_doctor)

    listing = sub.add_parser('list', help='describe everything in the belt')
    listing.add_argument('--json', action='store_true')
    listing.add_argument('--include-personal', action='store_true')
    listing.set_defaults(func=cmd_list)

    add = sub.add_parser('add', help='scaffold a skill or package')
    add.add_argument('kind', choices=['skill', 'package'])
    add.add_argument('name')
    add.add_argument('--description', required=True)
    add.add_argument('--kind', dest='pkg_kind', choices=['files', 'npm', 'pypi'])
    add.add_argument('--name', dest='pkg_name')
    add.add_argument('--version')
    add.set_defaults(func=cmd_add)

    setter = sub.add_parser('set', help='change one allowlisted belt.json value')
    setter.add_argument('path')
    setter.add_argument('value')
    setter.set_defaults(func=cmd_set)

    runner = sub.add_parser('run', help='run one allowlisted task')
    runner.add_argument('task')
    runner.add_argument('--out', default=str(ROOT / 'task-output'))
    runner.add_argument('--preset')
    runner.set_defaults(func=cmd_run)

    index = sub.add_parser('index', help='regenerate or check belt.index.json and AGENTS.md')
    index.add_argument('--check', action='store_true', help='fail if generated files are stale')
    index.set_defaults(func=cmd_index)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.belt = Path(args.belt)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
