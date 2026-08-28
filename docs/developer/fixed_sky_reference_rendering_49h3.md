# Fixed-sky and rotating-horizon reference rendering

**Milestone:** 49H.3  
**Status:** Renderer-neutral transformation implemented; uncached canonical
reference rendering visually accepted  
**Acceptance date:** 2026-08-28

## Accepted behavior

The three-frame La Ligua south-circumpolar audit was inspected directly. It
established the requested presentation:

- stars remain fixed in the viewport;
- constellation lines and labels remain fixed with the stars;
- the equatorial grid remains fixed with the celestial scene;
- the semantic horizon rotates across the fixed celestial viewport;
- the AltAz grid rotates with the local horizon;
- title and page furniture remain stationary and upright.

This acceptance supersedes the presentation behavior of the 49H.2
complete-render baseline, in which the local horizon was fixed and the
celestial scene rotated.

## Astronomical transformation

`fixed_sky_circumpolar_orientation()` chooses a stable J2000 celestial
reference direction ten degrees from the selected celestial pole. It transforms
that same direction into the local horizontal frame at:

1. the explicit `celestial_anchor_time`; and
2. the frame simulation time.

The signed difference between the two tangent-plane position angles is added
to the chart's anchor position angle. The correction is zero at the anchor.
It uses Astropy's astronomical transformation at both instants and is not
approximated as elapsed hours multiplied by 15 degrees.

The established pole-centred `StereographicProjection` and
`SphericalFrame.position_angle_deg` remain the only projection owners.
The renderer performs no astronomical calculation.

## Geometry proof

`tests/test_fixed_sky_orientation.py` protects the transformation at the
renderer-neutral projection boundary. It proves that:

- the same celestial reference coordinate has identical projected coordinates
  at the anchor and a later frame;
- a fixed local-horizon point changes projected coordinates;
- an explicit non-zero anchor position angle is preserved;
- the calculation is not the solar-hour shortcut.

These invariants are stronger and less brittle than asserting one precomputed
angle.

## Canonical frame resolution

`resolve_fixed_sky_rotating_horizon_frame()` converts the explicit dual-time
ownership of one planned frame into an ordinary `ChartRequest`:

- the request observer is the frame-local observer, preserving ordinary
  horizon, AltAz, visibility, and furniture behavior;
- the circumpolar frame receives only the anchor-relative
  `position_angle_deg` correction;
- all other chart, content, detail, style, furniture, and output choices are
  preserved.

The first implementation is deliberately circumpolar-only. Unsupported chart
families fail rather than silently receiving an unproved transformation.

## Uncached reference renderer

`generate_fixed_sky_rotating_horizon_sequence()` resolves each frame and
calls the canonical `generate_chart_request()` entry point. Every frame is a
complete independent build and export. It creates no second sphere,
projection, renderer, furniture, or output path.

`tools/render_49h3_fixed_sky_reference.py` generates the reproducible
three-frame behavior-validation product under
`/tmp/wenu-49h3-fixed-sky/reference-frames` and writes
`fixed-sky-reference-audit.json`. The audit records the astronomical
position-angle provenance, times, dimensions, byte counts, and hashes.

## Deliberate limits

49H.3 does not claim:

- cached or shared celestial geometry;
- sequence manifest or restart/resume support;
- moving-object cadence separation;
- proper-motion or precession realization;
- a raster golden-file test.

Catalogue reference epoch and proper-motion realization remain independent
provider policy. They must not be inferred from either timeline instant.

## Next milestone

49H.4 may introduce scientifically keyed reuse only after benchmarking this
accepted uncached reference. Any optimized result must preserve the 49H.3
geometry invariants and reproduce its visual behavior while retaining the
complete-render route as a correctness reference.
