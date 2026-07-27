"""Fast regional examples using the planetary-nebula chart symbol."""

from pathlib import Path

import matplotlib.pyplot as plt

from wenu import (
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
    RegionalChart,
)
from wenu.sky import CelestialSphere


OUTPUT = Path("planetary-nebulae-output")

REGIONS = (
    (
        "01-ring.png",
        "Ring Nebula (M57)",
        "PN G063.1+13.9",
    ),
    (
        "02-helix.png",
        "Helix Nebula (NGC 7293)",
        "PN G036.1-57.1",
    ),
)


def main():
    OUTPUT.mkdir(exist_ok=True)
    observer = Observer(
        location="La Ligua",
        time="2026-07-27 02:00:00",
    )
    style = PublicationStyle(
        planetary_nebula_symbol_size=100.0,
        planetary_nebula_draw_labels=True,
    )

    for filename, title, identifier in REGIONS:
        sky = CelestialSphere(observer)
        sky.add_stars(magnitude_limit=11.0)
        layer = sky.add_planetary_nebulae(selected=[identifier])
        center = layer.spherical_geometry(observer)
        chart = RegionalChart(
            center_alt_deg=float(center.lat_deg[0]),
            center_az_deg=float(center.lon_deg[0]),
            field_width_deg=8.0,
            field_height_deg=8.0,
        )
        fig, ax = plt.subplots(
            figsize=chart.figure_size(7.0),
            dpi=180,
        )
        style.configure_axes(ax, title=title)
        renderer = MatplotlibRenderer(ax)
        sky.draw_chart(
            projection=chart.projection,
            renderer=renderer,
            viewport=chart.viewport,
            layer_options=style.layer_options(
                sky,
                horizon_altitude_deg=-90.0,
            ),
        )
        output = OUTPUT / filename
        fig.savefig(output, bbox_inches="tight")
        plt.close(fig)
        print(output)


if __name__ == "__main__":
    main()
