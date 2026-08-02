# Wenu implementation reference

**Architecture version:** 0.5
**Status:** Implemented
**Date:** 2026-08-02

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
    compose_chart,
)
```

The stable named choices are:

- chart styles: `"atlas"` and `"cartoon"`;
- output modes: `"print"` (with `"paper"` as an alias) and
  `"presentation"`.

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

## 4. Chart types

The canonical workflow supports:

- `RegionalChart`;
- `FullSkyChart`;
- `CircumpolarChart`;
- `BinocularChart`.

Each chart exposes `chart_context`, `render(...)`, and `export(...)` according
to its geometry and boundary requirements. `FullSkyChart` may place its
stereographic tangent point independently of the observer zenith; the observer
still determines the AltAz sky and horizon.

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

## 7. Legends

`LegendOptions` independently controls:

- canonical deep-sky object symbols;
- the visible stellar magnitude scale;
- chart-center and coordinate-system context;
- observer, location, date, and time when applicable.

Legend content is derived from resolved enabled layers. Legends are drawn as
part of export before the single final save.

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
