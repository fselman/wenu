"""Generate the canonical Galactic Mollweide all-sky map."""

import argparse
from pathlib import Path

from wenu import (
    Observer, add_chart_cli_arguments,
    chart_cli_furniture, chart_configuration,
    draw_chart_view_from_arguments,
    generate_celestial_sphere, get_chart_view,
)
from wenu.charts.subject_arguments import parse_constellation_list

LOCAL_TIME = "2026-08-15 21:00"
DEFAULT_OUTPUT = Path("output/examples/all-sky")


def chart_view(arguments, *, sky=None):
    configuration = chart_configuration(arguments)
    sky = generate_celestial_sphere() if sky is None else sky
    observer = Observer(location="La Ligua", time=LOCAL_TIME)
    mask = tuple(
        name for group in arguments.constellation_mask for name in group
    ) or None
    return get_chart_view(
        sky, observer, family="all_sky", projection="mollweide",
        coordinate_frame="galactic", position_angle_deg=0.0,
        constellation_mask=mask, configuration=configuration,
    )


def generate(arguments):
    view = chart_view(arguments)
    try:
        results = draw_chart_view_from_arguments(
            view, arguments, stem="all-sky",
            furniture=chart_cli_furniture(
                arguments, copyright="© Fernando Selman",
                configuration=getattr(view, "configuration", None),
                family=getattr(view, "family", None)),
            title="Galactic all-sky map — Mollweide projection")
        return tuple(result.output for result in results)
    finally:
        view.observer.close()


def parser():
    value = add_chart_cli_arguments(argparse.ArgumentParser(description=__doc__),
                                    default_output=DEFAULT_OUTPUT)
    value.add_argument(
        "--constellation-mask", action="append",
        type=parse_constellation_list, default=[]
    )
    return value


if __name__ == "__main__":
    for path in generate(parser().parse_args()):
        print(path)
