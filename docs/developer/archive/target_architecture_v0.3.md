# Wenu Target Architecture

**Version:** 0.3\
**Date:** 2026-07-24\
**Status:** Draft

------------------------------------------------------------------------

# 1. Guiding Philosophy

The fundamental abstraction of Wenu is **the celestial sphere**, not the
chart.

A chart is one representation of the celestial sphere for a particular
observer, projection and rendering style.

Every element that may appear on a chart is represented as a
**SkyLayer**.

------------------------------------------------------------------------

# 2. Overall Processing Pipeline

``` text
Observer
    ↓
CelestialSphere
    ↓
SkyLayer
    ↓
Spherical Geometry
    ↓
Projection
    ↓
Projected Geometry
    ↓
Renderer
```

Every layer follows exactly the same pipeline.

------------------------------------------------------------------------

# 3. Observer

Responsible for:

-   observing location
-   observing time
-   astronomical transformations
-   ephemerides

Future versions may support observers on bodies other than Earth.

------------------------------------------------------------------------

# 4. CelestialSphere

Responsibilities:

-   own SkyLayers
-   preserve drawing order
-   orchestrate chart generation
-   invoke projection
-   invoke renderer

------------------------------------------------------------------------

# 5. SkyLayer

Every drawable entity derives from:

``` text
SkyLayer
```

Two major subclasses exist.

## 5.1 AstronomicalObject

Represents physical astronomical entities.

``` text
AstronomicalObject
    ├── Stars
    ├── StarClusters
    ├── Galaxies
    ├── MilkyWay
    ├── Nebulae
    ├── MinorPlanets
    ├── Comets
    └── ...
```

Each astronomical object produces spherical geometry appropriate to its
representation.

### Stars

The first concrete implementation.

Responsibilities:

-   catalogue loading
-   filtering
-   magnitudes
-   colours
-   HIP/Gaia lookup
-   observer-dependent coordinates

Output:

``` text
Stars
    ↓
SphericalPoints
```

`Stars` knows nothing about projections or rendering.

## 5.2 GeometricalObject

Represents constructs on the celestial sphere rather than physical
astronomical entities.

``` text
GeometricalObject
    ├── ConstellationLines
    ├── ConstellationBoundaries
    ├── CoordinatesGrid
    ├── CelestialPoints
    └── ...
```

Examples:

-   constellation stick figures
-   IAU boundaries
-   coordinate grids
-   celestial poles
-   equinoxes
-   galactic center
-   ecliptic cardinal points

Like astronomical objects, every geometrical object produces spherical
geometry and participates in the same rendering pipeline.

------------------------------------------------------------------------

# 6. Geometry

## Spherical Geometry

-   SphericalPoint
-   SphericalPoints
-   SphericalCurve
-   SphericalCurves
-   SphericalGrid
-   SphericalPolygon
-   SphericalPolygons

## Projected Geometry

-   ProjectedPoint
-   ProjectedPoints
-   ProjectedCurve
-   ProjectedCurves
-   ProjectedGrid
-   ProjectedPolygon
-   ProjectedPolygons

Singular classes represent one geometric object. Projected curve and polygon
collections are lightweight wrappers around a reasonably small number of
their corresponding singular objects and may carry collection-level
metadata.

`ProjectedPoints` is intentionally different from `ProjectedPoint` and from
the other projected collection classes. It uses vectorized arrays rather
than wrapping large numbers of scalar point instances. This supports
efficient catalogue projection, masking, clipping and rendering.

------------------------------------------------------------------------

# 7. Projection

Projection transforms spherical geometry into projected geometry only.

Projection has no knowledge of astronomical or geometrical layers.

------------------------------------------------------------------------

# 8. Renderer

Consumes projected geometry and produces graphical output.

Renderer has no astronomical knowledge.

------------------------------------------------------------------------

# 9. Orchestration

``` text
for each SkyLayer

geometry = layer.spherical_geometry(observer)

projected = projection.project(geometry)

renderer.draw(projected)
```

------------------------------------------------------------------------

# 10. Dependency Direction

``` text
Observer
    ↓
CelestialSphere
    ↓
SkyLayer
    ↓
AstronomicalObject / GeometricalObject
    ↓
Spherical Geometry
    ↓
Projection
    ↓
Projected Geometry
    ↓
Renderer
```

Reverse dependencies are not permitted.

------------------------------------------------------------------------

# 11. Immediate Refactoring Goal

Establish the canonical pipeline beginning with Stars:

``` text
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

This same architecture will subsequently be adopted by every
`AstronomicalObject` and `GeometricalObject`.
