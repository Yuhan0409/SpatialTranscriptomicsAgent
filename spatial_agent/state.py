"""
state.py

定义 LangGraph Agent 的状态。
状态用于在不同节点之间传递信息。
"""

from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    空间转录组分析 Agent 的状态对象。

    字段说明：
    - user_query: 用户自然语言需求；
    - data_path: 输入 h5ad 文件路径；
    - output_dir: 输出目录；
    - plan: Agent 生成的分析计划；
    - current_step_index: 当前执行到第几步；
    - completed_steps: 已完成步骤；
    - current_data_path: 当前最新 h5ad 文件路径；
    - results: 每个工具返回的结果；
    - figures: 所有生成图表路径；
    - error: 当前错误信息；
    - retry_count: 错误重试次数；
    - final_report: 最终报告路径或文本；
    - final_answer: 最终返回给用户的总结。
    """
    user_query: str
    data_path: str
    output_dir: str

    plan: List[str]
    current_step_index: int
    completed_steps: List[str]

    current_data_path: str
    results: List[Dict[str, Any]]
    figures: List[str]

    error: Optional[str]
    retry_count: int

    final_report: str
    final_answer: str
    
    llm_plan_text: str
    llm_explanation: str