# Milestone 49F.2B semantic paint roles

**Status:** Implemented; full-suite verification complete  
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

- a stable registered name;
- the established numeric `zorder`;
- an SVG-safe token.

The historical numeric constants in `wenu.rendering.layers` remain available
and retain exactly the same values. They are derived from the typed role
registry, so existing styles and renderer calls do not change.

The registered name describes the exact position; it does not classify the
artist that occupies it. Exact roles retain established fractional
distinctions, including the ordered positions from 4.5 through 4.75.

## Rendering-result boundary

The shared `SemanticArtistRenderingResult` type is owned by the neutral
`wenu.chart_document` module. The `sky` and `rendering` packages remain sibling
packages and do not import one another.

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

A future SVG realization must preserve exact XML and numerical paint order
independently of semantic ownership. Only consecutive elements may be wrapped
together when wrapping would otherwise change rendering. If one logical
semantic layer occurs at separated positions, physical fragments may share its
semantic class and `data-wenu-layer` value while retaining unique IDs.

The SVG layer must not infer astronomical identity from a registered paint-role
name. In particular, an artist using the numerical position named `stars`
does not thereby become a star or a child of a stars group.

## Contracts established

49F.2B establishes:

- one authoritative immutable paint-role registry;
- backward-compatible numerical layer constants;
- exact role resolution for semantic Matplotlib artists;
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

## Verification

The final focused boundary, renderer, paint-role, orchestration, and SVG tests
passed 39 tests in 3.93 seconds. The complete suite passed 1,598 tests in 56.43
seconds. No visual acceptance rerun was required because this slice does not
alter serialized SVG properties, artist geometry, clipping, or paint order.
