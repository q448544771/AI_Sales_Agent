from app.llm.model import get_llm


llm = get_llm()

response = llm.invoke(
    "请只回复一句话：AI Sales Agent 模型连接成功。"
)

print(response.content)