"""Projection-neutral observer-horizon mask-opening contracts."""

from types import SimpleNamespace

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, Galactic
from astropy.time import Time
import numpy as np
import pytest

from wenu import (
    AllSkyChart,
    BinocularChart,
    CircumpolarChart,
    HorizonReference,
    RegionalChart,
    StereographicProjection,
    prepare_horizon_mask_opening,
)
from wenu.charts.coordinate_frames import horizontal_to_galactic
from wenu.geometry.frame import SphericalFrame


def observer():
    location = EarthLocation.from_geodetic(
        lon=-71.230289 * u.deg,
        lat=-32.443342 * u.deg,
        height=50.0 * u.m,
    )
    return SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-08-16T01:00:00"),
            location=location,
        ),
        galactic_frame=Galactic(),
    )


def prepared(chart, actual_observer=None, *, samples=73):
    return prepare_horizon_mask_opening(
        projection=chart.projection,
        viewport=chart.viewport,
        boundary=getattr(chart, "field_stop", None),
        observer=object() if actual_observer is None else actual_observer,
        samples=samples,
        radial_step_deg=15.0,
    )


def test_visible_hemisphere_is_native_altaz_opening_geometry():
    geometry = HorizonReference(samples=13).visible_hemisphere_geometry(
        object(), radial_step_deg=30.0
    )

    assert len(geometry) == 13
    assert geometry.metadata["mask_opening"] == "above_horizon"
    assert geometry.metadata["source_coordinate_system"] == "altaz"
    assert all(np.min(latitude) == pytest.approx(0.0)
               for latitude in geometry.lat_deg)
    assert all(np.max(latitude) == pytest.approx(90.0)
               for latitude in geometry.lat_deg)


def test_stereographic_inverse_round_trips_source_coordinates():
    projection = StereographicProjection(
        frame=SphericalFrame(
            pole_lon_deg=125.0,
            pole_lat_deg=23.0,
            position_angle_deg=17.0,
        )
    )
    longitude = np.asarray((110.0, 125.0, 142.0))
    latitude = np.asarray((18.0, 23.0, 31.0))

    x, y = projection.project_spherical(longitude, latitude)
    restored = projection.unproject_spherical(x, y)

    np.testing.assert_allclose(restored.lon_deg, longitude, atol=1.0e-10)
    np.testing.assert_allclose(restored.lat_deg, latitude, atol=1.0e-10)


@pytest.mark.parametrize(
    ("center_altitude", "visibility", "opening_count"),
    ((30.0, "above", 1), (0.0, "crossing", None), (-30.0, "below", 0)),
)
def test_regional_fields_distinguish_horizon_visibility(
    center_altitude, visibility, opening_count
):
    chart = RegionalChart(
        center_alt_deg=center_altitude,
        center_az_deg=180.0,
        field_width_deg=10.0,
        field_height_deg=10.0,
    )

    result = prepared(chart)

    assert result.visibility == visibility
    if opening_count is None:
        assert len(result.projected) > 0
    else:
        assert len(result.projected) == opening_count
    assert result.projected.metadata["horizon_visibility"] == visibility


def test_binocular_crossing_uses_the_circular_field_boundary():
    chart = BinocularChart(
        center_alt_deg=0.0,
        center_az_deg=90.0,
        field_diameter_deg=6.5,
    )

    result = prepared(chart)

    assert result.visibility == "crossing"
    assert len(result.projected) > 0
    assert all(np.all(polygon.finite) for polygon in result.projected)


@pytest.mark.parametrize(
    ("pole", "limit", "visibility"),
    (
        ("south", -69.75, "above"),
        ("south", -30.0, "crossing"),
        ("north", 69.75, "below"),
    ),
)
def test_circumpolar_fields_use_observer_horizon_altitudes(
    pole, limit, visibility
):
    actual_observer = observer()
    chart = CircumpolarChart(
        actual_observer,
        limiting_declination_deg=limit,
        pole=pole,
    )

    assert prepared(chart, actual_observer).visibility == visibility


def test_complete_sphere_transforms_then_uses_mollweide_seam_topology():
    actual_observer = observer()
    chart = AllSkyChart()

    result = prepare_horizon_mask_opening(
        projection=chart.projection,
        viewport=chart.viewport,
        observer=actual_observer,
        transform_spherical=lambda spherical: horizontal_to_galactic(
            spherical, actual_observer
        ),
        complete_sphere=True,
        samples=37,
        radial_step_deg=15.0,
    )

    assert result.visibility == "crossing"
    assert len(result.projected) >= len(result.spherical)
    assert result.projected.metadata["coordinate_system"] == "galactic"
    assert result.projected.metadata["mask_opening"] == "above_horizon"
    assert all(np.all(polygon.finite) for polygon in result.projected)
