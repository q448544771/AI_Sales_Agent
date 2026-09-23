from pprint import pprint


from app.graph.workflow import create_graph

from app.models.schemas import SalesGoal

from langchain_core.messages import HumanMessage


graph = create_graph()



initial_state = {

    "goal": SalesGoal(

        target_industry="汽车零部件",

        target_count=3,

        target_region="中国",

        product_focus=
        "工业机器视觉质检解决方案",

        user_requirement=
        "寻找近期可能需要机器视觉质检方案的企业"

    ),


    "research_plan":None,


    "messages":[

    HumanMessage(
        content=
        """
        寻找中国汽车零部件行业中，
        可能需要工业机器视觉质检方案的企业。
        """
        )

    ],

    "candidate_leads":[],

    "evidence":[],

    "status":"planning",

    "iteration":0,

    "max_iterations":3

}



result = graph.invoke(
    initial_state
)


print("\n========== Final State ==========\n")


pprint(result)