"""Generate the canonical visible-sky planisphere for La Ligua."""

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
DEFAULT_OUTPUT = Path("output/examples/planisphere")


def chart_view(arguments, *, sky=None):
    configuration = chart_configuration(arguments)
    sky = generate_celestial_sphere() if sky is None else sky
    observer = Observer(location="La Ligua", time=LOCAL_TIME)
    subject = chart_constellation_subject(arguments, required=False)
    return get_chart_view(
        sky, observer, family="planisphere", projection="stereographic",
        mask=arguments.mask,
        configuration=configuration,
        **({} if subject is None else subject.view_arguments()),
    )


def generate(arguments):
    view = chart_view(arguments)
    furniture = chart_cli_furniture(
        arguments,
        reference_labels={"equatorial": "Ecuador celeste",
                          "ecliptic": "Eclíptica", "galactic": "Plano galáctico"},
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
    add_constellation_subject_arguments(value)
    value.add_argument("--mask", action="store_true", default=None)
    return value


if __name__ == "__main__":
    for path in generate(parser().parse_args()):
        print(path)
