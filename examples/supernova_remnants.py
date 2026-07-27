"""Render verification charts for Vela and the Crab Nebula."""

from __future__ import annotations

import argparse
from pathlib import Path

import astropy.units as u
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord

from wenu import (
    CelestialSphere,
    ExportOptions,
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
    RegionalChart,
)


FIELDS = (
    (
        "vela",
        "Vela supernova remnant",
        SkyCoord(ra=128.75 * u.deg, dec=-45.6 * u.deg, frame="icrs"),
        "2026-12-15 23:00",
        14.0,
        14.0,
        None,
    ),
    (
        "crab",
        "Crab Nebula — M1",
        SkyCoord(ra=83.633 * u.deg, dec=22.017 * u.deg, frame="icrs"),
        "2026-12-15 23:00",
        6.5,
        6.5,
        12.0,
    ),
)


def build_field(center, time, width, height):
    observer = Observer(location="La Ligua", time=time)
    sky = CelestialSphere(observer)
    sky.add_stars(catalog="hipparcos", magnitude_limit=9.0)
    sky.add_supernova_remnants(samples=73)
    chart = RegionalChart.from_coordinate(
        observer,
        center,
        field_width_deg=width,
        field_height_deg=height,
        north_up=True,
    )
    return sky, chart


def generate(output_directory="supernova-remnants-output"):
    output = Path(output_directory)
    paths = []
    for index, (
        slug,
        title,
        center,
        time,
        width,
        height,
        minimum_size,
    ) in enumerate(FIELDS, start=1):
        sky, chart = build_field(center, time, width, height)
        style = PublicationStyle(
            supernova_remnant_color="gold",
            supernova_remnant_linewidth=0.9,
            supernova_remnant_linestyle="--",
            supernova_remnant_minimum_size_arcmin=minimum_size,
            supernova_remnant_draw_labels=True,
            supernova_remnant_label_fontsize=7.0,
        )
        figure, ax = plt.subplots(figsize=chart.figure_size(7.0))
        style.configure_axes(ax, title=title)
        _, saved = chart.export(
            sky,
            MatplotlibRenderer(ax),
            output / f"{index:02d}-{slug}.png",
            style=style,
            export_options=ExportOptions(dpi=300),
        )
        plt.close(figure)
        paths.append(saved)
    return tuple(paths)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output_directory",
        nargs="?",
        default="supernova-remnants-output",
    )
    args = parser.parse_args()
    for path in generate(args.output_directory):
        print(path)


if __name__ == "__main__":
    main()
