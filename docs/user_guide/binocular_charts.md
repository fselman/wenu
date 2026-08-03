# Binocular charts

`examples/binocular_object.py` centers a north-up circular binocular field on
a selected catalogue object. The documented targets are Centaurus A
(`NGC 5128`) and Omega Centauri (`NGC 5139`).

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
example does not create Matplotlib circles or clip artists itself.
