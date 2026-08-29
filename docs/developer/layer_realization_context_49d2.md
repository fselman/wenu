# Milestone 49D.2 — Minimal layer-realization context

**Status:** Implementation review candidate; runtime and scientific acceptance pending

**Implementation baseline:** `9e16ed2`

**Date:** 2026-08-29

## 1. Purpose

49D.2 implements the smallest typed handoff established by the accepted 49D.1
audit. It allows one registered `SkyLayer` to receive explicit scientific
realization input before projection without migrating or changing any existing
production layer.

The milestone proves the future moving-object insertion point with a
deterministic test-only provider. It does not add a real ephemeris, planet,
Moon, public option, cache, or scene graph.

## 2. Implemented contract

`sky/realization.py::LayerRealizationContext` is a frozen request-adjacent
value containing:

- `product_coordinate_spec`: the explicit spherical product-coordinate
  identity requested before projection;
- optional `observation`: an immutable `ObservationContext`;
- paired optional `evaluation_instant` and `evaluation_time_scale`;
- optional `reference_equinox`: the resolved equinox value available to
  constructed references.

The context deliberately contains no projection, viewport, renderer, style,
mode, furniture, output, or cache policy. It validates typed coordinate and
observation values, normalizes the evaluation time scale, rejects a partial
instant/time-scale pair, and preserves immutability.

49E must still decide the final time argument accepted by real ephemeris
providers. 49D.2 carries both instant and time scale without expanding the
existing `PositionProvider.position(instant=None)` protocol.

## 3. Compatibility-preserving dispatch

`SkyLayer.realize(context, observer, **geometry_options)` is a concrete
default adapter. It ignores the new context and calls the established
`spherical_geometry(observer, **geometry_options)` method.

`CelestialSphere.draw_chart(..., realization_context=None)` retains two
explicit routes:

| Request | Dispatch |
| --- | --- |
| Context omitted | Calls `layer.spherical_geometry(observer, ...)` directly, exactly as before 49D.2 |
| Typed context supplied | Calls `layer.realize(context, observer, ...)`; unmigrated layers inherit the default adapter |

An untyped context is rejected before layer realization. Geometry then follows
the unchanged projection, preparation, semantic-identity, rendering, and
result-record path.

No ordinary chart request supplies a realization context in 49D.2. Therefore
all existing public chart generation takes the exact legacy branch.

## 4. Controlled provider proof

`tests/test_layer_realization.py` defines a deterministic test-only
`PositionProvider` and dynamic `SkyLayer`. The provider returns one native
ICRS point for the explicit evaluation instant. The layer overrides
`realize()`, obtains that provider state, and transforms it exactly once
through `CoordinateService` into the requested Galactic product
`CoordinateSpec`.

The test proves that:

1. the provider receives the declared evaluation instant;
2. the layer receives the context, explicit observer, and ordinary
   geometry-selection options;
3. the legacy `spherical_geometry()` method is not used for the controlled
   dynamic layer;
4. `CoordinateService` returns the typed product-frame geometry;
5. identifier and finite coordinate arrays survive;
6. the resulting geometry enters the existing projection and renderer path.

The controlled provider and dynamic layer live only in tests. They are not
installed astronomical authorities and expose no public object choice.

## 5. Scientific meaning and limitations

The context is the scientific input to layer realization; it is not itself an
ephemeris result. A future dynamic layer remains responsible for:

- asking its provider for a state at the declared physical instant;
- preserving the provider's native frame, origin, status, time scale, model,
  and provenance;
- constructing a scientifically complete target `CoordinateSpec` in the
  requested product frame;
- invoking `CoordinateService` before projection.

A chart-wide frame choice alone cannot replace an object-specific coordinate
identity. The controlled test uses a complete target specification so that
provider instant and provenance remain explicit. 49E must define how a real
provider and product request compose that target identity for several moving
objects.

## 6. Explicit non-goals

49D.2 does not add or choose a JPL ephemeris. It also does not:

- add the Sun, Moon, planet, satellite, asteroid, or comet;
- change `PositionProvider`;
- thread the context through ordinary `ChartRequest` or CLI code;
- migrate any current catalogue, morphology, grid, point, or horizon layer;
- make the current observer optional;
- add caching, cadence optimization, or a reusable scene graph;
- change projection, preparation, clipping, masking, drawing order,
  appearance, semantic SVG, furniture, or export;
- change any existing product geometry.

## 7. Acceptance requirements

49D.2 is accepted when:

1. focused context and celestial-sphere pipeline tests pass;
2. all existing tests pass without updating visual baselines;
3. the controlled provider is confirmed to remain test-only;
4. Fernando accepts the context fields, compatibility branch, and remaining
   49E provider decisions;
5. the coordinate guide is reviewed pedagogically and scientifically;
6. no unexplained chart or output change is observed.

No new visual product is required because ordinary requests cannot yet supply
the context. The complete existing test suite remains the regression
authority. After acceptance and merge, 49E.1 may design the real
ephemeris-provider contract; a planet still belongs to a subsequent 49I
vertical slice.
