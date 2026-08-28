"""Semantic observer-horizon geometry contracts."""

from types import SimpleNamespace

import numpy as np
import pytest

from wenu import AltAzGrid, CelestialSphere, HorizonReference
from wenu.sky.geometrical_object import GeometricalObject


def coordinate_observer():
    return SimpleNamespace(
        t_astropy=SimpleNamespace(
            isot="2026-08-28T00:00:00.000", scale="utc"
        )
    )


def test_horizon_is_an_independent_semantic_geometry_layer():
    assert issubclass(HorizonReference, GeometricalObject)
    assert not issubclass(HorizonReference, AltAzGrid)
    assert HorizonReference.layer_name == "horizon"


def test_horizon_reuses_native_altitude_zero_geometry():
    observer = coordinate_observer()
    geometry = HorizonReference(samples=9).spherical_geometry(observer)

    assert len(geometry.lon_deg) == 1
    np.testing.assert_allclose(geometry.lat_deg[0], 0.0)
    np.testing.assert_allclose(
        geometry.lon_deg[0], np.arange(9, dtype=float) * 40.0
    )
    assert geometry.names.tolist() == ["horizon"]
    assert geometry.closed.tolist() == [True]
    assert geometry.metadata["coordinate_system"] == "altaz"
    assert geometry.metadata["output_coordinate_system"] == "altaz"
    assert geometry.metadata["reference"] == "horizon"


def test_observerless_horizon_requires_an_explicit_observer():
    with pytest.raises(RuntimeError, match="Observer"):
        HorizonReference().spherical_geometry(None)


def test_bound_horizon_retains_compatibility_observer():
    observer = coordinate_observer()
    geometry = HorizonReference(observer, samples=5).spherical_geometry(None)

    np.testing.assert_allclose(geometry.lat_deg[0], 0.0)


def test_celestial_sphere_registers_horizon_without_an_altaz_grid():
    observer = object()
    sky = CelestialSphere(observer)

    horizon = sky.add_horizon_reference(samples=13)

    assert horizon is sky.horizon_reference
    assert horizon.observer is observer
    assert horizon.samples == 13
    assert sky.layers == (horizon,)
    assert not any(isinstance(layer, AltAzGrid) for layer in sky.layers)


def test_horizon_sample_count_is_validated():
    with pytest.raises(ValueError, match="at least 4"):
        HorizonReference(samples=3)
