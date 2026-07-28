"""Output-medium modes for chart composition."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .context import ChartContext


@dataclass(frozen=True)
class ResolvedMode:
    """Concrete output dimensions and visual scale factors."""

    width_inches: float
    height_inches: float
    dpi: int
    font_scale: float
    line_scale: float
    symbol_scale: float
    contrast_scale: float
    transparent: bool
    prefer_vector: bool

    def __post_init__(self) -> None:
        positive = (
            self.width_inches,
            self.height_inches,
            self.font_scale,
            self.line_scale,
            self.symbol_scale,
            self.contrast_scale,
        )
        if not all(isfinite(float(value)) and value > 0.0 for value in positive):
            raise ValueError("Mode dimensions and scales must be positive.")
        if int(self.dpi) <= 0:
            raise ValueError("dpi must be positive.")

    @property
    def pixel_size(self) -> tuple[int, int]:
        """Nominal raster dimensions at the resolved DPI."""
        return (
            round(self.width_inches * self.dpi),
            round(self.height_inches * self.dpi),
        )

    @property
    def printable_area_in2(self) -> float:
        """Physical output area in square inches."""
        return self.width_inches * self.height_inches


@dataclass(frozen=True)
class ChartMode:
    """Output-medium configuration resolved against a chart context."""

    width_inches: float = 7.0
    height_inches: float | None = None
    dpi: int = 300
    font_scale: float = 1.0
    line_scale: float = 1.0
    symbol_scale: float = 1.0
    contrast_scale: float = 1.0
    transparent: bool = False
    prefer_vector: bool = False

    def resolve(self, context: ChartContext) -> ResolvedMode:
        """Resolve the natural height without modifying chart geometry."""
        width = float(self.width_inches)
        height = (
            width / context.aspect_ratio
            if self.height_inches is None
            else float(self.height_inches)
        )
        return ResolvedMode(
            width_inches=width,
            height_inches=height,
            dpi=int(self.dpi),
            font_scale=float(self.font_scale),
            line_scale=float(self.line_scale),
            symbol_scale=float(self.symbol_scale),
            contrast_scale=float(self.contrast_scale),
            transparent=bool(self.transparent),
            prefer_vector=bool(self.prefer_vector),
        )


@dataclass(frozen=True)
class PrintMode(ChartMode):
    """Defaults suitable for high-resolution printed charts."""

    dpi: int = 300
    font_scale: float = 1.0
    line_scale: float = 1.0
    symbol_scale: float = 1.0
    contrast_scale: float = 1.0
    prefer_vector: bool = True


@dataclass(frozen=True)
class PresentationMode(ChartMode):
    """Defaults suitable for projected or screen presentations."""

    dpi: int = 160
    font_scale: float = 1.35
    line_scale: float = 1.25
    symbol_scale: float = 1.25
    contrast_scale: float = 1.12
    prefer_vector: bool = False
