"""Results returned by generic celestial-chart orchestration."""

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


@dataclass(frozen=True)
class LayerRenderingResult:
    """Geometry and artists produced for one registered sky layer."""

    layer: Any
    semantic_identity: Any
    spherical: Any
    projected: Any
    artists: Any
    semantic_artists: tuple[SemanticArtistRenderingResult, ...] = ()


@dataclass(frozen=True)
class ChartRenderingResult:
    """Complete result of one ``CelestialSphere.draw_chart`` call."""

    projection: Any
    renderer: Any
    viewport: Any
    layers: tuple[LayerRenderingResult, ...]

