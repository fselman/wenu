# Creating a sky atlas

**Implemented baseline:** PR #234, main `6708f54a` (2026-10-17).
Geometry design, standalone index and publication commands are available.
The [kernel roadmap](../developer/kernel_roadmap_v0.9.5.md) describes future
architecture; it does not change these commands.

## Commands and independent inputs

| Command | Input responsibility | Output |
|---|---|---|
| `wenu_design_atlas` | Geometry request or installed layout | Resolved design JSON |
| `wenu_plot_atlas` | Design plus index presentation | Overview PNG/PDF/SVG |
| `wenu_create_atlas` | Design plus full chart presentation | Sheets, reports, manifest and assembled PDF |

Layout changes geometry. Full style changes selection/appearance and publication
settings. Index style changes only the overview. Selecting a style does not
retile the design; its name does not restrict it to one layout.

## Installed presets

| Protocol | Name | Main settings |
|---|---|---|
| Layout | `b4-landscape-five-band` | ISO B4 landscape, five interior bands, 34 charts |
| Layout | `b4-portrait` | ISO B4 portrait, three interior bands, 36 charts |
| Layout | `b4-hemispheres` | ISO B4 portrait, two circular stereographic hemispheres |
| Full chart style | `atlas-v6` | Magnitude 7.5; stellar diameter factor 1.7 |
| Full chart style | `atlas-hemispheres-v2` | Magnitude 5; half v6 star/cluster/PN diameters |
| Index style | `b4-landscape` | Landscape overview presentation |
| Index style | `b4-portrait` | Portrait overview presentation |

The name `atlas-v6` also exists under the separate ordinary `chart` protocol;
it is not the same input format. Full styles v1–v5 and old sizing/layout
experiments are historical examples, not registered current full styles.

```bash
wenu_chart presets
wenu_design_atlas --layout b4-portrait --output atlas_portrait_v1.json
wenu_plot_atlas --design atlas_portrait_v1.json --output-prefix atlas_portrait_index_v1
wenu_create_atlas --design atlas_portrait_v1.json --config atlas-v6 --charts 1 --output-dir atlas_portrait_review_v1
```

`wenu_create_atlas` defaults to `atlas-v6`. Index plotting chooses the matching
installed index presentation when `--config` is omitted. Explicit JSON/TOML
paths remain supported; the designer's geometry-request TOML and the two
presentation TOML protocols have separate validators. Existing outputs are
never overwritten: use new versioned output names/directories.

## Two hemispheric charts

`b4-hemispheres` contains two circular stereographic sheets on ISO B4 portrait
paper. Chart 1 covers Dec −90 through 0 degrees; chart 2 covers 0 through +90.
They have the same physical sky diameter and central angular scale. Their
only shared boundary is the equator, with zero shared area; unique primary
ownership assigns Dec 0 to the northern sheet. This is not a rectangular
180-degree footprint.

```bash
mkdir -p output/atlas_hemispheres_v1
wenu_design_atlas --layout b4-hemispheres --output output/atlas_hemispheres_v1/design_v1.json
wenu_plot_atlas --design output/atlas_hemispheres_v1/design_v1.json --output-prefix output/atlas_hemispheres_v1/index_v1
wenu_create_atlas --design output/atlas_hemispheres_v1/design_v1.json --config atlas-hemispheres-v2 --charts all --jobs 2 --index output/atlas_hemispheres_v1/index_v1.pdf --save-sky output/atlas_hemispheres_v1/native_sky_v1 --output-dir output/atlas_hemispheres_v1/publication_v1
```

For an editable geometry request use `examples/atlas_design_hemispheres_v1.toml`
as the designer's `--config`. It declares the hemisphere algorithm, 180-degree
field, zero overlap/shared band and square sky aspect. Use `atlas-v6` instead
when its brighter symbol sizes and magnitude 7.5 selection are wanted.

The hemisphere v2 style retains v6 colours and fonts; its star diameter
multiplier is 0.85, cluster multiplier 0.5 and PN multiplier 0.625. Those are
half the corresponding v6 diameters. Open-cluster angular diameters and minimum
symbols scale together. Other object classes retain v6 sizing. Neither the
catalogue angular sizes nor geometric central scale changes.

## Saved sky and publication lifecycle

`--save-sky DIRECTORY` writes an explicit native catalogue snapshot for reuse.
`--from-sky DIRECTORY` uses that saved snapshot without source acquisition.
For a later review, keep the design and index and choose a new output path:

```bash
wenu_create_atlas --design output/atlas_hemispheres_v1/design_v1.json --config atlas-hemispheres-v2 --from-sky output/atlas_hemispheres_v1/native_sky_v1 --charts 1,2 --jobs 2 --index output/atlas_hemispheres_v1/index_v1.pdf --output-dir output/atlas_hemispheres_v1/review_v2
```

Reuse verifies frozen resource identity, coverage and exact design binding.
Do not reuse a snapshot from the 34- or 36-chart layout with the hemispheric
design. The native snapshot retains the maximal catalogue; plotted magnitude
selection is separate. A sufficient snapshot can serve a changed magnitude
limit without being rebuilt, but an insufficient snapshot fails explicitly.

`--charts` accepts `all` or explicit chart selectors; subsets keep original
chart numbers. Serial and worker routes use the same chart pipeline. Output
includes individual sheet files, assembled `atlas.pdf` and a manifest with
design/snapshot identity, resolved presentation and product checksums.
Physical paper size and useful rectangle are retained without tight cropping.
PDF must be among the selected formats for assembly. A failed batch removes
only its staging/incomplete outputs; a completed saved sky is preserved.

`--index PDF` admits an unencrypted one-page index, records its digest and fits
it proportionally without rasterization. Choose the index from the same design:
an arbitrary supplied PDF does not itself prove design correspondence.
With an index, report/chart pairs place charts on odd right-hand pages.
Report margins mirror for binding. Without an index, chart-only assembly is
available. Report furniture and object-inventory science remain separate.

## Selection, labels and legends

`--magnitude-limit NUMBER` overrides the style's `star_magnitude_limit` within
the admitted range −2 through 11 and snapshot coverage. It selects stars, not
deep-sky objects or index stars. `star_size_scale` changes physical marker
diameter; `stellar_magnitude_sizing` controls the sizing law independently.

`--no-legend` hides the stellar-magnitude legend on chart pages; persistent
equivalent: `chart_legend_visible = false`. Reports and polar coordinate labels
are independent. `--legend` explicitly enables it.

`--no-planetary-nebulae` removes that layer; `--planetary-nebulae` enables it.
Without an explicit CLI switch, the selected style's layer list is retained.

Use `--exclude-layer nonstellar` to hide the atlas's label-only Messier layer
(M1, M2, etc.). Scientific object symbols remain in their independent layers.
Repeat exclusions, for example `--exclude-layer nonstellar --exclude-layer
planetary_nebulae`. Exclusions apply after individual switches, so an explicitly
excluded layer stays excluded. Use a fresh publication output directory.

## Coordinate grid and physical frame

Full-style fields include `grid_lines_visible`, `grid_label_fontsize`,
`grid_minor_label_scale`, `grid_frame_width_scale`, `grid_ra_step_hours`,
`grid_polar_ra_step_hours`, `grid_minute_labels_visible` and
`grid_dec_label_scale`. They are presentation TOML keys, not implied CLI flags.
Installed styles use 1-hour RA cadence, 2-hour polar RA cadence, 10-degree
declination parallels and 10-minute RA ticks, with minute labels disabled.

Coordinate labels attach to actual boundary crossings. RA/Dec conflict policy,
slanted ticks and polar interior declination labels are owned by the shared
grid/furniture pipeline. Frame widths are measured in physical display units;
the fixed circular band uses worst-case rotated glyph extents once for both
hemispheres. Appearance changes must preserve chart geometry and central scale.

## Catalogue defaults and criteria

New skies resolve verified installed curated catalogues: 513 open clusters and
319 planetary nebulae. Matching criteria appendices use these defaults automatically.
Explicit `--open-cluster-catalogue` and `--planetary-nebula-catalogue` override
sources before snapshot creation. `--from-sky` uses the already frozen sources;
do not combine it with new catalogue overrides.

`--selection-criteria` supplies explicit digest-bound criteria. The publication
verifies correspondence with the resolved curated ECSV, including
`planetary_nebulae.ecsv`, rather than applying a new selection during drawing.
Open-cluster sizes, `cluster_symbol_scale`, `deep_sky_symbol_scale` and
`planetary_nebula_symbol_scale` affect appearance, not source membership.
See the [curation guide](curation.md) for acquisition, selection and promotion.

## Current limitations and historical material

Facing report furniture and legends are implemented; detailed per-object
inventories/public-interest classification remain unfinished. Empty reserved
report space does not mean the chart has no objects. Existing output paths
are not resumable overwrite destinations.

Prototype APIs, old index/layout comparisons, marker-size experiments and full
acceptance logs are preserved in the
[original atlas guide](../developer/archive/pre_kernel_20261017/docs/user_guide/atlas.md).
The old explicit v6 style example remains `examples/atlas_chart_style_v6.toml`;
installed preset names are the current operational entry point.

## Nominal stellar motion for one sheet

A single native ICRS sheet can opt in to the accepted nominal stellar models.
Use the existing verified source-only saved sky, matching resolved design and
independent atlas presentation, plus a separate scientific TOML file. The
command performs no downloads and reconstructs no historical observer.

A minimal full-input model document has this form. Replace the source path and
manifest digest with the verified local source values; they are explicit inputs.

```toml
schema_version = 1
document_kind = "wenu-stellar-motion-request"
source_directory = "/absolute/path/to/stellar_enrichment_source_v1"
source_manifest_sha256 = "REPLACE_WITH_VERIFIED_64_CHARACTER_LOWERCASE_SHA256"
target_jyear_tcb = -8000.0

[[models]]
motion_policy = "full-input-rectilinear"
start_jyear_tcb = -8001.0
stop_jyear_tcb = 2050.0
distance_policy = "positive-parallax-reciprocal"
radial_velocity_policy = "spectroscopic-proxy"
```

This selects only the full-input subset; it does not silently fill missing data.
To select other already admitted models, append explicit ordered tables with
`motion_policy = "proper-motion-angular"` or
`motion_policy = "hipparcos2-angular-fallback"`, finite bounds and
`distance_policy = "not-used"`, `radial_velocity_policy = "not-used"`.
The Hipparcos-2 model additionally requires
`epoch_policy = "nominal-tcb-deferred-qualification"`. Table order selects the
first declared available model; a failed query never falls back to static stars.

Example invocation, after supplying the existing matching files and a new output
location (this is a command synopsis, not the guarded Mac acceptance recipe):

```bash
wenu_chart atlas-sheet --design /absolute/path/design.json \
  --config /absolute/path/presentation.toml \
  --from-sky /absolute/path/source-sky \
  --chart-number 1 \
  --stellar-motion-config /absolute/path/motion-v1.toml \
  --output-dir /absolute/path/new-sheet-output
```

The epoch values are nominal TCB Julian epochs, not calendar dates or a dated
equinox. Relative source paths resolve against the motion file, independently
of the shell working directory. Exact TOML/source/model identities, the resolved
epoch, finite coverage, availability and unknown physical accuracy are recorded
in the sheet report. Stars own realization; constellation lines and label anchors
follow their public positions while preserving source membership, names and V.

Omitting `--stellar-motion-config` preserves the existing static command.
Other chart families, historical observers and date-oriented axes remain
separate work. Physical ancient-position
accuracy is unknown. This single-sheet command extension passed complete Mac,
real-cache CLI/Python parity and present/ancient visual acceptance in PR #348,
merged at `c319c88f`.

### Nominal stellar motion for a multi-sheet atlas

The atlas publication command now accepts the same motion file:

```bash
wenu_create_atlas --design /absolute/path/design.json \
  --config /absolute/path/presentation.toml \
  --from-sky /absolute/path/source-sky \
  --charts 13,28 --jobs 2 \
  --stellar-motion-config /absolute/path/motion-v1.toml \
  --output-dir /absolute/path/new-atlas-output
```

Use `--jobs 1` for serial publication. Each process owns its stellar realization
and reuses it across sheets; all sheets and catalogue counts share scientific
source/model/event identities. No live stellar session is sent between workers.
The input is captured before dispatch, so editing the motion file afterward
does not change the running publication. The source sky stays source-only.

The count appendix reports the same nominal stellar epoch and unavailable
population. A supplied index is retained as a static reference, visibly marked
in the assembled atlas; selection-criteria PDFs retain their source meaning.
Failures publish no completion manifest. Without the motion option, existing
static publication behavior remains unchanged. This bounded multi-sheet route
passed Mac runtime/documentation, real-cache serial/spawn/single-sheet parity
and present/ancient visual acceptance in PR #350, merged at `9776052a`.
For the accepted two-sheet workload, serial execution was faster than two workers;
choose worker count for the actual workload rather than assuming a speedup.
Physical ancient-position accuracy remains unknown.



## Mean-axis atlas views

The K4b.06 candidate adds an optional scientific frame document to both
`wenu_chart atlas-sheet` and `wenu_create_atlas`. It changes axes while retaining
a barycentric origin. It does not move stars unless the independent
`--stellar-motion-config` is also supplied, and does not reconstruct an observer.
Mac actual-cache and visual acceptance remain pending.

Example `frame-jminus8000-v1.toml`:

```toml
schema_version = 1
document_kind = "wenu-atlas-frame"
axes = "mean-equator-equinox"
model_policy = "vcw2011-2012-erfa"

[equinox]
jd1 = -1200955
jd2 = 0.0
scale = "tt"

[start]
jd1 = -1200956
jd2 = 0.0
scale = "tt"

[stop]
jd1 = 2451546
jd2 = 0.0
scale = "tt"
```

These two-part dates declare a J-8000 TT equinox and a finite caller domain.
They are not a calendar-date or TCB conversion. Use
`axes = "mean-ecliptic-equinox"` for mean ecliptic axes. The corrected VCW
model admits only its qualified finite frame range J-198000..J202000;
source-motion and ephemeris domains remain separate, and physical accuracy
is unknown.

With an existing matching design/source sky and a new output location:

```bash
wenu_chart atlas-sheet --design /absolute/path/design.json \
  --config /absolute/path/presentation.toml \
  --from-sky /absolute/path/source-sky --chart-number 13 \
  --stellar-motion-config /absolute/path/motion-v1.toml \
  --atlas-frame-config /absolute/path/frame-jminus8000-v1.toml \
  --output-dir /absolute/path/new-dated-sheet
```

For a book, add the same `--atlas-frame-config` to the existing
`wenu_create_atlas` invocation. Both serial and spawn workers preserve the
captured scientific identity. No ordinary chart-family option or motion schema
has changed. The original ICRS design bytes stay intact; an explicitly identified
derived view uses their numerical layout in the selected axes.

The full presentation still selects layers. For ecliptic longitude/latitude
edge marks, include `ecliptic_grid` in its `layers`; `equatorial_grid` alone
draws the dated mean-equatorial reference in the ecliptic view without pretending
it is the primary ecliptic graticule. Equatorial edge labels use RA hours;
ecliptic edge labels use longitude degrees. Existing RA-cadence presentation
values set the corresponding 15-degree multiples for ecliptic meridians.
No layer is automatically added or renamed. Dated canonical references use the
TT mean-axis policy; Galactic references remain fixed. Noncanonical reference
grids/arbitrary celestial point policies refuse explicitly.

Reports retain the source design hash, derived sheet/frame identity, TT equinox,
stellar TCB event when present, target-axis centre, backend/matrices and unknown
accuracy. A supplied index remains a static unverified frame/date reference.
Omitting `--atlas-frame-config` retains native ICRS behavior.



