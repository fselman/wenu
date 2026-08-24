"""Installed command-line interface for ordinary Wenu chart generation."""

from __future__ import annotations

import argparse
from importlib.resources import files
from pathlib import Path

from wenu.charts.command_line import (
    add_chart_cli_arguments,
    draw_chart_view_from_arguments,
)
from wenu.charts.request import CHART_LANGUAGES
from wenu.charts.subject_arguments import (
    add_constellation_subject_arguments,
    chart_constellation_subject,
)
from wenu.charts.view import get_chart_view
from wenu.configuration import (
    load_configuration,
    translate_configuration_defaults,
)
from wenu.observer import Observer
from wenu.sky.maximal_sphere import generate_celestial_sphere


def _optional(value):
    return None if value == "none" else value


def _add_observer_arguments(parser):
    parser.add_argument("--observer-location")
    parser.add_argument("--observer-time")
    parser.add_argument("--observer-latitude", type=float)
    parser.add_argument("--observer-longitude", type=float)
    parser.add_argument("--observer-height", type=float)
    parser.add_argument("--observer-timezone")
    parser.add_argument("--ephemeris")
    parser.add_argument("--data-directory", type=Path)


def _add_common_arguments(parser, *, family):
    add_chart_cli_arguments(
        parser,
        default_output=Path("output/wenu-chart") / family,
        default_equatorial_grid=family != "binocular",
    )
    _add_observer_arguments(parser)
    parser.add_argument("--title")
    parser.add_argument("--language", choices=CHART_LANGUAGES)


def _add_mask_argument(parser):
    parser.add_argument("--mask", action="store_true", default=None)


def parser():
    """Return the complete installed ``wenu_chart`` parser."""
    value = argparse.ArgumentParser(
        prog="wenu_chart",
        description="Generate publication-quality static sky charts.",
    )
    commands = value.add_subparsers(dest="command", required=True)

    all_sky = commands.add_parser("all-sky")
    _add_common_arguments(all_sky, family="all-sky")
    add_constellation_subject_arguments(all_sky)
    _add_mask_argument(all_sky)

    planisphere = commands.add_parser("planisphere")
    _add_common_arguments(planisphere, family="planisphere")
    add_constellation_subject_arguments(planisphere)
    _add_mask_argument(planisphere)

    regional = commands.add_parser("regional")
    _add_common_arguments(regional, family="regional")
    add_constellation_subject_arguments(regional)
    _add_mask_argument(regional)
    regional.add_argument("--field-width", type=float)
    regional.add_argument("--field-height", type=float)
    regional.add_argument(
        "--center-altitude", type=float,
        help="fixed observer-local chart-center altitude in degrees",
    )
    regional.add_argument(
        "--center-azimuth", type=float,
        help="fixed observer-local chart-center azimuth in degrees",
    )
    orientation = regional.add_mutually_exclusive_group()
    orientation.add_argument(
        "--orientation",
        choices=("celestial-north-up", "zenith-up"),
        help="named chart orientation policy",
    )
    orientation.add_argument(
        "--position-angle", type=float,
        help="literal chart rotation in degrees",
    )

    circumpolar = commands.add_parser("circumpolar")
    _add_common_arguments(circumpolar, family="circumpolar")
    _add_mask_argument(circumpolar)
    circumpolar.add_argument("--limiting-declination", type=float)
    circumpolar.add_argument("--pole", choices=("north", "south"))

    binocular = commands.add_parser("binocular")
    _add_common_arguments(binocular, family="binocular")
    _add_mask_argument(binocular)
    binocular.add_argument("--target")
    binocular.add_argument("--ra", type=float)
    binocular.add_argument("--dec", type=float)
    binocular.add_argument("--display-name")
    binocular.add_argument("--field-diameter", type=float)
    binocular_orientation = binocular.add_mutually_exclusive_group()
    binocular_orientation.add_argument(
        "--orientation",
        choices=("celestial-north-up", "zenith-up"),
    )
    binocular_orientation.add_argument("--position-angle", type=float)

    defaults = commands.add_parser(
        "defaults",
        help="print or write the packaged authoritative TOML defaults",
    )
    defaults.add_argument(
        "--write",
        type=Path,
        metavar="PATH",
        help="write an editable copy of the authoritative TOML defaults",
    )
    return value


def _configured_subject(values, family):
    name = family.replace("-", "_")
    subject = values["subjects"][name]
    kind = subject["kind"]
    if kind == "none":
        return {}
    if kind == "target":
        return {"target": subject["target"]}
    if kind == "constellations":
        result = {"constellations": tuple(subject["constellations"])}
        group = _optional(subject.get("group", "none"))
        if group is not None:
            result = {"group": group}
        return result
    raise ValueError(f"Unsupported configured subject kind {kind!r}.")


def _subject_arguments(arguments, values):
    family = arguments.command
    if family in {"all-sky", "planisphere", "regional"}:
        subject = chart_constellation_subject(arguments, required=False)
        if subject is not None:
            return subject.view_arguments()
        configured_family = (
            "regional_single" if family == "regional" else family
        )
        return _configured_subject(values, configured_family)
    if family == "binocular":
        explicit = any(
            getattr(arguments, name) is not None
            for name in ("target", "ra", "dec", "display_name")
        )
        if explicit:
            return {
                "target": arguments.target,
                "ra_deg": arguments.ra,
                "dec_deg": arguments.dec,
                "display_name": arguments.display_name,
            }
        return _configured_subject(values, family)
    return {}


def _observer(arguments, values):
    configured = values["observer"]
    latitude = arguments.observer_latitude
    longitude = arguments.observer_longitude
    if (latitude is None) != (longitude is None):
        raise ValueError(
            "--observer-latitude and --observer-longitude must be used "
            "together."
        )
    explicit_coordinates = latitude is not None or longitude is not None
    options = {
        "location": (
            None
            if explicit_coordinates
            else arguments.observer_location or configured["location"]
        ),
        "time": arguments.observer_time or configured["time"],
        "lat_deg": latitude,
        "lon_deg": longitude,
        "elevation_m": (
            arguments.observer_height
            if arguments.observer_height is not None
            else _optional(configured["elevation"])
        ),
        "timezone_name": (
            arguments.observer_timezone
            or _optional(configured["timezone"])
        ),
        "ephemeris_name": (
            arguments.ephemeris or _optional(configured["ephemeris"])
        ),
        "data_directory": (
            arguments.data_directory
            or _optional(configured["data_directory"])
        ),
    }
    return Observer(**{
        name: item for name, item in options.items() if item is not None
    })


def _view_arguments(arguments):
    family = arguments.command
    common = {"mask": arguments.mask}
    if family == "regional":
        return {
            **common,
            "field_width_deg": arguments.field_width,
            "field_height_deg": arguments.field_height,
            "center_altitude_deg": arguments.center_altitude,
            "center_azimuth_deg": arguments.center_azimuth,
            "orientation": arguments.orientation,
            "position_angle_deg": arguments.position_angle,
        }
    if family == "circumpolar":
        return {
            **common,
            "limiting_declination_deg": arguments.limiting_declination,
            "pole": arguments.pole,
        }
    if family == "binocular":
        return {
            **common,
            "field_diameter_deg": arguments.field_diameter,
            "orientation": arguments.orientation,
            "position_angle_deg": arguments.position_angle,
        }
    return common


def _stem(view):
    if view.family == "regional" and view.constellations is not None:
        return f"regional-{view.constellations.key}"
    if view.family == "binocular" and view.target is not None:
        return f"binocular-{view.target.key}"
    return view.family.replace("_", "-")


def generate(arguments):
    """Generate every requested product through Wenu's ordinary facade."""
    values = load_configuration(arguments.config)
    configuration = translate_configuration_defaults(values)
    observer = _observer(arguments, values)
    try:
        sky = generate_celestial_sphere()
        view = get_chart_view(
            sky,
            observer,
            family=arguments.command.replace("-", "_"),
            configuration=configuration,
            **_subject_arguments(arguments, values),
            **_view_arguments(arguments),
        )
        results = draw_chart_view_from_arguments(
            view,
            arguments,
            stem=_stem(view),
            title=arguments.title,
            language=arguments.language,
        )
        return tuple(result.output for result in results)
    finally:
        observer.close()


def packaged_defaults_text():
    """Return the installed authoritative TOML document verbatim."""
    return files("wenu.configuration").joinpath("defaults.toml").read_text(
        encoding="utf-8"
    )


def write_defaults_template(path):
    """Write the packaged defaults byte-for-byte to ``path``."""
    destination = Path(path)
    destination.write_bytes(packaged_defaults_text().encode("utf-8"))
    return destination


def main(argv=None):
    """Run the installed command and return a process status."""
    arguments = parser().parse_args(argv)
    if arguments.command == "defaults":
        if arguments.write is None:
            print(packaged_defaults_text(), end="")
        else:
            print(write_defaults_template(arguments.write))
        return 0
    for output in generate(arguments):
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
