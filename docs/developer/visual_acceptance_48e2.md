# Milestone 48E.2 polar appearance review

Milestone 48E.2 is a visual checkpoint, not only a style-contract change. Run
the deterministic diagnostic after applying the patch and passing tests:

```bash
python tools/render_48e2_polar_preview.py
```

It writes these untracked artifacts below `output/48e2-polar-preview/`:

- `polar-planisphere-south.png`;
- `polar-planisphere-north.png`;
- `manifest.json` with projection, byte counts, and SHA-256 checksums.

The runner uses the canonical generated celestial sphere, ordinary atlas-print
composition, paired polar chart, and resolved calendar furniture. It fixes the
observer to La Ligua at 2026-08-15 21:00 only because the existing maximal
sphere enters canonical equatorial preparation through an observer; stellar
and constellation disk geometry remains equatorial and the physical content
policy is observer-independent.

Review both PNGs together and record only concrete defects:

- white paper and provisional blue stars are clean in print;
- star sizes remain legible through magnitude 5 without dominating figures;
- Milky Way regions are visibly filled but have no contour or edge outlines;
- constellation figures and labels remain subordinate yet readable;
- north and south share the same appearance and reverse only required disk
  handedness;
- the calendar ring is readable and remains outside the star aperture;
- no astronomical content is clipped by the star-aperture boundary;
- no element crosses the physical disk edge.

Typography, translation, reference curves, exact A4 placement, and assembly
marks are intentionally not acceptance criteria for this checkpoint. Use
`--projection stereographic` only as a comparison; the canonical classroom
preview remains polar azimuthal equidistant.
