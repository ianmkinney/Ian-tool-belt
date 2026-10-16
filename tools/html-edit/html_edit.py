#!/usr/bin/env python3
"""Serve an HTML file with an in-place editor; save cleaned .edited.html copies."""
import argparse
import json
import re
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
MARKER = 'data-html-edit-injected'
EDITOR_JS = ROOT / 'editor.js'
INJECT_SNIPPET = (
    f'<script {MARKER} src="/__html_edit__/editor.js"></script>\n'
    f'<link rel="stylesheet" {MARKER} href="/__html_edit__/editor.css">\n'
)
EDITOR_CSS = """:root {
  --tb-color-blueprint-navy: #0E3478;
  --tb-color-blueprint-cyan: #78D2FF;
  --tb-color-blueprint-amber: #FFC450;
  --tb-color-blueprint-ink: #FFFFFF;
}
"""


def inject_editor(document: str) -> str:
    if MARKER in document:
        return document
    lower = document.lower()
    idx = lower.rfind('</body>')
    if idx == -1:
        return document + INJECT_SNIPPET
    return document[:idx] + INJECT_SNIPPET + document[idx:]


_STRIP_PATTERNS = [
    (re.compile(rf'<script[^>]*{MARKER}[^>]*>.*?</script>\s*', re.I | re.S), ''),
    (re.compile(rf'<link[^>]*{MARKER}[^>]*>\s*', re.I), ''),
    (re.compile(r'\scontenteditable="(?:true|false)"', re.I), ''),
    (re.compile(r'\sclass="[^"]*\bhtml-edit-active\b[^"]*"', re.I), ''),
    (re.compile(r'\sclass="html-edit-active"', re.I), ''),
    (re.compile(r'\sdata-html-edit-[a-z-]+="[^"]*"', re.I), ''),
]


def strip_editor(document: str) -> str:
    out = document
    for pattern, repl in _STRIP_PATTERNS:
        out = pattern.sub(repl, out)
    out = re.sub(r'\sclass=""', '', out)
    return out


def default_out_path(source: Path, out_arg: Path | None, in_place: bool) -> Path:
    if in_place:
        return source
    if out_arg:
        return out_arg
    return source.with_name(f'{source.stem}.edited{source.suffix}')


class EditorHandler(BaseHTTPRequestHandler):
    served_file: Path = Path('.')
    out_path: Path = Path('.')
    in_place: bool = False
    writable_dir: Path = Path('.')

    def log_message(self, fmt, *args):
        sys.stderr.write(f'{self.address_string()} - {fmt % args}\n')

    def _send(self, code, body: bytes, content_type='text/html; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/__html_edit__/editor.js':
            return self._send(200, EDITOR_JS.read_bytes(), 'application/javascript; charset=utf-8')
        if path == '/__html_edit__/editor.css':
            return self._send(200, EDITOR_CSS.encode(), 'text/css; charset=utf-8')
        if path in ('/', '/index.html'):
            raw = self.served_file.read_text(encoding='utf-8')
            return self._send(200, inject_editor(raw).encode('utf-8'))
        self.send_error(404)

    def do_POST(self):
        if urlparse(self.path).path != '/save':
            return self.send_error(404)
        length = int(self.headers.get('Content-Length', 0))
        payload = json.loads(self.rfile.read(length).decode('utf-8'))
        cleaned = strip_editor(payload.get('html', ''))
        target = self.out_path.resolve()
        if not target.is_relative_to(self.writable_dir.resolve()):
            return self._send(403, b'forbidden')
        target.write_text(cleaned, encoding='utf-8')
        return self._send(200, json.dumps({'path': str(target)}).encode(), 'application/json')

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def serve(file: Path, port: int, out_path: Path, in_place: bool, open_browser: bool):
    writable = file.parent.resolve()
    out_path = out_path.resolve()
    if not out_path.is_relative_to(writable):
        raise ValueError('Output path must stay inside the source file directory')
    handler = EditorHandler
    handler.served_file = file.resolve()
    handler.out_path = out_path
    handler.in_place = in_place
    handler.writable_dir = writable
    server = ThreadingHTTPServer(('127.0.0.1', port), handler)
    url = f'http://127.0.0.1:{port}/'
    print(f'Serving {file} at {url}')
    print(f'Saves to {out_path}' + (' (in-place)' if in_place else ''))
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('html', type=Path, help='HTML file to edit')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--out', type=Path, help='output path for saves')
    parser.add_argument('--in-place', action='store_true', help='overwrite the source file on save')
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args(argv)
    file = args.html.resolve()
    if not file.is_file():
        parser.error(f'Not a file: {file}')
    out = default_out_path(file, args.out, args.in_place)
    serve(file, args.port, out, args.in_place, not args.no_browser)
    return 0


if __name__ == '__main__':
    sys.exit(main())
