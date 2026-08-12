"""Generate a binocular chart centered on any packaged object."""

import argparse
from pathlib import Path

from wenu import (
    ChartStyleOverrides, FixedDetailPolicy, Observer, ResolvedDetail,
    StellarMagnitudeSizing, add_chart_cli_arguments,
    draw_chart_view_from_arguments, generate_celestial_sphere, get_chart_view,
)

LOCAL_TIME = "2026-05-15 22:00"
FIELD_DIAMETER_DEG = 6.5
STAR_MAGNITUDE_LIMIT = 11.0
DEFAULT_OUTPUT = Path("output/examples/binocular-object")

def chart_view(arguments, *, sky=None):
    sky = generate_celestial_sphere() if sky is None else sky
    observer = Observer(location="La Ligua", time=LOCAL_TIME)
    return get_chart_view(
        sky, observer, family="binocular", target=arguments.target,
        field_diameter_deg=arguments.field_diameter, projection="stereographic",
        position_angle_deg=0.0, mask=False,
    )


def _details(view):
    samples = 73 if "globular_clusters" in view.target.required_families else 97
    common = dict(star_magnitude_limit=STAR_MAGNITUDE_LIMIT,
                  galaxy_magnitude_limit=11.0, extended_object_samples=samples)
    return {
        "atlas": FixedDetailPolicy(ResolvedDetail(**common)),
        "cartoon": FixedDetailPolicy(ResolvedDetail(
            **common, enabled_layers=frozenset({
                "stars", "constellation_lines", "galaxies",
                "globular_clusters", *view.target.required_families,
            }), constellation_star_mode="selected")),
    }


def generate(arguments):
    view = chart_view(arguments)
    target = view.target
    name = target.display_name + (
        "" if target.primary_identifier is None else f" ({target.primary_identifier})")
    title = f"{name} — {arguments.field_diameter:g}° binocular field"
    sizing = StellarMagnitudeSizing(reference="limiting_magnitude", scale=1.0, exponent=0.20,
                                    minimum_area=1.0, maximum_area=40.0)
    try:
        results = draw_chart_view_from_arguments(
            view, arguments, stem="binocular-object",
            product_details=_details(view), title=title,
            style_overrides=ChartStyleOverrides(stellar_magnitude_sizing=sizing))
        return tuple(result.output for result in results)
    finally:
        view.observer.close()


def parser():
    value = add_chart_cli_arguments(argparse.ArgumentParser(description=__doc__),
                                    default_output=DEFAULT_OUTPUT)
    value.add_argument("--target", default="centaurus-a")
    value.add_argument("--field-diameter", type=float, default=FIELD_DIAMETER_DEG)
    return value


if __name__ == "__main__":
    for path in generate(parser().parse_args()):
        print(path)
