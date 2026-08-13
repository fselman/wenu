# Circumpolar charts

`examples/circumpolar.py` renders the southern sky down to declination
−69.75°, a boundary chosen to cross the Large Magellanic Cloud. The chart owns
its declination boundary, circular clipping, and framing.

```bash
python examples/circumpolar.py \
  --style atlas --mode print \
  --output output/circumpolar-atlas-print.png
```

The default limiting declination remains −69.75°. Use
`--limiting-declination` when a wider polar field is required. For example, a
southern field extending to −30° crosses the La Ligua horizon and can display
both optional horizon roles:

```bash
python examples/circumpolar.py \
  --limiting-declination -30 --horizon --horizon-mask \
  --style atlas --mode print \
  --output output/circumpolar-horizon-crossing.png
```

Generate all four products with:

```bash
python examples/circumpolar.py \
  --all-products --output output/circumpolar
```

Atlas products show the detailed stellar field and shaded Magellanic Cloud
isophotes. When selected by the cartoon detail policy, the Milky Way and
Magellanic Clouds use unshaded dotted contours: black in print and yellow in
presentation. The exported area outside the circular boundary is transparent.

The common switches control stellar depth, constellation content, celestial
references, legends, counts, and credits without changing polar geometry.
