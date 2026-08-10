# Wenu implementation reference

**Architecture version:** 0.7
**Status:** Implemented
**Date:** 2026-08-04

This reference records the implemented public chart workflow. Lower-level
geometry, projection, preparation, and rendering APIs remain available for
advanced use, but ordinary chart production uses a resolved composition.

## 1. Canonical public imports

```python
from wenu import (
    AdaptiveDetailPolicy,
    AtlasChartStyle,
    BinocularChart,
    CartoonDetailPolicy,
    CelestialSphere,
    ChartContentOptions,
    ChartLegendSelection,
    ChartStyleOverrides,
    CircumpolarChart,
    DetailOverrides,
    FixedDetailPolicy,
    FullSkyChart,
    LegendOptions,
    MatplotlibRenderer,
    Observer,
    PresentationMode,
    PrintMode,
    RegionalChart,
    ResolvedDetail,
    SkyContentSelection,
    add_chart_arguments,
    chart_detail_overrides,
    compose_chart,
)
```

The stable named choices are:

- chart styles: `"atlas"` and `"cartoon"`;
- output modes: `"print"` (with `"paper"` as an alias) and
  `"presentation"`.

`Observer` owns its loaded Skyfield ephemeris. Call `observer.close()` when
its lifetime ends, or use `with Observer(...) as observer:` for deterministic
cleanup. Existing callers retain automatic finalization as a safety net.

## 2. Independent chart concerns

| Concern | Owns |
|---|---|
| Chart type | projection, framing, viewport, and final boundary |
| Style | visual appearance |
| Output mode | dimensions, DPI, and medium-specific visual scaling |
| Detail policy | astronomical selection and density |
| Legend policy | object, stellar-magnitude, and contextual furniture |

Styles and modes do not change chart geometry. Detail is resolved into
render-local layer options, so sequential exports of the same sky do not leak
selection state.

## 3. Canonical composition and export

```python
composition = compose_chart(
    chart,
    style="atlas",
    mode="print",
    detail=FixedDetailPolicy(
        ResolvedDetail(star_magnitude_limit=6.0)
    ),
    legends=LegendOptions(
        objects=True,
        stellar_magnitudes=True,
        context=True,
    ),
)

result = chart.export(
    sky,
    MatplotlibRenderer(ax),
    "chart.png",
    composition=composition,
)
```

`chart.export()` resolves render-local layer options, invokes the existing
chart renderer, draws requested legends, and saves exactly once. It returns a
`ChartExportResult`; established two-value unpacking remains supported:

```python
rendering, saved = result
```

Compatibility `style=` and `layer_options=` arguments remain available for
existing callers.

Canonical examples may add the complete shared command-line contract with:

```python
add_chart_arguments(parser, default_output="output/example")
```

The parsed request separates product selection, astronomical content,
appearance, and legends. Content and legend switches are opt-in. Explicit
visual overrides are immutable and apply after style/mode resolution:

```python
composition = compose_chart(
    chart,
    style="cartoon",
    mode="presentation",
    style_overrides=ChartStyleOverrides(
        constellation_linewidth=2.0,
        constellation_line_color="white",
    ),
)
```

Omitting `style_overrides` preserves the resolved style and mode defaults.
`chart_detail_overrides(arguments)` applies the caller magnitude limit and
the explicitly selected constellation and coordinate-grid layers relative to
the selected detail policy. Constellation lines, labels, and boundaries are
independent opt-in requests. It retains cartoon constellation-vertex
selection even when line figures are hidden.

Each canonical example exposes independent equatorial, ecliptic, and Galactic
grid and grid-label switches. A `*-grid-labels` switch enables only its own
grid. The grid systems use black, orange, and blue respectively for both
their default lines and numeric labels. The principal equator, ecliptic, and
Galactic plane remain separate furniture selected with
`--grid-references SELECTION`.

Cartoon presentation resolves a trichromatic palette: deep-blue background,
yellow stars/lines/boundaries/context, and white footer credits. Cartoon print
uses white paper with black structure, context, and credits. Circular chart
boundaries obtain their appearance from the resolved cartoon mode without
changing their chart-owned geometry. When Milky Way or Magellanic Cloud
isophotes are selected as cartoon content, they use unshaded dotted contours:
yellow in presentation and black in print.

## 4. Chart types

The canonical workflow supports:

- `RegionalChart`;
- `FullSkyChart`;
- `CircumpolarChart`;
- `BinocularChart`.

Each chart exposes `chart_context`, `render(...)`, and `export(...)` according
to its geometry and boundary requirements. `FullSkyChart` may place its
stereographic tangent point independently of the observer zenith; the observer
still determines the AltAz sky and horizon. `CircumpolarChart` owns its
declination-parallel boundary and circular grid-label anchor; when no explicit
boundary appearance is supplied, it resolves that appearance from the chart
style before delegating clipping to its circular rendering chart.
`BinocularChart` uses the same shared boundary-resolution contract, so direct
binocular compositions receive a visible style-owned aperture rim while an
explicit `boundary_style` retains precedence.
Circular charts, including full-sky planispheres, paint their style-owned sky
color only inside the clipping
boundary. Their default raster export leaves the surrounding figure and axes
area transparent while retaining titles and footer furniture.
The canonical `binocular_object.py` example centers the same binocular chart
family on either Centaurus A (NGC 5128) or Omega Centauri (NGC 5139) through
one target-selection interface and accepts an explicit field diameter.
The binocular stellar-magnitude legend defaults outside the rectangular axes
at lower right so its frame remains clear of the circular aperture.
Its stellar presentation opts into `StellarMagnitudeSizing` with the resolved
limiting magnitude as the reference, so the faintest selected magnitude uses
the configured minimum scatter area. Brighter stars grow by the configured
exponent and are bounded by the configured maximum area. The rendered stars
and stellar magnitude legend use the same sizing configuration.
`ChartContext.horizon_altitude_deg` optionally carries a chart-owned altitude
floor into composition detail application. Circumpolar charts set it to
`-90.0`, so their declination field and reference furniture are not clipped
at the observer's horizon; other circular chart families retain their prior
behavior.

## 4.1 Canonical examples

The supported user examples are exactly:

- `planisphere.py`;
- `regional_constellation_group.py`;
- `regional_constellation.py`;
- `circumpolar.py`;
- `binocular_object.py`.

An installed Wenu distribution provides the `wenu_examples` command. Running
it creates `wenu_examples/` in the current directory and installs these five
scripts from package resources. Existing scripts are preserved unless the
caller supplies `--force`.

Catalogue, symbol, legend, clipping, and historical style demonstrations are
test-local regression fixtures rather than additional public examples.

## 5. Styles and modes

Named styles are resolved by `compose_chart()`:

```python
printed = compose_chart(chart, style="atlas", mode="print")
slides = compose_chart(chart, style="atlas", mode="presentation")
cartoon = compose_chart(chart, style="cartoon", mode="print")
```

Concrete style and mode objects may also be supplied. Use
`cartoon_chart_style(...)` when explicit cartoon label placement or palette
controls are required.

## 6. Detail policies

Available policies include:

- `FixedDetailPolicy` for explicit resolved values;
- `AdaptiveDetailPolicy` for field-size-dependent density;
- `CartoonDetailPolicy` for sparse cartoon content while preserving
  constellation vertices.

`DetailOverrides` modifies a policy without merging content choices into
style or mode. Layer selection is applied locally for each render.

`SkyContentSelection` carries immutable named subsets for one render and is
owned by `ResolvedDetail.content_selection`. `None` preserves a registered
layer's default selection, while an empty set explicitly selects no members
of that family. The v0.8 migration initially applies the catalogue and
constellation-label selections already supported by layer geometry. It also
applies constellation-line and boundary subsets and Milky Way, LMC, and SMC
isophote levels as render-local geometry options. These selections do not
change the registered layers' loaded content or defaults.

## 7. Legends

`LegendOptions` independently controls:

- canonical deep-sky object symbols;
- the visible stellar magnitude scale;
- chart-center and coordinate-system context;
- observer, location, date, and time when applicable.

Legend content is derived from resolved enabled layers. Legends are drawn as
part of export before the single final save.
Planisphere legends use outside placements clear of the circular sky.
`LegendOptions.symbol_labels` and `LegendOptions.stellar_title` permit
example-local language overrides without changing global English defaults.

## 8. Canonical execution core

All chart combinations retain the same execution flow:

```text
catalogues and sky layers
    -> spherical geometry
    -> projection-domain guard
    -> projection
    -> projected geometry
    -> chart preparation
    -> CelestialSphere.draw_chart()
    -> renderer
    -> legends and export
```

The low-level call remains available to advanced callers:

```python
result = sky.draw_chart(
    projection=projection,
    renderer=renderer,
    viewport=viewport,
    layer_options=layer_options,
)
```

## 9. Package imports

Internal implementation imports use responsibility-based packages:

```python
from wenu.geometry.spherical import SphericalCurves, SphericalGrid
from wenu.geometry.projected import ProjectedCurve, ProjectedPoints
from wenu.geometry.frame import SphericalFrame
from wenu.geometry.viewport import Viewport
from wenu.projections.stereographic import StereographicProjection
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.charts.composition import ChartComposition, compose_chart
```

Pre-v0.4 singular top-level geometry modules and the old `wenu.renderers`,
`wenu.regional`, and `wenu.styles` packages do not exist.

## 10. Extension procedure

- Add a chart type only when geometry or framing differs.
- Add a style by composing visual components; do not add projection or export
  behavior to it.
- Add an output mode by implementing `resolve(context)` and preserving chart
  geometry and content.
- Add a detail policy by returning `ResolvedDetail`.
- Extend legends from resolved content and semantic render metadata, never by
  querying catalogues directly.

Every extension must continue through `CelestialSphere.draw_chart()`.

## 11. Compatibility and deprecation

The legacy `cartoon_output_mode()` and `compose_cartoon_chart()` wrappers
remain functional but emit `DeprecationWarning`. Their replacements and the
v0.5 compatibility policy are recorded in `deprecations_v0.5.md`.

## 12. User documentation and reference image

The v0.7 user guide begins at `docs/user_guide/index.md` and contains one page
for each canonical family plus a shared styles, modes, detail, and furniture
reference. `docs/user_guide.md` remains only as a compatibility link.

The README planisphere is the sole checked-in generated chart. Its generating
script, exact arguments, source commit, dimensions, SHA-256 checksum,
destination, and visual approval are recorded in
`docs/user_guide/planisphere.md`. All other generated products remain below
`output/` and outside version control.

### Sgr-Sco-Oph-Ser regional product

`examples/regional_constellation_group.py --group sgr-sco-oph-ser` selects the
Sagittarius, Scorpius, Ophiuchus, and two-part Serpens region. It does not
silently enable a grid. Every canonical family exposes `--altaz-grid`,
`--equatorial-grid`, `--ecliptic-grid`, and `--galactic-grid` plus the
corresponding label switches; regression commands request the required
systems explicitly. The AltAz grid has a black semantic base color, realized
as gray `#707070` for both lines and labels in print modes so it remains
subordinate to black stars. It excludes its altitude-zero circle so it does
not duplicate the chart-owned horizon.
It also enables the canonical outside-region mask by default, producing the
regional emphasis patch without an additional command-line switch.
