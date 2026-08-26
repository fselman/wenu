"""Neutral records shared by chart orchestration and renderers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SemanticArtistRenderingResult:
    """One renderer artist with Wenu identity and paint position."""

    artist: Any
    svg_id: str
    zorder: float
    paint_role: Any | None
