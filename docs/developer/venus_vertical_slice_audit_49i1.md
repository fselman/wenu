# Milestone 49I.1 — Drawable Venus vertical-slice audit

**Status:** Scientifically and architecturally accepted by Fernando on 2026-08-30; ready for integration.  
**As-is baseline:** `17f5c10`  
**Date:** 2026-08-30

## 1. Purpose

Define the smallest scientifically correct path from the accepted 49E.6
apparent Venus direction to one chartable semantic Venus object. This audit
does not implement the layer. It prevents the first visible planet from
bypassing product-frame transformation, chart preparation, semantic SVG, or
the shared exporter.

## 2. As-is findings

The provider and physical-direction chain is complete:

1. `SkyfieldEphemerisStateSource` supplies kernel-identified ICRF Cartesian
   states;
2. `AstrometricDirectionRealizer` owns observer subtraction and one-way
   light-time iteration;
3. `SkyfieldApparentDirectionRealizer` consumes that accepted result once and
   applies declared gravitational deflection and aberration; and
4. the result is observer-origin, apparent, fixed-ICRS-oriented
   `SphericalPoints` with no position reference epoch and no equinox.

The chart-side seam is not yet closed. `LayerRealizationContext` can carry the
product `CoordinateSpec`, observation, provider-evaluation instant/scale, and
reference equinox before projection. `CelestialSphere.draw_chart()` can pass
it to `SkyLayer.realize()`. Ordinary chart facades, however, do not construct
or pass that context. A Venus layer therefore cannot yet learn the selected
product frame through the approved layer boundary.

The renderer already draws `ProjectedPoints`, styles already supply ordinary
point rendering options, and semantic identity already flows from a sky layer
through Matplotlib to PNG, PDF, and annotated SVG. No new projection, renderer,
or exporter is required.

## 3. Required two-step implementation

### 49I.1A — Ordinary realization-context handoff

Construct one `LayerRealizationContext` from the resolved chart request and
observer, then pass it through every canonical chart family to
`CelestialSphere.draw_chart()`. Existing layers continue through
`SkyLayer.realize()`'s compatibility adapter and must retain identical
geometry.

The context owns scientific identity only:

- product coordinate system and reference frame;
- applicable reference equinox, separately from all epochs and instants;
- observer `ObservationContext`;
- provider evaluation/reception instant and time scale.

It owns no projection, viewport, style, label placement, renderer, output
format, or cache policy. The handoff must be proven output-neutral before
Venus is registered.

### 49I.1B — One Venus layer

Add a `VenusLayer(SkyLayer)` whose `realize()` performs exactly this sequence:

1. borrow the request observer's already-open ephemeris through the 49E.3
   adapter;
2. build the typed observer barycentric state at reception;
3. realize the accepted 49E.5 astrometric direction;
4. realize the accepted 49E.6 apparent direction without another `observe()`;
5. transform the resulting `SphericalPoints` exactly once through
   `CoordinateService` into `context.product_coordinate_spec`; and
6. return the transformed geometry before projection.

The layer must fail if no typed context, observation, evaluation instant, or
time scale is available. It must not fall back to the legacy
`spherical_geometry(observer)` call because that would conceal the product
frame.

## 4. Identity, visibility, and appearance

The source identity is stable `venus`, display name `Venus`, NAIF target ID
299, and exact ephemeris resource fingerprint. The renderer-neutral semantic
path is `sky/solar_system/planets/venus`; SVG-safe components use underscores,
while prose may write “Solar System.” The SVG annotator serializes this
upstream identity and never infers it from a label or marker.

49I.1 returns the apparent direction even when it lies outside a viewport or
below a horizon. Existing projection-domain guards, viewport culling, masks,
and chart boundaries own graphical visibility. The layer must not implement a
second altitude test or clipping path.

The first appearance is explicitly symbolic: one fixed Venus marker plus an
optional `Venus` label, owned by ordinary chart style and mode scaling. It is
not a physical disk. Visual magnitude, phase, illumination, angular diameter,
limb orientation, surface detail, and trails remain deferred. No fabricated
photometric quantity may be stored merely to select a marker size.

## 5. Minimum public surface

The first public selector should be `--planet venus`. The corresponding typed
request selection contains the identifier `venus`; unsupported planet names
fail explicitly. This gives examples a concise Wenu request without exposing
provider classes or astronomy calculations, while avoiding a collection of
body-specific switches such as `--venus`.

Venus is opt-in during 49I.1. Default charts remain unchanged. Configuration
may expose the same identifier only if it uses the existing content-selection
ownership; it must not choose kernels, correction models, coordinates, or
rendering paths independently.

## 6. Acceptance evidence

Acceptance requires:

1. deterministic proof that the ordinary context reaches all canonical chart
   families without changing existing geometry;
2. deterministic Venus-layer proof of one provider chain, one apparent
   correction, and one `CoordinateService` transform;
3. installed-DE440 numerical comparison at La Ligua;
4. one regional Venus acceptance chart in PNG, PDF, and SVG from the same
   projected record;
5. SVG path and stable Venus entity identity inspection;
6. a below-horizon or outside-viewport case governed by the existing mask and
   culling path;
7. routine and complete regression suites; and
8. Fernando's scientific and visual acceptance.

The visual chart should show Venus against stars and at least one coordinate
grid so position can be inspected. It should not attempt phase or a resolved
disk. Atlas print remains the visual baseline, with one presentation SVG used
to inspect semantic structure.

## 7. Non-goals

49I.1 does not add the Moon, Sun, other planets, natural satellites,
artificial satellites, phase, photometry, disks, trails, animation caching, a
planet catalogue, a second scene graph, or a separate SVG generator. It does
not redesign all legacy layers merely because the realization context becomes
available.

The Moon follows Venus because its stronger topocentric parallax, angular
extent, phase, and orientation require additional explicit contracts.

## 8. Scientific and architectural acceptance

Fernando accepted the 49I.1A-before-49I.1B sequence, typed ordinary
realization-context handoff, one product-frame transformation, opt-in
`--planet venus` interface, stable `sky/solar_system/planets/venus` identity,
symbolic marker and optional label, existing visibility/clipping ownership,
shared PNG/PDF/SVG path, and all stated non-goals on 2026-08-30.

The documentation gate passed all 48 current-documentation tests in 3.30
seconds on Fernando's Mac. This acceptance authorizes the bounded 49I.1A
implementation; it does not pre-accept its runtime result, 49I.1B Venus
geometry, or any visual chart.
