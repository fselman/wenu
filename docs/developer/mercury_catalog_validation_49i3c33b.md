# Mercury catalog and numerical validation — Milestone 49I.3C.3.3B

**Status:** Scientifically and architecturally accepted

**Implementation date:** 2026-09-01

**Acceptance date:** 2026-09-01

## Purpose

This slice makes Mercury the first non-Venus proof of the descriptor-driven
moving-body foundation. It registers one immutable physical-body descriptor
and exercises the existing generic frozen-Earth state realizer. It adds no
Mercury-specific layer, factory, projection, style, renderer, or exporter.

Mercury deliberately advertises only `frozen-earth-disk-sequence`. The public
sequence CLI requires both observed and frozen sequence capabilities, so this
registration does not expose `--planet-disk-sequence mercury`.

## Physical identity

The descriptor records physical body NAIF `199` and the JPL equal-volume mean
radius `2439.4 km`. The installed SPK may supply Mercury state through provider
target `1` or `199`; that actual provider identifier is retained independently
and never substituted for the physical-body identity.

## Evidence

`tests/test_mercury_catalog_state.py` proves catalog resolution, immutability,
capability gating, radius/model retention, provider target/centre retention,
distance-dependent angular diameter, provenance, and public-CLI exclusion.

`tools/validate_49i3c3_3b_mercury.py` requires an installed DE440 kernel and
refuses downloads. At every exact sample it independently computes direct
Skyfield vectors and compares the frozen Earth, relative Mercury vector,
fixed-ecliptic direction, distances, angular diameter, phase, illuminated
fraction, and bright-limb angle. It prints kernel identity, provider IDs,
samples, maximum residuals, and explicit tolerances, and requires an interior
thin-phase peak plus material distance spans.

## Acceptance boundary

Fernando accepted this descriptor-only Mercury slice scientifically and
architecturally after the installed-DE440 validator completed on the Mac. It
used `de440s.bsp` with SHA-256
`c1c7feeab882263fc493a9d5a5b2ddd71b54826cdf65d8d17a76126b260a49f2`,
resolved Mercury through provider target/centre `199/10`, and found an interior
thin-phase peak of `168.696859831 deg`. The Earth-Mercury distance spanned
`0.623127744760..1.374640492885 AU` and the Sun-Mercury distance spanned
`0.307535936142..0.466683324039 AU`.

Every independent residual passed its declared tolerance. The largest phase,
illuminated-fraction, and bright-limb-position-angle residuals were
`8.099e-10 deg`, `7.006e-12`, and `5.272e-09 deg`, respectively. The complete
Mac regression suite then passed all 2,047 tests in 97.93 seconds.

Public/drawable Mercury remains a later, separately reviewed milestone.
