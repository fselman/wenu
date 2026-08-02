"""Milestone 43H chart-visible constellation-label contracts."""

from types import SimpleNamespace

import numpy as np
import wenu.geometry.clipping as clipping_module

from wenu.charts.boundaries import circular_boundary
from wenu.charts.constellation_label_placement import (
    apply_visible_constellation_label_anchors,
)
from wenu.geometry.clipping import (
    clip_polygon_to_convex_boundary,
    polygon_centroid,
)
from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.geometry.viewport import Viewport


def test_convex_boundary_intersection_has_area_centroid():
    polygon = ProjectedPolygon(
        x=np.asarray([0.0, 2.0, 2.0, 0.0]),
        y=np.asarray([-0.5, -0.5, 0.5, 0.5]),
        name="TST",
    )
    boundary = ProjectedCurve(
        x=np.asarray([-1.0, 1.0, 1.0, -1.0]),
        y=np.asarray([-1.0, -1.0, 1.0, 1.0]),
        closed=True,
    )

    clipped = clip_polygon_to_convex_boundary(polygon, boundary)

    assert clipped is not None
    np.testing.assert_allclose(
        polygon_centroid(clipped), (0.5, 0.0)
    )


def test_convex_clipping_cleans_vertices_once(monkeypatch):
    calls = []
    original = clipping_module._remove_consecutive_duplicate_vertices

    def recording(vertices):
        calls.append(len(vertices))
        return original(vertices)

    monkeypatch.setattr(
        clipping_module,
        "_remove_consecutive_duplicate_vertices",
        recording,
    )
    polygon = ProjectedPolygon(
        x=np.asarray([-2.0, 2.0, 2.0, -2.0]),
        y=np.asarray([-2.0, -2.0, 2.0, 2.0]),
    )

    clipped = clip_polygon_to_convex_boundary(
        polygon, circular_boundary(1.0, samples=73)
    )

    assert clipped is not None
    assert len(calls) == 1


def test_partial_constellation_uses_visible_region_anchor():
    label_layer = object()
    region_layer = SimpleNamespace()
    region_geometry = object()
    region_layer.spherical_geometry = lambda observer: region_geometry
    projected_regions = ProjectedPolygons(
        items=[
            ProjectedPolygon(
                x=np.asarray([0.5, 1.5, 1.5, 0.5]),
                y=np.asarray([-0.25, -0.25, 0.25, 0.25]),
                name="TST",
            )
        ]
    )

    class Projection:
        def project_geometry(self, geometry):
            assert geometry is region_geometry
            return projected_regions

    sky = SimpleNamespace(
        constellation_labels=label_layer,
        constellation_boundaries=region_layer,
        observer=object(),
    )
    options = apply_visible_constellation_label_anchors(
        {label_layer: {"render": {"draw_labels": True}}},
        sky=sky,
        projection=Projection(),
        viewport=Viewport.centered(width=2.0, height=2.0),
        boundary=circular_boundary(1.0, samples=73),
    )
    projected_labels = ProjectedPoints(
        x=np.asarray([1.2]),
        y=np.asarray([0.0]),
        labels=np.asarray(["Tst"], dtype=object),
    )

    prepared = options[label_layer]["prepare"](
        object(), projected_labels
    )

    assert prepared.metadata["visible_region_anchors"] is True
    assert prepared.metadata["visible_region_anchor_inset"] == 0.94
    assert np.hypot(prepared.x[0], prepared.y[0]) < 0.94
    assert prepared.x[0] < projected_labels.x[0]


def test_complete_constellation_keeps_existing_anchor():
    label_layer = object()
    region_layer = SimpleNamespace()
    region_geometry = object()
    region_layer.spherical_geometry = lambda observer: region_geometry
    projected_regions = ProjectedPolygons(
        items=[
            ProjectedPolygon(
                x=np.asarray([-0.2, 0.2, 0.2, -0.2]),
                y=np.asarray([-0.2, -0.2, 0.2, 0.2]),
                name="TST",
            )
        ]
    )

    class Projection:
        def project_geometry(self, geometry):
            return projected_regions

    sky = SimpleNamespace(
        constellation_labels=label_layer,
        constellation_boundaries=region_layer,
        observer=object(),
    )
    options = apply_visible_constellation_label_anchors(
        {label_layer: {}},
        sky=sky,
        projection=Projection(),
        viewport=Viewport.centered(width=2.0, height=2.0),
        boundary=circular_boundary(1.0, samples=73),
    )
    labels = ProjectedPoints(
        x=np.asarray([0.1]),
        y=np.asarray([0.05]),
        labels=np.asarray(["Tst"], dtype=object),
    )

    prepared = options[label_layer]["prepare"](object(), labels)

    np.testing.assert_array_equal(prepared.x, labels.x)
    np.testing.assert_array_equal(prepared.y, labels.y)
