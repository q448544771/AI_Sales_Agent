from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from langgraph.prebuilt import ToolNode


# ============================================================
# 状态定义
# ============================================================

from app.agent.state import SalesAgentState



# ============================================================
# Agent节点
# ============================================================

from app.agent.planner import planning_node


from app.agent.executor import (
    executor_node,
    tools as executor_tools,
)


from app.agent.reviewer import review_node



# ============================================================
# Memory相关
# ============================================================

from app.agent.memory import memory_node


from app.agent.memory_retriever import (
    memory_retrieval_node,
)



# ============================================================
# Knowledge Retrieval
# ============================================================

from app.agent.knowledge_retriever import (
    knowledge_retrieval_node,
)



# ============================================================
# Follow-up销售动作
# ============================================================

from app.agent.followup import followup_node





# ============================================================
# Executor路由判断
# ============================================================

def should_continue(
    state: SalesAgentState
):

    """
    判断 Executor 下一步执行方向。


    如果最后一条 AIMessage 包含 tool_calls：

        Executor
            ↓
        Tools


    如果没有 tool_calls：

        Executor
            ↓
        Knowledge Retrieval
            ↓
        Review
    """


    messages = state.get(
        "messages",
        []
    )


    if not messages:

        return "knowledge"



    last_message = messages[-1]



    if getattr(
        last_message,
        "tool_calls",
        None
    ):

        return "tools"



    return "knowledge"







# ============================================================
# 创建Graph
# ============================================================

def create_graph():

    """
    AI Sales Agent 工作流


    当前流程：

    
    START

      ↓

    Memory Retrieval

      ↓

    Planner

      ↓

    Executor

      ↓

    Tool循环


      ↓


    Knowledge Retrieval

      ↓

    Reviewer

      ↓

    Memory

      ↓

    Follow-up

      ↓

    END



    Knowledge Retrieval作用：

    根据当前销售目标：

        产品信息
        行业信息

    检索企业产品知识，

    为Reviewer提供：

        产品能力
        适用场景
        解决方案


    """


    graph = StateGraph(
        SalesAgentState
    )



    # ========================================================
    # Nodes
    # ========================================================


    # --------------------------------------------------------
    # 1. CRM历史记忆检索
    # --------------------------------------------------------

    graph.add_node(

        "memory_retrieval",

        memory_retrieval_node

    )



    # --------------------------------------------------------
    # 2. 任务规划
    # --------------------------------------------------------

    graph.add_node(

        "planner",

        planning_node

    )



    # --------------------------------------------------------
    # 3. Agent执行
    # --------------------------------------------------------

    graph.add_node(

        "executor",

        executor_node

    )



    # --------------------------------------------------------
    # 4. Tool执行
    # --------------------------------------------------------

    graph.add_node(

        "tools",

        ToolNode(
            executor_tools
        )

    )



    # --------------------------------------------------------
    # 5. 产品知识检索
    # --------------------------------------------------------

    graph.add_node(

        "knowledge",

        knowledge_retrieval_node

    )



    # --------------------------------------------------------
    # 6. 客户评估
    # --------------------------------------------------------

    graph.add_node(

        "review",

        review_node

    )



    # --------------------------------------------------------
    # 7. CRM保存
    # --------------------------------------------------------

    graph.add_node(

        "memory",

        memory_node

    )



    # --------------------------------------------------------
    # 8. 销售跟进
    # --------------------------------------------------------

    graph.add_node(

        "followup",

        followup_node

    )




    # ========================================================
    # Fixed Edges
    # ========================================================


    # START
    #
    # ↓
    #
    # Memory Retrieval

    graph.add_edge(

        START,

        "memory_retrieval"

    )



    # Memory Retrieval
    #
    # ↓
    #
    # Planner

    graph.add_edge(

        "memory_retrieval",

        "planner"

    )



    # Planner
    #
    # ↓
    #
    # Executor

    graph.add_edge(

        "planner",

        "executor"

    )



    # Tool
    #
    # ↓
    #
    # Executor继续推理

    graph.add_edge(

        "tools",

        "executor"

    )



    # Knowledge
    #
    # ↓
    #
    # Review

    graph.add_edge(

        "knowledge",

        "review"

    )



    # Review
    #
    # ↓
    #
    # Memory

    graph.add_edge(

        "review",

        "memory"

    )



    # Memory
    #
    # ↓
    #
    # Follow-up

    graph.add_edge(

        "memory",

        "followup"

    )



    # Follow-up
    #
    # ↓
    #
    # END

    graph.add_edge(

        "followup",

        END

    )




    # ========================================================
    # Conditional Edge
    # ========================================================


    graph.add_conditional_edges(

        "executor",

        should_continue,

        {

            "tools":

                "tools",


            "knowledge":

                "knowledge",

        }

    )




    # ========================================================
    # Compile
    # ========================================================

    return graph.compile()