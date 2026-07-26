"""Generate a regional chart with the area outside Crux dimmed."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere,
    ExportOptions,
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
    RegionalChart,
)


def generate(output):
    output = Path(output)
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )
    sky = CelestialSphere(observer)
    sky.add_stars(catalog="hipparcos", magnitude_limit=5.5)
    sky.add_constellations(system="western", selected=("Cru",))
    sky.add_constellation_boundaries(
        boundaries="iau",
        constellations=("Cru",),
    )

    chart = RegionalChart.from_constellations(
        sky,
        ("Cru",),
        angular_radius_deg=22.0,
        north_up=True,
        outside_mask_constellations=("Cru",),
    )
    style = PublicationStyle(
        outside_mask_color="black",
        outside_mask_alpha=0.40,
        outside_mask_zorder=20,
    )
    figure, ax = plt.subplots(figsize=chart.figure_size(7.0))
    style.configure_axes(ax, title="Crux highlighted")
    result, saved = chart.export(
        sky,
        MatplotlibRenderer(ax),
        output,
        style=style,
        export_options=ExportOptions(dpi=300),
    )
    plt.close(figure)
    return result, saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output",
        nargs="?",
        default="constellation-mask-output/crux.png",
    )
    arguments = parser.parse_args()
    _, output = generate(arguments.output)
    print(output)


if __name__ == "__main__":
    main()
