from pprint import pprint

from app.agent.planner import planning_node
from app.agent.state import SalesAgentState
from app.models.schemas import SalesGoal


goal = SalesGoal(
    target_industry="汽车零部件",
    target_count=3,
    target_region="中国",
    product_focus="工业机器视觉质检解决方案",
    user_requirement=(
        "寻找3家近期可能存在机器视觉质检需求的汽车零部件企业，"
        "重点关注近期扩产、新建产线或自动化升级的企业"
    ),
)


state: SalesAgentState = {
    "goal": goal,
    "candidate_leads": [],
    "evidence": [],
    "iteration": 0,
    "max_iterations": 3,
    "status": "planning",
}


print("\n========== 当前销售目标 ==========\n")

pprint(goal.model_dump())


print("\n========== Planning Node 开始 ==========\n")

update = planning_node(state)


print("\n========== Planning Node 返回 ==========\n")

plan = update["research_plan"]

pprint(plan.model_dump())


state.update(update)


print("\n========== 更新后的 Agent State ==========\n")

print("status:", state["status"])
print("iteration:", state["iteration"])
print("research_plan type:", type(state["research_plan"]))