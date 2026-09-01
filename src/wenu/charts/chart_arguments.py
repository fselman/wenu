"""Shared command-line arguments for canonical chart requests."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from math import isfinite
import re

from .detail import DetailOverrides, SkyContentSelection
from .product_options import add_chart_product_arguments
from .reference_policy import CelestialReferencePolicy
from .request_disks import (
    ObservedSolarSystemDiskSequenceDisplayRequest,
    SolarSystemDiskDisplayRequest,
)
from .style_overrides import ChartStyleOverrides
from wenu.sky.solar_system_disk_sequences import (
    ObservedSolarSystemDiskSequenceRequest,
)
from wenu.sky.venus import VENUS_POINT
from wenu.sky.venus_disk import VENUS_RADIUS_MODEL
from wenu.solar_system_appearance import VENUS_MEAN_RADIUS_KM

GRID_REFERENCES = frozenset({"equatorial", "ecliptic", "galactic"})
_DURATION = re.compile(r"^(?P<value>(?:\d+(?:\.\d*)?|\.\d+))(?P<unit>h|d|hour|hours|day|days)$", re.IGNORECASE)

def _duration_days(value):
    """Parse one positive governed hour/day duration into days."""
    match = _DURATION.fullmatch(str(value).strip())
    if match is None:
        raise argparse.ArgumentTypeError(
            "duration must be a positive number followed by h or d"
        )
    amount = float(match.group("value"))
    if not isfinite(amount) or amount <= 0.0:
        raise argparse.ArgumentTypeError("duration must be positive and finite")
    unit = match.group("unit").lower()
    return amount / 24.0 if unit in {"h", "hour", "hours"} else amount

@dataclass(frozen=True)
class ChartTrackOptions:
    """Shared physical sampling request parsed from the chart CLI."""
    body: str
    start_instant: str
    sample_step_days: float
    tick_step_days: float
    tick_count: int
    label_ticks: bool = False



class _ExplicitEquatorialGrid(argparse.Action):
    """Record an explicit equatorial choice separately from CLI defaults."""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        setattr(namespace, "_equatorial_grid_explicit", True)


def _grid_references(value):
    names = frozenset(
        item.strip().lower()
        for item in str(value).split(",")
        if item.strip()
    )
    if not names:
        raise argparse.ArgumentTypeError(
            "grid references cannot be empty"
        )
    if "all" in names:
        if names != {"all"}:
            raise argparse.ArgumentTypeError(
                "'all' cannot be combined with named grid references"
            )
        return GRID_REFERENCES
    unknown = names - GRID_REFERENCES
    if unknown:
        raise argparse.ArgumentTypeError(
            "unknown grid reference: " + ", ".join(sorted(unknown))
        )
    return names


@dataclass(frozen=True)
class ChartContentOptions:
    """Shared astronomical-content choices parsed by canonical examples."""

    magnitude_limit: float | None = None
    constellation_lines: bool = False
    constellation_labels: bool = False
    constellation_boundaries: bool = False
    horizon: bool = False
    horizon_mask: bool = False
    equatorial_grid: bool = False
    equatorial_grid_labels: bool = False
    ecliptic_grid: bool = False
    ecliptic_grid_labels: bool = False
    galactic_grid: bool = False
    galactic_grid_labels: bool = False
    grid_references: frozenset[str] = frozenset()
    poles: bool = False
    pole_labels: bool = False
    altaz_grid: bool = False
    altaz_grid_labels: bool = False
    equatorial_declination_step_deg: float | None = None
    reference_equinox: str | None = None
    planets: frozenset[str] = frozenset()
    moon: bool = False

    def __post_init__(self):
        if (
            self.magnitude_limit is not None
            and not isfinite(float(self.magnitude_limit))
        ):
            raise ValueError("magnitude_limit must be finite.")
        references = frozenset(
            str(name).strip().lower()
            for name in self.grid_references
            if str(name).strip()
        )
        if references - GRID_REFERENCES:
            raise ValueError(
                "grid_references must contain only equatorial, ecliptic, "
                "or galactic."
            )
        object.__setattr__(self, "grid_references", references)
        planets = frozenset(
            str(name).strip().lower()
            for name in self.planets
            if str(name).strip()
        )
        if planets - {"venus"}:
            raise ValueError("planets currently supports only venus.")
        object.__setattr__(self, "planets", planets)
        object.__setattr__(self, "moon", bool(self.moon))
        step = self.equatorial_declination_step_deg
        if step is not None:
            step = float(step)
            if not isfinite(step) or not 0.0 < step <= 90.0:
                raise ValueError(
                    "equatorial declination step must be finite and "
                    "between 0 and 90 degrees"
                )
            object.__setattr__(
                self, "equatorial_declination_step_deg", step
            )


@dataclass(frozen=True)
class ChartLegendSelection:
    """Resolved opt-in selection of the two canonical chart legends."""

    objects: bool = False
    stellar_magnitudes: bool = False
    stellar_counts: bool = False


def add_chart_content_arguments(parser):
    """Add shared astronomical-content arguments to ``parser``."""
    parser.add_argument(
        "--reference-equinox",
        metavar="EQUINOX",
        help=(
            "use one FK5/ecliptic reference equinox "
            "(for example J2000, B1950, or of_date)"
        ),
    )
    parser.add_argument(
        "--magnitude-limit",
        type=float,
        help="override the style/family stellar magnitude limit",
    )
    parser.add_argument(
        "--planet",
        action="append",
        choices=("venus",),
        default=[],
        help="draw a selected planet (currently: venus)",
    )
    parser.add_argument(
        "--planet-appearance",
        action="append",
        default=[],
        metavar="PLANET=MODE",
        help=(
            "select a planet appearance (currently: venus=resolved; "
            "regional/binocular only)"
        ),
    )
    parser.add_argument(
        "--planet-disk-magnification",
        action="append",
        default=[],
        metavar="PLANET=FACTOR",
        help=(
            "magnify one resolved disk after projection "
            "(factor 1 is physical scale)"
        ),
    )
    parser.add_argument(
        "--planet-disk-sequence",
        choices=("venus",),
        help=(
            "draw observed resolved disks at major epochs "
            "(regional/binocular only)"
        ),
    )
    parser.add_argument(
        "--disk-sequence-model",
        choices=("observed",),
        help="scientific sequence model (currently: observed)",
    )
    parser.add_argument("--disk-sequence-start", metavar="ISO_TIME")
    parser.add_argument(
        "--disk-sequence-step",
        type=_duration_days,
        metavar="DURATION",
    )
    parser.add_argument("--disk-sequence-n-steps", type=int, metavar="COUNT")
    parser.add_argument(
        "--disk-sequence-labels", action="store_true",
        help="label every resolved disk with its ISO date",
    )
    parser.add_argument(
        "--planet-track",
        choices=("venus",),
        help="draw the apparent path of a planet (regional/binocular only)",
    )
    parser.add_argument("--track-start", metavar="ISO_TIME")
    parser.add_argument("--track-sample-step", type=_duration_days, metavar="DURATION")
    parser.add_argument("--track-tick-step", type=_duration_days, metavar="DURATION")
    parser.add_argument("--track-tick-count", type=int, metavar="COUNT")
    parser.add_argument(
        "--track-tick-labels", action="store_true",
        help="label every major planet-track tick with its ISO date",
    )
    parser.add_argument(
        "--moon",
        action="store_true",
        help="draw the Moon as a symbolic point",
    )
    parser.add_argument(
        "--constellation-lines",
        action="store_true",
        help="draw constellation line figures",
    )
    parser.add_argument(
        "--constellation-labels",
        action="store_true",
        help="draw constellation labels",
    )
    parser.add_argument(
        "--constellation-boundaries",
        action="store_true",
        help="draw IAU constellation boundaries",
    )
    parser.add_argument(
        "--horizon",
        action="store_true",
        help="draw the observer horizon reference",
    )
    parser.add_argument(
        "--horizon-mask",
        action="store_true",
        help="shade the sky below the observer horizon",
    )
    parser.add_argument(
        "--altaz-grid",
        action="store_true",
        help="draw the configured AltAz grid",
    )
    parser.add_argument(
        "--altaz-grid-labels",
        action="store_true",
        help="draw AltAz-grid labels (and enable that grid)",
    )
    parser.add_argument(
        "--equatorial-grid",
        action=_ExplicitEquatorialGrid,
        nargs=0,
        default=False,
        help="draw the configured equatorial grid",
    )
    parser.add_argument(
        "--equatorial-grid-labels",
        action=_ExplicitEquatorialGrid,
        nargs=0,
        default=False,
        help="draw equatorial-grid labels (and enable that grid)",
    )
    parser.add_argument(
        "--declination-step",
        type=float,
        metavar="DEGREES",
        help="override spacing between equatorial declination parallels",
    )
    parser.add_argument(
        "--ecliptic-grid",
        action="store_true",
        help="draw the configured ecliptic grid",
    )
    parser.add_argument(
        "--ecliptic-grid-labels",
        action="store_true",
        help="draw ecliptic-grid labels (and enable that grid)",
    )
    parser.add_argument(
        "--galactic-grid",
        action="store_true",
        help="draw the configured Galactic grid",
    )
    parser.add_argument(
        "--galactic-grid-labels",
        action="store_true",
        help="draw Galactic-grid labels (and enable that grid)",
    )
    parser.add_argument(
        "--grid-references",
        type=_grid_references,
        default=frozenset(),
        metavar="SELECTION",
        help=(
            "draw labeled zero-latitude references selected from "
            "equatorial,ecliptic,galactic or all"
        ),
    )
    parser.add_argument(
        "--poles",
        action="store_true",
        default=None,
        help="draw configured visible coordinate-system poles",
    )
    parser.add_argument(
        "--pole-labels",
        action="store_true",
        default=None,
        help="label visible pole crosses with their abbreviations",
    )
    return parser


def add_chart_style_arguments(parser):
    """Add optional post-mode visual overrides to ``parser``."""
    parser.add_argument(
        "--sky-color",
        help="override the resolved chart sky/background color",
    )
    parser.add_argument("--constellation-line-width", type=float)
    parser.add_argument("--constellation-line-color")
    parser.add_argument("--constellation-label-color")
    parser.add_argument("--constellation-boundary-width", type=float)
    parser.add_argument("--constellation-boundary-color")
    return parser


def add_chart_legend_arguments(parser):
    """Add opt-in object and stellar-magnitude legend arguments."""
    parser.add_argument(
        "--legends",
        action="store_true",
        help="draw both the object and stellar-magnitude legends",
    )
    parser.add_argument(
        "--object-legend",
        action="store_true",
        help="draw the enabled-object symbol legend",
    )
    parser.add_argument(
        "--magnitude-legend",
        action="store_true",
        help="draw the stellar magnitude-size legend",
    )
    parser.add_argument(
        "--star-counts",
        action="store_true",
        help="append cumulative counts to magnitude-legend entries",
    )
    return parser


def add_chart_arguments(parser, *, default_output):
    """Add the shared product, content, style, and legend arguments."""
    add_chart_product_arguments(parser, default_output=default_output)
    add_chart_content_arguments(parser)
    add_chart_style_arguments(parser)
    add_chart_legend_arguments(parser)
    return parser


def chart_content_options(arguments) -> ChartContentOptions:
    """Resolve shared parsed content arguments into an immutable value."""
    return ChartContentOptions(
        magnitude_limit=arguments.magnitude_limit,
        constellation_lines=arguments.constellation_lines,
        constellation_labels=arguments.constellation_labels,
        constellation_boundaries=arguments.constellation_boundaries,
        horizon=arguments.horizon,
        horizon_mask=arguments.horizon_mask,
        altaz_grid=arguments.altaz_grid,
        altaz_grid_labels=arguments.altaz_grid_labels,
        equatorial_grid=arguments.equatorial_grid,
        equatorial_grid_labels=arguments.equatorial_grid_labels,
        ecliptic_grid=arguments.ecliptic_grid,
        ecliptic_grid_labels=arguments.ecliptic_grid_labels,
        galactic_grid=arguments.galactic_grid,
        galactic_grid_labels=arguments.galactic_grid_labels,
        grid_references=arguments.grid_references,
        poles=bool(arguments.poles),
        pole_labels=bool(arguments.pole_labels),
        equatorial_declination_step_deg=arguments.declination_step,
        reference_equinox=arguments.reference_equinox,
        planets=frozenset(getattr(arguments, "planet", ())),
        moon=bool(getattr(arguments, "moon", False)),
    )


def _key_value_options(values, *, option):
    result = {}
    for raw in values or ():
        text = str(raw).strip()
        if text.count("=") != 1:
            raise ValueError(f"{option} requires PLANET=VALUE.")
        key, value = (part.strip().lower() for part in text.split("=", 1))
        if not key or not value:
            raise ValueError(f"{option} requires PLANET=VALUE.")
        if key in result:
            raise ValueError(f"{option} cannot repeat {key}.")
        result[key] = value
    return result


def _disk_selections(arguments):
    appearances = _key_value_options(
        getattr(arguments, "planet_appearance", ()),
        option="planet-appearance",
    )
    magnifications = _key_value_options(
        getattr(arguments, "planet_disk_magnification", ()),
        option="planet-disk-magnification",
    )
    return appearances, magnifications


def chart_disk_options(arguments):
    """Resolve object-specific opt-in resolved-disk display requests."""
    appearances, magnifications = _disk_selections(arguments)
    unknown = set(appearances) - {"venus"}
    if unknown:
        raise ValueError("planet-appearance currently supports only venus.")
    invalid_modes = {
        target: mode
        for target, mode in appearances.items()
        if mode != "resolved"
    }
    if invalid_modes:
        raise ValueError("planet appearance mode must be resolved.")
    sequence_target = getattr(arguments, "planet_disk_sequence", None)
    selected = set(appearances) | (
        {sequence_target} if sequence_target else set()
    )
    unselected = set(magnifications) - selected
    if unselected:
        raise ValueError(
            "planet-disk-magnification requires resolved appearance."
        )
    return tuple(
        SolarSystemDiskDisplayRequest(
            target,
            float(magnifications.get(target, 1.0)),
        )
        for target in appearances
    )


def chart_disk_sequence_options(arguments):
    """Resolve the optional complete observed disk-sequence CLI group."""
    names = (
        "planet_disk_sequence",
        "disk_sequence_model",
        "disk_sequence_start",
        "disk_sequence_step",
        "disk_sequence_n_steps",
    )
    values = tuple(getattr(arguments, name, None) for name in names)
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        missing = [
            name.replace("_", "-")
            for name, value in zip(names, values)
            if value is None
        ]
        raise ValueError(
            "a planet disk sequence requires all sequence options; missing: "
            + ", ".join(missing)
        )
    target, model, start, step_days, n_steps = values
    if model != "observed":
        raise ValueError(
            "disk-sequence-model currently supports only observed."
        )
    if isinstance(n_steps, bool) or n_steps < 0:
        raise ValueError("disk-sequence-n-steps must be a nonnegative integer")
    appearances, magnifications = _disk_selections(arguments)
    if target in appearances:
        raise ValueError(
            "a planet cannot be both a single resolved disk and a disk sequence."
        )
    return ObservedSolarSystemDiskSequenceDisplayRequest(
        ObservedSolarSystemDiskSequenceRequest(
            descriptor=VENUS_POINT,
            start_instant=str(start).strip(),
            start_time_scale="utc",
            step_days=float(step_days),
            n_steps=int(n_steps),
            display_name=VENUS_POINT.display_name,
            physical_radius_km=VENUS_MEAN_RADIUS_KM,
            radius_model=VENUS_RADIUS_MODEL,
        ),
        magnification=float(magnifications.get(target, 1.0)),
        label_dates=bool(getattr(arguments, "disk_sequence_labels", False)),
    )


def chart_track_options(arguments):
    """Resolve the optional complete planet-track CLI group."""
    names = ("planet_track", "track_start", "track_sample_step", "track_tick_step", "track_tick_count")
    values = tuple(getattr(arguments, name, None) for name in names)
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        missing = [name.replace("_", "-") for name, value in zip(names, values) if value is None]
        raise ValueError("a planet track requires all track options; missing: " + ", ".join(missing))
    if isinstance(values[4], bool) or values[4] < 1:
        raise ValueError("track-tick-count must be a positive integer")
    if not str(values[1]).strip():
        raise ValueError("track-start must be non-empty")
    return ChartTrackOptions(
        body=values[0], start_instant=str(values[1]).strip(),
        sample_step_days=float(values[2]), tick_step_days=float(values[3]),
        tick_count=int(values[4]),
        label_ticks=bool(getattr(arguments, "track_tick_labels", False)),
    )

def chart_reference_policy(arguments, *, default=None):
    """Resolve the CLI value over one configured immutable default."""
    value = getattr(arguments, "reference_equinox", None)
    if value is not None:
        return CelestialReferencePolicy(value)
    return default or CelestialReferencePolicy()


def chart_style_overrides(
    arguments,
) -> ChartStyleOverrides:
    """Resolve parsed visual arguments without applying mode defaults."""
    return ChartStyleOverrides(
        sky_color=arguments.sky_color,
        constellation_linewidth=arguments.constellation_line_width,
        constellation_line_color=arguments.constellation_line_color,
        constellation_label_color=arguments.constellation_label_color,
        boundary_linewidth=arguments.constellation_boundary_width,
        boundary_color=arguments.constellation_boundary_color,
    )


def chart_detail_overrides(
    arguments,
) -> DetailOverrides:
    """Resolve magnitude and opt-in constellation layer visibility."""
    content = chart_content_options(arguments)
    grids = {
        "altaz_grid": content.altaz_grid or content.altaz_grid_labels,
        "equatorial_grid": (
            content.equatorial_grid or content.equatorial_grid_labels
        ),
        "ecliptic_grid": (
            content.ecliptic_grid or content.ecliptic_grid_labels
        ),
        "galactic_grid": (
            content.galactic_grid or content.galactic_grid_labels
        ),
    }
    additions = {
        name
        for name, enabled in (
            ("constellation_lines", content.constellation_lines),
            ("constellation_labels", content.constellation_labels),
            ("constellation_boundaries", content.constellation_boundaries),
            *grids.items(),
            ("venus", "venus" in content.planets),
            ("moon", content.moon),
        )
        if enabled
    }
    optional_layers = {
        "constellation_lines",
        "constellation_labels",
        "constellation_boundaries",
        "coordinate_grids",
        *grids,
        "venus",
        "moon",
    }
    labels = frozenset(
        name
        for name, enabled in (
            ("altaz_grid", content.altaz_grid_labels),
            ("equatorial_grid", content.equatorial_grid_labels),
            ("ecliptic_grid", content.ecliptic_grid_labels),
            ("galactic_grid", content.galactic_grid_labels),
        )
        if enabled
    )
    return DetailOverrides(
        star_magnitude_limit=content.magnitude_limit,
        equatorial_declination_step_deg=(
            content.equatorial_declination_step_deg
        ),
        enabled_layer_additions=frozenset(additions),
        disabled_layers=frozenset(optional_layers - additions),
        grid_label_layers=labels,
        constellation_star_mode=(
            "selected" if content.constellation_lines else "none"
        ),
    )


def chart_sky_content(arguments) -> SkyContentSelection:
    """Resolve selected moving bodies into request-owned sky content."""
    content = chart_content_options(arguments)
    selected = set(content.planets)
    if content.moon:
        selected.add("moon")
    return SkyContentSelection(
        solar_system_objects=frozenset(selected)
    )


def chart_legend_selection(arguments) -> ChartLegendSelection:
    """Resolve convenience and individual legend switches."""
    objects = bool(arguments.legends or arguments.object_legend)
    stellar = bool(arguments.legends or arguments.magnitude_legend)
    return ChartLegendSelection(
        objects=objects,
        stellar_magnitudes=stellar,
        stellar_counts=bool(stellar and arguments.star_counts),
    )
