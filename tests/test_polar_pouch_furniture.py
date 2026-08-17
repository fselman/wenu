"""Renderer-neutral physical geometry for the folded polar pouch."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from wenu import (
    PolarHorizonFaceOverlay,
    PolarHorizonPairOverlay,
    PolarPouchFurnitureRequest,
    PolarPouchPairFurniture,
)


def overlays():
    common = {
        "page_size_mm": (210.0, 297.0),
        "disk_center_mm": (105.0, 148.5),
        "disk_radius_mm": 97.5,
        "site_latitude_deg": -32.443342,
        "cut_clearance_mm": 1.0,
        "pole_position_mm": (105.0, 148.5),
    }
    south = PolarHorizonFaceOverlay(
        face="south",
        horizon_segments_mm=(((7.5, 148.5), (105.0, 120.0), (202.5, 148.5)),),
        meridian_horizon_position_mm=(105.0, 120.0),
        **common,
    )
    north = PolarHorizonFaceOverlay(
        face="north",
        horizon_segments_mm=(((7.5, 148.5), (105.0, 177.0), (202.5, 148.5)),),
        meridian_horizon_position_mm=(105.0, 177.0),
        **common,
    )
    return PolarHorizonPairOverlay(south=south, north=north)


def furniture(**options):
    return PolarPouchFurnitureRequest(**options).resolve(overlays())


def test_complete_disk_fits_above_the_fold_and_registers_on_it():
    value = furniture()

    assert isinstance(value, PolarPouchPairFurniture)
    assert value.faces == (value.south, value.north)
    for face in value.faces:
        assert face.page_size_mm == pytest.approx((210.0, 297.0))
        assert face.fold_y_mm == pytest.approx(97.0)
        assert face.disk_center_mm == pytest.approx((105.0, 194.5))
        assert face.disk_center_mm[1] - face.disk_radius_mm == pytest.approx(
            face.fold_y_mm
        )
        assert face.disk_center_mm[1] + face.disk_radius_mm == pytest.approx(
            292.0
        )
        np.testing.assert_allclose(
            face.fold_line_mm,
            ((5.0, 97.0), (205.0, 97.0)),
        )


def test_horizon_geometry_is_translated_without_recalculation():
    value = furniture()

    np.testing.assert_allclose(
        value.south.horizon_segments_mm[0],
        ((7.5, 194.5), (105.0, 166.0), (202.5, 194.5)),
    )
    np.testing.assert_allclose(
        value.north.horizon_segments_mm[0],
        ((7.5, 194.5), (105.0, 223.0), (202.5, 194.5)),
    )
    for face in value.faces:
        np.testing.assert_allclose(
            face.sky_window_boundary_mm[0],
            face.sky_window_boundary_mm[-1],
        )
        assert max(point[1] for point in face.sky_window_boundary_mm) == (
            pytest.approx(292.0)
        )


def test_three_identical_date_windows_span_37_5_degrees_with_5_degree_gaps():
    value = furniture()

    for face in value.faces:
        assert len(face.date_windows) == 3
        assert tuple(window.span_deg for window in face.date_windows) == (
            37.5,
            37.5,
            37.5,
        )
        for left, right in zip(
            face.date_windows[:-1], face.date_windows[1:], strict=True
        ):
            assert right.start_angle_deg - left.end_angle_deg == pytest.approx(
                5.0
            )
        assert face.date_windows == value.south.date_windows
        assert face.date_windows[0].start_angle_deg == pytest.approx(208.75)
        assert face.date_windows[-1].end_angle_deg == pytest.approx(331.25)
        assert face.date_windows[0].outer_radius_mm == pytest.approx(92.625)
        assert face.date_windows[0].inner_radius_mm == pytest.approx(80.925)


def test_hour_numbers_are_upright_and_short_marks_lie_outside_them():
    value = furniture()

    assert tuple(mark.hour for mark in value.south.hour_marks) == (
        19,
        20,
        21,
        22,
        23,
        0,
        1,
        2,
        3,
        4,
        5,
    )
    assert tuple(mark.angle_deg for mark in value.south.hour_marks) == tuple(
        reversed(tuple(mark.angle_deg for mark in value.north.hour_marks))
    )
    for face in value.faces:
        center = np.asarray(face.disk_center_mm)
        for mark in face.hour_marks:
            numeral = np.linalg.norm(
                np.asarray(mark.numeral_position_mm) - center
            )
            tick_start = np.linalg.norm(np.asarray(mark.tick_start_mm) - center)
            tick_end = np.linalg.norm(np.asarray(mark.tick_end_mm) - center)
            assert numeral < face.hour_circle_radius_mm
            assert tick_start == pytest.approx(face.hour_circle_radius_mm)
            assert tick_start < tick_end
            assert tick_end < face.date_windows[0].inner_radius_mm
            assert -90.0 <= mark.numeral_rotation_deg <= 90.0


def test_geographic_letters_are_fixed_pouch_furniture_not_sky_anchors():
    value = furniture()
    south = {}
    for label in value.south.labels:
        south.setdefault(label.text, []).append(label)
    north = {}
    for label in value.north.labels:
        north.setdefault(label.text, []).append(label)

    assert tuple(south) == (
        "E",
        "W",
        "S",
        "HORIZONTE",
        "Muchos cielos, un firmamento",
    )
    assert tuple(north) == ("W", "E", "N", "HORIZONTE")
    assert len(south["HORIZONTE"]) == 2
    assert len(north["HORIZONTE"]) == 2
    assert south["E"][0].position_mm[0] < south["W"][0].position_mm[0]
    assert north["W"][0].position_mm[0] < north["E"][0].position_mm[0]
    for face, labels, names in (
        (value.south, south, ("E", "S", "W")),
        (value.north, north, ("W", "N", "E")),
    ):
        horizon = np.asarray(max(face.horizon_segments_mm, key=len))
        order = np.argsort(horizon[:, 0])
        for name in names:
            label = labels[name][0]
            curve_y = np.interp(
                label.position_mm[0],
                horizon[order, 0],
                horizon[order, 1],
            )
            assert curve_y - label.position_mm[1] == pytest.approx(7.0)
    assert value.south.fold_y_mm < (
        south["Muchos cielos, un firmamento"][0].position_mm[1]
    ) < south["S"][0].position_mm[1]
    assert south["HORIZONTE"][0].rotation_deg < 0.0
    assert south["HORIZONTE"][1].rotation_deg > 0.0
    assert all(
        label.role == "horizon_bold"
        for label in (*south["HORIZONTE"], *north["HORIZONTE"])
    )
    assert not hasattr(overlays().south, "cardinals")


def test_labels_use_the_complete_horizon_when_resolver_splits_both_sides():
    value = overlays()
    split = type(value)(
        south=type(value.south)(
            **{
                **value.south.__dict__,
                "horizon_segments_mm": (
                    ((7.5, 148.5), (105.0, 120.0)),
                    ((105.0, 120.0), (202.5, 148.5)),
                ),
            }
        ),
        north=type(value.north)(
            **{
                **value.north.__dict__,
                "horizon_segments_mm": (
                    ((7.5, 148.5), (105.0, 177.0)),
                    ((105.0, 177.0), (202.5, 148.5)),
                ),
            }
        ),
    )
    resolved = PolarPouchFurnitureRequest().resolve(split)

    for face in resolved.faces:
        cardinals = [
            label for label in face.labels if label.role == "cardinal"
        ]
        horizons = [
            label for label in face.labels if label.text == "HORIZONTE"
        ]
        cardinal_x = tuple(
            label.position_mm[0] for label in cardinals
        )
        assert min(cardinal_x) < face.disk_center_mm[0]
        assert max(cardinal_x) > face.disk_center_mm[0]
        assert horizons[0].position_mm[0] < face.disk_center_mm[0]
        assert horizons[1].position_mm[0] > face.disk_center_mm[0]


def test_glue_strips_are_safe_and_request_is_validated_and_public():
    value = furniture()

    for face in value.faces:
        assert tuple(strip.side for strip in face.glue_strips) == (
            "left",
            "right",
        )
        assert face.glue_strips[0].lower_left_mm == pytest.approx((5.0, 97.0))
        assert face.glue_strips[1].upper_right_mm == pytest.approx((205.0, 297.0))
        assert face.glue_strips[0].upper_right_mm[0] <= (
            face.disk_center_mm[0] - face.disk_radius_mm
        )
        assert face.glue_strips[1].lower_left_mm[0] >= (
            face.disk_center_mm[0] + face.disk_radius_mm
        )
    request = PolarPouchFurnitureRequest()
    with pytest.raises(FrozenInstanceError):
        request.safe_margin_mm = 4.0
    with pytest.raises(TypeError, match="overlays"):
        request.resolve(object())
    with pytest.raises(ValueError, match="three date windows"):
        PolarPouchFurnitureRequest(date_window_count=2)
    with pytest.raises(ValueError, match="strictly ordered"):
        PolarPouchFurnitureRequest(hour_tick_outer_radius_fraction=0.96)

    import wenu

    for name in (
        "PolarPouchDateWindow",
        "PolarPouchFaceFurniture",
        "PolarPouchFurnitureRequest",
        "PolarPouchGlueStrip",
        "PolarPouchHourMark",
        "PolarPouchLabel",
        "PolarPouchPairFurniture",
    ):
        assert name in wenu.__all__
