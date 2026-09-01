# Drawable frozen-Earth Mercury sequence — Milestone 49I.3C.3.3C

**Status:** Implementation proposed; visual and operational acceptance pending

**Implementation date:** 2026-09-01

## Purpose

This slice exposes the scientifically accepted Mercury frozen-Earth state
through the descriptor-driven drawable machinery accepted in 49I.3C.3.3A.
It adds no Mercury-specific layer, factory, projection, preparation, style,
renderer, or exporter.

The public body choice is derived from the catalog's
`frozen_earth_disk_sequence` capability. Model validation rejects
`--disk-sequence-model observed` because Mercury does not advertise the
observed-sequence capability. Symbolic Mercury, tracks, single disks, observed
sequences, photometry, rotation, animation, and 3D remain unavailable.

## Metadata-driven display

`SolarSystemBodyDescriptor` now retains immutable localized display names.
Mercury supplies `Mercury` and `Mercurio`; the shared frozen-title function
combines that metadata with the English or Spanish construction. Layer names,
semantic roots, physical radius/model, target, per-centre magnification, and
the fixed Sun all continue to flow through shared factories.

Mercury components are rooted at
`sky/solar_system/planets/mercury/frozen_earth_sequence`. The fixed Sun remains
`sky/solar_system/star/sun`, uses the common six-point symbol, and is not
magnified.

## Deterministic evidence

`tests/test_frozen_earth_mercury_sequence_display.py` proves capability-based
CLI exposure, rejection of observed Mercury, exact start-inclusive cadence,
generic layer names and realization sharing, Mercury-only semantic paths,
per-centre magnification, fixed-Sun non-magnification, and English/Spanish
titles. Existing Venus display and synthetic minor-body machinery tests remain
unchanged and green.

## Proposed visual calibration

Run from the repository root with the accepted installed DE440 kernel:
The calibration selects `--planet-disk-sequence mercury`,
`--disk-sequence-step 2d`, and `--disk-sequence-n-steps 44`.

```bash
wenu_chart regional \
  --constellations Vir \
  --observer-location "La Ligua" \
  --observer-time "2026-08-30T00:00:00Z" \
  --field-width 70 \
  --field-height 30 \
  --orientation zenith-up \
  --style atlas \
  --mode presentation \
  --language es \
  --planet-disk-sequence mercury \
  --disk-sequence-model frozen-earth-ecliptic \
  --disk-sequence-start "2026-08-30T00:00:00Z" \
  --disk-sequence-step 2d \
  --disk-sequence-n-steps 44 \
  --grid-references ecliptic \
  --planet-disk-magnification mercury=200 \
  --equatorial-grid \
  --output /Users/fselman/Downloads/frozen-earth-mercury.png
```

Visual acceptance must confirm a Spanish title naming Mercurio, a fixed Sun,
the labeled fixed ecliptic, the transformed fixed-frame equatorial grid,
legible changing phases and angular sizes, unclipped disks, and no ordinary
sky content. PNG/PDF/SVG parity and the final cadence, field, magnification,
and date-label policy remain pending human review.
