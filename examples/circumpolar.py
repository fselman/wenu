"""Generate the canonical southern circumpolar chart."""

import argparse
from pathlib import Path

from wenu import (
    AdaptiveDetailPolicy, FixedDetailPolicy, Observer, ResolvedDetail,
    add_chart_cli_arguments,
    chart_cli_furniture, draw_chart_view_from_arguments,
    generate_celestial_sphere, get_chart_view,
)

LOCAL_TIME = "2026-08-15 21:00"
LIMITING_DECLINATION_DEG = -69.75
DEFAULT_OUTPUT = Path("output/examples/circumpolar")


def chart_view(arguments, *, sky=None):
    sky = generate_celestial_sphere() if sky is None else sky
    observer = Observer(location="La Ligua", time=LOCAL_TIME)
    return get_chart_view(
        sky, observer, family="circumpolar", pole="south",
        limiting_declination_deg=arguments.limiting_declination,
        projection="stereographic", position_angle_deg=0.0, mask=False,
    )


def generate(arguments):
    view = chart_view(arguments)
    details = {
        "atlas": AdaptiveDetailPolicy(star_magnitude_limit=6.5),
        "cartoon": FixedDetailPolicy(ResolvedDetail(
            star_magnitude_limit=3.0,
            enabled_layers=frozenset({"stars", "constellation_lines",
                                      "equatorial_grid", "milky_way",
                                      "magellanic_clouds"}),
            constellation_star_mode="selected")),
    }
    try:
        results = draw_chart_view_from_arguments(
            view, arguments, stem="circumpolar", product_details=details,
            furniture=chart_cli_furniture(
                arguments, pole_selection="both", copyright="© Fernando Selman"),
            title="Southern circumpolar sky — −69.75° boundary crossing the LMC")
        return tuple(result.output for result in results)
    finally:
        view.observer.close()


def parser():
    value = add_chart_cli_arguments(
        argparse.ArgumentParser(description=__doc__),
        default_output=DEFAULT_OUTPUT)
    value.add_argument("--limiting-declination", type=float,
                       default=LIMITING_DECLINATION_DEG)
    return value


if __name__ == "__main__":
    for path in generate(parser().parse_args()):
        print(path)
