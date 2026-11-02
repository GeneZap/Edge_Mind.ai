"""Module 4: safe mock tool execution. Never calls real models or external URLs."""
from ..state import EdgeState


def run_tools(state: EdgeState) -> dict:
    decision = state['decision']
    if decision['outcome'] != 'selected':
        return {
            'tool_result': {'status': 'not_run', 'content': '', 'error': decision['reason']},
            'trace': ['TOOLS: skipped; no permissible model'],
        }
    if state.get('simulate_failure', False) and state.get('attempts', 0) == 0:
        return {
            'tool_result': {'status': 'failed', 'content': '', 'error': 'SIMULATED transient timeout'},
            'trace': ['TOOLS: simulated transient timeout (for recovery demonstration)'],
        }
    sources = ', '.join(doc['source_id'] for doc in state.get('evidence', [])) or 'none'
    content = (
        f"[MOCK OUTPUT — NO LLM EXECUTED] Request: {state['query']} | "
        f"Selected: {decision['model_id']} | Retrieved sample sources: {sources}"
    )
    return {
        'tool_result': {'status': 'simulated', 'content': content, 'error': None},
        'trace': ['TOOLS: produced mock output; no real inference or cloud requests'],
    }
