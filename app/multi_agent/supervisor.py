"""Phase 5.1 deterministic supervisor prototype."""

from typing import Any, Mapping

from app.multi_agent.contracts import AGENT_SEQUENCE, RouteName, WorkerName

DEFAULT_MAX_TURNS = 10

VALID_WORKERS = frozenset(AGENT_SEQUENCE)
VALID_ROUTES = VALID_WORKERS | {"finish"}


def _completed(state: Mapping[str, Any]) -> list[WorkerName]:
    items = state.get("completed_agents") or []

    if not isinstance(items, list):
        raise ValueError("completed_agents must be a list")

    unknown = [
        name for name in items
        if name not in VALID_WORKERS
    ]

    if unknown:
        raise ValueError(f"Unknown completed agents: {unknown}")

    return list(dict.fromkeys(items))


def mark_agent_complete(
    state: Mapping[str, Any],
    agent: WorkerName,
) -> dict:
    """Call only after a worker has successfully completed its task."""

    if agent not in VALID_WORKERS:
        raise ValueError(f"Unknown worker: {agent}")

    completed = _completed(state)

    if agent not in completed:
        completed.append(agent)

    return {"completed_agents": completed}


def supervisor_node(state: Mapping[str, Any]) -> dict:
    """Choose the next unfinished worker."""

    turns = state.get("supervisor_turns", 0)
    limit = state.get("supervisor_max_turns", DEFAULT_MAX_TURNS)

    if not isinstance(turns, int) or turns < 0:
        turns = 0

    if not isinstance(limit, int) or limit < 1:
        limit = DEFAULT_MAX_TURNS

    try:
        completed = _completed(state)
    except ValueError as exc:
        return {
            "next_agent": "finish",
            "supervisor_error": str(exc),
            "status": "multi_agent_failed",
        }

    missing = next(
        (
            name for name in AGENT_SEQUENCE
            if name not in completed
        ),
        None,
    )

    if missing is None:
        return {
            "next_agent": "finish",
            "supervisor_error": None,
            "status": "multi_agent_completed",
        }

    if turns >= limit:
        return {
            "next_agent": "finish",
            "supervisor_error": (
                f"Supervisor handoff budget exhausted: "
                f"{turns}/{limit}"
            ),
            "status": "multi_agent_failed",
        }

    return {
        "next_agent": missing,
        "supervisor_turns": turns + 1,
        "supervisor_error": None,
        "status": "multi_agent_routing",
    }


def supervisor_route(state: Mapping[str, Any]) -> RouteName:
    """LangGraph conditional-edge selector."""

    route = state.get("next_agent", "finish")

    return route if route in VALID_ROUTES else "finish"