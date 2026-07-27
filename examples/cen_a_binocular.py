"""Render a 6.5-degree binocular field centered on Centaurus A."""

from __future__ import annotations

import argparse
from pathlib import Path

import astropy.units as u
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
from matplotlib.patches import Circle

from wenu import (
    CelestialSphere,
    ExportOptions,
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
    RegionalChart,
)


FIELD_DIAMETER_DEG = 6.5
STAR_MAGNITUDE_LIMIT = 11.0
GALAXY_MAGNITUDE_LIMIT = 11.0

# ICRS position of NGC 5128 (Centaurus A).
CEN_A = SkyCoord(
    ra="13h25m27.615s",
    dec="-43d01m08.81s",
    frame="icrs",
)


def build_chart():
    """Return the observer, sky, and north-up Cen A chart."""
    observer = Observer(
        location="La Ligua",
        time="2026-05-15 22:00",
    )
    sky = CelestialSphere(observer)
    sky.add_stars(
        catalog="hipparcos",
        magnitude_limit=STAR_MAGNITUDE_LIMIT,
    )
    sky.add_galaxies(
        magnitude_limit=GALAXY_MAGNITUDE_LIMIT,
        samples=97,
    )
    chart = RegionalChart.from_coordinate(
        observer,
        CEN_A,
        field_width_deg=FIELD_DIAMETER_DEG,
        field_height_deg=FIELD_DIAMETER_DEG,
        north_up=True,
    )
    return observer, sky, chart


def chart_style():
    """Return a high-contrast binocular-field style."""
    return PublicationStyle(
        star_area_scale=1.0,
        galaxy_edge_color="cyan",
        galaxy_linewidth=0.9,
        galaxy_edge_alpha=1.0,
        galaxy_face_color="deepskyblue",
        galaxy_face_alpha=0.16,
        galaxy_minimum_size_arcmin=1.0,
        galaxy_draw_labels=True,
        galaxy_label_color="cyan",
        galaxy_label_fontsize=6.0,
    )


def circular_aperture(ax, chart, *, sky_color, edge_color="white"):
    """Clip plotted sky artists to the chart's circular binocular field."""
    viewport = chart.viewport
    center_x = 0.5 * (viewport.xlim[0] + viewport.xlim[1])
    center_y = 0.5 * (viewport.ylim[0] + viewport.ylim[1])
    radius = 0.5 * min(
        viewport.xlim[1] - viewport.xlim[0],
        viewport.ylim[1] - viewport.ylim[0],
    )

    # The axes remain white outside the simulated eyepiece.
    ax.set_facecolor("white")
    disk = Circle(
        (center_x, center_y),
        radius,
        transform=ax.transData,
        facecolor=sky_color,
        edgecolor="none",
        zorder=-100.0,
        clip_on=False,
    )
    ax.add_patch(disk)

    # Clip every already-rendered sky artist. The disk itself is excluded.
    artists = (
        list(ax.lines)
        + list(ax.collections)
        + [patch for patch in ax.patches if patch is not disk]
        + list(ax.texts)
    )
    for artist in artists:
        artist.set_clip_path(disk)

    rim = Circle(
        (center_x, center_y),
        radius,
        transform=ax.transData,
        facecolor="none",
        edgecolor=edge_color,
        linewidth=1.0,
        zorder=100.0,
        clip_on=False,
    )
    ax.add_patch(rim)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_aspect("equal", adjustable="box")
    return disk, rim


def generate(output_directory="cen-a-binocular-output"):
    """Generate and return the Cen A binocular chart path."""
    _, sky, chart = build_chart()
    style = chart_style()
    figure, ax = plt.subplots(figsize=chart.figure_size(7.0))
    style.configure_axes(
        ax,
        title="Centaurus A — 6.5° binocular field",
    )
    renderer = MatplotlibRenderer(ax)
    result = chart.render(sky, renderer, style=style)
    circular_aperture(
        ax,
        chart,
        sky_color=style.sky_color,
        edge_color=style.foreground_color,
    )
    output = Path(output_directory) / "cen-a-6.5-deg.png"
    saved = ExportOptions(dpi=300).save(figure, output)
    plt.close(figure)
    return result, saved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output_directory",
        nargs="?",
        default="cen-a-binocular-output",
    )
    arguments = parser.parse_args()
    _, path = generate(arguments.output_directory)
    print(path)


if __name__ == "__main__":
    main()
