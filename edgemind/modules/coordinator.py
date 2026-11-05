"""Execute an actual provider in live mode, retaining mock mode for old tests."""
from ..state import EdgeState


def run_tools(state: EdgeState) -> dict:
    decision = state['decision']
    if decision['outcome'] != 'selected':
        return {
            'tool_result': {'status': 'not_run', 'content': '', 'error': decision['reason']},
            'trace': ['TOOLS: skipped; no permissible model'],
        }
    if not state.get('use_real_models'):
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
    from ..providers import ProviderError, generate
    try:
        response = generate(decision['model_id'], decision['provider'],
                            state['query'], state.get('evidence', []))
        return {'tool_result': {'status': 'completed', 'content': response, 'error': None},
                'trace': [f"TOOLS: executed {decision['provider']} provider"]}
    except ProviderError as exc:
        return {'tool_result': {'status': 'failed', 'content': '', 'error': str(exc)},
                'trace': [f"TOOLS: {decision['provider']} execution failed"]}
