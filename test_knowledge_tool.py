from app.tools.knowledge_tools import (
    search_product_knowledge,
)



# ============================================================
# 测试产品知识库Tool
# ============================================================

result = search_product_knowledge.invoke(

    {

        "query":
            "新能源汽车结构件有哪些机器视觉检测方案"

    }

)



print(
    "\n========== Knowledge Tool Test ==========\n"
)


print(
    "Success:",
    result.get(
        "success"
    )
)


print(
    "Query:",
    result.get(
        "query"
    )
)


print(
    "Count:",
    result.get(
        "count"
    )
)



print(
    "\n========== Results ==========\n"
)



for index, item in enumerate(

    result.get(
        "results",
        []
    ),

    start=1

):

    print(
        f"Result {index}"
    )


    print(
        "Source:",
        item.get(
            "source"
        )
    )


    print(
        "Content:"
    )


    print(
        item.get(
            "content"
        )
    )


    print(
        "------------------------------"
    )