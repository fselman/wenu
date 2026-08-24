"""Milestone 16 production regional-chart API tests."""

from types import SimpleNamespace

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time
import numpy as np
import pytest

from wenu.charts.regional import (
    ExportOptions,
    RegionalChart,
    celestial_north_position_angle,
    local_orientation_at,
    resolve_chart_orientation,
    target_up_position_angle,
)
from wenu.charts.styles import PublicationStyle


@pytest.fixture(autouse=True)
def stable_celestial_north(monkeypatch):
    monkeypatch.setattr(
        "wenu.charts.regional.celestial_north_position_angle",
        lambda *args, **kwargs: 0.0,
    )


def test_angular_radius_and_aspect_define_viewport():
    chart = RegionalChart.from_angular_radius(
        center_alt_deg=45.0,
        center_az_deg=120.0,
        angular_radius_deg=20.0,
        aspect_ratio=1.5,
        crop_x=0.1,
        crop_y=-0.2,
    )
    assert chart.field_width_deg == 60.0
    assert chart.field_height_deg == 40.0
    assert chart.viewport.aspect_ratio > 1.0
    assert chart.viewport.center == pytest.approx((0.1, -0.2))
    width, height = chart.figure_size(7.0)
    assert width / height == pytest.approx(
        chart.viewport.aspect_ratio
    )


def test_projection_tangent_point_maps_to_origin():
    chart = RegionalChart(
        center_alt_deg=35.0,
        center_az_deg=210.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
    )
    x, y = chart.projection.project_spherical(210.0, 35.0)
    assert np.hypot(x, y) < 2.0e-8


def test_target_up_position_angle_accepts_non_celestial_poles():
    assert target_up_position_angle(
        center_alt_deg=30.0,
        center_az_deg=45.0,
        target_alt_deg=60.0,
        target_az_deg=45.0,
    ) == pytest.approx(0.0, abs=1.0e-10)


def test_celestial_north_uses_the_public_altaz_observer_contract():
    observer = SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-08-16T01:00:00"),
            location=EarthLocation.from_geodetic(
                lon=-71.23 * u.deg,
                lat=-32.44 * u.deg,
            ),
        )
    )

    angle = celestial_north_position_angle(
        observer,
        center_alt_deg=20.0,
        center_az_deg=270.0,
    )

    assert np.isfinite(angle)


def test_pointwise_orientation_retains_parallactic_geometry(monkeypatch):
    monkeypatch.setattr(
        "wenu.charts.regional.celestial_north_position_angle",
        lambda *args, **kwargs: 32.5,
    )

    local = local_orientation_at(
        object(), altitude_deg=20.0, azimuth_deg=270.0
    )

    assert local.celestial_meridian_position_angle_deg == pytest.approx(32.5)
    assert local.zenith_position_angle_deg == pytest.approx(0.0)
    assert local.parallactic_angle_deg == pytest.approx(-32.5)


def test_named_and_literal_orientations_are_explicit(monkeypatch):
    monkeypatch.setattr(
        "wenu.charts.regional.local_orientation_at",
        lambda *args, **kwargs: SimpleNamespace(
            celestial_meridian_position_angle_deg=18.0
        ),
    )

    north = resolve_chart_orientation(
        object(), center_alt_deg=20.0, center_az_deg=270.0,
        orientation="celestial-north-up",
    )
    zenith = resolve_chart_orientation(
        object(), center_alt_deg=20.0, center_az_deg=270.0,
        orientation="zenith-up",
    )
    literal = resolve_chart_orientation(
        object(), center_alt_deg=20.0, center_az_deg=270.0,
        position_angle_deg=0.0,
    )

    assert north.position_angle_deg == pytest.approx(18.0)
    assert zenith.position_angle_deg == pytest.approx(0.0)
    assert literal.position_angle_deg == pytest.approx(0.0)
    assert literal.source == "position-angle"
    with pytest.raises(ValueError, match="exactly one"):
        resolve_chart_orientation(
            object(), center_alt_deg=20.0, center_az_deg=270.0,
            orientation="zenith-up", position_angle_deg=0.0,
        )


def test_invalid_field_is_rejected():
    with pytest.raises(ValueError, match="field_width_deg"):
        RegionalChart(
            center_alt_deg=0.0,
            center_az_deg=0.0,
            field_width_deg=0.0,
            field_height_deg=20.0,
        )


class Figure:
    def __init__(self):
        self.saved = None

    def savefig(self, path, **kwargs):
        self.saved = (path, kwargs)


def test_export_options_are_reproducible(tmp_path):
    figure = Figure()
    options = ExportOptions(
        dpi=240,
        transparent=True,
        metadata={"Creator": "Wenu"},
    )
    path = options.save(figure, tmp_path / "chart.png")
    assert path.name == "chart.png"
    assert figure.saved[1]["dpi"] == 240
    assert figure.saved[1]["transparent"] is True
    assert figure.saved[1]["metadata"] == {"Creator": "Wenu"}


def test_style_configures_axes():
    calls = []
    axes = SimpleNamespace(
        figure=SimpleNamespace(facecolor=None),
        set_facecolor=lambda value: calls.append(("face", value)),
        set_title=lambda value: calls.append(("title", value)),
        set_xticks=lambda value: calls.append(("x", value)),
        set_yticks=lambda value: calls.append(("y", value)),
    )
    axes.figure.set_facecolor = lambda value: calls.append(
        ("figure", value)
    )
    style = PublicationStyle(sky_color="navy")
    assert style.configure_axes(axes, title="Crux") is axes
    assert ("face", "navy") in calls
    assert ("title", "Crux") in calls


def test_constellation_center_requires_configured_layers():
    with pytest.raises(RuntimeError, match="Add stars"):
        RegionalChart.from_constellations(
            SimpleNamespace(
                stars=None,
                constellation_lines=None,
            ),
            ["Cru"],
            angular_radius_deg=20.0,
        )


def test_constellation_field_can_be_derived_from_loaded_geometry():
    stars = SimpleNamespace(
        spherical_geometry=lambda observer, alt_min: SimpleNamespace(
            ids=np.asarray([1, 2, 3]),
            lon_deg=np.asarray([350.0, 0.0, 10.0]),
            lat_deg=np.asarray([-5.0, 0.0, 5.0]),
        )
    )
    sky = SimpleNamespace(
        observer=object(),
        stars=stars,
        constellation_lines=SimpleNamespace(
            edges_by_constellation={"Test": [(1, 2), (2, 3)]}
        ),
    )

    chart = RegionalChart.from_constellations(
        sky,
        ["Test"],
        framing_padding=1.2,
    )

    assert chart.center_az_deg == pytest.approx(0.0, abs=1.0e-8)
    assert chart.center_alt_deg == pytest.approx(0.0, abs=1.0e-8)
    assert chart.field_width_deg == pytest.approx(chart.field_height_deg)
    assert chart.field_height_deg > 24.0


def test_constellation_region_framing_uses_complete_official_boundary():
    stars = SimpleNamespace(
        spherical_geometry=lambda observer, alt_min: SimpleNamespace(
            ids=np.asarray([1, 2]),
            lon_deg=np.asarray([0.0, 2.0]),
            lat_deg=np.asarray([0.0, 0.0]),
        )
    )
    regions = SimpleNamespace(
        spherical_geometry=lambda observer, selected: SimpleNamespace(
            lon_deg=(np.asarray([350.0, 10.0, 10.0, 350.0]),),
            lat_deg=(np.asarray([-8.0, -8.0, 8.0, 8.0]),),
        )
    )
    sky = SimpleNamespace(
        observer=object(),
        stars=stars,
        constellation_lines=SimpleNamespace(
            edges_by_constellation={"Test": [(1, 2)]}
        ),
        constellation_boundaries=regions,
    )

    chart = RegionalChart.from_constellations(
        sky,
        ["Test"],
        framing_constellations=["TestRegion"],
        framing_padding=1.15,
    )

    assert chart.center_az_deg == pytest.approx(0.0, abs=1.0e-8)
    assert chart.center_alt_deg == pytest.approx(0.0, abs=1.0e-8)
    assert chart.field_height_deg > 26.0


def test_explicit_constellation_field_preserves_compatible_behavior():
    stars = SimpleNamespace(
        spherical_geometry=lambda observer, alt_min: SimpleNamespace(
            ids=np.asarray([1, 2]),
            lon_deg=np.asarray([10.0, 20.0]),
            lat_deg=np.asarray([30.0, 35.0]),
        )
    )
    sky = SimpleNamespace(
        observer=object(),
        stars=stars,
        constellation_lines=SimpleNamespace(
            edges_by_constellation={"Test": [(1, 2)]}
        ),
    )

    chart = RegionalChart.from_constellations(
        sky,
        ["Test"],
        angular_radius_deg=10.0,
        aspect_ratio=1.5,
    )

    assert chart.field_width_deg == pytest.approx(30.0)
    assert chart.field_height_deg == pytest.approx(20.0)


@pytest.mark.parametrize(
    ("name", "value"),
    [("framing_padding", 1.0), ("minimum_angular_radius_deg", 0.0)],
)
def test_invalid_automatic_constellation_framing_is_rejected(name, value):
    stars = SimpleNamespace(
        spherical_geometry=lambda observer, alt_min: SimpleNamespace(
            ids=np.asarray([1, 2]),
            lon_deg=np.asarray([0.0, 1.0]),
            lat_deg=np.asarray([0.0, 1.0]),
        )
    )
    sky = SimpleNamespace(
        observer=object(),
        stars=stars,
        constellation_lines=SimpleNamespace(
            edges_by_constellation={"Test": [(1, 2)]}
        ),
    )

    with pytest.raises(ValueError, match=name):
        RegionalChart.from_constellations(sky, ["Test"], **{name: value})


def test_regional_grid_defaults_to_viewport_clipping():
    grid = SimpleNamespace(coordinate_system="equatorial")
    assert "prepare" not in PublicationStyle()._grid_options(grid)

    horizon_limited = PublicationStyle(
        grid_minimum_altitude_deg=0.0
    )
    assert callable(
        horizon_limited._grid_options(grid)["prepare"]
    )


def test_regional_horizon_mask_uses_rectangular_chart_viewport(monkeypatch):
    calls = {}
    monkeypatch.setattr(
        "wenu.charts._masking.draw_composed_outside_mask",
        lambda **kwargs: calls.update(kwargs),
    )

    class Sky:
        observer = object()

        def draw_chart(self, **kwargs):
            return "result"

    chart = RegionalChart(
        center_alt_deg=0.0,
        center_az_deg=180.0,
        field_width_deg=10.0,
        field_height_deg=8.0,
    )

    assert chart.render(
        Sky(), object(), horizon_mask=True
    ) == "result"
    assert calls["horizon_mask"] is True
    assert calls["viewport"] == chart.viewport
    assert calls["boundary"] is None
