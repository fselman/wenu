"""Milestone 16 production regional-chart API tests."""

from types import SimpleNamespace

import numpy as np
import pytest

from wenu.charts.regional import ExportOptions, RegionalChart
from wenu.charts.styles import PublicationStyle


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
