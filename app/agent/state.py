from typing import TypedDict, Annotated, List, Any

from langchain_core.messages import BaseMessage


from app.models.schemas import (
    SalesGoal,
    ResearchPlan
)

from langgraph.graph.message import add_messages


class SalesAgentState(TypedDict):

    # 用户销售目标
    goal: SalesGoal

    # Planning输出
    research_plan: ResearchPlan | None

    # 对话消息历史（修改这里：使用 Annotated + add_messages 实现消息自动追加，避免被新消息覆盖）
    messages: Annotated[
        list[BaseMessage],
        add_messages
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

    # 上下文
    memory_context: list