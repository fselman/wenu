from __future__ import annotations

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import (
    AltAz,
    BarycentricTrueEcliptic,
    EarthLocation,
    FK4,
    FK5,
    Galactic,
    ICRS,
    SkyCoord,
)
from astropy.time import Time

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import (
    CoordinateSpec,
    ICRS_ASTROMETRIC_SPEC,
    ObservationContext,
    PositionStatus,
)
from wenu.geometry.spherical import (
    SphericalCurves,
    SphericalGrid,
    SphericalPoints,
    SphericalPolygons,
)


GALACTIC_SPEC = CoordinateSpec(
    frame="galactic",
    origin="galactic-center",
    position_status=PositionStatus.ASTROMETRIC,
    provider="astropy",
)


def test_points_match_astropy_and_preserve_semantics():
    points = SphericalPoints(
        lon_deg=np.array([0.0, 83.6331]),
        lat_deg=np.array([0.0, 22.0145]),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
        ids=np.array(["origin", "crab"], dtype=object),
        labels=np.array(["O", "M1"], dtype=object),
        names=np.array(["Origin", "Crab"], dtype=object),
        metadata={"family": "test"},
    )

    transformed = CoordinateService().transform(points, GALACTIC_SPEC)
    expected = SkyCoord(
        points.lon_deg * u.deg,
        points.lat_deg * u.deg,
        frame=ICRS(),
    ).transform_to(Galactic()).spherical

    assert isinstance(transformed, SphericalPoints)
    np.testing.assert_allclose(
        transformed.lon_deg, expected.lon.to_value(u.deg), atol=1e-10
    )
    np.testing.assert_allclose(
        transformed.lat_deg, expected.lat.to_value(u.deg), atol=1e-10
    )
    assert transformed.coordinate_spec is GALACTIC_SPEC
    np.testing.assert_array_equal(transformed.ids, points.ids)
    np.testing.assert_array_equal(transformed.labels, points.labels)
    np.testing.assert_array_equal(transformed.names, points.names)
    assert transformed.metadata == points.metadata
    assert transformed.ids is not points.ids
    assert transformed.metadata is not points.metadata


def test_icrs_galactic_round_trip_is_coincident():
    points = SphericalPoints(
        lon_deg=np.array([12.0, 120.0, 310.0]),
        lat_deg=np.array([-60.0, 0.0, 75.0]),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
    )
    service = CoordinateService()

    galactic = service.transform(points, GALACTIC_SPEC)
    restored = service.transform(galactic, ICRS_ASTROMETRIC_SPEC)

    np.testing.assert_allclose(restored.lon_deg, points.lon_deg, atol=1e-10)
    np.testing.assert_allclose(restored.lat_deg, points.lat_deg, atol=1e-10)


def test_curves_preserve_segmentation_closure_and_semantics():
    curves = SphericalCurves(
        lon_deg=(np.array([0.0, 1.0]), np.array([10.0, 20.0, 30.0])),
        lat_deg=(np.array([2.0, 3.0]), np.array([-5.0, 0.0, 5.0])),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
        closed=np.array([False, True]),
        ids=np.array(["a", "b"], dtype=object),
        names=np.array(["first", "second"], dtype=object),
        metadata={"role": "grid"},
    )

    transformed = CoordinateService().transform(curves, GALACTIC_SPEC)

    assert isinstance(transformed, SphericalCurves)
    assert tuple(map(len, transformed.lon_deg)) == (2, 3)
    np.testing.assert_array_equal(transformed.closed, curves.closed)
    np.testing.assert_array_equal(transformed.ids, curves.ids)
    np.testing.assert_array_equal(transformed.names, curves.names)
    assert transformed.metadata == curves.metadata


def test_polygons_preserve_ring_topology():
    polygons = SphericalPolygons(
        lon_deg=(np.array([0.0, 1.0, 0.0]), np.array([20.0, 21.0, 21.0, 20.0])),
        lat_deg=(np.array([0.0, 0.0, 1.0]), np.array([5.0, 5.0, 6.0, 6.0])),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
        ids=np.array(["triangle", "box"], dtype=object),
    )

    transformed = CoordinateService().transform(polygons, GALACTIC_SPEC)

    assert isinstance(transformed, SphericalPolygons)
    assert tuple(map(len, transformed.lon_deg)) == (3, 4)
    np.testing.assert_array_equal(transformed.ids, polygons.ids)


def test_grid_preserves_component_names_and_component_semantics():
    component = SphericalCurves(
        lon_deg=(np.array([0.0, 10.0]),),
        lat_deg=(np.array([0.0, 5.0]),),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
        names=np.array(["meridian"], dtype=object),
    )
    grid = SphericalGrid(
        components={"meridians": component},
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
        metadata={"grid": "reference"},
    )

    transformed = CoordinateService().transform(grid, GALACTIC_SPEC)

    assert isinstance(transformed, SphericalGrid)
    assert tuple(transformed.components) == ("meridians",)
    assert transformed.coordinate_spec is GALACTIC_SPEC
    assert transformed["meridians"].coordinate_spec is GALACTIC_SPEC
    np.testing.assert_array_equal(
        transformed["meridians"].names, component.names
    )
    assert transformed.metadata == grid.metadata


def test_altaz_requires_explicit_observation_context():
    points = SphericalPoints(
        lon_deg=np.array([10.0]),
        lat_deg=np.array([20.0]),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
    )
    altaz_spec = CoordinateSpec(
        frame="altaz",
        origin="observer",
        position_status=PositionStatus.APPARENT,
        instant="2026-08-28T00:00:00",
        time_scale="utc",
    )

    with pytest.raises(ValueError, match="ObservationContext"):
        CoordinateService().transform(points, altaz_spec)


def test_altaz_matches_astropy_for_explicit_observation():
    context = ObservationContext(
        longitude_deg=-71.5,
        latitude_deg=-33.0,
        elevation_m=100.0,
        instant="2026-08-28T00:00:00",
    )
    altaz_spec = CoordinateSpec(
        frame="altaz",
        origin="observer",
        position_status=PositionStatus.APPARENT,
        instant=context.instant,
        time_scale=context.time_scale,
    )
    points = SphericalPoints(
        lon_deg=np.array([83.6331]),
        lat_deg=np.array([22.0145]),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
    )

    transformed = CoordinateService().transform(
        points, altaz_spec, observation=context
    )
    frame = AltAz(
        obstime=Time(context.instant, scale=context.time_scale),
        location=EarthLocation.from_geodetic(
            context.longitude_deg * u.deg,
            context.latitude_deg * u.deg,
            context.elevation_m * u.m,
        ),
        pressure=0.0 * u.hPa,
    )
    expected = SkyCoord(
        points.lon_deg * u.deg,
        points.lat_deg * u.deg,
        frame=ICRS(),
    ).transform_to(frame).spherical

    np.testing.assert_allclose(
        transformed.lon_deg, expected.lon.to_value(u.deg), atol=1e-10
    )
    np.testing.assert_allclose(
        transformed.lat_deg, expected.lat.to_value(u.deg), atol=1e-10
    )


@pytest.mark.parametrize(
    "spec, message",
    [
        (
            CoordinateSpec(
                frame="icrs",
                origin="solar-system-barycenter",
                longitude_unit="rad",
            ),
            "degree",
        ),
        (
            CoordinateSpec(
                frame="unsupported",
                origin="unknown",
            ),
            "Unsupported astronomical frame",
        ),
    ],
)
def test_unsupported_coordinate_contracts_fail_explicitly(spec, message):
    points = SphericalPoints(
        lon_deg=np.array([0.0]),
        lat_deg=np.array([0.0]),
        coordinate_spec=ICRS_ASTROMETRIC_SPEC,
    )

    with pytest.raises(ValueError, match=message):
        CoordinateService().transform(points, spec)


@pytest.mark.parametrize(
    "source_spec, source_frame",
    [
        (
            CoordinateSpec(
                frame="fk4",
                origin="solar-system-barycenter",
                position_status=PositionStatus.ASTROMETRIC,
                equinox="B1875.0",
            ),
            FK4(equinox=Time("B1875.0")),
        ),
        (
            CoordinateSpec(
                frame="fk5",
                origin="solar-system-barycenter",
                position_status=PositionStatus.ASTROMETRIC,
                equinox="J2050.0",
            ),
            FK5(equinox=Time("J2050.0")),
        ),
        (
            CoordinateSpec(
                frame="barycentric-true-ecliptic",
                origin="solar-system-barycenter",
                position_status=PositionStatus.ASTROMETRIC,
                equinox="J2050.0",
            ),
            BarycentricTrueEcliptic(equinox=Time("J2050.0")),
        ),
    ],
)
def test_reference_frames_match_astropy(source_spec, source_frame):
    points = SphericalPoints(
        lon_deg=np.array([15.0, 120.0]),
        lat_deg=np.array([-20.0, 35.0]),
        coordinate_spec=source_spec,
    )

    transformed = CoordinateService().transform(
        points, ICRS_ASTROMETRIC_SPEC
    )
    expected = SkyCoord(
        points.lon_deg * u.deg,
        points.lat_deg * u.deg,
        frame=source_frame,
    ).transform_to(ICRS()).spherical

    np.testing.assert_allclose(
        transformed.lon_deg, expected.lon.to_value(u.deg), atol=1e-10
    )
    np.testing.assert_allclose(
        transformed.lat_deg, expected.lat.to_value(u.deg), atol=1e-10
    )
