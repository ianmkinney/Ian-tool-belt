"""Update one allowlisted belt.json variable, then validate (or roll back)."""
import argparse
import re
import sys
from beltfile import find, load, save_validated, set_package_version

ID = r'([a-z][a-z0-9-]*)'
SETTABLE = [
    (r'version|description', 'top-level field'),
    (rf'(servers|personalServers)\.{ID}\.(url|status)', 'server field'),
    (rf'packages\.{ID}\.version', 'package pin'),
    (rf'models\.{ID}\.(status|defaultPreset)', 'model field'),
    (rf'models\.{ID}\.presets\.{ID}\.(baseUrl|model)', 'model preset field'),
]


def set_value(belt, path, value):
    """Apply one change in memory and return the previous value."""
    if not any(re.fullmatch(pattern, path) for pattern, _ in SETTABLE):
        raise ValueError(f'Not a settable variable: {path}')
    parts = path.split('.')
    if len(parts) == 1:
        old, belt[path] = belt[path], value
        return old
    if parts[0] == 'packages':
        return set_package_version(belt, parts[1], value)
    item = find(belt[parts[0]], parts[1], parts[0].rstrip('s'))
    if parts[0] == 'models' and parts[2] == 'presets':
        if parts[3] not in item['presets']:
            raise ValueError(f'Unknown preset: {parts[3]}')
        item = item['presets'][parts[3]]
    old, item[parts[-1]] = item[parts[-1]], value
    return old


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, epilog='Settable: ' + ', '.join(
        f'{p} ({d})' for p, d in SETTABLE))
    parser.add_argument('manifest')
    parser.add_argument('path', help='for example servers.playwright.status or packages.playwright-mcp.version')
    parser.add_argument('value')
    args = parser.parse_args(argv)
    try:
        belt = load(args.manifest)
        old = set_value(belt, args.path, args.value)
        if old == args.value:
            print(f'{args.path} already {args.value!r}; nothing changed')
            return 0
        save_validated(args.manifest, belt)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'Update failed: {error}', file=sys.stderr)
        return 1
    print(f'{args.path}: {old!r} -> {args.value!r}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
