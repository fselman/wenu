# Wenu SVG output audit and plan

**Milestone:** 49F.0  
**Status:** Approved planning and documentation; runtime implementation not started  
**Planning baseline:** `d315c51`  
**Decision date:** 2026-08-25

## 1. Purpose and authority

This document converts the SVG direction in
`post_v0.9_architecture_roadmap.md` into an inspectable implementation and
acceptance plan. It records the current SVG behavior, the intended 2D vector
product contract, the boundary with the future Wenu3D program, and the
relationship between vector output and constellation artwork.

It does not declare current incidental SVG output production-ready. It does not
authorize a new renderer, a 3D implementation, or constellation-artwork
implementation. Each behavioral stage requires its own as-is check and bounded
milestone.

## 2. Product and release direction

The intended release sequence is:

1. Wenu 1.0 rationalizes coordinate and astronomical-state ownership, adds the
   Moon and planets through explicit position providers, and closes a governed
   static 2D chart product including documented SVG output.
2. Wenu 1.x may introduce registered constellation artwork through the same
   semantic celestial geometry used by ordinary charts.
3. Wenu 2.0 introduces Wenu3D as a distinct realization of shared astronomical
   and semantic state, with its own camera, material, lighting, depth, scene,
   rendering, animation, and export policies.

SVG strengthens the 1.0 publication product. It must not constrain the 2.0
scene architecture.

## 3. Current as-is

Wenu already reaches Matplotlib's SVG backend through the canonical export
path when the destination filename ends in `.svg`.

The ordinary path is:

```text
resolved chart request and composition
    -> canonical spherical and projected geometry
    -> CelestialSphere.draw_chart()
    -> MatplotlibRenderer
    -> furniture and legends
    -> ExportOptions.save()
    -> figure.savefig(path, ...)
```

`ExportOptions.save()` passes the destination path to
`Matplotlib.figure.savefig()`. Matplotlib therefore infers SVG from the file
extension. There is no SVG renderer, SVG chart family, or SVG-specific
astronomical path.

Current limitations and unverified behavior:

- the packaged product extension is `.png`;
- one explicitly named output can already use `.svg`;
- directory and `--all-products` naming use the configured default extension
  and expose no convenient explicit format selection;
- `mode.print.prefer_vector` describes output preference but does not select
  an output format;
- SVG is not a documented supported CLI, configuration, Python, or user-guide
  product;
- no test protects SVG physical dimensions, view box, clipping, masks,
  transparency, symbols, labels, legends, furniture, metadata, or absence of
  unintended raster payloads;
- no font policy distinguishes reproducible publication output from editable
  working output;
- no representative SVG has recorded visual acceptance.

The architecture should first verify this existing path. A dedicated SVG
renderer is considered only after a concrete requirement is shown to be
impossible or materially defective in Matplotlib's backend.

## 4. Product contract

A supported Wenu SVG is a two-dimensional vector publication or editing
product generated from the same resolved chart and canonical rendering flow as
PNG and PDF.

SVG output must:

- preserve identical astronomical selection and projected geometry;
- preserve chart-owned framing, viewport, boundary, and clipping;
- preserve style, detail, legend, furniture, title, and footer semantics;
- record deterministic physical dimensions and a corresponding view box;
- preserve intentional transparency, face color, masks, alpha, line styles,
  symbols, and text orientation;
- contain no unexpected embedded raster image payload;
- remain inspectable in a standards-compliant browser and editable in
  Inkscape, the primary reference editor;
- expose a Wenu-owned semantic layer and object hierarchy with stable public
  identifiers and classes;
- permit whole-layer editing and object-level editing where the semantic
  object is independently meaningful;
- remain practically interoperable with other SVG-capable editors, including
  Illustrator when available, without making any editor's private document
  model authoritative;
- avoid tests coupled to irrelevant Matplotlib-generated identifiers,
  incidental ordering, or serialization details.

SVG output must not:

- choose an astronomical frame, observer, instant, projection, or detail
  policy;
- introduce another celestial scene, preparation pipeline, chart family,
  renderer, furniture owner, or final-save path;
- silently alter geometry to accommodate an output backend;
- serve as Wenu's internal scene representation;
- serve as the Wenu3D interchange format;
- expose Matplotlib's incidental artist tree as the supported editing
  abstraction;
- require Illustrator or any proprietary editor to exercise a promised editing
  capability.

## 5. Editable SVG document model

The editable SVG product is a structured document, not merely a picture that
happens to use vector primitives. Wenu owns this structure. Neither Matplotlib,
Inkscape, Illustrator, nor another editor defines the authoritative layer
taxonomy.

The SVG root must contain stable nested groups representing Wenu semantic
roles. The initial hierarchy to verify and refine during Milestone 49F.1 is:

```text
wenu-chart
    background
    sky-area
        milky-way
        coordinate-grids
            equatorial-grid
                grid-lines
                grid-labels
            ecliptic-grid
            galactic-grid
            horizontal-grid
        reference-curves
        constellation-artwork
        constellation-lines
        deep-sky-objects
        stars
        solar-system
            sun
            moon
            planets
        labels
            star-labels
            constellation-labels
            object-labels
    masks-and-boundaries
    legends
    furniture
        title
        footer
        attribution
```

Only groups relevant to a particular product need be emitted. The audit may
adjust names or nesting before they become public, but the accepted vocabulary
must then be documented and versioned. New semantic roles must extend this
taxonomy rather than depend on backend-generated group names.

### Layer and object identity

- Each public semantic group must have a stable, unique XML `id` and a
  semantic `class`; display names may also be supplied for editor layer
  panels.
- Repeated astronomical objects must carry stable identities derived from
  Wenu-owned catalogue or semantic identifiers, not draw order.
- Independently meaningful objects must be addressable within their layer. For
  example, one constellation label must be selectable and movable without
  ungrouping every constellation label, and its identifier must remain distinct
  from the visible translated text.
- Geometry reused as a symbol may use SVG definitions and references only when
  common editors still permit the promised object-level editing. Otherwise the
  editable policy may deliberately emit expanded objects.
- Clip paths, masks, definitions, and backend bookkeeping may remain technical
  structures, but must not replace or obscure the public semantic hierarchy.
- Z-order must follow the documented Wenu hierarchy while preserving the
  established visual result.

### Editing permissions and scientific integrity

"Editable" does not mean that every property may be changed legitimately.
Wenu must classify exported objects by the editing operations that preserve
their meaning:

| Semantic category | Appearance | Visibility | Position or geometry |
| --- | --- | --- | --- |
| Scientific geometry: stars, constellation-line vertices, coordinate curves and grids, object positions, chart boundaries, registered artwork geometry | Editable | Editable | Locked; not a supported edit |
| Scientific symbols whose position is meaningful | Editable | Editable | Locked; not a supported edit |
| Annotation labels: constellation, star, coordinate, and object labels | Font and appearance editable | Editable | Editable when the product marks the label as layout-adjustable |
| Legends, titles, footer, attribution, and other furniture | Editable | Editable | Editable within the page-layout contract |
| Technical definitions, clip paths, masks, and transforms | Not a user editing surface | Not a user editing surface | Not a user editing surface |

Therefore, in an editable SVG, a user must be able to:

- select the constellation-lines layer and change its color or line width
  without changing any vertex position;
- select a coordinate-grid layer and restyle its lines separately from its
  labels without changing the grid geometry;
- select all constellation labels and change their font properties;
- select one layout-adjustable constellation label and move or restyle it
  independently;
- hide or show a complete semantic layer without damaging unrelated content;
- inspect an object's Wenu identity and editing classification without
  inferring them from visible text or serialized position.

Scientific groups should be locked by default in the primary reference editor
when this can be represented without compromising standard SVG. Because SVG
does not provide a universally enforced, editor-independent lock, this is a
workflow guard rather than tamper-proof protection. Wenu's documented
`data-wenu-edit` classification (for example `style`, `layout`, or
`none`) is authoritative; editor-specific lock metadata is optional and
advisory.

Moving a locked scientific object in an external editor creates a scientifically
modified derivative that Wenu does not certify. No external edit alters Wenu's
astronomical source or feeds coordinates back into Wenu.

### Editor policy

Standards-compliant SVG and Wenu's documented hierarchy are normative.
Rendering in current mainstream browsers is the baseline portability check.
Inkscape is the primary reference editor because it is free and open source,
uses SVG as its native document format, exposes nested layers and objects, and
permits direct XML inspection.

Illustrator is an optional secondary interoperability check because it is
widely used in professional illustration and publishing. It is not required,
and Adobe-specific namespaces, layer conventions, or round-trip behavior must
not become part of Wenu's contract. Scribus may later be checked for page
layout and print/PDF workflows, but it is not the reference SVG editor.

## 6. Font policy

Wenu will support two explicit SVG font policies:

### Reproducible publication

Convert text to vector paths. This is the default candidate for archival and
portable publication output because it preserves glyph appearance without
requiring the receiving system to have the original fonts.

Acceptance must verify:

- all expected labels remain visible;
- Spanish and English glyphs are preserved;
- file size remains practical;
- path conversion does not introduce raster images;
- the resulting text is intentionally not searchable or directly editable as
  text.

### Editable working output

Retain text as SVG text elements. This output is intended for editing,
searching, accessibility work, and downstream typographic adjustment.

Acceptance must verify and document:

- required font family and fallback policy;
- expected behavior when the font is unavailable;
- possible text reflow or metric changes in browsers and vector editors;
- no silent claim of byte-for-byte visual portability.

The implementation milestone must name this policy through Wenu's public
product/export vocabulary rather than requiring users to know Matplotlib
configuration keys.

## 7. Relationship to Wenu3D

SVG is a language for two-dimensional vector and mixed vector/raster graphics.
It is not the shared representation between Wenu and Wenu3D.

The shared boundary must instead be renderer-neutral astronomical and semantic
scene state:

```text
catalogue, ephemeris, or orbit provider
    -> explicit astronomical state
    -> coordinate service
    -> typed semantic celestial scene
         -> 2D chart realization -> Matplotlib -> PNG / PDF / SVG
         -> 3D scene realization -> Wenu3D -> image / animation / glTF / GLB
```

The shared semantic scene may carry:

- stable astronomical identity and provenance;
- explicit direction or position, coordinate frame, origin, epoch, instant,
  observer, and physical-status metadata as applicable;
- typed points, curves, surfaces, labels, and semantic symbols;
- selection and visibility state;
- time-dependent provider state;
- appearance roles that remain independent of Matplotlib artists, SVG
  elements, or 3D meshes.

The 2D and 3D realizations may legitimately represent the same semantic object
differently. A star may be a magnitude-scaled 2D marker and a luminous point,
billboard, or symbolic sphere in 3D. The Moon may be a phase-correct 2D disk
and an illuminated sphere in 3D. Those differences belong downstream of the
shared scientific state.

For initial portable 3D delivery, glTF/GLB is the likely format to evaluate
because it represents scene nodes, transformations, meshes, materials,
textures, cameras, and animation. OpenUSD remains a later option only if Wenu
develops complex composed-asset or digital-content-creation workflows that
justify its greater scope.

No glTF, GLB, USD, camera, lighting, material, depth, or 3D-scene contract is
introduced by Milestone 49F.

## 8. Constellation artwork

Constellation artwork is a semantic celestial asset, not an output-format
special case. Its source artwork and celestial registration must remain
separate.

### Artwork asset

An artwork record may reference:

- SVG paths for line or vector illustration;
- an alpha-capable raster asset for painted illustration;
- stable asset and constellation identifiers;
- artist, source, provenance, copyright, and licence;
- intrinsic authoring dimensions and artwork revision.

### Celestial registration

A separate immutable registration must define:

- constellation identity;
- anchor stars or celestial control points;
- authoring coordinate system;
- scale, orientation, handedness, deformation, and sampling policy;
- visibility, opacity, layering, seam, clipping, and mask behavior;
- attribution requirements.

A 2D chart cannot generally paste a flat SVG rectangle over a nonlinear sky
projection. Registered paths or a sampled artwork mesh must be transformed,
warped, projection-guarded, projected, seam-split, and clipped through
canonical geometry.

Wenu3D may realize the same registration as vector strokes, a transparent
triangulated mesh, or a texture on a spherical patch. SVG can therefore be a
useful constellation-art source format without becoming the 3D scene format.

A future first artwork milestone should use one licensed constellation as a
vertical slice and prove registration, nonlinear projection, seam behavior,
clipping, attribution, and 2D/3D reuse before adding a full collection.

## 9. Representative SVG verification matrix

The first behavioral verification should cover:

| Product | Primary contract |
| --- | --- |
| Regional chart | rectangular viewport, masks, labels, context, ordinary CLI path |
| Planisphere | circular boundary, outside transparency, legends and footer |
| Galactic all-sky | Mollweide ellipse, seam-split geometry, grid labels |
| Binocular chart | circular aperture, dense stars, semantic symbols, magnitude scale |
| Circumpolar chart | declination boundary, circular clipping, reference grids |
| Polar disk/page or pouch | exact physical size, non-tight page, furniture, symbols and typography |

For each representative product verify:

- XML parses and has an SVG root;
- width, height, units, and view box agree with the product request;
- expected clip paths and visible drawing classes exist;
- required Wenu semantic groups, IDs, classes, nesting, and z-order exist;
- representative layers and individual labels can be selected according to
  their editing classification without destructive ungrouping;
- scientific geometry carries the non-layout editing classification and is
  locked by default where the reference editor permits it;
- permitted style edits leave scientific positions and geometry unchanged;
- no unexpected `image` element or raster data URI exists;
- both font policies satisfy their declared structural contract;
- transparency and background behavior match the product;
- the corresponding PNG or PDF has the same astronomical geometry and visual
  hierarchy;
- browser rendering and Inkscape editing acceptance are recorded;
- optional Illustrator inspection records interoperability differences without
  redefining the contract.

Tests should assert documented Wenu semantic identities, hierarchy, editing
invariants, and numeric tolerances. They must not assert incidental
Matplotlib-generated identifiers or complete serialized snapshots.

## 10. Planned implementation milestones

### Milestone 49F.1 - Reference generation and structural audit

- generate the verification matrix through existing public requests;
- characterize current physical dimensions, view boxes, text policy, clipping,
  transparency, metadata, and raster payloads;
- add backend-tolerant SVG inspection helpers and focused tests;
- record defects without changing the renderer unless a minimal correction is
  separately approved.

### Milestone 49F.2 - Semantic document structure

- finalize and document the public semantic layer taxonomy;
- map existing Wenu rendering roles and stable object identities onto SVG
  groups, IDs, classes, and editor display names;
- preserve existing geometry, clipping, appearance, and the canonical final
  save while adding the supported document structure;
- add structural tests for nesting, identity, z-order, editing classification,
  scientific-geometry protection, and representative object-level editing;
- verify in Inkscape that scientific layers are guarded against accidental
  movement while permitted style and label-layout edits remain practical.

### Milestone 49F.3 - Explicit output and font policy

- define public output-format and SVG-font-policy vocabulary;
- make single-file, directory, and all-product naming deterministic;
- expose the selected policy through the unified CLI and configuration;
- reject contradictory filename and explicit-format requests;
- retain one final save and the same chart/export owners.

### Milestone 49F.4 - Documentation and product acceptance

- document SVG, the layer taxonomy, IDs, and editing guarantees in CLI help,
  configuration, implementation reference, source tree, README, and user guide;
- record reproducible representative commands and artifacts;
- inspect rendering in current mainstream browsers;
- perform the primary editing acceptance in Inkscape;
- record optional Illustrator interoperability results when Illustrator is
  available;
- compare against atlas-print visual authorities;
- record accepted limitations and close the supported product contract.

## 11. Stop conditions

Stop and re-audit if SVG work would:

- introduce a second astronomical, projection, rendering, furniture, or export
  pipeline;
- make SVG choose different geometry or content;
- expose raw Matplotlib configuration as Wenu's only public contract;
- make incidental serialized SVG structure rather than the documented Wenu
  semantic hierarchy and behavior the test oracle;
- make an editor-specific layer model or proprietary namespace authoritative;
- claim editable output while flattening promised layers or preventing
  independent selection of meaningful objects;
- imply that scientific geometry is freely repositionable or certify a
  derivative whose star, constellation-line, grid, boundary, or registered
  artwork geometry has been moved;
- treat SVG as the internal celestial scene or Wenu3D exchange format;
- embed unexplained raster payloads;
- mix constellation-art registration implementation into SVG verification;
- begin 3D scene implementation before its scientific and semantic inputs are
  explicit.

## 12. Completion definition

Milestone 49F is complete when Wenu exposes a documented, deterministic SVG
product through its canonical workflow; representative chart families pass
semantic-layer, classified-editability, scientific-geometry protection,
structural, physical, font, transparency,
raster-payload, browser-rendering, and Inkscape acceptance; 2D geometry is
identical to established products; optional Illustrator interoperability does
not define the product; and the SVG contract remains cleanly downstream of the scientific scene needed for Moon,
planet, constellation-artwork, and future Wenu3D work.
