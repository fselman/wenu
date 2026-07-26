# Wenu

**Language:** English | [Español](README.es.md)

Wenu is a Python library for producing accurate, reproducible,
publication-quality static charts of the sky. It supports regional charts and
observer-dependent full-sky charts through one geometry pipeline.

Wenu is intended for observing guides, books, articles, education, public
outreach, and guided observation. It is not an interactive planetarium.

*Wenu* means **sky** in Mapudungun, the language of the Mapuche people of
southern South America.

## Project status

Wenu remains under active development and has not yet reached its first public
release. The v0.4 chart architecture is implemented. Public APIs may still
change before release.

See `LICENSE` for the current usage terms.

## Implemented features

- observer-dependent sky calculations;
- coordinate-neutral spherical and projected geometry;
- arbitrary tangent-point stereographic projection;
- regional chart production API;
- full-sky chart production API with independent horizon and tangent point;
- Hipparcos stellar catalogue;
- Western and alternative constellation-line systems;
- IAU constellation boundaries assembled in B1875;
- equatorial, ecliptic, and Galactic grids;
- celestial reference points;
- publication styles and reproducible export;
- generic preparation and Matplotlib rendering;
- package-boundary and regression tests.

## Installation

```bash
git clone https://github.com/fselman/wenu.git
cd wenu
pip install -e .
```

Wenu requires Python 3.10 or newer. Runtime dependencies are declared in
`pyproject.toml`: Astropy, Matplotlib, NumPy, and Pandas.

## Regional chart

```python
import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere,
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
    RegionalChart,
)

observer = Observer(
    location="La Ligua",
    time="2026-08-15 21:00",
)
sky = CelestialSphere(observer)
sky.add_stars(catalog="hipparcos", magnitude_limit=5.5)
sky.add_constellations(
    system="western",
    selected=("Cru", "Cen"),
)

chart = RegionalChart.from_constellations(
    sky,
    ("Cru", "Cen"),
    angular_radius_deg=35.0,
    north_up=True,
)
style = PublicationStyle()
figure, ax = plt.subplots(figsize=chart.figure_size(7.0))
style.configure_axes(ax, title="Crux and Centaurus")
chart.render(
    sky,
    MatplotlibRenderer(ax),
    style=style,
)
figure.savefig("regional.png", dpi=300)
```

## Full-sky chart

```python
import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere,
    ExportOptions,
    FullSkyChart,
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
)

observer = Observer(
    location="La Ligua",
    time="2026-08-15 21:00",
)
sky = CelestialSphere(observer)
sky.add_stars(catalog="hipparcos", magnitude_limit=5.5)
sky.add_constellations(system="western")

chart = FullSkyChart()
style = PublicationStyle(star_area_scale=0.25)
figure, ax = plt.subplots(figsize=chart.figure_size(7.0))
style.configure_axes(ax, title="Visible sky")
chart.export(
    sky,
    MatplotlibRenderer(ax),
    "full-sky.png",
    style=style,
    export_options=ExportOptions(dpi=300),
)
```

`FullSkyChart` may place its stereographic tangent point independently of the
observer zenith. The observer continues to determine the AltAz sky and
horizon.

See:

- `examples/full_sky_chart.py`;
- `examples/milestone16_regional_charts.py`.

## Architecture

The canonical pipeline is:

```text
Observer
  → CelestialSphere and SkyLayer
  → spherical geometry
  → projection
  → projected geometry
  → optional preparation
  → renderer
```

The principal packages are:

- `wenu.objects`: physical astronomical catalogue objects;
- `wenu.sky`: sky layers and canonical orchestration;
- `wenu.geometry`: coordinate-neutral values and algorithms;
- `wenu.projections`: map projections;
- `wenu.charts`: chart specifications and styles;
- `wenu.rendering`: preparation and graphical backends.

Developer references:

- `docs/developer/current_architecture.md`;
- `docs/developer/implementation_reference.md`;
- `docs/developer/target_architecture_v0.4.md`;
- `docs/developer/wenu_migration_roadmap_v0.4.md`.

## Tests

```bash
pytest
python examples/full_sky_chart.py
python examples/milestone16_regional_charts.py
```

Generated chart-output directories should remain outside version control.

## Data attribution

Astronomical catalogue and dataset attribution is documented in
`DATA_ATTRIBUTION.md`.

## Acknowledgements

Wenu builds on Astropy, Matplotlib, NumPy, Pandas, and public astronomical
catalogues.
