"""Stable entry point Layer 1 can call without knowing about LangGraph internals.

The current implementation is a MOCK demo. Layer 3 adapters are not connected.
"""
from .contracts import Evidence, ModelCapability, mock_model_registry
from .graph import make_graph
from .state import EdgeState


def run_task(
    query: str,
    privacy_mode: str = 'local_only',
    network: str = 'online',
    complexity: str = 'simple',
    documents: list[Evidence] | None = None,
    available_models: list[ModelCapability] | None = None,
    simulate_failure: bool = False,
) -> EdgeState:
    if not query.strip():
        raise ValueError('Query cannot be empty')
    initial: EdgeState = {
        'query': query,
        'privacy_mode': privacy_mode,
        'network': network,
        'complexity': complexity,
        'available_models': available_models if available_models is not None else mock_model_registry(),
        'documents': documents if documents is not None else [],
        'simulate_failure': simulate_failure,
        'attempts': 0,
        'trace': [],
    }
    return make_graph().invoke(initial, config={'recursion_limit': 20})
