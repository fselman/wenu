"""Atlas-style chart of the J2000 sky south of declination -40 degrees."""

from __future__ import annotations

import argparse
from pathlib import Path

import astropy.units as u
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.coordinates import FK5, SkyCoord
from astropy.time import Time

from wenu import (
    AtlasChartStyle,
    CelestialSphere,
    ExportOptions,
    MatplotlibRenderer,
    Observer,
    RegionalChart,
    draw_chart_legend,
)
from wenu.geometry.projected import ProjectedCurve


LIMITING_DECLINATION_DEG = -40.0
OPEN_CLUSTERS = (
    "Melotte 25",
    "IC 2391",
    "IC 2602",
    "NGC 2516",
    "NGC 3532",
    "NGC 4755",
)
PLANETARY_NEBULAE = (
    "PN G036.1-57.1",  # Helix Nebula
    "PN G261.0+32.0",  # Southern Owl Nebula
)
SUPERNOVA_REMNANTS = (
    "G263.9-03.3",  # Vela
    "G292.0+01.8",
    "G296.5+10.0",
    "G315.4-02.3",  # RCW 86
)
DEFAULT_OUTPUT = Path(
    "output/style-gallery/atlas-south-circumpolar-dec-minus40.png"
)


def south_pole():
    """Return the J2000 South Celestial Pole."""
    return SkyCoord(
        ra=0.0 * u.deg,
        dec=-90.0 * u.deg,
        frame=FK5(equinox=Time("J2000")),
    )


def declination_boundary(observer, projection, samples=1441):
    """Project the J2000 declination -40 degree limiting circle."""
    ra = np.linspace(0.0, 360.0, int(samples), endpoint=False)
    coordinates = SkyCoord(
        ra=ra * u.deg,
        dec=np.full_like(ra, LIMITING_DECLINATION_DEG) * u.deg,
        frame=FK5(equinox=Time("J2000")),
    )
    horizontal = coordinates.transform_to(observer.altaz_frame)
    x, y = projection.project_spherical(
        horizontal.az.deg,
        horizontal.alt.deg,
    )
    return ProjectedCurve(
        x=x,
        y=y,
        closed=True,
        name="declination_-40",
    )


def polar_grid_label_anchor(curve, ax, boundary_radius):
    """Anchor grid labels just inside the circular polar boundary."""
    finite = curve.finite
    if not np.any(finite):
        return None
    x = curve.x[finite]
    y = curve.y[finite]
    radius = np.hypot(x, y)
    inside = radius <= float(boundary_radius) * (1.0 + 1.0e-6)
    if not np.any(inside):
        return None
    x = x[inside]
    y = y[inside]
    radius = radius[inside]

    if curve.name.startswith("right_ascension_"):
        index = int(np.argmax(radius))
        return 0.965 * x[index], 0.965 * y[index]

    index = int(np.argmin(x))
    return 0.965 * x[index], 0.965 * y[index]


def build_chart():
    """Build the sky, polar chart, and atlas style."""
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )
    sky = CelestialSphere(observer)
    sky.add_milky_way_isophotes()
    sky.add_magellanic_cloud_isophotes("lmc")
    sky.add_magellanic_cloud_isophotes("smc")
    sky.add_stars(catalog="hipparcos", magnitude_limit=6.5)
    sky.add_galaxies(magnitude_limit=10.5)
    sky.add_open_clusters(selected=OPEN_CLUSTERS)
    sky.add_globular_clusters(magnitude_limit=9.0)
    sky.add_supernova_remnants(selected=SUPERNOVA_REMNANTS)
    sky.add_planetary_nebulae(selected=PLANETARY_NEBULAE)
    sky.add_constellations(system="western")
    sky.add_constellation_boundaries(boundaries="iau")
    grid = sky.add_equatorial_grid(
        ra=tuple(range(0, 360, 30)),
        dec=(-75, -60, -45),
        frame="fk5",
        equinox="J2000",
        samples=1441,
        meridian_dec_min=-75.0,
        meridian_dec_max=90.0,
    )

    chart = RegionalChart.from_coordinate(
        observer,
        south_pole(),
        field_width_deg=100.0,
        field_height_deg=100.0,
        position_angle_deg=0.0,
    )
    return sky, chart, grid, AtlasChartStyle()


def generate(output=DEFAULT_OUTPUT):
    """Generate the circular atlas chart at double-resolution PNG DPI."""
    output = Path(output)
    sky, chart, grid, style = build_chart()
    figure, ax = plt.subplots(figsize=chart.figure_size(10.0))
    style.configure_axes(
        ax,
        title="Southern circumpolar atlas — J2000 declination ≤ −40°",
    )
    renderer = MatplotlibRenderer(ax)
    boundary = declination_boundary(sky.observer, chart.projection)
    renderer.set_clip_boundary(
        boundary,
        style={
            "facecolor": "none",
            "edgecolor": "#707070",
            "linewidth": 0.8,
            "zorder": 8.0,
        },
    )
    layer_options = style.layer_options(
        sky,
        horizon_altitude_deg=-90.0,
    )
    grid_options = dict(layer_options[grid])
    grid_render = dict(grid_options["render"])
    boundary_radius = float(
        np.nanmedian(np.hypot(boundary.x, boundary.y))
    )
    grid_render["label_anchor"] = (
        lambda curve, axes: polar_grid_label_anchor(
            curve,
            axes,
            boundary_radius,
        )
    )
    grid_options["render"] = grid_render
    layer_options[grid] = grid_options

    result, saved = chart.export(
        sky,
        renderer,
        output,
        style=style,
        layer_options=layer_options,
        export_options=ExportOptions(dpi=480),
    )
    draw_chart_legend(ax, chart, sky, style)
    figure.savefig(saved, dpi=480, bbox_inches="tight")
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
