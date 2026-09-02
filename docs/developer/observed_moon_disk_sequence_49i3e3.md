# Observed Moon disk sequence — Milestone 49I.3E.3

**Status:** Scientifically accepted; visual and regression acceptance pending  
**Implementation base:** `eba3bd9`  
**Scientific acceptance date:** `2026-09-02`

## Purpose and boundary

This milestone adapts the accepted Moon descriptor and physical appearance into
Wenu's existing generic observed multi-epoch disk sequence. It adds
`--moon-disk-sequence` and no Moon-specific scientific realizer, geometry,
projection, preparation, renderer, semantic exporter, or output backend.

Only the observed model is implemented. Frozen-Earth lunar sequences,
interpolation, animation, texture,Click, albedo, craters, libration, axes, eclipses,
refraction, occultations, animation, and simultaneous sequences remain outside
this milestone.

## Public request

A complete request uses:

```text
--moon-disk-sequence
--disk-sequence-model observed
--disk-sequence-start ISO_TIME
--disk-sequence-step DURATION
--disk-sequence-n-steps COUNT
--disk-sequence-labels
--moon-disk-magnification FACTOR
```

The start is included and `COUNT` is the number of intervals, so the result
contains `COUNT + 1` independently realized samples. Magnification remains
finite, bounded by `1 <= M_moon <= 1000`, display-only, and common to the
sequence. It scales each projected disk about its own physical centre.

The complete group is required. A Moon sequence conflicts with single resolved
`--moon`, symbolic Moon appearance, and a simultaneous planet sequence.
`frozen-earthMapping` is rejected because the Moon's orbital relation to Earth
requires a separately defined model.

## Fixed-chart scientific contract

The ordinary chart observer time is the chart epoch. It fixes the background,
catalog evaluation, horizon, viewport, product coordinate specification,
projection, tangent plane, labels, and furniture.

Every sequence sample has its own exact physical epoch. The generic
`ObservedSolarSystemDiskSequenceRealizer` independently reevaluates the
topocentric observer, retarded Moon and Sun directions, apparent corrections,
distance, angular diameter, phase, illuminated fraction, bright-limb
orientation, and 720-sample spherical disk geometry.

`ObservedSolarSystemDiskSequenceRealization` transforms every complete
sample geometry into the one chart-epoch product frame before aggregation.
This transports the centre and tangent geometry together; it never treats the
scalar bright-limb position angle as frame-invariant and never substitutes a
sample-epoch AltAz frame for the fixed chart frame.

## Descriptor and rendering ownership

`MOON_BODY` advertises the generic `observed_disk_sequence` capability and
authorizes it in regional, binocular, circumpolar, planisphere, and all-sky
families. Venus retains its existing regional/binocular observed boundary.

Generic layers derive:

- `moon_disk_sequence_illuminated`
- `moon_disk_sequence_limb`
- `moon_disk_sequence_terminator`
- optional `moon_disk_sequence_labels`

Their semantic paths remain below
`sky/solar_system/natural_satellites/moon/disk_sequence`. Ordinary clipping,
per-centre post-projection magnification, label placement, PNG/PDF/SVG
rendering, and semantic export remain shared.

## Installed-DE440 validation

Run:

```bash
python tools/validate_49i3e3_observed_moon_sequence.py
```

The validator refuses downloads and uses the installed accepted
`de440s.bsp`. Five independently realized samples span both sides of the
separate chart epoch `2026-09-16T12:00:00Z`. Fernando scientifically accepted
the validation on 2026-09-02.

Maximum absolute residuals against direct Skyfield were:

| Quantity | Residual |
| --- | ---: |
| apparent right ascension | `5.458e-08 deg` |
| apparent declination | `2.376e-08 deg` |
| topocentric distance | `3.800e-12 au` |
| angular diameter | `2.887e-06 arcsec` |
| phase angle | `5.702e-08 deg` |
| illuminated fraction | `7.859e-11` |
| bright-limb position angle | `1.193e-07 deg` |

Minimum demonstrated topocentric parallax was `0.196988 deg`. Every residual
satisfies the accepted 49I.3E envelope.

## Reproducible visual review

Run:

```bash
python tools/render_49i3e3_observed_moon_sequence_review.py
```

The matrix renders regional, 7.5-degree binocular, circumpolar, planisphere,
and Mollweide all-sky sequences. The regional sequence spans eight daily
samples from new Moon toward first quarter; the binocular diagnostic uses
seven two-hour samples. Both use exact topocentric chart-epoch centring. DSOs
are omitted; binocular stars extend to magnitude 11 and other families to
magnitude 5. Regional PNG/PDF/SVG products test export parity.

Human review must confirm that the background and projection remain fixed,
centres follow a coherent path, phase and orientation evolve plausibly,
magnification does not move centres, labels are legible, and clipping creates
no folds, chords, inverted fills, or seam artifacts.

## Verification and stop condition

The initial focused adapter and compatibility suite passed 100 tests in 3.22
seconds. Documentation, expanded focused tests, routine/full regression, and
visual acceptance remain pending.

Do not merge until those gates pass. This milestone does not authorize any
frozen-Earth or other new lunar sequence model.
