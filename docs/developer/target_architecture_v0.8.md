# Wenu target architecture v0.8

**Status:** Proposed
**Source:** `current_architecture_v0.7.md`
**Migration plan:** `wenu_migration_0.7_to_0.8.md`

Version 0.8 begins by completing the semantic coordinate-grid family with an
observer-local `AltAzGrid`. Its semantic detail name is `altaz_grid`, its
public controls are `--altaz-grid` and `--altaz-grid-labels`. Its base
semantic line and label colors are black; print modes realize both as gray
`#707070` so the observer grid remains subordinate to black stars.

AltAz geometry enters the existing spherical-geometry pipeline directly as
azimuth meridians and altitude parallels. It does not create a second grid,
projection, clipping, rendering, or export pipeline. The altitude-zero circle
is excluded by default because the horizon is chart-owned geometry and must
remain visible independently of optional content. AltAz therefore adds no
value to `--grid-references`.

Canonical examples configure the fourth grid declaratively without enabling
it by default. Detail owns selection, style owns appearance, and label
selection remains render-local and grid-specific.

## Reusable celestial content and observed geometry

The canonical pipeline must support loading one complete astronomical data
set and deriving several chart products from it without repeatedly reading or
permanently filtering the same catalogues. Construction defines what content
is available; resolved detail defines what a particular chart includes.

Wenu distinguishes three conceptual states while retaining
`CelestialSphere` as the compatible public orchestration facade:

1. observer-independent catalogue and native geometry, including stellar and
   deep-sky catalogues, constellation topology, boundaries, and isophotes;
2. observer- and time-dependent spherical geometry in horizontal AltAz
   coordinates;
3. render-local content selection followed by chart-owned projection,
   framing, masking, and boundary application.

AltAz remains the canonical spherical geometry entering projection. It is not
an intrinsic stored coordinate of an observer-independent catalogue. Layers
may cache their AltAz realization for a particular observer and instant, but
that cache must be invalidated or separately keyed when the location, time,
ephemeris, or source data changes.

Catalogue load ceilings and sampling quality must be sufficient for every
requested chart. Shallower magnitude limits, named object selections,
constellation subsets, isophote levels, and enabled content are render-local
detail choices. Rendering one chart must not mutate the available catalogue
content or affect a subsequent chart made from the same celestial sphere.

This refinement does not create a second sky or rendering pipeline.
`CelestialSphere.draw_chart()` remains the execution core, and every layer
continues to provide spherical geometry to the established projection,
preparation, rendering, furniture, and export stages.

## Future time-dependent layers

The same layer contract must accommodate future solar-system and artificial
satellite content without treating dynamic AltAz coordinates as immutable
catalogue data.

- planets and the Moon derive apparent topocentric state from an ephemeris,
  observer, and instant;
- artificial satellites derive topocentric state from identified orbital
  elements and an instant, while tracks additionally own a sampled time
  interval;
- static catalogue data may be reused across times, but observed geometry is
  cached only under a complete observer/time/source key;
- dynamic layers enter the same spherical-geometry, projection, clipping,
  rendering, legend, and export pipeline as existing layers.

Public abstractions beyond `CelestialSphere` are introduced only when the
implemented caching and time-sequence requirements demonstrate that they are
necessary. The migration begins with internal ownership boundaries and
render-local selection rather than a speculative parallel object model.
