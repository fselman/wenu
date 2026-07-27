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


@dataclass(frozen=True)
class SymbolLibrary:
    """Named normalized marker paths used by complete chart styles."""

    planetary_nebula: Path = field(
        default_factory=_circle_with_radial_ticks
    )

    @property
    def symbols(self) -> Mapping[str, Path]:
        """Return the currently implemented symbols by semantic name."""
        return MappingProxyType(
            {"planetary_nebula": self.planetary_nebula}
        )

    def __getitem__(self, name: str) -> Path:
        return self.symbols[name]


DEFAULT_SYMBOLS = SymbolLibrary()
