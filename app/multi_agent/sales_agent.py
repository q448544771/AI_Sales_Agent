"""Phase 5.6 - Evidence-grounded Sales Agent.

Inputs:
    research_output
    knowledge_output
    analysis_output
    candidate_leads

Output:
    sales_output

DeepSeek selects verified evidence, product references, contact roles,
and discovery questions.

The final outreach draft is assembled deterministically.

This module never sends messages, calls CRM tools, or writes to a database.
"""

import json
import math

from collections.abc import Mapping
from typing import Any

from app.llm.model import get_fast_llm

from app.models.review_schema import LeadAssessment

from app.agent.reviewer import clean_json_content


# ============================================================
# 1. Sales Agent configuration
# ============================================================

ALLOWED_CONTACT_ROLES = (
    "质量负责人",
    "自动化负责人",
    "生产负责人",
    "技术负责人",
    "通用业务联系人",
)


QUESTION_BANK = {
    "current_method": (
        "请问目前主要采用人工检测还是自动化检测？"
    ),
    "inspection_target": (
        "请问希望检测的具体零部件和检测工位有哪些？"
    ),
    "defect_types": (
        "请问当前最关注的缺陷类型或尺寸指标是什么？"
    ),
    "cycle_time": (
        "请问产线节拍及单件允许检测时间是多少？"
    ),
    "system_integration": (
        "请问现场是否需要对接MES或质量追溯系统？"
    ),
    "project_timing": (
        "请问目前是否已有项目计划、预算或预计实施时间？"
    ),
    "sample_validation": (
        "是否方便提供样件，以便开展打光与成像可行性验证？"
    ),
}


# ============================================================
# 2. General helpers
# ============================================================

def _get(value: Any, key: str, default=None):

    if isinstance(value, Mapping):
        return value.get(key, default)

    return getattr(value, key, default)


def _lines(value: Any) -> list[str]:

    if value is None:
        return []

    if isinstance(value, str):

        return [
            line.strip()
            for line in value.splitlines()
            if line.strip()
        ]

    if isinstance(value, (list, tuple)):

        result = []

        for item in value:
            result.extend(_lines(item))

        return result

    return []


def _unique(items: list[str]) -> list[str]:

    return list(dict.fromkeys(items))


def _target_count(state: Mapping[str, Any]) -> int:

    count = _get(
        state.get("goal"),
        "target_count",
        3,
    )

    if (
        isinstance(count, bool)
        or not isinstance(count, int)
    ):
        count = 3

    return min(max(count, 1), 3)


# ============================================================
# 3. Rebuild original company facts
# ============================================================

def _company_facts(
    state: Mapping[str, Any],
) -> dict[str, list[str]]:

    research = state.get("research_output") or {}

    records = research.get("company_records") or []

    result = {}

    for record in records:

        if not isinstance(record, Mapping):
            continue

        company = record.get("company")

        if not isinstance(company, str) or not company.strip():
            continue

        company = company.strip()

        profile = record.get("profile") or {}

        signals = []

        if isinstance(profile, Mapping):
            signals = _lines(profile.get("signals"))

        facts = _unique(
            signals
            + _lines(record.get("news"))
            + _lines(record.get("jobs"))
        )

        result[company] = _unique(
            result.get(company, []) + facts
        )

    return result


# ============================================================
# 4. Rebuild original knowledge documents
# ============================================================

def _knowledge_documents(
    state: Mapping[str, Any],
) -> list[dict]:

    output = state.get("knowledge_output") or {}

    documents = output.get("documents") or []

    result = []

    for document in documents:

        if not isinstance(document, Mapping):
            continue

        content = document.get("content")
        source = document.get("source")

        if not isinstance(content, str) or not content.strip():
            continue

        if not isinstance(source, str) or not source.strip():
            continue

        result.append({
            "content": content.strip(),
            "source": source.strip(),
        })

    return result


# ============================================================
# 5. Verify Analysis Agent output before using it
# ============================================================

def _prepare_candidates(
    state: Mapping[str, Any],
) -> list[dict]:

    analysis = state.get("analysis_output") or {}

    if analysis.get("status") not in {
        "complete",
        "insufficient_research",
    }:

        raise ValueError(
            "Sales Agent requires completed Analysis output"
        )

    leads = state.get("candidate_leads") or []

    if not isinstance(leads, list):

        raise ValueError(
            "candidate_leads must be a list"
        )

    if not leads:
        return []

    limit = _target_count(state)

    if len(leads) > limit:

        raise ValueError(
            "candidate_leads exceeds target count"
        )

    assessments = analysis.get("assessments") or []

    if not isinstance(assessments, list):

        raise ValueError(
            "analysis assessments must be a list"
        )

    by_company = {}

    for assessment in assessments:

        if not isinstance(assessment, Mapping):
            raise ValueError(
                "Invalid analysis assessment"
            )

        company = assessment.get("company")

        if company in by_company:
            raise ValueError(
                "Duplicate analysis assessment"
            )

        by_company[company] = assessment

    original_facts = _company_facts(state)

    documents = _knowledge_documents(state)

    prepared = []

    seen_companies = set()

    for lead in leads:

        # Retain compatibility with the Phase 4 schema.
        validated = LeadAssessment.model_validate(
            lead
        ).model_dump()

        company = validated["company"]

        if company in seen_companies:
            raise ValueError(
                f"Duplicate candidate: {company}"
            )

        seen_companies.add(company)

        if company not in original_facts:
            raise ValueError(
                f"Unknown research company: {company}"
            )

        if company not in by_company:
            raise ValueError(
                f"Missing analysis assessment: {company}"
            )

        score = validated["purchase_intent_score"]

        if (
            not math.isfinite(score)
            or not 0 <= score <= 1
        ):
            raise ValueError(
                f"Invalid assessment score: {company}"
            )

        evidence = validated["evidence"]

        if not evidence or not all(
            fact in original_facts[company]
            for fact in evidence
        ):

            raise ValueError(
                f"Unsupported research evidence: {company}"
            )

        assessment = by_company[company]

        if assessment.get("evidence") != evidence:

            raise ValueError(
                f"Analysis and candidate evidence differ: {company}"
            )

        matches = assessment.get("match_provenance") or []

        if not isinstance(matches, list):

            raise ValueError(
                f"Invalid knowledge provenance: {company}"
            )

        verified_matches = []

        for match in matches:

            if not isinstance(match, Mapping):
                raise ValueError(
                    f"Malformed knowledge match: {company}"
                )

            signal = match.get("company_signal")
            quote = match.get("knowledge_quote")
            source = match.get("knowledge_source")
            reason = match.get("reason")

            if not all(
                isinstance(value, str) and value.strip()
                for value in (signal, quote, source, reason)
            ):

                raise ValueError(
                    f"Incomplete knowledge match: {company}"
                )

            if signal not in evidence:

                raise ValueError(
                    f"Unsupported match signal: {company}"
                )

            supported = any(
                document["source"] == source
                and quote in document["content"]
                for document in documents
            )

            if not supported:

                raise ValueError(
                    f"Unsupported knowledge quotation: {company}"
                )

            verified_matches.append({
                "company_signal": signal,
                "knowledge_quote": quote,
                "knowledge_source": source,
                "reason": reason,
            })

        prepared.append({
            "company": company,
            "purchase_intent_score": score,
            "opportunity_level": validated["opportunity_level"],
            "evidence_options": evidence,
            "knowledge_match_options": verified_matches,
            "analysis_recommended_action": (
                validated["recommended_action"]
            ),
        })

    return prepared


# ============================================================
# 6. Sales planning prompt
# ============================================================

def _build_prompt(prepared: list[dict]) -> str:

    reference = [
        {
            "company": "企业名称",
            "contact_role": "质量负责人",
            "evidence_refs": [
                "从evidence_options中原样选择"
            ],
            "knowledge_match_indices": [0],
            "question_ids": [
                "current_method",
                "defect_types",
                "project_timing",
            ],
        }
    ]

    return f"""
你是企业AI销售助手。

你的任务不是重新判断企业事实，也不是自行编造销售文案。

你只需要从已经验证的选项中，为每家企业选择：

1. 建议联系的岗位角色；
2. 用于销售切入的原始企业证据；
3. 可引用的知识库匹配编号；
4. 适合初次沟通的需求确认问题编号。

所有候选企业及其合法选项：

{json.dumps(prepared, ensure_ascii=False, indent=2)}

合法联系人角色：

{json.dumps(ALLOWED_CONTACT_ROLES, ensure_ascii=False)}

合法问题编号：

{json.dumps(QUESTION_BANK, ensure_ascii=False, indent=2)}

严格要求：

1. company必须与输入企业名称完全相同。
2. 每家企业必须输出一项，不能新增、遗漏或重复企业。
3. contact_role只能使用指定枚举。
4. evidence_refs必须从本企业的evidence_options原样选取。
5. evidence_refs至少1条，最多2条。
6. knowledge_match_indices使用从0开始的整数编号。
7. 只可选本企业已有的知识匹配编号，最多2个。
8. 没有可用知识匹配时填写空数组。
9. question_ids只能从QUESTION_BANK选择，选2至4个。
10. 不要生成任何新的企业事实、产品性能或客户案例。
11. 不要输出新的联系方式、邮箱或客户负责人姓名。
12. 不要声称已经触达客户、发送消息或确认采购。
13. 只输出JSON数组，不要Markdown或解释。

输出结构参考：

{json.dumps(reference, ensure_ascii=False, indent=2)}
"""


# ============================================================
# 7. Validate LLM selections
# ============================================================

def _validate_selection(
    item: Any,
    candidate: dict,
) -> dict:

    company = candidate["company"]

    if not isinstance(item, Mapping):
        raise ValueError(
            f"Invalid Sales selection for {company}"
        )

    if item.get("company") != company:
        raise ValueError(
            f"Sales company mismatch: {company}"
        )

    role = item.get("contact_role")

    if role not in ALLOWED_CONTACT_ROLES:
        raise ValueError(
            f"Invalid contact role: {company}"
        )

    evidence_refs = item.get("evidence_refs")

    if (
        not isinstance(evidence_refs, list)
        or not 1 <= len(evidence_refs) <= 2
        or len(evidence_refs) != len(set(evidence_refs))
    ):
        raise ValueError(
            f"Invalid evidence selection: {company}"
        )

    if not all(
        isinstance(fact, str)
        and fact in candidate["evidence_options"]
        for fact in evidence_refs
    ):
        raise ValueError(
            f"Unsupported selected evidence: {company}"
        )

    indices = item.get("knowledge_match_indices")

    if (
        not isinstance(indices, list)
        or len(indices) > 2
        or len(indices) != len(set(map(str, indices)))
    ):
        raise ValueError(
            f"Invalid knowledge indices: {company}"
        )

    options = candidate["knowledge_match_options"]

    if not all(
        isinstance(index, int)
        and not isinstance(index, bool)
        and 0 <= index < len(options)
        for index in indices
    ):
        raise ValueError(
            f"Unsupported knowledge index: {company}"
        )

    question_ids = item.get("question_ids")

    if (
        not isinstance(question_ids, list)
        or not 2 <= len(question_ids) <= 4
        or len(question_ids) != len(set(question_ids))
    ):
        raise ValueError(
            f"Invalid discovery questions: {company}"
        )

    if not all(
        isinstance(question_id, str)
        and question_id in QUESTION_BANK
        for question_id in question_ids
    ):
        raise ValueError(
            f"Unknown question ID: {company}"
        )

    return {
        "company": company,
        "contact_role": role,
        "evidence_refs": evidence_refs,
        "knowledge_matches": [
            options[index]
            for index in indices
        ],
        "discovery_questions": [
            QUESTION_BANK[question_id]
            for question_id in question_ids
        ],
    }


# ============================================================
# 8. Assemble sales draft from verified content only
# ============================================================

def _build_sales_draft(
    selection: dict,
    data_mode: str,
) -> dict:

    company = selection["company"]
    role = selection["contact_role"]

    evidence = selection["evidence_refs"][0]

    matches = selection["knowledge_matches"]

    if data_mode == "mock_company_mcp":

        prefix = (
            "【模拟数据｜仅供内部演练｜禁止发送】\n"
        )

        draft_status = "mock_internal_only"

    else:

        prefix = (
            "【待人工核验｜尚未发送】\n"
        )

        draft_status = "requires_human_review"

    # Only source-backed claims are inserted into the draft.
    draft = (
        prefix
        + f"您好，根据当前初步调研记录，了解到贵司"
        + f"“{evidence}”，具体情况仍需向贵司核实。"
    )

    if matches:

        quote = matches[0]["knowledge_quote"]

        draft += (
            f"我们的内部产品资料记录有"
            f"“{quote}”相关能力，"
            f"可以在明确具体检测对象后进一步讨论适配性。"
        )

    draft += (
        f"希望向贵司{role}了解当前检测方式、"
        f"主要质量检测难点及后续项目安排。"
        f"如方便，期待开展一次简短的需求交流。"
    )

    next_action = (
        f"建议人工核实企业情报后，"
        f"联系{role}，确认具体检测对象、"
        f"现有检测方式、产线节拍及采购计划；"
        f"在需求明确后讨论样件成像或POC验证。"
        f"CRM阶段仅依据真实销售沟通记录决定。"
    )

    return {
        "company": company,
        "contact_role": role,
        "entry_point": evidence,
        "evidence_refs": selection["evidence_refs"],
        "knowledge_refs": matches,
        "discovery_questions": (
            selection["discovery_questions"]
        ),
        "outreach_draft": draft,
        "next_action": next_action,
        "draft_status": draft_status,
        "requires_human_review": True,
        "send_performed": False,
        "crm_write_performed": False,
    }


# ============================================================
# 9. Main Sales Agent
# ============================================================

def run_sales(
    state: Mapping[str, Any],
    *,
    llm: Any = None,
) -> dict:

    prepared = _prepare_candidates(state)

    research = state.get("research_output") or {}

    data_mode = research.get(
        "data_mode",
        "unknown",
    )

    # No verified leads: never invent sales targets.
    if not prepared:

        return {
            "sales_output": {
                "status": "no_candidates",
                "data_mode": data_mode,
                "draft_count": 0,
                "drafts": [],
                "requires_human_review": True,
                "send_performed": False,
                "crm_write_performed": False,
            }
        }

    model = (
        llm
        if llm is not None
        else get_fast_llm()
    )

    response = model.invoke(
        _build_prompt(prepared)
    )

    content = getattr(
        response,
        "content",
        None,
    )

    if not isinstance(content, str):
        raise ValueError(
            "Sales LLM must return JSON text"
        )

    payload = json.loads(
        clean_json_content(content)
    )

    if not isinstance(payload, list):

        raise ValueError(
            "Sales Agent must return a JSON array"
        )

    if len(payload) != len(prepared):

        raise ValueError(
            "Sales Agent returned an incorrect candidate count"
        )

    selections = {}

    for item in payload:

        if not isinstance(item, Mapping):
            raise ValueError(
                "Invalid Sales response item"
            )

        company = item.get("company")

        if (
            not isinstance(company, str)
            or company in selections
        ):

            raise ValueError(
                "Duplicate or invalid Sales company"
            )

        selections[company] = item

    drafts = []

    for candidate in prepared:

        company = candidate["company"]

        if company not in selections:

            raise ValueError(
                f"Missing Sales selection: {company}"
            )

        selection = _validate_selection(
            selections[company],
            candidate,
        )

        drafts.append(
            _build_sales_draft(
                selection,
                data_mode,
            )
        )

    return {
        "sales_output": {
            "status": "complete",
            "data_mode": data_mode,
            "draft_count": len(drafts),
            "drafts": drafts,
            "requires_human_review": True,
            "send_performed": False,
            "crm_write_performed": False,
        }
    }


def sales_agent_node(state: Mapping[str, Any]) -> dict:

    """Worker entrypoint for the Phase 5 Multi-Agent Graph."""

    return run_sales(state)