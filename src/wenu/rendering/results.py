"""Renderer-side records carried into chart rendering results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from wenu.rendering.paint_roles import PaintRole


@dataclass(frozen=True)
class SemanticArtistRenderingResult:
    """One renderer artist with Wenu identity and paint position."""

    artist: Any
    svg_id: str
    zorder: float
    paint_role: PaintRole | None
