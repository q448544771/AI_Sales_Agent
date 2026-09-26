from pathlib import Path

from langchain_chroma import Chroma



def create_vectorstore(
    documents,
    embedding_model,
    persist_directory="app/knowledge/vector_db"
):

    """
    创建新的Chroma向量库
    """


    Path(
        persist_directory
    ).mkdir(
        parents=True,
        exist_ok=True
    )


    vectorstore = Chroma.from_documents(

        documents=documents,

        embedding=embedding_model,

        persist_directory=persist_directory

    )


    return vectorstore




def load_vectorstore(

    embedding_model,

    persist_directory="app/knowledge/vector_db"

):

    """
    加载已有Chroma数据库
    """


    vectorstore = Chroma(

        persist_directory=persist_directory,

        embedding_function=embedding_model

    )


    return vectorstore