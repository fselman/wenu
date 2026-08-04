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
    add_chart_arguments,
    chart_context_lines, chart_detail_overrides,
    chart_legend_selection, chart_product_options, chart_style_overrides,
    compose_chart,
    observer_context_lines,
)


DEFAULT_OUTPUT = Path("output/examples/regional-constellation")


def build_chart(
    constellation="Cru",
    *,
    mask=False,
    field_width_deg=18.0,
    field_height_deg=16.0,
    position_angle_deg=None,
):
    selected = (constellation,)
    observer = Observer(location="La Ligua", time="2026-08-15 21:00")
    sky = CelestialSphere(observer)
    sky.add_milky_way_isophotes()
    sky.add_stars(catalog="hipparcos", magnitude_limit=6.5)
    sky.add_constellations(system="western", selected=selected)
    sky.add_constellation_boundaries(boundaries="iau", constellations=selected)
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
    chart = RegionalChart.from_constellations(
        sky,
        selected,
        angular_radius_deg=field_height_deg / 2.0,
        aspect_ratio=field_width_deg / field_height_deg,
        north_up=position_angle_deg is None,
        position_angle_deg=(
            0.0 if position_angle_deg is None else position_angle_deg
        ),
        label_selection=selected,
        outside_mask_constellations=(selected if mask else None),
    )
    return sky, chart


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
    sky, chart = build_chart(
        arguments.constellation,
        mask=arguments.mask,
        field_width_deg=arguments.field_width,
        field_height_deg=arguments.field_height,
        position_angle_deg=arguments.position_angle,
    )
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
            detail_overrides=chart_detail_overrides(arguments),
            style_overrides=chart_style_overrides(arguments),
            furniture=furniture(sky, chart, arguments),
        )
        figure, ax = plt.subplots(figsize=(composition.mode.width_inches, composition.mode.height_inches))
        composition.style.configure_axes(ax, title=f"{arguments.constellation} — IAU constellation region")
        _, path = chart.export(sky, MatplotlibRenderer(ax), output, composition=composition)
        plt.close(figure)
        saved.append(path)
    return tuple(saved)


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    add_chart_arguments(value, default_output=DEFAULT_OUTPUT)
    value.add_argument("--constellation", default="Cru")
    value.add_argument("--mask", action="store_true")
    value.add_argument(
        "--field-width", type=float, default=18.0,
        help="horizontal angular field in degrees (default: 18)",
    )
    value.add_argument(
        "--field-height", type=float, default=16.0,
        help="vertical angular field in degrees (default: 16)",
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
