"""Reference chart for tuning the white AtlasChartStyle."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere,
    FixedDetailPolicy,
    LegendOptions,
    MatplotlibRenderer,
    Observer,
    PrintMode,
    RegionalChart,
    ResolvedDetail,
    compose_chart,
)


LINE_CONSTELLATIONS = ("Sgr", "Sco", "Oph", "Ser1", "Ser2")
BOUNDARY_CONSTELLATIONS = ("Sgr", "Sco", "Oph", "Ser")
LABEL_CONSTELLATIONS = ("Sgr", "Sco", "Oph", "SerCap", "SerCau")
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
DEFAULT_OUTPUT = Path(
    "output/style-gallery/atlas-sag-sco-oph-ser.png"
)


def generate(output=DEFAULT_OUTPUT):
    """Generate one representative atlas-style regional chart."""
    output = Path(output)
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
    )
    sky = CelestialSphere(observer)
    sky.add_milky_way_isophotes()
    sky.add_stars(
        catalog="hipparcos",
        magnitude_limit=6.5,
    )
    sky.add_galaxies(magnitude_limit=11.0)
    sky.add_open_clusters(selected=OPEN_CLUSTERS)
    sky.add_globular_clusters(magnitude_limit=11.0)
    sky.add_supernova_remnants(selected=SUPERNOVA_REMNANTS)
    sky.add_planetary_nebulae(selected=PLANETARY_NEBULAE)
    sky.add_constellations(
        system="western",
        selected=LINE_CONSTELLATIONS,
    )
    sky.add_constellation_boundaries(
        boundaries="iau",
        constellations=BOUNDARY_CONSTELLATIONS,
    )
    sky.add_equatorial_grid(
        ra=tuple(range(0, 360, 15)),
        dec=tuple(range(-75, 76, 15)),
        frame="fk5",
        equinox="J2000",
    )

    chart = RegionalChart.from_constellations(
        sky,
        LINE_CONSTELLATIONS,
        angular_radius_deg=43.0,
        aspect_ratio=1.38,
        north_up=True,
        crop_y=0.12,
        label_selection=LABEL_CONSTELLATIONS,
    )
    composition = compose_chart(
        chart,
        style="atlas",
        mode=PrintMode(width_inches=10.0, dpi=600),
        detail=FixedDetailPolicy(
            ResolvedDetail(
                star_magnitude_limit=6.5,
                galaxy_magnitude_limit=11.0,
            )
        ),
        legends=LegendOptions(
            objects=True,
            stellar_magnitudes=True,
            context=True,
        ),
    )

    figure, ax = plt.subplots(
        figsize=(
            composition.mode.width_inches,
            composition.mode.height_inches,
        ),
    )
    composition.style.configure_axes(
        ax,
        title="Sagittarius–Scorpius atlas-style reference",
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
