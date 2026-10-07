"""Smoke-test one MCP connection from the belt with the pinned MCP Inspector CLI.

Lists the server's tools and, with --call, makes one named harmless call. Header credentials come
only from the environment variables the manifest references; a server whose variables are unset is
skipped. Credential values are never printed. Exit codes: 0 passed or skipped, 1 Inspector run
failed, 3 bad configuration.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from beltfile import find
from validate import all_servers, validate

ROOT = Path(__file__).resolve().parents[1]
INSPECTOR = '@modelcontextprotocol/inspector'
OK, FAILED, BAD_CONFIG = 0, 1, 3


def inspector_spec(belt):
    for package in belt.get('packages', []):
        if package['kind'] == 'npm' and package['name'] == INSPECTOR:
            return f"{INSPECTOR}@{package['version']}"
    raise ValueError(f'belt.json has no pinned npm package named {INSPECTOR}')


def missing_credentials(server, environ):
    return sorted({ref['env'] for ref in server.get('headersFromEnv', {}).values() if not environ.get(ref['env'])})


def header_values(server, environ):
    return {header: ref['prefix'] + environ[ref['env']] for header, ref in server.get('headersFromEnv', {}).items()}


def build_command(spec, server, environ, tool=None, tool_args=None, connect_timeout_ms=60000):
    options = ['--format', 'json', '--connect-timeout', str(connect_timeout_ms)]
    if tool:
        options += ['--method', 'tools/call', '--tool-name', tool, '--tool-args-json', json.dumps(tool_args or {})]
    else:
        options += ['--method', 'tools/list']
    command = ['npx', '--yes', spec, '--cli']
    if server['transport'] == 'stdio':
        # Under --cli, tokens before `--` are the server command; the server's own flags need it.
        return command + [server['command'], *server['args'], '--', *options]
    headers = [arg for name, value in header_values(server, environ).items() for arg in ('--header', f'{name}: {value}')]
    return command + ['--transport', 'http', '--server-url', server['url'], *headers, '--stored-auth-only', *options]


def isolated_env(environ, storage_dir):
    """Keep the run away from a developer's stored OAuth tokens and keep secrets off disk."""
    env = {k: v for k, v in environ.items() if k != 'MCP_CATALOG_PATH'}
    env.update(MCP_STORAGE_DIR=storage_dir, MCP_INSPECTOR_OAUTH_STATE_PATH=str(Path(storage_dir) / 'oauth.json'),
               MCP_INSPECTOR_SECRET_STORE='memory', MCP_AUTO_OPEN_ENABLED='false')
    return env


def redact(text, secrets):
    for secret in secrets:
        text = text.replace(secret, '[redacted]')
    return text


def error_summary(stderr):
    """The Inspector ends a failed run with a one-line JSON error envelope on stderr."""
    lines = stderr.strip().splitlines()
    try:
        error = json.loads(lines[-1])['error']
        return f"{error.get('code', 'error')}: {error.get('message', '')}".strip()
    except (IndexError, ValueError, KeyError, TypeError):
        return lines[-1] if lines else 'no error output'


def smoke(belt, server_id, environ=os.environ, tool=None, tool_args=None, run=subprocess.run, timeout=300):
    server = find(all_servers(belt), server_id, 'server')
    spec = inspector_spec(belt)
    result = {'server': server_id, 'transport': server['transport'], 'inspector': spec,
              'method': 'tools/call' if tool else 'tools/list'}
    missing = missing_credentials(server, environ)
    if missing:
        result.update(status='skipped', detail=f"Set {', '.join(missing)} to test this server")
        return result, OK
    secrets = {environ[ref['env']] for ref in server.get('headersFromEnv', {}).values()}
    with tempfile.TemporaryDirectory() as storage:
        argv = build_command(spec, server, environ, tool, tool_args)
        try:
            done = run(argv, env=isolated_env(environ, storage), capture_output=True, text=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            result.update(status='failed', detail=redact(f'Could not run the Inspector: {error}', secrets))
            return result, FAILED
    if done.returncode != 0:
        result.update(status='failed', exitCode=done.returncode, detail=redact(error_summary(done.stderr), secrets))
        return result, FAILED
    try:
        payload = json.loads(done.stdout)['result']
    except (ValueError, KeyError, TypeError):
        result.update(status='failed', detail='Inspector output was not the expected JSON envelope')
        return result, FAILED
    if tool:
        texts = [c.get('text', '') for c in payload.get('content', []) if isinstance(c, dict) and c.get('type') == 'text']
        result['tool'] = tool
        result['output'] = redact('\n'.join(texts), secrets)
    else:
        result['tools'] = sorted(t['name'] for t in payload.get('tools', []) if isinstance(t, dict) and 'name' in t)
    result['status'] = 'passed'
    return result, OK


def parse_tool_args(text):
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError('--args must be a JSON object')
    return value


def main(argv=None, environ=os.environ, run=subprocess.run):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('server', help='server id from servers or personalServers, e.g. playwright')
    parser.add_argument('--belt', default=str(ROOT / 'belt.json'))
    parser.add_argument('--call', metavar='TOOL', help='also call this harmless, read-only tool')
    parser.add_argument('--args', default='{}', help='JSON object of arguments for --call')
    parser.add_argument('--timeout', type=float, default=300, help='seconds before the run is abandoned')
    parser.add_argument('--json', action='store_true', help='print a JSON result')
    args = parser.parse_args(argv)
    try:
        belt = validate(args.belt)
        tool_args = parse_tool_args(args.args)
        result, code = smoke(belt, args.server, environ, args.call, tool_args, run, args.timeout)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'Configuration error: {error}', file=sys.stderr)
        return BAD_CONFIG
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Server: {result['server']} ({result['transport']}) via {result['inspector']}")
        if 'tools' in result:
            print(f"Tools ({len(result['tools'])}): " + (', '.join(result['tools']) or 'none listed'))
        if 'output' in result:
            print(f"{result['tool']} returned:\n{result['output']}")
        print({'passed': 'Smoke test passed.', 'skipped': f"Skipped: {result.get('detail')}"}
              .get(result['status'], f"Smoke test failed: {result.get('detail')}"))
    return code


if __name__ == '__main__':
    sys.exit(main())
