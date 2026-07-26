"""Concise Milestone 16 regional-chart production examples."""

from pathlib import Path

import astropy.units as u
from astropy.coordinates import SkyCoord
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


OUTPUT = Path("milestone16-output")


def make_sky(*, system="western", selected=None, boundaries=False):
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )
    sky = CelestialSphere(observer)
    sky.add_stars(magnitude_limit=5.5)
    sky.add_constellations(system=system, selected=selected)
    if boundaries:
        sky.add_constellation_boundaries(
            constellations=selected,
        )
    return sky


def save(chart, sky, filename, title):
    style = PublicationStyle()
    figure, ax = plt.subplots(figsize=chart.figure_size(7.0))
    style.configure_axes(ax, title=title)
    chart.export(
        sky,
        MatplotlibRenderer(ax),
        OUTPUT / filename,
        style=style,
        export_options=ExportOptions(
            dpi=300,
            metadata={"Creator": "Wenu Milestone 16"},
        ),
    )
    plt.close(figure)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    crux = make_sky(selected=["Cru"], boundaries=True)
    save(
        RegionalChart.from_constellations(
            crux,
            ["Cru"],
            angular_radius_deg=18.0,
            label_selection=["Cru"],
        ),
        crux,
        "01-crux.png",
        "Crux",
    )

    crux_centaurus = make_sky(selected=["Cru", "Cen"])
    save(
        RegionalChart.from_constellations(
            crux_centaurus,
            ["Cru", "Cen"],
            angular_radius_deg=30.0,
            aspect_ratio=1.35,
            north_up=True,
        ),
        crux_centaurus,
        "02-crux-centaurus.png",
        "Crux and Centaurus — north up",
    )

    mapuche = make_sky(system="mapuche")
    southern_cross = SkyCoord(
        ra=187.5 * u.deg,
        dec=-60.0 * u.deg,
        frame="icrs",
    )
    save(
        RegionalChart.from_coordinate(
            mapuche.observer,
            southern_cross,
            field_width_deg=55.0,
            field_height_deg=42.0,
            north_up=True,
            label_selection=(),
        ),
        mapuche,
        "03-mapuche.png",
        "Mapuche constellation figures",
    )

    grid = make_sky(selected=["Cru", "Cen"], boundaries=True)
    grid.add_equatorial_grid(
        ra=[165.0, 180.0, 195.0, 210.0],
        dec=[-70.0, -60.0, -50.0, -40.0],
    )
    save(
        RegionalChart.from_constellations(
            grid,
            ["Cru", "Cen"],
            angular_radius_deg=30.0,
            aspect_ratio=1.4,
            north_up=True,
            crop_y=0.05,
        ),
        grid,
        "04-publication.png",
        "Southern Cross region",
    )


if __name__ == "__main__":
    main()
