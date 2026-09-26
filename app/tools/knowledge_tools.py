from langchain_core.tools import tool


from app.knowledge.retriever.product_retriever import (
    get_product_retriever,
)



# ============================================================
# 产品知识库检索Tool
# ============================================================

@tool
def search_product_knowledge(
    query: str
):

    """
    查询企业内部产品知识库。

    适用于需要了解以下内容时：

    - 产品能力
    - 产品参数
    - 适用行业
    - 检测场景
    - 行业解决方案
    - 客户案例
    - 产品优势
    - 销售切入方案

    Args:
        query:
            需要查询的产品、行业、场景或解决方案问题。

            例如：

            "新能源汽车结构件焊缝视觉检测方案"

            "汽车零部件表面缺陷检测"

            "工业机器视觉尺寸检测能力"

    Returns:
        与问题最相关的企业内部知识。
    """


    # ========================================================
    # 参数清理
    # ========================================================

    query = (
        query
        or
        ""
    ).strip()



    # ========================================================
    # 参数校验
    # ========================================================

    if not query:

        return {

            "success":
                False,

            "message":
                "知识库查询内容不能为空",

            "query":
                query,

            "results":
                [],

        }



    # ========================================================
    # 获取知识库Retriever
    # ========================================================

    retriever = (
        get_product_retriever()
    )



    # ========================================================
    # 执行语义检索
    # ========================================================

    documents = retriever.invoke(
        query
    )



    # ========================================================
    # LangChain Document
    #
    # ↓
    #
    # JSON友好的Python数据
    # ========================================================

    results = []


    for document in documents:


        results.append(

            {

                "content":
                    document.page_content,

                "source":
                    document.metadata.get(
                        "source"
                    ),

                "metadata":
                    dict(
                        document.metadata
                    ),

            }

        )



    # ========================================================
    # 返回标准结构
    # ========================================================

    return {

        "success":
            True,

        "query":
            query,

        "count":
            len(results),

        "results":
            results,

    }