"""Loopback-only HTTP API for the VS Code extension host. Not a public server."""
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .providers import local_models, model_registry
from .retrieval import LocalIndex
from .service import run_task

MAX_REQUEST = 350_000


def serve(host='127.0.0.1', port=8765, token=None):
    if host not in ('127.0.0.1', 'localhost', '::1'):
        raise ValueError('EdgeMind API must bind to loopback only')
    token = token or os.getenv('EDGEMIND_API_TOKEN') or secrets.token_urlsafe(32)
    index = LocalIndex()

    class Handler(BaseHTTPRequestHandler):
        def respond(self, code, body):
            raw = json.dumps(body).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(raw)

        def authorized(self):
            return secrets.compare_digest(self.headers.get('X-EdgeMind-Token', ''), token)

        def do_GET(self):
            if not self.authorized():
                return self.respond(401, {'error': 'Unauthorized'})
            if self.path == '/health':
                models = local_models()
                return self.respond(200, {'status': 'ok', 'local_models': models,
                                          'cloud_configured': bool(os.getenv('EDGEMIND_CLOUD_API_KEY') and os.getenv('EDGEMIND_CLOUD_MODEL'))})
            self.respond(404, {'error': 'Unknown endpoint'})

        def do_POST(self):
            if not self.authorized():
                return self.respond(401, {'error': 'Unauthorized'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length <= 0 or length > MAX_REQUEST:
                    return self.respond(413, {'error': 'Invalid request size'})
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    return self.respond(400, {'error': 'Expected JSON object'})
                workspace = data.get('workspace', '')
                if not isinstance(workspace, str) or not workspace or len(workspace) > 2048:
                    return self.respond(400, {'error': 'Workspace required'})
                if self.path == '/index':
                    path, content = data.get('path'), data.get('content')
                    if not isinstance(path, str) or not isinstance(content, str) or len(path) > 512:
                        return self.respond(400, {'error': 'Invalid document'})
                    count = index.put(workspace, path, content)
                    return self.respond(200, {'indexed': count, 'total_chunks': index.count(workspace)})
                if self.path == '/chat':
                    query = data.get('query', '')
                    if not isinstance(query, str) or not query.strip() or len(query) > 24000:
                        return self.respond(400, {'error': 'Invalid query'})
                    allowed = data.get('allow_cloud') is True
                    evidence = index.search(workspace, query)
                    # Cloud is only selected if explicitly enabled for this request.
                    result = run_task(query=query, privacy_mode='cloud_allowed' if allowed else 'local_only',
                                      network='online', complexity='simple', documents=evidence,
                                      available_models=model_registry(), use_real_models=True,
                                      prefer_cloud=allowed)
                    return self.respond(200, {'status': result['status'],
                                              'content': result['tool_result']['content'],
                                              'error': result['tool_result'].get('error'),
                                              'provider': result['decision'].get('provider'),
                                              'model': result['decision'].get('model_id'),
                                              'sources': [x['source_id'] for x in result.get('evidence', [])]})
                self.respond(404, {'error': 'Unknown endpoint'})
            except (ValueError, TypeError, KeyError) as exc:
                self.respond(400, {'error': str(exc)})
            except Exception:
                # Do not leak private request content or stack traces to clients.
                self.respond(500, {'error': 'Internal server error'})

        def log_message(self, format, *args):
            return  # Never log prompts or snippets

    server = ThreadingHTTPServer((host, int(os.getenv('EDGEMIND_API_PORT', port))), Handler)
    print('EdgeMind loopback API listening on port', server.server_port, flush=True)
    server.serve_forever()


if __name__ == '__main__':
    serve()
