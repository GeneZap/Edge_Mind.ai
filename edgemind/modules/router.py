"""Deterministic policy-enforced routing, with explicit cloud preference."""
from ..contracts import ModelCapability, ModelDecision
from ..state import EdgeState


def choose_model(privacy_mode: str, network: str, complexity: str,
                 registry: list[ModelCapability], prefer_cloud: bool = False) -> ModelDecision:
    if privacy_mode not in {'local_only', 'cloud_allowed'}:
        raise ValueError('Invalid privacy mode')
    if network not in {'online', 'offline'}:
        raise ValueError('Invalid network status')
    if complexity not in {'simple', 'complex'}:
        raise ValueError('Invalid complexity')
    candidates = [
        m for m in registry if m['available'] and complexity in m['complexities']
        and (privacy_mode == 'cloud_allowed' or m['provider'] == 'local')
        and (network == 'online' or m['provider'] == 'local')
    ]
    preference = ('cloud' if prefer_cloud and privacy_mode == 'cloud_allowed' and network == 'online'
                  else 'cloud' if complexity == 'complex' and privacy_mode == 'cloud_allowed'
                  else 'local')
    candidates.sort(key=lambda m: (m['provider'] != preference, m['provider'] != 'local'))
    if not candidates:
        return {'outcome': 'deferred', 'model_id': None, 'provider': None,
                'device': None,
                'reason': 'No permitted available model supports this task; it will not be silently uploaded.'}
    chosen = candidates[0]
    return {'outcome': 'selected', 'model_id': chosen['model_id'],
            'provider': chosen['provider'], 'device': chosen['device'],
            'reason': 'Selected from available capabilities after privacy, network, and task checks.'}


def route_model(state: EdgeState) -> dict:
    result = choose_model(state['privacy_mode'], state['network'], state['complexity'],
                          state['available_models'], state.get('prefer_cloud', False))
    label = f"{result['model_id']} ({result['device']})" if result['outcome'] == 'selected' else 'DEFERRED'
    return {'decision': result, 'trace': [f'ROUTER: {label} — {result["reason"]}']}
