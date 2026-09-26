import os


from dotenv import load_dotenv

from langchain_openai import ChatOpenAI



load_dotenv()



# ============================================================
# DeepSeek公共配置
# ============================================================

def _get_common_config() -> dict:

    """
    读取所有DeepSeek模型实例共同使用的配置。
    """


    api_key = os.getenv(
        "LLM_API_KEY"
    )


    base_url = os.getenv(
        "LLM_BASE_URL"
    )


    model_name = os.getenv(
        "LLM_MODEL"
    )


    if not api_key:

        raise ValueError(
            "缺少环境变量 LLM_API_KEY"
        )


    if not base_url:

        raise ValueError(
            "缺少环境变量 LLM_BASE_URL"
        )


    if not model_name:

        raise ValueError(
            "缺少环境变量 LLM_MODEL"
        )


    return {

        "api_key":
            api_key,

        "base_url":
            base_url,

        "model":
            model_name,

    }



# ============================================================
# Fast LLM
# ============================================================

def get_fast_llm() -> ChatOpenAI:

    """
    非思考模式模型。


    适用于：

    - 结构化输出
    - 信息抽取
    - 分类
    - 格式转换
    - 普通生成任务


    特点：

    thinking = disabled
    """


    config = (
        _get_common_config()
    )


    return ChatOpenAI(

        **config,

        extra_body={

            "thinking": {

                "type":
                    "disabled"

            }

        },

    )



# ============================================================
# Tool Calling LLM
# ============================================================

def get_tool_llm() -> ChatOpenAI:

    """
    Tool Calling专用模型。


    适用于：

    - MCP Tool Calling
    - LangChain bind_tools
    - 多轮Tool调用
    - Executor
    - Agent工具执行循环


    为什么关闭Thinking：

    DeepSeek Thinking Mode在多轮Tool Calling时，

    要求上一轮Assistant消息中的
    reasoning_content能够完整回传。


    当前ChatOpenAI兼容层没有稳定保存这一字段，

    因此在：

        Assistant
            ↓
        Tool Call
            ↓
        Tool Result
            ↓
        Assistant

    的多轮Tool Calling过程中，

    可能出现：

        reasoning_content must be passed back


    为保证Agent Tool Calling稳定性，

    Executor统一使用：

        thinking = disabled


    Planner和Reviewer仍然可以继续使用：

        get_reasoning_llm()
    """


    config = (
        _get_common_config()
    )


    return ChatOpenAI(

        **config,

        extra_body={

            "thinking": {

                "type":
                    "disabled"

            }

        },

    )



# ============================================================
# Reasoning LLM
# ============================================================

def get_reasoning_llm() -> ChatOpenAI:

    """
    思考模式模型。


    适用于：

    - Planner
    - Reviewer
    - 复杂分析
    - 销售机会判断
    - 多步骤推理


    不建议用于当前Executor的
    多轮MCP Tool Calling。


    特点：

    thinking = enabled
    """


    config = (
        _get_common_config()
    )


    return ChatOpenAI(

        **config,

        extra_body={

            "thinking": {

                "type":
                    "enabled"

            }

        },

    )



# ============================================================
# 兼容旧接口
# ============================================================

def get_llm() -> ChatOpenAI:

    """
    暂时保留，

    用于兼容之前：

        test_llm.py

    默认返回非Thinking模型。
    """


    return get_fast_llm()