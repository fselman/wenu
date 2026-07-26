# Wenu current architecture

Status: as implemented on `feature/regional-stereographic-charts` at commit
`8c8abeb` (Milestone 16).

This document describes the code that exists now. It is not a target design or
a migration plan.

## 1. Architectural summary

Wenu has one canonical chart pipeline:

```text
Observer
  -> CelestialSphere and ordered SkyLayer objects
  -> spherical geometry
  -> StereographicProjection
  -> projected geometry
  -> optional generic preparation
  -> MatplotlibRenderer
  -> Matplotlib artists
```

Astronomy, geometry, projection, preparation, and rendering are separate
responsibilities:

| Concern | Current owner |
|---|---|
| Observation time and location | `Observer` |
| Astronomical data and coordinate transformation | `SkyLayer` implementations |
| Layer ordering and chart orchestration | `CelestialSphere` |
| Coordinate-neutral spherical values | `wenu.spherical` |
| Stereographic projection | `StereographicProjection` |
| Projected Cartesian values | `wenu.projected` |
| Generic clipping and visual preparation | `wenu.rendering` |
| Matplotlib artist creation | `MatplotlibRenderer` |
| Reproducible regional-chart configuration | `RegionalChart` |
| Reusable publication defaults | `PublicationStyle` |

There are no astronomy-aware Matplotlib adapters and no layer-specific drawing
methods in the current pipeline.

## 2. Principal runtime objects

### 2.1 `Observer`

`Observer` represents the observing context: time, latitude, longitude, and the
coordinate frames required by Astropy and Skyfield. Layers use it to transform
catalogue or native-frame coordinates into apparent horizontal coordinates.

### 2.2 `SkyLayer`

`SkyLayer` is the common layer contract:

```python
spherical_geometry(observer)
```

The returned value is a spherical geometry container. A layer does not project
its geometry and does not render it.

The current hierarchy distinguishes two semantic categories:

- `AstronomicalObject`, currently used by `Stars`.
- `GeometricalObject`, used by points, constellation figures, boundaries,
  labels, and coordinate grids.

The distinction is descriptive; both participate through the same
`SkyLayer.spherical_geometry()` contract.

### 2.3 `CelestialSphere`

`CelestialSphere` owns the observer and the ordered collection of active
layers. Its `draw_chart()` method is the canonical orchestration entry point.

For every layer, in order, it:

1. resolves per-layer options;
2. requests spherical geometry;
3. projects that geometry;
4. optionally applies a generic preparation callable;
5. derives renderer options;
6. asks the renderer to draw the projected geometry.

It returns records containing the spherical geometry, projected geometry, and
created artists. These records make the pipeline observable without storing
projected or rendered state inside layers.

`Constellations` is a grouping/facade around constellation-related layers. It
is not itself a `SkyLayer` and does not own projected state.

## 3. Current sky layers

| Layer | Source/native frame | Spherical output | Important behavior |
|---|---|---|---|
| `Stars` | star catalogue, observer time | `SphericalPoints` | magnitude filtering; vectorized points; HIP identifiers and magnitude metadata |
| `CelestialPoints` | named Astropy coordinates | `SphericalPoints` | transforms reference points to observer-time Alt/Az; carries label/style metadata |
| `ConstellationLines` | constellation edge data | `SphericalCurves` | endpoints are evaluated at observer time |
| `ConstellationBoundaries` | official B1875/FK4 boundary polygons | `SphericalPolygons` | polygons are formed and sampled in B1875 before transformation, preserving the intended boundary geometry |
| `ConstellationLabels` | visible-star anchors and boundary information | `SphericalPoints` | projection-independent label anchors; supports per-render selection and minimum-star rules |
| `EquatorialGrid` | equatorial coordinates | `SphericalGrid` | produces named meridian, parallel, and optional reference components |
| `EclipticGrid` | ecliptic coordinates | `SphericalGrid` | produces ecliptic meridians, parallels, and optional ecliptic reference |
| `GalacticGrid` | galactic coordinates | `SphericalGrid` | produces galactic meridians, parallels, and optional galactic-plane reference |

Coordinate-grid curves are generated as spherical geometry and projected like
every other curve. For regional charts, grids may be generated over the full
regional viewport and left to the renderer's axes-patch clipping. An explicit
minimum altitude can instead apply horizon clipping.

## 4. Geometry model

### 4.1 Spherical geometry

`wenu.spherical` contains coordinate-neutral containers:

- `SphericalPoint`
- `SphericalPoints`
- `SphericalCurve`
- `SphericalCurves`
- `SphericalGrid`
- `SphericalPolygon`
- `SphericalPolygons`

Longitudes and latitudes are expressed in degrees. In the chart pipeline the
usual interpretation is azimuth and altitude, but the geometry containers do
not encode that astronomy-specific meaning.

`SphericalPoints` is vectorized because star catalogues and point layers may
contain large numbers of objects. The other collection classes are semantic
wrappers around manageable collections of singular objects, with collection
metadata where needed.

### 4.2 Projected geometry

`wenu.projected` mirrors the spherical model:

- `ProjectedPoint`
- `ProjectedPoints`
- `ProjectedCurve`
- `ProjectedCurves`
- `ProjectedGrid`
- `ProjectedPolygon`
- `ProjectedPolygons`

Projected coordinates are Cartesian `x`, `y` values. Projection preserves
identifiers, labels, names, closure information, and metadata required by
generic preparation and rendering.

`ProjectedGrid` preserves named component groups rather than flattening
meridians, parallels, and reference curves into one anonymous collection.

## 5. Projection and viewport

### 5.1 `StereographicProjection`

`StereographicProjection` is coordinate-neutral. It projects scalars, arrays,
and all supported spherical geometry containers.

An optional `SphericalFrame` defines:

- the tangent point (`pole_lon_deg`, `pole_lat_deg`);
- the chart position angle;
- the orientation used before stereographic projection.

This supports both full-sky and arbitrary tangent-point regional charts.
East-west flipping and projection radius are projection configuration, not
layer or renderer behavior.

### 5.2 `Viewport`

`Viewport` is a pure Cartesian rectangle. It represents the final crop in
projected coordinates and does not know about astronomy or Matplotlib.

The renderer applies a viewport to the axes limits. Matplotlib's axes patch is
also used as the final clip path for points, curves, polygons, and text.

## 6. Generic preparation

`wenu.rendering` contains reusable transformations between projection and
rendering. Current examples include:

- converting magnitude to symbol sizes;
- deriving point styles;
- radial label offsets;
- clipping supported geometry to a minimum latitude.

Preparation functions operate on geometry and return prepared projected
geometry or renderer options. They do not create artists and do not import
astronomical layers.

This stage is optional. It exists so presentation-related transformations do
not leak back into sky-layer data acquisition or into the renderer.

## 7. Rendering

`MatplotlibRenderer` wraps a Matplotlib `Axes`.

Its responsibilities are:

- applying a `Viewport`;
- dispatching on projected geometry type;
- resolving common, per-entity, and per-component styles;
- drawing points, curves, grids, polygons, and labels;
- clipping all relevant artists to the axes patch;
- returning the created Matplotlib artists.

The renderer receives already projected geometry. It contains no catalogue
loading, celestial coordinate conversion, precession, observer-time logic, or
stereographic mathematics.

Low-level `render_*` functions support the renderer implementation, but the
normal public flow is through `MatplotlibRenderer.draw()`.

## 8. Chart orchestration records

The canonical pipeline returns two immutable result records:

- `LayerRenderingResult`: layer, spherical geometry, projected/prepared
  geometry, and artists for one layer.
- `ChartRenderingResult`: projection, renderer, viewport, and the ordered layer
  results for a chart.

These results make intermediate values available for testing and inspection.
They replace the legacy practice of attaching projection and artist state to
domain objects.

## 9. Layer options

`CelestialSphere.draw_chart()` accepts options keyed by layer. A structured
entry can contain:

```python
{
    "geometry": {...},
    "prepare": callable,
    "render": {...} | callable,
}
```

- `geometry` is passed to `spherical_geometry()`.
- `prepare(spherical, projected)` returns the geometry supplied to the
  renderer.
- `render` is either a renderer keyword mapping or a callable deriving that
  mapping from the spherical and projected values.

Flat renderer keyword mappings remain accepted for compatibility.

This mechanism supports per-render selections and styles without mutating
layers or introducing specialized draw paths.

## 10. Regional production API

`RegionalChart` is an immutable regional chart specification. It configures:

- tangent altitude and azimuth;
- angular field width and height;
- position angle or celestial-north-up orientation;
- projection radius and east-west orientation;
- projected crop offset;
- optional constellation-label selection.

It provides constructors centered on:

- an explicit horizontal direction;
- an arbitrary Astropy coordinate;
- the spherical mean of selected constellation-line endpoints.

Its `projection` and `viewport` properties translate angular chart
configuration into the canonical projection pipeline. `render()` delegates to
`CelestialSphere.draw_chart()`; it does not implement another pipeline.

`ExportOptions` centralizes reproducible `savefig` options. `PublicationStyle`
configures the axes and produces layer options for the same canonical
orchestrator.

## 11. Dependency rules

The present architecture enforces these directions:

```text
objects / sky
    -> spherical geometry and coordinate libraries

projection
    -> spherical geometry, projected geometry, spherical frame

generic preparation
    -> spherical/projected geometry

renderer
    -> projected geometry, viewport, Matplotlib

chart APIs
    -> sky orchestrator, projection, viewport, style, renderer
```

In particular:

- `wenu.objects` and `wenu.sky` do not import Matplotlib renderers;
- sky layers do not import projection or projected-geometry modules;
- sky layers expose no direct `draw`, `project`, or Matplotlib-adapter methods;
- renderer code does not import astronomy-domain layers;
- there is one projection-to-render path.

`tests/test_milestone15b_dependencies.py` protects these boundaries.

## 12. Removed legacy architecture

Milestone 15B removed the parallel rendering architecture, including:

- `regional_chart.py`;
- `sky/curves.py` and `CelestialCurve`;
- layer-specific renderer adapter modules;
- direct layer drawing methods;
- renderer-specific state stored by layers;
- the old adapter-oriented tests.

The surviving compatibility projection entry points are covered by regression
tests, but they do not reverse the current dependency direction.

## 13. Current architectural limits

The following are facts about the current implementation, not proposed
solutions:

- Matplotlib is the implemented rendering backend.
- The production convenience API is regional-chart focused; a comparably
  polished public full-sky production API is not yet separate from examples.
- Style is expressed through dictionaries and `PublicationStyle`, not through
  a general backend-independent style object model.
- Layer ordering is explicit and significant because it determines artist
  stacking.
- `CelestialSphere` remains both the sky-layer registry and the canonical
  chart orchestrator.

Future architecture decisions belong in `target_architecture_v0.4.md`, not in
this document.
