from app.knowledge.loaders.document_loader import load_documents


docs = load_documents(
    "app/knowledge/data"
)


print(
    "文档数量:",
    len(docs)
)


for doc in docs:

    print("================")

    print(
        doc.metadata
    )

    print(
        doc.page_content[:200]
    )