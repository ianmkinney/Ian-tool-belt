"""Validate the minimal 0.1-draft manifest; does not execute belt contents."""
import json
import re
import sys
from pathlib import Path


def validate(path):
    path = Path(path).resolve()
    data = json.loads(path.read_text())
    fields = {'formatVersion', 'name', 'version', 'description', 'rules',
              'skills', 'servers', 'adapters', 'secretRefs'}
    if not isinstance(data, dict) or set(data) != fields:
        raise ValueError('Manifest must contain exactly the documented draft fields')
    if data['formatVersion'] != '0.1-draft':
        raise ValueError('Unsupported formatVersion')
    for field, pattern in [('name', r'[a-z][a-z0-9-]*'),
                           ('version', r'[0-9]+\.[0-9]+\.[0-9]+')]:
        if not isinstance(data[field], str) or not re.fullmatch(pattern, data[field]):
            raise ValueError(f'Invalid {field}')
    if not isinstance(data['description'], str):
        raise ValueError('description must be a string')
    for field in ['rules', 'skills', 'servers', 'adapters', 'secretRefs']:
        if not isinstance(data[field], list):
            raise ValueError(f'{field} must be an array')
    for field in ['skills', 'servers', 'adapters', 'secretRefs']:
        if data[field]:
            raise ValueError(f'{field} entries are not supported by this draft validator')
    for entry in data['rules']:
        if not isinstance(entry, str) or not entry or Path(entry).is_absolute():
            raise ValueError('Rule paths must be nonempty relative strings')
        target = (path.parent / entry).resolve()
        if not target.is_relative_to(path.parent) or not target.is_file():
            raise ValueError('Rule must resolve to a file inside the belt directory')
    return data


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 scripts/validate.py PATH_TO_BELT_JSON')
    try:
        belt = validate(sys.argv[1])
    except (OSError, ValueError) as error:
        sys.exit(f'Invalid belt: {error}')
    print(f"Valid minimal draft belt: {belt['name']}@{belt['version']}")
