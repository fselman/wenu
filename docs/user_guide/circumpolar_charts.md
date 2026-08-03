# Circumpolar charts

`examples/circumpolar.py` renders the southern sky down to declination
−69.75°, a boundary chosen to cross the Large Magellanic Cloud. The chart owns
its declination boundary, circular clipping, and framing.

```bash
python examples/circumpolar.py \
  --style atlas --mode print \
  --output output/circumpolar-atlas-print.png
```

Generate all four products with:

```bash
python examples/circumpolar.py \
  --all --output output/circumpolar
```

Atlas products show the detailed stellar field and shaded Magellanic Cloud
isophotes. When selected by the cartoon detail policy, the Milky Way and
Magellanic Clouds use unshaded dotted contours: black in print and yellow in
presentation. The exported area outside the circular boundary is transparent.

The common switches control stellar depth, constellation content, celestial
references, legends, counts, and credits without changing polar geometry.
