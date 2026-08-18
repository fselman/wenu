"""Shared command-line adaptation for constellation chart subjects."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from .constellation_resolver import normalize_constellations


def parse_constellation_list(value):
    """Parse and normalize one comma-separated IAU abbreviation list."""
    names = tuple(
        item.strip() for item in str(value).split(",") if item.strip()
    )
    try:
        return normalize_constellations(names)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


@dataclass(frozen=True)
class ChartConstellationSubjectOptions:
    """One arbitrary IAU set or packaged constellation-group alias."""

    constellations: tuple[str, ...] | None = None
    group: str | None = None

    def __post_init__(self):
        if (self.constellations is None) == (self.group is None):
            raise ValueError(
                "Specify either constellations or a packaged group."
            )
        if self.constellations is not None:
            object.__setattr__(
                self,
                "constellations",
                normalize_constellations(self.constellations),
            )
        if self.group is not None:
            group = str(self.group).strip()
            if not group:
                raise ValueError("group cannot be empty.")
            object.__setattr__(self, "group", group)

    def view_arguments(self):
        """Return friendly subject arguments for ``get_chart_view``."""
        return {
            "constellations": self.constellations,
            "group": self.group,
        }


def add_constellation_subject_arguments(
    parser,
    *,
    default_constellations=None,
    default_group=None,
):
    """Add mutually exclusive arbitrary-set and packaged-group controls."""
    if default_constellations is not None and default_group is not None:
        raise ValueError(
            "default_constellations and default_group are mutually exclusive."
        )
    defaults = (
        None
        if default_constellations is None
        else normalize_constellations(default_constellations)
    )
    subjects = parser.add_mutually_exclusive_group()
    subjects.add_argument(
        "--constellations",
        type=parse_constellation_list,
        default=defaults,
        metavar="IAU,...",
        help="comma-separated IAU constellation abbreviations",
    )
    subjects.add_argument(
        "--group",
        default=default_group,
        help="packaged constellation-group alias",
    )
    return parser


def chart_constellation_subject(arguments, *, required=True):
    """Return the typed constellation subject selected by parsed controls."""
    group = getattr(arguments, "group", None)
    constellations = (
        None if group is not None
        else getattr(arguments, "constellations", None)
    )
    if constellations is None and group is None and not required:
        return None
    return ChartConstellationSubjectOptions(
        constellations=constellations,
        group=group,
    )
