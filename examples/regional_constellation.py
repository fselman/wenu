"""Generate a regional chart for one IAU constellation."""

import argparse
from pathlib import Path

from wenu import (
    Observer, add_chart_cli_arguments,
    chart_cli_furniture, chart_configuration,
    draw_chart_view_from_arguments,
    generate_celestial_sphere, get_chart_view,
)
from wenu.charts.center_arguments import resolve_named_center
from wenu.charts.subject_arguments import parse_constellation_list

LOCAL_TIME = "2026-08-15 21:00"
DEFAULT_OUTPUT = Path("output/examples/regional-constellation")


def chart_view(arguments, *, sky=None):
    configuration = chart_configuration(arguments)
    sky = generate_celestial_sphere() if sky is None else sky
    observer = Observer(location="La Ligua", time=LOCAL_TIME)
    center = resolve_named_center(arguments.center_on)
    if not center.is_constellation:
        raise ValueError("This example requires a constellation center.")
    mask = tuple(
        name for group in arguments.constellation_mask for name in group
    ) or None
    orientation = arguments.orientation or (
        None if arguments.position_angle is not None else "celestial-north-up")
    return get_chart_view(
        sky, observer, family="regional",
        constellations=center.value.constellations,
        field_width_deg=arguments.field_width,
        field_height_deg=arguments.field_height,
        orientation=orientation,
        position_angle_deg=arguments.position_angle,
        projection="stereographic", constellation_mask=mask,
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
    value.add_argument("--center-on", default="constellation:Cru")
    value.add_argument(
        "--constellation-mask", action="append",
        type=parse_constellation_list, default=[]
    )
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
