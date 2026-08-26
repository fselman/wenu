# Milestone 49F.2B semantic paint roles

**Status:** Implemented; focused tests complete  
**Base:** `d28eff6`  
**Branch:** `feature/svg-paint-roles`  
**Date:** 2026-08-26

## Purpose

49F.2A established stable semantic layer identity and demonstrated that the
current visual result cannot safely be rewritten as one SVG parent group per
logical layer. Matplotlib paints by global `zorder`; some layers, especially
constellation labels, contain artists at several positions with unrelated
content between them.

49F.2B makes that paint order explicit without changing it. It provides a typed
vocabulary that a later SVG grouping step can consume instead of inferring
meaning from backend element order.

## Typed model

`PaintRole` is an immutable exact paint position with:

- a stable semantic name;
- the established numeric `zorder`;
- one coarse `PaintBand`;
- an SVG-safe token.

The historical numeric constants in `wenu.rendering.layers` remain available
and retain exactly the same values. They are now derived from the typed role
registry, so existing styles and renderer calls do not change.

The ordered coarse bands are:

| Rank | Band | Representative roles |
| ---: | --- | --- |
| 0 | background | background |
| 1 | extended sky | Milky Way, Magellanic Clouds, galaxy fills |
| 2 | structure | boundaries, curves and grids |
| 3 | constellations | constellation figures |
| 4 | objects | galaxies, nebulae, clusters and remnants |
| 5 | stars | ordinary, bright, multiple and variable stars |
| 6 | points | named reference points and markers |
| 7 | labels | astronomical labels |
| 8 | overlays | outside masks and other final overlays |

Exact roles retain their established fractional distinctions. For example,
galaxies, supernova remnants, planetary nebulae, open clusters, and globular
clusters occupy ordered positions from 4.5 through 4.75 inside the objects
band.

## Rendering-result boundary

Each Matplotlib artist assigned a Wenu semantic SVG anchor now produces an
immutable `SemanticArtistRenderingResult` containing:

- the renderer artist reference;
- its stable SVG identifier;
- its exact numeric `zorder`;
- its matching typed paint role, when the position belongs to the registry.

These records are carried by `LayerRenderingResult.semantic_artists`. A
renderer that does not implement semantic assignment returns the established
rendering result with an empty semantic-artist tuple. An unnamed synthetic
layer remains supported and has no semantic identity or records.

A custom or backend-default numerical position that is not in the public
registry remains observable through `zorder` and has `paint_role=None`. Wenu
does not invent a public semantic role from an unknown number.

## Safe future SVG hierarchy

Semantic membership and paint hierarchy are orthogonal:

- semantic identity answers *what the content is*;
- paint role answers *where it must be painted*.

A future SVG realization must preserve the following order:

```text
paint band
    exact paint role / zorder
        consecutive semantic fragment
            addressable objects
```

Only consecutive elements may be wrapped together. If one logical semantic
layer occurs in several paint roles or separated runs, it must be represented
by several physical fragments. Those fragments share a semantic class and
`data-wenu-layer` value but require unique fragment IDs. They must not be moved
into one parent merely to simplify an editor panel.

This model permits class-level visibility and appearance edits across all
fragments of one logical layer while retaining the accepted visual result.
Editor display layers may expose paint bands, with semantic fragments below
them. A future acceptance test must verify whether this remains practical in
Inkscape before the hierarchy becomes a supported product contract.

## Contracts established

49F.2B establishes:

- one authoritative immutable paint-role registry;
- backward-compatible numerical layer constants;
- nine ordered coarse paint bands;
- exact role and band resolution for semantic Matplotlib artists;
- explicit representation of unknown/custom paint positions;
- a no-reordering rule for future SVG grouping.

It does not yet:

- alter SVG IDs or add SVG classes and data attributes;
- create SVG or Inkscape parent layers;
- move or regroup serialized elements;
- define class-level style rules;
- add editor-specific lock metadata;
- change geometry, clipping, appearance, or output selection.

Those operations belong to later 49F.2 slices and must build on this typed
boundary rather than inspect Matplotlib-generated names or reorder the accepted
chart.
