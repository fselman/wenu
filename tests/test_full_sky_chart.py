"""Milestone 23 full-sky production API tests."""

from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from wenu import FullSkyChart
from wenu.coordinates import GENERIC_SPHERICAL_SPEC

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.rendering import MatplotlibRenderer
from wenu.rendering.preparation import clip_to_latitude
from wenu.geometry.spherical import SphericalCurves, SphericalPolygons


def test_default_chart_reproduces_zenith_centered_horizon():
    chart = FullSkyChart()
    x, y = chart.projection.project_spherical(0.0, 90.0)
    assert np.hypot(x, y) < 2.0e-8
    assert chart.viewport.xlim == pytest.approx((-2.0, 2.0), abs=2e-4)
    assert chart.viewport.ylim == pytest.approx((-2.0, 2.0), abs=2e-4)
    assert chart.figure_size(7.0) == pytest.approx((7.0, 7.0))


def test_tangent_point_and_horizon_are_independent():
    chart = FullSkyChart(
        center_alt_deg=45.0,
        center_az_deg=210.0,
    )
    x, y = chart.projection.project_spherical(210.0, 45.0)
    assert np.hypot(x, y) < 2.0e-8
    center = (
        (chart.viewport.x_min + chart.viewport.x_max) / 2.0,
        (chart.viewport.y_min + chart.viewport.y_max) / 2.0,
    )
    assert np.hypot(*center) > 0.1
    assert np.all(chart.horizon.finite)


@pytest.mark.parametrize("center_alt,angle,flip", [(90, 0, True), (45, 37, False)])
@pytest.mark.parametrize("dpi", [100, 300])
def test_horizon_grid_labels_use_cardinal_spokes_and_an_exterior_margin(center_alt, angle, flip, dpi):
    from wenu.charts.boundaries import HorizonGridLabelAnchor
    from wenu.geometry.projected import ProjectedGrid

    chart = FullSkyChart(center_alt_deg=center_alt, position_angle_deg=angle, flip_ew=flip)
    anchor = HorizonGridLabelAnchor(chart.projection, chart.horizon)
    fig, ax = plt.subplots(figsize=(4, 4), dpi=dpi)
    ax.set_xlim(chart.viewport.xlim)
    ax.set_ylim(chart.viewport.ylim)
    ax.set_aspect("equal")
    fig.canvas.draw()
    renderer = MatplotlibRenderer(ax)
    renderer.set_clip_boundary(chart.horizon)
    curves = ProjectedCurves(items=[ProjectedCurve([0, 1], [0, 1], name=name)
        for name in ["altitude_30", "altitude_60", "azimuth_0", "azimuth_90", "azimuth_180", "azimuth_270"]])
    renderer.draw(ProjectedGrid(components={"parallels": curves}), draw_labels=True,
                  label_anchor=anchor, label_style={"fontsize": 6},
                  component_label_styles={"parallels": {"color": "red"}})
    boundary = renderer._clip_patch.get_path().transformed(renderer._clip_patch.get_transform())
    for altitude in (30, 60):
        texts = [text for text in ax.texts if text.get_text() == f"altitude_{altitude}"]
        assert len(texts) == 4
        positions = [chart.projection.project_spherical(az, altitude) for az in (0, 90, 180, 270)]
        np.testing.assert_allclose([text.get_position() for text in texts], positions)
    for text in ax.texts:
        assert text.get_rotation() == 0
        assert text.get_color() == "red"
        if text.get_text().startswith("azimuth_"):
            box = text.get_window_extent(fig.canvas.get_renderer())
            assert not boundary.intersects_bbox(box, filled=True)
            assert not text.get_clip_on()
    assert len(anchor(ProjectedCurve([0, 0], [0, 0], name="altitude_90"))) == 1
    custom = HorizonGridLabelAnchor(chart.projection, chart.horizon, altitude_label_azimuths_deg=(45, 225))
    assert len(custom(ProjectedCurve([0, 0], [0, 0], name="altitude_30"))) == 2
    plt.close(fig)


def test_tangent_point_must_not_expose_projection_antipode():
    with pytest.raises(ValueError, match="stereographic antipode"):
        FullSkyChart(center_alt_deg=0.0)
    with pytest.raises(ValueError, match="stereographic antipode"):
        FullSkyChart(center_alt_deg=-10.0)


def test_latitude_clipping_interpolates_horizon_crossings():
    spherical = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([0.0, 0.0, 0.0],),
        lat_deg=([-10.0, 10.0, -10.0],),
    )
    projected = SimpleNamespace(
        __iter__=None,
    )
    from wenu.geometry.projected import ProjectedCurves
    projected = ProjectedCurves(
        items=[
            ProjectedCurve(
                x=[-1.0, 0.0, 1.0],
                y=[0.0, 1.0, 0.0],
            )
        ]
    )
    clipped = clip_to_latitude(
        spherical,
        projected,
        minimum=0.0,
    )
    assert len(clipped) == 1
    assert clipped[0].x == pytest.approx([-0.5, 0.0, 0.5])
    assert clipped[0].y == pytest.approx([0.5, 1.0, 0.5])


def test_complete_sphere_latitude_floor_preserves_split_curves():
    spherical = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([170.0, -170.0],),
        lat_deg=([0.0, 0.0],),
    )
    from wenu.geometry.projected import ProjectedCurves

    projected = ProjectedCurves(items=[
        ProjectedCurve(x=[-2.0, -1.0], y=[0.0, 0.0]),
        ProjectedCurve(x=[1.0, 2.0], y=[0.0, 0.0]),
    ])

    assert clip_to_latitude(
        spherical, projected, minimum=-90.0
    ) is projected


def test_complete_sphere_polygon_layer_remains_boundary_only():
    spherical = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=([0.0, 1.0, 1.0, 0.0],),
        lat_deg=([0.0, 0.0, 1.0, 1.0],),
    )
    projected = ProjectedPolygons(items=[ProjectedPolygon(
        x=[0.0, 1.0, 1.0, 0.0],
        y=[0.0, 0.0, 1.0, 1.0],
    )])

    prepared = clip_to_latitude(
        spherical, projected, minimum=-90.0
    )

    assert isinstance(prepared, ProjectedCurves)
    assert len(prepared) == 1
    assert prepared[0].closed is False


def test_renderer_applies_projected_boundary_to_all_artists():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    boundary = ProjectedCurve(
        x=[-1.0, 0.0, 1.0, 0.0],
        y=[0.0, 1.0, 0.0, -1.0],
        closed=True,
    )
    patch = renderer.set_clip_boundary(
        boundary,
        style={"facecolor": "none", "edgecolor": "white"},
    )
    artists = renderer.draw(
        ProjectedCurve(x=[-2.0, 2.0], y=[0.0, 0.0])
    )
    assert artists[0].get_clip_path() is not None
    assert patch in ax.patches
    plt.close(figure)


def test_render_delegates_with_chart_horizon():
    calls = {}

    class Renderer:
        def set_clip_boundary(self, boundary, *, style):
            calls["boundary"] = boundary
            calls["boundary_style"] = style

    class Style:
        def layer_options(self, sky, *, horizon_altitude_deg):
            calls["minimum"] = horizon_altitude_deg
            return {"base": {"render": {"style": {"color": "white"}}}}

    class Sky:
        def draw_chart(self, **kwargs):
            calls["draw"] = kwargs
            return "result"

    chart = FullSkyChart(
        center_alt_deg=60.0,
        horizon_altitude_deg=5.0,
        altitude_label_azimuths_deg=(45.0, 225.0),
    )
    result = chart.render(
        Sky(),
        Renderer(),
        style=Style(),
        layer_options={
            "override": {"render": {}},
            "altaz_grid": {"render": {"label_anchor": None}},
        },
    )
    assert result == "result"
    assert calls["minimum"] == 5.0
    assert calls["boundary"].closed
    assert "base" in calls["draw"]["layer_options"]
    assert "override" in calls["draw"]["layer_options"]
    anchor = calls["draw"]["layer_options"]["altaz_grid"]["render"]["label_anchor"]
    assert anchor.altitude_label_azimuths_deg == (45.0, 225.0)
    assert anchor.horizon_altitude_deg == 5.0


def test_full_sky_chart_can_draw_an_outside_constellation_mask(monkeypatch):
    calls = {}

    def draw_mask(**kwargs):
        calls.update(kwargs)

    monkeypatch.setattr(
        "wenu.charts._masking.draw_composed_outside_mask",
        draw_mask,
    )

    class Renderer:
        def set_clip_boundary(self, boundary, *, style):
            pass

    class Sky:
        constellation_labels = None

        def draw_chart(self, **kwargs):
            return "result"

    chart = FullSkyChart(outside_mask_constellations=("Cru", "Cen"))
    result = chart.render(Sky(), Renderer())

    assert result == "result"
    assert calls["constellations"] == ("Cru", "Cen")
    assert calls["viewport"] == chart.viewport
    assert calls["visible_minimum_latitude_deg"] == pytest.approx(0.0)
    assert calls["planisphere"] is True


def test_full_sky_chart_ignores_horizon_mask(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "wenu.charts._masking.draw_composed_outside_mask",
        lambda **kwargs: calls.append(kwargs),
    )

    class Renderer:
        def set_clip_boundary(self, boundary, *, style):
            pass

    class Sky:
        constellation_labels = None

        def draw_chart(self, **kwargs):
            return "result"

    assert FullSkyChart().render(
        Sky(), Renderer(), horizon_mask=True
    ) == "result"
    assert calls == []


def test_full_sky_chart_is_a_top_level_export():
    import wenu

    assert "FullSkyChart" in wenu.__all__
    assert wenu.FullSkyChart is FullSkyChart
