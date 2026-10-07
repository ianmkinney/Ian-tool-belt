"""Shared helpers for editing belt.json: stable formatting and validate-or-rollback writes."""
import json
from pathlib import Path
from validate import validate


def load(path):
    return json.loads(Path(path).read_text())


def dump(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + '\n'


def save_validated(path, data):
    """Write data, validate the result, and restore the previous file if it is invalid."""
    path = Path(path)
    original = path.read_text()
    path.write_text(dump(data))
    try:
        return validate(path)
    except Exception:
        path.write_text(original)
        raise


def find(items, identifier, kind):
    for item in items:
        if item.get('id') == identifier:
            return item
    raise ValueError(f'Unknown {kind}: {identifier}')


def set_package_version(belt, package_id, version):
    """Pin a package and every stdio server argument that installs it."""
    package = find(belt.get('packages', []), package_id, 'package')
    old = package['version']
    package['version'] = version
    if package['kind'] == 'npm':
        for server in belt['servers'] + belt.get('personalServers', []):
            if server['transport'] == 'stdio':
                server['args'] = [f"{package['name']}@{version}" if a == f"{package['name']}@{old}" else a
                                  for a in server['args']]
    return old
