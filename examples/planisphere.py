"""Generate canonical visible-sky planispheres for La Ligua.

Examples:
    python examples/planisphere.py --style atlas --mode print
    python examples/planisphere.py --all --output output/planisphere
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere,
    ChartFurnitureOptions,
    FooterOptions,
    FixedDetailPolicy,
    FullSkyChart,
    LegendOptions,
    MatplotlibRenderer,
    Observer,
    PoleAnnotations,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
    ResolvedDetail,
    add_chart_arguments,
    chart_context_lines,
    chart_detail_overrides,
    chart_legend_selection,
    chart_product_options,
    chart_style_overrides,
    compose_chart,
    observer_context_lines,
)


LOCAL_TIME = "2026-08-15 21:00"
DEFAULT_OUTPUT = Path("output/examples/planisphere")
OPEN_CLUSTERS = (
    "NGC 6405", "NGC 6475", "NGC 6530",
    "NGC 6603", "NGC 6611", "NGC 6705",
)
PLANETARY_NEBULAE = (
    "PN G349.5+01.0", "PN G002.4+05.8", "PN G008.0+03.9",
    "PN G009.4-05.0", "PN G010.1+00.7", "PN G025.8-17.9",
)
SUPERNOVA_REMNANTS = (
    "G004.5+06.8", "G006.4-00.1", "G011.2-00.3",
    "G021.8-00.6", "G027.4+00.0", "G034.7-00.4",
)


def build_chart():
    """Build the shared scientific sky and zenith-centred chart."""
    observer = Observer(location="La Ligua", time=LOCAL_TIME)
    sky = CelestialSphere(observer)
    sky.add_milky_way_isophotes()
    sky.add_magellanic_cloud_isophotes("lmc")
    sky.add_magellanic_cloud_isophotes("smc")
    # Keep the catalogue deep enough to retain all constellation-line
    # vertices; the composition detail policy below controls which ordinary
    # stars are visible in this wide-field product.
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
    return sky, FullSkyChart(
        center_alt_deg=90.0,
        center_az_deg=0.0,
        horizon_altitude_deg=0.0,
        horizon_color="#707070",
        horizon_linewidth=0.8,
    )


def furniture(sky, chart, arguments):
    legends = chart_legend_selection(arguments)
    references = "labeled" if arguments.references else "none"
    poles = "visible" if arguments.poles else "none"
    return ChartFurnitureOptions(
        references=ReferenceAnnotations(
            ecliptic=ReferencePlaneAnnotation(
                state=references, label="Ecliptic"
            ),
            galactic_plane=ReferencePlaneAnnotation(
                state=references, label="Galactic plane"
            ),
        ),
        poles=PoleAnnotations(
            celestial=poles,
            ecliptic=poles,
            galactic=poles,
            labels=arguments.pole_labels,
        ),
        footer=FooterOptions(
            application=arguments.credits,
            copyright=("© Fernando Selman" if arguments.credits else None),
        ),
        legends=LegendOptions(
            objects=legends.objects,
            stellar_magnitudes=legends.stellar_magnitudes,
            stellar_counts=legends.stellar_counts,
            context=False,
            context_lines=(
                chart_context_lines(
                    chart,
                    sky,
                    center=arguments.center,
                    grid=arguments.grid,
                )
                + observer_context_lines(
                    sky.observer,
                    location=arguments.location,
                    date=arguments.date,
                    local_time=arguments.local_time,
                    labels=False,
                )
            ),
        ),
    )


def generate(arguments):
    """Generate the selected product matrix and return saved paths."""
    options = chart_product_options(arguments)
    sky, chart = build_chart()
    saved = []
    for product, output in options.outputs(stem="planisphere"):
        detail = (
            None
            if product.style == "cartoon"
            else FixedDetailPolicy(
                ResolvedDetail(star_magnitude_limit=5.0)
            )
        )
        composition = compose_chart(
            chart,
            style=product.style,
            mode=product.mode,
            detail=detail,
            detail_overrides=chart_detail_overrides(arguments),
            style_overrides=chart_style_overrides(arguments),
            furniture=furniture(sky, chart, arguments),
        )
        figure, ax = plt.subplots(figsize=(
            composition.mode.width_inches,
            composition.mode.height_inches,
        ))
        composition.style.configure_axes(
            ax,
            title="La Ligua planisphere — 15 August 2026, 21:00",
        )
        _, path = chart.export(
            sky,
            MatplotlibRenderer(ax),
            output,
            composition=composition,
        )
        plt.close(figure)
        saved.append(path)
    return tuple(saved)


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    add_chart_arguments(value, default_output=DEFAULT_OUTPUT)
    value.add_argument("--credits", action="store_true")
    value.add_argument(
        "--no-center", action="store_false", dest="center",
        help="omit the two chart-center coordinate lines",
    )
    value.add_argument(
        "--no-grid", action="store_false", dest="grid",
        help="omit the coordinate-grid line",
    )
    value.add_argument("--location", action="store_true")
    value.add_argument("--date", action="store_true")
    value.add_argument("--local-time", action="store_true")
    return value


def main():
    for path in generate(parser().parse_args()):
        print(path)


if __name__ == "__main__":
    main()
