from app.knowledge.retriever.product_retriever import (
    get_product_retriever
)



def knowledge_retrieval_node(state):

    """
    Knowledge Retrieval Node

    根据当前销售任务，
    从产品知识库检索相关方案。

    输出:
    state["knowledge_context"]
    """


    goal = state.get(
        "goal"
    )


    if not goal:

        return {

            "knowledge_context":[]

        }


    # ----------------------------
    # 构造查询问题
    # ----------------------------

    query = (

        goal.product_focus

        +

        " "

        +

        goal.target_industry

    )


    print(
        "\n===== Knowledge Retrieval ====="
    )

    print(
        "查询知识:",
        query
    )


    # ----------------------------
    # 获取Retriever
    # ----------------------------

    retriever = (
        get_product_retriever()
    )


    # ----------------------------
    # 检索
    # ----------------------------

    docs = retriever.invoke(
        query
    )


    context = []


    for doc in docs:


        context.append(

            {

                "content":
                    doc.page_content,


                "source":
                    doc.metadata.get(
                        "source"
                    )

            }

        )


    print(
        "检索结果数量:",
        len(context)
    )


    return {

        "knowledge_context":
            context

    }