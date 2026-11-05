"""Full HTTP smoke test against a fake Ollama server, no paid credentials needed."""
import json
import os
import socket
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from edgemind.api import serve


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class FakeOllamaHandler(BaseHTTPRequestHandler):
    calls = []
    def log_message(self, *args):
        pass
    def do_GET(self):
        if self.path == '/api/tags':
            self.respond({'models': [{'name': 'qwen-demo:latest'}, {'name': 'nomic-embed-text:latest'}]})
        else:
            self.send_error(404)
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
        self.calls.append((self.path, payload))
        if self.path == '/api/embed':
            self.respond({'embeddings': [[1.0, 0.0, 0.0]]})
        elif self.path == '/api/chat':
            self.respond({'message': {'role': 'assistant', 'content': 'Local demo answer'}})
        else:
            self.send_error(404)
    def respond(self, payload):
        raw = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class TestHttpEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.ollama_port = free_port()
        cls.api_port = free_port()
        cls.ollama = ThreadingHTTPServer(('127.0.0.1', cls.ollama_port), FakeOllamaHandler)
        threading.Thread(target=cls.ollama.serve_forever, daemon=True).start()
        cls.env = patch.dict(os.environ, {
            'EDGEMIND_API_TOKEN': 'test-secret-token',
            'EDGEMIND_API_PORT': str(cls.api_port),
            'EDGEMIND_INDEX_DB': str(Path(cls.temp.name) / 'test.sqlite3'),
            'OLLAMA_HOST': f'http://127.0.0.1:{cls.ollama_port}',
            'EDGEMIND_EMBED_MODEL': 'nomic-embed-text:latest',
        })
        cls.env.start()
        threading.Thread(target=serve, daemon=True).start()
        for _ in range(100):
            try:
                cls.call('/health')
                break
            except OSError:
                time.sleep(0.05)
        else:
            raise AssertionError('API did not start')

    @classmethod
    def tearDownClass(cls):
        cls.ollama.shutdown()
        cls.ollama.server_close()
        cls.env.stop()
        cls.temp.cleanup()

    @classmethod
    def call(cls, path, payload=None, token='test-secret-token'):
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(f'http://127.0.0.1:{cls.api_port}{path}',
                          data=body, headers={'X-EdgeMind-Token': token,
                                              'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_authenticated_retrieval_and_inference(self):
        code, health = self.call('/health')
        self.assertEqual(code, 200)
        self.assertIn('qwen-demo:latest', health['local_models'])
        self.assertFalse(health['cloud_configured'])
        code, result = self.call('/index', {
            'workspace': 'file:///example', 'path': 'invoice.py',
            'content': 'def calculate_invoice(total): return total * 2'})
        self.assertEqual(code, 200)
        self.assertGreater(result['indexed'], 0)
        code, response = self.call('/chat', {
            'workspace': 'file:///example', 'query': 'Explain calculate_invoice',
            'allow_cloud': False})
        self.assertEqual(code, 200)
        self.assertEqual(response['status'], 'COMPLETED')
        self.assertEqual(response['provider'], 'local')
        self.assertEqual(response['model'], 'qwen-demo:latest')
        self.assertEqual(response['content'], 'Local demo answer')
        self.assertIn('invoice.py#chunk-0', response['sources'])
        self.assertTrue(any(route == '/api/chat' for route, _ in FakeOllamaHandler.calls))

    def test_unauthorized_request_rejected(self):
        code, result = self.call('/health', token='bad-token')
        self.assertEqual(code, 401)
        self.assertEqual(result['error'], 'Unauthorized')


if __name__ == '__main__':
    unittest.main()
