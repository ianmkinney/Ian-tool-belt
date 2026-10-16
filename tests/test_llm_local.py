"""The llm helper builds a command for the local-ai preset and never prints a key."""
import contextlib
import io
import unittest

from belt_fixture import ROOT, load_script

llm_local = load_script('llm_local')
check = load_script('local_ai_check')
BELT = str(ROOT / 'belt.json')
SECRET = 'super-secret-value'


def run(argv, environ, runner=None, which=None):
    out, err = io.StringIO(), io.StringIO()
    kwargs = {'environ': environ}
    if runner is not None:
        kwargs['runner'] = runner
    if which is not None:
        kwargs['which'] = which
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = llm_local.main(['--belt', BELT, *argv], **kwargs)
    return code, out.getvalue(), err.getvalue()


class LlmLocalTests(unittest.TestCase):
    def test_defaults_to_the_ollama_preset(self):
        settings = check.resolve(check.validate(BELT), environ={})
        argv = llm_local.command(settings, ['Reply with ready'])
        self.assertEqual(argv, [
            'llm', 'openai', 'endpoint', 'http://localhost:11434/v1', '-m', 'gemma4:e2b',
            'Reply with ready'])
        self.assertNotIn('--key', argv)

    def test_env_and_preset_override_the_endpoint(self):
        belt = check.validate(BELT)
        settings = check.resolve(belt, None, {
            'LOCAL_AI_BASE_URL': 'http://127.0.0.1:9/v1/',
            'LOCAL_AI_MODEL': 'demo',
            'LOCAL_AI_API_KEY': SECRET,
        })
        argv = llm_local.command(settings, ['-s', 'Summarize this file'])
        self.assertEqual(argv[:6], [
            'llm', 'openai', 'endpoint', 'http://127.0.0.1:9/v1', '-m', 'demo'])
        self.assertEqual(argv[6:8], ['--key', SECRET])
        self.assertEqual(argv[8:], ['-s', 'Summarize this file'])
        studio = check.resolve(belt, 'lm-studio', {'LOCAL_AI_MODEL': 'local-model'})
        self.assertEqual(llm_local.command(studio, [])[3], 'http://localhost:1234/v1')

    def test_empty_preset_model_is_a_configuration_error(self):
        settings = check.resolve(check.validate(BELT), 'llama-cpp', {})
        with self.assertRaises(ValueError):
            llm_local.command(settings, ['hello'])
        code, out, err = run(['--preset', 'llama-cpp', '--print', 'hello'], {})
        self.assertEqual(code, 3)
        self.assertEqual(out, '')
        self.assertIn('no model', err)
        self.assertNotIn(SECRET, err)

    def test_print_redacts_the_api_key_and_does_not_run_llm(self):
        def fail(*_args, **_kwargs):
            raise AssertionError('llm should not start')

        code, out, err = run(
            ['--print', '-s', 'Summarize this diff'],
            {'LOCAL_AI_API_KEY': SECRET},
            runner=fail, which=fail)
        self.assertEqual(code, 0)
        self.assertEqual(err, '')
        self.assertIn('http://localhost:11434/v1', out)
        self.assertIn('gemma4:e2b', out)
        self.assertIn('-s', out)
        self.assertIn('$LOCAL_AI_API_KEY', out)
        self.assertNotIn(SECRET, out)
        self.assertNotIn(SECRET, err)

    def test_missing_llm_does_not_print_the_key(self):
        code, out, err = run(
            ['Say hello'],
            {'LOCAL_AI_API_KEY': SECRET},
            which=lambda _name: None,
            runner=lambda *_args: self.fail('runner called'))
        self.assertEqual(code, 1)
        self.assertEqual(out, '')
        self.assertIn('not on PATH', err)
        self.assertNotIn(SECRET, err)

    def test_exec_passes_the_key_without_printing_it(self):
        seen = {}

        def runner(cmd, argv):
            seen['cmd'] = cmd
            seen['argv'] = argv

        code, out, err = run(
            ['Say hello'],
            {'LOCAL_AI_API_KEY': SECRET, 'LOCAL_AI_MODEL': 'demo'},
            runner=runner, which=lambda name: '/usr/bin/llm' if name == 'llm' else None)
        self.assertEqual(code, 0)
        self.assertEqual(out, '')
        self.assertEqual(err, '')
        self.assertEqual(seen['cmd'], 'llm')
        argv = seen['argv']
        self.assertEqual(argv[argv.index('--key') + 1], SECRET)
        self.assertEqual(argv[-1], 'Say hello')
        self.assertEqual(argv[argv.index('-m') + 1], 'demo')

    def test_unknown_preset_fails_before_llm(self):
        code, out, err = run(['--preset', 'missing', 'hello'], {})
        self.assertEqual(code, 3)
        self.assertEqual(out, '')
        self.assertIn('Unknown preset', err)


if __name__ == '__main__':
    unittest.main()
