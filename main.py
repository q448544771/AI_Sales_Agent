from pprint import pprint

from app.agent.state import SalesAgentState
from app.models.schemas import SalesGoal


goal = SalesGoal(
    target_industry="汽车零部件",
    target_count=3,
    target_region="中国",
    product_focus="工业机器视觉质检解决方案",
    user_requirement=(
        "寻找3家近期可能存在机器视觉质检需求的汽车零部件企业"
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


print("=== Sales Goal ===")

pprint(goal.model_dump())

print()

print("=== Initial Agent State ===")

pprint(state)