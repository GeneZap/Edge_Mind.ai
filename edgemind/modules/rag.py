"""Module 2: tiny keyword mock, NOT yet advanced RAG.

Later replace this with embedding search + BM25 + reranking. The interface
remains `retrieve(state) -> {'evidence': [...], 'trace': [...]}`.
"""
import re
from ..state import EdgeState


def retrieve(state: EdgeState) -> dict:
    query_tokens = set(re.findall(r'[a-z0-9]+', state['query'].lower()))
    documents = state.get('documents', [])
    ranked = []
    for doc in documents:
        tokens = set(re.findall(r'[a-z0-9]+', doc['text'].lower()))
        score = len(tokens & query_tokens)
        if score:
            ranked.append((score, doc))
    ranked.sort(key=lambda entry: entry[0], reverse=True)
    evidence = [document for _, document in ranked[:3]]
    return {
        'evidence': evidence,
        'trace': [f'RAG: keyword-only DEMO retrieved {len(evidence)} passages (no embeddings yet)'],
    }
