from langchain_core.messages import HumanMessage

from app.agent.executor import execute_agent



messages = [

    HumanMessage(
        content="""
        我正在寻找中国汽车零部件行业中，
        可能需要工业机器视觉质检方案的企业。

        请自主判断下一步应该做什么。
        """
    )

]


response = execute_agent(
    messages
)


print("\n========== Final ==========")

print(response.content)