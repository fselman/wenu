"""Reusable, independently constructed astronomical chart symbols."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

import numpy as np
from matplotlib.path import Path


def _circle_with_radial_ticks() -> Path:
    """Return a normalized planetary-nebula symbol.

    The glyph is constructed from the conventional hollow circle with four
    short radial ticks. Its coordinates are normalized for use as a
    Matplotlib scatter marker; chart styles control its displayed area.
    """
    circle = Path.unit_circle()
    vertices = [circle.vertices]
    codes = [circle.codes]
    for inner, outer in (
        ((0.0, 0.55), (0.0, 1.0)),
        ((0.0, -0.55), (0.0, -1.0)),
        ((0.55, 0.0), (1.0, 0.0)),
        ((-0.55, 0.0), (-1.0, 0.0)),
    ):
        vertices.append(np.asarray((inner, outer), dtype=float))
        codes.append(
            np.asarray((Path.MOVETO, Path.LINETO), dtype=np.uint8)
        )
    return Path(
        np.concatenate(vertices),
        np.concatenate(codes),
    )


def _dotted_circle() -> Path:
    """Return twelve filled dots on a normalized circumference."""
    paths = []
    dot = Path.unit_circle()
    for angle in np.linspace(0.0, 2.0 * np.pi, 12, endpoint=False):
        center = 0.93 * np.asarray(
            (np.cos(angle), np.sin(angle))
        )
        vertices = 0.07 * dot.vertices + center
        paths.append(Path(vertices, dot.codes))
    return Path.make_compound_path(*paths)


def _variable_star() -> Path:
    """Return an independent conventional variable-star marker."""
    circle = Path.unit_circle()
    dot = Path.unit_circle()
    dot_vertices = 0.24 * dot.vertices
    return Path.make_compound_path(circle, Path(dot_vertices, dot.codes))


def _multiple_star() -> Path:
    """Return an independent conventional multiple-star marker."""
    circle = Path.unit_circle()
    divider = Path(
        np.asarray(((-0.72, -0.72), (0.72, 0.72)), dtype=float),
        np.asarray((Path.MOVETO, Path.LINETO), dtype=np.uint8),
    )
    return Path.make_compound_path(circle, divider)


def _filled_five_point_star() -> Path:
    """Return a normalized compact five-point stellar marker."""
    return Path.unit_regular_star(5)


@dataclass(frozen=True)
class SymbolLibrary:
    """Named normalized marker paths used by complete chart styles."""

    planetary_nebula: Path = field(
        default_factory=_circle_with_radial_ticks
    )
    open_cluster: Path = field(default_factory=_dotted_circle)
    variable_star: Path = field(default_factory=_variable_star)
    multiple_star: Path = field(default_factory=_multiple_star)
    filled_five_point_star: Path = field(
        default_factory=_filled_five_point_star
    )

    @property
    def symbols(self) -> Mapping[str, Path]:
        """Return the currently implemented symbols by semantic name."""
        return MappingProxyType(
            {
                "planetary_nebula": self.planetary_nebula,
                "open_cluster": self.open_cluster,
                "variable_star": self.variable_star,
                "multiple_star": self.multiple_star,
                "filled_five_point_star": self.filled_five_point_star,
            }
        )

    def __getitem__(self, name: str) -> Path:
        return self.symbols[name]


DEFAULT_SYMBOLS = SymbolLibrary()
