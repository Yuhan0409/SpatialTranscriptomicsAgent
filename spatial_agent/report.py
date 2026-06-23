"""
report.py

根据 Agent 执行状态生成 Markdown 报告。
"""

from pathlib import Path
from typing import Dict, Any, List

def generate_markdown_report(state: Dict[str, Any]) -> str:
    """
    生成 Markdown 格式分析报告。

    Parameters
    ----------
    state : Dict[str, Any]
        LangGraph Agent 执行结束后的状态。

    Returns
    -------
    str
        报告文件路径。
    """
    output_dir = Path(state["output_dir"])
    report_dir = output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_path = report_dir / "analysis_report.md"

    lines: List[str] = []

    lines.append("# 空间转录组分析 Agent 报告\n")
    lines.append("## 1. 用户需求\n")
    lines.append(f"{state['user_query']}\n")

    lines.append("## 2. Agent 分析计划\n")
    if state.get("llm_plan_text"):
        lines.append("### 2.1 LLM 生成的自然语言计划\n")
        lines.append(state["llm_plan_text"])
        lines.append("")

    lines.append("### 2.2 实际执行工具计划\n")
    for i, step in enumerate(state.get("plan", []), start=1):
        lines.append(f"{i}. {step}")
    lines.append("")

    lines.append("## 3. 已完成步骤\n")
    for step in state.get("completed_steps", []):
        lines.append(f"- {step}")
    lines.append("")

    lines.append("## 4. 工具执行结果摘要\n")
    for result in state.get("results", []):
        lines.append(f"### {result.get('step', 'unknown')}")
        for key, value in result.items():
            if key != "figures":
                lines.append(f"- **{key}**: {value}")
        lines.append("")

    lines.append("## 5. 生成图表\n")
    for fig in state.get("figures", []):
        lines.append(f"- {fig}")
    lines.append("")

    lines.append("## 6. 结果解释\n")
    if state.get("llm_explanation"):
        lines.append(state["llm_explanation"])
    else:
        lines.append(
            "本 Agent 根据 Scanpy/AnnData 的计算结果生成分析摘要。"
            "对于 cluster 和 marker gene，当前仅提供统计结果层面的解释，"
            "不做未经验证的具体生物学功能推断。"
        )
    lines.append("")

    lines.append("## 7. 注意事项与不足\n")
    lines.append("- 当前主要支持 `.h5ad` 格式数据。")
    lines.append("- 如果数据缺少 `obsm['spatial']`，空间可视化会被跳过。")
    lines.append("- Marker gene 结果需要结合专业数据库和文献进一步解释。")
    lines.append("- 后续可扩展空间邻域分析、空间可变基因识别和细胞通讯分析。")
    lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return str(report_path)