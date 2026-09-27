
"""Phase 6.6 - Read-only CRM Agent for real company evidence.

Only query_leads can be invoked.

The worker:
- accepts real Research / Analysis / Sales outputs;
- checks original-source evidence consistency;
- detects exact-name existing/missing/duplicate CRM rows;
- treats legacy CRM records as unverified;
- never creates or updates CRM records;
- never treats a matched CRM row as proof of a real customer.

No mock fallback.
No numeric purchase-intent score.
No external message sending.
"""

import hashlib
import json

from collections.abc import Mapping
from typing import Any

from app.mcp.adapter import (
    load_crm_langchain_tools_sync,
)

from app.multi_agent.real_sales_agent import (
    DRAFT_BANNER,
)


DATA_MODE = "real_source_page"
READ_TOOL = "query_leads"


class RealCRMError(ValueError):
    pass


# ============================================================
# 1. Load strictly read-only CRM tool
# ============================================================

def _load_query_tool():

    tools = load_crm_langchain_tools_sync()

    matches = [
        tool
        for tool in tools
        if tool.name == READ_TOOL
    ]

    if len(matches) != 1:

        raise RealCRMError(
            "Expected exactly one query_leads MCP tool"
        )

    # Never return create_lead or update_lead_stage.
    return matches[0]


def _decode_crm_result(raw: Any) -> list[dict]:

    if isinstance(raw, str):

        try:
            raw = json.loads(raw.strip())

        except json.JSONDecodeError as exc:

            raise RealCRMError(
                "CRM MCP returned invalid JSON"
            ) from exc

    if (
        isinstance(raw, Mapping)
        and set(raw) == {"result"}
    ):

        return _decode_crm_result(
            raw["result"]
        )

    if not isinstance(raw, list):

        raise RealCRMError(
            "query_leads must return a list"
        )

    records = []

    for item in raw:

        if not isinstance(item, Mapping):

            raise RealCRMError(
                "Malformed CRM record"
            )

        company = item.get("company")

        if (
            not isinstance(company, str)
            or not company.strip()
        ):

            raise RealCRMError(
                "CRM record has no valid company name"
            )

        records.append(dict(item))

    return records


def _read_crm_rows(query_tool=None):

    tool = (
        query_tool
        if query_tool is not None
        else _load_query_tool()
    )

    if getattr(tool, "name", None) != READ_TOOL:

        raise RealCRMError(
            "Only query_leads is authorized"
        )

    try:

        raw = tool.invoke({
            "industry": "",
            "min_score": 0.0,
        })

    except Exception as exc:

        raise RuntimeError(
            "CRM read-only query failed"
        ) from exc

    return _decode_crm_result(raw)


# ============================================================
# 2. Logical snapshot for integration testing
# ============================================================

def _fingerprint_rows(rows: list[dict]) -> str:

    normalized = sorted(
        json.dumps(
            record,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )
        for record in rows
    )

    payload = json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def capture_crm_snapshot(
    *,
    query_tool=None,
) -> dict:

    """
    Capture the logical result of the existing
    CRM query_leads interface.

    Does not expose unrelated customer records.
    Does not alter CRM.

    This is a logical query-result snapshot,
    not a byte-level SQLite database hash.
    """

    rows = _read_crm_rows(
        query_tool
    )

    return {
        "row_count": len(rows),
        "sha256": _fingerprint_rows(rows),
        "read_only": True,
    }


# ============================================================
# 3. Validate Phase 6 upstream outputs
# ============================================================

def _prepare_review_items(
    state: Mapping[str, Any],
) -> list[dict]:

    research = state.get("research_output")
    analysis = state.get("analysis_output")
    sales = state.get("sales_output")

    if not all(
        isinstance(value, Mapping)
        for value in (
            research,
            analysis,
            sales,
        )
    ):

        raise RealCRMError(
            "Real Research, Analysis and Sales are required"
        )

    for name, output in [
        ("Research", research),
        ("Analysis", analysis),
        ("Sales", sales),
    ]:

        if output.get("data_mode") != DATA_MODE:

            raise RealCRMError(
                f"{name} returned non-real data"
            )

    if research.get("mock_fallback_used") is not False:

        raise RealCRMError(
            "Mock fallback is forbidden"
        )

    if research.get("status") not in {
        "complete",
        "insufficient_evidence",
    }:

        raise RealCRMError(
            "Invalid Research status"
        )

    if analysis.get("status") not in {
        "complete",
        "insufficient_evidence",
    }:

        raise RealCRMError(
            "Invalid Analysis status"
        )

    if sales.get("status") not in {
        "complete",
        "no_verified_assessments",
    }:

        raise RealCRMError(
            "Invalid Sales status"
        )

    if state.get("candidate_leads") != []:

        raise RealCRMError(
            "Legacy scored candidate leads are forbidden"
        )

    for name, output in [
        ("Research", research),
        ("Analysis", analysis),
        ("Sales", sales),
    ]:

        if output.get("crm_write_performed") is not False:

            raise RealCRMError(
                f"{name} indicates a CRM write"
            )

        if output.get("send_performed") is not False:

            raise RealCRMError(
                f"{name} indicates an outbound message"
            )

    if (
        analysis.get("crm_stage_changed") is not False
        or sales.get("crm_stage_changed") is not False
    ):

        raise RealCRMError(
            "Upstream CRM stage was changed"
        )

    if (
        analysis.get("requires_human_review") is not True
        or sales.get("requires_human_review") is not True
    ):

        raise RealCRMError(
            "Upstream human-review requirement is missing"
        )

    original_evidence = research.get(
        "verified_evidence"
    )

    assessments = analysis.get(
        "assessments"
    )

    drafts = sales.get(
        "drafts"
    )

    if not all(
        isinstance(value, list)
        for value in (
            original_evidence,
            assessments,
            drafts,
        )
    ):

        raise RealCRMError(
            "Malformed real upstream records"
        )

    if research.get(
        "verified_evidence_count"
    ) != len(original_evidence):

        raise RealCRMError(
            "Research evidence count mismatch"
        )

    if analysis.get(
        "selected_count"
    ) != len(assessments):

        raise RealCRMError(
            "Analysis assessment count mismatch"
        )

    if sales.get(
        "draft_count"
    ) != len(drafts):

        raise RealCRMError(
            "Sales draft count mismatch"
        )

    if drafts and sales.get("status") != "complete":

        raise RealCRMError(
            "Nonempty drafts require complete Sales output"
        )

    if not drafts and sales.get("status") != (
        "no_verified_assessments"
    ):

        raise RealCRMError(
            "Empty drafts require no_verified_assessments status"
        )

    # --------------------------------------------------------
    # Validate Analysis assessments against Research evidence
    # --------------------------------------------------------

    assessment_map = {}

    for assessment in assessments:

        if not isinstance(assessment, Mapping):

            raise RealCRMError(
                "Malformed Analysis assessment"
            )

        company = assessment.get("company")

        if (
            not isinstance(company, str)
            or not company.strip()
            or company in assessment_map
        ):

            raise RealCRMError(
                "Invalid or duplicate Analysis company"
            )

        if (
            assessment.get("purchase_intent_status")
            != "unverified"
            or assessment.get("budget_status")
            != "unknown"
            or assessment.get("contact_status")
            != "unknown"
        ):

            raise RealCRMError(
                "Unconfirmed purchase facts were promoted"
            )

        if (
            assessment.get("requires_human_review") is not True
            or assessment.get("crm_stage_changed") is not False
            or assessment.get("send_performed") is not False
        ):

            raise RealCRMError(
                "Unsafe Analysis assessment"
            )

        evidence = assessment.get(
            "observed_evidence"
        )

        if (
            not isinstance(evidence, list)
            or not evidence
        ):

            raise RealCRMError(
                "Assessment has no actual evidence"
            )

        for item in evidence:

            if (
                not isinstance(item, Mapping)
                or item not in original_evidence
            ):

                raise RealCRMError(
                    "Assessment evidence is absent from Research"
                )

            if (
                item.get("company") != company
                or item.get("verification_status")
                != "literal_quote_from_article"
                or company not in item.get("quote", "")
            ):

                raise RealCRMError(
                    "Unverified company evidence"
                )

        assessment_map[company] = dict(
            assessment
        )

    # --------------------------------------------------------
    # Validate Sales drafts against Analysis
    # --------------------------------------------------------

    draft_map = {}

    for draft in drafts:

        if not isinstance(draft, Mapping):

            raise RealCRMError(
                "Malformed Sales draft"
            )

        company = draft.get(
            "company"
        )

        if (
            company not in assessment_map
            or company in draft_map
        ):

            raise RealCRMError(
                "Sales company differs from Analysis"
            )

        if draft.get("draft_status") != (
            "real_internal_review_only"
        ):

            raise RealCRMError(
                "Draft is not restricted to internal review"
            )

        if (
            draft.get("requires_human_review") is not True
            or draft.get("send_performed") is not False
            or draft.get("crm_write_performed") is not False
        ):

            raise RealCRMError(
                "Unsafe Sales draft"
            )

        if (
            draft.get("purchase_intent_status")
            != "unverified"
            or draft.get("budget_status")
            != "unknown"
        ):

            raise RealCRMError(
                "Sales promoted an unverified buying claim"
            )

        text = draft.get(
            "outreach_draft"
        )

        if (
            not isinstance(text, str)
            or not text.startswith(DRAFT_BANNER)
        ):

            raise RealCRMError(
                "Internal-review banner is missing"
            )

        assessment = assessment_map[
            company
        ]

        entry = draft.get(
            "entry_point"
        )

        if (
            not isinstance(entry, Mapping)
            or entry not in assessment[
                "observed_evidence"
            ]
        ):

            raise RealCRMError(
                "Sales entry point has no Analysis provenance"
            )

        if (
            entry.get("quote") not in text
            or entry.get("source_url") not in text
        ):

            raise RealCRMError(
                "Draft lost its original evidence citation"
            )

        refs = draft.get(
            "evidence_refs"
        )

        if (
            not isinstance(refs, list)
            or entry not in refs
            or not all(
                item in assessment["observed_evidence"]
                for item in refs
            )
        ):

            raise RealCRMError(
                "Sales evidence references do not match Analysis"
            )

        matches = assessment.get(
            "product_matches"
        )

        knowledge_refs = draft.get(
            "knowledge_refs"
        )

        if (
            not isinstance(matches, list)
            or not isinstance(knowledge_refs, list)
            or not all(
                match in matches
                for match in knowledge_refs
            )
        ):

            raise RealCRMError(
                "Sales knowledge references are unsupported"
            )

        draft_map[company] = dict(draft)

    if len(draft_map) != len(drafts):

        raise RealCRMError(
            "Duplicate Sales drafts"
        )

    # --------------------------------------------------------
    # Build candidates without any fabricated score
    # --------------------------------------------------------

    prepared = []

    for company, assessment in assessment_map.items():

        draft = draft_map.get(
            company
        )

        evidence = assessment[
            "observed_evidence"
        ]

        source_urls = list(
            dict.fromkeys(
                item["source_url"]
                for item in evidence
            )
        )

        proposed_action = (
            draft.get("next_action")
            if draft is not None
            else assessment.get("recommended_action")
        )

        if not (
            isinstance(proposed_action, str)
            and proposed_action.strip()
        ):

            raise RealCRMError(
                "Missing manual review action"
            )

        prepared.append({
            "company": company,
            "source_urls": source_urls,
            "source_evidence_count": len(evidence),

            "draft_present": draft is not None,

            "draft_status": (
                draft["draft_status"]
                if draft is not None
                else None
            ),

            "proposed_next_action": (
                proposed_action.strip()
            ),
        })

    return prepared


# ============================================================
# 4. Exact-name read-only CRM matching
# ============================================================

def run_real_crm(
    state: Mapping[str, Any],
    *,
    query_tool=None,
) -> dict:

    prepared = _prepare_review_items(
        state
    )

    if not prepared:

        return {
            "crm_output": {
                "status": "no_candidates",
                "mode": "read_only",
                "data_mode": DATA_MODE,

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

                "send_performed": False,
                "requires_human_review": True,

                "write_block_reason": (
                    "no_explicit_write_authorization"
                ),
            }
        }

    # This is the only actual CRM MCP invocation.
    crm_rows = _read_crm_rows(
        query_tool
    )

    snapshot_sha256 = _fingerprint_rows(
        crm_rows
    )

    matched = {
        item["company"]: []
        for item in prepared
    }

    # Do not expose unrelated CRM rows.
    for row in crm_rows:

        company = row["company"].strip()

        if company in matched:

            matched[company].append(
                row
            )

    review_records = []

    existing_count = 0
    missing_count = 0
    duplicate_count = 0

    for candidate in prepared:

        company = candidate["company"]

        found = matched[company]

        base = {
            **candidate,

            "purchase_intent_status": "unverified",

            "crm_write_performed": False,
            "action_taken": "none",

            "requires_human_review": True,
        }

        # ----------------------------------------------------
        # No matching CRM record
        # ----------------------------------------------------

        if not found:

            missing_count += 1

            review_records.append({
                **base,

                "lookup_status": "not_found",

                "existing_stage": None,
                "existing_next_action": None,
                "last_contact_time": None,

                "crm_record_provenance": (
                    "no_existing_record"
                ),

                "suggested_review": (
                    "人工核实企业主体及实际需求后，"
                    "再决定是否建立CRM记录。"
                ),
            })

            continue

        # ----------------------------------------------------
        # Multiple matching CRM records
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

                "crm_record_provenance": (
                    "unverified_legacy_crm_records"
                ),

                "suggested_review": (
                    "CRM存在同名重复记录，"
                    "需要人工核对数据来源及重复项。"
                    "禁止自动覆盖或合并。"
                ),
            })

            continue

        # ----------------------------------------------------
        # Exactly one matching CRM record
        # ----------------------------------------------------

        existing_count += 1

        row = found[0]

        review_records.append({
            **base,

            "lookup_status": "existing",

            # Read-only observations, not actual modifications.
            "existing_stage": row.get("stage"),

            "existing_next_action": row.get(
                "next_action"
            ),

            "last_contact_time": row.get(
                "last_contact_time"
            ),

            # The existing database previously contained
            # mock records. Its provenance is not assumed.
            "crm_record_provenance": (
                "unverified_legacy_crm_record"
            ),

            "suggested_review": (
                "保留CRM原有阶段和跟进信息；"
                "人工核查已有记录来源、企业主体和新证据，"
                "再决定是否采纳后续行动建议。"
            ),
        })

    status = (
        "manual_dedup_required"
        if duplicate_count
        else "review_only"
    )

    return {
        "crm_output": {
            "status": status,

            "mode": "read_only",
            "data_mode": DATA_MODE,

            "query_count": 1,
            "candidate_count": len(prepared),

            "existing_count": existing_count,
            "missing_count": missing_count,
            "duplicate_count": duplicate_count,

            "review_records": review_records,

            # Full-result fingerprint without disclosing
            # unrelated CRM records.
            "crm_query_snapshot_sha256": snapshot_sha256,

            "read_performed": True,

            "create_performed": False,
            "update_performed": False,
            "stage_changed": False,

            "send_performed": False,
            "requires_human_review": True,

            "write_block_reason": (
                "no_explicit_write_authorization"
            ),
        }
    }


# ============================================================
# 5. LangGraph Worker entrypoint
# ============================================================

def real_crm_agent_node(
    state: Mapping[str, Any],
) -> dict:

    return run_real_crm(
        state
    )
