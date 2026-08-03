"""Atlas-style visible-sky planisphere for La Ligua."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere,
    FullSkyChart,
    LegendOptions,
    MatplotlibRenderer,
    Observer,
    PrintMode,
    compose_chart,
    observer_context_lines,
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
    sky.add_equatorial_grid(
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
    return sky, chart


def generate(output=DEFAULT_OUTPUT):
    """Generate the 480 dpi La Ligua atlas planisphere."""
    output = Path(output)
    sky, chart = build_planisphere()
    composition = compose_chart(
        chart,
        style="atlas",
        mode=PrintMode(width_inches=10.0, dpi=480),
        legends=LegendOptions(
            objects=True,
            stellar_magnitudes=False,
            context=True,
            context_lines=observer_context_lines(sky.observer),
        ),
    )
    figure, ax = plt.subplots(
        figsize=(
            composition.mode.width_inches,
            composition.mode.height_inches,
        )
    )
    composition.style.configure_axes(
        ax,
        title="La Ligua planisphere — 15 August 2026, 21:00",
    )
    result, saved = chart.export(
        sky,
        MatplotlibRenderer(ax),
        output,
        composition=composition,
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
