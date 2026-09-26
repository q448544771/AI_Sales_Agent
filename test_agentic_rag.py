from langchain_core.messages import HumanMessage

from app.agent.executor import execute_agent


messages = [

    HumanMessage(

        content="""
某新能源汽车结构件企业近期新增了机器人焊接生产工位，
同时正在招聘自动化工程师和质量检测工程师。

请分析这个企业可能存在的机器视觉质检机会，
并结合我们公司的产品能力给出具体切入方案。
"""

    )

]


result = execute_agent(
    messages
)


print(
    "\n========== Final Result ==========\n"
)


print(
    result.content
)