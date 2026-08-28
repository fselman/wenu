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

The test-side `inspect_svg()` helper records only structural facts
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
| Regional | Rectangular viewport, masks, labels | SVG/PNG geometry and hierarchy | Accepted on Mac |
| Planisphere | Circular boundary, outside transparency | Legends, footer, background | Accepted on Mac |
| Galactic all-sky | Mollweide ellipse, seam splitting | Grid labels and seam behavior | SVG parity accepted; label defects recorded |
| Binocular | Circular aperture, dense symbols | Magnitude scale and labels | Geometry accepted; editing performance defective |
| Circumpolar | Declination boundary and clipping | Reference grids | Accepted on Mac |
| Polar disk/page and pouch | Exact physical size, non-tight page | Furniture and typography | Accepted after metadata correction |

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


## Recorded representative results

All files were generated outside the repository on Fernando's Mac through the
existing public request or canonical physical-page exporter.

| Product | Size | Paths / uses | Clips | Raster | Inkscape result |
| --- | ---: | ---: | ---: | ---: | --- |
| Regional | 6.1 MB | 9,160 / not recorded | 1 | none | Correct; fit drawing/page 174% |
| Galactic all-sky | 2.8 MB | 3,583 / not recorded | 2 | none | Correct serialization; fit drawing/page 145% |
| Planisphere | 1.9 MB | 1,942 / not recorded | 2 | none | Correct; fit drawing/page 149% |
| Binocular, magnitude 11 | 40 MB | 60,055 / 171 | 2 | none | Correct but slow; fit drawing/page 149% |
| Circumpolar south to -35 degrees | 2.1 MB | 3,327 / 506 | 2 | none | Correct; fit drawing/page 149% |
| Polar south A4 | 2.0 MB | 2,611 / 1,522 | 3 | none | Correct; fit drawing/page 74% |
| Polar north A4 | 1.9 MB | 2,510 / 1,435 | 3 | none | Correct; fit drawing/page 74% |
| Polar pouch A4 | 93 KB | 104 / 302 | 2 | none | Correct; fit drawing/page 74% |

Every inspected document had matching physical dimensions and view box,
one metadata element, no SVG mask element, no image element, and no raster data
URI. Matplotlib's current default converted all visible text to paths.

The regional file initially opened at 6.1 percent zoom, but fit drawing and fit
page both produced 174 percent. This was an Inkscape initial-view quirk, not
evidence of far-off-page geometry. The binocular file showed a slight
horizontal recentering between fit drawing and fit page at the same rounded
zoom value; no visible geometry defect resulted.

The binocular file took approximately 10 seconds to open and 35 seconds to
close in Inkscape. Its 40 MB size and 60,055 paths are not practical for the
eventual editable product. Milestone 49F.2 must examine symbol reuse and
semantic object structure without sacrificing object-level editing.

The all-sky SVG and matching PNG both showed an incorrectly placed or oriented
Galactic-plane label and an incorrectly oriented celestial-equator label.
Because PNG and SVG match, these are existing all-sky label-placement defects,
not SVG serialization defects. The same reference labels were correctly
oriented in the planisphere and circumpolar products.

The canonical polar-page export initially failed because PDF-oriented
`Subject` metadata is rejected by Matplotlib's SVG writer. The approved
minimal correction translates `Subject` to SVG `Description` while
preserving non-SVG metadata. After that correction both canonical pages and the canonical pouch sheet
exported successfully at exactly 595.275591 by 841.889764 points, corresponding
to A4 210 by 297 mm. The pouch preserved its apertures, horizon boundaries,
folds, spine, cut and registration marks, title, instructions, and clipping.
Its 93 KB structure remained responsive in Inkscape.

## Defects and deferred decisions

The audit confirms these pre-existing product gaps without correcting them:

- users cannot explicitly select a format independently of output naming;
- directory and all-product naming remain tied to the configured extension;
- font representation is an undeclared Matplotlib setting;
- SVG contains no Wenu-owned semantic layer, object identity, class, or editing
  classification;
- scientific geometry is not guarded through a documented SVG editing policy;
- no Wenu-owned semantic layers appear in Inkscape; all products expose only
  backend structure rather than the planned editing hierarchy.

These belong to Milestones 49F.2 through 49F.4. They are not reasons to create a
second renderer during 49F.1.

## Acceptance and closure

Remote acceptance requires the focused SVG tests and the full test suite.
The representative matrix has been rendered and inspected on Fernando's Mac.
The post-correction full suite passed 1,590 tests in 57.83 seconds.
Milestone 49F.1 closes after the final branch diff and pull request are
reviewed. This audit still does not
claim the complete supported SVG product planned for Milestones 49F.2-49F.4.
