"""Generate a canonical regional chart for one IAU constellation."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from wenu import (
    CelestialSphere, ChartFurnitureOptions, FooterOptions,
    FixedDetailPolicy, LegendOptions,
    MatplotlibRenderer, Observer, PoleAnnotations, ReferenceAnnotations,
    ReferencePlaneAnnotation, RegionalChart, ResolvedDetail,
    add_chart_product_arguments,
    chart_product_options, compose_chart,
)


DEFAULT_OUTPUT = Path("output/examples/regional-constellation")


def build_chart(constellation="Cru", *, mask=False):
    selected = (constellation,)
    observer = Observer(location="La Ligua", time="2026-08-15 21:00")
    sky = CelestialSphere(observer)
    sky.add_milky_way_isophotes()
    sky.add_stars(catalog="hipparcos", magnitude_limit=6.5)
    sky.add_constellations(system="western", selected=selected)
    sky.add_constellation_boundaries(boundaries="iau", constellations=selected)
    sky.add_equatorial_grid(
        ra=tuple(range(0, 360, 15)), dec=tuple(range(-75, 76, 15)),
        frame="fk5", equinox="J2000",
    )
    chart = RegionalChart.from_constellations(
        sky, selected, angular_radius_deg=22.0, aspect_ratio=1.15,
        north_up=True, label_selection=selected,
        outside_mask_constellations=(selected if mask else None),
    )
    return sky, chart


def furniture(arguments):
    state = "labeled" if arguments.references else "none"
    poles = "visible" if arguments.poles else "none"
    return ChartFurnitureOptions(
        references=ReferenceAnnotations(
            ecliptic=ReferencePlaneAnnotation(state=state, label="Ecliptic"),
            galactic_plane=ReferencePlaneAnnotation(state=state, label="Galactic plane"),
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
        legends=LegendOptions(stellar_counts=arguments.star_counts),
    )


def generate(arguments):
    options = chart_product_options(arguments)
    sky, chart = build_chart(arguments.constellation, mask=arguments.mask)
    saved = []
    stem = f"regional-{arguments.constellation.lower()}"
    for product, output in options.outputs(stem=stem):
        detail = (
            None
            if product.style == "cartoon"
            else FixedDetailPolicy(
                ResolvedDetail(star_magnitude_limit=6.5)
            )
        )
        composition = compose_chart(
            chart, style=product.style, mode=product.mode,
            detail=detail,
            furniture=furniture(arguments),
        )
        figure, ax = plt.subplots(figsize=(composition.mode.width_inches, composition.mode.height_inches))
        composition.style.configure_axes(ax, title=f"{arguments.constellation} — IAU constellation region")
        _, path = chart.export(sky, MatplotlibRenderer(ax), output, composition=composition)
        plt.close(figure)
        saved.append(path)
    return tuple(saved)


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    add_chart_product_arguments(value, default_output=DEFAULT_OUTPUT)
    value.add_argument("--constellation", default="Cru")
    value.add_argument("--mask", action="store_true")
    value.add_argument("--references", action="store_true")
    value.add_argument("--poles", action="store_true")
    value.add_argument(
        "--pole-labels",
        action="store_true",
        help="label visible pole crosses with their abbreviations",
    )
    value.add_argument("--credits", action="store_true")
    value.add_argument("--star-counts", action="store_true")
    return value


def main():
    for path in generate(parser().parse_args()):
        print(path)


if __name__ == "__main__":
    main()
