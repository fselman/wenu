# Chart examples

Wenu has five ordinary chart families. The six installed Python examples use
the same public request and export path; regional charts have two examples
because a single constellation and a constellation group are common teaching
tasks.

Run these commands from the repository root after `pip install -e .`.
Generated products belong below `output/`.

## Galactic all-sky map

```bash
wenu_chart all-sky \
  --style atlas --mode print --format svg \
  --galactic-grid-labels \
  --output output/all-sky.svg
```

Canonical script: `python examples/all_sky.py ...`  
Detailed guide: [Galactic Mollweide all-sky map](all_sky.md)

## Visible-sky planisphere

```bash
wenu_chart planisphere \
  --observer-location "La Ligua" \
  --observer-time "2026-08-15T21:00:00-04:00" \
  --style cartoon --mode presentation --format png \
  --credits \
  --output output/la-ligua-planisphere.png
```

Canonical script: `python examples/planisphere.py ...`  
Detailed guide: [Planisphere](planisphere.md)

## Regional chart

A single official constellation:

```bash
wenu_chart regional \
  --observer-location "La Ligua" \
  --observer-time "2026-08-15T21:00:00-04:00" \
  --constellations Cru --mask \
  --style atlas --mode print --format pdf \
  --output output/crux.pdf
```

A teaching group:

```bash
wenu_chart regional \
  --observer-location "La Ligua" \
  --observer-time "2026-08-15T21:00:00-04:00" \
  --constellations Sgr,Sco,Oph,Ser \
  --style cartoon --mode presentation --format png \
  --output output/galactic-centre.png
```

Canonical scripts: `python examples/regional_constellation.py ...` and
`python examples/regional_constellation_group.py ...`  
Detailed guide: [Regional charts](regional_charts.md)

## Circumpolar chart

```bash
wenu_chart circumpolar \
  --observer-location "La Ligua" \
  --observer-time "2026-08-15T21:00:00-04:00" \
  --pole south --limiting-declination -60 \
  --style atlas --mode print --format svg \
  --output output/circumpolar-south.svg
```

Canonical script: `python examples/circumpolar.py ...`  
Detailed guide: [Circumpolar charts](circumpolar_charts.md)

## Binocular chart

```bash
wenu_chart binocular \
  --observer-location "La Ligua" \
  --observer-time "2026-08-15T21:00:00-04:00" \
  --target omega-centauri --field-diameter 7.5 \
  --magnitude-limit 11 \
  --style atlas --mode print --format png \
  --output output/omega-centauri-binocular.png
```

Canonical script: `python examples/binocular_object.py ...`  
Detailed guide: [Binocular charts](binocular_charts.md)

## Add Solar-System objects

The same chart requests may add apparent planets and the resolved Moon:

```bash
wenu_chart regional \
  --observer-location "La Ligua" \
  --observer-time "2026-09-16T12:00:00Z" \
  --constellations Sgr,Sco,Oph \
  --planet venus,mars,jupiter,saturn \
  --moon --moon-disk-magnification 8 \
  --style atlas --mode presentation --format svg \
  --output output/regional-solar-system.svg
```

The magnification changes only the drawn lunar size. It does not change the
Moon's calculated position, distance, physical diameter, phase, or
illumination. See [configuration and Solar-System controls](configuration.md)
for symbolic compatibility and observed Moon sequences.

## Shared controls

All families share style, mode, output-format, detail, content, coordinate
reference, legend, and credit controls. See
[Styles, modes, detail, and furniture](styles_modes_detail.md) and
[SVG output and editing](svg_output.md).
