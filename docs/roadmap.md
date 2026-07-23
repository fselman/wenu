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

# Remaining work

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

## Commit 12 — Regional charts

Generalize projection to arbitrary tangent points.

Support:

- constellation charts
- binocular charts
- telescope charts
- guide-book figures

using the same rendering pipeline.

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
