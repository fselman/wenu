# Milestone 49F.2C semantic SVG attributes

**Status:** Implemented; focused tests and Mac editor acceptance complete  
**Base:** `e4fdbcf`  
**Branch:** `feature/svg-semantic-attributes`  
**Acceptance date:** 2026-08-26

## Scope

49F.2C serializes the semantic identity and paint-order records established in
49F.2A and 49F.2B as standard SVG classes and data attributes. It annotates
existing Wenu-owned artist groups in place. It does not create parent groups,
move elements, alter IDs, or change geometry, style, clipping, and paint order.

## Export boundary

The Matplotlib renderer attaches renderer-neutral semantic metadata to each
artist that already receives a Wenu SVG ID. After the canonical Matplotlib SVG
save, `annotate_semantic_svg()` adds attributes to the corresponding serialized
`g` element. The operation performs no XML tree restructuring.

A representative annotated group carries:

```xml
<g id="wenu-layer-constellation-lines--artist-0001"
   class="wenu-semantic-artist wenu-layer-constellation-lines
          wenu-paint-boundaries wenu-band-structure"
   data-wenu-layer="constellation_lines"
   data-wenu-zorder="2"
   data-wenu-paint-role="boundaries"
   data-wenu-paint-band="structure">
```

The exact class whitespace is ordinary SVG serialization and is not a contract.
The individual tokens and data values are the supported semantic facts.

SVG figures without Wenu semantic artists remain unchanged by the annotation
step. Non-SVG exports do not invoke it.

## Identity and paint meaning

Semantic identity and paint identity remain orthogonal:

- `data-wenu-layer` says what logical Wenu layer owns the artist;
- `data-wenu-zorder` records its exact established paint position;
- `data-wenu-paint-role` names that registered paint position;
- `data-wenu-paint-band` supplies its coarse stacking band.

A paint-role name does not reclassify the astronomical content. For example,
the current constellation-label artists occupy the numerical stars paint
position, so they remain members of `constellation_labels` while reporting the
`stars` paint role and band. This observed distinction is intentional and
prevents later grouping from confusing semantic ownership with stacking.

## Regional acceptance

The accepted Centaurus, Crux, and Musca regional command produced 232 semantic
artists:

| Semantic layer | Artists |
| --- | ---: |
| Constellation labels | 4 |
| Constellation lines | 36 |
| Equatorial grid | 46 |
| Galaxies | 20 |
| Globular clusters | 11 |
| Milky Way isophotes | 49 |
| Open clusters | 1 |
| Stars | 1 |
| Supernova remnants | 64 |

All 232 resolved to documented paint roles and bands; there were no custom or
unknown paint positions. The band distribution was:

| Paint band | Artists |
| --- | ---: |
| Constellations | 12 |
| Extended sky | 50 |
| Objects | 96 |
| Stars | 4 |
| Structure | 70 |

The SVG opened normally in Inkscape. The chart appearance, fit drawing/page,
and individual object selection were unchanged. Object properties exposed the
existing Wenu ID and the new classes and data attributes.

The file was saved from Inkscape under a new name. Before and after that editor
round trip, both files contained exactly 232 semantic artists, identical layer
counts, and zero missing paint-band attributes. Inkscape therefore preserves
the new standard metadata in the representative workflow.

## Contracts and deferred work

49F.2C establishes:

- standard SVG semantic and paint class tokens;
- explicit layer, exact zorder, paint-role, and paint-band data attributes;
- deterministic annotation of existing Wenu artist groups;
- no-op behavior for SVG without Wenu semantic artists;
- preservation through the accepted Inkscape round trip.

It deliberately defers:

- parent paint-band, paint-role, or semantic-fragment groups;
- shared class-level style rules;
- `data-wenu-edit` editing classification;
- advisory Inkscape locking metadata;
- font policy and explicit output-format selection;
- performance optimization for dense binocular SVG.

Later grouping must use these explicit attributes and the 49F.2B no-reordering
rule. It must not infer semantic meaning from Matplotlib-generated IDs or
visible text.
