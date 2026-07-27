"""Masked regional verification of stellar classification symbols."""

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


LINE_CONSTELLATIONS = ("Cen", "Cru")
BOUNDARY_CONSTELLATIONS = ("Cen", "Cru")
LABEL_CONSTELLATIONS = ("Cen", "Cru")
DEFAULT_OUTPUT = Path(
    "output/stellar-symbols/centaurus-crux.png"
)


def generate(output=DEFAULT_OUTPUT):
    """Render a compact Centaurus–Crux stellar-symbol test chart."""
    output = Path(output)

    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )
    sky = CelestialSphere(observer)
    sky.add_stars(
        catalog="hipparcos",
        magnitude_limit=5.5,
    )
    sky.add_constellations(
        system="western",
        selected=LINE_CONSTELLATIONS,
    )
    sky.add_constellation_boundaries(
        boundaries="iau",
        constellations=BOUNDARY_CONSTELLATIONS,
    )

    chart = RegionalChart.from_constellations(
        sky,
        LINE_CONSTELLATIONS,
        angular_radius_deg=24.0,
        aspect_ratio=1.15,
        north_up=True,
        label_selection=LABEL_CONSTELLATIONS,
        outside_mask_constellations=BOUNDARY_CONSTELLATIONS,
    )

    style = PublicationStyle(
        star_area_scale=0.55,
        draw_variable_star_symbols=True,
        variable_star_color="cyan",
        variable_star_symbol_size=12.0,
        variable_star_linewidth=0.55,
        variable_star_alpha=0.9,
        draw_multiple_star_symbols=True,
        multiple_star_color="gold",
        multiple_star_symbol_size=12.0,
        multiple_star_linewidth=0.55,
        multiple_star_alpha=0.9,
        outside_mask_color="black",
        outside_mask_alpha=0.48,
        outside_mask_zorder=20.0,
        label_fontsize=10.0,
    )

    figure, ax = plt.subplots(
        figsize=chart.figure_size(8.0),
    )
    style.configure_axes(
        ax,
        title="Variable and multiple stars in Centaurus–Crux",
    )
    result, saved = chart.export(
        sky,
        MatplotlibRenderer(ax),
        output,
        style=style,
        export_options=ExportOptions(dpi=240),
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
