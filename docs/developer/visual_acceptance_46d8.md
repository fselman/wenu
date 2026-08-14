# Milestone 46D.8 visual acceptance

**Status:** Pending Mac rendering and human approval

**Matrix source:** `tools/render_46d8_visual_matrix.py`

**Required source commit:** `5fa6bfa`

## Purpose

This fixed matrix closes visual parity after the automated observer, view,
drawing, configuration, precedence, and isolation contracts in Milestones
46D.8A–46D.8C. It invokes the actual `wenu_chart` module entry point in a fresh
process for every product. It does not add a rendering path or compare images
by an arbitrary pixel threshold.

Atlas print remains the golden baseline. Cartoon presentation is a parity
smoke product: it must retain the same scientific geometry and content meaning
while applying its distinct approved appearance and medium adaptation.
Every non-binocular product uses stellar magnitude limit 5.0; the binocular
products use 11.0 so their smaller fields retain the intended depth.

## Run

List the 18 products without rendering:

```bash
python tools/render_46d8_visual_matrix.py --list
```

Render the complete matrix and deterministic manifest:

```bash
python tools/render_46d8_visual_matrix.py \
  --output output/46d8-visual-matrix
```

One product can be repeated independently when review finds a question:

```bash
python tools/render_46d8_visual_matrix.py \
  --entry diagnostic-regional-explicit-field-horizon \
  --output output/46d8-visual-matrix-rerun
```

The runner stops on the first failed command. `manifest.json` records the
source commit, exact public command, output path, PNG dimensions, byte size,
and SHA-256 checksum for each successful product. Generated files remain
under `output/` and are not committed.

## Matrix

The first twelve products pair every canonical family in atlas-print and
cartoon-presentation modes:

| Family | Atlas print | Cartoon presentation |
| --- | --- | --- |
| Galactic all-sky | required | required |
| visible-sky planisphere | required | required |
| regional single constellation | required | required |
| regional constellation group with mask | required | required |
| southern circumpolar | required | required |
| binocular target | required | required |

Six atlas-print diagnostics cover the remaining high-risk combinations:

| Diagnostic | Required evidence |
| --- | --- |
| all-sky mask and horizon | disjoint regions, horizon reference, one effective translucent mask |
| regional explicit field and horizon | explicit width, height, angle, combined Oph/Ser mask, horizon crossing |
| binocular horizon | aperture, horizon reference, and below-horizon mask remain distinct |
| circumpolar horizon | declination boundary and observer horizon intersect correctly |
| planisphere horizon no-op | optional horizon roles do not duplicate or alter its intrinsic boundary |
| legends, references, and grids | four grids, three reference planes, poles, legends, counts, context, credits |

## Review checklist

For every product verify:

- the subject, center, orientation, extent, and boundary are correct;
- stars, constellation content, deep-sky objects, and Milky Way retain the
  expected scientific selection and hierarchy;
- grids, labels, reference planes, poles, legends, context, and footer do not
  collide or escape the chart boundary;
- masks are applied once, with no accumulated opacity or lost visible patch;
- atlas-print geometry and appearance have no unexplained change;
- cartoon-presentation changes appearance and scale, not geometry or meaning;
- the output is not empty, truncated, unexpectedly opaque, or mislabeled.

Record any defect by matrix entry name and retain its manifest record. Do not
approve 46D.8 visually until all 18 entries pass or every intentional change
is explained and accepted.

## Product review appendix

Use one checkbox in every criterion column for every product. Leave a box
unchecked when review is incomplete or a defect remains, and describe the
issue in the comment field.

- **F** — subject, center, orientation, field, and boundary
- **C** — scientific content and hierarchy
- **R** — grids, labels, references, poles, legends, context, and footer
- **M** — masks and clipping
- **A** — atlas-print baseline, or cartoon appearance without geometry drift
- **O** — complete, nonempty, correctly labeled output

| Product | F | C | R | M | A | O | Comment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `canonical-all-sky-atlas-print` | [+] | [-] | [-] | [+] | [+] | [+] | Too many PNs, OC. Label of grid should be half size. Latitude only in the central longitude. Place the latitude above and to the left. Draw the 0 latitude line and their mark the 0, 90, and 180 degrees. Color of grid should be subtler, blue-grey? |
| `canonical-all-sky-cartoon-presentation` | [+] | [-] | [-] | [+] | [+] | [+] | Add few of the brightes clusters and galaxies, including the MCs. Similar grid changes as in previous example.|
| `canonical-planisphere-atlas-print` | [+] | [-] | [-] | [+] | [+] | [+] | Too many clusters, PN, SNRs as in previous plots. Grid should be of a more subtle grey. Grid labels should be half size. Declination labels should stay in a single RA line, e.g. the central one, at upper-left corner of the intersection of the chosen RA line and the corresponding declination.|
| `canonical-planisphere-cartoon-presentation` | [+] | [-] | [-] | [+] | [+] | [+] | Same comments as before. In addition add the MW and MCs. Add a few of the brightest clusters and galaxies.|
| `canonical-regional-single-atlas-print` | [+] | [+] | [-] | [-] | [+] | [+] | It plots the single 12:00 RA line and no declination line. The line should be of a subtler grey. There should be at least two RA and two dec lines. The RA labels in format hh:mm and the Dec labels in dd:mm. Did not see the mask of the constellation (it is OK if not requested).|
| `canonical-regional-single-cartoon-presentation` | [+] | [-] | [-] | [+] | [+] | [ ] | I would add the MW contours. Same comments about a single grid line appearing. I would outline with a mask the constellation. |
| `canonical-regional-group-atlas-print` | [+] | [-] | [-] | [+] | [+] | [+] | Too many clusters, PNs. Label sizes correct. Declination label should be above the declination line (cannot read sign). I would make the grid a bit subtler too.|
| `canonical-regional-group-cartoon-presentation` | [+] | [+] |[-] | [-] | [+] | [ ] | I would add MW contours, and a few of the brighter clusters. Dec labels should be raised above Dec line. Masked region barely noticeable. It should look much whiter a more opaque.
| `canonical-circumpolar-atlas-print` | [+] | [+] | [-] | [+] | [+] | [+] | Grid should be of a subtler grey. The RA spacing should be every 2h.|
| `canonical-circumpolar-cartoon-presentation` | [+] | [+] | [-] | [+] | [+] | [+] | The RA spacing should be every 2h. |
| `canonical-binocular-atlas-print` | [+] | [+] | [-] | [+] | [+] | [-] | All stars look the same size (perhaps they should). There should not be a grid. Needs field center and diameter in the title.|
| `canonical-binocular-cartoon-presentation` | [+] | [-] | [-] | [+] | [+] | [-] | Needs the symbol for the target. There should not be a grid. Needs field center and diameter in the title. |
| `diagnostic-all-sky-mask-horizon` | [+] | [-] | [-] | [-] | [-] | [ ] | Too many clusters, PNs. Same issue with the grid as other all-sky. The above horizon unmasked area looks the same as the masked one. It seems to outline with the mask Cygnus and Crux. I do not see UMa masked. The horizon is properly drawn. |
| `diagnostic-regional-explicit-field-horizon` | [+] | [-] | [-] | [?] | [+] | [+] | Too many clusters and PNs. Although the constellations are masked, the horizon is nowhere to be seen. Equatorial grid should be subtler and Dec labesl should be above Dec lines. Not enough space outside constellation.|
| `diagnostic-binocular-horizon` | [-] | [+] | [-] | [?] | [+] | [+] | Does not show the horizon, only the -45 dec line.|
| `diagnostic-circumpolar-horizon` | [+] | [-] | [-] | [+] | [+] | [+] | Too many clusters, PNs, and SNRs. Grid lines shoukld be of a subtler grey. The declination labels should be next to the drawn RA line closer to the upper meridian, and they should be above to the Dec line, and to the left of the meridian.|
| `diagnostic-planisphere-horizon-noop` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Same comments as per planisphere |
| `diagnostic-legends-references-grids` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Same comment as previous regional.|

The appendix may be committed with every box empty. Completing it is the
human visual-approval record and may be committed separately after review.

## Approval record

Complete this section only after the Mac run:

- source commit:
- fast suite:
- integration suite:
- visual suite:
- full suite:
- atlas-print products approved:
- cartoon-presentation products approved:
- diagnostic products approved:
- unexplained golden-baseline changes:
- reviewer and date:
