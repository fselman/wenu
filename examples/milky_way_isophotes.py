"""Visual verification of the Milky Way isophote layer."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere,
    ExportOptions,
    FullSkyChart,
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
)


def generate(output):
    output = Path(output)
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )
    sky = CelestialSphere(observer)
    sky.add_milky_way_isophotes()
    sky.add_stars(catalog="hipparcos", magnitude_limit=5.5)
    sky.add_constellations(system="western")

    chart = FullSkyChart()
    style = PublicationStyle(
        star_area_scale=0.25,
        milky_way_color="deepskyblue",
        milky_way_alpha=0.11,
    )
    figure, ax = plt.subplots(figsize=chart.figure_size(8.0))
    style.configure_axes(ax, title="Milky Way isophotes")
    _, saved = chart.export(
        sky,
        MatplotlibRenderer(ax),
        output,
        style=style,
        export_options=ExportOptions(dpi=200),
    )
    plt.close(figure)
    return saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output",
        nargs="?",
        default="milky-way-isophotes-output/full-sky.png",
    )
    args = parser.parse_args()
    print(generate(args.output))


if __name__ == "__main__":
    main()
