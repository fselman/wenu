# Wenu public configuration-default audit

This audit is the Milestone 46D.1 authority map for the future versioned TOML
configuration. It records the implemented sources at base commit
`f1d1ec22bbc6373c151c59521cb3aa92968f5355`. It does not authorize a second
runtime registry and does not change current behavior.

## Classification

Every effective value belongs to exactly one class:

- **public default** — a user may reasonably select another stable value;
- **derived value** — computed from public inputs or chart context and retained
  in its Python owner;
- **invariant** — required for scientific, geometrical, or pipeline validity;
- **implementation detail** — renderer or algorithm machinery with no public
  semantic meaning.

Only public defaults belong in `defaults.toml`. Validation, derivation,
catalogue operations, projection mathematics, clipping, renderer dispatch,
and export execution remain Python responsibilities.

## Responsibility map

| Responsibility | Implemented owner | Classification boundary |
| --- | --- | --- |
| observer | `Observer`, example observer arguments | location, time, elevation, timezone, ephemeris and data-directory choices are public; parsed astronomical state is derived |
| subject | request and subject resolvers, packaged groups | default targets, constellations and groups are public; catalogue lookup and alias resolution are behavior |
| family geometry | `charts/view_defaults.py`, chart constructors | projection choice, frame, pole, field, position angle, mask default and limiting declination are public; resolved viewport and projection domain are derived |
| detail | `charts/detail.py`, canonical example product policies | magnitude/size limits, density, enabled layers and label choices are public; spatial selection and adaptive formula results are derived |
| style | `charts/style_components.py`, `charts/presets.py` | semantic canvas, star, isophote, deep-sky, grid, mask and legend appearance is public |
| output mode | `charts/modes.py`, atlas/cartoon mode adapters | dimensions, DPI, scale factors, transparency, vector preference and palettes are public; scaled effective values are derived |
| grids/references | `GridStyle`, grid constructors, furniture | visibility, labels and appearance are public; sampled coordinates and label placement are derived |
| furniture | furniture and legend contracts | reference states, poles, context, footer and legend presentation are public; resolved legend contents and anchors are derived |
| product | `ChartProductOptions` and shared arguments | style, mode, product selection, output stem/path policy and language are public; deterministic suffixes are derived |
| export | `ChartMode`, `ExportOptions`, export workflow | DPI, transparency, face color, bounding-box and padding policies are public; circular transparency and final dimensions are derived |

## Appearance coverage checklist

Milestones 46D.1B through 46D.4 must account for every item below. A checked
item means its owner is identified here, not that it has already moved to
TOML.

- [x] canvas background, foreground and footer colors;
- [x] star color, magnitude-to-area parameters, minimum/maximum area and
  variable/multiple-star symbol size, edge width and opacity;
- [x] Milky Way, LMC and SMC fill, edge and contour colors, opacity, line
  width and `line_style`;
- [x] nonstellar, galaxy, supernova-remnant, globular-cluster,
  planetary-nebula and open-cluster colors, fills, symbols, sizes, edges,
  edge widths, opacity, labels and fonts;
- [x] constellation figure and boundary color, line width, `line_style`,
  opacity, label color, font, alignment and offset;
- [x] equatorial, ecliptic, Galactic and AltAz grid color and `line_style`,
  shared grid line width and opacity, and grid-label appearance;
- [x] horizon color, line width, `line_style`, opacity and z-order;
- [x] outside-mask color, opacity and z-order;
- [x] chart boundary background, color, line width, `line_style`, opacity and
  z-order;
- [x] object and magnitude legend visibility, location, columns, fonts,
  frame, face, edge, opacity and text color;
- [x] reference-line and pole selection, labels, symbol appearance and
  automatic or explicit anchors;
- [x] title, context and footer fonts, colors, labels, padding and placement;
- [x] output width, height, DPI, transparency, face color, bounding box,
  padding and raster/vector preference.

No configurable line-bearing element may omit independent `color`,
`line_width`, and `line_style` keys merely because two current elements share
a Python scale factor or literal.

## Implemented default sources

The exact-value inventory must traverse every source below before 46D.1 can be
closed.

1. `examples/all_sky.py`, `binocular_object.py`, `circumpolar.py`,
   `planisphere.py`, `regional_constellation.py`, and
   `regional_constellation_group.py`;
2. installed example adapters and shared observer, subject, chart, product,
   content, style, legend and command-line argument builders;
3. `ChartViewDefaults` and all six entries in `CHART_VIEW_DEFAULTS`;
4. `ChartRequest`, its nested observer/subject/frame/product/composition
   values, and resolver fallbacks;
5. `SkyContentSelection`, `ResolvedDetail`, `DetailOverrides`, adaptive detail
   policies and per-product example policies;
6. `StellarMagnitudeSizing`, `CanvasStyle`, `StellarStyle`, `IsophoteStyle`,
   `DeepSkyStyle`, `GridStyle`, `MaskStyle`, `LegendStyle`, `ChartStyle`,
   `AtlasChartStyle`, `CartoonChartStyle`, and `PublicationStyle`;
7. `ChartMode`, `PrintMode`, `PresentationMode`, atlas presentation palette,
   cartoon print/presentation palettes, and every mode transformation;
8. grid sampling defaults, reference annotations, pole annotations, chart
   context, footer, legend plans, legend geometry and magnitude-legend style;
9. regional, full-sky, all-sky, circumpolar and binocular chart-constructor
   presentation and geometry defaults;
10. composition, drawing and export defaults including `ExportOptions` and
    circular-output derivations.

## Derived values and invariants excluded from TOML

- projected viewport coordinates, projection-domain guards and clipping;
- natural height derived from width and chart aspect ratio;
- output pixel dimensions derived from physical size and DPI;
- mode-scaled effective fonts, lines and symbols;
- fallback colors derived from foreground or semantic palette values;
- automatic constellation framing, label anchors and collision clearance;
- star areas computed from magnitude sizing and limiting magnitude;
- observer frames, transformed coordinates and observed-cache keys;
- catalogue identities, joins, sampling algorithms and load operations;
- canonical pipeline ordering and the single final export operation;
- supported geometry types, valid projection domains and scientific range
  validation.

## Duplication and conflict register

The audit found these implemented duplications or naming conflicts. They must
be resolved by schema translation, not copied into TOML as parallel keys.

1. `ChartStyle` is the semantic composed owner while `PublicationStyle` is a
   flat compatibility implementation with duplicated defaults.
2. example parsers and shared CLI parsers currently repeat public defaults
   such as style, mode, output, fields, position angle, masks and content.
3. family geometry is declared by `ChartViewDefaults` but some canonical
   examples restate projection, frame, position angle, pole or field values.
4. atlas/cartoon palettes contain literal colors while semantic style sections
   contain their base colors; mode adapters also contain transformation rules.
5. line-style fields currently use Python/Matplotlib spellings such as `-`,
   `--` and `:`. TOML will use the public vocabulary `solid`, `dashed`,
   `dotted`, `dash_dot`, and `none`, translated at the typed boundary.
6. Python uses both `linewidth` and `line_width`, and both `linestyle` and
   `line_style`. TOML will consistently use `line_width` and `line_style`.
7. grid line width and opacity are shared across several coordinate grids in
   `GridStyle`; the schema must expose independent values for each grid even
   if packaged defaults initially match.
8. boundary appearance refers to both IAU constellation boundaries and chart
   frame/clip boundaries. They require distinct responsibility paths.
9. circular transparency, natural height, fallback label colors and palette
   scaling are derived behavior and must not become duplicated public literals.
10. parser defaults cannot remain effective after user TOML support; omitted
    CLI values need a distinct sentinel so precedence remains deterministic.

## Output-mode transformation inventory

- print mode: 300 DPI, unit font/line/symbol/contrast scales, vector preferred;
- presentation mode: 160 DPI, font scale 1.35, line and symbol scale 1.25,
  contrast scale 1.12, vector not preferred;
- natural height is derived from chart aspect ratio when omitted;
- atlas print preserves its base semantic style;
- atlas presentation replaces its palette and scales fonts, lines and symbols;
- cartoon print and presentation each select a palette, suppress variable and
  multiple-star overlays, adapt isophotes to contours, scale appearance and
  apply label clearance/halo presentation;
- no mode transformation may change subject, geometry, selection or masking.

## Closure rule

Milestone 46D.1B must add the exact, ordered value inventory for every public
default named by this source checklist and mark each value public, derived,
invariant, or implementation detail. Only then may Milestone 46D.2 derive the
versioned TOML schema. No runtime configuration code begins in 46D.1.
