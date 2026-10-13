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


## Amateur-review annotations and photometry (2026-10-13)

The original 1,931-row Dias snapshot remains intact. OpenClusters.load()
adds derived `excluded_ir_embedded` and `amateur_exclusion_reason` columns,
marking exactly source flags IR (344 rows) and E (5 rows). No row is deleted.
The opt-in `exclude_infrared_embedded` geometry option omits marked rows from
native/observed drawing. Unknown or absent source flags are not inferred.

`open_clusters_openngc_photometry_v1.ecsv` is a separate, Dias-digest-bound
V-magnitude supplement from OpenNGC v20260501, with source codes, explicit
identity joins, missing/type-conflict/ambiguity status and shared-identity
review flags. It retains all Dias identifiers in source order. Parameters
are heterogeneous; they are not a complete or homogeneous brightness survey.
OpenNGC attribution and CC BY-SA 4.0 apply; the licence is packaged alongside
Caldwell at ../caldwell/CC-BY-SA-4.0.txt. Regenerate explicitly using
`PYTHONPATH=src python tools/query_open_cluster_photometry.py`.

`tools/compare_open_clusters.py` reads catalogues locally, marks selection
reasons in its full CSV, and can write a separate filtered ECSV and PNG/SVG/PDF
plot. It supports chosen x/y parameters, inclusive min/max E(B-V) bounds and an
explicit missing-reddening policy. Missing plot coordinates appear in labelled
categorical margins; no physical measurements are imputed.
