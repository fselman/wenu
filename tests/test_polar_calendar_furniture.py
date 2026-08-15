from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from wenu import (
    CommonYearCalendarRequest,
    PolarCalendarFurnitureRequest,
    PolarCalendarPairFurniture,
    PolarPlanispherePairRequest,
)


def circular_difference(left, right):
    return (float(left) - float(right) + 180.0) % 360.0 - 180.0


@pytest.mark.parametrize(
    "projection_name",
    ("polar_azimuthal_equidistant", "stereographic"),
)
def test_calendar_furniture_resolves_both_faces_and_every_daily_tick(
    projection_name,
):
    pair = PolarPlanispherePairRequest(
        projection_name=projection_name
    ).resolve()

    furniture = PolarCalendarFurnitureRequest().resolve(pair)

    assert isinstance(furniture, PolarCalendarPairFurniture)
    assert furniture.faces == (furniture.south, furniture.north)
    assert len(furniture.calendar.days) == 365
    for face in furniture.faces:
        assert len(face.ticks) == 365
        assert sum(tick.month_boundary for tick in face.ticks) == 12
        assert tuple(tick.ordinal for tick in face.ticks) == tuple(
            range(1, 366)
        )


def test_day_and_month_labels_are_semantic_and_at_true_arc_centers():
    pair = PolarPlanispherePairRequest().resolve()
    furniture = PolarCalendarFurnitureRequest().resolve(pair)

    for face, chart in (
        (furniture.south, pair.south),
        (furniture.north, pair.north),
    ):
        assert len(face.day_labels) == 71
        assert len(face.month_labels) == 12
        assert {label.day for label in face.day_labels} == {
            5, 10, 15, 20, 25, 30
        }
        assert all(label.text_key is None for label in face.day_labels)
        assert all(label.text is None for label in face.month_labels)
        assert tuple(label.text_key for label in face.month_labels) == tuple(
            month.label_key for month in furniture.calendar.months
        )
        for label, month in zip(
            face.month_labels, furniture.calendar.months, strict=True
        ):
            expected = paper_calendar_angle(
                chart, (month.center_angle_deg - 180.0) % 360.0
            )
            assert circular_difference(
                label.angle_deg, expected
            ) == pytest.approx(0.0)


def test_calendar_geometry_reserves_the_star_disk_and_strengthens_boundaries():
    pair = PolarPlanispherePairRequest(physical_diameter_mm=200.0).resolve()
    furniture = PolarCalendarFurnitureRequest().resolve(pair)

    for face in furniture.faces:
        assert face.star_disk_radius_mm == pytest.approx(80.0)
        assert face.outer_radius_mm == pytest.approx(100.0)
        for tick in face.ticks:
            assert np.hypot(*tick.inner) == pytest.approx(80.0)
            expected = 84.5 if tick.month_boundary else 82.5
            assert np.hypot(*tick.outer) == pytest.approx(expected)
        for label in face.labels:
            assert np.hypot(*label.position) > face.star_disk_radius_mm
            assert np.hypot(*label.position) < face.outer_radius_mm


def test_explicit_paired_calendar_radius_is_the_star_disk_boundary():
    pair = PolarPlanispherePairRequest(calendar_radius_mm=78.0).resolve()

    furniture = PolarCalendarFurnitureRequest().resolve(pair)

    assert furniture.south.star_disk_radius_mm == pytest.approx(78.0)
    assert furniture.north.star_disk_radius_mm == pytest.approx(78.0)


def test_explicit_calendar_radius_must_leave_furniture_room():
    pair = PolarPlanispherePairRequest(calendar_radius_mm=92.0).resolve()

    with pytest.raises(ValueError, match="calendar_radius_mm"):
        PolarCalendarFurnitureRequest().resolve(pair)


def test_label_rotation_places_each_typographic_base_outward():
    furniture = PolarCalendarFurnitureRequest().resolve(
        PolarPlanispherePairRequest().resolve()
    )

    for face in furniture.faces:
        for label in face.labels:
            assert label.base_outward is True
            assert label.text_mirrored is False
            assert circular_difference(
                label.rotation_deg, label.angle_deg + 90.0
            ) == pytest.approx(0.0)


@pytest.mark.parametrize(
    "projection_name",
    ("polar_azimuthal_equidistant", "stereographic"),
)
def test_faces_have_opposite_date_handedness_without_mirrored_text(
    projection_name,
):
    pair = PolarPlanispherePairRequest(
        projection_name=projection_name
    ).resolve()
    furniture = PolarCalendarFurnitureRequest().resolve(pair)

    for south, north in zip(
        furniture.south.ticks, furniture.north.ticks, strict=True
    ):
        assert north.inner[0] == pytest.approx(-south.inner[0])
        assert north.inner[1] == pytest.approx(south.inner[1])
    south_step = circular_difference(
        furniture.south.ticks[1].angle_deg,
        furniture.south.ticks[0].angle_deg,
    )
    north_step = circular_difference(
        furniture.north.ticks[1].angle_deg,
        furniture.north.ticks[0].angle_deg,
    )
    assert south_step == pytest.approx(-north_step)


@pytest.mark.parametrize("face_name", ("south", "north"))
def test_bottom_date_alignment_places_midnight_ra_directly_up(face_name):
    pair = PolarPlanispherePairRequest().resolve()
    furniture = PolarCalendarFurnitureRequest().resolve(pair)
    face = getattr(furniture, face_name)
    chart = getattr(pair, face_name)

    for month, day in ((1, 1), (3, 20), (6, 21), (9, 22), (12, 31)):
        record = furniture.calendar.day(month, day)
        tick = face.ticks[record.ordinal - 1]
        disk_rotation = -90.0 - tick.angle_deg
        ra_angle = projected_ra_angle(chart, record.midnight_ra_deg)
        assert circular_difference(
            ra_angle + disk_rotation, 90.0
        ) == pytest.approx(0.0, abs=1.0e-10)


def test_request_is_immutable_configurable_and_validated():
    calendar = CommonYearCalendarRequest(longitude_deg=-70.5)
    request = PolarCalendarFurnitureRequest(
        calendar=calendar,
        star_disk_radius_fraction=0.75,
    )
    pair = PolarPlanispherePairRequest().resolve()

    furniture = request.resolve(pair)

    assert furniture.calendar.longitude_deg == pytest.approx(-70.5)
    assert furniture.south.star_disk_radius_mm == pytest.approx(73.125)
    with pytest.raises(FrozenInstanceError):
        request.star_disk_radius_fraction = 0.8
    with pytest.raises(TypeError, match="calendar"):
        PolarCalendarFurnitureRequest(calendar=object())
    with pytest.raises(ValueError, match="star_disk"):
        PolarCalendarFurnitureRequest(star_disk_radius_fraction=1.0)
    with pytest.raises(ValueError, match="month ticks"):
        PolarCalendarFurnitureRequest(
            day_tick_length_fraction=0.05,
            month_tick_length_fraction=0.04,
        )
    with pytest.raises(ValueError, match="label radii"):
        PolarCalendarFurnitureRequest(day_label_radius_fraction=0.7)
    with pytest.raises(TypeError, match="pair"):
        request.resolve(object())


def test_calendar_furniture_types_are_public():
    import wenu

    for name in (
        "PolarCalendarFaceFurniture",
        "PolarCalendarFurnitureRequest",
        "PolarCalendarLabel",
        "PolarCalendarPairFurniture",
        "PolarCalendarTick",
    ):
        assert name in wenu.__all__


def projected_ra_angle(chart, right_ascension_deg):
    x, y = chart.projection.project_spherical(
        np.asarray((right_ascension_deg,)), np.asarray((0.0,))
    )
    return np.degrees(np.arctan2(y[0], x[0])) % 360.0


def paper_calendar_angle(chart, right_ascension_deg):
    return (projected_ra_angle(chart, right_ascension_deg) + 180.0) % 360.0
