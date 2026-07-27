"""Southern open-cluster charts using the fixed symbol library."""

from pathlib import Path

import matplotlib.pyplot as plt

from wenu import (
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
    RegionalChart,
)
from wenu.sky import CelestialSphere


OUTPUT = Path("open-cluster-output")

REGIONS = (
    ("01-ic2602.png", "Southern Pleiades — IC 2602", "IC 2602"),
    ("02-jewel-box.png", "Jewel Box — NGC 4755", "NGC 4755"),
    ("03-ngc3532.png", "Wishing Well Cluster — NGC 3532", "NGC 3532"),
)


def main():
    OUTPUT.mkdir(exist_ok=True)
    observer = Observer(
        location="La Ligua",
        time="2026-07-27 02:00:00",
    )
    style = PublicationStyle(
        open_cluster_symbol_size=110.0,
        open_cluster_draw_labels=True,
    )

    for filename, title, identifier in REGIONS:
        sky = CelestialSphere(observer)
        sky.add_stars(magnitude_limit=10.0)
        layer = sky.add_open_clusters(selected=[identifier])
        center = layer.spherical_geometry(observer)
        chart = RegionalChart(
            center_alt_deg=float(center.lat_deg[0]),
            center_az_deg=float(center.lon_deg[0]),
            field_width_deg=10.0,
            field_height_deg=10.0,
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
