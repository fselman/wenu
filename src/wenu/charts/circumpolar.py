"""Reusable north- and south-circumpolar chart type."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u

from wenu.charts.binocular import BinocularChart
from wenu.geometry.projected import ProjectedCurve


@dataclass(frozen=True)
class CircumpolarChart:
    """A circular polar chart bounded by a declination parallel."""

    observer: object
    limiting_declination_deg: float
    pole: str = "south"
    position_angle_deg: float = 0.0
    projection_radius: float = 2.0
    flip_ew: bool = True
    boundary_samples: int = 721

    def __post_init__(self):
        pole = str(self.pole).strip().lower()
        if pole not in {"north", "south"}:
            raise ValueError("pole must be 'north' or 'south'.")
        object.__setattr__(self, "pole", pole)
        limit = float(self.limiting_declination_deg)
        if not -90.0 < limit < 90.0:
            raise ValueError(
                "limiting_declination_deg must be between -90 and 90."
            )
        if pole == "south" and limit >= 0.0:
            raise ValueError(
                "A south-circumpolar limit must be negative."
            )
        if pole == "north" and limit <= 0.0:
            raise ValueError(
                "A north-circumpolar limit must be positive."
            )

    @property
    def pole_declination_deg(self):
        return -90.0 if self.pole == "south" else 90.0

    @property
    def angular_radius_deg(self):
        return abs(
            self.limiting_declination_deg
            - self.pole_declination_deg
        )

    @property
    def pole_coordinate(self):
        return SkyCoord(
            ra=0.0 * u.deg,
            dec=self.pole_declination_deg * u.deg,
            frame="fk5",
            equinox="J2000",
        )

    @property
    def binocular_chart(self):
        """Return the circular projected chart used for rendering."""
        return BinocularChart.from_coordinate(
            self.observer,
            self.pole_coordinate,
            field_diameter_deg=2.0 * self.angular_radius_deg,
            position_angle_deg=self.position_angle_deg,
            projection_radius=self.projection_radius,
            flip_ew=self.flip_ew,
            boundary_samples=self.boundary_samples,
        )

    @property
    def projection(self):
        return self.binocular_chart.projection

    @property
    def boundary(self):
        right_ascension = np.linspace(
            0.0,
            360.0,
            int(self.boundary_samples),
        )
        coordinate = SkyCoord(
            ra=right_ascension * u.deg,
            dec=np.full_like(
                right_ascension,
                self.limiting_declination_deg,
            ) * u.deg,
            frame="fk5",
            equinox="J2000",
        )
        horizontal = coordinate.transform_to(self.observer.altaz_frame)
        x, y = self.projection.project_spherical(
            horizontal.az.deg,
            horizontal.alt.deg,
        )
        return ProjectedCurve(
            x,
            y,
            closed=True,
            name=(
                "declination_"
                f"{self.limiting_declination_deg:g}"
            ),
        )

    @property
    def field_stop(self):
        # A declination parallel is a projected circle when the tangent
        # point is the corresponding celestial pole.
        return self.binocular_chart.field_stop

    @property
    def viewport(self):
        return self.binocular_chart.viewport

    @property
    def coordinate_label_anchor(self):
        return self.binocular_chart.coordinate_label_anchor

    @property
    def chart_context(self):
        return self.binocular_chart.chart_context

    def figure_size(self, width_inches=7.0):
        return self.binocular_chart.figure_size(width_inches)

    def render(self, *args, **kwargs):
        return self.binocular_chart.render(*args, **kwargs)

    def export(self, *args, **kwargs):
        return self.binocular_chart.export(*args, **kwargs)
