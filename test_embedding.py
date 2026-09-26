from app.knowledge.embeddings.embedding_model import get_embedding_model



embedding = get_embedding_model()



text = "汽车零部件外观缺陷检测"



vector = embedding.embed_query(
    text
)



print(
    "向量长度:",
    len(vector)
)


print(
    vector[:10]
)