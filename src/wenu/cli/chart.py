"""Installed command-line interface for ordinary Wenu chart generation."""

from __future__ import annotations

import argparse
from importlib.resources import files
from pathlib import Path

from wenu.charts.command_line import (
    add_chart_cli_arguments,
    chart_view_requests_from_arguments,
    draw_chart_view_from_arguments,
)
from wenu.charts.center_arguments import (
    parse_degree_angle,
    parse_icrs_ra,
    resolve_named_center,
)
from wenu.charts.object_center import get_object_center
from wenu.charts.request import CHART_LANGUAGES
from wenu.charts.target_resolver import ResolvedTarget
from wenu.charts.sequence import (
    ObserverTimeChartSequenceRequest,
    generate_observer_time_chart_sequence,
)
from wenu.charts.sequence_arguments import (
    add_chart_sequence_arguments,
    chart_sequence_cli_options,
)
from wenu.charts.subject_arguments import parse_constellation_list
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
    add_chart_sequence_arguments(parser)
    parser.add_argument("--title")
    parser.add_argument("--language", choices=CHART_LANGUAGES)
    parser.add_argument(
        "--constellation-system",
        choices=("western",),
        help="constellation vocabulary and line-figure system",
    )
    if family != "circumpolar":
        parser.add_argument(
            "--constellation-mask",
            action="append",
            type=parse_constellation_list,
            default=[],
            metavar="IAU[,IAU...]",
            help="mask outside the selected constellations",
        )


def parser():
    """Return the complete installed ``wenu_chart`` parser."""
    value = argparse.ArgumentParser(
        prog="wenu_chart",
        description="Generate publication-quality static sky charts.",
        allow_abbrev=False,
    )
    commands = value.add_subparsers(dest="command", required=True)

    all_sky = commands.add_parser("all-sky", allow_abbrev=False)
    _add_common_arguments(all_sky, family="all-sky")

    planisphere = commands.add_parser("planisphere", allow_abbrev=False)
    _add_common_arguments(planisphere, family="planisphere")

    regional = commands.add_parser("regional", allow_abbrev=False)
    _add_common_arguments(regional, family="regional")
    regional.add_argument("--field-width", type=float)
    regional.add_argument("--field-height", type=float)
    regional.add_argument("--center-on", metavar="IDENTIFIER")
    regional.add_argument("--center-icrs-ra", type=parse_icrs_ra)
    regional.add_argument("--center-icrs-dec", type=parse_degree_angle)
    regional.add_argument("--center-name")
    regional.add_argument(
        "--center-altitude", type=parse_degree_angle,
        help="fixed observer-local chart-center altitude in degrees",
    )
    regional.add_argument(
        "--center-azimuth", type=parse_degree_angle,
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

    circumpolar = commands.add_parser("circumpolar", allow_abbrev=False)
    _add_common_arguments(circumpolar, family="circumpolar")
    circumpolar.add_argument("--limiting-declination", type=float)
    circumpolar.add_argument("--pole", choices=("north", "south"))

    binocular = commands.add_parser("binocular", allow_abbrev=False)
    _add_common_arguments(binocular, family="binocular")
    binocular.add_argument("--center-on", metavar="IDENTIFIER")
    binocular.add_argument("--center-icrs-ra", type=parse_icrs_ra)
    binocular.add_argument("--center-icrs-dec", type=parse_degree_angle)
    binocular.add_argument("--center-name")
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
        allow_abbrev=False,
    )
    defaults.add_argument(
        "--write",
        type=Path,
        metavar="PATH",
        help="write an editable copy of the authoritative TOML defaults",
    )
    return value


def _configured_center(values, family):
    name = family.replace("-", "_")
    center = values["centers"][name]
    kind = center["kind"]
    if kind == "none":
        return {}
    if kind == "target":
        return {"target": center["target"]}
    if kind == "constellations":
        result = {"constellations": tuple(center["constellations"])}
        group = _optional(center.get("group", "none"))
        if group is not None:
            result = {"group": group}
        return result
    raise ValueError(f"Unsupported configured subject kind {kind!r}.")


def _coordinate_center(arguments):
    icrs = (arguments.center_icrs_ra, arguments.center_icrs_dec)
    horizontal = (
        getattr(arguments, "center_altitude", None),
        getattr(arguments, "center_azimuth", None),
    )
    for names, pair in (
        (("--center-icrs-ra", "--center-icrs-dec"), icrs),
        (("--center-altitude", "--center-azimuth"), horizontal),
    ):
        if (pair[0] is None) != (pair[1] is None):
            raise ValueError(
                f"{names[0]} and {names[1]} must be used together."
            )
    forms = sum((
        arguments.center_on is not None,
        icrs[0] is not None,
        horizontal[0] is not None,
    ))
    if forms > 1:
        raise ValueError(
            "Specify exactly one named, ICRS, or horizontal center."
        )
    if arguments.center_name is not None and icrs[0] is None:
        raise ValueError("--center-name requires an explicit ICRS center.")
    if icrs[0] is not None:
        return {
            "ra_deg": icrs[0], "dec_deg": icrs[1],
            "display_name": arguments.center_name,
        }
    if horizontal[0] is not None:
        return {
            "center_altitude_deg": horizontal[0],
            "center_azimuth_deg": horizontal[1],
        }
    return None


def _resolved_named_center_arguments(
    specification, arguments, configuration, observer
):
    directory = (
        arguments.minor_body_resource_directory
        or getattr(configuration, "minor_body_resource_directory", None)
    )
    session = None
    try:
        if directory is not None:
            from wenu.minor_body_resources import MinorBodyResourceSession

            session = MinorBodyResourceSession(directory, observer)
            session.__enter__()
        center = resolve_named_center(
            specification,
            minor_body_collection=(
                None if session is None else session.collection
            ),
        )
        if center.is_constellation:
            if center.kind == "group":
                return {"group": center.identifier}
            return {"constellations": center.value.constellations}
        if isinstance(center.value, ResolvedTarget):
            return {"target": center.value.key}
        if (
            center.value.ephemeris_source_key == "minor_body_spk"
            and session is None
        ):
            raise ValueError(
                "asteroid centers require "
                "--minor-body-resource-directory."
            )
        point = get_object_center(
            center.value,
            observer,
            source_resolver=(
                None if session is None else session.source_binding
            ),
            reference_equinox=configuration.reference_policy.resolved_equinox(
                observer
            ),
        )
        return {
            "center_altitude_deg": point.altitude_deg,
            "center_azimuth_deg": point.azimuth_deg,
        }
    finally:
        if session is not None:
            session.__exit__(None, None, None)


def _center_arguments(arguments, values, configuration, observer):
    if arguments.command not in {"regional", "binocular"}:
        return {}
    explicit = _coordinate_center(arguments)
    if explicit is not None:
        return explicit
    if arguments.center_on is not None:
        return _resolved_named_center_arguments(
            arguments.center_on, arguments, configuration, observer
        )
    configured_family = (
        "regional_single" if arguments.command == "regional"
        else "binocular"
    )
    return _configured_center(values, configured_family)


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
    mask = tuple(
        name
        for group in getattr(arguments, "constellation_mask", ())
        for name in group
    ) or None
    common = {
        "constellation_mask": mask,
        "constellation_system": arguments.constellation_system,
    }
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
        subject_arguments = _center_arguments(
            arguments, values, configuration, observer
        )
        view_arguments = _view_arguments(arguments)
        if view_arguments["constellation_system"] is None:
            view_arguments["constellation_system"] = (
                getattr(configuration, "constellation_system", "western")
            )
        if view_arguments["constellation_mask"] is None:
            mask_family = (
                "regional_single"
                if arguments.command == "regional"
                else arguments.command.replace("-", "_")
            )
            masks = getattr(configuration, "constellation_masks", {}) or {}
            view_arguments["constellation_mask"] = (
                tuple(masks.get(mask_family, ())) or None
            )
        view = get_chart_view(
            sky,
            observer,
            family=arguments.command.replace("-", "_"),
            configuration=configuration,
            **subject_arguments,
            **view_arguments,
        )
        sequence_options = chart_sequence_cli_options(
            arguments,
            start=getattr(observer, "utc_datetime", None),
            default_display_timezone=(
                getattr(observer, "timezone_name", None) or "UTC"
            ),
            defaults=configuration.sequence,
        )
        common_options = {
            "stem": _stem(view),
            "title": arguments.title,
            "language": arguments.language,
        }
        if sequence_options is None:
            results = draw_chart_view_from_arguments(
                view,
                arguments,
                **common_options,
            )
            return tuple(result.output for result in results)
        requests = chart_view_requests_from_arguments(
            view,
            arguments,
            sequence=True,
            **common_options,
        )
        if len(requests) != 1:
            raise RuntimeError(
                "A CLI chart sequence must resolve exactly one chart request."
            )
        sequence = ObserverTimeChartSequenceRequest(
            chart=requests[0],
            timeline=sequence_options.timeline,
            playback=sequence_options.playback,
            configuration=configuration,
        )
        generation = generate_observer_time_chart_sequence(
            sequence,
            restart_policy=sequence_options.restart_policy,
        )
        return generation.outputs
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
