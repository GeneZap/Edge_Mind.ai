"""Module 6: bounded retry for simulated transient failure; otherwise defer."""
from ..state import EdgeState


MAX_RETRIES = 1


def recover(state: EdgeState) -> dict:
    if state['verification']['status'] == 'FAILED' and state.get('attempts', 0) < MAX_RETRIES:
        new_attempts = state.get('attempts', 0) + 1
        return {'attempts': new_attempts, 'recovery_action': 'retry',
                'trace': [f'RECOVERY: retrying tools (attempt {new_attempts}/{MAX_RETRIES})']}
    return {'recovery_action': 'defer', 'status': 'DEFERRED',
            'trace': ['RECOVERY: deferred, no permitted or safe retry available']}
