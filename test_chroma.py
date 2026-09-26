from app.knowledge.embeddings.embedding_model import get_embedding_model

from app.knowledge.vectorstore.chroma_store import load_vectorstore



embedding = get_embedding_model()



db = load_vectorstore(

    embedding

)



results = db.similarity_search(

    "新能源汽车结构件有哪些检测方案",

    k=3

)



for i, doc in enumerate(results):

    print("================")

    print(
        "Result:",
        i
    )

    print(
        doc.page_content
    )

    print(
        doc.metadata
    )