from app.agent.state import SalesAgentState
# from app.llm.model import get_llm
from app.llm.model import get_fast_llm
from app.models.schemas import ResearchPlan


PLANNER_SYSTEM_PROMPT = """
你是企业级 B2B AI Sales Agent 的 Planning 模块。

你的唯一职责是：

根据用户给出的销售目标，制定后续潜在客户研究计划。

你现在不能：
1. 寻找具体企业；
2. 虚构企业名称；
3. 执行真实搜索；
4. 直接给出销售结论。

你只负责制定研究计划。

研究计划需要帮助后续 Executor 判断哪些企业可能存在真实购买需求。

对于工业 AI、机器视觉和智能制造场景，可重点考虑：

- 新建工厂或生产基地
- 新建或扩建生产线
- 自动化升级
- 数字化改造
- 招聘机器视觉工程师
- 招聘自动化工程师
- 招聘质量检测工程师
- 新产品量产
- 质量控制需求
- 产能扩张

请严格使用系统提供的 ResearchPlan 数据结构。

字段含义：

target_industry:
目标客户行业。

target_region:
目标客户所在区域。

target_count:
需要寻找的潜在客户数量。
必须直接使用用户要求的数量。

buying_signals:
后续判断企业是否具有购买需求时重点观察的信号。

research_dimensions:
后续针对每家候选企业需要调查哪些信息。

search_queries:
后续搜索工具可以直接使用的初始搜索关键词。

plan_reasoning_summary:
用简短文字解释为什么这样规划。
只输出可供系统使用的规划依据，
不要输出详细内部推理过程。

不要创建 ResearchPlan 之外的任何字段。
"""


def planning_node(state: SalesAgentState) -> dict:
    """
    Planning Node

    根据用户销售目标生成结构化 ResearchPlan。

    输入：
        SalesAgentState

    输出：
        research_plan
        status
    """

    goal = state["goal"]

    # llm = get_llm()
    llm = get_fast_llm()

    # 使用 Function Calling，
    # 让模型严格按照 ResearchPlan Schema 返回结果
    structured_llm = llm.with_structured_output(
        ResearchPlan,
        method="function_calling",
    )

    user_prompt = f"""
根据下面的销售目标制定客户研究计划。

目标行业：
{goal.target_industry}

目标区域：
{goal.target_region}

目标客户数量：
{goal.target_count}

销售产品或解决方案：
{goal.product_focus}

用户原始需求：
{goal.user_requirement}

注意：

target_count 必须为：
{goal.target_count}

不要修改字段名称。
不要创建额外字段。
不要寻找具体企业。
"""

    plan = structured_llm.invoke(
        [
            ("system", PLANNER_SYSTEM_PROMPT),
            ("human", user_prompt),
        ]
    )

    return {
        "research_plan": plan,
        "status": "executing",
    }