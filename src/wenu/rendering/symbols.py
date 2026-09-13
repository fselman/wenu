"""Reusable, independently constructed astronomical chart symbols."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

import numpy as np
from matplotlib.path import Path
from matplotlib.transforms import Affine2D


@dataclass(frozen=True)
class CometSymbolGeometry:
    """Backend-independent normalized geometry of Wenu's comet symbol."""

    circle_radius: float = 0.2304
    short_spoke_angles_deg: tuple[float, ...] = (
        45.0,
        90.0,
        135.0,
        180.0,
        225.0,
        270.0,
        315.0,
    )
    short_outer_radius: float = 0.36
    tail_fan_angle_deg: float = 25.0
    outer_tail_radius: float = 1.0904
    central_tail_radius: float = 1.5204

    def __post_init__(self):
        exposed_outer = self.outer_tail_radius - self.circle_radius
        exposed_central = self.central_tail_radius - self.circle_radius
        if exposed_outer <= 0.0 or self.short_outer_radius <= self.circle_radius:
            raise ValueError("comet spokes must extend outside the circle.")
        if abs(exposed_central / exposed_outer - 1.5) > 1.0e-12:
            raise ValueError(
                "central comet-tail spoke must be 1.5 times the outer spokes."
            )
        if not 0.0 < self.tail_fan_angle_deg < 180.0:
            raise ValueError("comet tail fan angle must lie between 0 and 180 deg.")

    @property
    def tail_angles_deg(self):
        half = self.tail_fan_angle_deg / 2.0
        return (-half, 0.0, half)

    @property
    def tail_outer_radii(self):
        return (
            self.outer_tail_radius,
            self.central_tail_radius,
            self.outer_tail_radius,
        )


COMET_SYMBOL_GEOMETRY = CometSymbolGeometry()


def _radial_segment(angle_deg, inner_radius, outer_radius):
    angle = np.deg2rad(angle_deg)
    unit = np.asarray((np.cos(angle), np.sin(angle)))
    return Path(
        np.asarray((inner_radius * unit, outer_radius * unit), dtype=float),
        np.asarray((Path.MOVETO, Path.LINETO), dtype=np.uint8),
    )


def _comet_head_symbol() -> Path:
    """Materialize the canonical coma and short-spoke geometry once."""
    geometry = COMET_SYMBOL_GEOMETRY
    circle = Path.unit_circle().transformed(
        Affine2D().scale(geometry.circle_radius)
    )
    spokes = tuple(
        _radial_segment(
            angle,
            geometry.circle_radius,
            geometry.short_outer_radius,
        )
        for angle in geometry.short_spoke_angles_deg
    )
    return Path.make_compound_path(circle, *spokes)


def _comet_symbol() -> Path:
    """Materialize the canonical head plus three-spoke tail once."""
    geometry = COMET_SYMBOL_GEOMETRY
    tail = tuple(
        _radial_segment(angle, geometry.circle_radius, radius)
        for angle, radius in zip(
            geometry.tail_angles_deg,
            geometry.tail_outer_radii,
            strict=True,
        )
    )
    return Path.make_compound_path(_comet_head_symbol(), *tail)


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
    return Path.unit_regular_star(5, innerCircle=0.38)


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
    comet: Path = field(default_factory=_comet_symbol)
    comet_head: Path = field(default_factory=_comet_head_symbol)

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
                "comet": self.comet,
                "comet_head": self.comet_head,
            }
        )

    def __getitem__(self, name: str) -> Path:
        return self.symbols[name]


DEFAULT_SYMBOLS = SymbolLibrary()
