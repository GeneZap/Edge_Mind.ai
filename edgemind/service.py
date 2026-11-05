"""Stable interface for terminal mocks and live VS Code requests."""
from .contracts import Evidence, ModelCapability, mock_model_registry
from .graph import make_graph
from .state import EdgeState


def run_task(query: str, privacy_mode: str = 'local_only', network: str = 'online',
             complexity: str = 'simple', documents: list[Evidence] | None = None,
             available_models: list[ModelCapability] | None = None,
             simulate_failure: bool = False, use_real_models: bool = False,
             prefer_cloud: bool = False) -> EdgeState:
    if not query.strip():
        raise ValueError('Query cannot be empty')
    if prefer_cloud and privacy_mode != 'cloud_allowed':
        raise ValueError('Cloud preference requires explicit cloud permission')
    initial: EdgeState = {
        'query': query, 'privacy_mode': privacy_mode, 'network': network,
        'complexity': complexity, 'available_models': available_models if available_models is not None else mock_model_registry(),
        'documents': documents if documents is not None else [],
        'simulate_failure': simulate_failure, 'attempts': 0, 'trace': [],
        'use_real_models': use_real_models, 'prefer_cloud': prefer_cloud,
    }
    return make_graph().invoke(initial, config={'recursion_limit': 20})
