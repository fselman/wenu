# Milestone 49F.4A: Exact paint order without coarse grouping

**Status:** Implemented; full-suite and real-SVG verification complete
**Base:** `c88c4df`
**Branch:** `feature/svg-product-documentation`
**Decision date:** 2026-08-26

## Decision

Wenu no longer defines or serializes coarse paint-order groupings. Exact
drawing order is already represented by SVG XML order, numerical
`data-wenu-zorder`, and the optional registered
`data-wenu-paint-role`. Another coarser category did not answer an essential
product question and risked being mistaken for semantic ownership.

The removal was requested during the 49F.4 documentation review, before Wenu
1.0 could freeze the unnecessary concept as public SVG API.

## Clean separation of concerns

The current SVG contract answers four independent questions:

| Question | Authority |
|---|---|
| What is the object? | Upstream semantic identity and `data-wenu-layer` |
| How is it drawn? | Style roles and SVG presentation |
| When is it drawn? | Existing XML order, exact z-order, and optional registered paint role |
| What may an editor change? | `data-wenu-edit` |

A registered paint-role name describes one exact numerical position. It does
not classify the object occupying that position. If a constellation label uses
the numerical position registered as `stars`, it remains a constellation
label and must never be inferred to be a star or placed under a semantic stars
group.

The low-level SVG annotation code receives resolved metadata from upstream. It
does not contain or reconstruct astronomical knowledge from coordinates,
styles, text, Matplotlib-generated identifiers, or paint positions.

## Runtime removal

The change removes:

- the `PaintBand` type;
- all grouping constants and registries associated with it;
- the field formerly carried by `PaintRole`;
- SVG `wenu-band-*` class tokens;
- SVG `data-wenu-paint-band` attributes;
- tests and documentation that treated coarse stacking as product structure.

`PaintRole` now contains only its exact numeric z-order and registered name.
The existing numerical layer constants, geometry, clipping, appearance, and
XML order are unchanged.

## Semantic hierarchy direction

The planned logical constellation hierarchy is:

```text
constellations
    constellation-artwork
    constellation-boundaries
    constellation-lines
    constellation-labels
```

Semantic ownership is independent of paint order. A physical SVG parent may be
created only when it preserves established rendering. If one logical group
occupies separated positions, ordered physical fragments may share semantic
class and logical-parent metadata. The serializer must not reorder artists to
make the editor tree resemble the conceptual taxonomy.

Hierarchical grouping remains a later, separately tested implementation slice.
This milestone removes an unsuitable organizing concept; it does not yet move
or wrap SVG elements.

## Compatibility

This intentionally changes the experimental SVG metadata accepted during
49F.2C. Files generated before this decision may retain the removed class and
attribute, but newly generated SVG does not emit them. Wenu does not interpret
external edited SVG as scientific input, so no migration or reader change is
required.


## Verification

The focused runtime, configuration, CLI, documentation, renderer, and package
boundary suite passed:

```text
137 passed in 4.93s
```

A fresh Centaurus, Crux, and Musca regional SVG contained:

```text
semantic artists: 232
edit policies: {'layout': 4, 'style': 228}
missing exact paint roles: 0
band attributes: 0
band classes: 0
```

Semantic-layer counts were unchanged from the accepted 49F.2C/49F.2D chart.
The runtime removal therefore preserves semantic ownership and supported
editing classification while eliminating the unnecessary metadata.


Final verification on Fernando Selman's clean, synchronized Mac checkout:

```text
git diff --check: no output
1616 passed in 56.38s
```
