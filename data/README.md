# Data Directory

This directory is used to store input `.h5ad` files.

Large spatial transcriptomics data files are not included in this GitHub repository because of file size limits.

## Expected File

Please place your test data as:

```text
data/example.h5ad
Then run:

python main.py --data "data/example.h5ad" --query "请对该空间转录组数据进行完整基础分析，包括数据概览、质量控制、预处理、UMAP降维、Leiden聚类、空间可视化和marker gene分析" --output "outputs"
Real Data Used in This Project
The project was tested with data from:

GSE278603
GSM9046245_Embryo_E7.75_stereo_rep1.h5ad
Due to the large size of the original .h5ad file, it is not included in this repository.

Create a Small Test Dataset
If the original dataset is large, create a small reproducible subset:

python scripts/make_small_h5ad.py --input "path/to/raw_data.h5ad" --output "data/example.h5ad" --n_obs 5000 --n_vars 3000
Inspect Data Structure
Before running the full Agent, inspect the AnnData structure:

python scripts/inspect_h5ad.py --data "data/example.h5ad"
The inspection script prints:

number of observations and genes
obs columns
var columns
obsm keys
spatial coordinate information if available
