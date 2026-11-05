"""Bounded retries and one-way cloud-to-local fallback."""
from ..state import EdgeState

MAX_RETRIES = 1


def recover(state: EdgeState) -> dict:
    if (state.get('use_real_models') and state['verification']['status'] == 'FAILED'
            and state['decision'].get('provider') == 'cloud'
            and not state.get('fallback_attempted')):
        local = [m for m in state['available_models'] if m['provider'] == 'local' and m['available']]
        if local:
            selected = local[0]
            decision = {'outcome': 'selected', 'model_id': selected['model_id'],
                        'provider': 'local', 'device': selected['device'],
                        'reason': 'Cloud failed; automatic local fallback'}
            return {'decision': decision, 'fallback_attempted': True,
                    'recovery_action': 'retry',
                    'trace': ['RECOVERY: cloud unavailable; switched to local Ollama']}
    if (not state.get('use_real_models') and state['verification']['status'] == 'FAILED'
            and state.get('attempts', 0) < MAX_RETRIES):
        new_attempts = state.get('attempts', 0) + 1
        return {'attempts': new_attempts, 'recovery_action': 'retry',
                'trace': [f'RECOVERY: retrying tools (attempt {new_attempts}/{MAX_RETRIES})']}
    return {'recovery_action': 'defer', 'status': 'DEFERRED',
            'trace': ['RECOVERY: deferred, no permitted or safe retry available']}
