"""Observer-latitude geometry for the paired polar horizon overlay."""

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, ICRS
from astropy.time import Time
import numpy as np
import pytest

from wenu import (
    PolarHorizonOverlayRequest,
    PolarHorizonPairOverlay,
    PolarPageFurnitureRequest,
    PolarPlanispherePairRequest,
)


LATITUDE = -32.443342


def observer(latitude=LATITUDE):
    location = EarthLocation.from_geodetic(
        lon=-71.230289 * u.deg,
        lat=latitude * u.deg,
        height=50.0 * u.m,
    )
    return SimpleNamespace(
        lat_deg=latitude,
        altaz_frame=AltAz(
            obstime=Time("2026-08-16T01:00:00"), location=location
        ),
        icrs_frame=ICRS(),
    )


def resolved_overlay(**options):
    pair = PolarPlanispherePairRequest().resolve()
    pages = PolarPageFurnitureRequest(source_revision="b3a95ae").resolve(pair)
    overlay = PolarHorizonOverlayRequest(**options).resolve(
        pair, pages, observer()
    )
    return pair, pages, overlay


def test_request_resolves_paired_canonical_horizon_geometry():
    _, pages, overlay = resolved_overlay()

    assert isinstance(overlay, PolarHorizonPairOverlay)
    assert overlay.faces == (overlay.south, overlay.north)
    for face, page in zip(overlay.faces, pages.faces, strict=True):
        assert face.page_size_mm == pytest.approx((210.0, 297.0))
        assert face.disk_center_mm == pytest.approx(page.disk_center_mm)
        assert face.disk_radius_mm == pytest.approx(97.5)
        assert face.site_latitude_deg == pytest.approx(LATITUDE)
        assert face.cut_clearance_mm == pytest.approx(1.0)
        assert face.horizon_segments_mm
        for segment in face.horizon_segments_mm:
            assert len(segment) >= 2


def test_geographic_orientation_matches_each_face_in_the_hands():
    _, _, overlay = resolved_overlay()
    center_x, center_y = overlay.south.disk_center_mm
    south = {item.label: item.position_mm for item in overlay.south.cardinals}
    north = {item.label: item.position_mm for item in overlay.north.cardinals}

    assert tuple(south) == ("E", "S", "W")
    assert south["E"][0] < center_x < south["W"][0]
    assert south["E"][1] == pytest.approx(center_y, abs=0.2)
    assert south["W"][1] == pytest.approx(center_y, abs=0.2)
    assert south["S"][1] < center_y
    assert tuple(north) == ("W", "N", "E")
    assert north["W"][0] < center_x < north["E"][0]
    assert north["W"][1] == pytest.approx(center_y, abs=0.2)
    assert north["E"][1] == pytest.approx(center_y, abs=0.2)
    assert north["N"][1] > center_y


def test_pole_to_meridian_horizon_distance_encodes_site_latitude():
    pair, _, overlay = resolved_overlay()

    expected = (
        abs(LATITUDE)
        / pair.south.angular_radius_deg
        * pair.south_registration.outer_radius_mm
    )
    assert overlay.south.pole_to_horizon_mm == pytest.approx(
        expected, abs=0.5
    )
    assert overlay.north.pole_to_horizon_mm == pytest.approx(
        expected, abs=0.5
    )


def test_disk_is_wholly_contained_by_the_physical_overlay_page():
    _, _, overlay = resolved_overlay()

    for face in overlay.faces:
        center_x, center_y = face.disk_center_mm
        radius = face.disk_radius_mm
        width, height = face.page_size_mm
        assert center_x - radius >= 0.0
        assert center_x + radius <= width
        assert center_y - radius >= 0.0
        assert center_y + radius <= height


def test_request_validates_identity_and_is_immutable_and_public():
    pair = PolarPlanispherePairRequest().resolve()
    pages = PolarPageFurnitureRequest(source_revision="b3a95ae").resolve(pair)
    request = PolarHorizonOverlayRequest()

    with pytest.raises(ValueError, match="latitude must match"):
        request.resolve(pair, pages, observer(latitude=-33.0))
    with pytest.raises(TypeError, match="pair"):
        request.resolve(object(), pages, observer())
    with pytest.raises(TypeError, match="pages"):
        request.resolve(pair, object(), observer())
    with pytest.raises(FrozenInstanceError):
        request.samples = 100
    with pytest.raises(ValueError, match="samples"):
        PolarHorizonOverlayRequest(samples=8)
    with pytest.raises(ValueError, match="cut_clearance"):
        PolarHorizonOverlayRequest(cut_clearance_mm=-1.0)

    import wenu

    for name in (
        "PolarHorizonCardinal",
        "PolarHorizonFaceOverlay",
        "PolarHorizonOverlayRequest",
        "PolarHorizonPairOverlay",
    ):
        assert name in wenu.__all__
