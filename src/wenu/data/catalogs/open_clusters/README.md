# Dias/HEASARC optically visible open clusters

This directory contains Wenu's normalized snapshot of established and likely
open clusters selected from the NASA HEASARC `OPENCLUST` table. Explicit
asterisms, dubious/non-existent objects, associations, moving groups, possible
globular clusters, and cluster remnants are excluded.

The source supplies apparent diameter for almost every object, but no
homogeneous integrated visual magnitude. Wenu therefore applies no magnitude
limit to this snapshot.

Regenerate from the repository root with:

```shell
python tools/query_open_clusters_heasarc.py
```

Please cite Dias et al. (2002) and HEASARC when using these data.
