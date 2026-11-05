"""Check execution status without misrepresenting mock output."""
from ..state import EdgeState


def verify(state: EdgeState) -> dict:
    result = state['tool_result']
    if result['status'] == 'failed':
        report = {'status': 'FAILED', 'explanation': result['error'] or 'Tool failed'}
    elif result['status'] == 'not_run':
        report = {'status': 'BLOCKED', 'explanation': 'No valid execution path available'}
    elif result['status'] == 'completed':
        report = {'status': 'COMPLETED', 'explanation': 'Model returned a non-empty response; factual accuracy not independently established.'}
    else:
        report = {
            'status': 'SIMULATED',
            'explanation': 'Workflow completed structurally. Output is mocked, not a real verified AI answer.',
        }
    return {'verification': report, 'status': report['status'],
            'trace': [f'VERIFIER: {report["status"]} — {report["explanation"]}']}
