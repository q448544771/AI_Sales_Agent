import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()


def _get_common_config() -> dict:
    """
    读取所有 DeepSeek 模型实例共同使用的配置。
    """

    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model_name = os.getenv("LLM_MODEL")

    if not api_key:
        raise ValueError("缺少环境变量 LLM_API_KEY")

    if not base_url:
        raise ValueError("缺少环境变量 LLM_BASE_URL")

    if not model_name:
        raise ValueError("缺少环境变量 LLM_MODEL")

    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model_name,
    }


def get_fast_llm() -> ChatOpenAI:
    """
    非思考模式模型。

    适用于：
    - 结构化输出
    - 信息抽取
    - 分类
    - 格式转换
    - 需要强约束 Function Calling 的任务
    """

    config = _get_common_config()

    return ChatOpenAI(
        **config,
        extra_body={
            "thinking": {
                "type": "disabled"
            }
        },
    )


def get_reasoning_llm() -> ChatOpenAI:
    """
    思考模式模型。

    适用于：
    - 复杂分析
    - Review
    - 销售机会判断
    - 自主 Tool Calling
    """

    config = _get_common_config()

    return ChatOpenAI(
        **config,
        extra_body={
            "thinking": {
                "type": "enabled"
            }
        },
    )


# 暂时保留，兼容之前 test_llm.py
def get_llm() -> ChatOpenAI:
    return get_fast_llm()