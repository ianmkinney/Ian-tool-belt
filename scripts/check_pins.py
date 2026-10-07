"""Check pinned npm/PyPI packages for newer stable releases; optionally bump the pins."""
import argparse
import json
import re
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen
from beltfile import load, save_validated, set_package_version

REGISTRIES = {
    'npm': ('https://registry.npmjs.org/{name}/latest', lambda body: body['version']),
    'pypi': ('https://pypi.org/pypi/{name}/json', lambda body: body['info']['version']),
}
STABLE = r'(\d+)\.(\d+)\.(\d+)'


def fetch_latest(kind, name, timeout=15):
    template, pick = REGISTRIES[kind]
    request = Request(template.format(name=quote(name, safe='@/')), headers={'Accept': 'application/json'})
    with urlopen(request, timeout=timeout) as response:
        return pick(json.load(response))


def is_newer(latest, pinned):
    """Only stable X.Y.Z releases count; pre-releases and odd formats are never auto-bumped."""
    new, old = re.fullmatch(STABLE, latest), re.fullmatch(STABLE, pinned)
    return bool(new) and (not old or tuple(map(int, new.groups())) > tuple(map(int, old.groups())))


def check(belt, lookup=fetch_latest, apply=False):
    results = []
    for package in belt.get('packages', []):
        if package['kind'] not in REGISTRIES:
            continue
        entry = {'id': package['id'], 'kind': package['kind'], 'name': package['name'],
                 'pinned': package['version']}
        try:
            entry['latest'] = lookup(package['kind'], package['name'])
        except Exception as error:
            entry.update(status='lookup-failed', detail=str(error))
        else:
            if not is_newer(entry['latest'], package['version']):
                entry['status'] = 'current'
            elif apply:
                set_package_version(belt, package['id'], entry['latest'])
                entry['status'] = 'bumped'
            else:
                entry['status'] = 'newer-available'
        results.append(entry)
    return results


def main(argv=None, lookup=fetch_latest):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('--apply', action='store_true', help='rewrite belt.json with newer pins')
    parser.add_argument('--report', help='also write the JSON report to this path')
    args = parser.parse_args(argv)
    belt = load(args.manifest)
    results = check(belt, lookup, args.apply)
    if any(r['status'] == 'bumped' for r in results):
        try:
            save_validated(args.manifest, belt)
        except (OSError, ValueError, TypeError, KeyError) as error:
            print(f'Bump rejected by validation: {error}', file=sys.stderr)
            return 1
    report = json.dumps(results, indent=2) + '\n'
    if args.report:
        with open(args.report, 'w') as handle:
            handle.write(report)
    print(report, end='')
    for failed in (r for r in results if r['status'] == 'lookup-failed'):
        print(f"Could not check {failed['name']}: {failed['detail']}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
