from typing import Literal

from pydantic import BaseModel, Field


class SalesGoal(BaseModel):
    """用户输入的销售目标。"""

    target_industry: str = Field(
        description="目标客户所属行业，例如汽车零部件、半导体、新能源"
    )

    target_count: int = Field(
        default=3,
        ge=1,
        le=20,
        description="希望寻找的潜在客户数量"
    )

    target_region: str = Field(
        default="中国",
        description="目标客户所在区域"
    )

    product_focus: str | None = Field(
        default=None,
        description="希望销售的产品或解决方案"
    )

    user_requirement: str = Field(
        description="用户原始销售需求"
    )


class ResearchPlan(BaseModel):
    """Sales Agent Planning 阶段输出的客户研究计划。"""

    target_industry: str = Field(
        description="目标客户所属行业"
    )

    target_region: str = Field(
        description="目标客户所在区域"
    )

    target_count: int = Field(
        ge=1,
        le=20,
        description="需要寻找的潜在客户数量"
    )

    buying_signals: list[str] = Field(
        default_factory=list,
        description="判断企业存在购买意向时需要关注的外部商业信号"
    )

    research_dimensions: list[str] = Field(
        default_factory=list,
        description="针对每家候选企业需要调查的信息维度"
    )

    search_queries: list[str] = Field(
        default_factory=list,
        description="后续 Web Search Tool 可以直接使用的搜索关键词"
    )

    plan_reasoning_summary: str = Field(
        description="对研究计划的简洁、可解释说明，不包含模型内部详细推理"
    )


class Evidence(BaseModel):
    """支撑某个销售判断的外部证据。"""

    company_name: str

    evidence_type: Literal[
        "official",
        "news",
        "job",
        "industry",
        "other",
    ]

    title: str

    content: str = Field(
        description="与销售机会相关的证据摘要"
    )

    source_url: str | None = None

    published_at: str | None = None

    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="该条证据的可信度"
    )


class LeadProfile(BaseModel):
    """经过研究后形成的潜在客户画像。"""

    company_name: str

    industry: str

    region: str | None = None

    website: str | None = None

    company_summary: str = ""

    opportunity_signals: list[str] = Field(
        default_factory=list
    )

    potential_needs: list[str] = Field(
        default_factory=list
    )

    evidence: list[Evidence] = Field(
        default_factory=list
    )

    product_fit: str | None = None

    recommended_action: str | None = None


class ReviewResult(BaseModel):
    """Review 阶段对当前研究结果的检查结果。"""

    passed: bool

    completeness: float = Field(
        ge=0.0,
        le=1.0,
        description="当前研究结果的完整程度"
    )

    missing_information: list[str] = Field(
        default_factory=list
    )

    unreliable_leads: list[str] = Field(
        default_factory=list
    )

    feedback: str = Field(
        description="如果未通过，需要告诉 Executor 下一步补充什么"
    )
    
class ToolResult(BaseModel):
    """
    Agent Tool 执行结果。
    """

    success: bool = Field(
        description="工具是否成功执行"
    )

    tool_name: str = Field(
        description="执行的工具名称"
    )

    result: str = Field(
        description="工具返回的信息"
    )

    data: list[dict] = Field(
        default_factory=list,
        description="结构化数据"
    )