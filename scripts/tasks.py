"""Run one allowlisted belt task and save its log and outputs under --out.

Used by the "Run belt task" workflow; only the names in TASKS can run. Each task is a
fixed argument list run without a shell, so inputs cannot add commands.
"""
import argparse
import subprocess
import sys
from pathlib import Path
from validate import ADAPTERS, validate

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def export_steps(targets, out, preset):
    extra = ['--preset', preset] if preset else []
    return [[PY, 'scripts/export.py', 'belt.json', '--target', t, '--out', str(out / 'exports' / t), *extra]
            for t in targets]


TASKS = {
    'validate': (lambda out, preset: [[PY, 'scripts/validate.py', 'belt.json'],
                                      [PY, 'scripts/validate.py', 'examples/personal/belt.json']],
                 'Validate the belt and example manifests'),
    'unit-tests': (lambda out, preset: [[PY, '-m', 'unittest', 'discover', '-s', 'tests', '-v']],
                   'Run the unit test suite'),
    'check-styling': (lambda out, preset: [[PY, 'scripts/build_tokens.py', '--check']],
                      'Confirm styling/tokens.css matches tokens.json'),
    'check-pins': (lambda out, preset: [[PY, 'scripts/check_pins.py', 'belt.json',
                                         '--report', str(out / 'pins.json')]],
                   'Report newer releases for pinned packages (no changes)'),
    'export-all': (lambda out, preset: export_steps(validate(ROOT / 'belt.json')['adapters'], out, preset),
                   'Export every declared client target'),
}
for _target in ADAPTERS:
    TASKS[f'export-{_target}'] = ((lambda t: lambda out, preset: export_steps([t], out, preset))(_target),
                                  f'Export the {_target} target')


def run(task, out, preset=None):
    if task not in TASKS:
        raise ValueError(f'Unknown task {task!r}; allowed: {", ".join(sorted(TASKS))}')
    if preset and not preset.replace('-', '').isalnum():
        raise ValueError('Invalid preset name')
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    status = 0
    with open(out / f'{task}.log', 'w') as log:
        for argv in TASKS[task][0](out, preset):
            log.write('$ ' + ' '.join(argv[1:] if argv[0] == PY else argv) + '\n')
            log.flush()
            status = subprocess.run(argv, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
            log.write(f'[exit {status}]\n')
            if status:
                break
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list', help='show allowlisted tasks')
    runner = sub.add_parser('run', help='run one task')
    runner.add_argument('task')
    runner.add_argument('--out', required=True, help='directory for the log and outputs')
    runner.add_argument('--preset', help='local model preset for export tasks')
    args = parser.parse_args(argv)
    if args.command == 'list':
        for name, (_, description) in sorted(TASKS.items()):
            print(f'{name:22} {description}')
        return 0
    try:
        status = run(args.task, args.out, args.preset)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    print((Path(args.out) / f'{args.task}.log').read_text(), end='')
    return status


if __name__ == '__main__':
    sys.exit(main())
