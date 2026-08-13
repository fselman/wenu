"""Contracts for composing independent chart-mask restrictions once."""

from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from wenu.charts._masking import draw_composed_outside_mask
from wenu.charts._masking import compose_projected_mask_openings
from wenu.geometry.projected import ProjectedPolygon, ProjectedPolygons
from wenu.geometry.viewport import Viewport
from wenu.rendering import MatplotlibRenderer


def _opening(name):
    return ProjectedPolygons(items=[ProjectedPolygon(
        x=[-0.5, 0.5, 0.5, -0.5],
        y=[-0.5, -0.5, 0.5, 0.5],
        name=name,
    )])


def test_constellation_and_horizon_restrictions_draw_once(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "wenu.charts._masking.prepare_constellation_mask_opening",
        lambda **kwargs: _opening("constellations"),
    )
    monkeypatch.setattr(
        "wenu.charts._masking.prepare_horizon_mask_opening",
        lambda **kwargs: SimpleNamespace(projected=_opening("horizon")),
    )

    class Renderer:
        def draw_outside_mask(self, polygons, *, viewport, style):
            calls.append((polygons, viewport, style))
            return "mask"

    viewport = Viewport(-1.0, 1.0, -1.0, 1.0)
    result = draw_composed_outside_mask(
        sky=SimpleNamespace(observer=object()),
        projection=object(),
        renderer=Renderer(),
        viewport=viewport,
        observer=None,
        style={"alpha": 0.2},
        constellations=("Cru",),
        horizon_mask=True,
    )

    assert result == "mask"
    assert len(calls) == 1
    polygons, drawn_viewport, style = calls[0]
    assert polygons.metadata["mask_opening_group_sizes"] == (1, 1)
    assert tuple(polygon.name for polygon in polygons) == (
        "constellations", "horizon"
    )
    assert drawn_viewport == viewport
    assert style == {"alpha": 0.2}


def test_planisphere_horizon_mask_is_a_no_op():
    class Renderer:
        def draw_outside_mask(self, *args, **kwargs):
            raise AssertionError("planisphere horizon mask must not draw")

    result = draw_composed_outside_mask(
        sky=SimpleNamespace(observer=object()),
        projection=object(),
        renderer=Renderer(),
        viewport=Viewport(-1.0, 1.0, -1.0, 1.0),
        observer=None,
        style={},
        horizon_mask=True,
        planisphere=True,
    )

    assert result is None


def test_planisphere_constellation_mask_is_identical_with_horizon_switch(
    monkeypatch,
):
    opening = _opening("constellations")
    drawn = []
    monkeypatch.setattr(
        "wenu.charts._masking.prepare_constellation_mask_opening",
        lambda **kwargs: opening,
    )

    def reject_horizon(**kwargs):
        raise AssertionError("planisphere must not prepare a horizon mask")

    monkeypatch.setattr(
        "wenu.charts._masking.prepare_horizon_mask_opening",
        reject_horizon,
    )

    class Renderer:
        def draw_outside_mask(self, polygons, *, viewport, style):
            drawn.append(polygons)
            return "mask"

    common = {
        "sky": SimpleNamespace(observer=object()),
        "projection": object(),
        "renderer": Renderer(),
        "viewport": Viewport(-1.0, 1.0, -1.0, 1.0),
        "observer": None,
        "style": {"alpha": 0.3},
        "constellations": ("Cru",),
        "planisphere": True,
    }

    assert draw_composed_outside_mask(
        **common, horizon_mask=False
    ) == "mask"
    assert draw_composed_outside_mask(
        **common, horizon_mask=True
    ) == "mask"
    assert len(drawn) == 2
    assert drawn[0].metadata == drawn[1].metadata
    assert tuple(polygon.name for polygon in drawn[0]) == (
        "constellations",
    )
    assert tuple(polygon.name for polygon in drawn[1]) == (
        "constellations",
    )


def _winding_number(path, point):
    """Return the signed winding of a compound Matplotlib path."""
    from matplotlib.path import Path

    winding = 0
    starts = np.flatnonzero(path.codes == Path.MOVETO)
    stops = np.concatenate((starts[1:], [len(path.vertices)]))
    x, y = point
    for start, stop in zip(starts, stops):
        vertices = path.vertices[start:stop]
        for first, second in zip(vertices[:-1], vertices[1:]):
            cross = (
                (second[0] - first[0]) * (y - first[1])
                - (x - first[0]) * (second[1] - first[1])
            )
            if first[1] <= y < second[1] and cross > 0.0:
                winding += 1
            elif second[1] <= y < first[1] and cross < 0.0:
                winding -= 1
    return winding


def test_compound_winding_leaves_only_group_intersection_transparent():
    first = ProjectedPolygons(items=[ProjectedPolygon(
        x=[-0.8, 0.2, 0.2, -0.8],
        y=[-0.8, -0.8, 0.8, 0.8],
    )])
    second = ProjectedPolygons(items=[ProjectedPolygon(
        x=[-0.2, 0.8, 0.8, -0.2],
        y=[-0.8, -0.8, 0.8, 0.8],
    )])
    figure, ax = plt.subplots()
    patch = MatplotlibRenderer(ax).draw_outside_mask(
        compose_projected_mask_openings(first, second),
        viewport=Viewport(-1.0, 1.0, -1.0, 1.0),
        style={"facecolor": "black", "alpha": 0.3},
    )

    assert _winding_number(patch.get_path(), (0.0, 0.0)) == 0
    assert _winding_number(patch.get_path(), (-0.5, 0.0)) != 0
    assert _winding_number(patch.get_path(), (0.9, 0.0)) != 0
    assert len(ax.patches) == 1
    assert patch.get_alpha() == 0.3
    plt.close(figure)


def test_seam_pieces_remain_in_their_independent_opening_groups(monkeypatch):
    calls = []
    constellations = ProjectedPolygons(items=[
        _opening("constellation_left")[0],
        _opening("constellation_right")[0],
    ])
    horizon = ProjectedPolygons(items=[
        _opening("horizon_left")[0],
        _opening("horizon_center")[0],
        _opening("horizon_right")[0],
    ])
    monkeypatch.setattr(
        "wenu.charts._masking.prepare_constellation_mask_opening",
        lambda **kwargs: constellations,
    )
    monkeypatch.setattr(
        "wenu.charts._masking.prepare_horizon_mask_opening",
        lambda **kwargs: SimpleNamespace(projected=horizon),
    )

    class Renderer:
        def draw_outside_mask(self, polygons, *, viewport, style):
            calls.append(polygons)
            return "mask"

    result = draw_composed_outside_mask(
        sky=SimpleNamespace(observer=object()),
        projection=object(),
        renderer=Renderer(),
        viewport=Viewport(-1.0, 1.0, -1.0, 1.0),
        observer=None,
        style={"alpha": 0.3},
        constellations=("Cru",),
        horizon_mask=True,
        complete_sphere=True,
    )

    assert result == "mask"
    assert len(calls) == 1
    assert calls[0].metadata["mask_opening_group_sizes"] == (2, 3)
    assert len(calls[0]) == 5
