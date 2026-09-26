"""Phase 5.4 - Knowledge Agent.

Research output -> contextual product queries -> Knowledge MCP
-> knowledge_output + knowledge_context.

This module does not write CRM or modify the Phase 4 graph.
"""

import json
from collections.abc import Mapping
from typing import Any

from app.mcp.adapter import load_knowledge_langchain_tools_sync


KNOWLEDGE_TOOL_NAME = "search_product_knowledge"
MAX_KNOWLEDGE_CALLS = 2

SCENE_KEYWORDS = {
    "焊缝检测": ("焊接", "焊缝", "焊点"),
    "装配检测": ("装配", "漏装", "错装", "少件"),
    "外观缺陷检测": ("外观", "表面缺陷", "划痕", "毛刺", "凹坑"),
    "尺寸测量": ("尺寸", "公差", "精密", "测量"),
    "质量追溯": ("追溯",),
}


def _field(value: Any, name: str, default: Any = None) -> Any:
    """Read either a dictionary or an existing Pydantic model."""

    if isinstance(value, Mapping):
        return value.get(name, default)

    return getattr(value, name, default)


def _as_text(value: Any) -> str:

    if isinstance(value, str):
        return value

    if isinstance(value, (list, tuple)):
        return " ".join(_as_text(item) for item in value)

    if isinstance(value, Mapping):
        return " ".join(_as_text(item) for item in value.values())

    return "" if value is None else str(value)


def _research_signal_text(state: Mapping[str, Any]) -> str:
    """Only use tool-derived research records, not LLM summary text."""

    research = state.get("research_output") or {}
    records = research.get("company_records") or []

    fragments = []

    for record in records:

        if not isinstance(record, Mapping):
            continue

        profile = record.get("profile") or {}

        if isinstance(profile, Mapping):
            fragments.append(_as_text(profile.get("signals", [])))

        fragments.append(_as_text(record.get("news", [])))
        fragments.append(_as_text(record.get("jobs", [])))

    return " ".join(fragments)


def build_knowledge_queries(
    state: Mapping[str, Any],
    max_calls: int = MAX_KNOWLEDGE_CALLS,
) -> list[str]:
    """Create bounded queries from the sales goal and research evidence."""

    if not isinstance(max_calls, int) or max_calls < 1:
        raise ValueError("max_calls must be a positive integer")

    limit = min(max_calls, MAX_KNOWLEDGE_CALLS)

    goal = state.get("goal")

    focus = _field(
        goal,
        "product_focus",
        "工业机器视觉质检解决方案",
    ) or "工业机器视觉质检解决方案"

    industry = _field(
        goal,
        "target_industry",
        "汽车零部件",
    ) or "汽车零部件"

    queries = [
        (
            f"{focus} {industry} "
            "外观缺陷检测 尺寸测量 装配检测 产品能力"
        )
    ]

    signals = _research_signal_text(state)

    matched_scenes = []

    for scene, keywords in SCENE_KEYWORDS.items():

        if any(keyword in signals for keyword in keywords):
            matched_scenes.append(scene)

    if matched_scenes:

        contextual_query = (
            f"{industry} "
            f"{' '.join(matched_scenes)} "
            "机器视觉质检能力及适用场景"
        )

        if contextual_query not in queries:
            queries.append(contextual_query)

    return queries[:limit]


def _decode_result(value: Any) -> dict:
    """Normalize the documented Knowledge MCP result structure."""

    if isinstance(value, str):

        try:
            value = json.loads(value)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Knowledge MCP returned invalid JSON"
            ) from exc

    if not isinstance(value, Mapping):
        raise ValueError(
            "Knowledge MCP result must be a dictionary"
        )

    # Compatible with a single-field MCP wrapper.
    if set(value.keys()) == {"result"}:
        return _decode_result(value["result"])

    if value.get("success") is not True:
        raise RuntimeError(
            f"Knowledge MCP reported failure: "
            f"{value.get('message', 'unknown error')}"
        )

    if not isinstance(value.get("results"), list):
        raise ValueError(
            "Knowledge MCP result is missing a valid results list"
        )

    return dict(value)


def _normalize_document(raw: Any) -> dict | None:
    """Require both document content and verifiable source metadata."""

    if not isinstance(raw, Mapping):
        return None

    content = raw.get("content")
    metadata = raw.get("metadata") or {}

    if not isinstance(metadata, Mapping):
        metadata = {}

    source = raw.get("source") or metadata.get("source")

    if not isinstance(content, str) or not content.strip():
        return None

    if not isinstance(source, str) or not source.strip():
        return None

    return {
        "content": content.strip(),
        "source": source.strip(),
        "metadata": dict(metadata),
    }


def _load_knowledge_tool():
    """Load the existing Knowledge MCP adapter, never the CRM adapter."""

    tools = load_knowledge_langchain_tools_sync()

    matches = [
        item
        for item in tools
        if item.name == KNOWLEDGE_TOOL_NAME
    ]

    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one search_product_knowledge MCP tool"
        )

    return matches[0]


def run_knowledge(
    state: Mapping[str, Any],
    *,
    tool: Any = None,
    max_calls: int = MAX_KNOWLEDGE_CALLS,
) -> dict:
    """Run bounded product retrieval and preserve document provenance."""

    queries = build_knowledge_queries(
        state,
        max_calls=max_calls,
    )

    knowledge_tool = (
        tool if tool is not None
        else _load_knowledge_tool()
    )

    if getattr(knowledge_tool, "name", None) != KNOWLEDGE_TOOL_NAME:
        raise ValueError(
            "Knowledge Agent can only call search_product_knowledge"
        )

    unique_documents: dict[tuple[str, str], dict] = {}
    query_log = []

    for query in queries:

        try:
            raw_result = knowledge_tool.invoke({
                "query": query,
            })

        except Exception as exc:
            raise RuntimeError(
                "Knowledge MCP tool invocation failed"
            ) from exc

        result = _decode_result(raw_result)

        accepted = 0

        for raw_document in result["results"]:

            document = _normalize_document(raw_document)

            if document is None:
                continue

            key = (
                document["source"],
                document["content"],
            )

            if key not in unique_documents:
                unique_documents[key] = document
                accepted += 1

        query_log.append({
            "query": query,
            "returned_count": len(result["results"]),
            "new_unique_documents": accepted,
        })

    documents = list(unique_documents.values())

    context = [
        {
            "content": document["content"],
            "source": document["source"],
        }
        for document in documents
    ]

    return {
        "knowledge_output": {
            "status": "complete" if documents else "empty",
            "source_type": "internal_product_knowledge",
            "mcp_tool": KNOWLEDGE_TOOL_NAME,
            "mcp_calls": len(query_log),
            "queries": queries,
            "query_log": query_log,
            "document_count": len(documents),
            "documents": documents,
            "evidence_policy": (
                "Only retrieved product documentation is evidence. "
                "No unsupported ROI, performance metrics, "
                "customer references or POC results."
            ),
        },
        "knowledge_context": context,
    }


def knowledge_agent_node(state: Mapping[str, Any]) -> dict:
    """Entrypoint for create_multi_graph()."""

    return run_knowledge(state)