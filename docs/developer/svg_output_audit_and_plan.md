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
- remain inspectable in a standards-compliant browser and practical vector
  editor;
- avoid tests coupled to irrelevant Matplotlib element identifiers, ordering,
  or serialization details.

SVG output must not:

- choose an astronomical frame, observer, instant, projection, or detail
  policy;
- introduce another celestial scene, preparation pipeline, chart family,
  renderer, furniture owner, or final-save path;
- silently alter geometry to accommodate an output backend;
- serve as Wenu's internal scene representation;
- serve as the Wenu3D interchange format.

## 5. Font policy

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

## 6. Relationship to Wenu3D

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

## 7. Constellation artwork

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

## 8. Representative SVG verification matrix

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
- no unexpected `image` element or raster data URI exists;
- both font policies satisfy their declared structural contract;
- transparency and background behavior match the product;
- the corresponding PNG or PDF has the same astronomical geometry and visual
  hierarchy;
- browser and vector-editor inspection records any portability difference.

Tests should assert semantic invariants and tolerances, not Matplotlib-generated
identifier strings or complete serialized snapshots.

## 9. Planned implementation milestones

### Milestone 49F.1 - Reference generation and structural audit

- generate the verification matrix through existing public requests;
- characterize current physical dimensions, view boxes, text policy, clipping,
  transparency, metadata, and raster payloads;
- add backend-tolerant SVG inspection helpers and focused tests;
- record defects without changing the renderer unless a minimal correction is
  separately approved.

### Milestone 49F.2 - Explicit output and font policy

- define public output-format and SVG-font-policy vocabulary;
- make single-file, directory, and all-product naming deterministic;
- expose the selected policy through the unified CLI and configuration;
- reject contradictory filename and explicit-format requests;
- retain one final save and the same chart/export owners.

### Milestone 49F.3 - Documentation and product acceptance

- document SVG in CLI help, configuration, implementation reference, source
  tree, README, and user guide;
- record reproducible representative commands and artifacts;
- inspect in at least one browser and one practical vector editor;
- compare against atlas-print visual authorities;
- record accepted limitations and close the supported product contract.

## 10. Stop conditions

Stop and re-audit if SVG work would:

- introduce a second astronomical, projection, rendering, furniture, or export
  pipeline;
- make SVG choose different geometry or content;
- expose raw Matplotlib configuration as Wenu's only public contract;
- make serialized SVG structure rather than semantic behavior the test oracle;
- treat SVG as the internal celestial scene or Wenu3D exchange format;
- embed unexplained raster payloads;
- mix constellation-art registration implementation into SVG verification;
- begin 3D scene implementation before its scientific and semantic inputs are
  explicit.

## 11. Completion definition

Milestone 49F is complete when Wenu exposes a documented, deterministic SVG
product through its canonical workflow; representative chart families pass
structural, physical, font, transparency, raster-payload, and visual
acceptance; 2D geometry is identical to established products; and the SVG
contract remains cleanly downstream of the scientific scene needed for Moon,
planet, constellation-artwork, and future Wenu3D work.
