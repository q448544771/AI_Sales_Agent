from typing import TypedDict, Annotated

from langchain_core.messages import BaseMessage

from app.models.schemas import (
    SalesGoal,
    ResearchPlan,
)

from langgraph.graph.message import add_messages


class SalesAgentState(TypedDict):

    # 用户销售目标
    goal: SalesGoal

    # Planning输出
    research_plan: ResearchPlan | None

    # 对话消息历史
    #
    # 使用 Annotated + add_messages
    # 实现LangGraph消息自动追加，
    # 避免新消息覆盖历史消息。
    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    # 候选客户
    candidate_leads: list[dict]

    # 证据
    evidence: list[dict]

    # 当前状态
    status: str

    # 当前循环次数
    iteration: int

    # 最大循环
    max_iterations: int

    # CRM / Agent历史上下文
    memory_context: list

    # 产品知识库检索上下文
    #
    # 由：
    #
    # app.agent.knowledge_retriever
    #
    # 中的：
    #
    # knowledge_retrieval_node
    #
    # 写入。
    #
    # 典型结构：
    #
    # [
    #     {
    #         "content": "...",
    #         "source": "..."
    #     }
    # ]
    #
    # Reviewer可以读取该字段，
    # 将企业需求与内部产品知识进行匹配。
    knowledge_context: list[dict]