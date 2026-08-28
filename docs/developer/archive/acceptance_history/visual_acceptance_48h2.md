# Milestone 48H.2 polar binocular-content acceptance

## Scope

This checkpoint reviews the curated binocular objects added to the existing
paired polar disks. It does not change stars, constellation geometry,
projection, calendar geometry, disk dimensions, page furniture, or pouch
geometry.

## Deterministic review

From a clean repository after applying the Milestone 48H.2 patch, run:

```bash
python tools/render_48e4_polar_pages.py \
  --source-revision "$(git rev-parse --short HEAD)" \
  --output output/48h2-polar-binocular
```

Print or inspect both PDFs at actual size.

## Acceptance checks

- Both faces use the same pre-projection curated identifier selection.
- No face contains more than 15 selected binocular targets, including the
  Magellanic Clouds on the south face.
- Messier objects use `M` labels; other catalogue fallbacks abbreviate NGC as
  `N` and IC as `I`.
- Recognizable common names replace Melotte designations where available.
- IC 2602 is labelled `Pléyades S`; NGC 3532 retains the neutral `N3532`
  designation rather than a translated nickname.
- M81/M82 and the Double Cluster retain both symbols but use one label each.
- NGC 224 is labelled M31 and NGC 598 is labelled M33; no M31 companion is
  included in the curated selection.
- Omega Centauri is labelled only with the Greek letter omega.
- M27 is present as the selected planetary nebula.
- Outline-based deep-sky symbols remain visible at actual print size through
  the polar-only configurable minimum diameter; globular-cluster circles use
  twice the ordinary minimum diameter.
- Deep-sky label baselines are perpendicular to the radius, with typographic
  down facing the disk center, and remain readable around the disk.
- Labels remain subordinate to constellation names and stellar structure.
- No unselected deep-sky catalogue members appear.
- Ordinary atlas, cartoon, regional, all-sky, circumpolar, and binocular
  products remain unchanged.

Carina and the Coalsack are intentionally absent because the current Wenu
catalogues do not yet provide the required canonical object-class provenance.

## Current disposition

Code and automated contracts are ready for a new actual-size paper review.
Final visual acceptance remains with Fernando Selman.
