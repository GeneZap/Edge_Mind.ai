"""Shared contracts between Layers 1, 2, and 3.

All module outputs are plain dictionaries compatible with LangGraph state.
Mock models are declared here temporarily; real capabilities will come from Layer 3.
"""
from typing import Literal, TypedDict

PrivacyMode = Literal["local_only", "cloud_allowed"]
Complexity = Literal["simple", "complex"]


class ModelCapability(TypedDict):
    model_id: str
    provider: Literal["local", "cloud"]
    device: str
    complexities: list[str]
    available: bool


class ModelDecision(TypedDict):
    outcome: Literal["selected", "deferred"]
    model_id: str | None
    provider: str | None
    device: str | None
    reason: str


class Evidence(TypedDict):
    source_id: str
    text: str


class ToolResult(TypedDict):
    status: Literal["simulated", "failed", "not_run"]
    content: str
    error: str | None


class Verification(TypedDict):
    status: Literal["SIMULATED", "FAILED", "BLOCKED"]
    explanation: str


def mock_model_registry() -> list[ModelCapability]:
    """Example capabilities only; this does NOT probe the user's hardware."""
    return [
        {"model_id": "mock-qwen-1.5b", "provider": "local", "device": "GPU",
         "complexities": ["simple"], "available": True},
        {"model_id": "mock-meta-cloud", "provider": "cloud", "device": "CLOUD",
         "complexities": ["simple", "complex"], "available": True},
        {"model_id": "mock-npu-classifier", "provider": "local", "device": "NPU",
         "complexities": [], "available": True},
    ]
