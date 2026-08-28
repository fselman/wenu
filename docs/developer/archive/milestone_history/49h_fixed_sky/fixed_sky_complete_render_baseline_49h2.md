# Circumpolar complete-render baseline

**Milestone:** 49H.2
**Status:** Baseline implemented, visually characterized, and accepted
**Base:** 49H.1 on `feature/fixed-sky-rotating-horizon`

## Purpose

The existing observer-time sequence is the independent record of Wenu's
current circumpolar behavior. Each frame enters the canonical static request
pipeline and completely rebuilds, prepares, projects, renders, furnishes, and
exports the chart at its own observer instant.

This product is called the **complete-render baseline**. It is not the oracle
for the requested fixed-sky presentation.

## Visual characterization

The 2026-08-27 and 2026-08-28 real-render audits established that:

- the stellar sky rotates in the viewport;
- celestial constellation content and the equatorial grid rotate with it;
- the semantic horizon and AltAz geometry remain fixed in the local viewport;
- title and other page furniture remain fixed and upright;
- the initial audit accidentally hid the semantic horizon because its explicit
  enabled-layer set omitted `horizon`;
- the widened declination -50 degree audit visibly shows the horizon as the
  dashed arc near the lower edge of all three frames.

This is the exact inverse of the requested fixed-sky presentation. Direct pixel
equality with these frames would therefore preserve the wrong behavior. The
accepted characterization is instead an independent input to deriving the
required anchor transformation.

## Baseline API

`fixed_sky_complete_render_baseline_request()` derives an ordinary
`ObserverTimeChartSequenceRequest` from the 49H.1 request and requires a
separate output directory.

`generate_fixed_sky_complete_render_baseline()` delegates only to
`generate_observer_time_chart_sequence()`. It does not call a fixed-sky
renderer, share prepared candidate geometry, register images, or introduce
another export path. Existing sequence manifest and restart/resume verification
remain in force.

The explicit celestial anchor is not substituted into the baseline and is not
confused with a catalogue reference epoch.

## PNG measurements

`compare_png_frames()` converts two images to RGBA and records dimensions,
changed pixels, changed-pixel fraction, maximum absolute channel difference,
and mean absolute channel difference.

`PngFrameComparisonTolerance` makes comparison limits explicit. Exact pixel
equality is the default. These values are general measurement tools; comparing
a future candidate directly with the unregistered baseline is not an
acceptance test.

## Reproducible audit

`tools/render_49h2_complete_render_baseline.py` builds a three-frame south
circumpolar baseline limited to declination -50 degrees by default. At La
Ligua the south celestial pole is about 32 degrees above the horizon, so this
40-degree-radius field visibly intersects the semantic horizon. The earlier
-60-degree limit had a 30-degree radius and correctly placed the nearest
horizon just outside the viewport. The baseline includes stars, constellation
lines and labels, equatorial and AltAz grids, and the semantic horizon.

It writes:

- frames and the ordinary manifest under `complete-render-baseline/`;
- `fixed-sky-baseline-audit.json` beside that directory.

The JSON declares:

- `role = unregistered_complete_render_baseline`;
- `target_pixel_oracle = false`;
- manifest identity, anchor, simulation/display instants, dimensions, byte
  counts, hashes, and render/reuse counts.

The audit fails for inconsistent dimensions or identical observer-time frames.

## Requirement for the real oracle

A fixed-sky oracle must independently express the requested invariants:

- stars, constellation geometry, deep-sky objects, and equatorial grid remain
  fixed relative to the celestial viewport;
- horizon, cardinal directions, AltAz grid, visibility, and optional Earth or
  landscape mask change with observer time;
- furniture stays upright and stationary;
- catalogue epoch and proper-motion realization remain separate provider
  policy.

For a circumpolar chart, Wenu can keep the established pole-centred
stereographic projection and vary only its spherical-frame position angle. The
angle must be derived from a fixed celestial reference direction transformed
into the local horizontal frame at both the celestial anchor and the frame
instant. Subtracting those tangent-plane position angles gives a renderer-
neutral correction that is zero at the anchor and follows the actual
astronomical transformation. It must not be approximated as elapsed hours
multiplied by 15 degrees.

Rotating completed raster frames is not the production architecture because it
would also rotate furniture and introduce resampling.

## Stop condition

49H.3 fixed-sky rendering and all caching remain blocked until the
renderer-neutral anchor transformation and a true target oracle are defined
and tested. The complete-render baseline remains an independent scientific
input to that derivation, not its expected pixel output.
