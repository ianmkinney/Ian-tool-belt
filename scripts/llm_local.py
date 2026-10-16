"""Build an llm openai endpoint command for the belt's local-ai preset.

Reads LOCAL_AI_BASE_URL, LOCAL_AI_MODEL and LOCAL_AI_API_KEY, falling back to
the selected preset in belt.json (ollama by default). Does not contact the
model, install llm, or print API keys. CI does not run this script.
"""
import argparse
import os
import shlex
import shutil
import sys
from pathlib import Path

from local_ai_check import resolve
from validate import validate

ROOT = Path(__file__).resolve().parents[1]


def command(settings, extra):
    """argv for `llm openai endpoint`, including --key only when a key is set."""
    if not settings['model']:
        raise ValueError(
            f"Preset {settings['preset']!r} has no model. "
            'Set LOCAL_AI_MODEL or the preset model before prompting.')
    argv = ['llm', 'openai', 'endpoint', settings['baseUrl'], '-m', settings['model']]
    if settings['apiKey']:
        argv.extend(['--key', settings['apiKey']])
    return [*argv, *extra]


def redact(argv):
    """Copy argv with every --key value replaced. The real key is never printed."""
    shown = []
    hide = False
    for part in argv:
        if hide:
            shown.append('$LOCAL_AI_API_KEY')
            hide = False
            continue
        shown.append(part)
        if part == '--key':
            hide = True
    return shown


def main(argv=None, environ=None, runner=os.execvp, which=shutil.which):
    environ = os.environ if environ is None else environ
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--belt', default=str(ROOT / 'belt.json'))
    parser.add_argument('--preset', help='ollama (default), lm-studio, llama-cpp, vllm, ...')
    parser.add_argument('--print', action='store_true', dest='show',
                        help='print the llm command and exit; API keys are redacted')
    args, extra = parser.parse_known_args(argv)
    if extra[:1] == ['--']:
        extra = extra[1:]
    try:
        settings = resolve(validate(args.belt), args.preset, environ)
        argv_out = command(settings, extra)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'Configuration error: {error}', file=sys.stderr)
        return 3
    if args.show:
        print(shlex.join(redact(argv_out)))
        return 0
    if which('llm') is None:
        print('llm is not on PATH. Install the pinned package; see docs/llm.md. No prompt was sent.',
              file=sys.stderr)
        return 1
    try:
        runner(argv_out[0], argv_out)
    except OSError as error:
        print(f'Could not start llm: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
