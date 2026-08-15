"""Immutable common-year calendar geometry for polar planispheres."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np
from astropy.time import Time


COMMON_YEAR_MONTH_LENGTHS = (
    31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
)
COMMON_YEAR_DAY_LABELS = frozenset({5, 10, 15, 20, 25, 30})
MONTH_LABEL_KEYS = (
    "month.january",
    "month.february",
    "month.march",
    "month.april",
    "month.may",
    "month.june",
    "month.july",
    "month.august",
    "month.september",
    "month.october",
    "month.november",
    "month.december",
)


@dataclass(frozen=True)
class CalendarDayRecord:
    """One civil date and its handedness-neutral ring position."""

    month: int
    day: int
    ordinal: int
    midnight_ra_deg: float
    calendar_angle_deg: float
    label_text: str | None


@dataclass(frozen=True)
class CalendarMonthRecord:
    """One true common-year month arc and semantic label anchor."""

    month: int
    label_key: str
    start_ordinal: int
    length_days: int
    start_angle_deg: float
    end_angle_deg: float
    center_angle_deg: float
    arc_degrees: float


@dataclass(frozen=True)
class CalendarBoundaryRecord:
    """One month-boundary tick at the first day of a month."""

    month: int
    ordinal: int
    calendar_angle_deg: float


@dataclass(frozen=True)
class CommonYearCalendarScale:
    """Resolved 365-day semantic geometry without renderer policy."""

    reference_year: int
    longitude_deg: float
    standard_utc_offset_hours: float
    reference_midnight_ra_deg: float
    daily_step_deg: float
    days: tuple[CalendarDayRecord, ...]
    months: tuple[CalendarMonthRecord, ...]
    boundaries: tuple[CalendarBoundaryRecord, ...]

    @property
    def labels(self):
        return tuple(day for day in self.days if day.label_text is not None)

    def day(self, month, day):
        """Return one date record by one-based month and day."""
        month = int(month)
        day = int(day)
        if not 1 <= month <= 12:
            raise ValueError("month must be between 1 and 12.")
        length = COMMON_YEAR_MONTH_LENGTHS[month - 1]
        if not 1 <= day <= length:
            raise ValueError("day is outside the selected common-year month.")
        ordinal = sum(COMMON_YEAR_MONTH_LENGTHS[: month - 1]) + day
        return self.days[ordinal - 1]


@dataclass(frozen=True)
class CommonYearCalendarRequest:
    """Astronomical calibration for one deterministic civil date ring."""

    longitude_deg: float = -71.230289
    standard_utc_offset_hours: float = -4.0
    reference_year: int = 2026

    def __post_init__(self):
        longitude = float(self.longitude_deg)
        offset = float(self.standard_utc_offset_hours)
        year = int(self.reference_year)
        if not np.isfinite(longitude) or not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude_deg must be finite and in [-180, 180].")
        if not np.isfinite(offset) or not -14.0 <= offset <= 14.0:
            raise ValueError(
                "standard_utc_offset_hours must be finite and in [-14, 14]."
            )
        if year < 1 or year > 9998:
            raise ValueError("reference_year must be between 1 and 9998.")
        if calendar.isleap(year):
            raise ValueError("reference_year must be a common year.")
        object.__setattr__(self, "longitude_deg", longitude)
        object.__setattr__(self, "standard_utc_offset_hours", offset)
        object.__setattr__(self, "reference_year", year)

    def resolve(self):
        """Return a closed mean-common-year scale anchored at local midnight."""
        reference_ra = _local_mean_sidereal_time_deg(
            self.reference_year,
            1,
            1,
            longitude_deg=self.longitude_deg,
            standard_utc_offset_hours=self.standard_utc_offset_hours,
        )
        step = 360.0 / 365.0
        days = []
        months = []
        boundaries = []
        ordinal = 1
        for month, (length, label_key) in enumerate(
            zip(COMMON_YEAR_MONTH_LENGTHS, MONTH_LABEL_KEYS, strict=True),
            start=1,
        ):
            start_ordinal = ordinal
            start_angle = _calendar_angle(reference_ra, ordinal, step)
            boundaries.append(
                CalendarBoundaryRecord(
                    month=month,
                    ordinal=ordinal,
                    calendar_angle_deg=start_angle,
                )
            )
            for day in range(1, length + 1):
                midnight_ra = _midnight_ra(reference_ra, ordinal, step)
                days.append(
                    CalendarDayRecord(
                        month=month,
                        day=day,
                        ordinal=ordinal,
                        midnight_ra_deg=midnight_ra,
                        calendar_angle_deg=(midnight_ra + 180.0) % 360.0,
                        label_text=(
                            str(day)
                            if day in COMMON_YEAR_DAY_LABELS
                            else None
                        ),
                    )
                )
                ordinal += 1
            end_angle = _calendar_angle(reference_ra, ordinal, step)
            center_offset = (start_ordinal - 1) + length / 2.0
            center_angle = (
                reference_ra + 180.0 + center_offset * step
            ) % 360.0
            months.append(
                CalendarMonthRecord(
                    month=month,
                    label_key=label_key,
                    start_ordinal=start_ordinal,
                    length_days=length,
                    start_angle_deg=start_angle,
                    end_angle_deg=end_angle,
                    center_angle_deg=center_angle,
                    arc_degrees=length * step,
                )
            )
        return CommonYearCalendarScale(
            reference_year=self.reference_year,
            longitude_deg=self.longitude_deg,
            standard_utc_offset_hours=self.standard_utc_offset_hours,
            reference_midnight_ra_deg=reference_ra,
            daily_step_deg=step,
            days=tuple(days),
            months=tuple(months),
            boundaries=tuple(boundaries),
        )


def _midnight_ra(reference_ra_deg, ordinal, daily_step_deg):
    return (
        float(reference_ra_deg)
        + (int(ordinal) - 1) * float(daily_step_deg)
    ) % 360.0


def _calendar_angle(reference_ra_deg, ordinal, daily_step_deg):
    return (
        _midnight_ra(reference_ra_deg, ordinal, daily_step_deg) + 180.0
    ) % 360.0


def _local_mean_sidereal_time_deg(
    year,
    month,
    day,
    *,
    longitude_deg,
    standard_utc_offset_hours,
):
    offset = timezone(timedelta(hours=float(standard_utc_offset_hours)))
    local_midnight = datetime(
        int(year), int(month), int(day), tzinfo=offset
    )
    instant = Time(local_midnight.astimezone(timezone.utc))
    greenwich = float(instant.sidereal_time("mean", "greenwich").deg)
    return (greenwich + float(longitude_deg)) % 360.0
