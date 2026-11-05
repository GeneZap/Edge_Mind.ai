# Integration contracts for your three-person EdgeMind team

## Layer 1 developer — Terminal now, FastAPI/React later

Call the Python function `edgemind.service.run_task(...)`. Example:

```python
from edgemind.service import run_task

result = run_task(
    query='Summarize my project',
    privacy_mode='local_only',
    network='online',
    complexity='simple',
)
print(result['status'])
print(result['trace'])
```

`run_task` currently executes **only simulated** model responses.
Do not label `SIMULATED` as a correct AI answer.

Expected input: `query` string, `privacy_mode` (`local_only` or `cloud_allowed`),
`network` (`online` or `offline`), `complexity` (`simple` or `complex`),
and optional `documents` (list of `{source_id, text}`).

Layer 1 should get meaningful user permission before allowing cloud processing.
Do not put uploaded private documents into logs or publicly reachable services.

## Layer 3 developer — GPU/NPU/Meta inference and retrieval stores

Provide a capability registry compatible with `ModelCapability` from
`edgemind.contracts`:

```python
{
    'model_id': 'qwen-1.5b-openvino',
    'provider': 'local',
    'device': 'GPU',
    'complexities': ['simple'],
    'available': True,
}
```

This is a declared capability, **not a measured guarantee**. Implement the
real inference adapter in a later milestone; maintain a typed response with
`status`, `content`, and `error`. The Layer 2 Tool Coordinator currently returns
mock data and **must be explicitly changed** to call the real adapter.

NPU availability alone does not mean it can run an LLM. Register only
models that were actually compiled and tested on the selected device.

## Layer 2 developer — You

Own `edgemind/graph.py`, `contracts.py`, `state.py`, `service.py`, and
all six `edgemind/modules/*.py` implementations.

Development order: contracts → router → RAG → coordinator → planner →
verification → recovery. Keep tests passing after every change.

## Collaboration rule

Freeze interfaces for the next milestone. If a field changes, update
`contracts.py`, `TEAM_HANDOFF.md`, and relevant tests together.
