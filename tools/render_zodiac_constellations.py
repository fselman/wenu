"""Render selected traditional zodiac constellations as separate charts."""

from __future__ import annotations

import argparse
from copy import copy
from pathlib import Path

import astropy.units as u
from astropy.coordinates import BarycentricMeanEcliptic, FK5, SkyCoord
from astropy.time import Time

from wenu import (
    ChartStyleOverrides,
    FixedDetailPolicy,
    Observer,
    ResolvedDetail,
    add_chart_cli_arguments,
    chart_cli_furniture,
    chart_configuration,
    draw_chart_view_from_arguments,
    default_chart_legend_plan,
    generate_celestial_sphere,
    get_chart_view,
    parse_constellation_list,
    resolve_constellation_label_offsets,
)
from wenu.charts.regional import target_up_position_angle
from wenu.translations import translate_label


ZODIAC_CONSTELLATIONS = (
    "Ari", "Tau", "Gem", "Cnc", "Leo", "Vir",
    "Lib", "Sco", "Sgr", "Cap", "Aqr", "Psc",
)
REVIEW_CONSTELLATIONS = (*ZODIAC_CONSTELLATIONS, "Oph")
REVIEW_FIGURES = {"Oph": ("Oph", "Ser")}
REVIEW_LABEL_POSITIONS = {"Oph": {"SerCau": "cl"}}
REVIEW_LABEL_CLEARANCE = (0.48, 0.20)
ENGLISH_NAMES = {
    "Ari": "Aries",
    "Tau": "Taurus",
    "Gem": "Gemini",
    "Cnc": "Cancer",
    "Leo": "Leo",
    "Vir": "Virgo",
    "Lib": "Libra",
    "Sco": "Scorpius",
    "Sgr": "Sagittarius",
    "Cap": "Capricornus",
    "Aqr": "Aquarius",
    "Psc": "Pisces",
    "Oph": "Ophiuchus",
}
STAR_MAGNITUDE_LIMIT = 5.5
REFERENCE_MAGNITUDE_RANGE = (0, 5)
ECLIPTIC_LINEWIDTH = 1.0
GRID_LABEL_FONTSIZE = 7.5
DEFAULT_OUTPUT = Path("output/zodiac-constellations")
VISIBLE_LAYERS = frozenset({
    "stars",
    "constellation_lines",
    "constellation_labels",
    "equatorial_grid",
})
ZODIAC_LEGEND_PLAN = default_chart_legend_plan("regional").with_stars(
    anchor=(0.99, 0.02),
)


def _north_ecliptic_pole(observer):
    pole = SkyCoord(
        lon=0.0 * u.deg,
        lat=90.0 * u.deg,
        frame=BarycentricMeanEcliptic(equinox=Time("J2000")),
    )
    return pole.transform_to(observer.altaz_frame)


def _review_figures(constellation):
    return REVIEW_FIGURES.get(constellation, (constellation,))


def _review_label_offsets(constellation):
    positions = REVIEW_LABEL_POSITIONS.get(constellation)
    if positions is None:
        return None
    resolved = resolve_constellation_label_offsets(
        positions,
        clearance=REVIEW_LABEL_CLEARANCE,
    )
    return {
        label: offset
        for label, offset in resolved.items()
        if label != "__default__"
    }


def _provisional_view(sky, observer, configuration, constellation, mask):
    return get_chart_view(
        sky,
        observer,
        family="regional",
        constellations=_review_figures(constellation),
        display_name=translate_label(ENGLISH_NAMES[constellation], "es"),
        projection="stereographic",
        mask=mask,
        configuration=configuration,
    )


def _chart_view(sky, observer, configuration, constellation, mask):
    provisional = _provisional_view(
        sky, observer, configuration, constellation, mask
    )
    chart = provisional.chart
    pole = _north_ecliptic_pole(observer)
    position_angle = target_up_position_angle(
        center_alt_deg=chart.center_alt_deg,
        center_az_deg=chart.center_az_deg,
        target_alt_deg=float(pole.alt.deg),
        target_az_deg=float(pole.az.deg),
    )
    return get_chart_view(
        sky,
        observer,
        family="regional",
        constellations=_review_figures(constellation),
        display_name=translate_label(ENGLISH_NAMES[constellation], "es"),
        position_angle_deg=position_angle,
        projection="stereographic",
        mask=mask,
        configuration=configuration,
    )


def _center_coordinate(view):
    chart = view.chart
    horizontal = SkyCoord(
        alt=float(chart.center_alt_deg) * u.deg,
        az=float(chart.center_az_deg) * u.deg,
        frame=view.observer.altaz_frame,
    )
    return horizontal.transform_to(FK5(equinox=Time("J2000")))


def _title(view, constellation):
    center = _center_coordinate(view)
    right_ascension = center.ra.to_string(
        unit=u.hourangle,
        sep=":",
        precision=0,
        pad=True,
        fields=2,
    )
    declination = center.dec.to_string(
        unit=u.deg,
        sep=":",
        precision=0,
        pad=True,
        alwayssign=True,
        fields=2,
    )
    return (
        f"{translate_label(ENGLISH_NAMES[constellation], 'es')} — "
        f"RA {right_ascension}, Dec {declination}"
    )


def _effective_arguments(arguments, destination):
    effective = copy(arguments)
    effective.output = destination
    effective.style = "cartoon"
    effective.mode = "presentation"
    effective.all_products = False
    effective.magnitude_limit = STAR_MAGNITUDE_LIMIT
    effective.constellation_lines = True
    effective.constellation_labels = True
    effective.constellation_boundaries = False
    effective.equatorial_grid = True
    effective.equatorial_grid_labels = True
    effective.ecliptic_grid = False
    effective.ecliptic_grid_labels = False
    effective.grid_references = frozenset({"equatorial", "ecliptic"})
    effective.poles = False
    effective.pole_labels = False
    effective.legends = False
    effective.object_legend = False
    effective.magnitude_legend = True
    effective.star_counts = False
    return effective


def _selected_constellations(arguments):
    selected = tuple(arguments.constellations)
    unsupported = tuple(
        name for name in selected if name not in REVIEW_CONSTELLATIONS
    )
    if unsupported:
        raise ValueError(
            "Only zodiac constellations and Ophiuchus are supported: "
            + ", ".join(unsupported)
        )
    return selected


def render_zodiac(arguments, *, sky=None):
    """Render and return selected zodiac paths through the Wenu facade."""
    selected = _selected_constellations(arguments)
    configuration = chart_configuration(arguments)
    sky = generate_celestial_sphere() if sky is None else sky
    observer_options = {}
    if arguments.data_directory is not None:
        observer_options["data_directory"] = arguments.data_directory
    observer = Observer(
        location="La Ligua",
        time="2026-08-15 21:00",
        **observer_options,
    )
    output_directory = Path(arguments.output)
    extension = str(arguments.file_format).lstrip(".")
    outputs = []
    detail = FixedDetailPolicy(ResolvedDetail(
        star_magnitude_limit=STAR_MAGNITUDE_LIMIT,
        enabled_layers=VISIBLE_LAYERS,
    ))
    try:
        for constellation in selected:
            index = REVIEW_CONSTELLATIONS.index(constellation) + 1
            view = _chart_view(
                sky,
                observer,
                configuration,
                constellation,
                bool(arguments.mask),
            )
            destination = output_directory / (
                f"{index:02d}-{constellation.lower()}.{extension}"
            )
            effective = _effective_arguments(arguments, destination)
            results = draw_chart_view_from_arguments(
                view,
                effective,
                stem=f"{index:02d}-{constellation.lower()}",
                detail=detail,
                furniture=chart_cli_furniture(
                    effective,
                    copyright="© Fernando Selman",
                    configuration=configuration,
                    family=view.family,
                    language="es",
                    ecliptic_keypoints="labeled",
                    ecliptic_keypoint_legend=True,
                    stellar_title="",
                    stellar_reference_range=REFERENCE_MAGNITUDE_RANGE,
                    stellar_background="sky",
                    legend_plan=ZODIAC_LEGEND_PLAN,
                ),
                style_overrides=ChartStyleOverrides(
                    ecliptic_linewidth=ECLIPTIC_LINEWIDTH,
                    coordinate_label_fontsize=GRID_LABEL_FONTSIZE,
                    constellation_label_offsets=(
                        _review_label_offsets(constellation)
                    ),
                ),
                title=_title(view, constellation),
                language="es",
            )
            outputs.extend(result.output for result in results)
    finally:
        observer.close()
    return tuple(outputs)


def parser():
    value = add_chart_cli_arguments(
        argparse.ArgumentParser(description=__doc__),
        default_output=DEFAULT_OUTPUT,
    )
    value.set_defaults(
        style="cartoon",
        mode="presentation",
        magnitude_limit=STAR_MAGNITUDE_LIMIT,
        constellation_lines=True,
        constellation_labels=True,
        equatorial_grid=True,
        equatorial_grid_labels=True,
        grid_references=frozenset({"equatorial", "ecliptic"}),
    )
    value.add_argument(
        "--constellations",
        type=parse_constellation_list,
        default=ZODIAC_CONSTELLATIONS,
        metavar="IAU,...",
        help=(
            "comma-separated zodiac or Ophiuchus abbreviations; "
            "default: all twelve"
        ),
    )
    value.add_argument(
        "--format",
        choices=("pdf", "png", "svg"),
        default="png",
        dest="file_format",
    )
    value.add_argument("--data-directory", type=Path)
    value.add_argument(
        "--mask",
        action="store_true",
        help="shade outside the selected IAU region using Wenu's mask style",
    )
    value.add_argument(
        "--presentation",
        action="store_const",
        const="presentation",
        dest="mode",
        help="select Wenu's presentation mode (the default)",
    )
    return value


def main():
    for path in render_zodiac(parser().parse_args()):
        print(path)


if __name__ == "__main__":
    main()
