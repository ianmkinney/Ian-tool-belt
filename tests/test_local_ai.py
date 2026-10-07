import contextlib
import io
import json
import socket
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from belt_fixture import ROOT, load_script

check = load_script('local_ai_check')
BELT = str(ROOT / 'belt.json')


class FakeRuntime(BaseHTTPRequestHandler):
    """A minimal OpenAI-compatible endpoint standing in for Ollama; no real model needed."""
    models = ['gemma4:e2b', 'qwen3.5:latest']
    seen_auth = []

    def log_message(self, *args):
        pass

    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        FakeRuntime.seen_auth.append(self.headers.get('Authorization'))
        if self.path == '/v1/models':
            self.reply(200, {'object': 'list', 'data': [{'id': m, 'object': 'model'} for m in self.models]})
        else:
            self.reply(404, {'error': 'not found'})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if self.path == '/v1/chat/completions' and body['model'] in self.models:
            self.reply(200, {'choices': [{'message': {'role': 'assistant', 'content': ' ready\n'}}]})
        else:
            self.reply(400, {'error': 'bad request'})


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class LocalAiCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), FakeRuntime)
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/v1'
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def run_check(self, *args, **env):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = check.main(['--belt', BELT, '--timeout', '2', *args], environ=env)
        return code, out.getvalue(), err.getvalue()

    def test_defaults_to_the_ollama_preset(self):
        settings = check.resolve(check.validate(BELT), environ={})
        self.assertEqual(settings, {'preset': 'ollama', 'baseUrl': 'http://localhost:11434/v1',
                                    'model': 'gemma4:e2b', 'apiKey': ''})

    def test_alternative_presets_and_env_overrides(self):
        belt = check.validate(BELT)
        self.assertEqual(check.resolve(belt, 'lm-studio', {})['baseUrl'], 'http://localhost:1234/v1')
        settings = check.resolve(belt, 'ollama', {'LOCAL_AI_BASE_URL': self.url + '/', 'LOCAL_AI_MODEL': 'x'})
        self.assertEqual((settings['baseUrl'], settings['model']), (self.url, 'x'))
        with self.assertRaises(ValueError):
            check.resolve(belt, 'missing', {})

    def test_reachable_endpoint_lists_models(self):
        code, out, _ = self.run_check('--json', LOCAL_AI_BASE_URL=self.url)
        self.assertEqual(code, check.OK)
        result = json.loads(out)
        self.assertTrue(result['reachable'])
        self.assertEqual(result['models'], ['gemma4:e2b', 'qwen3.5:latest'])

    def test_latest_tag_matches_untagged_model_name(self):
        code, _, _ = self.run_check(LOCAL_AI_BASE_URL=self.url, LOCAL_AI_MODEL='qwen3.5')
        self.assertEqual(code, check.OK)

    def test_missing_model_has_its_own_exit_code(self):
        code, out, _ = self.run_check(LOCAL_AI_BASE_URL=self.url, LOCAL_AI_MODEL='llama-missing')
        self.assertEqual(code, check.MODEL_MISSING)
        self.assertIn("'llama-missing' is not available", out)

    def test_chat_round_trip(self):
        code, out, _ = self.run_check('--chat', '--json', LOCAL_AI_BASE_URL=self.url)
        self.assertEqual(code, check.OK)
        self.assertEqual(json.loads(out)['chatReply'], 'ready')

    def test_api_key_is_sent_but_never_printed(self):
        FakeRuntime.seen_auth.clear()
        code, out, err = self.run_check('--json', LOCAL_AI_BASE_URL=self.url, LOCAL_AI_API_KEY='KEY_SENTINEL')
        self.assertEqual(code, check.OK)
        self.assertEqual(FakeRuntime.seen_auth, ['Bearer KEY_SENTINEL'])
        self.assertNotIn('KEY_SENTINEL', out + err)

    def test_unreachable_endpoint_fails_cleanly(self):
        url = f'http://127.0.0.1:{free_port()}/v1'
        code, out, _ = self.run_check(LOCAL_AI_BASE_URL=url)
        self.assertEqual(code, check.UNREACHABLE)
        self.assertIn('Cannot reach', out)

    def test_http_error_is_reported(self):
        code, out, _ = self.run_check(LOCAL_AI_BASE_URL=self.url + '/wrong')
        self.assertEqual(code, check.UNREACHABLE)
        self.assertIn('HTTP 404', out)

    def test_remote_plain_http_is_refused_before_any_request(self):
        code, _, err = self.run_check(LOCAL_AI_BASE_URL='http://192.168.1.20:11434/v1', LOCAL_AI_API_KEY='k')
        self.assertEqual(code, check.BAD_CONFIG)
        self.assertIn('Configuration error', err)


if __name__ == '__main__':
    unittest.main()
