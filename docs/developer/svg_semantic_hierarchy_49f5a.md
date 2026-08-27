# Milestone 49F.5A: Sky-propagated semantic hierarchy metadata

**Status:** Implemented; focused and real-SVG verification complete  
**Base:** `e577b19`  
**Branch:** `feature/svg-semantic-hierarchy`  
**Acceptance date:** 2026-08-27

## Purpose

49F.5A extends Wenu's existing sky-owned semantic identity. It does not add a
new chart-document orchestration layer. Each existing sky layer now propagates
the metadata needed to build a designer-oriented SVG hierarchy later:

- semantic path and parent path;
- invariant editor display name;
- astronomical presentation order agreed for Wenu;
- shared style role;
- existing editing policy.

The chart subsystem continues to own projection, framing, clipping, masks,
boundary, and furniture. It does not classify celestial content. The
Matplotlib renderer and SVG serializer carry supplied values without inferring
astronomy from z-order, style, visible text, or backend IDs.

## Accepted presentation order

The initial sky-owned order is:

| Order | Semantic content |
|---:|---|
| 10 | Galaxies |
| 20–21 | Milky Way and Magellanic Clouds |
| 30–33 | Clusters, planetary nebulae, and supernova remnants |
| 40 | Star symbols |
| 50–52 | Constellation lines, boundaries, and labels |
| 70–74 | Coordinate grids and celestial reference points |
| 80 | Horizon within chart masks and boundary |

Solar-system content will occupy the reserved 60 range when its providers are
implemented. Canvas/background, chart masks and boundary, and furniture remain
chart/page responsibilities.

## Propagation

`SemanticLayerIdentity` carries the sky contract into
`SemanticArtistRenderingResult`. The renderer attaches the same values to
each Wenu-owned Matplotlib artist. SVG annotation exposes:

```text
data-wenu-semantic-path
data-wenu-parent-path
data-wenu-display-name
data-wenu-presentation-order
data-wenu-style-role
data-wenu-edit
```

The style role is also emitted as a composable `wenu-style-*` class.

This slice deliberately does not change existing numerical z-orders, XML
order, grouping, geometry, clipping, appearance, or visibility. Unknown safe
extension layers retain a generic path, title-cased display name, style role
derived from their name, and no declared presentation order.

## Regional acceptance

The accepted Centaurus, Crux, and Musca SVG retained 232 semantic artists.
Every artist carried hierarchy metadata. Representative results included:

```text
sky/galaxies                                      order 10
sky/milky_way_and_magellanic_clouds/milky_way   order 20
sky/deep_sky_objects/open_clusters               order 30
sky/deep_sky_objects/globular_clusters           order 31
sky/deep_sky_objects/supernova_remnants          order 33
sky/stars/symbols                                order 40
sky/constellations/lines                         order 50
sky/constellations/labels                        order 52
sky/grids/equatorial                             order 70
```

The constellation-label artists retained `layout`; all other artists in this
representative chart retained `style`. Layer counts were unchanged from the
accepted 49F.4A chart.

## Verification

The focused hierarchy, chart-execution, SVG, paint-role, renderer, and package
boundary suite passed 51 tests in 4.15 seconds.

## Deferred work

Later slices must separately implement and verify:

- individual constellation, grid curve, tick, and label identity;
- actual nested SVG groups and editor layer labels;
- deliberate transition from historical z-orders to presentation order;
- shared inherited style rules and individual overrides;
- whole-group visibility in Inkscape and Illustrator;
- chart-owned background, mask, boundary, and furniture groups.
