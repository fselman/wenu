# Wenu current architecture

**Status:** Implemented on `feature/regional-stereographic-charts` through
commit `c7feaf7` (Milestone 23)  
**Architecture version:** 0.4  
**Date:** 2026-07-26

This document describes the implemented architecture. Historical targets and
migration plans are retained under `docs/developer/archive/`.

## 1. Purpose

Wenu produces reproducible, publication-quality static charts of the sky. It
supports regional charts and observer-dependent full-sky charts through one
pipeline. It is not designed as an interactive planetarium.

## 2. Canonical pipeline

Every drawable sky layer follows:

```text
Observer
  → CelestialSphere
  → SkyLayer.spherical_geometry()
  → spherical geometry
  → projection
  → projected geometry
  → optional preparation
  → renderer
  → graphical artists
```

`CelestialSphere.draw_chart()` is the only chart-execution pipeline. Regional
and full-sky chart specifications configure and delegate to it.

## 3. Package structure

```text
src/wenu/
├── __init__.py
├── observer.py
├── coordinates.py
├── objects/
│   ├── astronomical_object.py
│   └── stars.py
├── sky/
│   ├── sky_layer.py
│   ├── geometrical_object.py
│   ├── celestial_sphere.py
│   ├── rendering_results.py
│   ├── points.py
│   ├── constellation_lines.py
│   ├── constellation_boundaries.py
│   ├── constellation_labels.py
│   ├── constellations.py
│   └── coordinate_grids.py
├── geometry/
│   ├── spherical.py
│   ├── projected.py
│   ├── frame.py
│   ├── clipping.py
│   └── viewport.py
├── projections/
│   └── stereographic.py
├── charts/
│   ├── regional.py
│   ├── full_sky.py
│   └── styles.py
├── rendering/
│   ├── preparation.py
│   ├── matplotlib.py
│   ├── _matplotlib_primitives.py
│   ├── _matplotlib_axes.py
│   └── layers.py
├── catalogs/
├── resources.py
└── data/
```

## 4. Responsibilities

| Concern | Owner |
|---|---|
| Time, location, and observer frames | `Observer` |
| Physical catalogue objects | `objects/` |
| Celestial constructs and layer geometry | `sky/` |
| Coordinate conversion helpers | `coordinates.py` |
| Coordinate-neutral values and algorithms | `geometry/` |
| Map projections | `projections/` |
| Chart specifications and styles | `charts/` |
| Preparation and graphical backends | `rendering/` |

## 5. Observer and sky layers

`Observer` owns observing time and location. Concrete layers transform their
native data into observer-time horizontal longitude and latitude.

Every drawable layer implements:

```python
spherical_geometry(observer, **geometry_options)
```

Layers do not project or draw themselves. Implemented layers include:

- vectorized Hipparcos stars;
- celestial reference points;
- observer-time constellation lines;
- B1875-constructed IAU constellation boundaries;
- projection-independent constellation labels;
- equatorial, ecliptic, and Galactic grids.

`Constellations` is a grouping façade, not a layer and not a rendering path.

## 6. Geometry

`geometry/spherical.py` and `geometry/projected.py` provide corresponding
point, curve, grid, and polygon types.

Singular curve and polygon types represent one object. Their collection
classes are lightweight semantic wrappers. `SphericalPoints` and
`ProjectedPoints` remain vectorized for catalogue-scale processing.

Projection preserves identities, labels, names, closure, component grouping,
and applicable metadata.

`SphericalFrame` rotates generic spherical coordinates to an arbitrary tangent
frame. `Viewport` is a pure projected Cartesian rectangle.

## 7. Projection

`StereographicProjection` is independent of observers, sky layers, chart
styles, and Matplotlib. It supports:

- scalar and vector inputs;
- all implemented spherical geometry containers;
- arbitrary tangent points;
- position angle;
- east-west orientation;
- configurable radius.

The tangent point and the observer are separate concepts. Chart
specifications choose the projection frame; layers obtain the horizontal sky
from the observer.

## 8. Preparation

`rendering/preparation.py` contains backend-independent transformations:

- magnitude-to-area conversion;
- per-point style derivation;
- label offsets;
- clipping to spherical latitude.

Latitude clipping interpolates curve intersections with the limiting
latitude. This gives explicit endpoints at the horizon rather than merely
discarding the first hidden sample.

## 9. Rendering

`MatplotlibRenderer` consumes projected geometry. It:

- applies rectangular viewports;
- dispatches by projected geometry type;
- applies common, entity, and grid-component styles;
- draws points, curves, polygons, grids, and labels;
- supports a projected closed clip boundary;
- returns the created artists.

The projected clip boundary permits a full-sky horizon to differ from the
projection center. Rendering contains no astronomical transformation or map
projection.

## 10. Chart specifications

### 10.1 `RegionalChart`

`RegionalChart` is immutable and supports:

- explicit horizontal centers;
- centers derived from Astropy coordinates;
- centers derived from constellation figures;
- arbitrary position angles or celestial north up;
- rectangular angular fields and crop offsets;
- reproducible figure sizing and export.

### 10.2 `FullSkyChart`

`FullSkyChart` represents the sky above an observer-defined limiting altitude.
It supports:

- a tangent point independent of the observer zenith;
- a configurable horizon altitude;
- arbitrary position angle and east-west orientation;
- a projected horizon boundary and derived viewport;
- reproducible figure sizing and export.

The observer defines the AltAz sky and horizon. The tangent point defines the
stereographic origin. The chart validates that the retained sky does not
contain the projection antipode.

The standard example places the tangent point at the South Celestial Pole
while keeping the observer zenith toward the top of the chart.

Neither chart type uses a parallel rendering pipeline, and there is no
speculative common `Chart` superclass.

## 11. Styles and export

`PublicationStyle` configures Matplotlib axes and produces structured layer
options. A chart may provide the authoritative horizon altitude while the
style supplies its graphical policy.

`ExportOptions` fixes DPI, bounding-box behavior, transparency, face color,
and metadata. Physical figure size and raster DPI remain independent.

## 12. Structured layer options

Per-render behavior is configured as:

```python
{
    "geometry": {...},
    "prepare": callable,
    "render": {...} | callable,
}
```

Chart-specific choices are supplied through these options rather than by
mutating shared layers.

## 13. Results

The pipeline returns immutable inspection records:

- `LayerRenderingResult`;
- `ChartRenderingResult`.

They retain the layer, spherical value, prepared projected value, artists,
projection, renderer, and viewport as applicable.

## 14. Dependency rules

The permitted high-level directions are:

```text
objects/ ───────┐
                ├─→ sky/ ──────────→ geometry/
coordinates.py ─┘

projections/ ──────────────────────→ geometry/
rendering/ ────────────────────────→ geometry/
charts/ ─→ sky/, geometry/, projections/, rendering/
```

Reverse dependencies and obsolete module paths are prohibited by:

- `tests/test_milestone15b_dependencies.py`;
- `tests/test_milestone22_package_boundaries.py`.

There are no forwarding modules for the pre-v0.4 layout.

## 15. Public API

Intentional top-level exports include:

```python
from wenu import (
    CelestialSphere,
    ExportOptions,
    FullSkyChart,
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
    RegionalChart,
    StereographicProjection,
    Viewport,
)
```

Internal module organization is not itself a public compatibility promise.

## 16. Current limits

Version 0.4 intentionally provides:

- one map projection implementation;
- one graphical backend;
- static rather than interactive output;
- explicit dictionary-based layer options;
- no abstract renderer hierarchy;
- no common chart superclass.

These are deliberate v0.4 boundaries rather than unfinished parallel
architectures.
