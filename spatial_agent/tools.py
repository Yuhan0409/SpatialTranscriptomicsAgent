"""
tools.py

本文件封装空间转录组分析中的核心工具函数。
这些函数会被 LangGraph Agent 的 executor 节点调用。

设计原则：
1. 每个工具只负责一个明确步骤；
2. 每个工具接收文件路径和参数，返回结构化摘要；
3. 每个工具会将中间结果保存到 outputs 目录；
4. 如果出错，抛出异常，由 LangGraph 的 checker 节点处理。
"""

from pathlib import Path
from typing import Dict, Any, List, Optional

import scanpy as sc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def get_spatial_coordinates(adata):
    """
    自动识别 AnnData 中的空间坐标。
    不同空间转录组平台保存坐标的字段可能不同。
    """
    if "spatial" in adata.obsm:
        return adata.obsm["spatial"], "obsm['spatial']"

    if "X_spatial" in adata.obsm:
        return adata.obsm["X_spatial"], "obsm['X_spatial']"

    candidates = [
        ("x", "y"),
        ("X", "Y"),
        ("spatial_x", "spatial_y"),
        ("coord_x", "coord_y"),
        ("array_col", "array_row"),
        ("imagecol", "imagerow"),
        ("row", "col"),
    ]

    for x_col, y_col in candidates:
        if x_col in adata.obs.columns and y_col in adata.obs.columns:
            return adata.obs[[x_col, y_col]].values, f"obs[['{x_col}', '{y_col}']]"

    return None, None

def ensure_output_dirs(output_dir: str) -> Dict[str, Path]:
    """
    创建输出目录。

    Parameters
    ----------
    output_dir : str
        用户指定的输出根目录。

    Returns
    -------
    Dict[str, Path]
        包含 figures、reports、processed 三个目录路径。
    """
    root = Path(output_dir)
    fig_dir = root / "figures"
    report_dir = root / "reports"
    processed_dir = root / "processed"

    fig_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    return {
        "root": root,
        "figures": fig_dir,
        "reports": report_dir,
        "processed": processed_dir,
    }

def load_h5ad_tool(data_path: str, output_dir: str) -> Dict[str, Any]:
    """
    读取 h5ad 文件并输出数据概览。

    功能：
    1. 读取 AnnData；
    2. 检查 obs、var、obsm；
    3. 判断是否存在空间坐标；
    4. 返回数据基本信息。
    """
    dirs = ensure_output_dirs(output_dir)

    adata = sc.read_h5ad(data_path)
    
    coords, spatial_source = get_spatial_coordinates(adata)
    has_spatial = coords is not None
    
    summary = {
        "step": "load_h5ad",
        "status": "success",
        "input_path": data_path,
        "n_obs": int(adata.n_obs),
        "n_vars": int(adata.n_vars),
        "obs_columns": list(adata.obs.columns),
        "var_columns": list(adata.var.columns),
        "obsm_keys": list(adata.obsm.keys()),
        "has_spatial": has_spatial,
        "spatial_source": spatial_source,
    }

    # 保存一份原始数据副本路径记录，不强制重写大文件
    summary_path = dirs["reports"] / "data_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("Data Summary\n")
        f.write("====================\n")
        for k, v in summary.items():
            f.write(f"{k}: {v}\n")

    summary["summary_file"] = str(summary_path)

    return summary

def run_qc_tool(
    data_path: str,
    output_dir: str,
    min_genes: int = 200,
    min_cells: int = 3,
    max_mito: float = 20.0,
) -> Dict[str, Any]:
    """
    执行质量控制。

    QC 内容：
    1. 计算每个 cell/spot 的 total_counts；
    2. 计算 n_genes_by_counts；
    3. 如果是小鼠/人类基因名，识别线粒体基因；
    4. 过滤低质量 cell/spot 和低表达 gene；
    5. 绘制 QC 图；
    6. 保存过滤后的 h5ad。
    """
    dirs = ensure_output_dirs(output_dir)
    adata = sc.read_h5ad(data_path)

    before_n_obs = adata.n_obs
    before_n_vars = adata.n_vars

    # 识别线粒体基因
    # 人类通常以 MT- 开头，小鼠通常以 mt- 开头
    var_names = adata.var_names.astype(str)
    adata.var["mt"] = var_names.str.startswith("MT-") | var_names.str.startswith("mt-")

    # 计算 QC 指标
    sc.pp.calculate_qc_metrics(
        adata,
        qc_vars=["mt"],
        percent_top=None,
        log1p=False,
        inplace=True,
    )

    # 绘制 QC 小提琴图
    qc_violin_path = dirs["figures"] / "qc_violin.png"
    sc.pl.violin(
        adata,
        ["n_genes_by_counts", "total_counts", "pct_counts_mt"],
        jitter=0.4,
        multi_panel=True,
        show=False,
    )
    plt.savefig(qc_violin_path, dpi=150, bbox_inches="tight")
    plt.close()

    # 绘制 QC 散点图
    qc_scatter_path = dirs["figures"] / "qc_scatter.png"
    sc.pl.scatter(
        adata,
        x="total_counts",
        y="pct_counts_mt",
        show=False,
    )
    plt.savefig(qc_scatter_path, dpi=150, bbox_inches="tight")
    plt.close()

    # 执行过滤
    sc.pp.filter_cells(adata, min_genes=min_genes)
    sc.pp.filter_genes(adata, min_cells=min_cells)
    adata = adata[adata.obs["pct_counts_mt"] < max_mito].copy()

    after_n_obs = adata.n_obs
    after_n_vars = adata.n_vars

    output_path = dirs["processed"] / "qc_filtered.h5ad"
    adata.write_h5ad(output_path)

    return {
        "step": "qc",
        "status": "success",
        "input_path": data_path,
        "output_path": str(output_path),
        "before_n_obs": int(before_n_obs),
        "before_n_vars": int(before_n_vars),
        "after_n_obs": int(after_n_obs),
        "after_n_vars": int(after_n_vars),
        "min_genes": min_genes,
        "min_cells": min_cells,
        "max_mito": max_mito,
        "figures": [str(qc_violin_path), str(qc_scatter_path)],
    }

def preprocess_tool(
    data_path: str,
    output_dir: str,
    n_top_genes: int = 3000,
) -> Dict[str, Any]:
    """
    执行基础预处理。

    步骤：
    1. normalize_total；
    2. log1p；
    3. highly_variable_genes；
    4. scale；
    5. 保存预处理后的 h5ad。
    """
    dirs = ensure_output_dirs(output_dir)
    adata = sc.read_h5ad(data_path)

    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    # 高变基因筛选
    sc.pp.highly_variable_genes(
        adata,
        n_top_genes=n_top_genes,
        flavor="seurat_v3",          # 对低 UMI 数据更友好
        batch_key=None,
    )

    hvg_path = dirs["figures"] / "highly_variable_genes.png"
    sc.pl.highly_variable_genes(adata, show=False)
    plt.savefig(hvg_path, dpi=150, bbox_inches="tight")
    plt.close()

    # 保存原始 log-normalized 数据
    adata.raw = adata

    # 只保留高变基因用于后续 PCA
    adata = adata[:, adata.var["highly_variable"]].copy()

    if hasattr(adata.X, "toarray"):
        adata.X = adata.X.toarray()

    sc.pp.scale(adata, max_value=10)

    output_path = dirs["processed"] / "preprocessed.h5ad"
    adata.write_h5ad(output_path)

    return {
        "step": "preprocess",
        "status": "success",
        "input_path": data_path,
        "output_path": str(output_path),
        "n_top_genes": n_top_genes,
        "n_obs": int(adata.n_obs),
        "n_vars_after_hvg": int(adata.n_vars),
        "figures": [str(hvg_path)],
    }

def cluster_tool(
    data_path: str,
    output_dir: str,
    n_pcs: int = 30,
    resolution: float = 0.5,
) -> Dict[str, Any]:
    """
    执行 PCA、邻居图、UMAP 和 Leiden 聚类。
    """
    dirs = ensure_output_dirs(output_dir)
    adata = sc.read_h5ad(data_path)

    # PCA
    sc.tl.pca(adata, svd_solver="arpack", n_comps=n_pcs)

    pca_path = dirs["figures"] / "pca_variance_ratio.png"
    sc.pl.pca_variance_ratio(adata, log=True, show=False)
    plt.savefig(pca_path, dpi=150, bbox_inches="tight")
    plt.close()

    # 邻居图 + UMAP
    sc.pp.neighbors(adata, n_neighbors=15, n_pcs=n_pcs)
    sc.tl.umap(adata)

    # Leiden 聚类
    sc.tl.leiden(adata, resolution=resolution, key_added="leiden")

    umap_path = dirs["figures"] / "umap_leiden.png"
    sc.pl.umap(adata, color="leiden", show=False)
    plt.savefig(umap_path, dpi=150, bbox_inches="tight")
    plt.close()

    output_path = dirs["processed"] / "clustered.h5ad"
    adata.write_h5ad(output_path)

    n_clusters = adata.obs["leiden"].nunique()

    return {
        "step": "cluster",
        "status": "success",
        "input_path": data_path,
        "output_path": str(output_path),
        "n_pcs": n_pcs,
        "resolution": resolution,
        "n_clusters": int(n_clusters),
        "figures": [str(pca_path), str(umap_path)],
    }

def spatial_plot_tool(
    data_path: str,
    output_dir: str,
    color: str = "leiden",
    gene: Optional[str] = None,
) -> Dict[str, Any]:
    """
    绘制空间分布图。

    说明：
    - 如果 AnnData 中存在 obsm['spatial']，使用 matplotlib 画空间散点图；
    - color 可以是 obs 中的列，例如 leiden/cell_type；
    - gene 可以是某个基因名，用于绘制基因空间表达。
    """
    dirs = ensure_output_dirs(output_dir)
    adata = sc.read_h5ad(data_path)

    coords, spatial_source = get_spatial_coordinates(adata)
    if coords is None:
        return {
            "step": "spatial_plot",
            "status": "skipped",
            "reason": "No spatial coordinates found in any supported format",
            "figures": [],
        }

    x = coords[:, 0]
    y = coords[:, 1]

    figures = []

    # 画 cluster 或 obs 字段空间分布
    if color in adata.obs.columns:
        fig_path = dirs["figures"] / f"spatial_{color}.png"

        categories = adata.obs[color].astype("category")
        codes = categories.cat.codes

        plt.figure(figsize=(6, 5))
        scatter = plt.scatter(x, y, c=codes, s=5, cmap="tab20")
        plt.title(f"Spatial distribution colored by {color}")
        plt.xlabel("spatial x")
        plt.ylabel("spatial y")
        plt.gca().invert_yaxis()
        plt.colorbar(scatter, label=color)
        plt.tight_layout()
        plt.savefig(fig_path, dpi=150)
        plt.close()

        figures.append(str(fig_path))

    # 画 gene 空间表达
    if gene is not None:
        if gene in adata.var_names:
            fig_path = dirs["figures"] / f"spatial_gene_{gene}.png"

            expr = adata[:, gene].X
            if hasattr(expr, "toarray"):
                expr = expr.toarray().flatten()
            else:
                expr = np.asarray(expr).flatten()

            plt.figure(figsize=(6, 5))
            scatter = plt.scatter(x, y, c=expr, s=5, cmap="viridis")
            plt.title(f"Spatial expression of {gene}")
            plt.xlabel("spatial x")
            plt.ylabel("spatial y")
            plt.gca().invert_yaxis()
            plt.colorbar(scatter, label="expression")
            plt.tight_layout()
            plt.savefig(fig_path, dpi=150)
            plt.close()

            figures.append(str(fig_path))
        else:
            return {
                "step": "spatial_plot",
                "status": "partial_success",
                "reason": f"Gene {gene} not found in adata.var_names",
                "figures": figures,
            }

    return {
        "step": "spatial_plot",
        "status": "success",
        "input_path": data_path,
        "color": color,
        "gene": gene,
        "figures": figures,
    }

def marker_gene_tool(
    data_path: str,
    output_dir: str,
    groupby: str = "leiden",
    n_genes: int = 10,
) -> Dict[str, Any]:
    """
    进行 marker gene 分析。

    使用 scanpy.tl.rank_genes_groups 对不同 cluster 做差异基因分析。
    """
    dirs = ensure_output_dirs(output_dir)
    adata = sc.read_h5ad(data_path)

    if groupby not in adata.obs.columns:
        raise ValueError(f"groupby={groupby} not found in adata.obs")

    sc.tl.rank_genes_groups(
        adata,
        groupby=groupby,
        method="wilcoxon",
    )

    # 保存 marker gene 图
    marker_plot_path = dirs["figures"] / "marker_genes_rank.png"
    sc.pl.rank_genes_groups(adata, n_genes=n_genes, sharey=False, show=False)
    plt.savefig(marker_plot_path, dpi=150, bbox_inches="tight")
    plt.close()

    # 提取 marker gene 表
    result = adata.uns["rank_genes_groups"]
    groups = result["names"].dtype.names

    rows = []
    for group in groups:
        for i in range(n_genes):
            rows.append({
                "cluster": group,
                "rank": i + 1,
                "gene": result["names"][group][i],
                "score": result["scores"][group][i],
                "pvals_adj": result["pvals_adj"][group][i],
                "logfoldchanges": result["logfoldchanges"][group][i],
            })

    marker_df = pd.DataFrame(rows)

    marker_csv_path = dirs["reports"] / "marker_genes.csv"
    marker_df.to_csv(marker_csv_path, index=False)

    output_path = dirs["processed"] / "clustered_with_markers.h5ad"
    adata.write_h5ad(output_path)

    return {
        "step": "marker_gene",
        "status": "success",
        "input_path": data_path,
        "output_path": str(output_path),
        "groupby": groupby,
        "n_genes": n_genes,
        "marker_csv": str(marker_csv_path),
        "figures": [str(marker_plot_path)],
    }
    
def spatial_neighborhood_tool(
    data_path: str,
    output_dir: str,
    groupby: str = "leiden",
) -> Dict[str, Any]:
    
    try:
        import squidpy as sq
    except ImportError:
        return {
            "step": "spatial_neighborhood",
            "status": "skipped",
            "reason": "Squidpy not installed. Run: pip install squidpy",
            "figures": [],
        }

    dirs = ensure_output_dirs(output_dir)
    adata = sc.read_h5ad(data_path)

    # 1. 检查是否有空间坐标
    coords, source = get_spatial_coordinates(adata)  # 使用你之前写的辅助函数
    if coords is None:
        return {
            "step": "spatial_neighborhood",
            "status": "skipped",
            "reason": "No spatial coordinates found",
            "figures": [],
        }

    # 2. 计算空间邻接矩阵（如果已有 neighbors，会跳过）
    sq.gr.spatial_neighbors(adata, coord_type="generic")

    # 3. 计算邻域富集（Permutation test）
    sq.gr.nhood_enrichment(adata, groupby=groupby)

    # 4. 绘制邻域富集热图
    fig_path = dirs["figures"] / "spatial_nhood_enrichment.png"
    sq.pl.nhood_enrichment(
        adata,
        groupby=groupby,
        title=f"Neighborhood Enrichment ({groupby})",
        save=fig_path,
        show=False,
    )
    plt.close()

    return {
        "step": "spatial_neighborhood",
        "status": "success",
        "input_path": data_path,
        "groupby": groupby,
        "figures": [str(fig_path)],
    }