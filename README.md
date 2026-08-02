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
release. The v0.5 chart architecture is implemented. It provides one
composition and export workflow across chart types, styles, output modes,
detail policies, and legends. Public APIs may still change before release.

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
- atlas and cartoon chart styles;
- print/paper and presentation output modes;
- render-local fixed, adaptive, and cartoon detail policies;
- integrated object, stellar-magnitude, and contextual legends;
- regional, full-sky, circumpolar, and binocular chart types;
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

## Canonical chart composition

```python
import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere,
    FixedDetailPolicy,
    LegendOptions,
    MatplotlibRenderer,
    Observer,
    RegionalChart,
    ResolvedDetail,
    compose_chart,
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
figure, ax = plt.subplots(figsize=chart.figure_size(7.0))
composition = compose_chart(
    chart,
    style="atlas",
    mode="print",
    detail=FixedDetailPolicy(
        ResolvedDetail(star_magnitude_limit=5.5)
    ),
    legends=LegendOptions(
        objects=True,
        stellar_magnitudes=True,
        context=True,
    ),
)
chart.export(
    sky,
    MatplotlibRenderer(ax),
    "regional.png",
    composition=composition,
)
```

Change the independent choices without changing chart geometry:

```python
atlas_slides = compose_chart(
    chart, style="atlas", mode="presentation"
)
cartoon_print = compose_chart(
    chart, style="cartoon", mode="print"
)
```

The same workflow supports `RegionalChart`, `FullSkyChart`,
`CircumpolarChart`, and `BinocularChart`. `FullSkyChart` may place its
stereographic tangent point independently of the observer zenith; the observer
continues to determine the AltAz sky and horizon.

See:

- `examples/atlas_style.py`;
- `examples/atlas_summer_triangle.py`;
- `examples/circumpolar_atlas.py`;
- `examples/la_ligua_planisphere.py`;
- `examples/cartoon_modes.py`.

## Architecture

The canonical pipeline is:

```text
Observer
  → CelestialSphere and SkyLayer
  → spherical geometry
  → projection-domain guard
  → projection
  → projected geometry
  → chart preparation
  → renderer
  → legends and export
```

The principal packages are:

- `wenu.objects`: physical astronomical catalogue objects;
- `wenu.sky`: sky layers and canonical orchestration;
- `wenu.geometry`: coordinate-neutral values and algorithms;
- `wenu.projections`: map projections;
- `wenu.charts`: chart specifications and styles;
- `wenu.rendering`: preparation and graphical backends.

Developer references:

- `docs/developer/current_architecture_v0.4.md` (migration baseline);
- `docs/developer/implementation_reference.md`;
- `docs/developer/target_architecture_v0.5.md` (implemented architecture);
- `docs/developer/wenu_migration_0.4_to_0.5.md` (completed roadmap);
- `docs/developer/deprecations_v0.5.md`.

## Tests

```bash
pytest
python examples/atlas_style.py
python examples/cartoon_modes.py
```

Generated chart-output directories should remain outside version control.

## Data attribution

Astronomical catalogue and dataset attribution is documented in
`DATA_ATTRIBUTION.md`.

## Acknowledgements

Wenu builds on Astropy, Matplotlib, NumPy, Pandas, and public astronomical
catalogues.
