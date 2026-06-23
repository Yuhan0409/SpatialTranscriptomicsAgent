"""
make_small_h5ad.py

从真实 h5ad 数据中裁剪一个小型测试数据。
用途：
1. 快速测试 Agent；
2. 课堂演示；
3. 助教本地测试。
"""

import argparse
import scanpy as sc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--n_obs", type=int, default=5000)
    parser.add_argument("--n_vars", type=int, default=3000)
    args = parser.parse_args()

    print("Loading original data...")
    adata = sc.read_h5ad(args.input)

    print("Original data:")
    print(adata)

    # 如果细胞/spot 数多于 n_obs，则随机抽样
    if adata.n_obs > args.n_obs:
        sc.pp.subsample(adata, n_obs=args.n_obs, random_state=42)

    # 如果基因数多于 n_vars，先按表达量选前 n_vars 个基因
    if adata.n_vars > args.n_vars:
        # 计算每个基因的总表达
        X = adata.X
        if hasattr(X, "toarray"):
            gene_sum = X.sum(axis=0).A1
        else:
            gene_sum = X.sum(axis=0)

        top_gene_idx = gene_sum.argsort()[-args.n_vars:]
        adata = adata[:, top_gene_idx].copy()

    print("Small data:")
    print(adata)

    adata.write_h5ad(args.output)
    print(f"Saved to {args.output}")

if __name__ == "__main__":
    main()