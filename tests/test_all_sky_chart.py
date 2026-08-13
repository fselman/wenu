"""Galactic Mollweide all-sky chart contracts."""

from types import SimpleNamespace

import numpy as np
import pytest

from wenu import AllSkyChart
from wenu.charts.legend_plan import chart_type_name, default_chart_legend_plan
from wenu.geometry.spherical import SphericalPoints


def test_all_sky_chart_owns_the_complete_mollweide_ellipse():
    chart = AllSkyChart()

    assert chart.projection.central_longitude_deg == pytest.approx(0.0)
    assert chart.projection.flip_ew is True
    assert chart.boundary.closed
    assert chart.viewport.aspect_ratio == pytest.approx(2.0)
    assert chart.figure_size(8.0) == pytest.approx((8.0, 4.0))
    assert chart.chart_context.angular_width_deg == pytest.approx(360.0)
    assert chart.chart_context.angular_height_deg == pytest.approx(180.0)
    assert chart.selects_full_sphere is True


def test_all_sky_render_transforms_geometry_before_projection(monkeypatch):
    calls = {}
    source = SphericalPoints(lon_deg=[1.0], lat_deg=[2.0])
    galactic = SphericalPoints(lon_deg=[3.0], lat_deg=[4.0])

    def transform(geometry, observer):
        calls.setdefault("transforms", []).append((geometry, observer))
        return galactic

    monkeypatch.setattr(
        "wenu.charts.all_sky.horizontal_to_galactic", transform
    )

    class Renderer:
        def set_clip_boundary(self, boundary, *, style):
            calls["boundary"] = boundary

    class Sky:
        observer = None
        constellation_labels = None

        def draw_chart(self, **kwargs):
            calls["draw"] = kwargs
            return kwargs["project_geometry"](source)

    observer = object()
    result = AllSkyChart().render(Sky(), Renderer(), observer=observer)

    assert result.x == pytest.approx(
        AllSkyChart().projection.project_geometry(galactic).x
    )
    assert calls["transforms"] == [(source, observer)]
    assert calls["draw"]["observer"] is observer
    assert calls["boundary"].name == "all_sky_boundary"


def test_all_sky_mask_uses_galactic_transform_without_horizon_rejection(
    monkeypatch,
):
    calls = {}
    monkeypatch.setattr(
        "wenu.charts._masking.draw_composed_outside_mask",
        lambda **kwargs: calls.update(kwargs),
    )

    class Renderer:
        def set_clip_boundary(self, boundary, *, style):
            pass

    class Sky:
        observer = None
        constellation_labels = None

        def draw_chart(self, **kwargs):
            return "result"

    chart = AllSkyChart(outside_mask_constellations=("Cru", "Cen"))
    assert chart.render(Sky(), Renderer(), observer=object()) == "result"
    assert calls["constellations"] == ("Cru", "Cen")
    assert calls["transform_spherical"] is not None
    assert calls["complete_sphere"] is True
    assert "visible_minimum_latitude_deg" not in calls


def test_all_sky_horizon_mask_uses_ellipse_and_galactic_seam_path(
    monkeypatch,
):
    calls = {}
    monkeypatch.setattr(
        "wenu.charts._masking.draw_composed_outside_mask",
        lambda **kwargs: calls.update(kwargs),
    )

    class Renderer:
        def set_clip_boundary(self, boundary, *, style):
            pass

    class Sky:
        observer = None
        constellation_labels = None

        def draw_chart(self, **kwargs):
            return "result"

    chart = AllSkyChart()
    assert chart.render(
        Sky(), Renderer(), observer=object(), horizon_mask=True
    ) == "result"
    assert calls["horizon_mask"] is True
    assert calls["boundary"].name == "all_sky_boundary"
    np.testing.assert_allclose(calls["boundary"].x, chart.boundary.x)
    np.testing.assert_allclose(calls["boundary"].y, chart.boundary.y)
    assert calls["transform_spherical"] is not None
    assert calls["complete_sphere"] is True


def test_all_sky_chart_is_public():
    import wenu

    assert "AllSkyChart" in wenu.__all__
    assert wenu.AllSkyChart is AllSkyChart


def test_all_sky_chart_has_a_stable_composition_identity():
    assert AllSkyChart.chart_type == "all_sky"
    assert chart_type_name(AllSkyChart()) == "all_sky"
    plan = default_chart_legend_plan("all_sky")
    assert plan.objects.outside is True
    assert plan.stars.outside is True
