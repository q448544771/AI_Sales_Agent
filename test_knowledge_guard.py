from langchain_core.messages import HumanMessage

from app.agent.executor import execute_agent



messages = [

    HumanMessage(

        content="""

请基于我们公司的内部产品知识库回答下面几个问题：

1. 我司是否支持新能源汽车结构件焊缝视觉检测？

2. 我司焊缝检测的检出率是否达到99.9%？

3. 我司方案是否通过IATF 16949认证？

4. 我司是否已有明确的焊缝检测ROI数据？

5. 我司是否已有具体的焊缝检测POC成功案例？

要求：

只能把内部知识库明确提供的信息描述为我司已有能力。

知识库没有提供的信息必须明确说明“当前知识库未提供”，
不能自行补充。

"""

    )

]



result = execute_agent(
    messages
)



print(
    "\n========== Knowledge Guard Result ==========\n"
)


print(
    result.content
)