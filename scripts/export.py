"""Generate client configuration; never install, authenticate or execute servers."""
import argparse
import json
import re
from pathlib import Path
from validate import ADAPTERS, validate

ENV_SYNTAX = {'claude-code': '${%s}', 'vscode': '${env:%s}', 'cursor': '${env:%s}', 'opencode': '{env:%s}'}
MCP_FILE = {'claude-code': ('.mcp.json', 'mcpServers'), 'vscode': ('.vscode/mcp.json', 'servers'),
            'cursor': ('.cursor/mcp.json', 'mcpServers')}
SKILL_ROOT = {'cursor': '.cursor/skills', 'opencode': '.opencode/skills'}
NATIVE = ('cursor', 'opencode')


def server_config(target, server):
    if server['transport'] == 'stdio':
        if target == 'opencode':
            return {'type': 'local', 'command': [server['command'], *server['args']], 'enabled': True}
        return {'type': 'stdio', 'command': server['command'], 'args': server['args']}
    headers = {header: ref['prefix'] + ENV_SYNTAX[target] % ref['env']
               for header, ref in server['headersFromEnv'].items()}
    if target == 'opencode':
        config = {'type': 'remote', 'url': server['url'], 'enabled': True, 'headers': headers}
        if headers:
            config['oauth'] = False
        return config
    if target == 'cursor':
        return {'url': server['url'], 'headers': headers}
    return {'type': 'http', 'url': server['url'], 'headers': headers}


def local_model(belt, preset_name):
    models = belt.get('models', [])
    if not models:
        if preset_name:
            raise ValueError('This belt declares no local model presets')
        return None
    model = models[0]
    preset_name = preset_name or model['defaultPreset']
    if preset_name not in model['presets']:
        raise ValueError(f'Unknown preset: {preset_name}')
    return model, preset_name, model['presets'][preset_name]


def opencode_config(target_servers, model_info):
    config = {'$schema': 'https://opencode.ai/config.json', 'instructions': ['INSTRUCTIONS.md'],
              'mcp': target_servers}
    if model_info:
        model, preset_name, preset = model_info
        if not preset['model']:
            raise ValueError(f'Preset {preset_name} has no model; set models.{model["id"]}.presets.'
                             f'{preset_name}.model with scripts/belt_set.py first')
        config['provider'] = {model['id']: {
            'npm': '@ai-sdk/openai-compatible',
            'name': f'Local AI ({preset_name})',
            'options': {'baseURL': preset['baseUrl'], 'apiKey': ENV_SYNTAX['opencode'] % model['env']['apiKey']},
            'models': {preset['model']: {'name': preset['model']}}}}
        config['model'] = f"{model['id']}/{preset['model']}"
    return config


def env_example(model_info):
    model, preset_name, preset = model_info
    lines = [f'# Local AI connection for {model["id"]}; default preset: {preset_name}.',
             '# Put these in your shell profile or an untracked .env. Never commit real keys.',
             f"{model['env']['baseUrl']}={preset['baseUrl']}",
             f"{model['env']['model']}={preset['model']}",
             '# Ollama and most local runtimes ignore the key; set it only if yours requires one.',
             f"{model['env']['apiKey']}=", '', '# Other presets:']
    for name, other in model['presets'].items():
        if name != preset_name:
            lines.append(f"# {name}: {model['env']['baseUrl']}={other['baseUrl']}  ({other['docs']})")
    return '\n'.join(lines) + '\n'


def skill_destination(target, entry):
    if target in SKILL_ROOT:
        return f'{SKILL_ROOT[target]}/{Path(entry).parent.name}'
    return str(Path(entry).parent)


def copy_skill(source_dir, destination):
    for path in sorted(source_dir.rglob('*')):
        if path.is_file() and not path.is_symlink():
            target = destination / path.relative_to(source_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())


def cursor_rule(text):
    heading = re.search(r'^#\s+(.+)$', text, re.M)
    description = heading.group(1).strip() if heading else 'Tool Belt rule'
    return f'---\ndescription: {json.dumps(description)}\nalwaysApply: true\n---\n\n{text}'


def export_belt(manifest, target, output, preset=None, include_personal=False):
    manifest = Path(manifest).resolve()
    belt = validate(manifest)
    if target not in belt['adapters']:
        raise ValueError('Target is not declared in this belt')
    output = Path(output)
    if output.exists():
        raise ValueError('Output already exists; choose a new directory')
    model_info = local_model(belt, preset)
    servers = belt['servers'] + (belt.get('personalServers', []) if include_personal else [])
    target_servers = {s['id']: server_config(target, s) for s in servers}
    files = {}
    if target == 'opencode':
        files['opencode.json'] = json.dumps(opencode_config(target_servers, model_info), indent=2) + '\n'
    else:
        filename, root_key = MCP_FILE[target]
        files[filename] = json.dumps({root_key: target_servers}, indent=2) + '\n'
    rules = [(entry, (manifest.parent / entry).read_text()) for entry in belt['rules']]
    if target == 'cursor':
        for entry, text in rules:
            files[f'.cursor/rules/{Path(entry).stem}.mdc'] = cursor_rule(text)
    instructions = '\n\n'.join(text for _, text in rules) + '\n\n## Available skills\n'
    skills = {entry: skill_destination(target, entry) for entry in belt['skills']}
    for destination in skills.values():
        instructions += f'- Read `{destination}/SKILL.md` when its description matches the task.\n'
    if model_info:
        model, preset_name, preset_values = model_info
        instructions += (f"\n## Local model\n\nAn optional OpenAI-compatible local model (`{model['id']}`, "
                         f"preset `{preset_name}`) may be configured through `{model['env']['baseUrl']}`, "
                         f"`{model['env']['model']}` and `{model['env']['apiKey']}`. It is not assumed to be "
                         'running. Check it with `python3 scripts/local_ai_check.py` from the belt checkout '
                         'before relying on it.\n')
        files['local-ai.env.example'] = env_example(model_info)
    files['INSTRUCTIONS.md'] = instructions
    report = {'target': target, 'beltVersion': belt['version'], 'connectionConfig': 'generated',
              'authentication': 'not-performed', 'liveClientTest': 'not-performed',
              'rulesAndSkills': ('native-locations-generated-untested' if target in NATIVE
                                 else 'manual-loading-required'),
              'gateway': 'not-implemented', 'secretRefs': belt['secretRefs'],
              'personalConnections': 'included' if include_personal else 'excluded',
              'packages': [f"{p['id']}@{p['version']}" for p in belt.get('packages', [])]}
    if model_info:
        report['localModel'] = {'id': model_info[0]['id'], 'preset': model_info[1],
                                'baseUrl': model_info[2]['baseUrl'], 'reachability': 'not-checked',
                                'clientWiring': ('provider-config-generated' if target == 'opencode'
                                                 else 'env-example-only')}
    files['compatibility.json'] = json.dumps(report, indent=2) + '\n'
    output.mkdir(parents=True)
    for relative, text in files.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)
    for entry, destination in skills.items():
        copy_skill((manifest.parent / entry).parent, output / destination)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest')
    parser.add_argument('--target', required=True, choices=ADAPTERS)
    parser.add_argument('--out', required=True)
    parser.add_argument('--preset', help='local model preset (default: the belt\'s defaultPreset)')
    parser.add_argument('--include-personal', action='store_true',
                        help='also export personalServers (excluded by default)')
    args = parser.parse_args()
    try:
        report = export_belt(args.manifest, args.target, args.out, args.preset, args.include_personal)
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f'Export failed: {error}\n')
    print(json.dumps(report, indent=2))
