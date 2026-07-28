"""Output-neutral geometric context supplied by chart specifications."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Any

from wenu.geometry.viewport import Viewport


class BoundaryKind(str, Enum):
    """Semantic shape used for clipping and boundary label placement."""

    RECTANGULAR = "rectangular"
    CIRCULAR = "circular"
    ARBITRARY = "arbitrary"


@dataclass(frozen=True)
class ChartContext:
    """Geometry exposed by a chart type to composition policies.

    This value deliberately contains no colors, symbols, catalogue limits,
    renderer objects, or Matplotlib artists.
    """

    viewport: Viewport
    angular_width_deg: float
    angular_height_deg: float
    tangent_longitude_deg: float
    tangent_latitude_deg: float
    boundary_kind: BoundaryKind = BoundaryKind.RECTANGULAR
    clip_boundary: Any | None = None
    visible_solid_angle_sq_deg: float | None = None

    def __post_init__(self) -> None:
        values = (
            self.angular_width_deg,
            self.angular_height_deg,
            self.tangent_longitude_deg,
            self.tangent_latitude_deg,
        )
        if not all(isfinite(float(value)) for value in values):
            raise ValueError("Chart-context angular values must be finite.")
        if not 0.0 < float(self.angular_width_deg) <= 360.0:
            raise ValueError(
                "angular_width_deg must be between 0 and 360 degrees."
            )
        if not 0.0 < float(self.angular_height_deg) <= 360.0:
            raise ValueError(
                "angular_height_deg must be between 0 and 360 degrees."
            )
        if not -90.0 <= float(self.tangent_latitude_deg) <= 90.0:
            raise ValueError(
                "tangent_latitude_deg must be between -90 and 90."
            )
        if self.visible_solid_angle_sq_deg is not None:
            solid_angle = float(self.visible_solid_angle_sq_deg)
            if not isfinite(solid_angle) or solid_angle <= 0.0:
                raise ValueError(
                    "visible_solid_angle_sq_deg must be positive and finite."
                )

    @property
    def aspect_ratio(self) -> float:
        """Natural projected width divided by projected height."""
        return self.viewport.aspect_ratio

    @property
    def angular_area_deg2(self) -> float:
        """Rectangular angular-area proxy used by initial detail policies."""
        return self.angular_width_deg * self.angular_height_deg
