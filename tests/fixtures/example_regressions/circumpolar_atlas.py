"""Atlas chart whose circular boundary bisects the Large Magellanic Cloud."""

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
    CircumpolarChart,
    LegendOptions,
    MatplotlibRenderer,
    Observer,
    PrintMode,
    compose_chart,
)


LIMITING_DECLINATION_DEG = -69.75
OPEN_CLUSTERS = (
    "Melotte 25",
    "IC 2391",
    "IC 2602",
    "NGC 2516",
    "NGC 3532",
    "NGC 4755",
)
PLANETARY_NEBULAE = (
    "PN G036.1-57.1",  # Helix Nebula
    "PN G261.0+32.0",  # Southern Owl Nebula
)
SUPERNOVA_REMNANTS = (
    "G263.9-03.3",  # Vela
    "G292.0+01.8",
    "G296.5+10.0",
    "G315.4-02.3",  # RCW 86
)
DEFAULT_OUTPUT = Path(
    "output/style-gallery/atlas-south-circumpolar-lmc-boundary.png"
)


def build_chart():
    """Build the sky, polar chart, and atlas style."""
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )
    sky = CelestialSphere(observer)
    sky.add_milky_way_isophotes()
    sky.add_magellanic_cloud_isophotes("lmc")
    sky.add_stars(catalog="hipparcos", magnitude_limit=6.5)
    sky.add_galaxies(magnitude_limit=10.5)
    sky.add_open_clusters(selected=OPEN_CLUSTERS)
    sky.add_globular_clusters(magnitude_limit=9.0)
    sky.add_supernova_remnants(selected=SUPERNOVA_REMNANTS)
    sky.add_planetary_nebulae(selected=PLANETARY_NEBULAE)
    sky.add_constellations(system="western")
    sky.add_constellation_boundaries(boundaries="iau")
    sky.add_equatorial_grid(
        ra=tuple(range(0, 360, 30)),
        dec=(-85, -80, -75),
        frame="fk5",
        equinox="J2000",
        samples=1441,
        meridian_dec_min=-75.0,
        meridian_dec_max=90.0,
    )

    chart = CircumpolarChart(
        observer,
        limiting_declination_deg=LIMITING_DECLINATION_DEG,
        pole="south",
        position_angle_deg=0.0,
    )
    return sky, chart


def generate(output=DEFAULT_OUTPUT):
    """Generate the circular atlas chart at double-resolution PNG DPI."""
    output = Path(output)
    sky, chart = build_chart()
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
        )
    )
    composition.style.configure_axes(
        ax,
        title=(
            "Southern circumpolar atlas — "
            "the −69.75° boundary bisects the LMC"
        ),
    )
    result, saved = chart.export(
        sky,
        MatplotlibRenderer(ax),
        output,
        composition=composition,
        boundary_style={
            "facecolor": "none",
            "edgecolor": "#707070",
            "linewidth": 0.8,
            "zorder": 8.0,
        },
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
