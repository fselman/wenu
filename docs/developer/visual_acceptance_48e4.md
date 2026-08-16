# Milestone 48E.4 actual-size polar-page acceptance

**Status:** Awaiting generated-page and physical review

**Implementation base:** `b6a9044181acf78875bbde596919cfaf653e504f`

**Astronomical checkpoint:** `09a2afd`

## Generate the review PDFs

From a clean repository after committing Milestone 48E.4C:

```bash
python tools/render_48e4_polar_pages.py \
  --source-revision "$(git rev-parse --short HEAD)" \
  --output output/48e4-polar-pages
```

Expected untracked outputs:

- `polar-planisphere-south-a4.pdf`;
- `polar-planisphere-north-a4.pdf`;
- `manifest.json`.

Do not add these generated files to Git.

## Digital checks

- both PDF media boxes are exactly A4: 210 by 297 mm;
- each page contains one complete 195 mm disk without clipping;
- the stellar aperture is 164 mm in diameter inside the unchanged 195 mm
  cut disk, and the tightened date ring remains legible;
- the centre punch, dashed cut line, three registration glyphs, 50 mm ruler,
  and every required text role are present;
- the centre and registration marks are solid black for transmitted-light
  alignment;
- the north registration pattern is the left-right reflection of the south
  pattern, so corresponding marks coincide with both face titles upright;
- `SOUTH / SUR` and `NORTH / NORTE` identify the correct pages;
- page text is readable normally and is never mirrored;
- the manifest records both files, byte sizes, checksums, projection, page,
  disk, and stellar-aperture dimensions, DPI, and source revision;
- the known 48E.3 ecliptic/equator/reference-frame issues are unchanged.

## Physical checks

Print one set with `Actual Size` or `100%`; disable `Fit`, `Scale to Fit`, and
printer-driver enlargement or reduction.

Measure and record:

| Check | Requested | Measured south | Measured north |
|---|---:|---:|---:|
| page | 210 × 297 mm | pending | pending |
| disk diameter | 195.0 mm | pending | pending |
| scale ruler | 50.0 mm | pending | pending |
| centre punch radius | 1.0 mm | pending | pending |

Then:

- pierce both centre marks and confirm coincidence;
- place the blank sides together;
- keep both face titles upright and align triangle with triangle, circle with
  circle, and square with square against a light source;
- confirm that the triangular cue prevents an accidental 180-degree assembly;
- verify that no calendar label or information block is cut or obscured;
- confirm that instructions, La Ligua/Papudo coordinates, UTC-4, daylight-
  saving disclaimer, projection, coverage, magnitude 5.5, product identifier,
  and source revision are legible;
- record only print-blocking corrections before beginning the horizon overlay.

## Disposition

- Digital review: pending.
- Physical actual-size review: pending.
- Approved for classroom printing: pending Fernando Selman review.
