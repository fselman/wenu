# Wenu configuration schema version 1

**Status:** Milestone 46D.2 specification
**Schema version:** `1`
**Runtime status:** Packaged and optional partial user documents are strictly
validated and translated through the ordinary view, composition, furniture,
product, and export pipeline

This document is the authoritative structural contract for Wenu's first
versioned TOML configuration. It derives its public paths from
`archive/audits/configuration_default_audit.md`. It specifies names, types, ordering, and
validation without creating a runtime registry or changing current defaults.

## Document boundary

The root is a TOML table containing the scalar `schema_version = 1`, followed
by these top-level tables in this exact order:

1. `observer`
2. `sequence`
3. `subjects`
4. `families`
5. `detail`
6. `styles`
7. `modes`
8. `grids_references`
9. `coordinates`
10. `furniture`
11. `products`
12. `export`

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

### `observer`

- `location`: string
- `time`: string in an Astropy-accepted explicit form
- `elevation`: optional-number
- `timezone`: optional-string
- `ephemeris`: optional-string
- `data_directory`: optional-string

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

### `subjects`

Each family table has exactly one default public subject declaration:

- `all_sky.kind`: `none`
- `planisphere.kind`: `none`
- `regional_single.kind`: `constellations`; `constellations`: string-list
- `regional_group.kind`: `constellations` or `group`;
  `constellations`: string-list; `group`: optional-string
- `circumpolar.kind`: `none`
- `binocular.kind`: `target`; `target`: string

Only the fields required by `kind` may be active. `constellations` must be
nonempty and contain unique IAU abbreviations. A `target`, `group`, and
`constellations` declaration may not compete within one subject.

### `families`

Every family contains `projection`, `coordinate_frame`, `orientation`,
`position_angle`, and `mask`. `orientation` is optional and accepts
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

The listed projection/frame pairs are version-1 invariants. Configuration
may state them for reproducibility but may not invent another pairing.

### `detail`

- `neutral`: optional star and catalogue magnitude limits, optional extended
  object minimum sizes and sample count, positive `label_density`, optional
  enabled layers, grid-label layer list, optional constellation-star mode,
  and extra-star identifier list.
- `content.default_layers` and `content.cartoon_layers`: string-list.
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
may not change observer, subject, family geometry, or masking.

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
