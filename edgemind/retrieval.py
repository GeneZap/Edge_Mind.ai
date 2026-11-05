"""Private, per-workspace SQLite retrieval. Uses Ollama embeddings when available,
and a deterministic lexical fallback when the embedding model is absent.
No source code is sent to a cloud embedding provider.
"""
import hashlib
import json
import math
import os
import re
import sqlite3
from pathlib import Path
from urllib.request import Request, urlopen

EXTENSIONS = {'.py','.js','.jsx','.ts','.tsx','.json','.md','.html','.css','.scss','.java','.go','.rs','.c','.cpp','.h','.hpp','.yml','.yaml','.toml','.sql','.sh','.ps1'}
MAX_FILE_BYTES = 256_000
MAX_CHUNKS_PER_FILE = 60


def workspace_key(workspace: str) -> str:
    return hashlib.sha256(workspace.encode('utf-8')).hexdigest()[:24]


def tokenize(text: str) -> set[str]:
    return set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*|[0-9]+', text.lower()))


def chunks(text: str, size: int = 1400, overlap: int = 200):
    for start in range(0, len(text), size - overlap):
        yield text[start:start + size]
        if start + size >= len(text):
            break


def embeddings(text: str, host: str, model: str):
    body = json.dumps({'model': model, 'input': text}).encode()
    req = Request(host.rstrip('/') + '/api/embed', data=body,
                  headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=3) as response:
            value = json.load(response).get('embeddings', [])
            return value[0] if value else None
    except (OSError, ValueError, KeyError, IndexError):
        return None


def cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    denominator = math.sqrt(sum(x*x for x in a) * sum(y*y for y in b))
    return sum(x*y for x, y in zip(a, b)) / denominator if denominator else 0.0


class LocalIndex:
    def __init__(self, db_path=None, ollama_host=None, embed_model=None):
        self.path = Path(db_path or os.environ.get('EDGEMIND_INDEX_DB') or
                         Path.home() / '.edgemind' / 'index.sqlite3')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.host = ollama_host or os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
        self.model = embed_model or os.getenv('EDGEMIND_EMBED_MODEL', 'nomic-embed-text')
        with self._connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS chunks (workspace TEXT NOT NULL, path TEXT NOT NULL, ordinal INTEGER NOT NULL, content TEXT NOT NULL, vector TEXT, PRIMARY KEY(workspace,path,ordinal))')
            db.execute('CREATE INDEX IF NOT EXISTS chunks_workspace ON chunks(workspace)')

    def _connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def put(self, workspace: str, path: str, text: str):
        ext = Path(path).suffix.lower()
        if ext not in EXTENSIONS or path.startswith('.') or '/.git/' in '/' + path:
            return 0
        if len(text.encode('utf-8')) > MAX_FILE_BYTES:
            return 0
        entries = []
        for number, part in enumerate(chunks(text)):
            if number >= MAX_CHUNKS_PER_FILE:
                break
            vector = embeddings(part, self.host, self.model)
            entries.append((workspace_key(workspace), path, number, part,
                            json.dumps(vector) if vector is not None else None))
        with self._connect() as db:
            db.execute('DELETE FROM chunks WHERE workspace=? AND path=?',
                       (workspace_key(workspace), path))
            db.executemany('INSERT INTO chunks VALUES (?,?,?,?,?)', entries)
        return len(entries)

    def search(self, workspace: str, query: str, limit=4):
        query_tokens = tokenize(query)
        query_vector = embeddings(query, self.host, self.model)
        with self._connect() as db:
            rows = db.execute('SELECT path,ordinal,content,vector FROM chunks WHERE workspace=?',
                              (workspace_key(workspace),)).fetchall()
        ranked = []
        for path, number, content, stored_vector in rows:
            tokens = tokenize(content)
            lexical = len(query_tokens & tokens) / max(1, len(query_tokens))
            semantic = cosine(query_vector, json.loads(stored_vector)) if query_vector and stored_vector else 0
            score = 0.65 * semantic + 0.35 * lexical if semantic else lexical
            if score > 0:
                ranked.append((score, {'source_id': f'{path}#chunk-{number}', 'text': content}))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in ranked[:limit]]

    def count(self, workspace: str):
        with self._connect() as db:
            return db.execute('SELECT COUNT(*) FROM chunks WHERE workspace=?',
                              (workspace_key(workspace),)).fetchone()[0]
