"""Deterministic proof that Moon uses the shared direction contracts."""

from types import SimpleNamespace

import pytest
from astropy.time import Time

from wenu.ephemeris import EphemerisResourceIdentity, EphemerisState
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
)
from wenu.solar_system_directions import (
    AstrometricDirectionRealizer,
    AstrometricDirectionRequest,
    ObserverBarycentricState,
)

RESOURCE = EphemerisResourceIdentity(
    provider="test/JPL",
    model="DE440-test",
    filename="deterministic.bsp",
    sha256="a" * 64,
    coverage_start="JD 2400000.5",
    coverage_end="JD 2500000.5",
    coverage_time_scale="tdb",
)
INSTANT = "2026-08-30T00:00:00.000"


class MoonSource:
    def state(self, request):
        return EphemerisState(
            request=request,
            position=(1.0025, 0.0004, 0.0002),
            velocity=(0.001, 0.002, 0.003),
            position_unit="au",
            velocity_unit="au/day",
            resource=RESOURCE,
            provider_target_id="301",
            provider_centre_id="0",
        )


def _astrometric():
    observer = ObserverBarycentricState(
        observer_id="La Ligua 52 m",
        centre="solar system barycenter",
        frame="icrf",
        instant=INSTANT,
        time_scale="tdb",
        position=(1.0, 0.0, 0.0),
        velocity=(0.0, 0.0, 0.0),
        position_unit="au",
        velocity_unit="au/day",
        resource=RESOURCE,
        provider_observer_id="WGS84 site",
        provider_centre_id="0",
    )
    request = AstrometricDirectionRequest(
        target="moon",
        centre="solar system barycenter",
        reception_instant=INSTANT,
        reception_time_scale="tdb",
    )
    return AstrometricDirectionRealizer().direction(
        MoonSource(), request, observer
    )


def test_moon_uses_the_generic_astrometric_contract_with_naif_301():
    result = _astrometric()

    assert result.request.target == "moon"
    assert result.target_provider_id == "301"
    assert result.observer_state.provider_centre_id == "0"
    assert result.geometry.ids.tolist() == ["moon"]
    assert result.geometry.coordinate_spec.origin == "observer"
    assert result.geometry.coordinate_spec.epoch is None
    assert result.geometry.coordinate_spec.equinox is None
    assert 0.0 < result.distance_au < 0.01
    assert result.light_time_days > 0.0


def test_moon_uses_the_generic_apparent_contract_without_second_observe(
    monkeypatch,
):
    astrometric = _astrometric()
    kernel = object()
    source = object.__new__(SkyfieldEphemerisStateSource)
    source._kernel = kernel
    source.resource = RESOURCE
    centre = SimpleNamespace(
        target="WGS84 site",
        position=SimpleNamespace(au=(1.0, 0.0, 0.0)),
        velocity=SimpleNamespace(au_per_d=(0.0, 0.0, 0.0)),
    )
    observer = SimpleNamespace(
        ephemeris=kernel,
        t=object(),
        t_astropy=Time(INSTANT, scale="tdb"),
        skyfield=SimpleNamespace(at=lambda time: centre),
    )
    captured = {}

    def apparent(self, deflectors):
        captured["target"] = self.target
        captured["deflectors"] = deflectors
        return SimpleNamespace(
            radec=lambda: (
                SimpleNamespace(hours=5.0),
                SimpleNamespace(degrees=-10.0),
                object(),
            )
        )

    monkeypatch.setattr(
        "wenu.skyfield_ephemeris.SkyfieldAstrometric.apparent",
        apparent,
    )
    result = SkyfieldApparentDirectionRealizer().direction(
        astrometric,
        observer=observer,
        source=source,
    )

    assert captured == {"target": 301, "deflectors": (10, 599, 699)}
    assert result.geometry.ids.tolist() == ["moon"]
    assert result.geometry.lon_deg == pytest.approx((75.0,))
    assert result.geometry.lat_deg == pytest.approx((-10.0,))
