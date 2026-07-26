"""Generate a publication full-sky chart through the public Wenu API."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from wenu import (
    CelestialSphere,
    ExportOptions,
    FullSkyChart,
    MatplotlibRenderer,
    Observer,
    PublicationStyle,
)
from wenu.coordinates import radec_to_altaz


def build_sky():
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )
    sky = CelestialSphere(observer)
    sky.add_stars(catalog="hipparcos", magnitude_limit=5.5)
    sky.add_constellations(system="western")
    sky.add_constellation_boundaries(boundaries="iau")

    points = sky.add_points()
    points.add_equatorial_pole(pole="visible")
    points.add_ecliptic_pole(pole="visible")
    points.add_galactic_center()
    points.add_ecliptic_keypoints()

    sky.add_equatorial_grid(include_equator=True)
    sky.add_ecliptic_grid(include_ecliptic=True)
    sky.add_galactic_grid(include_plane=True)
    return sky


def generate(output):
    output = Path(output)
    sky = build_sky()
    south_pole_altitude, south_pole_azimuth = radec_to_altaz(
        np.asarray([0.0]),
        np.asarray([-90.0]),
        sky.observer.t,
        sky.observer.lat_deg,
        sky.observer.lon_deg,
    )
    chart = FullSkyChart(
        center_alt_deg=float(south_pole_altitude[0]),
        center_az_deg=float(south_pole_azimuth[0]),
        position_angle_deg=0.0,
    )
    style = PublicationStyle(
        star_area_scale=0.25,
        grid_minimum_altitude_deg=0.0,
    )

    figure, ax = plt.subplots(figsize=chart.figure_size(7.0))
    style.configure_axes(
        ax,
        title="Full-sky chart — SCP tangent, zenith up",
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
        default="milestone23-output/full-sky.png",
    )
    arguments = parser.parse_args()
    _, output = generate(arguments.output)
    print(output)


if __name__ == "__main__":
    main()
