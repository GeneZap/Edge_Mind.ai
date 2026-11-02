"""Module 5: checks structure; never claims mock data is factual validation."""
from ..state import EdgeState


def verify(state: EdgeState) -> dict:
    result = state['tool_result']
    if result['status'] == 'failed':
        report = {'status': 'FAILED', 'explanation': result['error'] or 'Tool failed'}
    elif result['status'] == 'not_run':
        report = {'status': 'BLOCKED', 'explanation': 'No valid execution path available'}
    else:
        report = {
            'status': 'SIMULATED',
            'explanation': 'Workflow completed structurally. Output is mocked, not a real verified AI answer.',
        }
    return {'verification': report, 'status': report['status'],
            'trace': [f'VERIFIER: {report["status"]} — {report["explanation"]}']}
