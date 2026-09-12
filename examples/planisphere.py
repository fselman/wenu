"""Generate the canonical visible-sky planisphere for La Ligua."""

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
DEFAULT_OUTPUT = Path("output/examples/planisphere")


def chart_view(arguments, *, sky=None):
    configuration = chart_configuration(arguments)
    sky = generate_celestial_sphere() if sky is None else sky
    observer = Observer(location="La Ligua", time=LOCAL_TIME)
    mask = tuple(
        name for group in arguments.constellation_mask for name in group
    ) or None
    return get_chart_view(
        sky, observer, family="planisphere", projection="stereographic",
        constellation_mask=mask,
        configuration=configuration,
    )


def generate(arguments):
    view = chart_view(arguments)
    furniture = chart_cli_furniture(
        arguments,
        language="es",
        copyright="© Fernando Selman",
        symbol_labels=(("open_cluster", "Cúmulo abierto"),
                       ("globular_cluster", "Cúmulo globular"),
                       ("planetary_nebula", "Nebulosa planetaria"),
                       ("supernova_remnant", "Remanente de supernova"),
                       ("galaxy", "Galaxia"), ("milky_way", "Vía Láctea")),
        stellar_title="Estrellas",
        configuration=getattr(view, "configuration", None),
        family=getattr(view, "family", None))
    try:
        results = draw_chart_view_from_arguments(
            view, arguments, stem="planisphere",
            furniture=furniture,
            title="Planisferio de La Ligua — 15 de agosto de 2026, 21:00",
            language="es")
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
