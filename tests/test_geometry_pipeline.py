"""Milestone 15A tests for canonical rendering preparation."""

from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from wenu.geometry.projected import ProjectedCurve, ProjectedCurves, ProjectedPoints
from wenu.rendering.preparation import (
    clip_to_latitude,
    magnitude_sizes,
    radial_label_offset,
)
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.sky_layer import SkyLayer
from wenu.geometry.spherical import SphericalCurves, SphericalPoints


class Layer(SkyLayer):
    layer_name = "test"

    def spherical_geometry(self, observer, *, minimum=-10.0):
        return SphericalPoints(
            lon_deg=[0.0, 1.0],
            lat_deg=[minimum, 20.0],
        )


class Projection:
    def project_geometry(self, geometry):
        return ProjectedPoints(
            x=geometry.lon_deg,
            y=geometry.lat_deg,
        )


class Renderer:
    def __init__(self):
        self.calls = []

    def draw(self, geometry, **options):
        self.calls.append((geometry, options))
        return []


def test_draw_chart_supports_geometry_and_preparation_options():
    sky = CelestialSphere(object())
    layer = sky.add(Layer())
    renderer = Renderer()

    result = sky.draw_chart(
        projection=Projection(),
        renderer=renderer,
        layer_options={
            layer: {
                "geometry": {"minimum": 5.0},
                "prepare": lambda spherical, projected: clip_to_latitude(
                    spherical,
                    projected,
                    minimum=10.0,
                ),
                "render": {"style": {"color": "white"}},
            }
        },
    )

    assert result.layers[0].spherical.lat_deg[0] == 5.0
    assert np.isnan(result.layers[0].projected.x[0])
    assert renderer.calls[0][1] == {
        "style": {"color": "white"}
    }


def test_render_options_may_be_derived_from_geometry():
    sky = CelestialSphere(object())
    sky.add(Layer())
    renderer = Renderer()
    sky.draw_chart(
        projection=Projection(),
        renderer=renderer,
        layer_options={
            "test": {
                "render": lambda spherical, projected: {
                    "style": {"s": np.arange(len(spherical))}
                }
            }
        },
    )
    assert np.array_equal(
        renderer.calls[0][1]["style"]["s"],
        [0, 1],
    )


def test_curve_clipping_preserves_visible_runs():
    spherical = SphericalCurves(
        lon_deg=([0.0, 1.0, 2.0, 3.0],),
        lat_deg=([-1.0, 1.0, 2.0, -1.0],),
    )
    projected = ProjectedCurves(
        items=[
            ProjectedCurve(
                x=[0.0, 1.0, 2.0, 3.0],
                y=[0.0, 1.0, 2.0, 3.0],
            )
        ]
    )
    clipped = clip_to_latitude(spherical, projected)
    assert len(clipped) == 1
    np.testing.assert_allclose(
    clipped[0].x,
    [0.5, 1.0, 2.0, 8.0 / 3.0],
    )


def test_curve_clipping_subsets_all_per_entity_metadata():
    spherical = SphericalCurves(
        lon_deg=(
            [0.0, 1.0, 2.0],
            [0.0, 1.0, 2.0, 3.0, 4.0],
        ),
        lat_deg=(
            [-2.0, -2.0, -2.0],
            [1.0, 1.0, -1.0, 1.0, 1.0],
        ),
    )
    projected = ProjectedCurves(
        items=[
            ProjectedCurve(
                x=[0.0, 1.0, 2.0],
                y=[0.0, 1.0, 2.0],
            ),
            ProjectedCurve(
                x=[0.0, 1.0, 2.0, 3.0, 4.0],
                y=[0.0, 1.0, 2.0, 3.0, 4.0],
            ),
        ],
        metadata={
            "semantic_entity_keys": ("north", "south"),
            "semantic_entity_display_names": ("North", "South"),
            "styles": ({"color": "red"}, {"color": "blue"}),
            "collection_value": "preserved",
        },
    )

    clipped = clip_to_latitude(spherical, projected)

    assert len(clipped) == 2
    assert clipped.metadata["semantic_entity_keys"] == (
        "south", "south"
    )
    assert clipped.metadata["semantic_entity_display_names"] == (
        "South", "South"
    )
    assert clipped.metadata["styles"] == (
        {"color": "blue"}, {"color": "blue"}
    )
    assert clipped.metadata["collection_value"] == "preserved"


def test_curve_clipping_supports_a_maximum_latitude():
    spherical = SphericalCurves(
        lon_deg=([0.0, 1.0, 2.0, 3.0],),
        lat_deg=([1.0, -1.0, -2.0, 1.0],),
    )
    projected = ProjectedCurves(
        items=[
            ProjectedCurve(
                x=[0.0, 1.0, 2.0, 3.0],
                y=[0.0, 1.0, 2.0, 3.0],
            )
        ]
    )

    clipped = clip_to_latitude(
        spherical,
        projected,
        minimum=-90.0,
        maximum=0.0,
    )

    assert len(clipped) == 1
    np.testing.assert_allclose(
        clipped[0].x,
        [0.5, 1.0, 2.0, 8.0 / 3.0],
    )


def test_magnitude_sizes_matches_legacy_formula():
    sizes = magnitude_sizes([5.0, 4.0])
    assert sizes[0] == 1.5
    assert sizes[1] > sizes[0]


def test_radial_label_offset():
    offset = radial_label_offset(0.1)
    np.testing.assert_allclose(
        offset(3.0, 4.0),
        (0.06, 0.08),
    )
