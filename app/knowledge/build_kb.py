from app.knowledge.loaders.document_loader import load_documents

from app.knowledge.loaders.text_splitter import split_documents

from app.knowledge.embeddings.embedding_model import get_embedding_model

from app.knowledge.vectorstore.chroma_store import create_vectorstore



def build_kb():


    print("Loading documents...")


    docs = load_documents(

        "app/knowledge/data"

    )


    print(
        "Documents:",
        len(docs)
    )


    print("Splitting...")


    chunks = split_documents(
        docs
    )


    print(
        "Chunks:",
        len(chunks)
    )


    print("Loading embedding model...")


    embedding = get_embedding_model()



    print("Building Chroma...")


    vectorstore = create_vectorstore(

        chunks,

        embedding

    )


    print(
        "Knowledge base created!"
    )


    return vectorstore




if __name__ == "__main__":

    build_kb()