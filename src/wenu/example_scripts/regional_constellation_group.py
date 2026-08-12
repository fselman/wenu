"""Generate a regional chart for a packaged constellation group."""

import argparse
from pathlib import Path

from wenu import (
    FixedDetailPolicy, Observer, ResolvedDetail, add_chart_cli_arguments,
    chart_cli_furniture, draw_chart_view_from_arguments,
    generate_celestial_sphere, get_chart_view,
)

LOCAL_TIME = "2026-08-15 21:00"
DEFAULT_OUTPUT = Path("output/examples/regional-constellation-group")


def chart_view(arguments, *, sky=None):
    sky = generate_celestial_sphere() if sky is None else sky
    observer = Observer(location="La Ligua", time=LOCAL_TIME)
    return get_chart_view(
        sky, observer, family="regional", group=arguments.group,
        field_width_deg=arguments.field_width,
        field_height_deg=arguments.field_height,
        position_angle_deg=arguments.position_angle,
        projection="stereographic",
        mask=(arguments.mask or arguments.group == "sgr-sco-oph-ser"),
    )


def generate(arguments):
    view = chart_view(arguments)
    try:
        results = draw_chart_view_from_arguments(
            view, arguments, stem=f"regional-{view.constellations.key}",
            product_details={"atlas": FixedDetailPolicy(
                ResolvedDetail(star_magnitude_limit=6.5))},
            furniture=chart_cli_furniture(
                arguments, copyright="© Fernando Selman"),
            title=view.constellations.display_name)
        return tuple(result.output for result in results)
    finally:
        view.observer.close()


def parser():
    value = add_chart_cli_arguments(argparse.ArgumentParser(description=__doc__),
                                    default_output=DEFAULT_OUTPUT)
    value.add_argument("--group", default="summer-triangle")
    value.add_argument("--mask", action="store_true")
    value.add_argument("--field-width", type=float)
    value.add_argument("--field-height", type=float)
    value.add_argument("--position-angle", type=float, default=0.0)
    return value


if __name__ == "__main__":
    for path in generate(parser().parse_args()):
        print(path)
