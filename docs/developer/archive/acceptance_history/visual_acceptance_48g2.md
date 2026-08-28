# Visual acceptance — Milestone 48G.2C folded polar pouch

## Generated review command

```bash
python tools/render_48g2_polar_pouch.py \
  --source-revision "$(git rev-parse --short HEAD)" \
  --title "Muchos cielos, un firmamento" \
  --output output/48g2-polar-pouch
```

## Required digital checks

- Both PDFs have an A4 210 by 297 mm media box without tight cropping.
- The 195 mm disk guide is centred at `(105, 194.5)` mm.
- The fold is at 97 mm and tangent to the disk bottom.
- The complete disk remains 5 mm below the page top.
- The south horizon opens the larger southern sky above its concave cut.
- The north horizon opens the smaller northern sky above its convex cut.
- Both faces show three 37.5-degree date windows separated by 5 degrees.
- Date-window outlines are heavy enough to guide a hand cut, remain unfilled,
  and leave the disk's month names, day numbers, and date ticks readable.
- Each window retains a continuous outer paper strip over the disk's white
  edge margin.
- South hours run 19 at right through 05 at left.
- North hours run 19 at left through 05 at right.
- Every hour numeral is upright, bold, and inside the hour circle.
- Every short hour tick starts on the heavier hour circle and extends outward.
- Hour numerals sit close to the inside of the circle without touching it.
- South fixed labels are E, S, W, two curve-parallel `HORIZONTE` labels, and
  the raised italic title `Muchos cielos, un firmamento`.
- North fixed labels are bold W, N, E, and two curve-parallel `HORIZONTE`
  labels; all remain below the horizon cut on retained paper.
- E, W, and the face pole letter have equal local clearance below the horizon.
- Compass letters are paper instructions, not projected sky anchors.
- Fold, cut, hour, label, and glue marks are black.
- The single A4 sheet places south in the upper panel and north, rotated 180
  degrees, in the lower panel.
- North cardinal, horizon, and hour glyphs are upside down on the flat sheet
  and become upright after folding.
- Fold lines are at 148 and 149 mm, leaving a 1 mm folding spine.
- Each folded panel is 148 mm deep, so the 195 mm disk protrudes exactly 47 mm
  through the open edge for insertion after gluing.
- The diagnostic PNG shows both canonical disks faded, registered, and clipped
  behind the imposed pouch, with 15 August aligned to 21:00 on both faces; the
  fabrication PDF contains only clean marks.
- Each phantom disk center coincides with its imposed pouch disk-guide center;
  no canonical-page-to-pouch vertical offset remains.

## Physical print gate

1. Print the single sheet one-sided at 100 percent / Actual Size. Do not use
   Fit, Scale to Fit, or borderless enlargement.
2. Measure the disk guide: target 195 mm.
3. Measure the fold lines from the bottom page edge: targets 148 and 149 mm.
4. Verify that the lower panel is an exact 180-degree north-face imposition.
5. Cut one prototype sky opening and all three date windows.
6. Fold around the 1 mm spine with printed faces outward, glue only the narrow
   side zones, and insert the disk through the open edge.
7. Verify that the disk rests against the spine and protrudes 47 mm.
8. Rotate the disk by hand and confirm that date/hour alignment remains smooth
   and that the printed compass letters are used only to orient the assembled
   device toward the real horizon.

Record any duplex reflection, cut-path continuity, interference, or physical
scale defect before accepting the classroom print.
