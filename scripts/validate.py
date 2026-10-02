"""Validate belt declarations without executing tools or loading credentials."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local_file(root, entry):
    require(isinstance(entry, str) and bool(entry), 'File path must be a string')
    require(not Path(entry).is_absolute(), 'File path must be relative')
    target = (root / entry).resolve()
    require(target.is_relative_to(root) and target.is_file(), 'File must stay inside belt')
    return target


def validate(path):
    path = Path(path).resolve()
    data = json.loads(path.read_text())
    fields = {'formatVersion', 'name', 'version', 'description', 'rules',
              'skills', 'servers', 'adapters', 'secretRefs'}
    require(isinstance(data, dict) and set(data) == fields, 'Unexpected or missing fields')
    require(data['formatVersion'] in ('0.1-draft', '0.2-draft'), 'Unsupported format')
    for key, pattern in [('name', r'[a-z][a-z0-9-]*'), ('version', r'\d+\.\d+\.\d+')]:
        require(isinstance(data[key], str) and re.fullmatch(pattern, data[key]), f'Invalid {key}')
    require(isinstance(data['description'], str), 'description must be text')
    for key in ['rules', 'skills', 'servers', 'adapters', 'secretRefs']:
        require(isinstance(data[key], list), f'{key} must be an array')
    if data['formatVersion'] == '0.1-draft':
        require(not any(data[k] for k in ['skills', 'servers', 'adapters', 'secretRefs']),
                '0.1 supports only rules')
    for entry in data['rules'] + data['skills']:
        local_file(path.parent, entry)
    for entry in data['skills']:
        text = local_file(path.parent, entry).read_text()
        require(Path(entry).name == 'SKILL.md', 'Skill must point to SKILL.md')
        require(text.startswith('---\n') and '\n---\n' in text[4:], 'Missing skill frontmatter')
        front = text.split('---', 2)[1]
        require(re.search(r'^name: [a-z][a-z0-9-]*$', front, re.M), 'Invalid skill name')
        require(re.search(r'^description: .+', front, re.M), 'Missing skill description')
    require(all(isinstance(x, str) and re.fullmatch(r'[A-Z][A-Z0-9_]*', x)
                for x in data['secretRefs']), 'Invalid secret name')
    require(len(set(data['secretRefs'])) == len(data['secretRefs']), 'Duplicate secrets')
    require(all(x in ('claude-code', 'vscode') for x in data['adapters']), 'Unsupported adapter')
    ids = set()
    for s in data['servers']:
        require(isinstance(s, dict), 'Server must be an object')
        identifier = s.get('id')
        require(isinstance(identifier, str) and re.fullmatch(r'[a-z][a-z0-9-]*', identifier), 'Invalid server id')
        require(identifier not in ids, 'Duplicate server id')
        ids.add(identifier)
        require(s.get('status') in ('needs-credentials', 'needs-local-setup', 'untested'), 'Invalid status')
        if s.get('transport') == 'http':
            require(set(s) == {'id','transport','url','headersFromEnv','status'}, 'Invalid HTTP fields')
            require(isinstance(s['url'], str), 'URL must be text')
            u = urlsplit(s['url'])
            require(u.scheme == 'https' and u.hostname and not u.username and not u.password
                    and not u.query and not u.fragment, 'Use HTTPS URL without credentials or query')
            require(isinstance(s['headersFromEnv'], dict), 'Invalid header references')
            for header, ref in s['headersFromEnv'].items():
                require(re.fullmatch(r'[A-Za-z0-9_-]+', header), 'Invalid header name')
                require(isinstance(ref, dict) and set(ref) == {'env','prefix'}, 'Invalid secret reference')
                require(ref['env'] in data['secretRefs'], 'Undeclared secret')
                require(ref['prefix'] in ('', 'Bearer '), 'Unsupported header prefix')
        elif s.get('transport') == 'stdio':
            require(set(s) == {'id','transport','command','args','status'}, 'Invalid stdio fields')
            require(isinstance(s['command'], str) and bool(s['command']), 'Missing command')
            require(isinstance(s['args'], list) and all(isinstance(a,str) for a in s['args']), 'Invalid args')
        else:
            raise ValueError('Unsupported transport')
    return data


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 scripts/validate.py BELT_JSON')
    try:
        belt = validate(sys.argv[1])
    except (OSError, ValueError, TypeError) as error:
        sys.exit(f'Invalid belt: {error}')
    print(f"Valid belt: {belt['name']}@{belt['version']}")
