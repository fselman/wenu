# Regional charts

Regional charts use a tangent-plane view around one constellation or an
arbitrary constellation set. The chart owns projection and framing; the
examples only select the requested region and content.

## Constellation group

The default set is Sagittarius, Scorpius, Ophiuchus, and Serpens. Supply any
comma-separated set of three-letter IAU abbreviations; Wenu validates and
frames the complete set automatically.

```bash
python examples/regional_constellation_group.py \
  --constellations Sgr,Sco,Oph,Ser \
  --style atlas --mode print \
  --output output/galactic-centre.png
```

Use `--mask` to dim the area outside the union of the selected IAU
constellation regions. The mask does not require visible boundary lines.

```bash
python examples/regional_constellation_group.py \
  --constellations Cen,Cru,Mus --mask \
  --style cartoon --mode presentation \
  --output output/centaurus-crux-musca.png
```

Packaged teaching presets remain available through `--group`, for example
`--group summer-triangle`.

## Single constellation

Constellations use their three-letter IAU abbreviation. This Crux example
also requests the canonical outside mask:

```bash
python examples/regional_constellation.py \
  --constellations Cru --mask \
  --style atlas --mode print \
  --output output/crux.png
```

Both regional examples use the same `--constellations IAU,...` and optional
`--group ALIAS` subject controls. Both derive their default viewport from the
complete selected constellation geometry. Explicit `--field-width` and
`--field-height` values override that automatic framing when a wider or fixed
field is wanted. They also support the common magnitude,
labels, boundaries,
references, poles, visual overrides, legends, counts, and credits described
in [Styles, modes, detail, and furniture](styles_modes_detail.md).

## Camera centre and orientation

Content selection and camera framing are independent. A regional chart may
retain constellation-derived centring, or use an explicit observer-local
centre together with an explicit rectangular field:

```bash
wenu_chart regional --constellations Vir \
  --center-altitude 20 --center-azimuth 270 \
  --field-width 60 --field-height 50 \
  --orientation zenith-up \
  --output output/virgo-western-horizon.png
```

`--center-altitude` and `--center-azimuth` must be supplied together and
require both field dimensions. `--orientation celestial-north-up` and
`--orientation zenith-up` are named geometrical policies. Alternatively,
`--position-angle DEGREES` supplies a literal rotation; zero is an ordinary
angle and has no hidden meaning. Named orientation and literal position angle
are mutually exclusive.

Wenu also resolves the pointwise parallactic angle and the tangent directions
of celestial north and the local vertical at the chart centre. This milestone
retains that backend-neutral geometry for later furniture; it draws no
parallactic or meridian line.
