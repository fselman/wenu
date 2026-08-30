# Milestone 49I.1B — First drawable Venus layer

**Status:** Scientifically and visually accepted by Fernando on 2026-08-30;
ready for integration.
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

Deterministic tests prove one provider chain, one apparent correction, one
coordinate transformation, opt-in/default-off behavior, and stable semantics.
Fernando's Mac passed the 148-test implementation review, the 35-test focused
regression after the signed-Green-designation SVG correction, and all 1,898
tests in 82.01 seconds.

The installed-DE440 regional acceptance chart placed Venus at the same
position shown by Stellarium for La Ligua at the declared observation instant.
The PNG, PDF, and semantic SVG products looked the same. SVG acceptance also
exposed and closed a pre-existing collision between `G024.7-00.6` and
`G024.7+00.6`; their scientific display names remain unchanged while their
source-owned semantic keys now preserve `minus` and `plus`.
