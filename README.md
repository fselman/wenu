# Wenu

**Language:** English | [Español](README.es.md)

---

# Wenu

**Wenu** is an open-source Python library for creating beautiful, accurate, and customizable astronomical charts.

It was developed to support astronomy communication through education, public outreach, publishing, and guided observation of the night sky. Typical applications include observing guides, planispheres, educational material, books, articles, presentations, and astronomy courses.

Unlike interactive planetarium software, Wenu focuses on creating static charts whose appearance can be completely controlled and reproduced.

*Wenu* means **sky** in Mapudungun, the language of the Mapuche people of southern South America.

---

## Features

The current version supports

- observer-dependent sky calculations
- stereographic sky projections
- full-sky and regional charts
- Hipparcos stellar catalogue
- constellation lines
- IAU constellation boundaries
- equatorial, ecliptic, and Galactic coordinate grids
- celestial reference points
- customizable drawing styles
- layered chart composition
- Matplotlib rendering

---

## Design Philosophy

Wenu is built around three simple ideas.

- **The sky comes first.** Astronomical calculations should be independent of how the sky is displayed.

- **Charts should be publication quality.** Every element of a chart should contribute to clear and effective communication.

- **Reproducibility matters.** The same script should always produce the same chart.

This design makes it possible to create anything from a simple planisphere to detailed charts of individual constellations while maintaining a consistent programming interface.

---

## Architecture

The package is organized into a small number of core components.

### Observer

Represents the observing site and time and performs observer-dependent astronomical calculations.

### CelestialSphere

Represents the sky to be drawn. It manages stars, constellations, coordinate grids, boundaries, and other celestial structures.

### Projection

Projection classes transform celestial coordinates into planar coordinates suitable for plotting.

The current implementation provides a stereographic projection suitable for both planispheres and regional charts.

### Rendering

Rendering is performed using Matplotlib, allowing charts to be exported in publication-quality formats.

---

## Installation

Clone the repository

```bash
git clone https://github.com/<username>/wenu.git
```

Install the package

```bash
pip install -e .
```

---

## Dependencies

Wenu currently depends on

- Astropy
- Skyfield
- Matplotlib
- NumPy
- Pandas

---

## Project Status

Wenu is currently under active development.

The architecture is stabilizing, but the public API should still be considered subject to change until the first official release.

---

## Roadmap

Planned future developments include

- additional map projections
- stellar colours
- Milky Way isophotes
- deep-sky object catalogues
- additional rendering options
- automated tests
- expanded documentation

---

## Documentation

Additional documentation is available in the `docs/` directory.

---

## Data Attribution

Information about the astronomical catalogues and external datasets used by Wenu is provided in `DATA_ATTRIBUTION.md`.

---

## License

The license will be specified before the first public release.

---

## Acknowledgements

Wenu builds upon the outstanding work of the astronomical open-source community, particularly the developers of Astropy, Skyfield, and Matplotlib, together with publicly available astronomical catalogues.


