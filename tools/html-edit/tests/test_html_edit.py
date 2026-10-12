import json
import sys
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import html_edit  # noqa: E402

SAMPLE = """<!doctype html>
<html lang="en"><head><title>T</title></head>
<body><p>Hello</p><a href="/x">link</a></body></html>"""


class HtmlEditTests(unittest.TestCase):
    def test_inject_strip_roundtrip(self):
        injected = html_edit.inject_editor(SAMPLE)
        self.assertIn(html_edit.MARKER, injected)
        restored = html_edit.strip_editor(injected)
        self.assertEqual(restored.strip(), SAMPLE.strip())

    def test_save_endpoint_and_path_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'page.html'
            src.write_text(SAMPLE)
            out = Path(tmp) / 'page.edited.html'
            handler = html_edit.EditorHandler
            handler.served_file = src
            handler.out_path = out
            handler.in_place = False
            handler.writable_dir = Path(tmp).resolve()
            port = 18765
            server = html_edit.ThreadingHTTPServer(('127.0.0.1', port), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn = HTTPConnection('127.0.0.1', port, timeout=5)
                conn.request('POST', '/save', json.dumps({'html': SAMPLE}), {'Content-Type': 'application/json'})
                res = conn.getresponse()
                self.assertEqual(res.status, 200)
                self.assertTrue(out.is_file())
                bad = handler
                bad.out_path = Path('/tmp/outside.html')
                server2 = html_edit.ThreadingHTTPServer(('127.0.0.1', port + 1), bad)
                t2 = threading.Thread(target=server2.serve_forever, daemon=True)
                t2.start()
                try:
                    c2 = HTTPConnection('127.0.0.1', port + 1, timeout=5)
                    c2.request('POST', '/save', json.dumps({'html': SAMPLE}), {'Content-Type': 'application/json'})
                    self.assertEqual(c2.getresponse().status, 403)
                finally:
                    server2.shutdown()
            finally:
                server.shutdown()


if __name__ == '__main__':
    unittest.main()
