# Regional charts

Regional charts use a tangent-plane view around one constellation or a named
constellation group. The chart owns projection and framing; the examples only
select the requested region and content.

## Constellation group

The default group is the Summer Triangle. The other canonical group is the
Galactic-centre region.

```bash
python examples/regional_constellation_group.py \
  --group summer-triangle \
  --style atlas --mode print \
  --output output/summer-triangle.png
```

Use `--mask` to dim the area outside the union of the selected IAU
constellation regions. The mask does not require visible boundary lines.

```bash
python examples/regional_constellation_group.py \
  --group galactic-center --mask \
  --style cartoon --mode presentation \
  --output output/galactic-center.png
```

## Single constellation

Constellations use their three-letter IAU abbreviation. This Crux example
also requests the canonical outside mask:

```bash
python examples/regional_constellation.py \
  --constellation Cru --mask \
  --style atlas --mode print \
  --output output/crux.png
```

Both regional examples support the common magnitude, labels, boundaries,
references, poles, visual overrides, legends, counts, and credits described
in [Styles, modes, detail, and furniture](styles_modes_detail.md).
