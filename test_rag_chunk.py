from app.knowledge.loaders.document_loader import load_documents

from app.knowledge.loaders.text_splitter import split_documents



docs = load_documents(
    "app/knowledge/data"
)


print(
    "原始Document数量:",
    len(docs)
)



chunks = split_documents(
    docs
)


print(
    "切片数量:",
    len(chunks)
)



for i, chunk in enumerate(chunks):

    print("================")

    print(
        "Chunk:",
        i
    )

    print(
        "Length:",
        len(chunk.page_content)
    )

    print(
        chunk.page_content
    )
