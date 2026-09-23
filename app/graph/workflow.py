from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langgraph.prebuilt import ToolNode


# 状态定义
from app.agent.state import SalesAgentState


# Agent节点
from app.agent.planner import planning_node
from app.agent.executor import executor_node
from app.agent.reviewer import review_node

# Memory相关
from app.agent.memory import memory_node
from app.agent.memory_retriever import memory_retrieval_node

# Follow-up销售动作
from app.agent.followup import followup_node



# ==============================
# Tools
# ==============================

from app.tools.company_tools import (
    search_companies,
    search_company_news,
    search_company_jobs
)


from app.tools.crm_tools import (
    query_leads,
    update_lead_stage
)

# Executor可调用工具

tools = [

    # 企业搜索
    search_companies,


    # 新闻动态
    search_company_news,


    # 招聘信息
    search_company_jobs,


    # CRM历史客户查询
    query_leads,

    # CRM更新
    update_lead_stage

]



# ==============================
# Executor路由判断
# ==============================


def should_continue(
    state: SalesAgentState
):

    """
    判断Executor下一步：

    有tool_calls:
        Executor -> Tools


    无tool_calls:
        Executor -> Review

    """


    messages = state.get(
        "messages",
        []
    )


    if not messages:

        return "review"



    last_message = messages[-1]


    # LLM请求调用工具

    if getattr(
        last_message,
        "tool_calls",
        None
    ):

        return "tools"



    # 信息收集完成

    return "review"





# ==============================
# 创建Graph
# ==============================


def create_graph():

    """
    Sales Agent 工作流:

    
    START

      ↓

    Memory Retrieval
    历史客户记忆检索

      ↓

    Planner
    制定销售调研计划

      ↓

    Executor
    Agent自主决策


      ↓ tool_calls

    Tools

      ↓

    Executor循环


      ↓

    Review

      ↓

    Memory

      ↓

    Follow-up

      ↓

    END


    """



    graph = StateGraph(
        SalesAgentState
    )



    # ==========================
    # Nodes
    # ==========================


    # 历史记忆检索

    graph.add_node(

        "memory_retrieval",

        memory_retrieval_node

    )



    # 任务规划

    graph.add_node(

        "planner",

        planning_node

    )



    # Agent执行

    graph.add_node(

        "executor",

        executor_node

    )



    # Tool执行

    graph.add_node(

        "tools",

        ToolNode(tools)

    )



    # 客户评估

    graph.add_node(

        "review",

        review_node

    )



    # CRM记忆保存

    graph.add_node(

        "memory",

        memory_node

    )



    # 销售跟进任务生成

    graph.add_node(

        "followup",

        followup_node

    )





    # ==========================
    # Fixed Edges
    # ==========================


    # START
    # ↓
    # Memory Retrieval


    graph.add_edge(

        START,

        "memory_retrieval"

    )



    # Memory Retrieval

    graph.add_edge(

        "memory_retrieval",

        "planner"

    )



    # Planner

    graph.add_edge(

        "planner",

        "executor"

    )



    # Tool执行完成

    graph.add_edge(

        "tools",

        "executor"

    )



    # Review

    graph.add_edge(

        "review",

        "memory"

    )



    # Memory

    graph.add_edge(

        "memory",

        "followup"

    )



    # Follow-up

    graph.add_edge(

        "followup",

        END

    )





    # ==========================
    # Conditional Edge
    # ==========================


    graph.add_conditional_edges(

        "executor",

        should_continue,

        {


            "tools":

            "tools",



            "review":

            "review"

        }

    )




    return graph.compile()