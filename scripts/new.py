"""Scaffold a new skill or package and register it in belt.json.

  python3 scripts/new.py skill review-sql --description "Review SQL changes. Use when ..."
  python3 scripts/new.py package api-client --kind files --description "Shared HTTP client"
  python3 scripts/new.py package zod --kind npm --name zod --version 3.23.8 --description "Schema pin"
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from beltfile import load, save_validated

ID = r'[a-z][a-z0-9-]*'

SKILL_TEMPLATE = """---
name: {name}
description: {description}
---

# {title}

1. State the outcome this skill produces and the evidence that proves it.
2. List the steps in order. Prefer the project's existing tools and conventions.
3. Say what must never happen (secrets in Git, unreviewed writes, unverified claims).
4. Describe how to verify the result and what to report back.

Example request: <a synthetic request that should trigger this skill>
"""

PACKAGE_TEMPLATE = """# {title}

{description}

## Contents

Describe each file and how a project imports or copies it.

## Use in a project

Copy this folder or reference it from the belt checkout. Pin the belt version you copied from.

## Change it

Update the files, bump this package's `version` in belt.json, and add or update tests for any behavior.
"""


def title(identifier):
    return identifier.replace('-', ' ').capitalize()


def one_line(text, label):
    if not text or not text.strip() or '\n' in text:
        raise ValueError(f'{label} must be one non-empty line')
    return text.strip()


def add_skill(manifest, name, description):
    manifest = Path(manifest)
    if not re.fullmatch(ID, name):
        raise ValueError('Skill name must be lowercase letters, digits and hyphens')
    description = one_line(description, 'Description')
    folder = manifest.parent / 'skills' / name
    entry = f'skills/{name}/SKILL.md'
    belt = load(manifest)
    if folder.exists() or entry in belt['skills']:
        raise ValueError(f'Skill already exists: {name}')
    folder.mkdir(parents=True)
    # A JSON string is valid YAML, so descriptions containing ": " still parse in clients.
    (folder / 'SKILL.md').write_text(SKILL_TEMPLATE.format(
        name=name, description=json.dumps(description), title=title(name)))
    belt['skills'].append(entry)
    try:
        save_validated(manifest, belt)
    except Exception:
        shutil.rmtree(folder)
        raise
    return entry


def add_package(manifest, identifier, kind, description, name=None, version=None):
    manifest = Path(manifest)
    if not re.fullmatch(ID, identifier):
        raise ValueError('Package id must be lowercase letters, digits and hyphens')
    description = one_line(description, 'Description')
    belt = load(manifest)
    if 'packages' not in belt:
        raise ValueError('Packages require formatVersion 0.3-draft')
    if any(p['id'] == identifier for p in belt['packages']):
        raise ValueError(f'Package already exists: {identifier}')
    folder = None
    if kind == 'files':
        if name:
            raise ValueError('--name applies only to npm or pypi packages')
        folder = manifest.parent / 'packages' / identifier
        if folder.exists():
            raise ValueError(f'Folder already exists: {folder}')
        folder.mkdir(parents=True)
        (folder / 'README.md').write_text(PACKAGE_TEMPLATE.format(title=title(identifier), description=description))
        package = {'id': identifier, 'kind': kind, 'path': f'packages/{identifier}',
                   'version': version or '0.1.0', 'description': description}
    else:
        if not name or not version:
            raise ValueError(f'{kind} packages need --name and an exact --version')
        package = {'id': identifier, 'kind': kind, 'name': name, 'version': version, 'description': description}
    belt['packages'].append(package)
    try:
        save_validated(manifest, belt)
    except Exception:
        if folder:
            shutil.rmtree(folder)
        raise
    return package


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--belt', default='belt.json', help='manifest to update (default: belt.json)')
    sub = parser.add_subparsers(dest='command', required=True)
    skill = sub.add_parser('skill', help='create skills/<name>/SKILL.md and register it')
    skill.add_argument('name')
    skill.add_argument('--description', required=True, help='what it does and when to use it')
    package = sub.add_parser('package', help='register a reusable package')
    package.add_argument('id')
    package.add_argument('--kind', required=True, choices=['files', 'npm', 'pypi'])
    package.add_argument('--description', required=True)
    package.add_argument('--name', help='registry name for npm/pypi packages')
    package.add_argument('--version', help='exact pin (files packages default to 0.1.0)')
    args = parser.parse_args(argv)
    try:
        if args.command == 'skill':
            created = add_skill(args.belt, args.name, args.description)
            print(f'Created and registered {created}. Fill in the steps, then add it to skills/README.md.')
        else:
            created = add_package(args.belt, args.id, args.kind, args.description, args.name, args.version)
            print(f"Registered package {created['id']}@{created['version']}.")
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'Scaffold failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
