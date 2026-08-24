"""Plot Sag, Sco, Oph, and both parts of Serpens as one highlighted region."""

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


# The Western line file stores the two disconnected parts of Serpens
# separately. The official-boundary and mask APIs accept the collective
# abbreviation "Ser" and expand it to both regions.
LINE_CONSTELLATIONS = ("Sgr", "Sco", "Oph", "Ser1", "Ser2")
BOUNDARY_CONSTELLATIONS = ("Sgr", "Sco", "Oph", "Ser")
LABEL_CONSTELLATIONS = ("Sgr", "Sco", "Oph", "SerCap", "SerCau")


def generate(output, *, nonstellar_labels=False):
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
    sky.add_nonstellar(
        catalog="messier",
        samples=73,
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
        angular_radius_deg=45.0,
        aspect_ratio=1.25,
        orientation="celestial-north-up",
        crop_y=0.25,
        label_selection=LABEL_CONSTELLATIONS,
        outside_mask_constellations=BOUNDARY_CONSTELLATIONS,
    )

    style = PublicationStyle(
        outside_mask_color="black",
        outside_mask_alpha=0.42,
        outside_mask_zorder=20,
        label_fontsize=11,
        nonstellar_minimum_size_arcmin=30.0,
        nonstellar_draw_labels=nonstellar_labels,
        nonstellar_label_fontsize=7.0,
    )

    figure, ax = plt.subplots(figsize=chart.figure_size(9.0))
    style.configure_axes(
        ax,
        title="Sagittarius, Scorpius, Ophiuchus, and Serpens",
    )
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
        default=(
            "constellation-mask-output/"
            "sag-sco-oph-ser.png"
        ),
    )
    parser.add_argument(
        "--nonstellar-labels",
        action="store_true",
        help="label the plotted Messier symbols",
    )
    arguments = parser.parse_args()
    _, output = generate(
        arguments.output,
        nonstellar_labels=arguments.nonstellar_labels,
    )
    print(output)


if __name__ == "__main__":
    main()
