"""Extend Phase 4 state without altering the existing workflow."""

from typing import NotRequired

from app.agent.state import SalesAgentState
from app.multi_agent.contracts import RouteName, WorkerName


class MultiAgentState(SalesAgentState):
    next_agent: NotRequired[RouteName]
    completed_agents: NotRequired[list[WorkerName]]

    supervisor_turns: NotRequired[int]
    supervisor_max_turns: NotRequired[int]
    supervisor_error: NotRequired[str | None]

    research_output: NotRequired[dict]
    knowledge_output: NotRequired[dict]
    analysis_output: NotRequired[dict]
    sales_output: NotRequired[dict]
    crm_output: NotRequired[dict]