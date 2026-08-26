# Milestone 49F.2A semantic SVG identity

**Status:** Implemented; focused tests and Mac visual acceptance complete  
**Base:** `3c6f834`  
**Branch:** `feature/svg-semantic-identity`  
**Acceptance date:** 2026-08-26

## Scope

This slice establishes stable Wenu-owned identity from the domain layer through
the canonical Matplotlib rendering path and into serialized SVG. It does not
reorder artists, replace Matplotlib, or claim a complete editable-layer model.

A renderer-neutral immutable `SemanticLayerIdentity` is resolved from stable
layer metadata rather than translated labels or drawing order. Ordinary layers
use their `layer_name`; coordinate-grid layers combine the established
`coordinates_grid` family with their stable coordinate-system identity, for
example `equatorial_grid`.

The corresponding public SVG identifier is deterministic:

```text
stars              -> wenu-layer-stars
constellation_lines -> wenu-layer-constellation-lines
equatorial_grid    -> wenu-layer-equatorial-grid
```

Each Matplotlib artist receives a unique anchor below that identity, such as
`wenu-layer-constellation-lines--artist-0001`. The numeric suffix is an
internal artist discriminator; the semantic prefix is the stable Wenu-owned
contract.

Renderers that do not implement semantic assignment remain supported. PNG and
PDF follow the same geometry and drawing path and receive no format-specific
scientific behavior.

## Regional proof

A regional Centaurus, Crux, and Musca chart was generated through the public
CLI with constellation lines and labels, a labeled equatorial grid, legends,
and the ordinary maximal-sphere object layers. Focused tests passed 46 tests in
3.46 seconds before the representative export.

The serialized SVG exposed semantic anchors for:

| Semantic layer | Artists |
| --- | ---: |
| Stars | 1 |
| Constellation labels | 4 |
| Constellation lines | 36 |
| Equatorial grid | 46 |
| Galaxies | 20 |
| Globular clusters | 11 |
| Milky Way isophotes | 49 |
| Open clusters | 1 |
| Supernova remnants | 64 |

The chart opened correctly in Inkscape. Fit drawing and fit page both reported
196 percent. Its visual appearance matched the pre-identity regional chart.
Wenu semantic anchors appeared in the Layers and Objects panel. Existing
object identities such as constellation-label objects remained selectable, and
a label could be selected and moved independently on the canvas.

## Stacking finding

Matplotlib serializes artists by global paint order, not strictly by semantic
layer. Direct children of `axes_1` showed:

| Semantic layer | Positions | Gaps inside span |
| --- | ---: | ---: |
| Constellation labels | 5–239 | 231 |
| Constellation lines | 53–88 | 0 |
| Equatorial grid | 93–139 | 1 |
| Galaxies | 140–159 | 0 |
| Globular clusters | 225–235 | 0 |
| Milky Way isophotes | 1–50 | 1 |
| Open clusters | 224 | 0 |
| Stars | 236 | 0 |
| Supernova remnants | 160–223 | 0 |

The constellation-label result is decisive: one SVG parent group per semantic
layer would move elements across other painted content and could change the
chart. Wenu therefore does not regroup serialized elements in this slice.
Semantic identity is added in place, preserving the existing global
`zorder` behavior.

## Contract and deferred work

49F.2A establishes:

- immutable renderer-neutral semantic identity;
- deterministic Wenu SVG identity prefixes;
- unique per-artist SVG anchors;
- preservation of geometry, clipping, object identity, and paint order;
- Inkscape discovery and object-level editing proof.

It deliberately defers:

- a single Inkscape parent layer for every semantic category;
- an explicit Wenu stacking-band model for interleaved semantic content;
- class-level style vocabulary and editing policy;
- locking or protection metadata;
- font representation policy;
- binocular SVG size and interaction optimization.

A future grouping slice must define stacking bands before restructuring the SVG
tree. It must not infer grouping from incidental Matplotlib element order or
silently alter the accepted chart appearance.
