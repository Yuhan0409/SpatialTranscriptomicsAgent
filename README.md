# Spatial Transcriptomics Analysis Agent

基于 LangGraph 构建的空间转录组数据分析智能体。用户可以通过自然语言描述分析需求，Agent 自动规划并执行 `.h5ad` 数据读取、质量控制、预处理、降维聚类、空间可视化、Marker Gene 分析和 Markdown 报告生成。

## 1. Project Structure
'''
spatial_agent_project/
├── main.py
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── README.md
├── docs/
│   ├── design.md
│   ├── report_outline.md
│   └── example_outputs/
├── examples/
│   └── example_queries.md
├── scripts/
│   ├── inspect_h5ad.py
│   └── make_small_h5ad.py
└── spatial_agent/
    ├── state.py
    ├── tools.py
    ├── graph.py
    ├── report.py
    ├── llm.py
    ├── prompts.py
    ├── utils.py
    └── __init__.py
'''

## 2. Environment Setup
建议使用 Python 3.10。

conda create -n spatial-agent python=3.10 -y
conda activate spatial-agent
pip install -r requirements.txt

## 3. Data Preparation
本仓库不直接上传大型 .h5ad 数据文件。请自行准备 AnnData 格式的空间转录组数据，并放入 data/ 目录，例如：

data/example.h5ad
本项目测试使用的数据来源包括：

Scanpy PBMC3K 测试数据加模拟空间坐标
GSE278603: Digital reconstruction of full embryos during early mouse organogenesis
Example sample: GSM9046245_Embryo_E7.75_stereo_rep1.h5ad
如果原始数据较大，可以使用脚本裁剪小样本：

python scripts/make_small_h5ad.py --input "path/to/raw_data.h5ad" --output "data/example.h5ad" --n_obs 5000 --n_vars 3000
检查 .h5ad 数据结构：

python scripts/inspect_h5ad.py --data "data/example.h5ad"

## 4. Run the Agent
在项目根目录运行：

python main.py --data "data/example.h5ad" --query "请对该空间转录组数据进行完整基础分析，包括数据概览、质量控制、预处理、UMAP降维、Leiden聚类、空间可视化和marker gene分析" --output "outputs"
参数说明：

--data: 输入 .h5ad 文件路径
--query: 用户自然语言分析需求
--output: 输出目录，默认为 outputs

## 5. Outputs
运行完成后会生成：

outputs/
├── figures/
│   ├── qc_violin.png
│   ├── qc_scatter.png
│   ├── highly_variable_genes.png
│   ├── pca_variance_ratio.png
│   ├── umap_leiden.png
│   ├── spatial_leiden.png
│   └── marker_genes_rank.png
├── processed/
└── reports/
    ├── analysis_report.md
    ├── data_summary.txt
    └── marker_genes.csv
示例结果图见：

docs/example_outputs/

## 6. Optional LLM Configuration
本项目支持可选的大模型调用，用于生成自然语言分析计划和结果解释。没有 API key 时，系统会自动回退到规则计划和模板解释模式。

请在本地创建 .env 文件：

OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
注意：.env 包含密钥，不应上传到 GitHub。仓库中只保留 .env.example。

## 7. Streamlit Interface
如果需要使用网页界面：

streamlit run app.py
8. Agent Workflow
LangGraph 工作流包括：

START
  -> planner
  -> executor
  -> checker
  -> reporter
  -> explainer
  -> END
主要模块：

state.py: 定义 Agent 状态
tools.py: 封装 Scanpy 分析工具
graph.py: 定义 LangGraph 节点与流程
report.py: 生成 Markdown 分析报告
llm.py: 可选 LLM 调用封装

## 9. Notes
本仓库不包含大型 .h5ad 数据文件。
若输入数据不包含空间坐标，空间可视化步骤会自动跳过。
Marker gene 结果仅作为初步统计分析，需要结合文献和数据库进一步解释。
推荐在项目根目录运行所有命令。
