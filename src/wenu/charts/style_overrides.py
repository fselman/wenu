"""Render-local visual overrides applied after style and mode resolution."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite

from .style_components import StellarMagnitudeSizing


@dataclass(frozen=True)
class ChartStyleOverrides:
    """Optional caller values with precedence over resolved mode defaults."""

    constellation_linewidth: float | None = None
    constellation_line_color: str | None = None
    constellation_label_color: str | None = None
    boundary_linewidth: float | None = None
    boundary_color: str | None = None
    stellar_magnitude_sizing: StellarMagnitudeSizing | None = None

    def __post_init__(self):
        if (
            self.stellar_magnitude_sizing is not None
            and not isinstance(
                self.stellar_magnitude_sizing,
                StellarMagnitudeSizing,
            )
        ):
            raise TypeError(
                "stellar_magnitude_sizing must be StellarMagnitudeSizing."
            )
        for name in ("constellation_linewidth", "boundary_linewidth"):
            value = getattr(self, name)
            if value is None:
                continue
            if not isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"{name} must be finite and non-negative.")
        for name in (
            "constellation_line_color",
            "constellation_label_color",
            "boundary_color",
        ):
            value = getattr(self, name)
            if value is not None and not str(value).strip():
                raise ValueError(f"{name} cannot be empty.")

    def apply(self, style):
        """Return ``style`` with non-``None`` grid values replaced."""
        grids = getattr(style, "grids", None)
        if grids is None:
            raise TypeError("style overrides require a composed chart style.")
        changes = {
            name: getattr(self, name)
            for name in (
                "constellation_linewidth",
                "constellation_line_color",
                "constellation_label_color",
                "boundary_linewidth",
                "boundary_color",
            )
            if getattr(self, name) is not None
        }
        resolved = style if not changes else replace(
            style, grids=replace(grids, **changes)
        )
        if self.stellar_magnitude_sizing is None:
            return resolved
        stars = getattr(resolved, "stars", None)
        if stars is None:
            raise TypeError("stellar sizing requires a composed chart style.")
        return replace(
            resolved,
            stars=replace(
                stars,
                magnitude_sizing=self.stellar_magnitude_sizing,
            ),
        )
