from app.agent.knowledge_retriever import (
    knowledge_retrieval_node
)

from app.models.schemas import SalesGoal

state = {

    "goal":

    SalesGoal(

        target_industry="汽车零部件",

        target_count=3,

        target_region="中国",

        product_focus="工业机器视觉质检解决方案",

        user_requirement=
        "寻找需要机器视觉质检方案的企业"

    )

}



result = knowledge_retrieval_node(
    state
)


print("================")

print(
    result
)