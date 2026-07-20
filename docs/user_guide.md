# Wenu User Guide

## Introduction

Welcome to Wenu.

This guide introduces the basic concepts needed to create astronomical charts with Wenu. It is intended for educators, amateur astronomers, science communicators, and anyone interested in producing publication-quality charts of the night sky.

The software is under active development, so this guide will grow together with the project.

---

# Installation

Clone the repository

```bash
git clone https://github.com/<username>/wenu.git
```

Install Wenu

```bash
pip install -e .
```

---

# The Basic Workflow

Creating a chart in Wenu follows four simple steps.

1. Create an observer.
2. Create a celestial sphere.
3. Add the astronomical layers.
4. Draw the chart.

Most examples follow this same sequence.

---

# Example

```python
from wenu import Observer
from wenu.sky import CelestialSphere
from wenu import StereographicProjection

observer = Observer(...)

sky = CelestialSphere(observer)

sky.add_stars()
sky.add_constellations()

projection = StereographicProjection(...)

sky.draw(projection)
```

(The exact API may evolve as the project develops.)

---

# Main Components

The most important classes are

- Observer
- CelestialSphere
- Stars
- Constellations
- Projection

Together they define what part of the sky is observed, how it is represented, and how it is drawn.

---

# Learning Wenu

The best way to learn Wenu is by studying the examples provided with the project.

Each example focuses on one specific task, such as

- drawing stars
- drawing constellation lines
- plotting coordinate grids
- producing a planisphere

---

# Current Limitations

Wenu is under active development.

Some parts of the API may change before the first stable release.

---

# Next Steps

Future versions of this guide will include

- coordinate systems
- projections
- drawing styles
- labels
- custom layers
- creating your own charts

