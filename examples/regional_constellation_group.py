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
    add_chart_arguments,
    chart_context_lines, chart_detail_overrides,
    chart_legend_selection, chart_product_options, chart_style_overrides,
    compose_chart,
    observer_context_lines,
)


DEFAULT_OUTPUT = Path("output/examples/regional-constellation-group")
GROUPS = {
    "summer-triangle": {
        "lines": ("Cyg", "Lyr", "Vul", "Sge", "Aql"),
        "boundaries": ("Cyg", "Lyr", "Vul", "Sge", "Aql"),
        "labels": ("Cyg", "Lyr", "Vul", "Sge", "Aql"),
        "field_width": 143.52,
        "field_height": 104.0,
        "title": "The Summer Triangle — Cygnus, Lyra, Vulpecula, Sagitta, and Aquila",
        "open_clusters": ("NGC 6709", "NGC 6811", "NGC 6830", "NGC 6885", "NGC 6940"),
        "planetary_nebulae": ("PN G060.8-03.6", "PN G063.1+13.9"),
        "supernova_remnants": ("G065.3+05.7", "G074.0-08.5", "G078.2+02.1"),
    },
    "galactic-center": {
        "lines": ("Sgr", "Sco", "Oph", "Ser1", "Ser2"),
        "boundaries": ("Sgr", "Sco", "Oph", "Ser"),
        "labels": ("Sgr", "Sco", "Oph", "SerCap", "SerCau"),
        "field_width": 90.0,
        "field_height": 90.0,
        "title": "Sagittarius, Scorpius, Ophiuchus, and Serpens",
        "open_clusters": ("NGC 6405", "NGC 6475", "NGC 6530", "NGC 6603", "NGC 6611", "NGC 6705"),
        "planetary_nebulae": ("PN G349.5+01.0", "PN G002.4+05.8", "PN G008.0+03.9", "PN G009.4-05.0", "PN G010.1+00.7", "PN G025.8-17.9"),
        "supernova_remnants": ("G004.5+06.8", "G006.4-00.1", "G011.2-00.3", "G021.8-00.6", "G027.4+00.0", "G034.7-00.4"),
    },
    "sgr-sco-oph-ser": {
        "lines": ("Sgr", "Sco", "Oph", "Ser1", "Ser2"),
        "boundaries": ("Sgr", "Sco", "Oph", "Ser"),
        "labels": ("Sgr", "Sco", "Oph", "SerCap", "SerCau"),
        "field_width": 90.0,
        "field_height": 90.0,
        "title": "Sagittarius, Scorpius, Ophiuchus, and Serpens",
        "open_clusters": ("NGC 6405", "NGC 6475", "NGC 6530", "NGC 6603", "NGC 6611", "NGC 6705"),
        "planetary_nebulae": ("PN G349.5+01.0", "PN G002.4+05.8", "PN G008.0+03.9", "PN G009.4-05.0", "PN G010.1+00.7", "PN G025.8-17.9"),
        "supernova_remnants": ("G004.5+06.8", "G006.4-00.1", "G011.2-00.3", "G021.8-00.6", "G027.4+00.0", "G034.7-00.4"),
        "mask": True,
    },
}


def build_chart(
    group_name,
    *,
    mask=False,
    field_width_deg=None,
    field_height_deg=None,
    position_angle_deg=None,
):
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
        dec=tuple(value for value in range(-75, 76, 15) if value),
        frame="fk5", equinox="J2000",
    )
    sky.add_ecliptic_grid(
        longitude=tuple(range(0, 360, 15)),
        latitude=tuple(value for value in range(-75, 76, 15) if value),
        equinox="J2000",
        include_ecliptic=False,
    )
    sky.add_galactic_grid(
        longitude=tuple(range(0, 360, 15)),
        latitude=tuple(value for value in range(-75, 76, 15) if value),
        include_plane=False,
    )
    sky.add_altaz_grid(
        azimuth=tuple(range(0, 360, 15)),
        altitude=tuple(range(15, 90, 15)),
        include_horizon=False,
    )
    chart = RegionalChart.from_constellations(
        sky,
        group["lines"],
        angular_radius_deg=(
            group["field_height"]
            if field_height_deg is None
            else field_height_deg
        ) / 2.0,
        aspect_ratio=(
            group["field_width"]
            if field_width_deg is None
            else field_width_deg
        ) / (
            group["field_height"]
            if field_height_deg is None
            else field_height_deg
        ),
        north_up=position_angle_deg is None,
        position_angle_deg=(
            0.0 if position_angle_deg is None else position_angle_deg
        ),
        label_selection=group["labels"],
        outside_mask_constellations=(group["boundaries"] if mask else None),
    )
    return sky, chart, group["title"]


def furniture(sky, chart, arguments):
    legends = chart_legend_selection(arguments)
    def reference(name):
        return "labeled" if name in arguments.grid_references else "none"
    poles = "visible" if arguments.poles else "none"
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
    options = chart_product_options(arguments)
    group = GROUPS[arguments.group]
    sky, chart, title = build_chart(
        arguments.group,
        mask=(arguments.mask or group.get("mask", False)),
        field_width_deg=arguments.field_width,
        field_height_deg=arguments.field_height,
        position_angle_deg=arguments.position_angle,
    )
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
            detail_overrides=chart_detail_overrides(arguments),
            style_overrides=chart_style_overrides(arguments),
            furniture=furniture(sky, chart, arguments),
        )
        figure, ax = plt.subplots(figsize=(composition.mode.width_inches, composition.mode.height_inches))
        composition.style.configure_axes(ax, title=title)
        _, path = chart.export(sky, MatplotlibRenderer(ax), output, composition=composition)
        plt.close(figure)
        saved.append(path)
    return tuple(saved)


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    add_chart_arguments(value, default_output=DEFAULT_OUTPUT)
    value.add_argument("--group", choices=tuple(GROUPS), default="summer-triangle")
    value.add_argument("--mask", action="store_true")
    value.add_argument(
        "--field-width", type=float,
        help="horizontal angular field in degrees",
    )
    value.add_argument(
        "--field-height", type=float,
        help="vertical angular field in degrees",
    )
    value.add_argument(
        "--position-angle", type=float,
        help="chart rotation in degrees; the default keeps celestial north up",
    )
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
