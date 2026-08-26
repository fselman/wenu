# Milestone 49F.1 SVG structural audit

**Status:** Remote structural harness implemented; representative rendering and
Mac acceptance pending  
**Base:** `929a88c`  
**Branch:** `feature/svg-structural-audit`  
**Audit date:** 2026-08-26

## Scope

This audit observes the SVG currently emitted through Wenu's canonical
Matplotlib export path. It does not change rendering, select an output format,
define semantic SVG layers, or establish a public font policy.

Generated charts and temporary audit artifacts remain outside the repository.

## As-is execution path

The inspected implementation has one output-neutral execution path:

```text
resolved request and composition
    -> CelestialSphere.draw_chart()
    -> MatplotlibRenderer
    -> furniture and legends
    -> ExportOptions.save()
    -> Matplotlib figure.savefig()
```

`ExportOptions.save()` passes the destination directly to
`figure.savefig()`. A filename ending in `.svg` therefore selects
Matplotlib's SVG backend without a Wenu-specific renderer or astronomical
branch.

Ordinary chart exports default to `bbox_inches="tight"`. Physical polar page
and pouch exporters deliberately override that value with
`bbox_inches=None` so the requested paper dimensions remain authoritative.

## Inspection boundary

`wenu.rendering.svg_inspection.inspect_svg()` records only structural facts
that are meaningful across ordinary SVG serializers:

- SVG root namespace;
- numeric width and height plus their serialized units;
- the four-value view box;
- counts by XML local element name;
- image references and the presence of raster image elements.

It deliberately does not expose Matplotlib-generated identifiers, serialization
order, complete XML snapshots, or backend-private grouping as Wenu contracts.

Focused tests exercise:

- parseable SVG produced through the existing `ExportOptions.save()` path;
- both Matplotlib text-as-text and text-as-path behavior;
- clip-path presence without relying on a generated identifier;
- metadata presence;
- absence of raster image elements in a vector-only reference;
- detection of an embedded raster data URI;
- exact A4 physical dimensions for a non-tight export;
- rejection of missing or malformed dimensions and view boxes.

## Current structural findings

| Concern | Current finding | Consequence |
| --- | --- | --- |
| Backend selection | Inferred from the destination suffix | Incidental SVG works for an explicitly named file |
| Astronomical path | Identical to other static outputs | No second scientific or projection pipeline is needed |
| Ordinary sizing | Tight bounding box by default | Serialized dimensions depend on drawn extents |
| Physical products | Non-tight export with explicit figure size | Paper dimensions can remain exact |
| Dimension units | Matplotlib serializes physical SVG size in points | Tests must compare units and numeric tolerances |
| View box | Matplotlib emits a four-number view box | Physical-size and coordinate-space agreement is testable |
| Font representation | Controlled by Matplotlib's `svg.fonttype` setting | Current behavior is not yet a Wenu public policy |
| Clipping | Expressed with SVG clip paths | Tests can require clipping without freezing generated IDs |
| Metadata | SVG metadata is emitted by Matplotlib | Exact backend serialization is not a product API |
| Raster payloads | Detectable as SVG `image` elements | Each representative chart must be checked |
| Semantic layers | No Wenu-owned hierarchy exists | This remains Milestone 49F.2 |
| Class-level editing | No Wenu-owned class vocabulary exists | This remains Milestone 49F.2 |
| Format selection | No explicit Wenu output-format vocabulary exists | This remains Milestone 49F.3 |

## Representative verification matrix

The following products must be generated through their existing public requests.
The table distinguishes automated structure from visual and editor acceptance;
it must not be marked accepted merely because XML parsing succeeds.

| Product | Structural focus | Human focus | Status |
| --- | --- | --- | --- |
| Regional | Rectangular viewport, masks, labels | SVG/PNG geometry and hierarchy | Pending Mac render |
| Planisphere | Circular boundary, outside transparency | Legends, footer, background | Pending Mac render |
| Galactic all-sky | Mollweide ellipse, seam splitting | Grid labels and seam behavior | Pending Mac render |
| Binocular | Circular aperture, dense symbols | Magnitude scale and labels | Pending Mac render |
| Circumpolar | Declination boundary and clipping | Reference grids | Pending Mac render |
| Polar disk/page or pouch | Exact paper size, non-tight page | Furniture and typography | Pending Mac render |

For every generated SVG, record:

1. XML parsing and SVG namespace;
2. width, height, units, and view box;
3. clip-path, mask, text, path, and image counts;
4. whether raster image payloads are present;
5. background and transparency behavior;
6. the active Matplotlib text representation;
7. comparison with the corresponding PNG or PDF;
8. browser rendering;
9. Inkscape opening and object inspection.

Illustrator remains an optional interoperability check and does not define
acceptance.

## Defects and deferred decisions

The audit confirms these pre-existing product gaps without correcting them:

- users cannot explicitly select a format independently of output naming;
- directory and all-product naming remain tied to the configured extension;
- font representation is an undeclared Matplotlib setting;
- SVG contains no Wenu-owned semantic layer, object identity, class, or editing
  classification;
- scientific geometry is not guarded through a documented SVG editing policy;
- browser and Inkscape acceptance have not yet been recorded.

These belong to Milestones 49F.2 through 49F.4. They are not reasons to create a
second renderer during 49F.1.

## Acceptance and closure

Remote acceptance requires the focused SVG tests and the full test suite.
Scientific and visual closure additionally requires the representative matrix
to be rendered and inspected on Fernando's Mac. Until those checks are
recorded, 49F.1 remains open and no supported SVG product is claimed.
