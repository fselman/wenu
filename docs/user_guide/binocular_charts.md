# Binocular charts

`examples/binocular_object.py` centers a north-up circular binocular field on
a selected packaged catalogue object. Centaurus A (`NGC 5128`) and Omega
Centauri (`NGC 5139`) are the documented regression targets, but `--target`
accepts any drawable name or alias in Wenu's packaged resolver, such as `M57`.

```bash
python examples/binocular_object.py \
  --target centaurus-a \
  --style atlas --mode print \
  --output output/centaurus-a.png
```

Select Omega Centauri and change the field diameter:

```bash
python examples/binocular_object.py \
  --target omega-centauri --field-diameter 8.0 \
  --style cartoon --mode presentation \
  --magnitude-legend --credits \
  --output output/omega-centauri.png
```

The canonical binocular field uses a stellar limit of magnitude 11 unless
`--magnitude-limit` overrides it. Stellar symbol areas are normalized to the
resolved limiting magnitude: the faintest symbol uses the configured minimum,
brighter stars grow according to the configured exponent, and the configured
maximum bounds the brightest symbols. The magnitude legend uses exactly the
same sizing law and is placed outside the circular aperture.

The chart owns its aperture, clipping, rim, and transparent exterior. The
example is a pure `ChartRequest`: it does not load catalogues, construct grids,
create Matplotlib figures, clip artists, or implement export itself.
