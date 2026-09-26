from langchain_huggingface import HuggingFaceEmbeddings



def get_embedding_model():

    model_name = (
        "BAAI/bge-small-zh-v1.5"
    )


    model_kwargs = {

        "device": "cpu"

    }


    encode_kwargs = {

        "normalize_embeddings": True

    }


    embeddings = HuggingFaceEmbeddings(

        model_name=model_name,

        model_kwargs=model_kwargs,

        encode_kwargs=encode_kwargs

    )


    return embeddings