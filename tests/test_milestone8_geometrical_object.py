"""Milestone 8 tests for the GeometricalObject hierarchy."""

import pytest

from wenu.objects.astronomical_object import AstronomicalObject
from wenu.sky import GeometricalObject, SkyLayer
from wenu.sky.constellation_boundaries import ConstellationBoundaries


def test_geometrical_object_is_abstract_sky_layer():
    assert issubclass(GeometricalObject, SkyLayer)

    with pytest.raises(TypeError):
        GeometricalObject()


def test_geometrical_and_astronomical_branches_are_distinct():
    assert not issubclass(GeometricalObject, AstronomicalObject)
    assert not issubclass(AstronomicalObject, GeometricalObject)


def test_constellation_boundaries_are_geometrical_objects():
    assert issubclass(
        ConstellationBoundaries,
        GeometricalObject,
    )
    assert not issubclass(
        ConstellationBoundaries,
        AstronomicalObject,
    )

