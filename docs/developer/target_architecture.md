
# Wenu Target Architecture

**Status:** Target architecture after the first major refactoring

**Primary objective:** Separate astronomical content from projection and rendering while keeping the public API centered on the celestial sphere.

---

# 1. Guiding idea

The fundamental abstraction of Wenu is **the sky**, not the chart.

A chart is a particular representation of the celestial sphere for

- one observer,
- one instant,
- one projection,
- one viewport,
- one rendering style.

Accordingly, the central object remains:

```python
observer = Observer(...)

sky = CelestialSphere(observer)

sky.add_stars(...)
sky.add_constellations(...)
sky.add_boundaries(...)
sky.add_points(...)

sky.draw_chart(...)
```

The user builds a sky.

The sky produces charts.

---

# 2. Overall pipeline

Every chart follows the same pipeline.

```text
Observer
      │
      ▼
CelestialSphere
      │
      ▼
Astronomical layers
      │
      ▼
Spherical geometry
      │
      ▼
Projection
      │
      ▼
Projected geometry
      │
      ▼
Renderer
```

The important observation is that every astronomical object participates in the
pipeline in exactly the same way.

---

# 3. Responsibilities

## Observer

Owns the observing context:

- location
- time
- ephemerides
- astronomical coordinate transformations

It knows nothing about charts.

---

## CelestialSphere

This is the central orchestration object.

It owns astronomical layers and coordinates the generation of charts.

Responsibilities:

- maintain astronomical layers
- request spherical geometry from each layer
- invoke the projection
- invoke the renderer
- preserve drawing order

Conceptually:

```python
sky.draw_chart(
    projection=...,
    viewport=...,
    renderer=...,
)
```

`draw_chart()` coordinates the process.

It does not perform the work that belongs to the individual components.

---

## Astronomical layers

Examples include

- Stars
- CelestialPoints
- CelestialCurves
- Coordinate grids
- ConstellationLines
- ConstellationBoundaries
- DeepSkyObjects
- Milky Way contours

Every layer answers one question:

> What spherical geometry do you contribute to this sky?

Nothing more.

---

# 4. Geometry is the central abstraction

The real common language of the pipeline is geometry.

Every layer first produces spherical geometry.

For example:

```text
Stars
        ─────► SphericalPoints

Points
        ─────► SphericalPoints

ConstellationLines
        ─────► SphericalCurves

CoordinateGrid
        ─────► SphericalCurves

Boundaries
        ─────► SphericalPolygons
```

After that point the pipeline becomes completely generic.

---

# 5. Spherical geometry

The target geometry classes are

```text
SphericalPoint
SphericalPoints

SphericalCurve
SphericalCurves

SphericalPolygon
SphericalPolygons
```

These are pure geometric objects.

They contain

- spherical coordinates
- metadata
- frame identity

They do not know projections or renderers.

---

# 6. Projection

Projection transforms spherical geometry into projected geometry.

It knows only mathematics.

Its responsibility is

```text
Spherical geometry

↓

Projected geometry
```

It must never

- read catalogues
- perform astronomical transformations
- render objects

---

# 7. Projected geometry

Target classes:

```text
ProjectedPoint
ProjectedPoints

ProjectedCurve
ProjectedCurves

ProjectedPolygon
ProjectedPolygons
```

These remain renderer-independent.

They contain only projected geometry and metadata.

---

# 8. Renderer

The renderer consumes projected geometry.

Responsibilities:

- draw projected points
- draw projected curves
- draw projected polygons
- draw labels

The renderer performs no astronomy.

---

# 9. Stars

The purpose of Stars is to represent a stellar catalogue.

Responsibilities:

- catalogue loading
- filtering
- colours
- magnitudes
- HIP lookup
- observer-dependent astronomical coordinates

Its public contribution to the pipeline is

```text
Stars

↓

SphericalPoints
```

It must not know

- stereographic projection
- projected x/y coordinates
- matplotlib
- viewport
- artists
- marker sizes

---

# 10. Constellation lines

Constellation lines store

- constellation identity
- HIP endpoint pairs

They resolve endpoints through Stars and produce

```text
SphericalCurves
```

They never consume projected coordinates stored inside Stars.

---

# 11. CelestialSphere orchestration

Conceptually the orchestration becomes

```text
for each layer

        │
        ▼

layer.spherical_geometry(observer)

        │
        ▼

projection.project(...)

        │
        ▼

renderer.draw(...)
```

Every layer follows the identical sequence.

---

# 12. Dependency direction

The desired dependency graph is

```text
Observer

↓

Astronomical layers

↓

Spherical geometry

↓

Projection

↓

Projected geometry

↓

Renderer
```

There are no reverse dependencies.

In particular

- Stars must not import projection.
- Stars must not import renderers.
- Geometry classes must not import matplotlib.

---

# 13. Immediate refactoring

The first objective is therefore simple.

Remove every projection and rendering responsibility from Stars.

After refactoring:

```text
Stars

↓

SphericalPoints

↓

Projection

↓

ProjectedPoints

↓

Renderer
```

This becomes the canonical pipeline that every future layer follows.

---

# 14. Why this architecture?

This architecture has three important properties.

1. Every astronomical layer follows the same processing path.

2. Projection becomes completely independent of astronomical catalogues.

3. New layers—Milky Way contours, nebulae, galaxies, satellite tracks, custom constellations—can be added without changing the projection or rendering pipeline.

The architecture is therefore centered on the celestial sphere rather than on individual chart types, while still allowing `CelestialSphere.draw_chart()` to remain the principal public interface.
