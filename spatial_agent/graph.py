"""
graph.py

使用 LangGraph 构建空间转录组分析 Agent。

图结构：
START
  -> planner
  -> executor
  -> checker
  -> executor 或 reporter
  -> explainer
  -> END
"""

from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from spatial_agent.state import AgentState
from spatial_agent.tools import (
    load_h5ad_tool,
    run_qc_tool,
    preprocess_tool,
    cluster_tool,
    spatial_plot_tool,
    marker_gene_tool,
    spatial_neighborhood_tool,
)
from spatial_agent.report import generate_markdown_report

from spatial_agent.llm import get_llm

def planner_node(state: AgentState) -> AgentState:
    """
    规划节点。

    这里采用“规则执行计划 + 可选 LLM 文本计划”的混合策略：
    1. 规则计划用于保证工具调用稳定；
    2. LLM 计划用于增强 Agent 的自然语言理解和解释能力。
    """
    query = state["user_query"]

    plan = [
        "load_h5ad",
        "qc",
        "preprocess",
        "cluster",
        "spatial_plot",
        # "spatial_neighborhood",
        "marker_gene",
    ]

    if "概览" in query and "完整" not in query:
        plan = ["load_h5ad"]

    llm_plan_text = "使用默认规则计划执行基础空间转录组分析流程。"

    llm = get_llm()
    if llm is not None:
        prompt = f"""
你是一个空间转录组分析 Agent，负责将用户需求转化为分析计划。

用户需求：
{query}

系统可用工具：
1. load_h5ad：读取 .h5ad 数据并输出 obs、var、obsm 等概览
2. qc：进行质量控制，包括 cell/gene 过滤和 QC 图
3. preprocess：归一化、log 转换、高变基因筛选和标准化
4. cluster：PCA、UMAP 和 Leiden 聚类
5. spatial_plot：绘制 cluster 或基因的空间分布
6. marker_gene：进行 marker gene 分析

请生成一段简洁的中文分析计划。
要求：
- 不要编造任何尚未计算出的结果；
- 只描述将要执行的步骤；
- 说明每一步的目的；
- 输出 5 到 8 条。
"""
        try:
            response = llm.invoke(prompt)
            llm_plan_text = response.content
        except Exception as e:
            llm_plan_text = f"LLM 计划生成失败，使用默认规则计划。错误：{e}"

    return {
        **state,
        "plan": plan,
        "current_step_index": 0,
        "completed_steps": [],
        "current_data_path": state["data_path"],
        "results": [],
        "figures": [],
        "error": None,
        "retry_count": 0,
        "llm_plan_text": llm_plan_text,
    }

def executor_node(state: AgentState) -> AgentState:
    """
    执行节点。

    根据 plan 中的 current_step_index 调用对应工具。
    """
    try:
        plan = state["plan"]
        idx = state["current_step_index"]

        if idx >= len(plan):
            return state

        step = plan[idx]
        print(f"[Agent] Running step: {step}", flush=True)
        output_dir = state["output_dir"]
        current_data_path = state["current_data_path"]

        print(f"[Agent] Finished step: {step}", flush=True)
        result: Dict[str, Any]

        if step == "load_h5ad":
            result = load_h5ad_tool(
                data_path=current_data_path,
                output_dir=output_dir,
            )

        elif step == "qc":
            result = run_qc_tool(
                data_path=current_data_path,
                output_dir=output_dir,
                min_genes=200,
                min_cells=3,
                max_mito=20.0,
            )
            current_data_path = result["output_path"]

        elif step == "preprocess":
            result = preprocess_tool(
                data_path=current_data_path,
                output_dir=output_dir,
                n_top_genes=2000,
            )
            current_data_path = result["output_path"]

        elif step == "cluster":
            result = cluster_tool(
                data_path=current_data_path,
                output_dir=output_dir,
                n_pcs=30,
                resolution=0.5,
            )
            current_data_path = result["output_path"]

        elif step == "spatial_plot":
            result = spatial_plot_tool(
                data_path=current_data_path,
                output_dir=output_dir,
                color="leiden",
            )

        elif step == "marker_gene":
            result = marker_gene_tool(
                data_path=current_data_path,
                output_dir=output_dir,
                groupby="leiden",
                n_genes=10,
            )
            
        elif step == "spatial_neighborhood":
            result = spatial_neighborhood_tool(
            data_path=current_data_path,
            output_dir=output_dir,
            groupby="leiden",
            )
            
            current_data_path = result.get("output_path", current_data_path)

        else:
            raise ValueError(f"Unknown step: {step}")

        new_figures = list(state["figures"])
        if "figures" in result:
            new_figures.extend(result["figures"])

        return {
            **state,
            "current_data_path": current_data_path,
            "results": [*state["results"], result],
            "figures": new_figures,
            "completed_steps": [*state["completed_steps"], step],
            "current_step_index": idx + 1,
            "error": None,
        }

    except Exception as e:
        return {
            **state,
            "error": str(e),
            "retry_count": state["retry_count"] + 1,
        }

def checker_node(state: AgentState) -> AgentState:
    """
    检查节点。

    这里主要检查：
    1. 是否存在错误；
    2. 是否已经完成所有计划步骤。
    """
    return state

def route_after_check(state: AgentState) -> str:
    """
    条件边函数。

    根据当前状态决定下一步走向：
    - 如果有错误且重试次数小于 2，则重新执行 executor；
    - 如果还有步骤没完成，继续执行 executor；
    - 否则进入 reporter。
    """
    if state["error"] is not None and state["retry_count"] < 2:
        return "executor"

    if state["error"] is not None and state["retry_count"] >= 2:
        return "reporter"

    if state["current_step_index"] < len(state["plan"]):
        return "executor"

    return "reporter"

def reporter_node(state: AgentState) -> AgentState:
    """
    报告生成节点。
    """
    report_path = generate_markdown_report(state)

    return {
        **state,
        "final_report": report_path,
    }

def explainer_node(state: AgentState) -> AgentState:
    """
    结果解释节点。

    如果配置了 LLM，则基于工具执行结果生成解释；
    如果没有 LLM，则使用模板解释。
    """
    llm_explanation = ""

    if state["error"]:
        final_answer = (
            "分析流程执行过程中出现错误，已生成当前可用结果。"
            f"错误信息：{state['error']}。"
            f"报告路径：{state['final_report']}"
        )
        return {
            **state,
            "final_answer": final_answer,
            "llm_explanation": llm_explanation,
        }

    llm = get_llm()

    if llm is not None:
        prompt = f"""
你是一个谨慎的空间转录组数据分析助手。
下面是 Agent 已完成的分析步骤和工具返回结果。

用户需求：
{state['user_query']}

完成步骤：
{state['completed_steps']}

工具结果：
{state['results']}

生成图表：
{state['figures']}

请用中文生成简要结果解释。
要求：
1. 只能基于给出的结果进行描述；
2. 不要编造具体生物学机制；
3. 可以说明 QC、聚类、空间分布和 marker gene 结果的用途；
4. 如果结果中没有具体生物学注释，不要强行解释细胞类型；
5. 语言适合写入课程作业报告。
"""
        try:
            response = llm.invoke(prompt)
            llm_explanation = response.content
        except Exception as e:
            llm_explanation = f"LLM 解释生成失败：{e}"

    if not llm_explanation:
        llm_explanation = (
            "本次分析完成了空间转录组数据的基础流程，包括数据读取、质量控制、"
            "预处理、降维聚类、空间分布可视化和 marker gene 分析。"
            "这些结果可用于评估数据质量、观察细胞或 spot 的聚类结构，"
            "并初步识别不同 cluster 的代表性基因。"
            "需要注意的是，marker gene 的生物学含义仍需结合文献和数据库进一步验证。"
        )

    final_answer = (
        "空间转录组基础分析已完成。"
        f"共完成步骤：{', '.join(state['completed_steps'])}。"
        f"共生成 {len(state['figures'])} 个图表。"
        f"分析报告已保存至：{state['final_report']}。\n\n"
        f"结果解释：\n{llm_explanation}"
    )

    return {
        **state,
        "final_answer": final_answer,
        "llm_explanation": llm_explanation,
    }

def build_graph():
    """
    构建并编译 LangGraph。
    """
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("checker", checker_node)
    graph.add_node("reporter", reporter_node)
    graph.add_node("explainer", explainer_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "checker")

    graph.add_conditional_edges(
        "checker",
        route_after_check,
        {
            "executor": "executor",
            "reporter": "reporter",
        },
    )

    graph.add_edge("reporter", "explainer")
    graph.add_edge("explainer", END)

    return graph.compile()