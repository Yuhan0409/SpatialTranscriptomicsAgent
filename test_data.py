# import scanpy as sc
# import pandas as pd
# import numpy as np

# # 1. 下载一个内置的 PBMC 数据集（没有空间坐标，但能测通大部分流程）
# adata = sc.datasets.pbmc68k_reduced()

# # 2. 为了测试你的 spatial_plot_tool，我们伪造一个空间坐标列
# np.random.seed(42)
# adata.obsm['spatial'] = np.random.rand(adata.n_obs, 2) * 100

# # 3. 保存到 data 目录
# adata.write_h5ad("data/test_data.h5ad")
# print("测试数据已生成：data/test_data.h5ad")

import scanpy as sc
import numpy as np
import os

# 创建 data 文件夹
os.makedirs("data", exist_ok=True)

# 1. 下载 PBMC 3k 原始数据（约 3 MB，几秒钟）
print("正在下载 PBMC 3k 原始数据...")
adata = sc.datasets.pbmc3k()

# 2. 伪造空间坐标（用于测试 spatial_plot_tool）
np.random.seed(42)
adata.obsm['spatial'] = np.random.rand(adata.n_obs, 2) * 100

# 3. 保存为 .h5ad
adata.write_h5ad("data/pbmc3k_test.h5ad")

print("✅ 测试数据已生成：data/pbmc3k_test.h5ad")
print(f"细胞数 (spots): {adata.n_obs}")
print(f"基因数: {adata.n_vars}")
print(f"是否包含空间坐标: {'spatial' in adata.obsm}")