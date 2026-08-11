"""Generate canonical binocular charts centered on a selected object.

Examples:
    python examples/binocular_object.py --target centaurus-a
    python examples/binocular_object.py --target omega-centauri --all-products
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from wenu import (
    ChartContextOptions,
    ChartFrameRequest,
    ChartFurnitureOptions,
    ChartObserverRequest,
    ChartProductCompositionOptions,
    ChartProductOptions,
    ChartRequest,
    ChartStyleOverrides,
    ChartSubjectRequest,
    DetailOverrides,
    FixedDetailPolicy,
    FooterOptions,
    LegendOptions,
    PoleAnnotations,
    ReferenceAnnotations,
    ReferencePlaneAnnotation,
    ResolvedDetail,
    StellarMagnitudeSizing,
    add_chart_arguments,
    build_chart_request,
    chart_detail_overrides,
    chart_legend_selection,
    chart_product_options,
    chart_style_overrides,
    generate_chart_request,
    resolve_target,
)


LOCAL_TIME = "2026-05-15 22:00"
DEFAULT_FIELD_DIAMETER_DEG = 6.5
STAR_MAGNITUDE_LIMIT = 11.0
BINOCULAR_STELLAR_SIZING = StellarMagnitudeSizing(
    reference="limiting_magnitude",
    scale=1.0,
    exponent=0.20,
    minimum_area=1.0,
    maximum_area=40.0,
)
DEFAULT_OUTPUT = Path("output/examples/binocular-object")

CARTOON_CONTENT_LAYERS = frozenset({
    "stars",
    "constellation_lines",
    "galaxies",
    "globular_clusters",
})
ATLAS_CONTENT_LAYERS = frozenset({
    "stars",
    "galaxies",
    "globular_clusters",
})


def _product_compositions(options, target, arguments=None):
    style_overrides = (
        ChartStyleOverrides()
        if arguments is None
        else chart_style_overrides(arguments)
    )
    style_overrides = replace(
        style_overrides,
        stellar_magnitude_sizing=BINOCULAR_STELLAR_SIZING,
    )
    extended_samples = (
        73 if "globular_clusters" in target.required_families else 97
    )
    result = []
    for product in options.products:
        if product.style == "cartoon":
            detail = FixedDetailPolicy(ResolvedDetail(
                star_magnitude_limit=STAR_MAGNITUDE_LIMIT,
                galaxy_magnitude_limit=11.0,
                extended_object_samples=extended_samples,
                enabled_layers=(
                    CARTOON_CONTENT_LAYERS | target.required_families
                ),
                constellation_star_mode="selected",
            ))
        else:
            detail = FixedDetailPolicy(ResolvedDetail(
                star_magnitude_limit=STAR_MAGNITUDE_LIMIT,
                galaxy_magnitude_limit=11.0,
                extended_object_samples=extended_samples,
                enabled_layers=(
                    ATLAS_CONTENT_LAYERS | target.required_families
                ),
            ))
        result.append(ChartProductCompositionOptions(
            product=product,
            detail=detail,
            style_overrides=style_overrides,
        ))
    return tuple(result)


def _furniture(arguments):
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
        ),
        context=ChartContextOptions(
            center=arguments.center,
            grid=arguments.grid,
            location=arguments.location,
            date=arguments.date,
            local_time=arguments.local_time,
        ),
    )


def chart_request(
    target_key="centaurus-a",
    field_diameter_deg=DEFAULT_FIELD_DIAMETER_DEG,
    *,
    arguments=None,
):
    """Return the complete declarative request for one binocular field."""
    subject = ChartSubjectRequest(target=target_key)
    target = resolve_target(subject)
    options = (
        ChartProductOptions(output=DEFAULT_OUTPUT)
        if arguments is None
        else chart_product_options(arguments)
    )
    identifier = target.primary_identifier
    title = target.display_name if identifier is None else (
        f"{target.display_name} ({identifier})"
    )
    title += f" — {field_diameter_deg:g}° binocular field"
    return ChartRequest(
        observer=ChartObserverRequest(
            location="La Ligua",
            time=LOCAL_TIME,
        ),
        family="binocular",
        subject=subject,
        frame=ChartFrameRequest(field_diameter_deg=field_diameter_deg),
        product=options,
        detail=(
            chart_detail_overrides(arguments)
            if arguments is not None
            else DetailOverrides()
        ),
        furniture=(
            _furniture(arguments)
            if arguments is not None
            else ChartFurnitureOptions()
        ),
        product_compositions=_product_compositions(
            options, target, arguments
        ),
        title=title,
    )


def build_chart(
    target_key="centaurus-a",
    field_diameter_deg=DEFAULT_FIELD_DIAMETER_DEG,
    *,
    sky=None,
):
    """Build or reuse the selected-object sky and binocular chart."""
    build = build_chart_request(
        chart_request(target_key, field_diameter_deg),
        sky=sky,
    )
    return build.sky, build.chart, build.prepared.resolved.target


def generate(arguments):
    """Generate the selected target and product matrix."""
    request = chart_request(
        arguments.target,
        arguments.field_diameter,
        arguments=arguments,
    )
    return generate_chart_request(request).outputs


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    add_chart_arguments(value, default_output=DEFAULT_OUTPUT)
    value.add_argument(
        "--target",
        default="centaurus-a",
        help="packaged catalogue object at the center of the binocular field",
    )
    value.add_argument(
        "--field-diameter",
        type=float,
        default=DEFAULT_FIELD_DIAMETER_DEG,
        help="circular binocular field diameter in degrees",
    )
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
