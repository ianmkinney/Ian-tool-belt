"""Build the machine-readable belt map from belt.json, scripts and workflows."""
import json
import re
from pathlib import Path
from validate import ADAPTER_INFO, ADAPTERS, one_line, validate

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / 'belt.index.json'
AGENTS_PATH = ROOT / 'AGENTS.md'
INDEX_START = '<!-- belt-index:start -->'
INDEX_END = '<!-- belt-index:end -->'

COMMANDS = [
    {'id': 'use', 'run': 'python3 belt.py use',
     'description': 'Write this belt into the current project for Cursor, OpenCode, Claude Code or VS Code.'},
    {'id': 'doctor', 'run': 'python3 belt.py doctor',
     'description': 'Validate the belt, report missing env vars, and check local AI if it is running.'},
    {'id': 'list', 'run': 'python3 belt.py list',
     'description': 'Print every item in the belt with its one-line description.'},
    {'id': 'add', 'run': 'python3 belt.py add skill|package ...',
     'description': 'Scaffold a skill or package and register it in belt.json.'},
    {'id': 'set', 'run': 'python3 belt.py set PATH VALUE',
     'description': 'Change one allowlisted belt.json field and validate.'},
    {'id': 'run', 'run': 'python3 belt.py run TASK',
     'description': 'Run one allowlisted task (validate, tests, export, pins).'},
    {'id': 'index', 'run': 'python3 belt.py index',
     'description': 'Regenerate belt.index.json and the AGENTS.md belt map. CI runs index --check.'},
]

RULE_INFO = {
    'rules/working-agreement.md':
        'Shared operating rules: small changes, secrets out of Git, honest verification. Always apply.',
    'rules/engineering.md':
        'Clean code, tests, one PR per session, Conventional Commit titles, keep CI green. Follow on every code change.',
}

SCRIPT_INFO = {
    'belt.py': 'One command entry point for the belt. Prefer this over calling scripts/ directly.',
    'scripts/validate.py': 'Validate belt.json without running tools or reading secrets. Use before export or commit.',
    'scripts/export.py': 'Write one client export into a new directory. belt.py use wraps this and copies into a project.',
    'scripts/new.py': 'Scaffold a skill or package and register it. belt.py add wraps this.',
    'scripts/belt_set.py': 'Set one allowlisted belt.json value, then validate or roll back. belt.py set wraps this.',
    'scripts/check_pins.py': 'Look up newer stable npm/PyPI releases for pinned packages. Report-only unless --apply.',
    'scripts/tasks.py': 'Run one allowlisted belt task without a shell. belt.py run wraps this.',
    'scripts/local_ai_check.py': 'Contact the local OpenAI-compatible endpoint. Only script that does; belt.py doctor wraps it.',
    'scripts/mcp_smoke.py': 'Start one MCP server through the pinned Inspector and list (or call) a tool.',
    'scripts/belt_sync.py': 'Copy managed adoption-kit files into an app repo. Use --adopt for a first install.',
    'scripts/beltfile.py': 'Shared load/save helpers for belt.json. Import from other scripts; do not run it.',
    'scripts/build_tokens.py': 'Generate styling/tokens.css from tokens.json. --check confirms they match.',
    'scripts/belt_index.py': 'Build belt.index.json and the AGENTS.md map from belt.json. belt.py index wraps this.',
    'scripts/check_shell.py': 'Run shellcheck on git-tracked shell scripts. CI uses the belt shellcheck pin; not part of client export.',
}

WORKFLOW_INFO = {
    '.github/workflows/checks.yml':
        'Validate manifests, run tests, check tokens, export all four clients, and verify the generated index.',
    '.github/workflows/update-variable.yml':
        'Manually set one allowlisted belt.json value and open a draft PR.',
    '.github/workflows/bump-pins.yml':
        'Weekly lookup of newer npm/PyPI pins; opens a draft PR if a stable release is newer.',
    '.github/workflows/run-task.yml':
        'Manually run one allowlisted belt task and upload its log.',
    '.github/workflows/zizmor.yml':
        'Security-lint GitHub workflows with the zizmor pin from belt.json.',
    '.github/workflows/actionlint.yml':
        'Syntax-lint GitHub workflows with the actionlint-py pin from belt.json.',
    '.github/workflows/shellcheck.yml':
        'Lint tracked shell scripts with the shellcheck-py pin via scripts/check_shell.py.',
    '.github/workflows/gitleaks.yml':
        'Scan the repository for leaked secrets with the gitleaks github-release pin from belt.json.',
    '.github/workflows/release.yml':
        'release-please on push to main; merging its PR bumps versions and tags.',
    '.github/workflows/pr-title.yml':
        'Require a Conventional Commit pull request title.',
    '.github/workflows/belt-sync-reusable.yml':
        'Reusable weekly sync of managed files into adopted app repos.',
    '.github/workflows/release-please-reusable.yml':
        'Reusable release-please job for this repo and adopted apps.',
    '.github/workflows/pr-title-reusable.yml':
        'Reusable Conventional Commit title check for this repo and adopted apps.',
}

TEMPLATE_INFO = {
    'templates/app-adoption/AGENTS.md':
        'App-repo agent instructions pointing at belt rules. Copied by belt_sync --adopt.',
    'templates/app-adoption/.github/workflows/belt.yml':
        'App caller for PR-title and release-please reusable workflows.',
    'templates/app-adoption/.github/workflows/belt-sync.yml':
        'App caller for the weekly managed-file sync.',
    'templates/app-adoption/.tool-belt.json':
        'Adoption marker (belt name + version). Validate with python3 scripts/validate.py APP_DIR.',
    'templates/versioning/release.yml':
        'Standalone release-please caller template for app repos.',
    'templates/versioning/pr-title.yml':
        'Standalone PR-title caller template for app repos.',
    'templates/versioning/README.md':
        'How to wire release-please, PR titles and optional tokens in an app repo.',
    'templates/versioning/release-please-config.json':
        'release-please config copied into an app repo (release-type, extra-files).',
    'templates/versioning/.release-please-manifest.json':
        'release-please manifest template; the app version starts at 0.0.0.',
}

SKIPPED = [
    {'id': 'styling', 'reason': 'files package; copy styling/ yourself. Client exports do not include it.'},
    {'id': 'zizmor', 'reason': 'CI-only pin read by zizmor.yml; not an MCP server or export.'},
    {'id': 'actionlint', 'reason': 'CI-only pin read by actionlint.yml; not an MCP server or export.'},
    {'id': 'shellcheck', 'reason': 'CI-only pin read by shellcheck.yml and actionlint -shellcheck; not an MCP server or export.'},
    {'id': 'gitleaks', 'reason': 'CI-only pin read by gitleaks.yml; not an MCP server or export.'},
    {'id': 'mcp-inspector', 'reason': 'Used by scripts/mcp_smoke.py; not declared as a connection.'},
    {'id': 'ollmcp', 'reason': 'Optional client. Load the claude-code export with --servers-json; not a fifth adapter.'},
    {'id': 'playwright-mcp', 'reason': 'Consumed through the playwright server args, not copied as its own export.'},
    {'id': 'personalServers', 'reason': 'Outside-work connections. Omitted from exports and this index unless --include-personal.'},
    {'id': 'chatgpt', 'reason': 'Not an export adapter. Needs a hosted integration this belt does not generate.'},
]


def skill_description(root, entry):
    text = (root / entry).read_text()
    match = re.search(r'^description:\s+(.+)$', text.split('---', 2)[1], re.M)
    if not match:
        raise ValueError(f'Missing skill description in {entry}')
    value = json.loads(match.group(1)) if match.group(1).startswith('"') else match.group(1).strip()
    return one_line(value, f'{entry} description')


def package_pin(belt, package_id):
    return next(p for p in belt['packages'] if p['id'] == package_id)


def require_catalog(info, paths, label):
    expected = {str(p) if isinstance(p, str) else str(p) for p in paths}
    missing = expected - set(info)
    extra = set(info) - expected
    if missing or extra:
        raise ValueError(f'{label} catalog mismatch. Missing: {sorted(missing)}. Extra: {sorted(extra)}.')
    for key, description in info.items():
        one_line(description, f'{key} description')


def build(manifest=None, include_personal=False, checkout=ROOT):
    """Describe a belt.json. Script/workflow catalogs always come from this checkout."""
    manifest = Path(manifest or checkout / 'belt.json').resolve()
    root = manifest.parent
    belt = validate(manifest)
    scripts = ['belt.py', *[f'scripts/{p.name}' for p in sorted((checkout / 'scripts').glob('*.py'))]]
    workflows = [f'.github/workflows/{p.name}' for p in sorted((checkout / '.github/workflows').glob('*.yml'))]
    templates = [str(p.relative_to(checkout)) for p in sorted((checkout / 'templates').rglob('*'))
                 if p.is_file()]
    require_catalog(SCRIPT_INFO, scripts, 'script')
    require_catalog(WORKFLOW_INFO, workflows, 'workflow')
    require_catalog(RULE_INFO, belt['rules'], 'rule')
    require_catalog(TEMPLATE_INFO, templates, 'template')
    ollmcp = package_pin(belt, 'ollmcp')
    model = belt['models'][0]
    default = model['presets'][model['defaultPreset']]
    index = {
        'name': belt['name'],
        'version': belt['version'],
        'formatVersion': belt['formatVersion'],
        'description': belt['description'],
        'commands': COMMANDS,
        'servers': [{'id': s['id'], 'transport': s['transport'], 'status': s['status'],
                     'description': s['description']} for s in belt['servers']],
        'personalServers': {
            'count': len(belt.get('personalServers', [])),
            'exportedByDefault': False,
            'note': 'Outside-work connections. Details omitted here. Pass --include-personal to list or export them.',
        },
        'models': [{
            'id': model['id'], 'api': model['api'], 'status': model['status'],
            'description': model['description'], 'defaultPreset': model['defaultPreset'],
            'env': model['env'],
            'presets': [{'id': name, **{k: preset[k] for k in ('baseUrl', 'model', 'docs', 'description')}}
                        for name, preset in model['presets'].items()],
        }],
        'packages': [{'id': p['id'], 'kind': p['kind'], 'name': p.get('name', p.get('path')),
                      'version': p['version'], 'description': p['description']} for p in belt['packages']],
        'skills': [{'id': Path(entry).parent.name, 'path': entry,
                    'description': skill_description(root, entry)} for entry in belt['skills']],
        'rules': [{'id': Path(entry).stem, 'path': entry, 'description': RULE_INFO[entry]}
                  for entry in belt['rules']],
        'adapters': [{'id': name, **ADAPTER_INFO[name]} for name in belt['adapters']],
        'scripts': [{'id': path, 'description': SCRIPT_INFO[path]} for path in scripts],
        'workflows': [{'id': path, 'description': WORKFLOW_INFO[path]} for path in workflows],
        'templates': [{'id': path, 'description': TEMPLATE_INFO[path]} for path in templates],
        'skipped': SKIPPED,
        'secretRefs': [{'name': name,
                        'optional': name == model['env']['apiKey'],
                        'description': ('Optional local-runtime key; Ollama ignores it.'
                                        if name == model['env']['apiKey']
                                        else 'Set in the client environment before using the matching MCP server.')}
                       for name in belt['secretRefs']],
        'localModel': {
            'id': model['id'],
            'defaultPreset': model['defaultPreset'],
            'model': default['model'],
            'check': 'python3 belt.py doctor',
            'load': [
                {'client': 'opencode',
                 'run': 'python3 belt.py use opencode',
                 'then': 'OpenCode reads opencode.json, including the local-ai provider.'},
                {'client': 'claude-code',
                 'run': 'python3 belt.py use claude-code',
                 'then': 'ollama launch claude in that project; attach INSTRUCTIONS.md and skills/.'},
                {'client': 'ollmcp',
                 'run': (f'python3 belt.py use claude-code --out dist/claude-code && '
                         f'uvx ollmcp=={ollmcp["version"]} --servers-json dist/claude-code/.mcp.json '
                         f'--model {default["model"] or "MODEL"}'),
                 'then': 'Not an export adapter. HTTP header placeholders are not expanded; see docs/local-ai.md.'},
            ],
        },
    }
    if include_personal:
        index['personalServers']['servers'] = [
            {'id': s['id'], 'transport': s['transport'], 'status': s['status'],
             'description': s['description']} for s in belt.get('personalServers', [])]
    return index


def dump(index):
    return json.dumps(index, indent=2) + '\n'


def agents_map(index):
    lines = [
        '## Belt map',
        '',
        'Generated from `belt.json`. Do not edit between the markers; run `python3 belt.py index`.',
        'Machine-readable copy: [`belt.index.json`](belt.index.json).',
        '',
        '### Commands',
        '',
    ]
    for command in index['commands']:
        lines.append(f"- `{command['run']}` — {command['description']}")
    lines += ['', '### Drop this belt into a project', '',
              '```sh', 'python3 path/to/Ian-tool-belt/belt.py use', '```', '',
              'Auto-detects Cursor, OpenCode, Claude Code or VS Code. Pass a target if several are present. '
              'Existing files are left alone unless `--force`. Personal connections stay out unless `--include-personal`.',
              '', '### Connections, skills, rules', '']
    for group, key in [('Servers', 'servers'), ('Skills', 'skills'), ('Rules', 'rules')]:
        lines.append(f'**{group}**')
        for item in index[key]:
            lines.append(f"- `{item['id']}` — {item['description']}")
        lines.append('')
    lines += ['### Local model', '',
              f"Optional `{index['localModel']['id']}` (default preset `{index['localModel']['defaultPreset']}`, "
              f"model `{index['localModel']['model'] or '(unset)'}`). Check with `python3 belt.py doctor`.",
              '']
    for load in index['localModel']['load']:
        lines.append(f"- **{load['client']}:** `{load['run']}` — {load['then']}")
    lines += ['', '### Not exported as connections', '']
    for item in index['skipped']:
        lines.append(f"- `{item['id']}` — {item['reason']}")
    lines.append('')
    return '\n'.join(lines)


def render_agents(existing, section):
    if INDEX_START not in existing or INDEX_END not in existing:
        raise ValueError(f'{AGENTS_PATH.name} must contain {INDEX_START} and {INDEX_END} markers')
    before, rest = existing.split(INDEX_START, 1)
    _, after = rest.split(INDEX_END, 1)
    return f'{before}{INDEX_START}\n{section}{INDEX_END}{after}'


def write(index, agents_path=AGENTS_PATH, index_path=INDEX_PATH):
    index_path.write_text(dump(index))
    agents_path.write_text(render_agents(agents_path.read_text(), agents_map(index)))
    return index_path, agents_path


def check(index, agents_path=AGENTS_PATH, index_path=INDEX_PATH):
    expected_index = dump(index)
    expected_agents = render_agents(agents_path.read_text(), agents_map(index))
    stale = []
    if index_path.read_text() != expected_index:
        stale.append(str(index_path.name))
    if agents_path.read_text() != expected_agents:
        stale.append(str(agents_path.name))
    return stale
