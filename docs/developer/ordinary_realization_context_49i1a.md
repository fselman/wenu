# Milestone 49I.1A — Ordinary realization-context handoff

**Status:** Implementation and scientific review candidate.  
**Implementation baseline:** `62da7b9`  
**Date:** 2026-08-30

## Purpose

49I.1A makes the accepted 49D.2 `LayerRealizationContext` available to layers
during every ordinary declarative chart export. It adds no Venus layer and is
required to be output-neutral for all existing layers.

## Runtime ownership

`charts/request_realization.py::chart_request_realization_context()` builds
one immutable context from the resolved `ChartRequest` and matching observer.
`export_prepared_chart()` constructs it once before the product loop and passes
the same value through `export_composed_chart()`, each chart facade, and
`CelestialSphere.draw_chart()`.

The context contains the actual pre-projection product `CoordinateSpec`, the
observer `ObservationContext`, provider evaluation/reception instant and time
scale, and the independently resolved reference equinox. It contains no
projection, viewport, style, mode, furniture, renderer, output format, or
cache policy.

## Reachable ordinary product frames

| Ordinary families | Product frame in 49I.1A |
| --- | --- |
| planisphere, regional, circumpolar, binocular | observer-local vacuum AltAz |
| all_sky | observer-origin Galactic |

Both product specifications use `PositionStatus.APPARENT`, the observer
reception instant, and observer origin. Their position reference epoch and
equinox are absent. The request's celestial reference equinox is retained only
in `LayerRealizationContext.reference_equinox`; it is not attached to AltAz or
Galactic coordinates as though it defined those frames.

Lower-level equatorial projection machinery exists, including the polar
planisphere class, but `ChartRequest` does not currently expose equatorial as
an ordinary product choice. 49I.1A does not broaden that public vocabulary.

## Compatibility and output neutrality

The ordinary request path now always supplies the typed context. Existing
layers inherit `SkyLayer.realize()`, which discards the context and calls their
unchanged `spherical_geometry(observer, **geometry_options)` method. Therefore
their catalogue selection, apparent AltAz realization, projection,
preparation, renderer, semantics, and exporter remain unchanged.

No signature inspection or exception fallback is used. New dynamic layers may
override `realize()` explicitly; existing layers continue through one concrete
compatibility adapter. Direct low-level chart calls that omit a context remain
valid and retain their previous path.

## Verification

Tests protect horizontal and Galactic request mapping; separation of reference
equinox from product coordinates; observer identity rejection; one context
construction before a multi-product export; forwarding through the common
composed-export boundary; unchanged legacy-layer behavior; and existing chart,
masking, execution, and request-generation behavior.

Focused verification passes 109 tests. The routine and full suites remain for
Fernando's Mac because this workspace intentionally lacks the installed DE440
kernel used by ordinary observer construction.

## Non-goals

49I.1A adds no Venus layer, `--planet` option, planet style, semantic planet
identity, ephemeris evaluation, coordinate transform by an installed dynamic
layer, visible marker, label, PNG/PDF/SVG change, or cache. Those remain
49I.1B after output-neutral acceptance of this handoff.
