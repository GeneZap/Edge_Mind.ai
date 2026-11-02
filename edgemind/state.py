"""State shared by the six LangGraph modules."""
import operator
from typing import Annotated, TypedDict
from .contracts import Evidence, ModelCapability, ModelDecision, ToolResult, Verification


class EdgeState(TypedDict, total=False):
    query: str
    privacy_mode: str
    network: str
    complexity: str
    available_models: list[ModelCapability]
    documents: list[Evidence]
    simulate_failure: bool

    plan: list[str]
    evidence: list[Evidence]
    decision: ModelDecision
    tool_result: ToolResult
    verification: Verification
    recovery_action: str
    attempts: int
    status: str
    # Reducer adds messages across nodes; each node returns only new messages.
    trace: Annotated[list[str], operator.add]
