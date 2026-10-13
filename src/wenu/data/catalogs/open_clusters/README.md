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

## Hunt & Reffert (2024) prepared member resources

The full 7,167-row prepared aggregate table is
`open_clusters_hunt_reffert2024_v1.ecsv`; its separate 431-row type-o, converted
V5<11 subset is `open_clusters_hunt_reffert2024_v5lt11_v1.ecsv`. The adjacent
`open_clusters_hunt_reffert2024_v1.provenance.json` binds both products and
all four original CDS files by SHA-256. Raw 1,291,929-row member data remain
in an external cache. Ordinary plotting needs no network access.

Cite Hunt & Reffert (2024), A&A 686, A42,
https://doi.org/10.1051/0004-6361/202348662, CDS/VizieR J/A+A/686/A42 and
ESA/Gaia/DPAC. These are separate scientific sources from Dias and OpenNGC;
the OpenNGC CC BY-SA notice above does not relicense the Hunt/Gaia resources.
See the complete provenance and the living docs/user_guide/curation.md guide.

Default accepted members have probability >=0.5 and lie within the estimated
tidal radius. G5 and converted Johnson V5/B5 and Cousins R5 rank members
independently; fifth-member Gaia IDs, missing diagnostics and observed member
flux sums are retained. No extinction is removed. Source colour domains are
enforced; B/R redder than BP-RP=2 require confirmed M giants and are omitted.
Hunt's diameter is 2r50, and E(B-V) is explicitly AV50/3.1 under assumed
R_V=3.1. They are not the Dias diameter/reddening measurements.

The complete-source identifier audit matches all 29 Caldwell components and
27 Messier clusters through normalized primary names and published aliases.
Alternative alias claims stay in the review crosswalk. IR/E and E(B-V)<=3
criteria leave 428 of the 431 V5<11 candidates. The installed Dias sky layer
and atlas defaults remain unchanged. Use tools/query_hunt_reffert2024.py only
for explicit regeneration into a fresh candidate directory or verified cache
reuse; it refuses existing prepared outputs.
