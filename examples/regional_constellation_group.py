"""Generate a canonical regional chart for a constellation group."""

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


DEFAULT_OUTPUT = Path("output/examples/regional-constellation-group")
GROUPS = {
    "summer-triangle": {
        "lines": ("Cyg", "Lyr", "Vul", "Sge", "Aql"),
        "boundaries": ("Cyg", "Lyr", "Vul", "Sge", "Aql"),
        "labels": ("Cyg", "Lyr", "Vul", "Sge", "Aql"),
        "radius": 52.0,
        "title": "The Summer Triangle — Cygnus, Lyra, Vulpecula, Sagitta, and Aquila",
        "open_clusters": ("NGC 6709", "NGC 6811", "NGC 6830", "NGC 6885", "NGC 6940"),
        "planetary_nebulae": ("PN G060.8-03.6", "PN G063.1+13.9"),
        "supernova_remnants": ("G065.3+05.7", "G074.0-08.5", "G078.2+02.1"),
    },
    "galactic-center": {
        "lines": ("Sgr", "Sco", "Oph", "Ser1", "Ser2"),
        "boundaries": ("Sgr", "Sco", "Oph", "Ser"),
        "labels": ("Sgr", "Sco", "Oph", "SerCap", "SerCau"),
        "radius": 45.0,
        "title": "Sagittarius, Scorpius, Ophiuchus, and Serpens",
        "open_clusters": ("NGC 6405", "NGC 6475", "NGC 6530", "NGC 6603", "NGC 6611", "NGC 6705"),
        "planetary_nebulae": ("PN G349.5+01.0", "PN G002.4+05.8", "PN G008.0+03.9", "PN G009.4-05.0", "PN G010.1+00.7", "PN G025.8-17.9"),
        "supernova_remnants": ("G004.5+06.8", "G006.4-00.1", "G011.2-00.3", "G021.8-00.6", "G027.4+00.0", "G034.7-00.4"),
    },
}


def build_chart(group_name, *, mask=False):
    group = GROUPS[group_name]
    observer = Observer(location="La Ligua", time="2026-08-15 21:00")
    sky = CelestialSphere(observer)
    sky.add_milky_way_isophotes()
    sky.add_stars(catalog="hipparcos", magnitude_limit=6.5)
    sky.add_galaxies(magnitude_limit=11.0)
    sky.add_open_clusters(selected=group["open_clusters"])
    sky.add_globular_clusters(magnitude_limit=11.0)
    sky.add_supernova_remnants(selected=group["supernova_remnants"])
    sky.add_planetary_nebulae(selected=group["planetary_nebulae"])
    sky.add_constellations(system="western", selected=group["lines"])
    sky.add_constellation_boundaries(
        boundaries="iau", constellations=group["boundaries"]
    )
    sky.add_equatorial_grid(
        ra=tuple(range(0, 360, 15)),
        dec=tuple(range(-75, 76, 15)),
        frame="fk5", equinox="J2000",
    )
    chart = RegionalChart.from_constellations(
        sky,
        group["lines"],
        angular_radius_deg=group["radius"],
        aspect_ratio=1.38,
        north_up=True,
        label_selection=group["labels"],
        outside_mask_constellations=(group["boundaries"] if mask else None),
    )
    return sky, chart, group["title"]


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
    sky, chart, title = build_chart(arguments.group, mask=arguments.mask)
    saved = []
    stem = f"regional-{arguments.group}"
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
        composition.style.configure_axes(ax, title=title)
        _, path = chart.export(sky, MatplotlibRenderer(ax), output, composition=composition)
        plt.close(figure)
        saved.append(path)
    return tuple(saved)


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    add_chart_product_arguments(value, default_output=DEFAULT_OUTPUT)
    value.add_argument("--group", choices=tuple(GROUPS), default="summer-triangle")
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
