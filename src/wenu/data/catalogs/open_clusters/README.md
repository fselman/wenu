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
criteria leave 428 of the 431 V5<11 candidates. These original derivatives remain
unchanged; the current active curated catalogue is the separate 513-object Wenu
v0.2 selection. Use tools/query_hunt_reffert2024.py only
for explicit regeneration into a fresh candidate directory or verified cache
reuse; it refuses existing prepared outputs.


## Selected-cluster astrometry companion v1

`open_clusters_hunt_astrometry_v1.ecsv` retains 513 selected IDs in their accepted
order and is SHA-256-bound to the active `wenu_open_clusters_v0.2.ecsv` bytes.
It recovers the 509 matching Hunt aggregate solutions (502 with radial velocity).
All Hunt fields are masked for the four Dias-only clusters. The original curated
catalogue, its selection evidence and the full member-photometry derivatives are
unchanged. This companion is available for explicit offline enrichment; default
charts do not consume it or propagate cluster motions yet.

The `open_clusters_hunt_astrometry_source_v1.json` specification preserves the
original CDS field descriptions/units, reviewed PM convention, source epoch label,
SHA-256/byte counts, acquisition receipt and citation/policy URLs. The adjacent
`open_clusters_hunt_astrometry_v1.provenance.json` binds the derived ECSV bytes.
Source `e_*` fields are standard errors; `s_*` fields are dispersions. RV masks,
distance percentiles/counts/flags and heliocentric Galactic XYZ remain distinct.
The epoch time scale and coordinate origin are not declared in this ReadMe;
cluster-mean covariances are not supplied. These remain null. Gaia member-star
covariances are not cluster-mean covariances. Dias epochs and RA-motion conventions
must be resolved independently before adopting those four solutions.

With the small original CDS aggregate and ReadMe already acquired locally, run
this offline command from the repository root, replacing the two source paths
with your explicit local cache paths:

```shell
python tools/hunt_reffert_catalogue.py \
  --selected-catalogue src/wenu/data/curated_catalogs/open_clusters/wenu_open_clusters_v0.2.ecsv \
  --clusters /path/to/cache/clusters.dat.gz \
  --readme /path/to/cache/ReadMe \
  --specification src/wenu/data/catalogs/open_clusters/open_clusters_hunt_astrometry_source_v1.json \
  --output-directory output/cluster_astrometry_regeneration_v1
```

No member-star download is needed. The exact ReadMe and aggregate digests match
Wenu's earlier acquisition. Source schema changes require a reviewed new
specification/version. Use `attach_cluster_astrometry` in the existing developer
tool owner for an independent enriched table; every original column is preserved.
See the implementation reference for the explicit adoption and runtime-record
boundary. Cite Hunt & Reffert, A&A 686 A42 (2024), DOI above, CDS/VizieR and
ESA/Gaia/DPAC. Policy checked 2026-10-19: scientific usage requires source
acknowledgement; the source article declares CC BY 4.0. The derivative records
its selection/reformatting. CDS reserves information-system metadata rights;
this is not a blanket CC0 claim or permission for unrelated commercial reuse.


## Qualified nominal motion admission v1

`open_clusters_hunt_motion_admission_v1.json` binds the exact existing astrometry
companion/selected catalogue and accepted qualification evidence for explicit
runtime admission by `wenu.cluster_state.load_cluster_motion`. Its documented
Gaia lineage qualifies J2016.0(TCB), barycentric ICRS and mu_alpha_star. Column
mappings select the published `dist50` estimator, not inverse mean parallax.
It records the spectroscopic-RV proxy and density-mode/core-mean approximation.
Source units and source epoch are consumed from validated metadata, not software
catalogue defaults. The v1 raw data/ReadMe gaps remain preserved unchanged.

The provider's nominal rectilinear model requires explicit finite TCB coverage.
It advertises 502 full-input solutions while retaining seven missing-RV and four
unqualified Dias-only records as unavailable. Numerical evaluation and reuse
bounds now refer to the admitted binary64 SI rectilinear model. Source conversion,
measurement and physical-model accuracy are not certified. No automatic download, observer correction, additional light-time
correction or default chart/snapshot adoption occurs. See the implementation
reference's nominal cluster provider API for ownership and limits.
