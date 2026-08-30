"""Apparent Solar-System direction realization contracts."""

from types import SimpleNamespace

import pytest
from astropy.time import Time

from wenu.ephemeris import (
    EphemerisResourceIdentity,
    EphemerisState,
)
from wenu.skyfield_ephemeris import (
    SkyfieldApparentDirectionRealizer,
    SkyfieldEphemerisStateSource,
)
from wenu.solar_system_directions import (
    ApparentCorrectionPolicy,
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


class TargetSource:
    def state(self, request):
        return EphemerisState(
            request=request,
            position=(1.0, 1.0, 0.0),
            velocity=(0.10, 0.20, 0.30),
            position_unit="au",
            velocity_unit="au/day",
            resource=RESOURCE,
            provider_target_id="299",
            provider_centre_id="0",
        )


def astrometric_direction():
    observer_state = ObserverBarycentricState(
        observer_id="La Ligua",
        centre="solar system barycenter",
        frame="icrf",
        instant=INSTANT,
        time_scale="tdb",
        position=(0.0, 0.0, 0.0),
        velocity=(0.01, 0.02, 0.03),
        position_unit="au",
        velocity_unit="au/day",
        resource=RESOURCE,
        provider_observer_id="test site",
        provider_centre_id="0",
    )
    request = AstrometricDirectionRequest(
        target="venus",
        centre="solar system barycenter",
        reception_instant=INSTANT,
        reception_time_scale="tdb",
    )
    return AstrometricDirectionRealizer().direction(
        TargetSource(),
        request,
        observer_state,
    )


def skyfield_context():
    kernel = object()
    source = object.__new__(SkyfieldEphemerisStateSource)
    source._kernel = kernel
    source.resource = RESOURCE
    centre = SimpleNamespace(
        target="test site",
        position=SimpleNamespace(au=(0.0, 0.0, 0.0)),
        velocity=SimpleNamespace(au_per_d=(0.01, 0.02, 0.03)),
    )
    observer = SimpleNamespace(
        ephemeris=kernel,
        t=object(),
        t_astropy=Time(INSTANT, scale="tdb"),
        skyfield=SimpleNamespace(at=lambda time: centre),
    )
    return source, observer


def test_policy_declares_deflectors_and_requires_apparent_physics():
    policy = ApparentCorrectionPolicy()

    assert policy.model == "Skyfield apparent"
    assert policy.deflector_naif_ids == (10, 599, 699)
    assert policy.earth_deflection is True
    assert policy.aberration is True

    with pytest.raises(ValueError, match="aberration"):
        ApparentCorrectionPolicy(aberration=False)
    with pytest.raises(ValueError, match="earth_deflection"):
        ApparentCorrectionPolicy(earth_deflection=False)


def test_realizer_consumes_astrometric_result_without_observe(
    monkeypatch,
):
    astrometric = astrometric_direction()
    source, observer = skyfield_context()
    captured = {}

    def apparent(self, deflectors):
        captured["position"] = tuple(self.position.au)
        captured["velocity"] = tuple(self.velocity.au_per_d)
        captured["light_time"] = self.light_time
        captured["deflectors"] = deflectors
        return SimpleNamespace(
            radec=lambda: (
                SimpleNamespace(hours=12.0),
                SimpleNamespace(degrees=-20.0),
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

    assert captured["position"] == pytest.approx((1.0, 1.0, 0.0))
    assert captured["velocity"] == pytest.approx((0.09, 0.18, 0.27))
    assert captured["light_time"] == astrometric.light_time_days
    assert captured["deflectors"] == (10, 599, 699)
    assert result.geometry.lon_deg == pytest.approx((180.0,))
    assert result.geometry.lat_deg == pytest.approx((-20.0,))
    assert result.geometry.ids.tolist() == ["venus"]
    spec = result.geometry.coordinate_spec
    assert spec.frame == "icrs"
    assert spec.origin == "observer"
    assert spec.position_status.value == "apparent"
    assert spec.epoch is None
    assert spec.equinox is None
    assert spec.corrections == frozenset(
        (
            "one-way-light-time",
            "aberration",
            "gravitational-deflection",
            "earth-gravitational-deflection",
        )
    )
    assert "without observe()" in result.provenance[0]


def test_realizer_rejects_mismatched_observer_state():
    astrometric = astrometric_direction()
    source, observer = skyfield_context()
    observer.skyfield = SimpleNamespace(
        at=lambda time: SimpleNamespace(
            target="test site",
            position=SimpleNamespace(au=(1.0, 0.0, 0.0)),
            velocity=SimpleNamespace(au_per_d=(0.01, 0.02, 0.03)),
        )
    )

    with pytest.raises(ValueError, match="does not match"):
        SkyfieldApparentDirectionRealizer().direction(
            astrometric,
            observer=observer,
            source=source,
        )


def test_realizer_rejects_another_kernel_or_reception_instant():
    astrometric = astrometric_direction()
    source, observer = skyfield_context()
    observer.ephemeris = object()

    with pytest.raises(ValueError, match="same ephemeris"):
        SkyfieldApparentDirectionRealizer().direction(
            astrometric,
            observer=observer,
            source=source,
        )

    source, observer = skyfield_context()
    observer.t_astropy = Time("2026-08-30T00:01:00", scale="tdb")
    with pytest.raises(ValueError, match="reception instant"):
        SkyfieldApparentDirectionRealizer().direction(
            astrometric,
            observer=observer,
            source=source,
        )
