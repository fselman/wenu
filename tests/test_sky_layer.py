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


@pytest.mark.parametrize('operation,arguments', [
    ('add_stars', ()), ('add_venus', ()), ('add_moon', ()),
    ('add_solar_system_body', (object(),)), ('add_nonstellar', ()),
    ('add_galaxies', ()), ('add_open_clusters', ()),
    ('add_globular_clusters', ()), ('add_supernova_remnants', ()),
    ('add_planetary_nebulae', ()), ('add_milky_way_isophotes', ()),
    ('add_magellanic_cloud_isophotes', ('lmc',)), ('add_points', ()),
    ('add_constellations', ()), ('add_constellation_boundaries', ()),
    ('add_equatorial_grid', ()), ('add_altaz_grid', ()),
    ('add_horizon_reference', ()), ('add_ecliptic_grid', ()),
    ('add_galactic_grid', ()),
])
def test_convenience_methods_consume_supplied_assembly_without_fallback(operation, arguments):
    """Protect against silently constructing a concrete default in the core."""
    calls = []
    expected = ExampleLayer()
    class Assembly:
        def __getattr__(self, name):
            assert name == operation
            def construct(sky, *args, **kwargs):
                calls.append((sky, args, kwargs))
                return sky.add(expected)
            return construct
    sky = CelestialSphere(None, assembly=Assembly())
    assert getattr(sky, operation)(*arguments) is expected
    assert sky.layers == (expected,)
    assert calls[0][0] is sky and calls[0][1][:len(arguments)] == arguments
    class Refusing:
        def __getattr__(self, name):
            def refuse(*args, **kwargs):
                raise RuntimeError('assembly refused')
            return refuse
    sky = CelestialSphere(None, assembly=Refusing())
    with pytest.raises(RuntimeError, match='assembly refused'):
        getattr(sky, operation)(*arguments)
    assert sky.layers == ()
