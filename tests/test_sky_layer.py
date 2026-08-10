"""Milestone 6 tests for the common SkyLayer contract."""

from __future__ import annotations

import pytest

from wenu.sky import CelestialSphere, SkyLayer


class ExampleLayer(SkyLayer):
    layer_name = "example"

    def __init__(self, geometry=None):
        self.geometry = geometry

    def spherical_geometry(self, observer):
        return self.geometry


class DrawOnlyLayer:
    def draw(self, ax, projection):
        return []


def test_sky_layer_is_abstract():
    with pytest.raises(TypeError):
        SkyLayer()


def test_valid_sky_layer_is_accepted_and_returned():
    sphere = CelestialSphere(observer=object())
    layer = ExampleLayer()

    assert sphere.add(layer) is layer
    assert sphere.layers == (layer,)


def test_object_outside_sky_layer_contract_is_rejected():
    sphere = CelestialSphere(observer=object())

    with pytest.raises(TypeError, match="SkyLayer"):
        sphere.add(object())


def test_draw_method_alone_no_longer_satisfies_layer_contract():
    sphere = CelestialSphere(observer=object())

    with pytest.raises(TypeError, match="SkyLayer"):
        sphere.add(DrawOnlyLayer())


def test_layer_order_is_preserved():
    sphere = CelestialSphere(observer=object())
    first = ExampleLayer("first")
    second = ExampleLayer("second")

    sphere.extend([first, second])

    assert sphere.layers == (first, second)


def test_remove_preserves_remaining_layers():
    sphere = CelestialSphere(observer=object())
    first = ExampleLayer("first")
    second = ExampleLayer("second")
    sphere.extend([first, second])

    sphere.remove(first)

    assert sphere.layers == (second,)


def test_clear_removes_all_layers():
    sphere = CelestialSphere(observer=object())
    sphere.extend([ExampleLayer("first"), ExampleLayer("second")])

    sphere.clear()

    assert sphere.layers == ()
