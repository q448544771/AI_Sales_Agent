
"""Phase 5.5 - Evidence-grounded Analysis Agent.

Inputs:
    research_output
    knowledge_output / knowledge_context

Outputs:
    analysis_output
    candidate_leads

The agent has no MCP tools and performs no CRM writes.
"""

import json
import math
import re

from collections.abc import Mapping
from typing import Any

from app.llm.model import get_reasoning_llm

from app.models.review_schema import LeadAssessment

from app.agent.reviewer import (
    REVIEWER_RELIABILITY_RULES,
    clean_json_content,
    format_knowledge_context,
)


# ============================================================
# 1. General helpers
# ============================================================

def _get(value: Any, key: str, default=None):

    if isinstance(value, Mapping):
        return value.get(key, default)

    return getattr(value, key, default)


def _target_count(state: Mapping[str, Any]) -> int:

    count = _get(
        state.get("goal"),
        "target_count",
        3,
    )

    if isinstance(count, bool) or not isinstance(count, int):
        return 3

    return min(max(count, 1), 3)


def _lines(value: Any) -> list[str]:
    """Support lists and newline-joined MCP text results."""

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


# ============================================================
# 2. Prepare company facts from actual Research records
# ============================================================

def _collect_company_facts(
    state: Mapping[str, Any],
) -> dict[str, list[str]]:

    research = state.get("research_output") or {}

    records = research.get("company_records") or []

    companies: dict[str, list[str]] = {}

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

        if company not in companies:
            companies[company] = []

        companies[company] = _unique(
            companies[company] + facts
        )

    return companies


# ============================================================
# 3. Prepare source-backed product knowledge
# ============================================================

def _collect_knowledge(
    state: Mapping[str, Any],
) -> list[dict]:

    output = state.get("knowledge_output") or {}

    documents = (
        output.get("documents")
        or state.get("knowledge_context")
        or []
    )

    result = []

    seen = set()

    for document in documents:

        if not isinstance(document, Mapping):
            continue

        content = document.get("content")
        source = document.get("source")

        if not isinstance(content, str) or not content.strip():
            continue

        if not isinstance(source, str) or not source.strip():
            continue

        content = content.strip()
        source = source.strip()

        key = (source, content)

        if key in seen:
            continue

        seen.add(key)

        result.append({
            "content": content,
            "source": source,
        })

    return result


# ============================================================
# 4. Build grounded prompt
# ============================================================

def _build_prompt(
    state: Mapping[str, Any],
    company_facts: dict[str, list[str]],
    knowledge: list[dict],
    limit: int,
) -> str:

    goal = state.get("goal")

    product_focus = _get(
        goal,
        "product_focus",
        "工业机器视觉质检解决方案",
    )

    industry = _get(
        goal,
        "target_industry",
        "汽车零部件",
    )

    knowledge_text = format_knowledge_context(
        knowledge
    )

    company_text = json.dumps(
        company_facts,
        ensure_ascii=False,
        indent=2,
    )

    source_list = json.dumps(
        [
            document["source"]
            for document in knowledge
        ],
        ensure_ascii=False,
    )

    example = [
        {
            "company": "企业名称",
            "purchase_intent_score": 0.7,
            "opportunity_level": "中",
            "evidence": [
                "从企业事实中原样选取的一条内容"
            ],
            "solution_match": [
                {
                    "company_signal": "必须与evidence中的一条完全相同",
                    "knowledge_quote": "从知识库正文原样摘录的连续文字",
                    "knowledge_source": "知识来源路径",
                    "reason": "说明信号与产品能力的对应关系",
                }
            ],
            "recommended_action": (
                "联系相关负责人确认需求与预算，"
                "准备有知识库依据的方案，并安排后续验证。"
            ),
        }
    ]

    return f"""
你是一名B2B工业销售分析专家。

本次只分析上游 Research Agent 已收集的企业事实，
结合 Knowledge Agent 已返回的内部产品知识，
生成结构化销售机会分析。

产品方向：
{product_focus}

目标行业：
{industry}

最多返回：
{limit} 家企业

============================================================
企业原始事实
============================================================

{company_text}

============================================================
内部产品知识
============================================================

{knowledge_text}

合法知识来源：
{source_list}

============================================================
Reviewer可靠性规则
============================================================

{REVIEWER_RELIABILITY_RULES}

============================================================
Phase 5额外约束
============================================================

1. company必须来自企业原始事实中的企业名称。

2. evidence中的每条内容必须与该企业原始事实中的
某一条文字完全相同，不要改写，不要扩写。

3. purchase_intent_score必须是0到1之间的有限数值。

4. opportunity_level只能填写：高、中、低。

5. solution_match必须是对象数组。
每一个对象都必须包含：
company_signal、knowledge_quote、
knowledge_source、reason。

6. company_signal必须原样引用本企业的一条evidence。

7. knowledge_quote必须是对应来源文档正文中的
连续原文片段，不得自己创造产品能力。

8. knowledge_source必须与合法知识来源完全一致。

9. 如果没有能够验证的产品知识，
solution_match必须填写空数组。

10. 招聘和扩产只是销售机会信号，
不代表采购、预算、订单、客户沟通已经确认。

11. 不得虚构ROI、产品指标、成功客户案例、
已有POC结果、采购进度或CRM阶段。

12. recommended_action只能提出未来可执行动作；
不能仅凭当前情报要求直接推进CRM阶段。

13. 如果企业事实不足，可以不选择该企业；
禁止为凑数量虚构证据。

14. 所有外部企业信息来自当前Mock数据源，
本轮只用于工程联调，不能视为真实企业核验。

============================================================
输出要求
============================================================

仅输出JSON数组，不要Markdown，不要解释文字。

参考结构（仅展示字段，不要复制示例内容）：

{json.dumps(example, ensure_ascii=False, indent=2)}
"""


# ============================================================
# 5. Verify knowledge citations
# ============================================================

def _validate_matches(
    company: str,
    evidence: list[str],
    matches: Any,
    knowledge: list[dict],
) -> tuple[list[str], list[dict]]:

    if not isinstance(matches, list):
        raise ValueError(
            f"{company}: solution_match must be a list"
        )

    normalized = []

    provenance = []

    for match in matches:

        if not isinstance(match, Mapping):
            raise ValueError(
                f"{company}: solution_match must contain objects"
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
                f"{company}: incomplete solution_match fields"
            )

        signal = signal.strip()
        quote = quote.strip()
        source = source.strip()
        reason = reason.strip()

        if signal not in evidence:
            raise ValueError(
                f"{company}: solution_match references "
                "an unsupported company signal"
            )


        # 知识库中的合法能力名称可能较短，
        # 例如“尺寸测量”“焊缝检测”。
        #
        # 不再使用固定字符长度判断知识是否可靠，
        # 而是要求引文必须实际存在于指定来源文档中。

        supported = any(
            document["source"] == source
            and quote in document["content"]
            for document in knowledge
        )

        if not supported:
            raise ValueError(
                f"{company}: knowledge quotation or source "
                "is not present in retrieved documents"
            )

        provenance.append({
            "company_signal": signal,
            "knowledge_quote": quote,
            "knowledge_source": source,
            "reason": reason,
        })

        # Keep candidate_leads compatible with the legacy
        # LeadAssessment solution_match list field.
        normalized.append(
            f"{signal}；对应知识库能力：{quote}；"
            f"来源：{source}；分析：{reason}"
        )

    return normalized, provenance


# ============================================================
# 6. Recommended-action reliability guard
# ============================================================

UNSUPPORTED_ACTION_PATTERNS = (
    r"(?:直接|立即|自动).{0,12}"
    r"(?:升级|推进|变更).{0,16}"
    r"(?:CRM|qualified|meeting|阶段)",

    r"(?:提供|展示|已有|现成).{0,12}"
    r"(?:ROI数据|成功案例|POC成功|回本周期)",

    r"(?:已确认|确定已有).{0,12}"
    r"(?:采购预算|采购订单|销售沟通)",
)


def _validate_action(
    company: str,
    action: Any,
) -> str:

    if not isinstance(action, str) or not action.strip():

        raise ValueError(
            f"{company}: recommended_action is empty"
        )

    action = action.strip()

    for pattern in UNSUPPORTED_ACTION_PATTERNS:

        if re.search(
            pattern,
            action,
            flags=re.IGNORECASE,
        ):

            raise ValueError(
                f"{company}: recommended_action "
                "contains an unsupported factual or CRM claim"
            )

    return action


# ============================================================
# 7. Main Analysis Agent
# ============================================================

def run_analysis(
    state: Mapping[str, Any],
    *,
    llm: Any = None,
) -> dict:

    company_facts = _collect_company_facts(state)

    knowledge = _collect_knowledge(state)

    limit = _target_count(state)

    research = state.get("research_output") or {}

    data_mode = research.get(
        "data_mode",
        "unknown",
    )

    # No company records: do not ask LLM to invent leads.
    if not company_facts:

        return {
            "candidate_leads": [],
            "analysis_output": {
                "status": "insufficient_research",
                "data_mode": data_mode,
                "company_count": 0,
                "selected_count": 0,
                "assessments": [],
                "requires_external_verification": True,
            },
        }

    prompt = _build_prompt(
        state,
        company_facts,
        knowledge,
        limit,
    )

    model = (
        llm
        if llm is not None
        else get_reasoning_llm()
    )

    response = model.invoke(prompt)

    content = getattr(
        response,
        "content",
        None,
    )

    if not isinstance(content, str):
        raise ValueError(
            "Analysis LLM must return text JSON"
        )

    data = json.loads(
        clean_json_content(content)
    )

    if not isinstance(data, list):
        raise ValueError(
            "Analysis Agent must return a JSON array"
        )

    if len(data) > limit:
        raise ValueError(
            f"Analysis returned more than {limit} leads"
        )

    leads = []
    assessments = []

    selected_companies = set()

    for item in data:

        if not isinstance(item, Mapping):
            raise ValueError(
                "Analysis lead must be a JSON object"
            )

        company = item.get("company")

        if (
            not isinstance(company, str)
            or company not in company_facts
        ):

            raise ValueError(
                f"Unknown company in analysis: {company}"
            )

        if company in selected_companies:
            raise ValueError(
                f"Duplicate company in analysis: {company}"
            )

        selected_companies.add(company)

        score = item.get("purchase_intent_score")

        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(score)
            or not 0 <= score <= 1
        ):

            raise ValueError(
                f"{company}: invalid purchase_intent_score"
            )

        level = item.get("opportunity_level")

        if level not in {"高", "中", "低"}:

            raise ValueError(
                f"{company}: invalid opportunity_level"
            )

        evidence = item.get("evidence")

        if not isinstance(evidence, list) or not evidence:

            raise ValueError(
                f"{company}: evidence must be a nonempty list"
            )

        if not all(
            isinstance(fact, str)
            and fact in company_facts[company]
            for fact in evidence
        ):

            raise ValueError(
                f"{company}: evidence contains unsupported facts"
            )

        if len(evidence) != len(set(evidence)):

            raise ValueError(
                f"{company}: duplicate evidence"
            )

        matches, provenance = _validate_matches(
            company,
            evidence,
            item.get("solution_match"),
            knowledge,
        )

        action = _validate_action(
            company,
            item.get("recommended_action"),
        )

        validated = LeadAssessment(
            company=company,
            purchase_intent_score=score,
            opportunity_level=level,
            evidence=evidence,
            solution_match=matches,
            recommended_action=action,
        ).model_dump()

        leads.append(validated)

        assessments.append({
            **validated,
            "match_provenance": provenance,
            "company_evidence_source": (
                "research_output.company_records"
            ),
            "requires_external_verification": True,
        })

    return {
        "candidate_leads": leads,
        "analysis_output": {
            "status": "complete",
            "data_mode": data_mode,
            "company_count": len(company_facts),
            "selected_count": len(leads),
            "knowledge_document_count": len(knowledge),
            "assessments": assessments,
            "requires_external_verification": True,
            "crm_stage_changed": False,
        },
    }


def analysis_agent_node(state: Mapping[str, Any]) -> dict:

    """Worker entrypoint for the Phase 5 Multi-Agent Graph."""

    return run_analysis(state)
