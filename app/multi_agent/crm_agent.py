
"""Phase 5.7 - Read-only CRM Agent.

Inputs:
    research_output
    analysis_output
    candidate_leads
    sales_output

Outputs:
    crm_output

Responsibilities:
    - Read existing CRM records through CRM MCP.
    - Match selected candidate companies.
    - Detect missing and duplicate CRM records.
    - Preserve existing CRM stage and next_action.
    - Produce manual review suggestions.

This version NEVER invokes create_lead or update_lead_stage.
"""

import json
import math

from collections.abc import Mapping
from typing import Any

from app.mcp.adapter import load_crm_langchain_tools_sync
from app.models.review_schema import LeadAssessment


READ_TOOL_NAME = "query_leads"


# ============================================================
# 1. CRM MCP result normalization
# ============================================================

def _decode_crm_result(raw: Any) -> list[dict]:

    if isinstance(raw, str):

        try:
            raw = json.loads(raw)

        except json.JSONDecodeError as exc:

            raise ValueError(
                "CRM MCP returned invalid JSON"
            ) from exc

    # MCP adapter may unwrap this itself.
    if (
        isinstance(raw, Mapping)
        and set(raw.keys()) == {"result"}
    ):

        return _decode_crm_result(raw["result"])

    if not isinstance(raw, list):

        raise ValueError(
            "query_leads must return a list"
        )

    records = []

    for item in raw:

        if not isinstance(item, Mapping):

            raise ValueError(
                "CRM query contains a malformed record"
            )

        company = item.get("company")

        if (
            not isinstance(company, str)
            or not company.strip()
        ):

            raise ValueError(
                "CRM record contains an invalid company name"
            )

        records.append(dict(item))

    return records


# ============================================================
# 2. Validate upstream state
# ============================================================

def _prepare_candidates(state: Mapping[str, Any]) -> list[dict]:

    research = state.get("research_output") or {}

    analysis = state.get("analysis_output") or {}

    sales = state.get("sales_output") or {}

    leads = state.get("candidate_leads") or []

    if not isinstance(leads, list):

        raise ValueError(
            "candidate_leads must be a list"
        )

    if analysis.get("status") not in {
        "complete",
        "insufficient_research",
    }:

        raise ValueError(
            "CRM Agent requires completed Analysis output"
        )

    if analysis.get("crm_stage_changed") is not False:

        # For the no-candidate case, Analysis may omit this field.
        if leads or analysis.get("status") != "insufficient_research":

            raise ValueError(
                "Upstream Analysis must not change CRM stage"
            )

    if sales.get("send_performed") is not False:

        raise ValueError(
            "Sales output indicates a message was sent"
        )

    if sales.get("crm_write_performed") is not False:

        raise ValueError(
            "Sales output indicates a CRM write"
        )

    if sales.get("requires_human_review") is not True:

        raise ValueError(
            "Sales output must require human review"
        )

    if not leads:

        if sales.get("status") != "no_candidates":

            raise ValueError(
                "Empty candidates require no_candidates Sales status"
            )

        if sales.get("drafts") != []:

            raise ValueError(
                "Empty candidates must not contain Sales drafts"
            )

        return []

    if analysis.get("status") != "complete":

        raise ValueError(
            "Nonempty candidates require complete Analysis output"
        )

    if sales.get("status") != "complete":

        raise ValueError(
            "Nonempty candidates require complete Sales output"
        )

    research_mode = research.get("data_mode")

    if (
        not isinstance(research_mode, str)
        or not research_mode.strip()
    ):

        raise ValueError(
            "Research data_mode is missing"
        )

    if sales.get("data_mode") != research_mode:

        raise ValueError(
            "Sales and Research data_mode mismatch"
        )

    drafts = sales.get("drafts")

    if not isinstance(drafts, list):

        raise ValueError(
            "Sales drafts must be a list"
        )

    if sales.get("draft_count") != len(drafts):

        raise ValueError(
            "Sales draft_count mismatch"
        )

    if len(drafts) != len(leads):

        raise ValueError(
            "Sales drafts and candidate_leads count mismatch"
        )

    candidate_map = {}

    for lead in leads:

        validated = LeadAssessment.model_validate(
            lead
        ).model_dump()

        company = validated["company"].strip()

        if not company:

            raise ValueError(
                "Candidate company cannot be empty"
            )

        score = validated["purchase_intent_score"]

        if (
            not math.isfinite(score)
            or not 0 <= score <= 1
        ):

            raise ValueError(
                f"Invalid candidate score: {company}"
            )

        if company in candidate_map:

            raise ValueError(
                f"Duplicate candidate company: {company}"
            )

        candidate_map[company] = validated

    draft_map = {}

    for draft in drafts:

        if not isinstance(draft, Mapping):

            raise ValueError(
                "Invalid Sales draft"
            )

        company = draft.get("company")

        if (
            not isinstance(company, str)
            or company in draft_map
        ):

            raise ValueError(
                "Invalid or duplicate Sales draft company"
            )

        if draft.get("send_performed") is not False:

            raise ValueError(
                "An individual Sales draft was sent"
            )

        if draft.get("crm_write_performed") is not False:

            raise ValueError(
                "An individual Sales draft modified CRM"
            )

        if draft.get("requires_human_review") is not True:

            raise ValueError(
                "Sales draft lacks human-review requirement"
            )

        if research_mode == "mock_company_mcp":

            if draft.get("draft_status") != "mock_internal_only":

                raise ValueError(
                    "Mock Sales draft lacks internal-only restriction"
                )

        next_action = draft.get("next_action")

        if (
            not isinstance(next_action, str)
            or not next_action.strip()
        ):

            raise ValueError(
                "Sales draft next_action is empty"
            )

        draft_map[company] = dict(draft)

    if set(candidate_map) != set(draft_map):

        raise ValueError(
            "Sales drafts and Analysis candidates differ"
        )

    prepared = []

    for company, lead in candidate_map.items():

        draft = draft_map[company]

        selected_evidence = draft.get("evidence_refs")

        if (
            not isinstance(selected_evidence, list)
            or not selected_evidence
            or not all(
                isinstance(fact, str)
                and fact in lead["evidence"]
                for fact in selected_evidence
            )
        ):

            raise ValueError(
                f"Sales evidence mismatch: {company}"
            )

        prepared.append({
            "company": company,
            "score": lead["purchase_intent_score"],
            "level": lead["opportunity_level"],
            "evidence": lead["evidence"],
            "proposed_next_action": draft["next_action"].strip(),
            "draft_status": draft["draft_status"],
        })

    return prepared


# ============================================================
# 3. Load only the read-only CRM MCP tool
# ============================================================

def _load_query_tool():

    discovered = load_crm_langchain_tools_sync()

    matching = [
        tool
        for tool in discovered
        if tool.name == READ_TOOL_NAME
    ]

    if len(matching) != 1:

        raise RuntimeError(
            "Expected exactly one query_leads MCP tool"
        )

    return matching[0]


# ============================================================
# 4. Read-only CRM matching
# ============================================================

def run_crm(
    state: Mapping[str, Any],
    *,
    query_tool: Any = None,
) -> dict:

    prepared = _prepare_candidates(state)

    research = state.get("research_output") or {}

    data_mode = research.get(
        "data_mode",
        "unknown",
    )

    # No candidate means there is nothing to query or write.
    if not prepared:

        return {
            "crm_output": {
                "status": "no_candidates",
                "mode": "read_only",
                "data_mode": data_mode,
                "query_count": 0,
                "candidate_count": 0,
                "existing_count": 0,
                "missing_count": 0,
                "duplicate_count": 0,
                "review_records": [],
                "read_performed": False,
                "create_performed": False,
                "update_performed": False,
                "stage_changed": False,
                "requires_human_review": True,
            }
        }

    tool = (
        query_tool
        if query_tool is not None
        else _load_query_tool()
    )

    if getattr(tool, "name", None) != READ_TOOL_NAME:

        raise ValueError(
            "CRM Agent can only invoke query_leads"
        )

    # ========================================================
    # Query the whole CRM table for exact company-name matches.
    #
    # Do not filter by industry or score here:
    # duplicate detection must not miss an existing company
    # merely because its industry or score was stored differently.
    # ========================================================

    try:

        raw_result = tool.invoke({
            "industry": "",
            "min_score": 0.0,
        })

    except Exception as exc:

        raise RuntimeError(
            "CRM MCP read-only query failed"
        ) from exc

    crm_records = _decode_crm_result(
        raw_result
    )

    wanted = {
        item["company"]
        for item in prepared
    }

    matches = {
        company: []
        for company in wanted
    }

    # Do not expose unrelated CRM customers in crm_output.
    for record in crm_records:

        company = record["company"].strip()

        if company in matches:

            matches[company].append(record)

    review_records = []

    existing_count = 0
    missing_count = 0
    duplicate_count = 0

    for candidate in prepared:

        company = candidate["company"]

        found = matches[company]

        base = {
            "company": company,
            "candidate_score": candidate["score"],
            "candidate_level": candidate["level"],
            "proposed_next_action": (
                candidate["proposed_next_action"]
            ),
            "requires_human_review": True,
            "action_taken": "none",
            "crm_write_performed": False,
        }

        # ----------------------------------------------------
        # Not found: propose manual verification, not create.
        # ----------------------------------------------------

        if not found:

            missing_count += 1

            review_records.append({
                **base,
                "lookup_status": "not_found",
                "existing_stage": None,
                "existing_next_action": None,
                "last_contact_time": None,
                "suggested_review": (
                    "人工核实企业真实性、名称和实际需求后，"
                    "再决定是否创建CRM客户。"
                ),
            })

            continue

        # ----------------------------------------------------
        # Multiple rows: never choose one automatically.
        # ----------------------------------------------------

        if len(found) > 1:

            duplicate_count += 1

            review_records.append({
                **base,
                "lookup_status": "duplicate_records",
                "duplicate_record_count": len(found),
                "existing_stage": None,
                "existing_next_action": None,
                "last_contact_time": None,
                "suggested_review": (
                    "CRM存在同名重复记录，"
                    "需要人工检查和去重；禁止自动覆盖。"
                ),
            })

            continue

        # ----------------------------------------------------
        # Exactly one existing record.
        #
        # Preserve the actual stored stage / next_action.
        # Suggested new action is kept in a separate field.
        # ----------------------------------------------------

        existing = found[0]

        existing_count += 1

        review_records.append({
            **base,
            "lookup_status": "existing",
            "existing_stage": existing.get("stage"),
            "existing_next_action": (
                existing.get("next_action")
            ),
            "last_contact_time": (
                existing.get("last_contact_time")
            ),
            "suggested_review": (
                "保留CRM原有阶段和跟进记录；"
                "人工核实新情报后，决定是否采纳建议。"
            ),
        })

    status = (
        "manual_dedup_required"
        if duplicate_count > 0
        else "review_only"
    )

    return {
        "crm_output": {
            "status": status,
            "mode": "read_only",
            "data_mode": data_mode,
            "query_count": 1,
            "candidate_count": len(prepared),
            "existing_count": existing_count,
            "missing_count": missing_count,
            "duplicate_count": duplicate_count,
            "review_records": review_records,
            "read_performed": True,
            "create_performed": False,
            "update_performed": False,
            "stage_changed": False,
            "requires_human_review": True,
            "write_block_reason": (
                "mock_company_data"
                if data_mode == "mock_company_mcp"
                else "no_explicit_write_authorization"
            ),
        }
    }


def crm_agent_node(state: Mapping[str, Any]) -> dict:

    """Entrypoint for the Phase 5 Multi-Agent Graph."""

    return run_crm(state)
