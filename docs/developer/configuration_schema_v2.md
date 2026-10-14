# Wenu configuration schema version 2

**Status:** Milestone 46D.2 specification
**Schema version:** `2`
**Runtime status:** Packaged and optional partial user documents are strictly
validated and translated through the ordinary view, composition, furniture,
product, and export pipeline

This document is the authoritative structural contract for Wenu's first
versioned TOML configuration. It derives its public paths from
`archive/audits/configuration_default_audit.md`. It specifies names, types, ordering, and
validation without creating a runtime registry or changing current defaults.

The atlas and cartoon canvas tables now contain `grid_label_band` with
`enabled` (boolean), `fill_color`, `frame_color` and `label_color` (colour), `line_width`
and `padding_points` (finite nonnegative points). Defaults are true, white,
black, black, 0.8 and 2.0. Only non-polar planisphere, regional/constellation and
binocular render owners use this furniture. Explicit shared CLI band controls
have precedence; `none` selects transparent fill/frame colour.

## Document boundary

The root is a TOML table containing the scalar `schema_version = 2`, followed
by these top-level tables in this exact order:

1. `data`
2. `constellations`
3. `observer`
4. `sequence`
5. `centers`
6. `masks`
7. `families`
8. `detail`
9. `reports`
10. `styles`
11. `modes`
12. `grids_references`
13. `coordinates`
14. `furniture`
15. `products`
16. `export`

The packaged document is complete. A user document is a partial overlay but
must still declare `schema_version`. Tables and keys are emitted in the order
defined here; arrays preserve their declared order. Merge precedence is:

```text
packaged defaults.toml < optional user TOML < explicit CLI arguments
```

Unknown sections and keys are errors. Dotted keys may express documented
paths but may not create an undocumented intermediate table. TOML values are
data only: executable expressions, Python class names, renderer operations,
catalogue joins, imports, callbacks, and arbitrary code are prohibited.

## Common scalar types

- `boolean`: TOML `true` or `false`; integers are not booleans.
- `integer`: a TOML integer, excluding booleans.
- `number`: a finite TOML integer or float, excluding booleans.
- `string`: a TOML string.
- `color`: `none`, a CSS-style named color accepted by Wenu, or `#RRGGBB` /
  `#RRGGBBAA`; `null` in the audit becomes the string `none` when absence is a
  selectable public value.
- `line_style`: exactly `solid`, `dashed`, `dotted`, `dash_dot`, or `none`.
- `optional-*`: either the stated value or the string `none`.
- `string-list` and `number-list`: homogeneous TOML arrays.
- `point`: exactly two finite numbers.

All opacity values are in `[0, 1]`. Sizes, widths, DPI, sample counts, font
sizes, scale factors, and z-orders that represent nonnegative appearance are
`>= 0`; physical output dimensions and sampling counts are strictly positive.
Angles in degrees are finite. Longitudes are normalized by their existing
Python owner; latitudes and declinations must be in `[-90, 90]`.

Every configurable line-bearing element is a line table with independent
`color`, `line_width`, and `line_style` keys. A current shared value is copied
into each semantic line path in the packaged document; it is not represented
by a hidden global line setting.

## Ordered namespace

The paths below are ordered first by top-level responsibility and then by
their appearance in the future packaged document. A leaf annotation gives
its type or its closed vocabulary.

### `data`

- `moving_object_policy`: exactly `acquire-if-missing`, `offline`, or
  `refresh`. The default resolves a verified cached numbered-asteroid SPK or
  acquires it during installed-CLI preflight. `offline` prohibits network
  access and `refresh` requests a new provider solution. This policy never
  authorizes network access from request generation or rendering.

### `observer`

- `location`: string
- `time`: string in an Astropy-accepted explicit form
- `elevation`: optional-number
- `timezone`: optional-string
- `ephemeris`: optional-string
- `data_directory`: optional-string
- `minor_body_resource_directory`: optional-string path to one explicit,
  manifest-backed offline minor-body resource set

### `sequence`

- `stop`: optional ISO 8601 datetime string with explicit UTC offset;
- `frames`: optional integer, at least 2 when active;
- `display_timezone`: optional IANA time-zone name;
- `playback_duration`: optional positive seconds;
- `frames_per_second`: optional positive number;
- `restart_policy`: `restart` or `resume`.

`stop` and `frames` are both `none` for static generation or both active
for a uniform inclusive sequence. Playback duration and frame rate are
likewise absent or present together, and their product must imply the frame
count. The ordinary observer time remains the sequence start. Explicit CLI
values override these defaults.

### `constellations`

`system` selects the constellation vocabulary and line-figure tradition.
Version 2 accepts `western`. This parameter enables no content by itself.

### `centers`

Each family table has exactly one default public center declaration:

- `all_sky.kind`: `none`
- `planisphere.kind`: `none`
- `regional_single.kind`: `constellations`; `constellations`: string-list
- `regional_group.kind`: `constellations` or `group`;
  `constellations`: string-list; `group`: optional-string
- `circumpolar.kind`: `none`
- `binocular.kind`: `target`; `target`: string

Only the fields required by `kind` may be active. `constellations` must be
nonempty and contain unique IAU abbreviations. A `target`, `group`, and
`constellations` declaration may not compete within one center.

### `masks`

Each mask-capable chart-family table contains an independent `constellations`
string-list. Circumpolar charts do not expose a constellation mask.
An empty list means that no constellation mask is requested.

### `families`

Every family contains `projection`, `coordinate_frame`, `orientation`, and
`position_angle`. `orientation` is optional and accepts
`celestial-north-up` or `zenith-up`; `position_angle` is an optional number.
Regional and binocular families select exactly one of them. Other families
use `orientation = "none"` and a literal position angle. Family-specific
geometry follows:

- `all_sky`: `projection = "mollweide"`, `coordinate_frame = "galactic"`.
- `planisphere`: `projection = "stereographic"`,
  `coordinate_frame = "horizontal"`.
- `regional_single` and `regional_group`: optional positive `width` and
  `height`; both must be `none` together or positive together.
- `circumpolar`: `pole` is `north` or `south`; `limiting_declination` is a
  number consistent with that pole.
- `binocular`: positive `field_diameter`.

The listed projection/frame pairs are public geometry invariants. Configuration
may state them for reproducibility but may not invent another pairing.

### `detail`

- `neutral`: optional star and catalogue magnitude limits, optional extended
  object minimum sizes and sample count, positive `label_density`, optional
  enabled layers, grid-label layer list, optional constellation-star mode,
  and extra-star identifier list.
- `content.default_layers` and `content.cartoon_layers`: string-list.
- `constellations.labels`, `.lines`, and `.boundaries`: string-lists, empty
  by default; either explicit canonicalizable IAU codes or the sole `all`
  token. Matching `.labels_exclude`, `.lines_exclude`, and
  `.boundaries_exclude` lists accept only explicit IAU codes, default empty,
  and subtract independently without enabling layers. Explicit CLI lists
  replace their corresponding configuration lists. The schema remains v2.
- `cartoon`: `star_mode`, `bright_limit`, extra stars, `deep_sky`,
  `named_star_labels`, a galaxy magnitude ceiling, and minimum displayed
  sizes for open and globular clusters.
- `adaptive`: positive `reference_width`, nonnegative
  `magnitude_adjustment_per_octave`, nonnegative `maximum_adjustment`,
  `adapt_layers`, and ordered `levels` array of tables. Each level has
  `span`, catalogue ceilings, minimum sizes, and `label_density`; spans must
  be positive and strictly increasing.
- `canonical`: per-family atlas ceilings and binocular sample policy.
- `binocular_stellar_sizing`: reference vocabulary, positive scale and
  exponent, nonnegative `minimum_area`, and optional positive `maximum_area`;
  maximum must not be below minimum.

Layer names and constellation-star modes are closed vocabularies owned by the
existing typed detail boundary. Unknown names are errors.

### `styles`

`styles.atlas` and `styles.cartoon` each contain one complete semantic base
appearance; neither inherits from the other. Their ordered subtables are
`canvas`, `stars`, `milky_way`, `lmc`, `smc`, `nonstellar`, `galaxy`,
`supernova_remnant`, `globular_cluster`, `planetary_nebula`, `open_cluster`,
`constellation_boundaries`, `constellation_figures`, `constellation_labels`,
`equatorial_grid`, `ecliptic_grid`, `galactic_grid`, `altaz_grid`,
`coordinate_labels`, `horizon`, `mask`, `chart_boundary`, and `legend`.

Appearance leaves use the common scalar types. In particular:

- canvas exposes background, foreground, label font, and footer color;
  `labels_orientation` accepts `chart`, `upright`, or `up-away-from-cp`.
  It controls object/constellation typography; grids, references, and track
  dates retain separate policies. The away-from-pole override requires a
  polar-planisphere chart; explicit CLI orientation replaces the TOML value.
- stars expose color, magnitude sizing, area bounds, and variable/multiple
  symbol enablement, color, shape, size, edge width, and opacity;
- fills expose `color` and `opacity`; every edge, contour, figure, boundary,
  grid, horizon, and chart boundary exposes `color`, `line_width`, and
  `line_style`, plus its opacity and z-order where public;
- deep-sky symbols expose shape, size, face/fill, edge, edge width, opacity,
  and label color/font controls applicable to that family;
- labels expose color, font size, opacity, alignment, and offset where
  applicable;
- masks expose color, opacity, and z-order;
- legends expose visibility, location, fonts, frame, face, edge, opacity,
  columns, and optional text color.

`styles.palettes` contains only semantic color replacements, ordered as
`atlas_presentation`, `cartoon_print`, and `cartoon_presentation`. A palette
may not contain geometry, detail, or renderer operations.

### `modes`

- `base`: positive width, optional positive height, and transparency.
- `print` and `presentation`: positive DPI; positive font, line, symbol, and
  contrast scales; and `prefer_vector`.
- `cartoon`: label offset point, nonnegative clearance point, and halo
  opacity.

Natural height, output pixels, effective scaled appearance, and palette
application remain derived Python behavior and are not schema leaves.

### `grids_references`

- `coordinate_grid.samples`: positive odd integer.
- `coordinate_grid.frame`, `equinox`, meridian declination limits, reference
  inclusion switches, and optional requested coordinate lists.
- `references.state`: closed vocabulary defined by the existing furniture
  contract; `anchor`: optional point; equatorial, ecliptic, and Galactic
  labels: strings.
- `poles.state`: closed vocabulary; `labels`: boolean.

The four grid appearances live under `styles.atlas`; this section owns grid
construction and semantic reference choices, not their colors.

### `furniture`

- `footer`: enablement, application string, version inclusion, optional
  copyright, font, vertical coordinate, and left/right coordinates.
- `context`: center/grid/location/date/local-time/label switches.
- `legends`: object/star/context/count switches, title, and family-specific
  object/star placements.
- `magnitude_legend`: enablement, location, title, frame, optional fonts,
  marker, optional face/edge/text colors, edge width, label spacing,
  handle-text padding, border padding, and z-order.

Legend locations and markers are validated by the existing typed furniture
boundary. An enabled legend must have a non-`none` location.

### `products`

- `default.style`: `atlas` or `cartoon`
- `default.mode`: `print` or `presentation`
- `default.all_products`: boolean
- `default.language`: supported language identifier
- `default.title`: optional-string
- `default.extension`: `.png`, `.pdf`, or `.svg`

SVG extension selection invokes Wenu's single editable-text SVG contract. The
schema has no separate SVG font-policy key. An explicit CLI `--format` remains
the ordinary one-off override and must agree with an explicitly suffixed
single-file output.

Named product combinations contain only style, mode, detail-policy reference,
and post-mode visual overrides accepted by existing immutable contracts. They
may not change observer, center, family geometry, or masking.

### `export`

- positive `dpi`
- `bounding_box`: `tight` or `standard`
- `transparent`: boolean
- `face_color`: optional-color
- `metadata`: table of string keys and string values
- nonnegative `padding`

Circular transparency, effective face color, natural height, output pixels,
suffixes, rendering, and saving remain derived or behavioral Python owners.

## Validation and diagnostics

Validation is deterministic and depth-first in the section/key order above.
It occurs before catalogue loading, observer construction, chart creation, or
rendering. It rejects:

- unsupported or missing schema versions;
- unknown sections, intermediate tables, and keys;
- missing required packaged keys;
- wrong TOML types, non-finite numbers, invalid colors, invalid ranges, and
  unsupported closed-vocabulary values;
- duplicate identifiers where uniqueness is required; and
- contradictory combinations described in this specification.

Every diagnostic contains the complete configuration path, for example:

```text
styles.atlas.horizon.line_style: unsupported value "dashdot";
expected one of solid, dashed, dotted, dash_dot, none
```

Overlay diagnostics use the overlay path even when the packaged value at that
path is valid. Validation never silently ignores, coerces, or repairs an
invalid value.

## Translation boundary

Milestone 46D.3 will parse and validate the complete packaged document, then
translate it into existing immutable observer, request, geometry, detail,
style, mode, grid/reference, furniture, product, and export contracts. Python
retains validation behavior, scientific invariants, derived values, catalogue
operations, geometry, projection, preparation, rendering, and export. It may
define schema types and translators, but it must not copy public default
literals into a second registry.
## Celestial reference policy

`[coordinates.references]` owns the ordinary coupled celestial-reference
orientation. Its required `equinox` string defaults to `J2000` and accepts an
Astropy-readable equinox/date or `of_date`. `of_date` is resolved from the
declared chart observer time. This value controls reference representation,
not catalogue position propagation. An explicit `--reference-equinox` command
value overrides it.

## Stellar selection/report extension (candidate)

`detail.star_labels.names` and `.bayer` are string-list selectors with exact
`IAU:token[,token]` syntax. `.show_full_bayer_designation` is boolean, default
false. Lists default empty. Invalid types, unknown constellation abbreviations,
empty tokens and unsupported Bayer spellings fail validation; absent or
ambiguous catalogue matches fail during resolution before stellar selection.

The new root `reports` table follows `detail` and precedes `styles`.
`reports.stellar_designations` is boolean, default false, enabling per-static-
chart Markdown/JSON discrepancy reports. Sequence requests reject true.

`styles.atlas.stars.labels` and `styles.cartoon.stars.labels` have `color`
(default `none`, inheriting star colour), `font_size` (number, default 7),
`opacity` (number in [0,1], default 1), and `offset` (point, default [0.01,0.01]
in existing projected chart units). Appearance never changes star inclusion.
A CLI selector replaces only its corresponding TOML list; CLI boolean forms
including `--no-stellar-report` override the translated TOML values.

## Constellation publication controls

The stellar presentation stage adds these optional schema-v2 keys:

| Key | Default | Contract |
| --- | --- | --- |
| `detail.content.star_constellations` | `[]` | Nonempty IAU-code list restricts stars to the union of those regions; empty configuration list leaves selection unrestricted. |
| `styles.{atlas,cartoon}.stars.labels.placement` | `"fixed"` | `fixed` or `auto`; automatic placement affects only requested labels. |
| `styles.{atlas,cartoon}.constellation_figures.gap_points` | `"none"` | Inherit 1 point for a location planisphere, 0 elsewhere. A finite nonnegative number overrides this physical clearance beyond the drawn disk, including explicit zero. |
| `products.default.axes_frame` | `true` | Draw the rectangular axes frame. |
| `products.default.show_title` | `true` | Draw the title, retaining it in provenance. |

The existing `export.transparent` now reaches ordinary chart requests as well
as the export configuration. CLI `--transparent`/`--no-transparent` overrides
it; `--no-frame` and `--no-title` override product defaults. CLI equivalents
for content/style are `--stars-in-constellations`,
`--star-label-placement`, and `--constellation-line-gap`. Configuration and
CLI feed the same immutable request contracts.

Celestial-reference repetition uses the positive numeric setting
`grids_references.references.label_repeat_length_factor`, default `5.0`.
Automatic non-polar labels search near visible curve ends; repeat at both
ends when the contiguous visible arc exceeds this many rendered text widths.
Explicit anchors and polar reference furniture preserve their established policy.

### Optional stellar diameter policies (2026-10-11)

Under `styles.atlas.stars` and `styles.cartoon.stars`, optional merged-default
keys `mag_algorithm` (legacy/linear/asinh), `mag_dmin`, `mag_a`, `mag_b` and
`mag_size_reference` configure the canonical typed stellar policy. Positive
finite diameter coefficients are in mm; `mag_b` is a positive magnitude
interval; the reference is a finite magnitude. Legacy remains default and
preserves the established area fields. CLI overrides resolve after style,
mode and family defaults. Diameter laws use an independent sizing reference;
selection is still `detail` and must not extend beyond that reference.

### Quadratic stellar diameter option

`styles.atlas.stars.mag_algorithm` and `styles.cartoon.stars.mag_algorithm`
also accept `quadratic`, alongside legacy, linear and asinh. The shared law
is `d = mag_dmin + mag_a * max(0, mag_size_reference - m)**2`, in mm.
Here `mag_a` is mm per squared magnitude difference; `mag_b` is unused.
No new key or schema version is required. The review candidate sets
`mag_dmin = 0.30`, `mag_a = 0.04`, `mag_size_reference = 8`, and explicitly
uses diameter scale 1. Selection magnitude limits remain independent and
must not exceed the physical law's reference magnitude.

### Regional equatorial edge marks

The optional schema-v2 table selects the shared atlas/regional presentation:

```toml
[grids_references.coordinate_grid.edge_marks]
enabled = false
grid_lines_visible = true
grid_ra_step_hours = 2
grid_minute_labels_visible = false
grid_label_fontsize = 12.0
grid_minor_label_scale = 0.75
grid_frame_width_scale = 1.5
```

`enabled=true` selects configurable RA (default 2h) and 10-degree declination lines, all 10m RA marks,
whole-hour and smaller 20m/40m labels, and 10-degree declination marks/labels.
Font size and frame scale are positive finite numbers; the minor scale is
positive and at most 1. Booleans are strict. Appearance validates even when
disabled. Ordinary chart defaults remain disabled; atlas version-1 presentation
uses the same six appearance values directly and enables markings whenever
equatorial_grid is selected. These are distinct existing configuration formats.

`--equatorial-grid-ticks`/`--no-equatorial-grid-ticks` overrides `enabled`.
The matching appearance flags override TOML; `--no-grid-lines-visible`
keeps edge marks while hiding full curves. Appearance flags require the preset.
Ordinary admission requires regional charts, the equatorial grid and exterior
label band, and a compatible 10-degree declination step. Physical sky reduction
preserves angular coverage and the existing observer-time coordinate semantics.


The integer grid_ra_step_hours must be one of 1,2,3,4,6,8,12. The strict Boolean
grid_minute_labels_visible defaults false and controls only 20m/40m text, not
tick geometry. Their regional CLI counterparts override TOML. Dec labels use
the generic parallel rotation policy at the boundary; lines use 0.65 opacity
and 0.55-point width. Atlas presentation milky_way_color defaults #87CEFA and
controls MW/LMC/SMC fills; index [colours] accepts that optional key too.

The separate atlas chart-presentation TOML supports messier_label_fontsize
(default 7.0 points, finite and positive), independent of legend_fontsize.
The separate version-2 atlas geometry-request TOML accepts exactly one central
field_width_deg or field_height_deg, and optional polar_primary_diameter_deg.
These atlas records are separate from ordinary chart configuration schema v2.

Atlas chart-presentation TOML adds deep_sky_symbol_scale=1.8,
cluster_face_color="yellow", and grid_dec_label_scale=0.8. The first is a
positive finite diameter multiplier; the second is a valid colour string.
The shared ordinary grid edge-mark preset adds grid_dec_label_scale=1.0,
positive and finite, preserving existing ordinary appearance. These independent
label/symbol appearance values do not change chart coverage or catalogue data.


### Atlas index orientation and common-scale publication

The independent schema-version-1 index presentation accepts optional
`layout.orientation = "landscape"` or `"portrait"`. Landscape is the
compatibility default; width/height are oriented accordingly. Portrait draws
the south disk on top with page-oriented labels. See
`examples/atlas_index_style_v3.toml`.

The atlas's existing font, Dec scale, padding and frame multiplier determine
one common physical sky rectangle. The atlas cadence is 1h for nonpolar
sheets and 2h for polar sheets; the ordinary regional grid spacing option
retains its existing meaning. Common-scale publication rejects mixed-field
designs before source loading. An external index PDF requires same-prefix PNG
and SVG companions; all three are published independently inside the batch.

Atlas chart presentation now defaults `grid_ra_step_hours` to 1 and admits
`grid_polar_ra_step_hours`, default 2, independently. The supplied version-3
chart presentation records the accepted 1h/2h policy explicitly. The regional
mark record continues to use its existing single spacing field.


### Atlas sky rectangle and full-frame example (2026-10-13)

The separate version-1 atlas geometry/request page record admits optional
`sky_aspect_ratio`, a finite positive projected sky width/height ratio. This is
geometry, not index or publication presentation. Absence retains the useful-page
ratio and legacy serialized keys; unknown keys still fail admission. The
revision-3 36-chart example fixes 0.616831374967213, paired with chart-style-v4
`grid_frame_width_scale = 1.0` and the existing 12 pt RA/9.6 pt Dec fonts.
Changing presentation cannot reinterpret resolved footprints. No change is made
to general Wenu schema-version-2 chart geometry.


### Open-cluster atlas exclusion and offline review options (2026-10-13)

The separate atlas-chart presentation admits boolean
open_cluster_exclude_infrared_embedded, default false; atlas_chart_style_v5.toml
sets true. It forwards only a render selection to the existing open-cluster
layer. Original catalogue rows remain present. No general chart schema-2
selection key is introduced in this bounded milestone.

The offline tools command's x/y parameter choices, min/max E(B-V), explicit
missing-reddening policy, include-IR/embedded option and optional filtered ECSV
are inspection/curation inputs, separate from atlas TOML. No default numerical
observability threshold is admitted; copied catalogues retain source/selection
provenance. Data/output roots and versioned output names are explicit options.


## Installed current presentation and layout selection

An ordinary command's --config accepts a filesystem overlay or installed chart
preset atlas-v6/scorpius-v1. Regional atlas defaults first inherit the shared
chart subset of atlas-v6, then apply the supplied overlay and explicit CLI
values. Full atlas presentation remains its own version-1 protocol, including
report typography and publication settings; a layout JSON cannot be a chart
configuration. Layout and index preset names use their independently validated
protocols. All presets are installed package resources.

Additional generic style fields: stars.diameter_scale (positive);
open_cluster.face_color, angular_sizes and exclude_infrared_embedded;
globular_cluster.symbol_shape (none/globular_cluster), symbol_size and face_color;
nonstellar.labels_only; supernova_remnant.symbol_scale (positive). Open-cluster
symbol_shape admits circle/open_cluster/cluster_circle. Neutral defaults preserve
existing appearance; physical sizing, detail and geometry retain separate owners.


### Compact Sco installed comparison v2

The installed chart preset `scorpius-v2` retains the v1 catalogue/detail selection and suppresses object labels. Relative to v1, stellar diameters are 70%, cluster and PN symbol diameters 65%, SNR symbol scale 65%, and coordinate label font size and frame-width multiplier 70%. Open-cluster angular diameters and their minimum marker areas scale together using the positive `[styles.atlas.open_cluster].diameter_scale` (default 1.0; cartoon has the same neutral field). Shared label-only nonstellar rendering honors `draw_labels = false`. These controls remain in the existing configuration translation, composition and export owners; scientific catalogue membership and atlas layouts are unchanged. Full atlas v6 defaults remain intact. The regional stereographic print design is still deferred.

Run `wenu_chart regional --center-on Sco --field-width 60 --field-height 50 --config scorpius-v2 --style atlas --mode print --magnitude-limit 7 --output sco_installed_catalogues_v3.png` for the next installed-path visual review. This is a candidate comparison, not a new acceptance receipt.
