"""Fixed-frame grid contracts for frozen-Earth visualizations."""

from types import SimpleNamespace

import numpy as np

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.sky.frozen_earth_reference_grids import (
    FrozenEarthEclipticReference,
    FrozenEarthEquatorialGrid,
)
from wenu.sky.realization import LayerRealizationContext


def product_spec():
    return CoordinateSpec(
        frame="barycentric-mean-ecliptic",
        origin="frozen-earth",
        position_status=PositionStatus.GEOMETRIC,
        equinox="J2000",
        instant="2026-08-30T00:00:00Z",
        time_scale="utc",
        provider="test",
        model="fixed-Earth J2000 ecliptic construction",
    )


def test_equatorial_grid_is_realized_directly_in_fixed_product_axes():
    grid = FrozenEarthEquatorialGrid(
        SimpleNamespace(),
        product_coordinate_spec=product_spec(),
        frame="fk5",
        equinox="J2000",
        samples=37,
        ra=(0.0, 90.0),
        dec=(-30.0, 30.0),
        meridian_dec_min=-75.0,
        meridian_dec_max=90.0,
    )

    first = grid.spherical_geometry(SimpleNamespace(name="La Ligua"))
    second = grid.spherical_geometry(SimpleNamespace(name="Elsewhere"))

    assert first.coordinate_spec == product_spec()
    assert first.metadata["output_coordinate_system"] == (
        "barycentric-mean-ecliptic"
    )
    assert tuple(first.components) == ("meridians", "parallels")
    for name in first.components:
        for left, right in zip(
            first[name].lon_deg, second[name].lon_deg
        ):
            assert np.array_equal(left, right)
        for left, right in zip(
            first[name].lat_deg, second[name].lat_deg
        ):
            assert np.array_equal(left, right)


def test_ecliptic_reference_is_product_latitude_zero():
    context = LayerRealizationContext(product_spec())
    geometry = FrozenEarthEclipticReference().realize(
        context,
        SimpleNamespace(name="ignored"),
    )
    reference = geometry["reference"]

    assert geometry.coordinate_spec == product_spec()
    assert reference.names.tolist() == ["ecliptic"]
    assert reference.closed.tolist() == [True]
    assert np.array_equal(
        reference.lat_deg[0], np.zeros(reference.lat_deg[0].shape)
    )
    assert reference.lon_deg[0][0] == 0.0
    assert reference.lon_deg[0][-1] < 360.0
