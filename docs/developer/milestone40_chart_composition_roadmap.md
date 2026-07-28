# Milestone 40 — Chart composition and cartoon charts

## Purpose

Milestone 40 will separate four concerns that are presently partly mixed:

1. **Chart type** — projection, geometry, viewport, framing, clipping, and
   coordinate-label placement.
2. **Chart style** — the visual language used to draw the chart.
3. **Chart mode** — adaptations required by the output medium.
4. **Detail policy** — selection and density rules derived from the angular
   field and the physical output size.

The immediate application will be a reusable cartoon-chart preset that can
show constellation-defining stars, constellation lines and names, and a
small number of additional bright or explicitly selected stars.

The work must preserve the current public APIs while the new composition
model is introduced.

## Architectural definitions

### Chart type

A chart type owns geometric and spatial behavior:

- projection and tangent point;
- rectangular or circular viewport;
- field dimensions or limiting declination;
- clipping boundary;
- horizon treatment;
- coordinate-grid geometry;
- coordinate-label placement on the viewport boundary;
- natural aspect ratio.

Initial chart types:

- `RegionalChart`
- `PlanisphereChart`
- `CircumpolarChart`
- `BinocularChart`

`BinocularChart` should be a circular-field specialization of regional
charting, rather than a visual style.

### Chart style

A chart style owns appearance:

- canvas and foreground colors;
- star-size mapping;
- colors and widths of constellation lines and boundaries;
- coordinate-grid appearance;
- typography;
- symbols for catalogued objects;
- Milky Way and Magellanic Cloud appearance;
- masks;
- legend appearance;
- named layer z-orders.

Initial reusable styles:

- `AtlasChartStyle`
- `CartoonChartStyle`

Future styles may include `NightChartStyle` and `BookChartStyle`.

### Chart mode

A chart mode adapts a style to an output medium:

- physical or pixel dimensions;
- DPI and export defaults;
- font scaling;
- line-width scaling;
- symbol-size scaling;
- contrast adjustment;
- raster or vector preferences;
- transparent or opaque export.

Initial modes:

- `PrintMode`
- `PresentationMode`

A mode may scale style properties but must not change their semantic
meaning.

### Detail policy

A detail policy determines which objects and labels are included. Its
decisions depend primarily on the chart's angular field and secondarily on
the physical output size supplied by the mode.

The policy resolves values such as:

- stellar magnitude limit;
- galaxy magnitude limit;
- catalogue-specific selection limits;
- minimum apparent object sizes;
- label density;
- constellation-star selection;
- explicitly selected objects.

The policy must permit explicit overrides.

## Composition model

The public drawing model should converge on:

```python
chart.draw(
    sky,
    style=AtlasChartStyle(),
    mode=PrintMode(),
    detail=AdaptiveDetailPolicy(),
)
```

A convenience preset may bundle commonly paired defaults without merging
their responsibilities:

```python
chart.draw(
    sky,
    preset=CartoonChartPreset(),
    mode=PresentationMode(),
)
```

Conceptually:

```text
chart type    -> geometry, viewport, clipping, placement
detail policy -> selected objects and labels
chart style   -> visual properties
chart mode    -> output-dependent scaling
renderer      -> artists and exported figure
```

## Milestone 40A — Architectural contracts

### Goals

- Introduce explicit protocols or immutable configuration objects for chart
  type context, style, mode, and detail policy.
- Preserve the existing `PublicationStyle` adapter during migration.
- Establish deterministic composition and override precedence.

### Work

1. Define a `ChartContext` returned by a chart type. It should expose:
   - viewport;
   - clip boundary;
   - angular width and height;
   - visible solid angle when available;
   - tangent point;
   - coordinate-label placement strategy;
   - natural aspect ratio.
2. Define a `RenderContext` combining `ChartContext` and the resolved mode.
3. Define a `ResolvedDetail` value object containing effective catalogue
   and label limits.
4. Define a `ChartMode` interface and implement `PrintMode` and
   `PresentationMode`.
5. Define a `DetailPolicy` interface.
6. Specify precedence:
   - explicit call-site override;
   - explicit policy value;
   - adaptive policy result;
   - library default.

### Tests

- Components remain independently replaceable.
- Existing `PublicationStyle` output remains compatible.
- A mode scales appearance without changing layer selection.
- A style does not alter chart geometry.
- A chart type does not choose colors or symbols.

## Milestone 40B — Chart-type geometry

### Goals

Move circular, polar, and projection-domain behavior out of examples and
into reusable chart infrastructure.

### Work

1. Generalize viewport-boundary strategies:
   - rectangular;
   - circular;
   - arbitrary projected boundary.
2. Make coordinate-label anchoring a chart-type responsibility.
3. Move circumpolar circular clipping into `CircumpolarChart`.
4. Move planisphere horizon clipping into `PlanisphereChart`.
5. Introduce `BinocularChart` as a circular-field regional chart.
6. Apply projection-domain polygon clipping automatically during geometry
   preparation.
7. Remove manual clipping and label-anchor overrides from the Milestone 39
   examples.

### Tests

- Rectangular labels appear on the rectangular viewport.
- Planisphere labels appear on the horizon circle.
- Circumpolar labels appear on the limiting-declination circle.
- Binocular layers are clipped to the circular field stop.
- Filled spherical polygons do not produce projection-cap artifacts.

## Milestone 40C — Named layer ordering

### Goals

Complete the named z-order system before adding further styles.

### Work

1. Add named constants in `wenu.rendering.layers` for:
   - constellation boundaries;
   - constellation lines;
   - constellation labels;
   - coordinate grids;
   - coordinate labels;
   - masks;
   - legends and annotations.
2. Replace remaining numeric z-orders in chart styles and legend code.
3. Document the intended back-to-front ordering.

### Tests

- Active style and rendering modules contain no unapproved numeric z-order
  literals.
- All preset styles use the same semantic layer ordering.

## Milestone 40D — Adaptive detail policy

### Goals

Calculate catalogue depth from chart field and output scale.

### Work

1. Implement `AdaptiveDetailPolicy`.
2. Use chart angular area as the primary density variable.
3. Use printable area or pixel dimensions as a secondary density variable.
4. Resolve independent limits for:
   - stars;
   - galaxies;
   - open clusters;
   - globular clusters;
   - planetary nebulae;
   - supernova remnants;
   - labels.
5. Support absolute overrides and relative offsets:

   ```python
   AdaptiveDetailPolicy(
       star_magnitude_limit=11.0,
   )
   ```

   ```python
   AdaptiveDetailPolicy(
       star_magnitude_offset=1.0,
   )
   ```

6. Begin with documented field-size bands. Continuous interpolation should
   wait until visual calibration provides sufficient evidence.

### Initial stellar defaults

These values are provisional calibration points:

| Approximate field width | Stellar magnitude limit |
| ---: | ---: |
| 120 degrees or more | 5.5 |
| 60–120 degrees | 6.5 |
| 30–60 degrees | 8.0 |
| 15–30 degrees | 9.5 |
| 5–15 degrees | 11.0 |
| Less than 5 degrees | 12.0 |

### Tests

- Narrower fields resolve to equal or deeper stellar limits.
- Larger physical output can resolve to equal or deeper detail.
- Explicit limits override adaptive results.
- Relative offsets are applied after adaptive resolution.
- Catalogue classes receive their own resolved limits.

## Milestone 40E — Constellation-star identity

### Goals

Allow a detail policy to select the exact stars that define constellation
figures.

### Work

1. Preserve source stellar identifiers when constellation-line files are
   loaded.
2. Expose an immutable collection:

   ```python
   sky.constellation_lines.star_ids
   ```

3. Support identifiers for:
   - all loaded constellations;
   - selected constellations;
   - visible constellation figures.
4. Match line identifiers against the stellar catalogue before projection.
5. Report unresolved identifiers explicitly rather than silently omitting
   them.
6. Ensure line vertices and star centers are generated from the same
   underlying stellar positions.

### Tests

- Every resolvable constellation vertex has a corresponding plotted star.
- Selected constellations return only their own vertex identifiers.
- Shared stars are deduplicated.
- Missing identifiers generate a clear diagnostic.
- Alternative line systems such as Mapuche remain supported.

## Milestone 40F — Cartoon detail policy

### Goals

Implement the deliberately sparse content selection required by educational
cartoon charts.

### Selection rule

```text
drawn stars =
    constellation-line stars
    union very-bright stars
    union explicitly selected stars
```

### Proposed interface

```python
CartoonDetailPolicy(
    constellation_star_mode="selected",
    bright_star_magnitude_limit=1.5,
    extra_stars=(),
    include_deep_sky=False,
    label_named_stars=False,
)
```

Supported constellation-star modes:

- `"selected"` — vertices belonging to selected constellations;
- `"visible"` — vertices belonging to visible constellation figures;
- `"all"` — all loaded line-system vertices before viewport clipping;
- `"none"` — do not add constellation vertices.

### Default content

| Layer | Cartoon default |
| --- | --- |
| Constellation-line stars | On |
| Additional very bright stars | On |
| Constellation lines | On |
| Constellation names | On |
| Selected bright-star names | Optional |
| Constellation boundaries | Off |
| Coordinate grid | Off |
| Milky Way | Off |
| Deep-sky catalogues | Off |
| Horizon or frame | Determined by chart type |
| Cardinal directions | On for planisphere charts |

### Tests

- Faint constellation vertices remain present.
- Faint field stars not used by constellation figures are absent.
- Bright non-constellation stars remain present.
- Explicitly selected stars remain present.
- Star identifiers are deduplicated across all three sources.

## Milestone 40G — Cartoon visual style

### Goals

Implement a clear, sparse visual language suitable for teaching.

### Initial appearance

- high-contrast canvas;
- simple filled stellar disks;
- magnitude-dependent star sizes;
- prominent but restrained constellation lines;
- large readable constellation names;
- no variable- or multiple-star overlays;
- no boundaries by default;
- optional equator, ecliptic, cardinal directions, and named stars.

The first implementation should be original and configurable rather than a
literal reproduction of a published atlas design.

### Proposed interface

```python
CartoonChartStyle(
    sky_color="white",
    star_color="black",
    constellation_line_color="black",
    constellation_label_color="black",
    draw_constellation_boundaries=False,
)
```

### Tests

- The style can be applied unchanged to every supported chart type.
- Variable- and multiple-star overlays are disabled by default.
- Style selection does not change the resolved stellar set.
- Print and presentation modes preserve the same visual identity.

## Milestone 40H — Presets and legend metadata

### Goals

Provide convenient presets while keeping the underlying components
independent.

### Work

1. Add `CartoonChartPreset`, which composes:
   - `CartoonChartStyle`;
   - `CartoonDetailPolicy`.
2. Retain explicit style/detail arguments for advanced use.
3. Make legend coordinate metadata derive from the active grid rather than
   assuming FK5/J2000.
4. Generate legend symbols from the registered symbol library or layer
   descriptors.
5. Let chart type provide frame-specific context such as observer, time,
   horizon, tangent point, or limiting declination.

### Tests

- Preset expansion is equivalent to explicit style/detail composition.
- Legend metadata matches the actual coordinate grid and equinox.
- Legend symbols match active layer symbols.
- Disabling a layer removes its legend entry.

## Milestone 40I — Portability examples and regression tests

### Required examples

Create both print and presentation versions where appropriate:

1. rectangular regional cartoon;
2. circular La Ligua planisphere cartoon;
3. southern circumpolar cartoon;
4. binocular-field cartoon;
5. selected-constellation teaching chart;
6. full visible-constellation orientation chart.

All generated images should be written beneath:

```text
output/milestone40/
```

### Portability requirement

The same unmodified `CartoonChartStyle` and `CartoonDetailPolicy` must work
with every example. Examples may specify chart geometry, observer, time,
selected constellations, and explicit teaching targets, but must not patch
renderer or style internals.

### Regression tests

- Existing Atlas charts retain their appearance within accepted tolerances.
- Existing examples require no custom renderer callbacks.
- Full test suite passes.
- Source scans enforce package boundaries and named z-orders.

## Migration strategy

The work should be incremental:

1. Introduce interfaces and adapters without changing current behavior.
2. Promote reusable geometry behavior out of examples.
3. add named z-orders;
4. introduce adaptive detail resolution;
5. expose constellation vertex identifiers;
6. implement cartoon detail selection;
7. implement cartoon appearance;
8. add convenience presets;
9. migrate examples;
10. remove compatibility paths only after all active examples use the new
    composition API.

No clean break is required inside Milestone 40. A clean public API can be
presented immediately while the old flat `PublicationStyle` remains an
internal compatibility adapter.

## Completion criteria

Milestone 40 is complete when:

- chart type, style, mode, and detail policy have explicit non-overlapping
  responsibilities;
- catalogue depth responds to chart field and output dimensions;
- cartoon charts select constellation-line stars reliably;
- the same cartoon preset works on rectangular, circular, polar, and
  binocular charts;
- chart examples contain no manual projection clipping or label-anchor
  callbacks;
- legend metadata describes the actual coordinate system;
- all z-orders use named layer constants;
- Atlas charts remain operational;
- all tests and visual checks pass.

