"""Resolved physical calendar furniture for paired polar planispheres."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.polar_calendar import (
    CommonYearCalendarRequest,
    CommonYearCalendarScale,
)
from wenu.charts.polar_planisphere_pair import PolarPlanispherePair


@dataclass(frozen=True)
class PolarCalendarTick:
    """One physical daily tick, optionally strengthened at a month boundary."""

    month: int
    day: int
    ordinal: int
    angle_deg: float
    inner: tuple[float, float]
    outer: tuple[float, float]
    month_boundary: bool
    labeled_day: bool = False


@dataclass(frozen=True)
class PolarCalendarLabel:
    """One already-positioned semantic day or month label."""

    role: str
    text: str | None
    text_key: str | None
    month: int
    day: int | None
    angle_deg: float
    position: tuple[float, float]
    rotation_deg: float
    base_outward: bool = True
    text_mirrored: bool = False


@dataclass(frozen=True)
class PolarCalendarFaceFurniture:
    """Renderer-neutral calendar geometry for one physical disk face."""

    face: str
    center: tuple[float, float]
    star_disk_radius_mm: float
    outer_radius_mm: float
    ticks: tuple[PolarCalendarTick, ...]
    day_labels: tuple[PolarCalendarLabel, ...]
    month_labels: tuple[PolarCalendarLabel, ...]

    @property
    def labels(self):
        return self.day_labels + self.month_labels


@dataclass(frozen=True)
class PolarCalendarPairFurniture:
    """Matched calendar furniture with opposite face handedness."""

    calendar: CommonYearCalendarScale
    south: PolarCalendarFaceFurniture
    north: PolarCalendarFaceFurniture

    @property
    def faces(self):
        return self.south, self.north


@dataclass(frozen=True)
class PolarCalendarFurnitureRequest:
    """Resolve one common calendar scale onto matched physical disk faces."""

    calendar: CommonYearCalendarRequest = CommonYearCalendarRequest()
    star_disk_radius_fraction: float = 0.80
    day_tick_length_fraction: float = 0.025
    month_tick_length_fraction: float = 0.045
    day_label_radius_fraction: float = 0.845
    month_label_radius_fraction: float = 0.88

    def __post_init__(self):
        if not isinstance(self.calendar, CommonYearCalendarRequest):
            raise TypeError(
                "calendar must be a CommonYearCalendarRequest value."
            )
        values = np.asarray(
            (
                self.star_disk_radius_fraction,
                self.day_tick_length_fraction,
                self.month_tick_length_fraction,
                self.day_label_radius_fraction,
                self.month_label_radius_fraction,
            ),
            dtype=float,
        )
        if not np.all(np.isfinite(values)):
            raise ValueError("Calendar furniture fractions must be finite.")
        star, day_tick, month_tick, day_label, month_label = values
        if not 0.0 < star < 1.0:
            raise ValueError(
                "star_disk_radius_fraction must be between 0 and 1."
            )
        if not 0.0 < day_tick < month_tick:
            raise ValueError(
                "tick fractions must be positive, with month ticks longer."
            )
        if star + month_tick >= 1.0:
            raise ValueError(
                "month ticks must remain inside the physical disk."
            )
        if not star < day_label < month_label < 1.0:
            raise ValueError(
                "label radii must be ordered between the star disk and edge."
            )
        object.__setattr__(self, "star_disk_radius_fraction", float(star))
        object.__setattr__(self, "day_tick_length_fraction", float(day_tick))
        object.__setattr__(
            self, "month_tick_length_fraction", float(month_tick)
        )
        object.__setattr__(self, "day_label_radius_fraction", float(day_label))
        object.__setattr__(
            self, "month_label_radius_fraction", float(month_label)
        )

    def resolve(self, pair):
        """Return furniture derived from one already-resolved disk pair."""
        if not isinstance(pair, PolarPlanispherePair):
            raise TypeError("pair must be a PolarPlanispherePair value.")
        scale = self.calendar.resolve()
        south = self._resolve_face(
            "south", pair.south, pair.south_registration, scale
        )
        north = self._resolve_face(
            "north", pair.north, pair.north_registration, scale
        )
        return PolarCalendarPairFurniture(
            calendar=scale,
            south=south,
            north=north,
        )

    def _resolve_face(self, face, chart, registration, scale):
        outer_radius = registration.outer_radius_mm
        star_radius = (
            registration.calendar_radius_mm
            if registration.calendar_radius_mm is not None
            else outer_radius * self.star_disk_radius_fraction
        )
        day_label_radius = outer_radius * self.day_label_radius_fraction
        month_label_radius = outer_radius * self.month_label_radius_fraction
        if star_radius >= day_label_radius:
            raise ValueError(
                "calendar_radius_mm must leave room for calendar labels."
            )
        if (
            star_radius
            + outer_radius * self.month_tick_length_fraction
            >= outer_radius
        ):
            raise ValueError(
                "calendar_radius_mm must leave room for month ticks."
            )
        boundary_months = {boundary.month for boundary in scale.boundaries}
        ticks = []
        for day in scale.days:
            angle = _paper_calendar_angle(chart, day.midnight_ra_deg)
            month_boundary = day.day == 1 and day.month in boundary_months
            length_fraction = (
                self.month_tick_length_fraction
                if month_boundary
                else self.day_tick_length_fraction
            )
            ticks.append(
                PolarCalendarTick(
                    month=day.month,
                    day=day.day,
                    ordinal=day.ordinal,
                    angle_deg=angle,
                    inner=_radial_point(angle, star_radius),
                    outer=_radial_point(
                        angle, star_radius + outer_radius * length_fraction
                    ),
                    month_boundary=month_boundary,
                    labeled_day=day.label_text is not None,
                )
            )
        day_labels = tuple(
            _label(
                role="day",
                text=day.label_text,
                text_key=None,
                month=day.month,
                day=day.day,
                angle_deg=_paper_calendar_angle(
                    chart, day.midnight_ra_deg
                ),
                radius_mm=day_label_radius,
            )
            for day in scale.labels
        )
        month_labels = tuple(
            _label(
                role="month",
                text=None,
                text_key=month.label_key,
                month=month.month,
                day=None,
                angle_deg=_paper_calendar_angle(
                    chart, (month.center_angle_deg - 180.0) % 360.0
                ),
                radius_mm=month_label_radius,
            )
            for month in scale.months
        )
        return PolarCalendarFaceFurniture(
            face=face,
            center=(0.0, 0.0),
            star_disk_radius_mm=star_radius,
            outer_radius_mm=outer_radius,
            ticks=tuple(ticks),
            day_labels=day_labels,
            month_labels=month_labels,
        )


def _paper_calendar_angle(chart, midnight_ra_deg):
    x, y = chart.projection.project_spherical(
        np.asarray((float(midnight_ra_deg),)),
        np.asarray((0.0,)),
    )
    ra_angle = np.degrees(np.arctan2(float(y[0]), float(x[0])))
    return (ra_angle + 180.0) % 360.0


def _radial_point(angle_deg, radius_mm):
    angle = np.deg2rad(float(angle_deg))
    radius = float(radius_mm)
    return radius * np.cos(angle), radius * np.sin(angle)


def _label(
    *, role, text, text_key, month, day, angle_deg, radius_mm
):
    return PolarCalendarLabel(
        role=role,
        text=text,
        text_key=text_key,
        month=month,
        day=day,
        angle_deg=angle_deg,
        position=_radial_point(angle_deg, radius_mm),
        rotation_deg=(angle_deg + 90.0) % 360.0,
    )
