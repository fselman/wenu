# Wenu Development Roadmap

## Vision

Wenu is a Python package for producing publication-quality astronomical charts.

The architecture is intentionally layered:

```
Astronomical objects
        ↓
Coordinate transformations
        ↓
Projection
        ↓
Projected geometry
        ↓
Rendering
        ↓
Matplotlib (current backend)
```

The objective is to keep astronomy, geometry and rendering completely separated.

---

# Completed

## Commit 0
Project skeleton

## Commit 1
Observer abstraction

- Observer owns location, time and ephemerides.
- Named observing sites.
- Skyfield/Astropy integration.

## Commit 2
Viewport abstraction

- Projection-independent viewport.
- Defines visible Cartesian region.

## Commit 3
Projected geometry

- Introduced:
  - ProjectedPoint
  - ProjectedCurve
  - ProjectedPolygon
- Projection returns geometry instead of plotting.

## Commit 4
Visibility segmentation

- Cartesian clipping.
- Curve segmentation.
- Visibility handled before rendering.

## Commit 5
Cartesian clipping

- Robust clipping against viewport.
- Projection remains renderer-independent.

## Commit 6
Rendering primitives

Renderer package now provides:

- render_point()
- render_points()
- render_curve()
- render_polygon()

Rendering depends only on projected geometry.

Matplotlib-specific helpers are isolated inside:

```
renderers/
    matplotlib.py
    matplotlib_axes.py
```

## Commit 7
Star rendering

Stars now:

- load catalog
- compute apparent positions
- project coordinates
- compute marker sizes
- delegate rendering to renderer primitives

Stars no longer call Matplotlib directly.

---


## Commit 8 — Celestial Points

Render:

- SCP / NCP
- Galactic poles
- Ecliptic poles
- Galactic center
- Anticenter
- Equinoxes
- Solstices

using renderer primitives.

Goal:

```
CelestialPoints
        ↓
render_point()
```

---

## Commit 9 — Celestial Curves

Render:

- celestial equator
- ecliptic
- galactic equator
- constant declination
- constant latitude

using

```
ProjectedCurve
        ↓
render_curve()
```

---

## Commit 10 — Constellations

Render

- constellation lines
- boundaries
- labels

All rendering delegated to renderer primitives.

---

## Commit 11 — Complete chart scene

First complete publication-quality chart produced entirely with the new architecture.

---
# Remaining work

---
## Commit 12a — Regional charts

## Commit 12a — Regional and constellation charts

- Generalize the projection to arbitrary tangent points.
- make the viewport or chart aperture an explicit scene-level object rather than an implicit Matplotlib clip patch.

Produce regional charts, beginning with constellation-centered charts, using the same projected-geometry and rendering pipeline.

The generalized framing should later support:

- binocular fields;
- telescope fields;

using the same rendering pipeline.

## Commit 12b — Rendering and clipping corrections

Resolve inconsistencies discovered in the first complete chart:

- stars are currently limited using an altitude threshold;
- celestial curves are clipped only by the rectangular axes viewport;
- constellation lines, boundaries and labels are clipped by the circular sky patch;
- a constellation boundary near the celestial pole contains a spurious segment extending toward the pole.

Goals:

- define a single explicit clipping policy for the chart scene;
- distinguish astronomical visibility from geometric clipping;
- apply clipping consistently across all drawable layers;
- split projected paths at coordinate and projection discontinuities;
- remove spurious long segments near poles and coordinate wraps.

---

# Future work

## Milky Way

- isophotes
- HEALPix support
- FITS import utilities

## Deep-sky objects

- Messier
- NGC
- custom catalogs

## Coordinate grids

- Equatorial
- Galactic
- Ecliptic

## Labels

Collision avoidance.

## Styling

Themes.

## Additional renderers

Possible future backends:

- SVG
- PDF
- Cairo

without changing astronomical code.
