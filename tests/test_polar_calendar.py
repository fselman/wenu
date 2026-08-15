from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest
from astropy.time import Time

from wenu import (
    COMMON_YEAR_DAY_LABELS,
    COMMON_YEAR_MONTH_LENGTHS,
    CommonYearCalendarRequest,
)


LA_LIGUA_LONGITUDE_DEG = -71.230289


def circular_difference(left, right):
    return (float(left) - float(right) + 180.0) % 360.0 - 180.0


def actual_midnight_ra(month, day):
    offset = timezone(timedelta(hours=-4.0))
    local_midnight = datetime(2026, month, day, tzinfo=offset)
    instant = Time(local_midnight.astimezone(timezone.utc))
    greenwich = instant.sidereal_time("mean", "greenwich").deg
    return (greenwich + LA_LIGUA_LONGITUDE_DEG) % 360.0


def test_common_year_scale_has_every_real_date_once():
    scale = CommonYearCalendarRequest().resolve()

    assert len(scale.days) == 365
    assert tuple(day.ordinal for day in scale.days) == tuple(range(1, 366))
    assert len({(day.month, day.day) for day in scale.days}) == 365
    assert (2, 29) not in {(day.month, day.day) for day in scale.days}
    assert tuple(month.length_days for month in scale.months) == (
        COMMON_YEAR_MONTH_LENGTHS
    )


def test_day_labels_use_the_requested_five_day_cadence():
    scale = CommonYearCalendarRequest().resolve()

    assert COMMON_YEAR_DAY_LABELS == frozenset({5, 10, 15, 20, 25, 30})
    assert len(scale.labels) == 71
    for month in range(1, 13):
        expected = sorted(
            day
            for day in COMMON_YEAR_DAY_LABELS
            if day <= COMMON_YEAR_MONTH_LENGTHS[month - 1]
        )
        actual = [
            day.day for day in scale.labels if day.month == month
        ]
        assert actual == expected
    assert [day.day for day in scale.labels if day.month == 2] == [
        5, 10, 15, 20, 25
    ]


def test_month_records_follow_true_month_arcs_and_boundaries():
    scale = CommonYearCalendarRequest().resolve()

    assert len(scale.months) == 12
    assert len(scale.boundaries) == 12
    assert sum(month.arc_degrees for month in scale.months) == pytest.approx(
        360.0
    )
    for month, boundary in zip(
        scale.months, scale.boundaries, strict=True
    ):
        first_day = scale.days[month.start_ordinal - 1]
        assert boundary.month == month.month
        assert boundary.ordinal == month.start_ordinal
        assert boundary.calendar_angle_deg == pytest.approx(
            first_day.calendar_angle_deg
        )
        assert month.start_angle_deg == pytest.approx(
            first_day.calendar_angle_deg
        )
        expected_center = (
            month.start_angle_deg + month.arc_degrees / 2.0
        ) % 360.0
        assert circular_difference(
            month.center_angle_deg, expected_center
        ) == pytest.approx(0.0)


def test_daily_scale_closes_without_a_new_year_gap():
    scale = CommonYearCalendarRequest().resolve()
    angles = [day.calendar_angle_deg for day in scale.days]
    angles.append(angles[0] + 360.0)

    assert np.diff(np.unwrap(np.deg2rad(angles))) == pytest.approx(
        np.deg2rad(scale.daily_step_deg)
    )
    assert scale.daily_step_deg == pytest.approx(360.0 / 365.0)


def test_la_ligua_anchor_is_standard_time_local_midnight():
    scale = CommonYearCalendarRequest().resolve()

    assert scale.longitude_deg == pytest.approx(LA_LIGUA_LONGITUDE_DEG)
    assert scale.standard_utc_offset_hours == pytest.approx(-4.0)
    assert circular_difference(
        scale.reference_midnight_ra_deg, actual_midnight_ra(1, 1)
    ) == pytest.approx(0.0, abs=1e-10)


@pytest.mark.parametrize(
    "month,day",
    ((3, 20), (6, 21), (9, 22), (12, 21)),
)
def test_mean_common_year_tracks_seasonal_midnight_ra(month, day):
    scale = CommonYearCalendarRequest().resolve()

    error = circular_difference(
        scale.day(month, day).midnight_ra_deg,
        actual_midnight_ra(month, day),
    )
    assert abs(error) < 0.3


def test_calendar_angle_places_midnight_ra_on_upward_meridian():
    scale = CommonYearCalendarRequest().resolve()

    for day in scale.days:
        assert circular_difference(
            day.calendar_angle_deg, day.midnight_ra_deg + 180.0
        ) == pytest.approx(0.0)


def test_calendar_request_and_records_are_immutable_and_validated():
    request = CommonYearCalendarRequest()
    with pytest.raises(FrozenInstanceError):
        request.reference_year = 2025
    with pytest.raises(ValueError, match="common year"):
        CommonYearCalendarRequest(reference_year=2024)
    with pytest.raises(ValueError, match="longitude"):
        CommonYearCalendarRequest(longitude_deg=181.0)
    with pytest.raises(ValueError, match="standard_utc_offset_hours"):
        CommonYearCalendarRequest(standard_utc_offset_hours=15.0)

    scale = request.resolve()
    assert scale.day(12, 31).ordinal == 365
    with pytest.raises(ValueError, match="month"):
        scale.day(13, 1)
    with pytest.raises(ValueError, match="outside"):
        scale.day(2, 29)
