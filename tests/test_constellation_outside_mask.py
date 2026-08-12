"""Constellation outside-mask chart and renderer tests."""

from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from wenu.charts._masking import (
    _expanded_names,
    draw_constellation_outside_mask,
)
from wenu.charts.regional import RegionalChart
from wenu.charts.styles import PublicationStyle
from wenu.geometry.projected import (
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.geometry.spherical import SphericalPolygons
from wenu.geometry.viewport import Viewport
from wenu.rendering import MatplotlibRenderer


def test_style_exposes_outside_mask_presentation():
    style = PublicationStyle(
        outside_mask_color="white",
        outside_mask_alpha=0.2,
        outside_mask_zorder=12,
    )
    assert style.outside_mask_style() == {
        "facecolor": "white",
        "edgecolor": "none",
        "alpha": 0.2,
        "zorder": 12.0,
    }


def test_renderer_builds_compound_path_with_hole():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    polygon = ProjectedPolygon(
        x=[-0.5, 0.5, 0.5, -0.5],
        y=[-0.5, -0.5, 0.5, 0.5],
        name="CRU",
    )
    patch = renderer.draw_outside_mask(
        ProjectedPolygons(items=[polygon]),
        viewport=Viewport(-1.0, 1.0, -1.0, 1.0),
        style={"facecolor": "black", "alpha": 0.3},
    )
    from matplotlib.path import Path

    assert np.count_nonzero(patch.get_path().codes == Path.MOVETO) == 2
    assert patch.get_alpha() == pytest.approx(0.3)
    assert patch in ax.patches
    plt.close(figure)


def test_mask_artist_respects_existing_full_sky_clip_boundary():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    from wenu.geometry.projected import ProjectedCurve

    renderer.set_clip_boundary(
        ProjectedCurve(
            x=[-1.0, 0.0, 1.0, 0.0],
            y=[0.0, 1.0, 0.0, -1.0],
            closed=True,
        )
    )
    patch = renderer.draw_outside_mask(
        ProjectedPolygons(
            items=[
                ProjectedPolygon(
                    x=[-0.2, 0.2, 0.2, -0.2],
                    y=[-0.2, -0.2, 0.2, 0.2],
                )
            ]
        ),
        viewport=Viewport(-1.0, 1.0, -1.0, 1.0),
    )
    assert patch.get_clip_path() is not None
    plt.close(figure)


def test_renderer_can_shade_chart_with_no_visible_openings():
    figure, ax = plt.subplots()
    renderer = MatplotlibRenderer(ax)
    patch = renderer.draw_outside_mask(
        ProjectedPolygons(items=[]),
        viewport=Viewport(-1.0, 1.0, -1.0, 1.0),
    )
    from matplotlib.path import Path

    assert np.count_nonzero(patch.get_path().codes == Path.MOVETO) == 1
    assert patch in ax.patches
    plt.close(figure)


def test_full_sky_mask_discards_hidden_regions_before_projection():
    calls = {}
    spherical = SphericalPolygons(
        lon_deg=(
            [0.0, 1.0, 0.0],
            [2.0, 3.0, 2.0],
            [4.0, 5.0, 4.0],
        ),
        lat_deg=(
            [10.0, 20.0, 15.0],
            [-10.0, 5.0, -5.0],
            [-20.0, -10.0, -15.0],
        ),
        names=("CRU", "CEN", "UMA"),
    )

    class Boundaries:
        def spherical_geometry(self, observer, *, selected):
            calls["selected"] = selected
            return spherical

    class Projection:
        def project_geometry(self, value):
            calls["projected_names"] = tuple(value.names)
            calls["projected_latitudes"] = tuple(
                tuple(latitude) for latitude in value.lat_deg
            )
            return ProjectedPolygons(items=[
                ProjectedPolygon(
                    x=[0.0, 1.0, 0.0],
                    y=[0.0, 0.0, 1.0],
                    name=name,
                )
                for name in value.names
            ])

    class Renderer:
        def draw_outside_mask(self, polygons, *, viewport, style):
            calls["drawn_names"] = tuple(
                polygon.name for polygon in polygons
            )
            return "mask"

    result = draw_constellation_outside_mask(
        sky=SimpleNamespace(
            observer=object(), constellation_boundaries=Boundaries()
        ),
        projection=Projection(),
        renderer=Renderer(),
        viewport=Viewport(-1.0, 1.0, -1.0, 1.0),
        constellations=("Cru", "Cen", "UMa"),
        style={},
        visible_minimum_latitude_deg=0.0,
    )

    assert result == "mask"
    assert calls["selected"] == {"CRU", "CEN", "UMA"}
    assert calls["projected_names"] == ("CRU", "CEN")
    assert min(calls["projected_latitudes"][1]) < 0.0
    assert calls["drawn_names"] == ("CRU", "CEN")


def test_all_hidden_regions_produce_a_mask_without_openings():
    class Boundaries:
        def spherical_geometry(self, observer, *, selected):
            return SphericalPolygons(
                lon_deg=([0.0, 1.0, 0.0],),
                lat_deg=([-20.0, -10.0, -15.0],),
                names=("UMA",),
            )

    class Projection:
        def project_geometry(self, value):
            assert len(value) == 0
            return ProjectedPolygons(items=[])

    class Renderer:
        def draw_outside_mask(self, polygons, *, viewport, style):
            assert len(polygons) == 0
            return "fully shaded"

    assert draw_constellation_outside_mask(
        sky=SimpleNamespace(
            observer=object(), constellation_boundaries=Boundaries()
        ),
        projection=Projection(),
        renderer=Renderer(),
        viewport=Viewport(-1.0, 1.0, -1.0, 1.0),
        constellations=("UMa",),
        style={},
        visible_minimum_latitude_deg=0.0,
    ) == "fully shaded"


def test_serpens_selection_expands_to_both_regions():
    assert _expanded_names(("Ser",)) == {"SER1", "SER2"}
    assert _expanded_names(("SerCap", "SerCau")) == {"SER1", "SER2"}


def test_regional_chart_normalizes_mask_selection():
    chart = RegionalChart(
        center_alt_deg=40.0,
        center_az_deg=180.0,
        field_width_deg=30.0,
        field_height_deg=20.0,
        outside_mask_constellations=["Cru"],
    )
    assert chart.outside_mask_constellations == ("Cru",)
