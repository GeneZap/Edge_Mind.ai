"""Module 1: plan work; real agentic planning comes in a later stage."""
from ..state import EdgeState


def plan(state: EdgeState) -> dict:
    query = state['query'].strip()
    if not query:
        raise ValueError('The task cannot be empty.')
    steps = ['retrieve_relevant_evidence', 'generate_answer', 'verify_output']
    return {
        'plan': steps,
        'trace': ['PLANNER: created a fixed, testable 3-step plan (no LLM used)'],
    }
