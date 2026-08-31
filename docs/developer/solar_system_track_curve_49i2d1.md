# Milestone 49I.2D.1 — Scientific Solar-System track curve

**Status:** Implementation candidate; awaiting local numerical verification and
scientific acceptance  
**Implementation baseline:** `ea03400`  
**Date:** 2026-08-31

## Boundary

49I.2D.1 implements only the renderer-neutral scientific trajectory contract
accepted in 49I.2D. It adds frozen request/result wrappers and one
`SolarSystemTrackRealizer`. The first numerical target is Venus.

There is no public CLI or TOML field, no registered sky layer, no track style,
no projected tick segment, no date label, and no visible output.

## Request contract

`SolarSystemTrackRequest` contains:

- one accepted `SolarSystemPointDescriptor`;
- canonical start instant and time scale;
- positive sample step in days;
- positive tick step in days; and
- a positive tick count.

The closed duration is `tick_step_days * tick_count`. Regular samples include
both endpoints. Exact tick offsets, including the start, are merged into the
regular sample sequence even when the cadences are not integral multiples.
The resulting interval between adjacent vertices never exceeds the requested
sample step.

## Scalar scientific realization

`SolarSystemTrackRealizer.curve()` borrows one ephemeris resource and then,
for every sample instant:

1. constructs a view of the same geodetic observer at that instant;
2. reevaluates the observer barycentric state;
3. runs the accepted astrometric light-time realizer;
4. runs the descriptor's accepted apparent correction policy; and
5. retains the complete `ApparentDirection` evidence.

This scalar path is the correctness authority. It does not add provider
batching, orbit interpolation, caching, or an alternate apparent-place
calculation.

## One fixed-frame spherical curve

The per-sample apparent directions use fixed ICRS-oriented axes. Their
individual reception instants cannot honestly be collapsed into one
single-instant source `CoordinateSpec`, so the native track specification
declares the common ICRS axes, observer origin, apparent status, provider,
model, and corrections without one false common instant. Exact per-vertex
reception instants remain in track metadata and the immutable result.

The complete longitude/latitude arrays are assembled into exactly one open
`SphericalCurves`. `CoordinateService.transform()` is then invoked exactly
once with the chart's fixed `LayerRealizationContext`. Existing curve
segmentation, projection, clipping, preparation, rendering, and export remain
downstream and unchanged.

## Result contract

`SolarSystemTrackResult` retains:

- the exact request;
- one fixed-product-frame `SphericalCurves`;
- one reception instant per curve vertex;
- the common sample time scale;
- exact curve indices for the start and every major-time anchor;
- one complete `ApparentDirection` per vertex; and
- provenance stating scalar evaluation, one curve assembly, and fixed-frame
  transformation.

Track metadata retains body identity, sample instants, exact tick offsets and
indices, and the ephemeris SHA-256. Page tick length, tangent, glyph, date
format, colour, width, style, and drawing order remain absent.

## Deterministic tests

`tests/test_solar_system_tracks.py` proves:

- frozen request validation;
- exact insertion of non-commensurate tick instants;
- one source resource for the complete track;
- observer-state reevaluation at every sample;
- one apparent result per vertex;
- one `SphericalCurves` assembly;
- exactly one product-frame transformation after sampling;
- exact tick indices and retained resource identity; and
- rejection of an untyped or observation-free realization context.

## Installed-kernel validator

`tools/validate_49i2d1_venus_track.py` refuses downloads and requires the
installed DE440 kernel. It evaluates a 28-day La Ligua Venus track from
`2026-08-30T00:00:00Z`, sampled daily and anchored every seven days. Every
retained apparent ICRS direction is compared with direct Skyfield
`observe(...).apparent()`. The tool reports the maximum component residuals,
sample count, exact tick indices, kernel identity, and first/last coordinates
in the fixed chart frame.

The acceptance tolerance is proposed as `1e-7` degree per ICRS component,
matching the established apparent-direction numerical scale while remaining
far below chart resolution. Fernando must review the actual installed-kernel
results before acceptance.

## Non-goals

49I.2D.1 adds no:

- public `--planet-track` or duration syntax;
- chart request/detail selection;
- registered trajectory layer;
- projected tick, date label, glyph, line style, or semantic SVG path;
- planisphere, all-sky, regional, or binocular output change;
- physical disk, phase, illumination, photometry, or magnitude symbol;
- provider batching, caching, adaptive sampling, or spline smoothing; or
- projection, renderer, preparation, clipping, or exporter change.

## Acceptance requirements

49I.2D.1 is accepted when:

1. deterministic track tests and the relevant direction/curve suites pass;
2. the installed DE440 validator agrees with direct Skyfield within the
   declared tolerance;
3. Fernando accepts the common source specification without a false instant,
   complete per-sample evidence, fixed-frame transformation, and exact anchors;
4. routine and complete suites pass;
5. documentation is current; and
6. no visual comparison is required because the slice cannot draw anything.
