"""Validate belt declarations without executing tools or loading credentials."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

BASE_FIELDS = {'formatVersion', 'name', 'version', 'description', 'rules',
               'skills', 'servers', 'adapters', 'secretRefs'}
FIELDS = {'0.1-draft': BASE_FIELDS, '0.2-draft': BASE_FIELDS,
          '0.3-draft': BASE_FIELDS | {'models', 'packages', 'personalServers'}}
ADAPTERS = ('claude-code', 'vscode', 'cursor', 'opencode')
STATUSES = ('needs-credentials', 'needs-local-setup', 'untested')
LOOPBACK = ('localhost', '127.0.0.1', '::1')
ID = r'[a-z][a-z0-9-]*'
ENV = r'[A-Z][A-Z0-9_]*'
PIN = r'\d+\.\d+\.\d+([-+.][0-9A-Za-z.-]+)?'
PACKAGE_NAMES = {'npm': r'(@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*',
                 'pypi': r'[A-Za-z0-9][A-Za-z0-9._-]*'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inside(root, entry):
    require(isinstance(entry, str) and bool(entry), 'File path must be a string')
    require(not Path(entry).is_absolute(), 'File path must be relative')
    target = (root / entry).resolve()
    require(target.is_relative_to(root), 'File must stay inside belt')
    return target


def local_file(root, entry):
    target = inside(root, entry)
    require(target.is_file(), 'File must stay inside belt')
    return target


def clean_url(url, allow_http_loopback=False):
    require(isinstance(url, str), 'URL must be text')
    u = urlsplit(url)
    secure = u.scheme == 'https' or (allow_http_loopback and u.scheme == 'http'
                                     and u.hostname in LOOPBACK)
    require(secure and u.hostname and not u.username and not u.password
            and not u.query and not u.fragment,
            'Use HTTPS (or loopback HTTP for local models) without credentials or query')


def validate_skill(root, entry):
    text = local_file(root, entry).read_text()
    require(Path(entry).name == 'SKILL.md', 'Skill must point to SKILL.md')
    require(text.startswith('---\n') and '\n---\n' in text[4:], 'Missing skill frontmatter')
    front = text.split('---', 2)[1]
    name = re.search(r'^name: ([a-z][a-z0-9-]*)$', front, re.M)
    require(name, 'Invalid skill name')
    require(name.group(1) == Path(entry).parent.name, 'Skill name must match its folder')
    require(re.search(r'^description: .+', front, re.M), 'Missing skill description')


def validate_server(s, secrets):
    require(isinstance(s, dict), 'Server must be an object')
    require(isinstance(s.get('id'), str) and re.fullmatch(ID, s['id']), 'Invalid server id')
    require(s.get('status') in STATUSES, 'Invalid status')
    if s.get('transport') == 'http':
        require(set(s) == {'id', 'transport', 'url', 'headersFromEnv', 'status'}, 'Invalid HTTP fields')
        clean_url(s['url'])
        require(isinstance(s['headersFromEnv'], dict), 'Invalid header references')
        for header, ref in s['headersFromEnv'].items():
            require(re.fullmatch(r'[A-Za-z0-9_-]+', header), 'Invalid header name')
            require(isinstance(ref, dict) and set(ref) == {'env', 'prefix'}, 'Invalid secret reference')
            require(ref['env'] in secrets, 'Undeclared secret')
            require(ref['prefix'] in ('', 'Bearer '), 'Unsupported header prefix')
    elif s.get('transport') == 'stdio':
        require(set(s) == {'id', 'transport', 'command', 'args', 'status'}, 'Invalid stdio fields')
        require(isinstance(s['command'], str) and bool(s['command']), 'Missing command')
        require(isinstance(s['args'], list) and all(isinstance(a, str) for a in s['args']), 'Invalid args')
    else:
        raise ValueError('Unsupported transport')


def validate_model(m, secrets):
    require(isinstance(m, dict) and set(m) == {'id', 'api', 'env', 'defaultPreset', 'presets', 'status'},
            'Invalid model fields')
    require(isinstance(m['id'], str) and re.fullmatch(ID, m['id']), 'Invalid model id')
    require(m['api'] == 'openai-compatible', 'Unsupported model API')
    env = m['env']
    require(isinstance(env, dict) and set(env) == {'baseUrl', 'model', 'apiKey'}, 'Invalid model env')
    require(all(isinstance(v, str) and re.fullmatch(ENV, v) for v in env.values()), 'Invalid model env name')
    require(env['apiKey'] in secrets, 'Undeclared secret')
    presets = m['presets']
    require(isinstance(presets, dict) and presets, 'Model needs presets')
    for name, preset in presets.items():
        require(re.fullmatch(ID, name), 'Invalid preset name')
        require(isinstance(preset, dict) and set(preset) == {'baseUrl', 'model', 'docs'}, 'Invalid preset fields')
        clean_url(preset['baseUrl'], allow_http_loopback=True)
        require(isinstance(preset['model'], str), 'Preset model must be text')
        clean_url(preset['docs'])
    require(m['defaultPreset'] in presets, 'Unknown default preset')
    require(m['status'] in STATUSES, 'Invalid status')


def validate_package(p, root):
    require(isinstance(p, dict), 'Package must be an object')
    require(isinstance(p.get('id'), str) and re.fullmatch(ID, p['id']), 'Invalid package id')
    require(isinstance(p.get('version'), str) and re.fullmatch(PIN, p['version']), 'Package version must be an exact pin')
    require(isinstance(p.get('description'), str) and bool(p['description']), 'Missing package description')
    kind = p.get('kind')
    if kind in PACKAGE_NAMES:
        require(set(p) == {'id', 'kind', 'name', 'version', 'description'}, 'Invalid package fields')
        require(isinstance(p['name'], str) and re.fullmatch(PACKAGE_NAMES[kind], p['name']), 'Invalid package name')
    elif kind == 'files':
        require(set(p) == {'id', 'kind', 'path', 'version', 'description'}, 'Invalid package fields')
        require(inside(root, p['path']).is_dir(), 'Package path must be a folder inside belt')
        local_file(root, f"{p['path']}/README.md")
    else:
        raise ValueError('Unsupported package kind')


def check_npm_pins(servers, packages):
    pins = {p['name']: p['version'] for p in packages if p['kind'] == 'npm'}
    for server in servers:
        for arg in server.get('args', []):
            name, _, version = arg.rpartition('@')
            if name in pins:
                require(version == pins[name], f'{server["id"]} must use the {name} package pin')


def all_servers(belt):
    return belt['servers'] + belt.get('personalServers', [])


def validate(path):
    path = Path(path).resolve()
    root = path.parent
    data = json.loads(path.read_text())
    require(isinstance(data, dict), 'Unexpected or missing fields')
    require(data.get('formatVersion') in FIELDS, 'Unsupported format')
    require(set(data) == FIELDS[data['formatVersion']], 'Unexpected or missing fields')
    for key, pattern in [('name', ID), ('version', r'\d+\.\d+\.\d+')]:
        require(isinstance(data[key], str) and re.fullmatch(pattern, data[key]), f'Invalid {key}')
    require(isinstance(data['description'], str), 'description must be text')
    lists = FIELDS[data['formatVersion']] - {'formatVersion', 'name', 'version', 'description'}
    for key in sorted(lists):
        require(isinstance(data[key], list), f'{key} must be an array')
    if data['formatVersion'] == '0.1-draft':
        require(not any(data[k] for k in ['skills', 'servers', 'adapters', 'secretRefs']),
                '0.1 supports only rules')
    for entry in data['rules']:
        local_file(root, entry)
    for entry in data['skills']:
        validate_skill(root, entry)
    require(all(isinstance(x, str) and re.fullmatch(ENV, x) for x in data['secretRefs']), 'Invalid secret name')
    require(len(set(data['secretRefs'])) == len(data['secretRefs']), 'Duplicate secrets')
    require(all(x in ADAPTERS for x in data['adapters']), 'Unsupported adapter')
    if data['formatVersion'] != '0.3-draft':
        require(all(x in ('claude-code', 'vscode') for x in data['adapters']), 'Adapter requires 0.3-draft')
    ids = set()
    for server in all_servers(data):
        validate_server(server, data['secretRefs'])
        require(server['id'] not in ids, 'Duplicate server id')
        ids.add(server['id'])
    for key, check in [('models', lambda m: validate_model(m, data['secretRefs'])),
                       ('packages', lambda p: validate_package(p, root))]:
        seen = set()
        for item in data.get(key, []):
            check(item)
            require(item['id'] not in seen, f'Duplicate {key[:-1]} id')
            seen.add(item['id'])
    check_npm_pins(all_servers(data), data.get('packages', []))
    return data


ADOPTION_MARKER = '.tool-belt.json'
BELT_REPO = 'ianmkinney/Ian-tool-belt'


def validate_adoption(path):
    """Validate an app repo's .tool-belt.json adoption marker."""
    path = Path(path)
    if path.is_dir():
        path = path / ADOPTION_MARKER
    data = json.loads(path.read_text())
    require(isinstance(data, dict) and set(data) == {'belt', 'beltVersion'},
            'Unexpected or missing marker fields')
    require(data['belt'] == BELT_REPO, f'Marker must reference {BELT_REPO}')
    require(isinstance(data['beltVersion'], str)
            and re.fullmatch(r'\d+\.\d+\.\d+', data['beltVersion']), 'Invalid beltVersion')
    return data


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python3 scripts/validate.py BELT_JSON|.tool-belt.json|APP_DIR')
    target = Path(sys.argv[1])
    try:
        if target.is_dir() or target.name == ADOPTION_MARKER:
            marker = validate_adoption(target)
            print(f"Adopts belt: {marker['belt']}@{marker['beltVersion']}")
        else:
            belt = validate(target)
            print(f"Valid belt: {belt['name']}@{belt['version']}")
    except (OSError, ValueError, TypeError, KeyError) as error:
        sys.exit(f'Invalid belt: {error}')
