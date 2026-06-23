"""
llm.py

封装可选的大模型调用。
如果没有配置 API key，系统会自动退回到规则模式。
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# 获取项目根目录（假设 llm.py 在 spatial_agent/ 子目录下）
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"

# 显式加载 .env 文件
load_dotenv(dotenv_path=env_path)

def get_llm():
    """
    获取 LLM 对象。
    如果没有 OPENAI_API_KEY，则返回 None。
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "deepseek-chat")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")

    if not api_key:
        return None

    try:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
        )
    except Exception as e:
        print(f"Warning: failed to initialize LLM: {e}")
        return None