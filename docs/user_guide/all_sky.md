# Galactic Mollweide all-sky map

`examples/all_sky.py` draws the complete celestial sphere in Galactic
longitude and latitude. The example requests `family="all_sky"`,
`projection="mollweide"`, and `coordinate_frame="galactic"`; it does not
implement transformation, seam splitting, clipping, rendering, or export.

Generate the atlas print map:

```bash
python examples/all_sky.py \
  --style atlas --mode print \
  --output output/all-sky-atlas-print.png
```

The chart centers Galactic longitude zero and places the 180° seam at the
outer left and right tips of the 2:1 Mollweide ellipse. Longitude and latitude
are sampled every 30° by default. The labeled Galactic grid is the ordinary
default for this family; explicitly requested equatorial and ecliptic grids
are transformed overlays using the same spherical-geometry pipeline.
The zero-latitude parallel is included. Latitude labels are placed along the
central longitude, and only the principal 0°, 90°, 180°, and 270° longitudes
are labeled, keeping the complete-sphere view readable.
Because the 2:1 map is physically half as tall as the circular charts at the
same output width, its built-in styles halve stellar marker diameters. The
magnitude legend uses the same adjusted scale.

For example, add the labeled equatorial grid:

```bash
python examples/all_sky.py \
  --galactic-grid-labels --equatorial-grid-labels \
  --style atlas --mode print \
  --output output/all-sky-equatorial-overlay.png
```

An arbitrary adjacent or disjoint constellation set can define mask openings
without observer-horizon rejection:

```bash
python examples/all_sky.py \
  --constellations Cru,Cyg,UMa --mask \
  --style atlas --mode print \
  --output output/all-sky-regions.png
```

Every selected official region remains a separate opening. Regions crossing
the 180° seam are split by the projection and clipped at the chart ellipse.
Packaged aliases remain available through `--group ALIAS`.

Use `--all-products` for the four atlas/cartoon and print/presentation
products. The common magnitude, constellation, reference, pole, legend,
context, and credit controls are described in
[Styles, modes, detail, and furniture](styles_modes_detail.md).
