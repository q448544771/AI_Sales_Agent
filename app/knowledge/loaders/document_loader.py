from pathlib import Path

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader
)


def load_documents(data_path):

    """
    加载知识库文档

    支持:
    txt
    md
    pdf
    """

    documents = []


    path = Path(data_path)


    for file in path.rglob("*"):


        if file.suffix in [
            ".txt",
            ".md"
        ]:

            loader = TextLoader(
                str(file),
                encoding="utf-8"
            )

            docs = loader.load()


        elif file.suffix == ".pdf":

            loader = PyPDFLoader(
                str(file)
            )

            docs = loader.load()


        else:

            continue


        for doc in docs:

            doc.metadata["source"] = str(file)


        documents.extend(
            docs
        )


    return documents