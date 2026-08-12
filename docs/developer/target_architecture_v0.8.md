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

Wenu distinguishes four conceptual states while retaining
`CelestialSphere` as the compatible public orchestration facade:

1. observer-independent catalogue and native geometry, including stellar and
   deep-sky catalogues, constellation topology, boundaries, and isophotes;
2. observer- and time-dependent spherical geometry in horizontal AltAz
   coordinates;
3. an observer-bound chart view defining projection, framing, orientation,
   viewport, masking, and the final boundary;
4. render-local content selection, projection execution, preparation,
   rendering, furniture, and export.

The maximal `CelestialSphere` is an observer-independent loaded-content container.
It owns load ceilings, catalogue provenance, native geometry, and
caches, but it does not own one authoritative observer or instant.  The
observer enters at the chart-view boundary.  A view binds an observer and
instant to a chart family, subject, projection, frame, orientation, viewport,
mask, and boundary without acquiring style, detail, furniture, renderer, or
output state.  Observer ownership remains with the caller or the request
facade that created it; neither the maximal sphere nor a view closes an
observer it did not create.

AltAz remains the canonical spherical geometry entering projection. It is not
an intrinsic stored coordinate of an observer-independent catalogue. Layers
may cache several AltAz realizations, but each is keyed by the complete
observer location, instant, ephemeris, source, and geometry-quality identity.
Changing observer or instant selects or creates another realization; it does
not require reloading the maximal sphere.

Catalogue load ceilings and sampling quality must be sufficient for every
requested chart. Shallower magnitude limits, named object selections,
constellation subsets, isophote levels, and enabled content are render-local
detail choices. Rendering one chart must not mutate the available catalogue
content or affect a subsequent chart made from the same celestial sphere.

This refinement does not create a second sky or rendering pipeline.
`CelestialSphere.draw_chart()` remains the execution core and receives the
view's observer explicitly.  During migration its existing bound-observer
form remains compatible.  Every layer continues to provide spherical
geometry through `SkyLayer.spherical_geometry(observer)` to the established
projection, preparation, rendering, furniture, and export stages.

## Declarative user chart requests

Ordinary users must not have to reproduce the catalogue-loading, target
coordinate, projection, composition, Matplotlib, furniture, or export code in
the canonical examples. A user-facing request describes the desired chart;
Wenu resolves that request through the same maximal sphere and canonical
pipeline.

A complete ordinary request contains only the choices a user can reasonably
be expected to make:

- observer location and local date/time;
- chart family;
- subject, expressed as a catalogue identifier, common target name,
  coordinate, constellation, or constellation group;
- field diameter or width/height when the automatic framing is not desired;
- optional mask and astronomical content choices;
- style, output mode, legends, language, title, and destination.

Wenu owns the remaining procedure. In particular, it resolves packaged target
identities and aliases, selects the catalogue families required to represent
the target, obtains a compatible maximal sphere, constructs the chart,
resolves detail and furniture, creates the renderer, and exports exactly once.
Target resolution remains offline and provenance-controlled by default.
Unknown and ambiguous names produce explicit diagnostics rather than an
empty, apparently successful chart.

The Python request API and command-line interface are two adapters over one
immutable request contract. Regional requests accept arbitrary IAU
constellation sets as well as named packaged groups. Binocular requests accept
packaged object identifiers or explicit coordinates and are not limited to a
hard-coded example-target dictionary. The request resolver must verify that
the target and requested content are available under the selected load
profile.

An arbitrary constellation set is the ordinary regional-group primitive.
Packaged groups remain optional curated aliases carrying preset framing or
content, not the implementation of grouping. The shared command-line adapter
normalizes only the public subject vocabulary; the constellation resolver
retains IAU validation and Serpens identities, and the regional chart retains
automatic spherical framing.

A selected constellation set may later define several disjoint mask patches
on an observer-visible planisphere. Visibility is resolved only after the
observer-bound chart exists: wholly invisible official regions are omitted,
partly visible regions are clipped at the horizon and final chart boundary,
and separate visible regions remain separate patches. A later Mollweide
all-sky view reuses the same projection-neutral resolved set without horizon
rejection and owns its elliptical boundary and longitude-seam splitting in
the established projection and clipping pipeline.

Canonical examples become short declarations using this public request API.
They remain reproducible demonstrations and regression authorities, not
templates that require users to copy internal orchestration. Existing
lower-level chart, composition, layer, and renderer APIs remain available for
advanced callers.

## Three-stage ordinary Python interface

The ordinary Python interface presents one stable three-stage workflow:

1. generate reusable observer-independent celestial content;
2. obtain an observer-bound geometrical chart view for an instant, family,
   subject, projection, frame, orientation, and optional mask;
3. draw that view with explicit detail, style, furniture, title, and output
   choices.

The public vocabulary must remain small enough for canonical examples to use
few imports and fewer than 70 lines, including their command-line adapter.
Family defaults make concise calls possible, while each canonical example
spells out the important defaults so that a user can copy and alter them.
The immutable request graph remains the canonical internal and advanced
contract; the ordinary interface translates friendly arguments into that
graph instead of adding another construction or rendering path.

A view owns geometry, not appearance.  It records the observer identity,
resolved subject, projection, framing, position angle, orientation, viewport,
and mask.  Style, output mode, render-local detail, grids, legends, language,
title, and output belong to drawing.  The same view can therefore produce
atlas and cartoon charts without reconstructing or changing its geometry.
Unsupported projection names are rejected explicitly; exposing a projection
choice does not imply that more than the implemented stereographic projection
is available.

Defining a projection and applying it are separate operations.  The view
selects and configures projection before chart drawing.  Drawing then selects
the requested maximal content, realizes that content in AltAz for the view's
observer, applies the already configured projection, prepares and clips the
projected geometry, and renders it.  Projection remains lazy so a shallow
render need not project every object loaded in the maximal sphere.

The three stages delegate respectively to the canonical maximal-sphere
factory, observer-aware request resolution and chart-view construction, and
composition plus `CelestialSphere.draw_chart()`.  Existing structured request
and lower-level APIs remain available.  Shared command-line adaptation must
use the same ordinary interface and must not restore example-owned
orchestration.

## Reproducible image-frame sequences

Wenu may later produce ordered sequences of ordinary static chart images for
time-, observer-, trajectory-, or coordinate-epoch studies.  Each frame is a
normal view drawn through the same canonical pipeline, with deterministic
numbering and returned frame metadata.  Wenu does not encode movies, choose a
frame rate, add transitions, or invoke video software; external tools may
combine the exported images.

Sequence state must distinguish scientifically different variables:

- a rotating planisphere varies observer time at a fixed location;
- a Hawaii-to-Tahiti view of the Southern Cross varies observer location and
  time along an explicit trajectory;
- a precession demonstration varies coordinate epoch through an accepted
  precession model rather than treating epoch as observer time or imposing a
  cosmetic rotation.

One observer-independent maximal sphere is reused across frames.  Observer-,
instant-, ephemeris-, source-, and epoch-dependent realizations remain
separately keyed, and sequence rendering must not leak selection, mask, style,
or view state between frames.

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
