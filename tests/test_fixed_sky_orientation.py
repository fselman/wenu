"""Renderer-neutral fixed-sky circumpolar orientation tests."""

from datetime import datetime, timezone

import numpy as np

from wenu.charts.fixed_sky_orientation import (
    circumpolar_orientation_reference,
    fixed_sky_circumpolar_orientation,
)
from wenu.charts.circumpolar import CircumpolarChart
from wenu.observer import Observer


def observers():
    anchor = Observer(
        location="La Ligua",
        time=datetime(2026, 8, 22, 1, tzinfo=timezone.utc),
    )
    frame = Observer(
        location="La Ligua",
        time=datetime(2026, 8, 22, 7, tzinfo=timezone.utc),
    )
    return anchor, frame


def projected_reference(observer, *, position_angle_deg):
    chart = CircumpolarChart(
        observer,
        limiting_declination_deg=-50.0,
        pole="south",
        position_angle_deg=position_angle_deg,
    )
    horizontal = circumpolar_orientation_reference("south").transform_to(
        observer.altaz_frame
    )
    return np.asarray(
        chart.projection.project_spherical(
            horizontal.az.deg,
            horizontal.alt.deg,
        ),
        dtype=float,
    )


def test_anchor_orientation_is_zero_for_default_anchor_rotation():
    anchor, frame = observers()
    try:
        orientation = fixed_sky_circumpolar_orientation(
            anchor,
            anchor,
            pole="south",
        )
    finally:
        anchor.close()
        frame.close()

    assert orientation.position_angle_deg == 0.0


def test_orientation_keeps_fixed_celestial_reference_projected_in_place():
    anchor, frame = observers()
    try:
        orientation = fixed_sky_circumpolar_orientation(
            anchor,
            frame,
            pole="south",
        )
        anchored = projected_reference(anchor, position_angle_deg=0.0)
        corrected = projected_reference(
            frame,
            position_angle_deg=orientation.position_angle_deg,
        )
    finally:
        anchor.close()
        frame.close()

    assert np.allclose(corrected, anchored, atol=1.0e-12)


def test_orientation_rotates_local_horizon_while_celestial_scene_stays_fixed():
    anchor, frame = observers()
    try:
        orientation = fixed_sky_circumpolar_orientation(
            anchor,
            frame,
            pole="south",
        )
        anchor_chart = CircumpolarChart(
            anchor,
            limiting_declination_deg=-50.0,
            pole="south",
        )
        frame_chart = CircumpolarChart(
            frame,
            limiting_declination_deg=-50.0,
            pole="south",
            position_angle_deg=orientation.position_angle_deg,
        )
        anchor_horizon = np.asarray(
            anchor_chart.projection.project_spherical(180.0, 0.0)
        )
        rotated_horizon = np.asarray(
            frame_chart.projection.project_spherical(180.0, 0.0)
        )
    finally:
        anchor.close()
        frame.close()

    assert not np.allclose(rotated_horizon, anchor_horizon, atol=1.0e-6)


def test_orientation_uses_astronomical_transform_not_solar_hour_shortcut():
    anchor, frame = observers()
    try:
        orientation = fixed_sky_circumpolar_orientation(
            anchor,
            frame,
            pole="south",
        )
    finally:
        anchor.close()
        frame.close()

    assert not np.isclose(
        abs(orientation.position_angle_deg),
        90.0,
        atol=0.01,
    )
