from app.knowledge.retriever.product_retriever import (
    get_product_retriever
)


retriever = get_product_retriever()



docs = retriever.invoke(

    "汽车零部件有哪些视觉检测方案"

)



for i,doc in enumerate(docs):

    print("================")

    print(
        i
    )

    print(
        doc.page_content
    )