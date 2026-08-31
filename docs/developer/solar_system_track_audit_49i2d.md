# Milestone 49I.2D — Solar-System track contract

**Status:** Proposed audit; documentation only  
**Implementation baseline:** `d1971f5`  
**Date:** 2026-08-31

## 1. Purpose

49I.2D defines the smallest scientifically explicit contract for drawing the
apparent path of a Solar-System body before physical apparent-disk work begins.
The first implementation target is Venus in regional and binocular charts.
The contract is shared by planets and the Moon, but this audit does not install
a track layer, public option, style, or visible output.

The track must reuse Wenu's canonical sequence:

```text
time samples and body descriptor
    -> apparent topocentric directions on fixed ICRS-oriented axes
    -> one typed spherical curve with per-sample time provenance
    -> one transformation into the fixed chart product frame
    -> ordinary projection, clipping, preparation, rendering, and export
```

It is not a command-owned overlay, a renderer path, an SVG-only path, or a
sequence of independently drawn projected points.

## 2. Requested time vocabulary

The proposed public vocabulary for one initial track is:

```text
--planet-track venus
--track-start 2026-08-30T00:00:00Z
--track-sample-step 1h
--track-tick-step 7d
--track-tick-count 4
```

The names describe their purpose:

- `track-start` is the first physical reception instant;
- `track-sample-step` is the maximum interval used to approximate the curve;
- `track-tick-step` is the physical interval between major date marks; and
- `track-tick-count` is the number of marked intervals after the start.

The example ends exactly 28 days after the start. Regular hourly samples include
both endpoints, and exact tick instants are inserted if they do not coincide
with the regular cadence. Four ticks occur after the specially marked start,
at 7, 14, 21, and 28 days. The start receives the date label and customary
planet glyph. Later work may decide whether other ticks also receive dates.

Durations must be positive, finite, and parsed by one governed duration
vocabulary. The tick count must be a positive integer. The ephemeris resource
must cover every observer and target evaluation needed over the closed
interval.

## 3. Two different instants that must not be conflated

A track on a static chart has two temporal roles:

1. **Sample instants** determine the physical apparent direction of the body.
   The observer retains one geodetic location and elevation, but its
   barycentric state is reevaluated at every sample instant.
2. **Chart-frame instant** determines the fixed product frame, projection
   orientation, stellar background, viewport, and chart furniture.

For a regional or binocular chart, every apparent ICRS direction must be
expressed in the one fixed observer-local product frame declared by the chart
request. Transforming each sample into the AltAz frame of its own sample time
would trace much of the Earth's daily rotation and would not show the body's
path against the fixed stellar field.

The track therefore preserves every sample reception instant as per-vertex
scientific provenance while the resulting `SphericalCurves.coordinate_spec`
describes the single fixed product frame consumed by the projection.

## 4. Renderer-neutral track request and result

The exact installed names remain an implementation decision, but the
renderer-neutral request must contain:

- one `SolarSystemPointDescriptor` or equivalent shared body identity;
- one start instant and time scale;
- one positive sample cadence;
- one positive tick cadence;
- one positive tick count; and
- no projection, viewport, renderer, style, output, or label appearance.

The scientific realization must retain, for every sample:

- reception instant and time scale;
- apparent topocentric direction;
- emission instant and light time;
- observer identity and barycentric state provenance;
- target, centre, correction policy, and ephemeris resource identity.

The result must identify exact tick anchors and the starting vertex without
encoding page-space tick lengths, line colour, linewidth, linestyle, glyph
font, or date typography.

## 5. Reuse of spherical-curve machinery

The implemented `SphericalCurves` record is the correct downstream geometry.
It already carries sampled curve topology, coordinate identity, semantic
metadata, and curve identity. `CoordinateService` transforms complete curve
collections by concatenating their coordinate arrays, transforming them
vectorially, and restoring segmentation. Existing stereographic, Mollweide,
and polar projections accept `SphericalCurves`, and the ordinary preparation
and renderer path already handles projected curves.

49I.2D must use that machinery rather than introduce a body-specific curve,
projection, clipping, renderer, or exporter.

The provider/direction boundary is currently scalar. The first implementation
may evaluate samples through the accepted scalar direction realizer and then
assemble their coordinates into one curve. Provider batching is a later
optimization and must reproduce the scalar path within declared tolerances.

The sampled path is the scientific approximation. Wenu must not fit an
unconstrained longitude/latitude spline that can overshoot at longitude seams,
poles, stationary points, or retrograde loops. A renderer may join adjacent
projected samples with ordinary line segments.

## 6. Tick and label geometry

Tick anchors are physical times attached to exact vertices of the track.
Visible tick segments are chart annotations:

1. project the complete spherical curve through the ordinary chart machinery;
2. locate each projected major-time anchor;
3. estimate the local projected tangent from valid neighboring samples;
4. construct a short page-space segment perpendicular to that tangent; and
5. clip and render it through the existing preparation and renderer owners.

This downstream construction is necessary because a perpendicular direction on
the celestial sphere is not generally perpendicular after a non-conformal map
projection. Tick length, colour, width, and style are display policy.

Stationary points require an explicit fallback tangent using the nearest
non-coincident samples on both sides. A tick whose tangent cannot be resolved
must be omitted with deterministic metadata rather than drawn in an arbitrary
direction.

The start label uses the configured chart language and a declared date/time
format. The body is identified with its customary astronomical glyph; a text
fallback is required when the selected font cannot represent that glyph.

## 7. Projection, clipping, and discontinuities

The complete track is an ordinary spherical curve. Existing projection-domain
guards, longitude-seam splitting, viewport clipping, masks, and final chart
boundary remain authoritative.

The implementation must characterize:

- a track wholly outside the field;
- entry into and exit from the field;
- longitude wraparound and a Mollweide seam;
- retrograde loops and stationary points;
- clipped start or tick anchors;
- non-finite provider or projected samples; and
- a requested interval outside kernel coverage.

No straight projected segment may bridge a projection discontinuity or an
invalid sample.

## 8. Chart-family and selection policy

The first visible implementation is limited to regional and binocular charts.
A track is default-off and is requested independently of the body's ordinary
point marker. The implementation audit must decide whether the start glyph
replaces or coexists with a separately requested instantaneous body point, and
must prevent accidental duplicate labels.

Planisphere and all-sky products remain outside the first implementation.
Long-duration tracks may later be useful there, but their sampling, density,
seam, and labelling policies require separate visual acceptance.

The first runtime slice should install Venus only. The shared contract may then
be validated for the Moon, whose strong topocentric parallax and rapid motion
provide a materially different scientific test.

## 9. Appearance ownership

Chart style owns:

- track colour, linewidth, linestyle, and alpha;
- tick length and tick appearance;
- start glyph and date-label appearance; and
- drawing order relative to constellation lines, grids, body points, and labels.

Detail/request policy owns whether a track is selected. The track's physical
time interval and sample cadence are request geometry, not style. PNG, PDF, and
semantic SVG must consume the same projected track and annotations. The stable
semantic hierarchy must descend from the selected body's existing identity,
for example `sky/solar_system/planets/venus/track`.

## 10. Proposed implementation sequence

1. **49I.2D audit:** accept time semantics, fixed-frame meaning, ownership,
   curve reuse, CLI vocabulary, and non-goals.
2. **49I.2D.1 scientific curve:** add immutable request/result contracts and
   numerical Venus validation without public drawing.
3. **49I.2D.2 drawable Venus track:** add regional/binocular request plumbing,
   style, projected ticks, start label, and shared PNG/PDF/SVG output.
4. **49I.3 physical apparent-disk contract:** return to the separately governed
   Moon-and-planet physical geometry milestone.

Each runtime slice requires separate authorization and acceptance.

## 11. Explicit non-goals

This audit does not:

- add runtime source, a public CLI or TOML field, or a visible track;
- change Venus or Moon point appearance;
- add physical disk, phase, illumination, angular diameter, or limb geometry;
- add planetary photometry or magnitude-scaled symbols;
- add provider batching, caching, adaptive cadence, or orbit interpolation;
- change any projection, clipping, renderer, semantic-SVG, or exporter;
- add planisphere or all-sky tracks;
- add multiple simultaneous CLI track specifications;
- choose final style values or visual baselines; or
- alter existing chart results.

## 12. Acceptance requirements

The 49I.2D audit is accepted when Fernando agrees that:

1. per-sample physical instants and the fixed chart-frame instant are distinct;
2. the path becomes one ordinary `SphericalCurves` value before projection;
3. exact tick instants and complete per-sample provenance are retained;
4. visible perpendicular ticks are projected annotations, not spherical
   astronomical geometry;
5. regional and binocular charts are the first supported families;
6. the proposed CLI vocabulary expresses the requested example clearly;
7. runtime implementation remains separately authorized; and
8. current documentation tests and the complete suite pass without visual or
   numerical output changes.
