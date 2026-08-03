"""Shared command-line arguments for canonical chart requests."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .product_options import add_chart_product_arguments
from .detail import DetailOverrides
from .style_overrides import ChartStyleOverrides


@dataclass(frozen=True)
class ChartContentOptions:
    """Shared astronomical-content choices parsed by canonical examples."""

    magnitude_limit: float | None = None
    constellation_labels: bool = False
    constellation_boundaries: bool = False
    references: bool = False
    poles: bool = False
    pole_labels: bool = False

    def __post_init__(self):
        if (
            self.magnitude_limit is not None
            and not isfinite(float(self.magnitude_limit))
        ):
            raise ValueError("magnitude_limit must be finite.")


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
        "--references",
        action="store_true",
        help="draw configured celestial reference planes and labels",
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
        constellation_labels=arguments.constellation_labels,
        constellation_boundaries=arguments.constellation_boundaries,
        references=arguments.references,
        poles=arguments.poles,
        pole_labels=arguments.pole_labels,
    )


def chart_style_overrides(arguments) -> ChartStyleOverrides:
    """Resolve parsed visual arguments without applying mode defaults."""
    return ChartStyleOverrides(
        constellation_linewidth=arguments.constellation_line_width,
        constellation_line_color=arguments.constellation_line_color,
        constellation_label_color=arguments.constellation_label_color,
        boundary_linewidth=arguments.constellation_boundary_width,
        boundary_color=arguments.constellation_boundary_color,
    )


def chart_detail_overrides(arguments) -> DetailOverrides:
    """Resolve magnitude and opt-in constellation layer visibility."""
    content = chart_content_options(arguments)
    additions = {
        name
        for name, enabled in (
            ("constellation_labels", content.constellation_labels),
            ("constellation_boundaries", content.constellation_boundaries),
        )
        if enabled
    }
    removals = {
        name
        for name, enabled in (
            ("constellation_labels", content.constellation_labels),
            ("constellation_boundaries", content.constellation_boundaries),
        )
        if not enabled
    }
    return DetailOverrides(
        star_magnitude_limit=content.magnitude_limit,
        enabled_layer_additions=frozenset(additions),
        disabled_layers=frozenset(removals),
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
