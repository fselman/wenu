"""Generate galaxy verification charts in two constellation regions."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
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


@dataclass(frozen=True)
class Region:
    constellations: tuple[str, ...]
    title: str
    angular_radius_deg: float
    aspect_ratio: float
    crop_y: float = 0.0


REGIONS = {
    "centaurus-crux-musca": Region(
        constellations=("Cen", "Cru", "Mus"),
        title="Centaurus, Crux, and Musca",
        angular_radius_deg=38.0,
        aspect_ratio=1.25,
        crop_y=0.0,
    ),
    "virgo-coma": Region(
        constellations=("Vir", "Com"),
        title="Virgo and Coma Berenices",
        angular_radius_deg=36.0,
        aspect_ratio=1.25,
        crop_y=0.0,
    ),
}


def build_region(name):
    """Return observer, sky, and masked north-up chart for one region."""
    region = REGIONS[name]
    observer = Observer(
        location="La Ligua",
        time="2026-05-15 22:00",
    )
    sky = CelestialSphere(observer)
    sky.add_stars(
        catalog="hipparcos",
        magnitude_limit=6.0,
    )
    sky.add_galaxies(
        magnitude_limit=11.0,
        samples=73,
    )
    sky.add_constellations(
        system="western",
        selected=region.constellations,
    )
    sky.add_constellation_boundaries(
        boundaries="iau",
        constellations=region.constellations,
    )
    chart = RegionalChart.from_constellations(
        sky,
        region.constellations,
        angular_radius_deg=region.angular_radius_deg,
        aspect_ratio=region.aspect_ratio,
        orientation="celestial-north-up",
        crop_y=region.crop_y,
        label_selection=region.constellations,
        outside_mask_constellations=region.constellations,
    )
    return region, observer, sky, chart


def chart_style(*, filled):
    """Return the outline-only or translucent-fill verification style."""
    return PublicationStyle(
        galaxy_edge_color="cyan",
        galaxy_linewidth=0.7,
        galaxy_edge_alpha=0.9,
        galaxy_face_color=("deepskyblue" if filled else None),
        galaxy_face_alpha=(0.18 if filled else 0.0),
        galaxy_minimum_size_arcmin=6.0,
        galaxy_draw_labels=False,
        galaxy_label_fontsize=6.0,
        outside_mask_color="black",
        outside_mask_alpha=0.42,
        outside_mask_zorder=20.0,
        label_fontsize=10.0,
    )


def render_region(name, output, *, filled):
    """Render and save one verification chart."""
    region, _, sky, chart = build_region(name)
    style = chart_style(filled=filled)
    figure, ax = plt.subplots(figsize=chart.figure_size(9.0))
    suffix = " — translucent galaxy fill" if filled else ""
    style.configure_axes(ax, title=region.title + suffix)
    result, saved = chart.export(
        sky,
        MatplotlibRenderer(ax),
        output,
        style=style,
        export_options=ExportOptions(dpi=300),
    )
    plt.close(figure)
    return result, saved


def generate(output_directory):
    """Generate the requested Centaurus and Virgo/Coma charts."""
    output = Path(output_directory)
    products = []
    products.append(
        render_region(
            "centaurus-crux-musca",
            output / "01-centaurus-crux-musca-outline.png",
            filled=False,
        )[1]
    )
    products.append(
        render_region(
            "centaurus-crux-musca",
            output / "02-centaurus-crux-musca-filled.png",
            filled=True,
        )[1]
    )
    products.append(
        render_region(
            "virgo-coma",
            output / "03-virgo-coma-filled.png",
            filled=True,
        )[1]
    )
    return tuple(products)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "output_directory",
        nargs="?",
        default="galaxy-regions-output",
    )
    arguments = parser.parse_args()
    for path in generate(arguments.output_directory):
        print(path)


if __name__ == "__main__":
    main()
