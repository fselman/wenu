"""Render verification charts for omega Centauri and 47 Tucanae."""

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
        "omega-centauri",
        "Omega Centauri",
        SkyCoord(ra=201.697 * u.deg, dec=-47.480 * u.deg, frame="icrs"),
        "2026-05-15 22:00",
    ),
    (
        "47-tucanae",
        "47 Tucanae",
        SkyCoord(ra=6.023 * u.deg, dec=-72.081 * u.deg, frame="icrs"),
        "2026-10-15 22:00",
    ),
)


def build_field(center, time):
    observer = Observer(
        location="La Ligua",
        time=time,
    )
    sky = CelestialSphere(observer)
    sky.add_stars(catalog="hipparcos", magnitude_limit=8.0)
    sky.add_globular_clusters(magnitude_limit=12.0, samples=73)
    chart = RegionalChart.from_coordinate(
        observer,
        center,
        field_width_deg=12.0,
        field_height_deg=12.0,
        north_up=True,
    )
    return sky, chart


def generate(output_directory="globular-clusters-output"):
    output = Path(output_directory)
    paths = []
    style = PublicationStyle(
        globular_cluster_color="gold",
        globular_cluster_linewidth=0.9,
        globular_cluster_minimum_size_arcmin=10.0,
        globular_cluster_draw_labels=True,
        globular_cluster_label_fontsize=7.0,
    )
    for index, (slug, title, center, time) in enumerate(FIELDS, start=1):
        sky, chart = build_field(center, time)
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
        default="globular-clusters-output",
    )
    args = parser.parse_args()
    for path in generate(args.output_directory):
        print(path)


if __name__ == "__main__":
    main()
