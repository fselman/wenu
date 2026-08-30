# Milestone 49I.2B — Shared Solar-System point layer

**Status:** Scientifically and architecturally accepted by Fernando on
2026-08-30; ready for integration.
**Implementation baseline:** `b0d1dd4`  
**Date:** 2026-08-30

## Boundary

49I.2B extracts only the renderer-neutral orchestration already demonstrated by
Venus and the accepted Moon direction. It adds
`SolarSystemPointDescriptor` and `SolarSystemPointLayer`, then migrates
`VenusLayer` atomically to a thin configured specialization.

The shared layer owns this invariant sequence:

1. validate one typed `LayerRealizationContext` and body selection;
2. borrow one state source from the request observer;
3. realize the observer barycentric state at reception;
4. request the descriptor's target relative to its declared centre;
5. run the existing astrometric light-time realizer;
6. apply the descriptor's explicit apparent-correction policy;
7. attach stable point identity, display name, ephemeris hash, and apparent
   provenance;
8. transform exactly once into the product coordinate specification.

It returns ordinary `SphericalPoints` before projection. It does not project,
test visibility, choose appearance, render, or export.

## Frozen descriptor

`SolarSystemPointDescriptor` carries the body-specific values needed by the
shared orchestration:

- provider target key;
- stable semantic entity key;
- display name;
- request selection key;
- declared state centre;
- explicit `ApparentCorrectionPolicy`.

The descriptor is frozen and validates every text field. It does not select a
kernel, construct an observer, propagate an orbit, or describe a physical
body disk.

## Venus parity

`VENUS_POINT` freezes the existing Venus values. `VenusLayer` retains
`layer_name = "venus"`, remains default-off, and retains the established
`sky/solar_system/planets/venus` semantic path, request selection, label,
marker/style ownership, ephemeris metadata, and single product-frame
transformation.

The migration deliberately passes the descriptor's default correction policy
explicitly to the existing apparent realizer. This makes correction ownership
visible without changing the accepted Skyfield policy or numerical result.

## Moon proof without Moon content

`tests/test_solar_system_point_layer.py` uses a test-only Moon descriptor to
prove that target, centre, identity, correction policy, provenance, and one
coordinate transformation are body data rather than Venus literals. It does
not add `sky/moon.py`, register a Moon layer, change public selection, or draw
the Moon. Those remain 49I.2C.

## Current verification

The implementation candidate passed:

- 13 direct shared-layer and Venus parity tests in 1.86 seconds;
- 82 focused scientific and integration tests in 1.82 seconds;
- 1,881 routine tests with 30 deselected in 27.67 seconds;
- 53 current-documentation tests in 2.16 seconds; and
- all 1,912 tests in 91.04 seconds.

The same La Ligua regional Venus request at `2026-08-30T00:00:00Z` was
rendered from baseline `b0d1dd4` and this branch in PNG, PDF, and semantic SVG.
The PNG files were byte-identical. PDF rasterization produced equal
`315 x 402` RGBA arrays with zero differing pixels or channel values. After
normalizing only creation time, source revision, output pathname, and generated
Matplotlib reference IDs, the SVG semantic and graphical content was
byte-identical.

## Scientific and architectural acceptance

Fernando accepted the frozen descriptor, shared renderer-neutral orchestration,
thin Venus specialization, exact output parity, test-only Moon reuse proof, and
all stated non-goals on 2026-08-30. This acceptance authorizes integration of
49I.2B; it does not authorize a production Moon layer or any deferred 49I.2C
surface.

## Non-goals

49I.2B adds no Moon layer, `--moon`, generalized public selection, new style,
marker, phase, magnitude, angular diameter, physical disk, projection,
viewport, renderer, exporter, kernel download, second observer, second
light-time solution, or chart-output feature.
