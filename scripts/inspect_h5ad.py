"""
inspect_h5ad.py

用于检查真实 h5ad 数据结构。
重点查看：
1. n_obs / n_vars
2. obs columns
3. var columns
4. obsm keys
5. uns keys
6. layers keys
7. 是否存在空间坐标
"""

import argparse
import scanpy as sc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True)
    args = parser.parse_args()

    print("Loading data...")
    adata = sc.read_h5ad(args.data)

    print("\n========== Basic Info ==========")
    print(adata)

    print("\n========== Shape ==========")
    print("n_obs:", adata.n_obs)
    print("n_vars:", adata.n_vars)

    print("\n========== obs columns ==========")
    print(list(adata.obs.columns))

    print("\n========== var columns ==========")
    print(list(adata.var.columns))

    print("\n========== obsm keys ==========")
    print(list(adata.obsm.keys()))

    print("\n========== varm keys ==========")
    print(list(adata.varm.keys()))

    print("\n========== layers keys ==========")
    print(list(adata.layers.keys()))

    print("\n========== uns keys ==========")
    print(list(adata.uns.keys()))

    print("\n========== first obs ==========")
    print(adata.obs.head())

    print("\n========== first var ==========")
    print(adata.var.head())

    print("\n========== var names example ==========")
    print(adata.var_names[:20].tolist())

    print("\n========== obs names example ==========")
    print(adata.obs_names[:20].tolist())

    if "spatial" in adata.obsm:
        print("\nFound spatial coordinates in adata.obsm['spatial']")
        print(adata.obsm["spatial"][:5])
    else:
        print("\nNo adata.obsm['spatial'] found.")
        print("Please check whether spatial coordinates are stored in obs columns, such as x/y, spatial_x/spatial_y, array_row/array_col.")

if __name__ == "__main__":
    main()