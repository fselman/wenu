# Milestone 46D.8 visual acceptance

**Status:** Reviewed on Mac; 46D.8F–G remediation pending rerender

**Matrix source:** `tools/render_46d8_visual_matrix.py`

**Reviewed source commit:** `84baedb`

**Review record commit:** `a6739a7`

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
  --entry diagnostic-regional-explicit-field-mask \
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
| all-sky constellation mask | three disjoint regions and one effective translucent outside mask |
| regional explicit field and mask | explicit width, height, angle, and combined Oph/Ser mask |
| binocular field | aperture, target content, stellar sizing, and family furniture |
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

## Remediation register

The `84baedb` review identified shared policy defects rather than independent
example defects. Examples remain request-only; fixes belong to packaged
configuration and the existing family, detail, style, mask, and furniture
owners.

| ID | Finding | Classification | Owner | Planned slice |
| --- | --- | --- | --- | --- |
| GRID-1 | Equatorial lines are too dark and prominent. | confirmed common style policy | packaged atlas/cartoon grid style | 46D.8F |
| GRID-2 | Regional selection can produce fewer than two useful RA and Dec lines; circumpolar RA spacing is not two hours. | confirmed family grid policy | request-time grid configuration | 46D.8F |
| GRID-3 | Coordinate labels are too large or collide with their line; RA and Dec formatting and anchor meridians are inconsistent. | confirmed shared label policy | semantic grid formatter and placement | 46D.8F |
| GRID-4 | Galactic all-sky parallels use unintended latitudes and principal longitude labels crowd the outer ellipse. | confirmed all-sky grid policy | request-time Galactic grid and elliptical label anchor | 46D.8F.2 |
| DETAIL-1 | Atlas all-sky, planisphere, regional-group, and circumpolar products contain too many open clusters, planetary nebulae, and remnants. | confirmed family density policy | immutable detail policy | 46D.8G |
| CARTOON-1 | Cartoon products omit the Milky Way, Magellanic Clouds, and a restrained bright deep-sky selection. | confirmed product content policy | cartoon detail/content policy | 46D.8G |
| MASK-1 | The cartoon regional outside mask is too weak. | confirmed style policy | packaged cartoon mask style | 46D.8H–H.2 |
| LABEL-1 | Centered regional declination labels are clipped at the left boundary, hiding the minus sign in values such as `-15:00`. | confirmed rectangular anchor policy | shared coordinate-label anchor | 46D.8F.1 |
| MASK-2 | The combined all-sky mask correctly leaves visible only selected constellation regions above the horizon; UMa is present but masked below the horizon. Isolated products are still needed to judge each mask independently. | valid intersection behavior; ambiguous opacity diagnostic | visual matrix | 46D.8E and final closure |
| HORIZON-1 | Regional and Centaurus A binocular fields did not contain a demonstrated horizon crossing. | invalid diagnostic geometry, not yet a renderer defect | visual matrix | 46D.8E |
| BINOCULAR-1 | Binocular defaults should omit grids and provide target marker, center, and field diameter. | confirmed family/furniture policy | binocular request and context furniture | 46D.8I |
| BINOCULAR-2 | Stellar symbols appear nearly equal in size. | diagnosis required before changing behavior | binocular stellar sizing | 46D.8I |

Milestone 46D.8E separates the combined claims in the next matrix so that
each mask can be judged independently:
constellation masks are reviewed independently, the binocular diagnostic is
a field/furniture product, and the circumpolar product retains the explicit
horizon-crossing role. No production rendering behavior changes in 46D.8E.

Milestone 46D.8F centralizes the first appearance remediation. Atlas and
cartoon coordinate grids receive subtler shared line weights and opacity;
atlas-print equatorial lines use blue-grey. Coordinate-label bases are reduced
before mode scaling, equatorial labels use `hh:mm` and signed `dd:mm`, latitude
labels receive clearance above their lines, and all-sky latitude labels use
one central longitude. The all-sky grid includes its zero latitude and labels
only principal longitudes. Regional fields through 60 degrees use 15-degree
spacing, while circumpolar RA uses two-hour spacing. Examples remain unchanged.

Milestone 46D.8G routes named atlas products through the packaged adaptive
policy for their chart family, so command and example products share the same
DSO limits. Cartoon products add the Milky Way, Magellanic Clouds, galaxies
through magnitude 8, and only open clusters at least 60 arcmin and globular
clusters at least 30 arcmin. Planetary nebulae and remnants remain absent from
the restrained cartoon baseline. The matrix must be rerendered before either
detail finding is accepted.

Milestone 46D.8H strengthens the packaged cartoon outside mask from opacity
`0.25` to `0.68`. Its pale-grey color and z-order are unchanged, and no mask
geometry, opening intersection, or rendering-path behavior changes. The matrix
must be rerendered before `MASK-1` is accepted.

Milestone 46D.8H.1 removes the cartoon-mode sky-color substitution discovered
by rendering an opaque white user overlay. Cartoon presentation now preserves
the configured mask color and opacity. `MASK-1` remains pending until a local
overlay selects the final packaged values and the matrix is rerendered.

Milestone 46D.8H.2 promotes the locally selected warm-white `#fffdf5` mask at
opacity `0.45` and z-order `20.0` to the packaged cartoon authority. The
regional product and complete matrix must be rerendered before `MASK-1` is
accepted.

Milestone 46D.8F.1 routes regional coordinate-grid labels through the shared
rectangular anchor. Declination labels are left-aligned at the `0.01` viewport
inset and bottom-edge right-ascension labels are bottom-aligned there, so
larger type grows inward rather than crossing the chart boundary. The existing
above-line declination clearance remains unchanged. The regional product and
complete matrix must be rerendered before `LABEL-1` is accepted.

Milestone 46D.8F.2 draws Galactic all-sky parallels at `-60`, `-30`, `0`,
`30`, and `60` degrees and meridians every 45 degrees. It labels only `0`,
`90`, `180`, and `270` degrees immediately below the Galactic equator and to
the right of the corresponding meridian. The 180-degree label uses the left
seam so the label grows into the ellipse. Candidate segments whose equatorial
crossing does not match the named longitude's expected Mollweide position are
not labeled, suppressing false `90`-degree center and `180`-degree right-seam
duplicates. The all-sky products and complete matrix must be rerendered before
`GRID-4` is accepted.

Milestone 46D.8I removes the implicit equatorial grid from binocular products,
adds a render-local `+` at the resolved target, and includes the ICRS center
and field diameter in the title. The stellar renderer was already applying its
configured law correctly; the binocular-only exponent changes from `0.20` to
`0.35` so stars between magnitudes 8 and 11 have a clearer area progression.
The canonical and diagnostic binocular products must be rerendered before
`BINOCULAR-1` and `BINOCULAR-2` are accepted.

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
| `canonical-regional-group-cartoon-presentation` | [+] | [+] | [-] | [-] | [+] | [ ] | I would add MW contours, and a few of the brighter clusters. Dec labels should be raised above Dec line. Masked region barely noticeable. It should look much whiter and more opaque. |
| `canonical-circumpolar-atlas-print` | [+] | [+] | [-] | [+] | [+] | [+] | Grid should be of a subtler grey. The RA spacing should be every 2h.|
| `canonical-circumpolar-cartoon-presentation` | [+] | [+] | [-] | [+] | [+] | [+] | The RA spacing should be every 2h. |
| `canonical-binocular-atlas-print` | [+] | [+] | [-] | [+] | [+] | [-] | All stars look the same size (perhaps they should). There should not be a grid. Needs field center and diameter in the title.|
| `canonical-binocular-cartoon-presentation` | [+] | [-] | [-] | [+] | [+] | [-] | Needs the symbol for the target. There should not be a grid. Needs field center and diameter in the title. |
| `diagnostic-all-sky-constellation-mask` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Rerender required after removing the independent horizon opening. The prior combined product showed Cru and Cyg but did not independently prove UMa. |
| `diagnostic-regional-explicit-field-mask` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Rerender required after removing the unproven horizon claim. Prior review found excessive clusters/PNs, prominent grid, low Dec-label clearance, and too little context outside the selected constellations. |
| `diagnostic-binocular-field` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Rerender required as a field/furniture diagnostic. The prior Centaurus A field did not cross the horizon, so it supplied no horizon evidence. |
| `diagnostic-circumpolar-horizon` | [+] | [-] | [-] | [+] | [+] | [+] | Too many clusters, PNs, and SNRs. Grid lines shoukld be of a subtler grey. The declination labels should be next to the drawn RA line closer to the upper meridian, and they should be above to the Dec line, and to the left of the meridian.|
| `diagnostic-planisphere-horizon-noop` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Same comments as per planisphere |
| `diagnostic-legends-references-grids` | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | Same comment as previous regional.|

The original observations remain the baseline evidence. Renamed diagnostics
are deliberately reset because their command contracts changed and require a
new render.

## Approval record

Complete this section only after remediation and the final Mac rerun:

- source commit:
- fast suite:
- integration suite:
- visual suite:
- full suite:
- atlas-print products approved:
- cartoon-presentation products approved:
- diagnostic products approved:
- unexplained golden-baseline changes:
- reviewer and date: Fernando Selman, 2026-08-14 (initial review)
