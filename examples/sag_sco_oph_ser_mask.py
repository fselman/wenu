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
LINE_CONSTELLATIONS = ("Sag", "Sco", "Oph", "Ser1", "Ser2")
BOUNDARY_CONSTELLATIONS = ("Sag", "Sco", "Oph", "Ser")
LABEL_CONSTELLATIONS = ("Sag", "Sco", "Oph", "SerCap", "SerCau")


def generate(output):
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
        angular_radius_deg=45.0,
        aspect_ratio=1.25,
        north_up=True,
        crop_y=0.25,
        label_selection=LABEL_CONSTELLATIONS,
        outside_mask_constellations=BOUNDARY_CONSTELLATIONS,
    )

    style = PublicationStyle(
        outside_mask_color="black",
        outside_mask_alpha=0.42,
        outside_mask_zorder=20,
        label_fontsize=11,
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
    arguments = parser.parse_args()
    _, output = generate(arguments.output)
    print(output)


if __name__ == "__main__":
    main()
