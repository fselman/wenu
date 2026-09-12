# Regional charts

The [complete chart examples](chart_examples.md) include a runnable
installed-command example for this family.

Regional charts use a tangent-plane view around one constellation or an
arbitrary constellation set. The chart owns projection and framing; the
examples only select the requested region and content.

## Constellation group

The default set is Sagittarius, Scorpius, Ophiuchus, and Serpens. Supply any
comma-separated set of three-letter IAU abbreviations; Wenu validates and
frames the complete set automatically.

```bash
python examples/regional_constellation_group.py \
  --center-on constellation:Sgr,Sco,Oph,Ser \
  --style atlas --mode print \
  --output output/galactic-centre.png
```

Use `--constellation-mask IAU,...` to dim the area outside the union of the selected IAU
constellation regions. The mask does not require visible boundary lines.

```bash
python examples/regional_constellation_group.py \
  --center-on constellation:Cen,Cru,Mus \
  --constellation-mask Cen,Cru,Mus \
  --style cartoon --mode presentation \
  --output output/centaurus-crux-musca.png
```

Packaged teaching presets are selected only as centers, for example
`--center-on group:summer-triangle`. They do not request constellation lines,
labels, boundaries, masks, or deep-sky objects.

## Single constellation

Constellations use their three-letter IAU abbreviation. This Crux example
also requests the canonical outside mask:

```bash
python examples/regional_constellation.py \
  --center-on constellation:Cru \
  --constellation-mask Cru \
  --style atlas --mode print \
  --output output/crux.png
```

Both regional examples use the same `--center-on IDENTIFIER` control. A
qualified `constellation:IAU,...` or `group:ALIAS` center derives its default
viewport from the complete selected constellation geometry. Explicit `--field-width` and
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
wenu_chart regional \
  --center-altitude 20deg --center-azimuth 270deg \
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

A regional field may instead be centered on any packaged target, including a
star, cluster, nebula, or galaxy, or on an explicit ICRS coordinate:

```bash
wenu_chart regional --center-on star:Sirius \
  --field-width 20 --field-height 15 \
  --constellation-lines CMa --constellation-labels CMa \
  --output output/sirius-field.png

wenu_chart regional --center-icrs-ra 201.365deg \
  --center-icrs-dec=-43.019deg --center-name "My field" \
  --field-width 20 --field-height 15 \
  --output output/coordinate-field.png
```

Moving objects never become the center merely because they are selected for
drawing. Use `--center-on planet:Venus`, `--center-on moon:Moon`, or
`--center-on asteroid:79989` to request an apparent center at
`--observer-time`, and independently use `--planet`, `--moon`, or
`--asteroid` to draw an object. Supply `--field-width` and `--field-height`
for every point center. One or several selected moving objects therefore have
exactly the same unambiguous behavior.
For an observer-time sequence an explicit moving-object center remains fixed
at the first chart epoch; Wenu does not silently introduce a moving camera.

Wenu also resolves the pointwise parallactic angle and the tangent directions
of celestial north and the local vertical at the chart centre. This milestone
retains that backend-neutral geometry for later furniture; it draws no
parallactic or meridian line.
