from app.knowledge.embeddings.embedding_model import (
    get_embedding_model
)

from app.knowledge.vectorstore.chroma_store import (
    load_vectorstore
)



def get_product_retriever():

    """
    产品知识Retriever
    """

    embedding = get_embedding_model()


    vectorstore = load_vectorstore(
        embedding
    )


    retriever = vectorstore.as_retriever(

        search_kwargs={
            "k":3
        }

    )


    return retriever