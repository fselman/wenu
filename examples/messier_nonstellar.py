"""Render selected Messier objects as dotted angular outlines."""

from pathlib import Path

import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere,
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
    RegionalChart,
)


def main():
    observer = Observer(
        location="La Ligua",
        time="2026-08-15T21:00:00",
    )
    sky = CelestialSphere(observer)
    sky.add_stars(magnitude_limit=6.0)
    sky.add_nonstellar(
        catalog="messier",
        samples=73,
    )

    chart = RegionalChart(
        center_alt_deg=45.0,
        center_az_deg=25.0,
        field_width_deg=75.0,
        field_height_deg=55.0,
    )
    figure, axis = plt.subplots(
        figsize=chart.figure_size(9.0),
        constrained_layout=True,
    )
    style = PublicationStyle(
        nonstellar_minimum_size_arcmin=30.0,
        nonstellar_draw_labels=False,
    )
    style.configure_axes(axis, title="Messier objects")
    renderer = MatplotlibRenderer(axis)
    output = Path("messier-output/messier.png")
    chart.export(
        sky,
        renderer,
        output,
        style=style,
    )
    plt.close(figure)
    print(output)


if __name__ == "__main__":
    main()
