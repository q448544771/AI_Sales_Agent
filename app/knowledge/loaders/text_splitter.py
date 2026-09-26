from langchain_text_splitters import RecursiveCharacterTextSplitter



def split_documents(
    documents,
    chunk_size=800,
    chunk_overlap=150
):

    """
    文档切片

    参数:

    chunk_size:
        每个chunk最大字符数

    chunk_overlap:
        chunk之间重叠字符
    """


    splitter = RecursiveCharacterTextSplitter(

        chunk_size=chunk_size,

        chunk_overlap=chunk_overlap,

        separators=[

            "\n\n",
            "\n",
            "。",
            "，",
            " "

        ]

    )


    chunks = splitter.split_documents(
        documents
    )


    return chunks