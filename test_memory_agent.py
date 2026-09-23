from app.graph.workflow import create_graph


from app.models.schemas import SalesGoal


from langchain_core.messages import HumanMessage



graph = create_graph()



goal = SalesGoal(

    target_industry="汽车零部件",

    target_count=3,

    target_region="中国",

    product_focus="工业机器视觉质检解决方案",

    user_requirement=
    "寻找近期可能需要机器视觉质检方案的企业"

)



result = graph.invoke(

{

    "goal":goal,


    "messages":[

        HumanMessage(

            content=
            """
            帮我寻找汽车零部件行业中
            可能需要工业机器视觉质检方案的企业。
            """

        )

    ],


    "candidate_leads":[],

    "evidence":[],

    "iteration":0,

    "max_iterations":3,

    "status":"planning"

}

)




print("\n========== FINAL ==========")



for msg in result["messages"]:

    print("\n================")

    print(msg)