"""
app.py
Streamlit 前端界面 - 上传 .h5ad 并运行空间转录组分析 Agent
"""

import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="空间转录组分析 Agent", layout="wide")
st.title("空间转录组分析 Agent (LangGraph)")

with st.sidebar:
    st.header("配置")

    query = st.text_area("分析需求", value="完整分析", height=100)

    base_output_dir = st.text_input("输出根目录", value="outputs_streamlit")

    use_llm = st.checkbox(
        "启用 LLM 计划与解释",
        value=False,
        help="如果不勾选，将尽量禁用 OPENAI_API_KEY，避免 API 等待导致运行变慢。",
    )

    uploaded_file = st.file_uploader("上传 .h5ad 文件", type=["h5ad"])

    run_btn = st.button("运行分析", type="primary", use_container_width=True)

def stream_process(cmd, env):
    log_box = st.empty()
    logs = []

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )

    for line in process.stdout:
        logs.append(line)
        log_box.code("".join(logs[-80:]), language="bash")

    return_code = process.wait()
    return return_code, "".join(logs)

if run_btn:
    if uploaded_file is None:
        st.error("请先上传一个 .h5ad 文件！")
        st.stop()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = str(Path(base_output_dir) / f"run_{timestamp}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".h5ad") as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    cmd = [
        sys.executable,
        "-u",
        "main.py",
        "--data",
        tmp_path,
        "--query",
        query,
        "--output",
        output_dir,
    ]

    env = os.environ.copy()

    if not use_llm:
        env["OPENAI_API_KEY"] = ""
        env["OPENAI_BASE_URL"] = ""
        env["OPENAI_MODEL"] = ""

    st.info(f"输出目录：{output_dir}")
    st.info("正在运行分析，日志会实时更新。")

    start_time = time.time()

    try:
        with st.spinner("⏳ Agent 正在分析中，请稍候..."):
            return_code, logs = stream_process(cmd, env)

        elapsed = time.time() - start_time

        if return_code != 0:
            st.error(f"分析失败，退出码：{return_code}，耗时：{elapsed:.1f} 秒")
        else:
            st.success(f"✅ 分析完成，耗时：{elapsed:.1f} 秒")

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    fig_dir = Path(output_dir) / "figures"
    report_dir = Path(output_dir) / "reports"

    if fig_dir.exists():
        image_paths = sorted(fig_dir.glob("*.png"))
        st.subheader(f"📊 生成图表：{len(image_paths)} 张")

        cols = st.columns(3)
        for idx, img_path in enumerate(image_paths):
            with cols[idx % 3]:
                st.image(str(img_path), caption=img_path.name, use_container_width=True)
    else:
        st.warning("未找到输出图表，请检查日志。")

    report_path = report_dir / "analysis_report.md"
    if report_path.exists():
        st.subheader("📄 分析报告")
        report_text = report_path.read_text(encoding="utf-8")
        st.markdown(report_text)

        st.download_button(
            label="下载分析报告",
            data=report_text,
            file_name="analysis_report.md",
            mime="text/markdown",
        )

    marker_path = report_dir / "marker_genes.csv"
    if marker_path.exists():
        st.subheader("🧬 Marker genes")
        st.download_button(
            label="下载 marker_genes.csv",
            data=marker_path.read_bytes(),
            file_name="marker_genes.csv",
            mime="text/csv",
        )