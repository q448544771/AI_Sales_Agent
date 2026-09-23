from app.tools.crm_tools import query_leads



def memory_retrieval_node(state):


    """
    Memory Retrieval Node


    根据当前任务自动查询CRM

    将历史客户注入State

    """



    goal = state.get(
        "goal"
    )


    if not goal:


        return {

            "memory_context":[]

        }



    industry = goal.target_industry



    print(
        "\n===== Memory Retrieval ====="
    )


    print(
        "查询行业:",
        industry
    )



    history = query_leads.invoke(

        {
            "industry":industry
        }

    )



    print(
        "历史客户:",
        history
    )



    return {


        "memory_context":

        history

    }