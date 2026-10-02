"""Generate client configuration; never install, authenticate or execute servers."""
import argparse
import json
import shutil
from pathlib import Path
from validate import validate


def export_belt(manifest, target, output):
    manifest = Path(manifest).resolve()
    belt = validate(manifest)
    if target not in belt['adapters']:
        raise ValueError('Target is not declared in this belt')
    output = Path(output)
    if output.exists():
        raise ValueError('Output already exists; choose a new directory')
    servers = {}
    for server in belt['servers']:
        if server['transport'] == 'stdio':
            config = {'command': server['command'], 'args': server['args'], 'type': 'stdio'}
        else:
            headers = {}
            for header, ref in server['headersFromEnv'].items():
                variable = '${' + ('env:' if target == 'vscode' else '') + ref['env'] + '}'
                headers[header] = ref['prefix'] + variable
            config = {'type': 'http', 'url': server['url'], 'headers': headers}
        servers[server['id']] = config
    root_key, filename = ('mcpServers', '.mcp.json') if target == 'claude-code' else ('servers', '.vscode/mcp.json')
    output.mkdir(parents=True)
    destination = output / filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({root_key: servers}, indent=2) + '\n')
    rules = [ (manifest.parent / p).read_text() for p in belt['rules'] ]
    instructions = '\n\n'.join(rules) + '\n\n## Available skills\n'
    for entry in belt['skills']:
        destination = output / entry
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(manifest.parent / entry, destination)
        instructions += f'- Read `{entry}` when its description matches the task.\n'
    (output / 'INSTRUCTIONS.md').write_text(instructions)
    report = {'target':target, 'beltVersion':belt['version'], 'connectionConfig':'generated',
              'authentication':'not-performed', 'liveClientTest':'not-performed',
              'rulesAndSkills':'manual-loading-required', 'gateway':'not-implemented',
              'secretRefs':belt['secretRefs']}
    (output / 'compatibility.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest')
    parser.add_argument('--target', required=True, choices=['claude-code','vscode'])
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        report = export_belt(args.manifest, args.target, args.out)
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f'Export failed: {error}\n')
    print(json.dumps(report, indent=2))
