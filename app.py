"""
app.py
Streamlit 前端界面 - 让助教能直接上传文件并运行 Agent
"""

import streamlit as st
import subprocess
import tempfile
import os
import shutil
from pathlib import Path

# 页面设置
st.set_page_config(page_title="空间转录组分析 Agent", layout="wide")
st.title("🧬 空间转录组分析 Agent (LangGraph)")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置")
    query = st.text_area("分析需求", value="完整分析", height=100)
    output_dir = st.text_input("输出目录", value="outputs_streamlit")
    
    uploaded_file = st.file_uploader("📤 上传 .h5ad 文件", type=["h5ad"])
    
    run_btn = st.button("🚀 运行分析", type="primary", use_container_width=True)

# 主区域
if run_btn:
    if uploaded_file is None:
        st.error("请先上传一个 .h5ad 文件！")
    else:
        # 1. 保存上传的文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix=".h5ad") as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        
        # 2. 构建命令行（直接调用你的 main.py）
        cmd = [
            "python", "main.py",
            "--data", tmp_path,
            "--query", query,
            "--output", output_dir
        ]
        
        st.info(f"正在运行: {' '.join(cmd)}")
        
        # 3. 执行并显示日志
        with st.spinner("⏳ Agent 正在分析中，请稍候..."):
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 4. 显示运行日志
        with st.expander("📄 查看运行日志", expanded=True):
            if result.stdout:
                st.code(result.stdout, language="bash")
            if result.stderr:
                st.warning("运行警告/错误：")
                st.code(result.stderr, language="bash")
        
        # 5. 清理临时文件
        os.unlink(tmp_path)
        
        # 6. 展示生成的图表
        fig_dir = Path(output_dir) / "figures"
        if fig_dir.exists():
            st.success(f"✅ 分析完成！共生成 {len(list(fig_dir.glob('*.png')))} 张图表")
            
            # 网格展示图片
            cols = st.columns(3)
            for idx, img_path in enumerate(fig_dir.glob("*.png")):
                with cols[idx % 3]:
                    st.image(str(img_path), caption=img_path.name, use_container_width=True)
        else:
            st.warning("未找到输出图表，请检查日志中的错误。")