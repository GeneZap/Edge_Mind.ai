# EdgeMind — Layer 2 Starter (Learning Milestone 1)

A **terminal-first LangGraph skeleton** for the Intelligence & Orchestration layer.
It has **six independently testable modules** (planner, RAG, router, tool coordinator,
verifier, recovery), shared state, and clear interfaces for teammates.

> **Critical:** This starter uses **mock capabilities and mock model outputs**.
> It does **not** run your Qwen LLM, use the NPU, or call Meta cloud models yet.
> Its purpose is to prove the Layer 2 control flow and collaboration interfaces.

## Windows PowerShell quick start

You can use your existing EdgeMind environment, or make a new environment.
From this directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py --query "Explain the privacy policy" --demo-docs
```

If Python 3.11 isn't installed, use another compatible Python version such as 3.13.
If PowerShell blocks activation, run `\.venv\Scripts\python.exe` instead of `python`
for the commands below; no execution-policy changes are required.

### Try meaningful scenarios

```powershell
# Rule-based privacy routing: never upload private text to the cloud
python main.py --query "Summarize my report" --privacy local_only --complexity simple

# An explicitly cloud-permitted complex request selects the MOCK cloud provider
python main.py --query "Analyze contradictions" --privacy cloud_allowed --complexity complex

# Cannot complete complex work offline with the small mock local model
python main.py --query "Analyze contradictions" --privacy cloud_allowed --network offline --complexity complex

# Demonstrate recovery after one simulated transient timeout
python main.py --query "Summarize my report" --simulate-failure

# Inspect complete shared state and contracts
python main.py --query "What is GPU inference?" --demo-docs --json
```

### Run tests

```powershell
python -m unittest discover -s tests -v
```

## Three-layer boundary

- **Layer 1:** `main.py` / `edgemind/cli.py`; the future FastAPI interface calls `edgemind.service.run_task(...)`.
- **Layer 2:** `edgemind/graph.py`, `state.py`, `contracts.py`, and six independent modules.
- **Layer 3:** Real local GPU/NPU/cloud inference; represented here by the *mock* capability registry
  and *mock* responses. A teammate can implement the real adapter later.

## Workflow

`START → planner → rag → router → tools → verifier → END`

On an unavailable model or a simulated failure, `verifier → recovery`:
- one retry for a simulated transient failure; or
- defer the task without silently violating the privacy policy.

## Development order

1. **Today:** Verify the graph + contracts + terminal + tests using mocks.
2. **Next:** Implement a real Layer 3 adapter and exercise the Router against actual capabilities.
3. Implement hybrid RAG and compare it against the keyword-only mock.
4. Replace fixed planning with validated structured planning.
5. Improve tool execution and verification.
6. Add persisted checkpoints and richer recovery policies.

**Don't modify all six at once.** Each module has a narrow callable interface; develop and test one at a time.

## Files

```text
main.py                    Terminal entry point (Layer 1 adapter)
edgemind/contracts.py      Inter-team data contracts / mocked model registry
edgemind/service.py        Stable API for the Layer 1 teammate
edgemind/state.py          LangGraph shared state
edgemind/graph.py          Wires all six components together
edgemind/modules/planner.py
edgemind/modules/rag.py
edgemind/modules/router.py
edgemind/modules/coordinator.py
edgemind/modules/verifier.py
edgemind/modules/recovery.py
tests/                     Unit tests and workflow tests
```

## Safety and correctness boundaries

- This is not yet a full agent; the planner is fixed and RAG is keyword-only.
- Status **SIMULATED** does not mean an AI has actually answered correctly.
- The privacy rule is enforced by code in the Router, not by trusting LLM text.
- All tool outputs are synthetic. No real external systems are called.
- When integrating Layer 3, maintain the same privacy guarantee and obtain
  explicit authorization before cloud processing or non-read-only tool actions.

For team integration details, see **TEAM_HANDOFF.md**.
