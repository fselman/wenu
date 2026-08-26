# SVG output and editing

Wenu supports three chart-output formats through the same astronomical,
projection, composition, and final-save workflow:

| Format | Intended use | Text |
|---|---|---|
| PNG | fixed raster preview and delivery | pixels |
| PDF | portable publication and printing | publication text |
| SVG | vector editing in Inkscape and compatible editors | editable SVG text |

Select the format explicitly with:

```text
--format png
--format pdf
--format svg
```

SVG has one public contract: its labels and furniture remain genuine SVG
`<text>` elements. Wenu does not expose a separate SVG font-policy switch.
Use PDF when the primary requirement is portable publication rather than
downstream vector editing.

## Generate an editable SVG

For example:

```bash
wenu_chart regional \
  --constellations Cen,Cru,Mus \
  --mask \
  --field-width 60 \
  --field-height 45 \
  --orientation celestial-north-up \
  --observer-latitude -32.452 \
  --observer-longitude -71.231 \
  --observer-time 2026-08-21T21:00:00 \
  --observer-timezone America/Santiago \
  --constellation-lines \
  --constellation-labels \
  --equatorial-grid \
  --equatorial-grid-labels \
  --format svg \
  --output output/centaurus-crux-musca.svg
```

An explicit format and a single-file suffix must agree. For example,
`--format svg --output chart.pdf` is rejected. Existing commands that omit
`--format` retain their established naming behavior.

## Supported editing contract

Wenu annotates its SVG objects with stable Wenu-owned IDs, classes, and data
attributes. Representative semantic objects expose:

- `data-wenu-layer`: logical layer ownership;
- `data-wenu-paint-role` and `data-wenu-paint-band`: stacking identity;
- `data-wenu-edit="style"`: appearance and visibility may be edited, but
  scientific position and geometry must not be moved;
- `data-wenu-edit="layout"`: appearance, visibility, and label layout may be
  edited.

Inkscape is the reference editor. Constellation labels can be selected, moved,
rewritten, and given a different font family, size, weight, or color.
Scientific objects such as stars, grid curves, and constellation lines remain
individually selectable, but changing their positions produces a
scientifically modified derivative that Wenu does not certify.

The editing classification is authoritative workflow metadata, not a
tamper-proof lock. Standard SVG has no lock mechanism enforced by every
editor.

## Fonts and portability

Editable SVG normally names a font family but does not embed the font file.
When the named font is unavailable, a browser or editor may substitute a
fallback. Different glyph metrics can shift labels or change spacing.

Before publication, inspect the SVG on the destination system. Install the
documented font, choose an available replacement and review the layout, or
produce PDF for the portable publication copy. Font embedding in SVG is not
part of the current Wenu contract.

## Safe editor workflow

1. Keep the Wenu-generated SVG as the reproducible source artifact.
2. Open it in Inkscape and save editorial work under a separate filename.
3. Edit objects according to their `data-wenu-edit` classification.
4. Do not move scientific geometry.
5. Reopen the saved copy and inspect typography, clipping, masks, and page
   dimensions before delivery.

Wenu-generated semantic metadata and editable text have been verified through
an Inkscape Save As round trip. Illustrator interoperability is useful but
optional and does not define the SVG contract.
