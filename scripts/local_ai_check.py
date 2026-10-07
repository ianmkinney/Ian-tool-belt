"""Check that the local OpenAI-compatible model endpoint is reachable and list its models.

Settings come from the belt's model preset (Ollama by default), overridden by
LOCAL_AI_BASE_URL, LOCAL_AI_MODEL and LOCAL_AI_API_KEY. Exit codes:
0 reachable (and model present), 1 unreachable or HTTP error, 2 model missing, 3 bad configuration.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from validate import clean_url, validate

ROOT = Path(__file__).resolve().parents[1]
OK, UNREACHABLE, MODEL_MISSING, BAD_CONFIG = 0, 1, 2, 3


def resolve(belt, preset_name=None, environ=os.environ):
    models = belt.get('models', [])
    if not models:
        raise ValueError('This belt declares no local model')
    model = models[0]
    preset_name = preset_name or model['defaultPreset']
    if preset_name not in model['presets']:
        raise ValueError(f'Unknown preset: {preset_name}')
    preset = model['presets'][preset_name]
    env = model['env']
    settings = {'preset': preset_name,
                'baseUrl': (environ.get(env['baseUrl']) or preset['baseUrl']).rstrip('/'),
                'model': environ.get(env['model']) or preset['model'],
                'apiKey': environ.get(env['apiKey']) or ''}
    clean_url(settings['baseUrl'], allow_http_loopback=True)
    return settings


def request_json(settings, path, payload=None, timeout=5):
    headers = {'Accept': 'application/json'}
    if settings['apiKey']:
        headers['Authorization'] = f"Bearer {settings['apiKey']}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers['Content-Type'] = 'application/json'
    with urlopen(Request(settings['baseUrl'] + path, data=data, headers=headers), timeout=timeout) as response:
        return json.load(response)


def model_listed(wanted, available):
    """Ollama lists `gemma4` as `gemma4:latest`; accept either spelling."""
    return wanted in available or (':' not in wanted and f'{wanted}:latest' in available)


def check(settings, chat=False, timeout=5):
    result = {'preset': settings['preset'], 'baseUrl': settings['baseUrl'], 'model': settings['model'],
              'reachable': False, 'models': []}
    try:
        listing = request_json(settings, '/models', timeout=timeout)
        result['models'] = sorted(m['id'] for m in listing.get('data', []) if isinstance(m, dict) and 'id' in m)
        result['reachable'] = True
    except HTTPError as error:
        result['error'] = f'HTTP {error.code} from {settings["baseUrl"]}/models'
        return result, UNREACHABLE
    except (URLError, OSError, ValueError) as error:
        result['error'] = f'Cannot reach {settings["baseUrl"]}: {getattr(error, "reason", error)}'
        return result, UNREACHABLE
    if settings['model'] and not model_listed(settings['model'], result['models']):
        result['error'] = f"Model {settings['model']!r} is not available; pull or load it first"
        return result, MODEL_MISSING
    if chat:
        if not settings['model']:
            result['error'] = 'Set a model before using --chat'
            return result, BAD_CONFIG
        try:
            reply = request_json(settings, '/chat/completions', {
                'model': settings['model'], 'max_tokens': 16,
                'messages': [{'role': 'user', 'content': 'Reply with the single word: ready'}]}, timeout)
            result['chatReply'] = reply['choices'][0]['message']['content'].strip()
        except (HTTPError, URLError, OSError, ValueError, KeyError, IndexError, TypeError) as error:
            result['error'] = f'Chat request failed: {error}'
            return result, UNREACHABLE
    return result, OK


def main(argv=None, environ=os.environ):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--belt', default=str(ROOT / 'belt.json'))
    parser.add_argument('--preset', help='ollama (default), lm-studio, llama-cpp, vllm, ...')
    parser.add_argument('--chat', action='store_true', help='also send one tiny chat completion')
    parser.add_argument('--timeout', type=float, default=5)
    parser.add_argument('--json', action='store_true', help='print a JSON result')
    args = parser.parse_args(argv)
    try:
        settings = resolve(validate(args.belt), args.preset, environ)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f'Configuration error: {error}', file=sys.stderr)
        return BAD_CONFIG
    result, code = check(settings, args.chat, args.timeout)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Endpoint: {result['baseUrl']} (preset {result['preset']})")
        if result['reachable']:
            print('Models: ' + (', '.join(result['models']) or 'none listed'))
        if 'chatReply' in result:
            print(f"Chat reply: {result['chatReply']}")
        print(result.get('error', 'Local AI is reachable.'))
    return code


if __name__ == '__main__':
    sys.exit(main())
