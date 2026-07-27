# Harris Milky Way globular-cluster catalogue

The generated ECSV and CSV files in this directory are obtained from the
NASA HEASARC `globclust` table, based on:

William E. Harris, *A Catalog of Parameters for Globular Clusters in the
Milky Way*, AJ 112, 1487 (1996), using the December 2010 edition.

The catalogue contains 157 Milky Way globular clusters. Harris requests the
citation form “Harris 1996 (2010 edition).”

The source notice states that the data are supplied free of charge and that
any third party redistributing the catalogue must identify the original
McMaster source and do so without charging a fee for the catalogue.

Generate the local snapshot from the repository root with:

```bash
python tools/query_globular_clusters_heasarc.py
```
