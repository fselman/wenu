"""Generate a regional chart for one IAU constellation."""

import argparse
from pathlib import Path

from wenu import (
    Observer, add_chart_cli_arguments,
    add_constellation_subject_arguments, chart_cli_furniture,
    chart_configuration,
    chart_constellation_subject, draw_chart_view_from_arguments,
    generate_celestial_sphere, get_chart_view,
)

LOCAL_TIME = "2026-08-15 21:00"
DEFAULT_OUTPUT = Path("output/examples/regional-constellation")


def chart_view(arguments, *, sky=None):
    configuration = chart_configuration(arguments)
    sky = generate_celestial_sphere() if sky is None else sky
    observer = Observer(location="La Ligua", time=LOCAL_TIME)
    subject = chart_constellation_subject(arguments)
    orientation = arguments.orientation or (
        None if arguments.position_angle is not None else "celestial-north-up")
    return get_chart_view(
        sky, observer, family="regional", **subject.view_arguments(),
        field_width_deg=arguments.field_width,
        field_height_deg=arguments.field_height,
        orientation=orientation,
        position_angle_deg=arguments.position_angle,
        projection="stereographic", mask=arguments.mask,
        configuration=configuration,
    )


def generate(arguments):
    view = chart_view(arguments)
    try:
        results = draw_chart_view_from_arguments(
            view, arguments, stem=f"regional-{view.constellations.key}",
            furniture=chart_cli_furniture(
                arguments, copyright="© Fernando Selman",
                configuration=getattr(view, "configuration", None),
                family=getattr(view, "family", None)),
            title=view.constellations.display_name)
        return tuple(result.output for result in results)
    finally:
        view.observer.close()


def parser():
    value = add_chart_cli_arguments(argparse.ArgumentParser(description=__doc__),
                                    default_output=DEFAULT_OUTPUT)
    add_constellation_subject_arguments(
        value, default_constellations=("Cru",))
    value.add_argument("--mask", action="store_true", default=None)
    value.add_argument("--field-width", type=float)
    value.add_argument("--field-height", type=float)
    orientation = value.add_mutually_exclusive_group()
    orientation.add_argument(
        "--orientation", choices=("celestial-north-up", "zenith-up"))
    orientation.add_argument("--position-angle", type=float)
    return value


if __name__ == "__main__":
    for path in generate(parser().parse_args()):
        print(path)
