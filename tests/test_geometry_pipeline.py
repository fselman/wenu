"""Milestone 15A tests for canonical rendering preparation."""

from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from wenu.coordinates import GENERIC_SPHERICAL_SPEC

from wenu.geometry.projected import (
    ProjectedCurve,
    ProjectedCurves,
    ProjectedPoints,
    ProjectedPolygon,
    ProjectedPolygons,
)
from wenu.rendering.preparation import (
    clip_to_latitude,
    magnitude_sizes,
    radial_label_offset,
)
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.sky_layer import SkyLayer
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalPoints,
    SphericalPolygons,
)


class Layer(SkyLayer):
    layer_name = "test"

    def spherical_geometry(self, observer, *, minimum=-10.0):
        return SphericalPoints(coordinate_spec=GENERIC_SPHERICAL_SPEC,
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
    spherical = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
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
    spherical = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
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


def test_polygon_boundary_clipping_subsets_entity_metadata():
    spherical = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=(
            [0.0, 1.0, 1.0, 0.0],
            [2.0, 3.0, 3.0, 2.0],
        ),
        lat_deg=(
            [-2.0, -2.0, -1.0, -1.0],
            [1.0, 1.0, 2.0, 2.0],
        ),
    )
    projected = ProjectedPolygons(
        items=[
            ProjectedPolygon(
                x=[0.0, 1.0, 1.0, 0.0],
                y=[0.0, 0.0, 1.0, 1.0],
            ),
            ProjectedPolygon(
                x=[2.0, 3.0, 3.0, 2.0],
                y=[0.0, 0.0, 1.0, 1.0],
            ),
        ],
        metadata={
            "semantic_entity_keys": ("hidden", "visible"),
            "semantic_entity_display_names": ("Hidden", "Visible"),
        },
    )

    clipped = clip_to_latitude(spherical, projected)

    assert len(clipped) == 1
    assert clipped.metadata["semantic_entity_keys"] == ("visible",)
    assert clipped.metadata["semantic_entity_display_names"] == (
        "Visible",
    )


def test_curve_clipping_supports_a_maximum_latitude():
    spherical = SphericalCurves(coordinate_spec=GENERIC_SPHERICAL_SPEC,
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


@pytest.mark.parametrize("family", ("regional", "full-sky"))
def test_chart_domain_return_controls_prepare_and_draw_after_success(monkeypatch, family):
    """Protect the canonical guard seam, including refusal after a warm draw."""
    from wenu.charts import regional, full_sky

    module = regional if family == "regional" else full_sky
    chart = (regional.RegionalChart(center_alt_deg=90, center_az_deg=0,
             field_width_deg=30, field_height_deg=30)
             if family == "regional" else full_sky.FullSkyChart())
    sky = CelestialSphere(object())
    layer = sky.add(Layer())
    renderer = Renderer()
    renderer.apply_viewport = lambda viewport: None
    renderer.set_clip_boundary = lambda boundary, **kwargs: None
    prepared = []
    calls = []
    returned = ProjectedPoints(x=[0.11, -0.23], y=[-0.17, 0.19],
                               ids=["first", "second"], metadata={"receipt": "synthetic guard"})

    def guard(spherical, *, projection, viewport):
        calls.append((spherical, projection, viewport))
        if len(calls) > 1:
            raise ValueError("synthetic domain refusal")
        return returned

    def prepare(spherical, projected):
        prepared.append((spherical, projected))
        assert projected is returned
        return ProjectedPoints(x=projected.x + 0.01, y=projected.y,
                               ids=projected.ids, metadata=projected.metadata)

    monkeypatch.setattr(module, "project_geometry_for_viewport", guard)
    options = {layer: {"prepare": prepare, "render": {"style": {"color": "red"}}}}
    result = chart.render(sky, renderer=renderer, layer_options=options)
    assert len(calls) == len(prepared) == len(renderer.calls) == 1
    assert calls[0][0] is result.layers[0].spherical
    assert calls[0][2] == chart.viewport
    assert renderer.calls[0][0] is result.layers[0].projected
    np.testing.assert_allclose(renderer.calls[0][0].x, [0.12, -0.22])
    assert renderer.calls[0][0].ids.tolist() == ["first", "second"]
    assert renderer.calls[0][0].metadata["receipt"] == "synthetic guard"
    with pytest.raises(ValueError, match="synthetic domain refusal"):
        chart.render(sky, renderer=renderer, layer_options=options)
    assert len(calls) == 2
    assert len(prepared) == len(renderer.calls) == 1


@pytest.mark.parametrize("kind", ("stereographic", "polar_azimuthal_equidistant", "mollweide"))
def test_kernel_projection_return_controls_canonical_render_and_refusal(monkeypatch, kind):
    import importlib
    from dataclasses import replace

    names = {"stereographic": "StereographicProjection",
             "polar_azimuthal_equidistant": "PolarAzimuthalEquidistantProjection",
             "mollweide": "MollweideProjection"}
    cls = getattr(importlib.import_module("wenu_kernel.projections." + kind), names[kind])
    original = cls.project_geometry
    calls = []

    def returned_projection(self, spherical):
        calls.append(spherical)
        if len(calls) > 1:
            raise ValueError("synthetic projection refusal")
        # Deliberately change a real return: a consumer recomputing the original
        # projection or reusing the first draw must not pass this contract.
        return replace(original(self, spherical), x=np.array([0.17, -0.29]))

    monkeypatch.setattr(cls, "project_geometry", returned_projection)
    sky = CelestialSphere(object())
    sky.add(Layer())
    renderer = Renderer()
    projection = cls()
    result = sky.draw_chart(projection=projection, renderer=renderer)
    assert len(calls) == 1
    np.testing.assert_array_equal(renderer.calls[0][0].x, [0.17, -0.29])
    assert renderer.calls[0][0] is result.layers[0].projected
    with pytest.raises(ValueError, match="synthetic projection refusal"):
        sky.draw_chart(projection=projection, renderer=renderer)
    assert len(calls) == 2 and len(renderer.calls) == 1
