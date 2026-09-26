from app.mcp.adapter import (
    load_knowledge_langchain_tools_sync,
)



tools = (
    load_knowledge_langchain_tools_sync()
)



print(
    "\n========== Knowledge LangChain Tools ==========\n"
)


print(
    [
        tool.name
        for tool in tools
    ]
)



knowledge_tool = next(

    tool

    for tool in tools

    if tool.name
    ==
    "search_product_knowledge"

)



print(
    "\n========== Knowledge Tool Call ==========\n"
)


result = knowledge_tool.invoke(

    {

        "query":
            "新能源汽车结构件有哪些机器视觉检测方案"

    }

)



print(result)