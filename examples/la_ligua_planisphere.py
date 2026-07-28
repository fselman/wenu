"""Atlas-style visible-sky planisphere for La Ligua."""

from __future__ import annotations

import argparse
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    AtlasChartStyle,
    CelestialSphere,
    ExportOptions,
    FullSkyChart,
    MatplotlibRenderer,
    Observer,
    draw_chart_legend,
)


LOCAL_TIME = "2026-08-15 21:00"
DEFAULT_OUTPUT = Path(
    "output/style-gallery/atlas-la-ligua-planisphere-20260815-2100.png"
)
OPEN_CLUSTERS = (
    "NGC 6405",
    "NGC 6475",
    "NGC 6530",
    "NGC 6603",
    "NGC 6611",
    "NGC 6705",
)
PLANETARY_NEBULAE = (
    "PN G349.5+01.0",
    "PN G002.4+05.8",
    "PN G008.0+03.9",
    "PN G009.4-05.0",
    "PN G010.1+00.7",
    "PN G025.8-17.9",
)
SUPERNOVA_REMNANTS = (
    "G004.5+06.8",
    "G006.4-00.1",
    "G011.2-00.3",
    "G021.8-00.6",
    "G027.4+00.0",
    "G034.7-00.4",
)


def circular_grid_label_anchor(curve, ax, boundary):
    """Place coordinate labels immediately inside a circular boundary."""
    finite_boundary = boundary.finite
    boundary_radius = float(
        np.nanmedian(
            np.hypot(
                boundary.x[finite_boundary],
                boundary.y[finite_boundary],
            )
        )
    )
    finite = curve.finite
    if not np.any(finite):
        return None
    x = curve.x[finite]
    y = curve.y[finite]
    radius = np.hypot(x, y)
    inside = radius <= boundary_radius * (1.0 + 1.0e-6)
    if not np.any(inside):
        return None
    x = x[inside]
    y = y[inside]
    radius = radius[inside]
    index = int(np.argmax(radius))
    return 0.965 * x[index], 0.965 * y[index]


def utc_offset_text(local_datetime):
    """Format a timezone-aware UTC offset."""
    offset = local_datetime.utcoffset()
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "−"
    total_minutes = abs(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    return f"UTC{sign}{hours:02d}:{minutes:02d}"


def observation_context(observer):
    """Return location and local date/time lines for the chart legend."""
    local = observer.utc_datetime.astimezone(
        ZoneInfo(observer.timezone_name)
    )
    return (
        (
            f"Location: {observer.location_name} — "
            f"{abs(observer.lat_deg):.4f}° S, "
            f"{abs(observer.lon_deg):.4f}° W, "
            f"{observer.elevation_m:.0f} m"
        ),
        f"Date: {local:%Y-%m-%d}",
        (
            f"Local time: {local:%H:%M} "
            f"({utc_offset_text(local)})"
        ),
    )


def build_planisphere():
    """Build the La Ligua visible sky and zenith-centered chart."""
    observer = Observer(location="La Ligua", time=LOCAL_TIME)
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
        dec=tuple(range(-75, 76, 15)),
        frame="fk5",
        equinox="J2000",
        samples=1441,
        meridian_dec_min=-75.0,
        meridian_dec_max=90.0,
    )
    chart = FullSkyChart(
        center_alt_deg=90.0,
        center_az_deg=0.0,
        horizon_altitude_deg=0.0,
        horizon_color="#707070",
        horizon_linewidth=0.8,
    )
    return sky, chart, grid, AtlasChartStyle()


def generate(output=DEFAULT_OUTPUT):
    """Generate the 480 dpi La Ligua atlas planisphere."""
    output = Path(output)
    sky, chart, grid, style = build_planisphere()
    figure, ax = plt.subplots(figsize=chart.figure_size(10.0))
    style.configure_axes(
        ax,
        title="La Ligua planisphere — 15 August 2026, 21:00",
    )
    renderer = MatplotlibRenderer(ax)
    layer_options = style.layer_options(
        sky,
        horizon_altitude_deg=0.0,
    )
    grid_options = dict(layer_options[grid])
    grid_render = dict(grid_options["render"])
    grid_render["label_anchor"] = (
        lambda curve, axes: circular_grid_label_anchor(
            curve,
            axes,
            chart.horizon,
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
    draw_chart_legend(
        ax,
        chart,
        sky,
        style,
        context_lines=observation_context(sky.observer),
    )
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
