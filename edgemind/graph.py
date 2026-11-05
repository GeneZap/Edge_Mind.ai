"""The LangGraph runtime connects six independent module functions."""
from langgraph.graph import StateGraph, START, END
from .state import EdgeState
from .modules.planner import plan
from .modules.rag import retrieve
from .modules.router import route_model
from .modules.coordinator import run_tools
from .modules.verifier import verify
from .modules.recovery import recover


def next_after_verification(state: EdgeState) -> str:
    return 'recovery' if state['verification']['status'] in {'FAILED', 'BLOCKED'} else 'done'


def next_after_recovery(state: EdgeState) -> str:
    return 'tools' if state['recovery_action'] == 'retry' else 'done'


def make_graph():
    builder = StateGraph(EdgeState)
    builder.add_node('planner', plan)
    builder.add_node('rag', retrieve)
    builder.add_node('router', route_model)
    builder.add_node('tools', run_tools)
    builder.add_node('verifier', verify)
    builder.add_node('recovery', recover)

    builder.add_edge(START, 'planner')
    builder.add_edge('planner', 'rag')
    builder.add_edge('rag', 'router')
    builder.add_edge('router', 'tools')
    builder.add_edge('tools', 'verifier')
    builder.add_conditional_edges('verifier', next_after_verification,
                                  {'recovery': 'recovery', 'done': END})
    builder.add_conditional_edges('recovery', next_after_recovery,
                                  {'tools': 'tools', 'done': END})
    return builder.compile()
