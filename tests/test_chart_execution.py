"""Milestone 14 tests for generic CelestialSphere orchestration."""

from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from wenu.chart_document import EditPolicy
from wenu.sky.rendering_results import ChartRenderingResult
from wenu.geometry.projected import ProjectedPoints
from wenu.projections.stereographic import StereographicProjection
from wenu.rendering import MatplotlibRenderer
from wenu.rendering.paint_roles import POINTS
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.sky_layer import SkyLayer
from wenu.sky.semantic_identity import (
    SemanticLayerIdentity,
    semantic_layer_identity,
)
from wenu.geometry.spherical import SphericalPoints
from wenu.geometry.viewport import Viewport


class StubLayer(SkyLayer):
    def __init__(self, name, calls, longitude):
        self.layer_name = name
        self.calls = calls
        self.longitude = longitude

    def spherical_geometry(self, observer):
        self.calls.append(("geometry", self.layer_name, observer))
        return SphericalPoints(
            lon_deg=[self.longitude],
            lat_deg=[45.0],
            metadata={"layer": self.layer_name},
        )


class StubProjection:
    def __init__(self, calls):
        self.calls = calls

    def project_geometry(self, geometry):
        name = geometry.metadata["layer"]
        self.calls.append(("projection", name))
        return ProjectedPoints(
            x=geometry.lon_deg,
            y=geometry.lat_deg,
            metadata=geometry.metadata,
        )


class StubRenderer:
    def __init__(self, calls):
        self.calls = calls

    def apply_viewport(self, viewport):
        self.calls.append(("viewport", viewport))

    def draw(self, projected, **options):
        name = projected.metadata["layer"]
        self.calls.append(("renderer", name, options))
        return [f"artist:{name}"]


def test_draw_chart_preserves_layer_order_and_pipeline():
    observer = object()
    calls = []
    sky = CelestialSphere(observer)
    first = StubLayer("first", calls, 10.0)
    second = StubLayer("second", calls, 20.0)
    sky.extend([first, second])
    projection = StubProjection(calls)
    renderer = StubRenderer(calls)
    viewport = object()

    result = sky.draw_chart(
        projection=projection,
        renderer=renderer,
        viewport=viewport,
        layer_options={
            "first": {"style": {"color": "red"}},
        },
    )

    assert isinstance(result, ChartRenderingResult)
    assert [item.layer for item in result.layers] == [first, second]
    assert [item.semantic_identity for item in result.layers] == [
        SemanticLayerIdentity(name="first", svg_id="wenu-layer-first"),
        SemanticLayerIdentity(name="second", svg_id="wenu-layer-second"),
    ]
    assert all(not item.semantic_artists for item in result.layers)
    assert calls == [
        ("viewport", viewport),
        ("geometry", "first", observer),
        ("projection", "first"),
        (
            "renderer",
            "first",
            {"style": {"color": "red"}},
        ),
        ("geometry", "second", observer),
        ("projection", "second"),
        ("renderer", "second", {}),
    ]


def test_layer_instance_options_override_name_options():
    calls = []
    layer = StubLayer("points", calls, 10.0)
    sky = CelestialSphere(object())
    sky.add(layer)

    sky.draw_chart(
        projection=StubProjection(calls),
        renderer=StubRenderer(calls),
        layer_options={
            "points": {"style": {"color": "white"}},
            layer: {"style": {"color": "cyan"}},
        },
    )

    assert calls[-1] == (
        "renderer",
        "points",
        {"style": {"color": "cyan"}},
    )


def test_explicit_observer_overrides_bound_observer():
    calls = []
    bound_observer = object()
    explicit_observer = object()
    sky = CelestialSphere(bound_observer)
    sky.add(StubLayer("points", calls, 10.0))

    sky.draw_chart(
        projection=StubProjection(calls),
        renderer=StubRenderer(calls),
        observer=explicit_observer,
    )

    assert ("geometry", "points", explicit_observer) in calls
    assert ("geometry", "points", bound_observer) not in calls


def test_observerless_sphere_requires_explicit_observer():
    sky = CelestialSphere(None)
    sky.add(StubLayer("points", [], 10.0))

    with pytest.raises(TypeError, match="requires an observer"):
        sky.draw_chart(
            projection=StubProjection([]),
            renderer=StubRenderer([]),
        )


def test_repeated_rendering_with_different_projection_and_viewport():
    sky = CelestialSphere(SimpleNamespace())
    sky.add(StubLayer("test", [], 30.0))

    figure1, ax1 = plt.subplots()
    viewport1 = Viewport.centered(width=4.0, height=4.0)
    first = sky.draw_chart(
        projection=StereographicProjection(
            radius=2.0,
            flip_ew=False,
        ),
        renderer=MatplotlibRenderer(ax1),
        viewport=viewport1,
        layer_options={
            "test": {"style": {"s": 20.0, "c": "white", "zorder": 6.0}},
        },
    )

    figure2, ax2 = plt.subplots()
    viewport2 = Viewport.centered(width=2.0, height=2.0)
    second = sky.draw_chart(
        projection=StereographicProjection(
            radius=1.0,
            flip_ew=True,
        ),
        renderer=MatplotlibRenderer(ax2),
        viewport=viewport2,
        layer_options={
            "test": {"style": {"s": 20.0, "c": "white"}},
        },
    )

    assert first.layers[0].projected.x[0] == -second.layers[0].projected.x[0] * 2
    assert ax1.get_xlim() == viewport1.xlim
    assert (
        first.layers[0].artists[0].get_gid()
        == "wenu-layer-test--0001"
    )
    semantic_artist = first.layers[0].semantic_artists[0]
    assert semantic_artist.artist is first.layers[0].artists[0]
    assert semantic_artist.svg_id == "wenu-layer-test--0001"
    assert semantic_artist.zorder == 6.0
    assert semantic_artist.paint_role is POINTS
    assert semantic_artist.edit_policy is EditPolicy.STYLE
    assert semantic_artist.semantic_path == ("test",)
    assert semantic_artist.display_name == "Test"
    assert semantic_artist.presentation_order is None
    assert semantic_artist.style_role == "test"
    assert ax2.get_xlim() == viewport2.xlim
    plt.close(figure1)
    plt.close(figure2)


def test_draw_chart_rejects_non_renderer():
    sky = CelestialSphere(object())
    sky.add(StubLayer("test", [], 0.0))

    try:
        sky.draw_chart(
            projection=StubProjection([]),
            renderer=object(),
        )
    except TypeError as error:
        assert "draw" in str(error)
    else:
        raise AssertionError("Expected TypeError")


def test_grid_convenience_helpers_register_layers():
    observer = SimpleNamespace(t_astropy=object())
    sky = CelestialSphere(observer)

    equatorial = sky.add_equatorial_grid(
        ra=[0.0, 90.0],
        dec=[-30.0, 0.0, 30.0],
        include_equator=True,
    )
    ecliptic = sky.add_ecliptic_grid(include_ecliptic=True)
    galactic = sky.add_galactic_grid(include_plane=True)

    assert sky.layers == (equatorial, ecliptic, galactic)
    assert equatorial.ra == (0.0, 90.0)
    assert equatorial.dec == (-30.0, 0.0, 30.0)
    assert equatorial.include_equator
    assert ecliptic.include_ecliptic
    assert galactic.include_plane


def test_coordinate_grid_identity_uses_coordinate_system():
    layer = SimpleNamespace(
        layer_name="coordinates_grid",
        coordinate_system="equatorial",
    )

    identity = semantic_layer_identity(layer)

    assert identity.name == "equatorial_grid"
    assert identity.svg_id == "wenu-layer-equatorial-grid"
    assert identity.semantic_path == ("sky", "grids", "equatorial")
    assert identity.display_name == "Equatorial grid"
    assert identity.presentation_order == 70
    assert identity.style_role == "equatorial_grid"
    assert tuple(dict(identity.component_contracts)) == ("lines", "labels")


def test_semantic_identity_supports_unnamed_layers_and_rejects_unsafe_names():
    assert semantic_layer_identity(SimpleNamespace(layer_name=None)) is None
    with pytest.raises(ValueError, match="safe semantic name"):
        semantic_layer_identity(SimpleNamespace(layer_name="translated label"))


def test_label_layers_receive_layout_edit_policy():
    identity = semantic_layer_identity(
        SimpleNamespace(layer_name="constellation_labels")
    )

    assert identity.edit_policy is EditPolicy.LAYOUT
    assert identity.semantic_path == (
        "sky", "constellations", "labels_western"
    )
    assert identity.parent_path == ("sky", "constellations")
    assert identity.presentation_order == 52


def test_layer_can_declare_no_supported_external_edits():
    identity = semantic_layer_identity(
        SimpleNamespace(
            layer_name="technical_geometry",
            semantic_edit_policy="none",
        )
    )

    assert identity.edit_policy is EditPolicy.NONE
