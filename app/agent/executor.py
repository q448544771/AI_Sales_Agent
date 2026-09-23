from app.llm.model import get_reasoning_llm


from app.tools.company_tools import (
    search_companies,
    search_company_news,
    search_company_jobs,
)


from app.tools.crm_tools import (
    query_leads,
    update_lead_stage
)


from langchain_core.messages import (
    ToolMessage,
    SystemMessage
)



# ============================
# Agent工具列表
# ============================


tools = [

    # 新客户搜索

    search_companies,


    # 企业新闻

    search_company_news,


    # 招聘信息

    search_company_jobs,


    # CRM历史查询

    query_leads,


    # CRM状态更新

    update_lead_stage

]





# ============================
# Tool映射
# ============================


tool_map = {


    "search_companies":

        search_companies,


    "search_company_news":

        search_company_news,


    "search_company_jobs":

        search_company_jobs,


    "query_leads":

        query_leads,


    "update_lead_stage":

        update_lead_stage

}





# ============================
# 创建Executor
# ============================


def create_executor():


    llm = get_reasoning_llm()



    executor = llm.bind_tools(

        tools

    )


    return executor








# ============================
# Agent Loop测试版本
# ============================


def execute_agent(messages):


    executor = create_executor()



    while True:



        response = executor.invoke(

            messages

        )



        print(

            "\n===== AI Response ====="

        )


        print(response)




        # 没有工具调用

        # Agent认为任务完成


        if not response.tool_calls:


            return response





        # 保存AI消息


        messages.append(

            response

        )






        # 执行工具


        for tool_call in response.tool_calls:



            tool_name = tool_call["name"]


            tool_args = tool_call["args"]




            print(

                f"\n执行工具: {tool_name}"

            )




            tool = tool_map[

                tool_name

            ]




            result = tool.invoke(

                tool_args

            )




            print(

                "工具返回:",

                result

            )





            messages.append(


                ToolMessage(

                    content=str(result),

                    tool_call_id=

                    tool_call["id"]

                )


            )









# ============================
# LangGraph Executor Node
# ============================


def executor_node(state):


    executor = create_executor()



    # ========================
    # Memory上下文
    # ========================


    memory_context = state.get(

        "memory_context",

        []

    )





    memory_prompt = f"""

你是一名企业销售智能Agent。


你的任务：

寻找潜在客户，并持续维护CRM销售知识库。



当前CRM历史客户信息:


{memory_context}





执行策略:


1.

首先分析CRM已有客户。


如果数据库存在相关企业：

- 不重复创建客户
- 查看客户当前销售阶段
- 分析最新业务变化



2.

对于已有客户：

重点关注：

- 新投资项目
- 新产线建设
- 招聘变化
- 自动化升级
- 新采购信号
- 当前销售阶段变化



3.

如果客户发生销售推进：

根据实际情况更新CRM状态。


可更新阶段：

new

contacted

qualified

meeting

proposal

negotiation

won

lost




4.

如果历史客户不足：

调用企业搜索工具寻找新的潜在客户。



5.

你的目标：

不是生成一次性客户名单，

而是持续维护企业销售生命周期。




"""





    messages = [


        SystemMessage(

            content=memory_prompt

        )


    ] + state["messages"]






    response = executor.invoke(

        messages

    )





    return {


        "messages":

        [

            response

        ],



        "status":

        "executing"


    }