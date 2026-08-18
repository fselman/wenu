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

## Exact ordered value inventory

This is the Milestone 46D.1B input to schema design. Values use future TOML
spelling (`solid`, `dashed`, `dotted`, `dash_dot`, `none`) for line styles.
`null` means the implemented value is absent and a documented fallback or
derivation applies. Unless marked otherwise, entries are **public defaults**.

### Observer, subject, family, product, and export

- observer examples: location `La Ligua`; ordinary time
  `2026-08-15 21:00`; binocular time `2026-05-15 22:00`; elevation,
  timezone, ephemeris and data directory `null`;
- subjects: regional single `Cru`; regional group
  `Sgr,Sco,Oph,Ser`; binocular target `centaurus-a`; all other subjects
  `null`;
- every family: position angle `0.0`, mask `false`;
- binocular: stereographic/horizontal, diameter `6.5` degrees;
- regional single/group: stereographic/horizontal, automatic official-region
  framing, explicit width/height `null`;
- planisphere: stereographic/horizontal, visible hemisphere;
- circumpolar: stereographic/horizontal, pole `south`, limiting declination
  `-69.75` degrees;
- all-sky: Mollweide/Galactic, complete sphere;
- product: style `atlas`, mode `print`, all products `false`, language `en`,
  title `null`, extension `.png`;
- mode base: width `7.0` inches, height `null` (**derived** from aspect ratio),
  transparent `false`;
- print: DPI `300`, font/line/symbol/contrast scales `1.0`, prefer vector
  `true`; presentation: DPI `160`, font scale `1.35`, line scale `1.25`,
  symbol scale `1.25`, contrast scale `1.12`, prefer vector `false`;
- export compatibility: DPI `300`, bounding box `tight`, transparent `false`,
  face color `null`, metadata `{}`; circular transparency and effective face
  color are **derived**.

### Detail and content

- resolved neutral detail: all magnitude and minimum-size limits `null`,
  samples `null`, label density `1.0`, enabled layers `null`, grid-label
  layers empty, constellation-star mode `null`, extra stars empty;
- default content layers: stars, constellation lines/labels/boundaries, all
  four coordinate grids, Milky Way, Magellanic Clouds, galaxies, globular and
  open clusters, planetary nebulae, and supernova remnants;
- cartoon content: stars, constellation lines and labels, Milky Way,
  Magellanic Clouds, galaxies, globular clusters, and open clusters;
- cartoon detail: star mode `selected`, bright limit `3.0`, extra stars empty,
  deep sky `false`, named-star labels `false`, galaxy ceiling `8.0`, open
  cluster minimum size `60` arcmin, globular-cluster minimum size `30` arcmin;
- adaptive detail controls: reference width `7.0`, magnitude adjustment per
  octave `0.20`, maximum adjustment `0.50`, adapt layers `true`;
- adaptive levels `(span, stars, galaxies, open, globular, planetary,
  supernova, labels)`: `(3,12,12,0.5,0.2,0.1,0.5,1.30)`,
  `(6.5,11,12,1,0.5,0.2,1,1.20)`,
  `(15,9.5,11.8,2,1,0.5,2,1.05)`,
  `(30,8.2,11.5,4,2,1,4,0.90)`,
  `(60,7.2,11,8,4,2,8,0.72)`,
  `(100,6.5,10.5,15,8,4,15,0.55)`, and
  `(180,6,10,30,15,8,30,0.40)`;
- canonical atlas star ceilings: all-sky/planisphere `5.0`, regional and
  circumpolar `6.5`; binocular stars/galaxies `11.0`, extended samples `73`
  for globular targets otherwise `97`;
- binocular stellar sizing: limiting-magnitude reference, scale `1.0`,
  exponent `0.20`, minimum area `1.0`, maximum area `40.0`.

### Atlas-print semantic style

- canvas: background `white`, foreground `#505050`, label font `8.5`, footer
  color `null`;
- stars: color `#151515`, area scale `0.85`; magnitude sizing fixed reference
  `5.0`, scale `1.5`, exponent `0.35`, minimum area `1.0`, maximum `null`;
  variable and multiple overlays disabled, colors `null`, sizes `28.0`, line
  widths `0.7`, opacity `0.95`;
- Milky Way: fill `#b9d3da`/`0.28`, edge `null`/`0.0`/`0.0`, contour
  `#555555`, width `0.35`, style `dotted`, opacity `0.28`;
- LMC: fill `#b9d3da`/`0.22`, edge `null`/`0.0`, width `0.0`, style `solid`;
  SMC identical except fill opacity `0.18`;
- nonstellar: `#c5a000`, width `0.8`, opacity `0.9`, minimum `30` arcmin,
  labels false/font `7`, dots `12`, dot size `2`;
- galaxy: edge `#b43b37`, width `0.7`, opacity `0.9`, face `null`/`0.0`,
  minimum `6`, labels false/color `null`/font `6`;
- supernova remnant: `#5f844c`, width `0.55`, style `solid`, opacity `0.9`,
  minimum `10`, labels false/color `null`/font `6`;
- globular cluster: `#c5a000`, width `0.8`, opacity `0.9`, minimum `10`,
  labels false/color `null`/font `6`;
- planetary nebula: edge `#6f8e4d`, face `none`, size `18`, width `0.45`,
  opacity `0.95`, labels false/color `null`/font `6`;
- open cluster: `#d2b321`, size `18`, width `0.45`, opacity `0.9`, labels
  false/color `null`/font `6`;
- IAU boundaries: `#777777`, width `0.35`, style `dotted`, opacity `0.65`;
- constellation figures: `#686868`, width `0.35`, style `solid` (currently
  implicit), opacity `0.58`; labels `#5b5b5b`/`0.90`, offset `(0,0)`, center;
- equatorial: `#667788`/`0.35`/solid; ecliptic: orange/`0.35`/dashed;
  Galactic: blue/`0.35`/dashed; AltAz: `#707070`/`0.35`/solid; shared
  opacity `0.45`;
- coordinate labels enabled, fallback color `null`, font `3.5`, opacity `0.85`;
- horizon: altitude `0`, minimum altitude `null`, `#707070`, width `0.55`,
  style `dashed`, opacity `0.80`, z-order `3.5`;
- mask: `#d8d8d8`, opacity `0.42`, z-order `20`;
- chart boundary: background inherits the canvas; `#777777`, width `0.35`,
  style `dotted`, opacity `0.65`, z-order `8.0`; direct chart-constructor
  fallback colors and widths are compatibility implementation defaults
  displaced whenever the composed style is supplied;
- legend: visible, upper right, font `5.7`, title `6.2`, frame true, face white,
  edge `#777777`, opacity `0.90`, one column, text color `null`.

### Mode palettes and transformations

- cartoon semantic base: canvas `#fffdf7`/`#172238`, label font `13.0`;
  stars `#172238`, area scale `1.30`; Milky Way `#dbe8ef`/`0.20`, contour
  `#8aa6b6`/`0.45`/dotted/`0.35`; LMC/SMC fill opacity `0.18`/`0.16`;
  deep-sky colors nonstellar `#b07a17`, galaxy `#a84940`, supernova and
  planetary `#66865d`, globular `#b07a17`, open cluster `#b89028`;
  open/planetary symbol size `16.0`, width `0.55`; boundary
  `#9aa0a6`/`0.30`/dotted/`0.45`; figure
  `#304f78`/`1.15`/solid/`0.95`; label `#203958`/`1.0`; coordinate width
  `0.40`, opacity `0.45`, labels disabled/font `7.0`/opacity `0.75`; horizon
  `#304f78`/`0.75`/dashed/`0.85`; mask `#fffdf5`/`0.45`; legend disabled,
  font/title `7.0`/`7.5`; all unlisted component values match the explicitly
  repeated complete `styles.cartoon` tables in `defaults.toml`; cartoon mode
  realization preserves the translated mask color and opacity;

- atlas presentation palette: sky `#0262AD`, foreground `#F7FBFD`, stars
  `#FFF4CC`, structure `#FFE066`, labels `#FFF0A6`, frame `#BFE7F5`,
  Milky Way `#69B9D6`, deep sky `#FFE08A`;
- cartoon print palette: sky white, foreground/stars/figures/labels/frame/
  Milky Way/footer `#000000`, AltAz `#707070`, equatorial `#667788`, ecliptic
  orange, Galactic blue;
- cartoon presentation palette: sky `#0262AD`, foreground/stars/figures/
  labels/frame/Milky Way `#FFE066`, AltAz/equatorial/footer `#FFFFFF`,
  ecliptic `#FFA500`, Galactic `#66CCFF`;
- cartoon label offset `(0.18,0.14)`, clearance `(0.24,0.20)`, halo opacity
  `0.78`; mode adapters apply the scale factors above (**derived**) and do
  not change geometry or detail.

### Furniture, legends, grids, and implementation constants

- references: state `none`, anchor `null`; labels `Celestial equator`,
  `Ecliptic`, `Galactic plane`; poles none with labels true;
- footer: disabled, application `Wenu`, include version true, copyright null;
  rendered font `7.0`, y `0.018`, left/right x `0.01/0.99` are public
  appearance candidates currently embedded in rendering;
- context: center/grid true; location/date/local time/labels false;
- legend switches: objects/stars/context true, counts false, title `Stars`;
  regional placements upper/lower right; planisphere/all-sky same but outside;
  circumpolar upper right/lower left; binocular objects disabled and stars
  lower right outside;
- magnitude legend: enabled, lower right, title `Stars`, frame true, font/title
  font `null`, marker `o`, edge color `null`, edge width `0`, label spacing
  `0.5`, handle-text pad `0.8`, border pad `0.5`, z-order `1000`, remaining
  colors `null`;
- coordinate-grid samples `721`; equatorial frame `fk5`, equinox `of_date`,
  meridian declination `-90..90`; reference inclusions false; requested grid
  coordinate lists `null`;
- chart sampling/projection constants (`projection_radius`, boundary samples,
  `flip_ew`, automatic framing padding) are **invariants or implementation
  details** until schema design proves a stable public use; current values are
  radius `2.0` for stereographic charts, `1.0` for all-sky, samples `721`,
  east-west flip true, regional framing padding `1.15`.
