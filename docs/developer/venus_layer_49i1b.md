# Milestone 49I.1B — First drawable Venus layer

**Status:** Implementation and scientific/visual review candidate.  
**Implementation baseline:** `94d5e99`  
**Date:** 2026-08-30

## Boundary

`VenusLayer` is dormant canonical scene content until the typed request selects
`planets={"venus"}`, exposed concisely as `--planet venus`. It borrows the
request observer's open kernel, realizes the accepted astrometric and apparent
directions, and transforms the resulting apparent ICRS point exactly once into
the request's `LayerRealizationContext.product_coordinate_spec`.

The transformed point then follows the ordinary projection-domain guard,
projection, viewport culling, preparation, Matplotlib renderer, and shared
PNG/PDF/SVG exporter. Its semantic path is exactly
`sky/solar_system/planets/venus`. No network access, second observer, second
light-time calculation, altitude test, projection, renderer, or exporter is
owned by the layer.

## First appearance and non-goals

The first Venus is one fixed hollow circular marker and optional style-owned
label. It carries no magnitude, phase, illuminated fraction, angular diameter,
limb orientation, or physical disk. The Moon, Sun, other planets, trails, and
animation reuse remain later milestones.

## Acceptance

Deterministic tests must prove one provider chain, one apparent correction,
one coordinate transformation, opt-in/default-off behavior, and stable
semantics. Fernando's Mac must run the focused, routine, and full suites plus
an installed-DE440 regional PNG/PDF/SVG visual comparison. This document and
the implementation remain unaccepted until that scientific and visual review.
