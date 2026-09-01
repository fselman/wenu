# Mercury catalog and numerical validation — Milestone 49I.3C.3.3B

**Status:** Implementation proposed; installed-DE440 validation pending

**Implementation date:** 2026-09-01

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

Scientific acceptance remains pending until Fernando runs the installed-DE440
validator on the Mac and reviews its complete output. Public/drawable Mercury
remains a later, separately reviewed milestone.
