"""
Phase 5.2: Multi-Agent LangGraph workflow.

This graph is independent of the Phase 4 workflow.

The actual worker implementations are injected when the graph
is created. A worker must return a state update dictionary and
raise an exception when execution fails.
"""

from collections.abc import Callable, Mapping
from typing import Any

from langgraph.graph import StateGraph, START, END

from app.multi_agent.contracts import AGENT_SEQUENCE
from app.multi_agent.state import MultiAgentState
from app.multi_agent.supervisor import (
    supervisor_node,
    supervisor_route,
    mark_agent_complete,
)


WorkerNode = Callable[
    [MultiAgentState],
    Mapping[str, Any],
]


def _make_worker_node(
    name: str,
    worker_fn: WorkerNode,
):
    """
    Wrap a worker and record completion only after success.

    Workers must not directly modify Supervisor routing fields.
    """

    def worker_node(state: MultiAgentState) -> dict:
        update = worker_fn(state)

        if not isinstance(update, Mapping):
            raise TypeError(
                f"Worker '{name}' must return a mapping"
            )

        reserved_fields = {
            "completed_agents",
            "next_agent",
            "supervisor_turns",
            "supervisor_error",
        }

        conflicts = reserved_fields.intersection(update.keys())

        if conflicts:
            raise ValueError(
                f"Worker '{name}' attempted to modify "
                f"Supervisor-owned fields: {sorted(conflicts)}"
            )

        if update.get("status") in {
            "failed",
            "multi_agent_failed",
        }:
            raise RuntimeError(
                f"Worker '{name}' reported execution failure"
            )

        completion = mark_agent_complete(
            state,
            name,
        )

        return {
            **dict(update),
            **completion,
        }

    return worker_node


def create_multi_graph(
    worker_nodes: Mapping[str, WorkerNode],
):
    """
    Build an independent Supervisor-based Multi-Agent graph.

    All five workers must be explicitly supplied.
    No mock or placeholder workers are installed automatically.
    """

    expected = set(AGENT_SEQUENCE)
    provided = set(worker_nodes.keys())

    missing = expected - provided
    extra = provided - expected

    if missing or extra:
        raise ValueError(
            f"Invalid worker configuration. "
            f"Missing: {sorted(missing)}; "
            f"Unexpected: {sorted(extra)}"
        )

    for name, worker in worker_nodes.items():
        if not callable(worker):
            raise TypeError(
                f"Worker '{name}' must be callable"
            )

    graph = StateGraph(MultiAgentState)

    # Supervisor
    graph.add_node(
        "supervisor",
        supervisor_node,
    )

    # Professional workers
    for name in AGENT_SEQUENCE:
        graph.add_node(
            name,
            _make_worker_node(
                name,
                worker_nodes[name],
            ),
        )

    # Entry
    graph.add_edge(
        START,
        "supervisor",
    )

    # Each worker reports back to Supervisor
    for name in AGENT_SEQUENCE:
        graph.add_edge(
            name,
            "supervisor",
        )

    # Supervisor routing
    routes = {
        name: name
        for name in AGENT_SEQUENCE
    }

    routes["finish"] = END

    graph.add_conditional_edges(
        "supervisor",
        supervisor_route,
        routes,
    )

    return graph.compile()