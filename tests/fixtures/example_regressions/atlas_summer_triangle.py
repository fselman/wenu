"""Atlas-style chart of the Summer Triangle constellation region."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    AtlasChartStyle,
    CelestialSphere,
    LegendOptions,
    MatplotlibRenderer,
    Observer,
    PrintMode,
    RegionalChart,
    compose_chart,
)


CONSTELLATIONS = ("Cyg", "Lyr", "Vul", "Sge", "Aql")
OPEN_CLUSTERS = (
    "NGC 6709",
    "NGC 6811",
    "NGC 6830",
    "NGC 6885",
    "NGC 6940",
)
PLANETARY_NEBULAE = (
    "PN G060.8-03.6",  # M27, the Dumbbell Nebula
    "PN G063.1+13.9",  # M57, the Ring Nebula
)
SUPERNOVA_REMNANTS = (
    "G065.3+05.7",
    "G074.0-08.5",  # Cygnus Loop
    "G078.2+02.1",  # Gamma Cygni remnant
)
DEFAULT_OUTPUT = Path(
    "output/style-gallery/atlas-summer-triangle.png"
)


def generate(output=DEFAULT_OUTPUT):
    """Generate the Cyg–Lyr–Vul–Sge–Aql atlas-style chart."""
    output = Path(output)
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )
    sky = CelestialSphere(observer)
    sky.add_milky_way_isophotes()
    sky.add_stars(
        catalog="hipparcos",
        magnitude_limit=6.5,
    )
    sky.add_galaxies(magnitude_limit=11.0)
    sky.add_open_clusters(selected=OPEN_CLUSTERS)
    sky.add_globular_clusters(magnitude_limit=11.0)
    sky.add_supernova_remnants(selected=SUPERNOVA_REMNANTS)
    sky.add_planetary_nebulae(selected=PLANETARY_NEBULAE)
    sky.add_constellations(
        system="western",
        selected=CONSTELLATIONS,
    )
    sky.add_constellation_boundaries(
        boundaries="iau",
        constellations=CONSTELLATIONS,
    )
    sky.add_equatorial_grid(
        ra=tuple(range(0, 360, 15)),
        dec=tuple(range(-75, 76, 15)),
        frame="fk5",
        equinox="J2000",
    )

    chart = RegionalChart.from_constellations(
        sky,
        CONSTELLATIONS,
        angular_radius_deg=52.0,
        aspect_ratio=1.38,
        north_up=True,
        crop_y=0.0,
        label_selection=CONSTELLATIONS,
    )
    style = AtlasChartStyle()
    style = replace(
        style,
        grids=replace(
            style.grids,
            horizon_altitude_deg=-90.0,
            minimum_altitude_deg=-90.0,
        ),
    )
    composition = compose_chart(
        chart,
        style=style,
        mode=PrintMode(width_inches=10.0, dpi=480),
        legends=LegendOptions(
            objects=True,
            stellar_magnitudes=False,
            context=True,
        ),
    )
    figure, ax = plt.subplots(
        figsize=(
            composition.mode.width_inches,
            composition.mode.height_inches,
        ),
    )
    composition.style.configure_axes(
        ax,
        title="The Summer Triangle — Cygnus, Lyra, Vulpecula, "
        "Sagitta, and Aquila",
    )
    result, saved = chart.export(
        sky,
        MatplotlibRenderer(ax),
        output,
        composition=composition,
    )
    plt.close(figure)
    return result, saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output",
        nargs="?",
        default=DEFAULT_OUTPUT,
        type=Path,
    )
    arguments = parser.parse_args()
    _, saved = generate(arguments.output)
    print(saved)


if __name__ == "__main__":
    main()
