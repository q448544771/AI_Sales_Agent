from app.agent.executor import create_executor


executor = create_executor()


response = executor.invoke(
    """
    我正在寻找中国汽车零部件行业中，
    可能需要工业机器视觉质检方案的企业。

    目前应该执行什么操作？
    """
)


print(response)

print("\n========== Tool Calls ==========")

print(response.tool_calls)