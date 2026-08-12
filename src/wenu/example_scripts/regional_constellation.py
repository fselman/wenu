"""Generate a regional chart for one IAU constellation."""

import argparse
from pathlib import Path

from wenu import (
    AdaptiveDetailPolicy, Observer, add_chart_cli_arguments,
    add_constellation_subject_arguments, chart_cli_furniture,
    chart_constellation_subject, draw_chart_view_from_arguments,
    generate_celestial_sphere, get_chart_view,
)

LOCAL_TIME = "2026-08-15 21:00"
DEFAULT_OUTPUT = Path("output/examples/regional-constellation")


def chart_view(arguments, *, sky=None):
    sky = generate_celestial_sphere() if sky is None else sky
    observer = Observer(location="La Ligua", time=LOCAL_TIME)
    subject = chart_constellation_subject(arguments)
    return get_chart_view(
        sky, observer, family="regional", **subject.view_arguments(),
        field_width_deg=arguments.field_width,
        field_height_deg=arguments.field_height,
        position_angle_deg=arguments.position_angle,
        projection="stereographic", mask=arguments.mask,
    )


def generate(arguments):
    view = chart_view(arguments)
    try:
        results = draw_chart_view_from_arguments(
            view, arguments, stem=f"regional-{view.constellations.key}",
            product_details={"atlas": AdaptiveDetailPolicy(
                star_magnitude_limit=6.5)},
            furniture=chart_cli_furniture(
                arguments, copyright="© Fernando Selman"),
            title=view.constellations.display_name)
        return tuple(result.output for result in results)
    finally:
        view.observer.close()


def parser():
    value = add_chart_cli_arguments(argparse.ArgumentParser(description=__doc__),
                                    default_output=DEFAULT_OUTPUT)
    add_constellation_subject_arguments(
        value, default_constellations=("Cru",))
    value.add_argument("--mask", action="store_true")
    value.add_argument("--field-width", type=float, default=18.0)
    value.add_argument("--field-height", type=float, default=16.0)
    value.add_argument("--position-angle", type=float, default=0.0)
    return value


if __name__ == "__main__":
    for path in generate(parser().parse_args()):
        print(path)
