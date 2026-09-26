"""Phase 5.1: worker names, order, and planned tool boundaries."""

from typing import Literal

WorkerName = Literal["research", "knowledge", "analysis", "sales", "crm"]
RouteName = Literal["research", "knowledge", "analysis", "sales", "crm", "finish"]

AGENT_SEQUENCE: tuple[WorkerName, ...] = (
    "research", "knowledge", "analysis", "sales", "crm"
)

AGENT_TOOL_PERMISSIONS: dict[WorkerName, frozenset[str]] = {
    "research": frozenset({
        "search_company",
        "get_company_news",
        "get_company_jobs",
    }),
    "knowledge": frozenset({"search_product_knowledge"}),
    "analysis": frozenset(),
    "sales": frozenset(),
    "crm": frozenset({
        "query_leads",
        "create_lead",
        "update_lead_stage",
    }),
}