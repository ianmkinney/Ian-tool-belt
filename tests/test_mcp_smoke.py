import io
import json
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout

from belt_fixture import ROOT, BeltCase, load_script

smoke = load_script('mcp_smoke')
TOKEN = 'ghp_synthetic_token_value'


class FakeRun:
    def __init__(self, returncode=0, stdout='', stderr='', error=None):
        self.calls = []
        self.returncode, self.stdout, self.stderr, self.error = returncode, stdout, stderr, error

    def __call__(self, argv, env, **kwargs):
        self.calls.append((argv, env))
        if self.error:
            raise self.error
        return subprocess.CompletedProcess(argv, self.returncode, self.stdout, self.stderr)


def tools_listing(*names):
    return json.dumps({'result': {'tools': [{'name': n, 'inputSchema': {'type': 'object'}} for n in names]}})


def run_main(argv, environ, run):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = smoke.main(argv, environ, run)
    return code, out.getvalue(), err.getvalue()


class McpSmokeTests(BeltCase):
    def test_stdio_server_flags_stay_before_the_separator(self):
        run = FakeRun(stdout=tools_listing('browser_tabs', 'browser_click'))
        result, code = smoke.smoke(self.data, 'playwright', {}, run=run)
        self.assertEqual(code, smoke.OK)
        self.assertEqual(result['tools'], ['browser_click', 'browser_tabs'])
        argv, env = run.calls[0]
        playwright = next(s for s in self.data['servers'] if s['id'] == 'playwright')
        self.assertEqual(argv[:4], ['npx', '--yes', smoke.inspector_spec(self.data), '--cli'])
        separator = argv.index('--')
        self.assertEqual(argv[4:separator], [playwright['command'], *playwright['args']])
        self.assertIn('--headless', argv[4:separator])
        self.assertEqual(argv[separator + 1:], ['--format', 'json', '--connect-timeout', '60000',
                                               '--method', 'tools/list'])
        self.assertEqual(env['MCP_INSPECTOR_SECRET_STORE'], 'memory')
        self.assertEqual(env['MCP_AUTO_OPEN_ENABLED'], 'false')
        self.assertTrue(env['MCP_INSPECTOR_OAUTH_STATE_PATH'].startswith(env['MCP_STORAGE_DIR']))

    def test_inspector_uses_the_package_pin(self):
        next(p for p in self.data['packages'] if p['id'] == 'mcp-inspector')['version'] = '2.10.1'
        run = FakeRun(stdout=tools_listing())
        smoke.smoke(self.data, 'playwright', {}, run=run)
        self.assertIn('@modelcontextprotocol/inspector@2.10.1', run.calls[0][0])

    def test_inherited_oauth_state_and_catalog_are_replaced(self):
        run = FakeRun(stdout=tools_listing())
        environ = {'MCP_INSPECTOR_OAUTH_STATE_PATH': '/home/me/real-oauth.json', 'MCP_CATALOG_PATH': '/home/me/mcp.json'}
        smoke.smoke(self.data, 'playwright', environ, run=run)
        env = run.calls[0][1]
        self.assertNotIn('MCP_CATALOG_PATH', env)
        self.assertNotEqual(env['MCP_INSPECTOR_OAUTH_STATE_PATH'], '/home/me/real-oauth.json')

    def test_named_call_passes_json_arguments_verbatim(self):
        run = FakeRun(stdout=json.dumps({'result': {'content': [{'type': 'text', 'text': '- 0: about:blank'}]}}))
        result, code = smoke.smoke(self.data, 'playwright', {}, 'browser_tabs', {'action': 'list'}, run)
        self.assertEqual(code, smoke.OK)
        self.assertEqual(result['output'], '- 0: about:blank')
        argv = run.calls[0][0]
        self.assertEqual(argv[-6:], ['--method', 'tools/call', '--tool-name', 'browser_tabs',
                                     '--tool-args-json', '{"action": "list"}'])

    def test_http_server_reads_header_from_its_env_var(self):
        run = FakeRun(stdout=tools_listing('get_me'))
        smoke.smoke(self.data, 'github', {'GITHUB_MCP_TOKEN': TOKEN}, run=run)
        argv = run.calls[0][0]
        self.assertNotIn('--', argv)
        self.assertEqual(argv[argv.index('--server-url') + 1], 'https://api.githubcopilot.com/mcp/readonly')
        self.assertEqual(argv[argv.index('--header') + 1], f'Authorization: Bearer {TOKEN}')
        self.assertIn('--stored-auth-only', argv)
        self.assertEqual(argv[argv.index('--transport') + 1], 'http')

    def test_missing_credentials_skip_without_running(self):
        run = FakeRun()
        code, out, _ = run_main(['github', '--belt', str(self.manifest)], {'GITHUB_MCP_TOKEN': ''}, run)
        self.assertEqual(code, smoke.OK)
        self.assertEqual(run.calls, [])
        self.assertIn('Skipped: Set GITHUB_MCP_TOKEN', out)

    def test_failures_report_the_error_envelope_without_the_secret(self):
        envelope = json.dumps({'error': {'code': 'auth_required', 'message': f'rejected Bearer {TOKEN}'}})
        run = FakeRun(returncode=3, stderr=f'Unauthorized\n{envelope}\n')
        code, out, _ = run_main(['github', '--belt', str(self.manifest), '--json'], {'GITHUB_MCP_TOKEN': TOKEN}, run)
        self.assertEqual(code, smoke.FAILED)
        result = json.loads(out)
        self.assertEqual(result['exitCode'], 3)
        self.assertEqual(result['detail'], 'auth_required: rejected Bearer [redacted]')
        self.assertNotIn(TOKEN, out)

    def test_tool_output_is_redacted(self):
        run = FakeRun(stdout=json.dumps({'result': {'content': [{'type': 'text', 'text': f'echo {TOKEN}'}]}}))
        result, _ = smoke.smoke(self.data, 'github', {'GITHUB_MCP_TOKEN': TOKEN}, 'get_me', {}, run)
        self.assertEqual(result['output'], 'echo [redacted]')

    def test_inspector_that_cannot_start_fails_cleanly(self):
        for error in [FileNotFoundError('npx'), subprocess.TimeoutExpired('npx', 300)]:
            result, code = smoke.smoke(self.data, 'playwright', {}, run=FakeRun(error=error))
            self.assertEqual((code, result['status']), (smoke.FAILED, 'failed'))

    def test_unexpected_output_fails(self):
        result, code = smoke.smoke(self.data, 'playwright', {}, run=FakeRun(stdout='not json'))
        self.assertEqual((code, result['status']), (smoke.FAILED, 'failed'))

    def test_configuration_errors(self):
        without_inspector = [p for p in self.data['packages'] if p['id'] != 'mcp-inspector']
        cases = [(['nope'], 'Unknown server'), (['playwright', '--args', '[1]'], 'JSON object'),
                 (['playwright', '--args', '{bad'], 'Configuration error')]
        for argv, message in cases:
            code, _, err = run_main(argv + ['--belt', str(self.manifest)], {}, FakeRun())
            self.assertEqual(code, smoke.BAD_CONFIG)
            self.assertIn(message, err)
        self.data['packages'] = without_inspector
        self.write()
        code, _, err = run_main(['playwright', '--belt', str(self.manifest)], {}, FakeRun())
        self.assertEqual(code, smoke.BAD_CONFIG)
        self.assertIn('no pinned npm package', err)

    def test_real_belt_pins_the_inspector(self):
        belt = json.loads((ROOT / 'belt.json').read_text())
        self.assertRegex(smoke.inspector_spec(belt), r'^@modelcontextprotocol/inspector@\d+\.\d+\.\d+$')


if __name__ == '__main__':
    unittest.main()
