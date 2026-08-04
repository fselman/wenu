"""Generate canonical southern circumpolar charts crossing the LMC.

Examples:
    python examples/circumpolar.py --style atlas --mode print
    python examples/circumpolar.py --all-products --output output/circumpolar
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
    CircumpolarChart,
    FixedDetailPolicy,
    FooterOptions,
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
LIMITING_DECLINATION_DEG = -69.75
DEFAULT_OUTPUT = Path("output/examples/circumpolar")
OPEN_CLUSTERS = (
    "Melotte 25", "IC 2391", "IC 2602",
    "NGC 2516", "NGC 3532", "NGC 4755",
)
PLANETARY_NEBULAE = (
    "PN G036.1-57.1", "PN G261.0+32.0",
)
SUPERNOVA_REMNANTS = (
    "G263.9-03.3", "G292.0+01.8",
    "G296.5+10.0", "G315.4-02.3",
)
CARTOON_CONTENT_LAYERS = frozenset({
    "stars",
    "constellation_lines",
    "equatorial_grid",
    "milky_way",
    "magellanic_clouds",
})


def build_chart():
    """Build the polar sky and declination-limited chart."""
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
        dec=(-85, -80, -75),
        frame="fk5",
        equinox="J2000",
        samples=1441,
        meridian_dec_min=-75.0,
        meridian_dec_max=90.0,
    )
    sky.add_ecliptic_grid(
        longitude=tuple(range(0, 360, 30)),
        latitude=tuple(value for value in range(-75, 76, 15) if value),
        equinox="J2000",
        samples=1441,
        include_ecliptic=False,
    )
    sky.add_galactic_grid(
        longitude=tuple(range(0, 360, 30)),
        latitude=tuple(value for value in range(-75, 76, 15) if value),
        samples=1441,
        include_plane=False,
    )
    chart = CircumpolarChart(
        observer,
        limiting_declination_deg=LIMITING_DECLINATION_DEG,
        pole="south",
        position_angle_deg=0.0,
    )
    return sky, chart


def furniture(sky, chart, arguments):
    legends = chart_legend_selection(arguments)
    def reference(name):
        return "labeled" if name in arguments.grid_references else "none"
    poles = "both" if arguments.poles else "none"
    return ChartFurnitureOptions(
        references=ReferenceAnnotations(
            celestial_equator=ReferencePlaneAnnotation(
                state=reference("equatorial"), label="Celestial equator"
            ),
            ecliptic=ReferencePlaneAnnotation(
                state=reference("ecliptic"), label="Ecliptic"
            ),
            galactic_plane=ReferencePlaneAnnotation(
                state=reference("galactic"), label="Galactic plane"
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
                    chart, sky,
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
    """Generate the selected circumpolar product matrix."""
    options = chart_product_options(arguments)
    sky, chart = build_chart()
    saved = []
    for product, output in options.outputs(stem="circumpolar"):
        if product.style == "cartoon":
            detail = FixedDetailPolicy(ResolvedDetail(
                star_magnitude_limit=3.0,
                enabled_layers=CARTOON_CONTENT_LAYERS,
                constellation_star_mode="selected",
            ))
        else:
            detail = FixedDetailPolicy(
                ResolvedDetail(star_magnitude_limit=6.5)
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
            title=(
                "Southern circumpolar sky — "
                "−69.75° boundary crossing the LMC"
            ),
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
        help="omit chart-center coordinate context",
    )
    value.add_argument(
        "--no-grid", action="store_false", dest="grid",
        help="omit coordinate-grid context",
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
