"""Shared command-line arguments for canonical chart requests."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from math import isfinite

from .product_options import add_chart_product_arguments
from .detail import DetailOverrides
from .style_overrides import ChartStyleOverrides


GRID_REFERENCES = frozenset({"equatorial", "ecliptic", "galactic"})


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


@dataclass(frozen=True)
class ChartLegendSelection:
    """Resolved opt-in selection of the two canonical chart legends."""

    objects: bool = False
    stellar_magnitudes: bool = False
    stellar_counts: bool = False


def add_chart_content_arguments(parser):
    """Add shared astronomical-content arguments to ``parser``."""
    parser.add_argument(
        "--magnitude-limit",
        type=float,
        help="override the style/family stellar magnitude limit",
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
        help="draw configured visible coordinate-system poles",
    )
    parser.add_argument(
        "--pole-labels",
        action="store_true",
        help="label visible pole crosses with their abbreviations",
    )
    return parser


def add_chart_style_arguments(parser):
    """Add optional post-mode visual overrides to ``parser``."""
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
        poles=arguments.poles,
        pole_labels=arguments.pole_labels,
    )


def chart_style_overrides(
    arguments,
) -> ChartStyleOverrides:
    """Resolve parsed visual arguments without applying mode defaults."""
    return ChartStyleOverrides(
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
        )
        if enabled
    }
    optional_layers = {
        "constellation_lines",
        "constellation_labels",
        "constellation_boundaries",
        "coordinate_grids",
        *grids,
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
        enabled_layer_additions=frozenset(additions),
        disabled_layers=frozenset(optional_layers - additions),
        grid_label_layers=labels,
        constellation_star_mode=(
            "selected" if content.constellation_lines else "none"
        ),
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
