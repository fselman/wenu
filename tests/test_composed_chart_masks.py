"""Contracts for composing independent chart-mask restrictions once."""

from types import SimpleNamespace

from wenu.charts._masking import draw_composed_outside_mask
from wenu.geometry.projected import ProjectedPolygon, ProjectedPolygons
from wenu.geometry.viewport import Viewport


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
